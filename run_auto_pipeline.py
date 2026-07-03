"""
Automated end-to-end pipeline -- the "act" stage that follows sebi_monitor's
"perceive" stage. Detects a new SEBI circular, downloads it, and pushes it
through the SAME extraction/verification/enrichment/diff/audit steps a human
runs manually today (extract_full.py's chunk_text()/PROMPT, verify.py's
verify_file(), enrich.py's main(), operations.py's main(), diff_engine's
diff_obligations()) -- nothing here reimplements pipeline logic, it just wires
a freshly downloaded circular through the existing functions.

Only "Investment Advisers" is fully processed end-to-end: it's the only
category the rest of the pipeline (obligations_2025*.json, verify/enrich/
operations' hardcoded paths, the 2024-vs-2025 diff) is wired for today. Other
tracked categories (e.g. Stock Brokers) are still downloaded and recorded in
the manifest so nothing is silently dropped, but are flagged as download-only
until that category gets its own downstream wiring.

    python run_auto_pipeline.py
"""
import json
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from sebi_monitor import check_for_new_circulars
from src.config import OUTPUT, ROOT, EXTRACTION_MODEL
from src.ingest import pdf_to_text
from src.schema import ObligationList
from src.llm import extract_structured
from src.audit_log import append_event
from extract_full import chunk_text, PROMPT as EXTRACT_PROMPT
import verify
import enrich
import operations
from diff_engine import diff_obligations, load_obligations

CIRCULARS_DIR = ROOT / "data" / "raw" / "circulars"
MANIFEST_PATH = CIRCULARS_DIR / "manifest.json"
ARCHIVE_DIR = OUTPUT / "archive"

# Canonical step order the dashboard's "Refresh status" panel checks off --
# keep in sync with dashboard.py's PIPELINE_RUN_STEPS.
STATUS_PATH = OUTPUT / "pipeline_status.json"
STATUS_STEPS = ["search", "download", "extract", "verify", "build_rules", "update_register", "complete"]


def write_status(step, detail=""):
    """Progress file for the dashboard's manual 'Refresh status' button --
    same 'write after every step' pattern extract_full.py already uses for
    progress.json, just at pipeline-step granularity instead of per-chunk."""
    OUTPUT.mkdir(exist_ok=True)
    json.dump(
        {"step": step, "detail": detail, "updated_at": datetime.now(timezone.utc).isoformat()},
        open(STATUS_PATH, "w"),
    )

# The only category with full downstream wiring today -- see module docstring.
PROCESSABLE_CATEGORIES = {"Investment Advisers"}

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
DOWNLOAD_RETRIES = 3
DOWNLOAD_BACKOFF_SECONDS = 5
DOWNLOAD_TIMEOUT_SECONDS = 60

# The fixed circular reference extract_full.py's PROMPT was written for.
# Replaced with the new circular's real reference/date before use below.
OLD_CIRCULAR_REF = "SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/94, dated 27-Jun-2025"

_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
_HEADER_RE = re.compile(rf"([A-Za-z0-9][A-Za-z0-9/().\-]{{5,60}})\s+((?:{_MONTHS})\s+\d{{1,2}},?\s+\d{{4}})")


def resolve_url(url):
    return url if url.startswith("http") else f"https://www.sebi.gov.in{url}"


def slugify(text, max_len=60):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:max_len]


def category_slug(category):
    return re.sub(r"[^a-z0-9]+", "_", category.lower()).strip("_")


def circular_date_slug(date_text):
    """'Feb 06, 2026' -> '2026-02-06'. Falls back to a slugified raw string if
    SEBI ever changes the listing's date format."""
    try:
        return datetime.strptime(date_text, "%b %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return slugify(date_text, max_len=20)


def resolve_pdf_url(landing_url):
    """The SEBI listing links to an HTML landing page, not the PDF directly --
    the actual PDF is embedded as an iframe's `file=` query param. Falls back
    to treating the landing URL itself as the PDF if it already ends in .pdf."""
    if landing_url.lower().endswith(".pdf"):
        return landing_url
    resp = requests.get(landing_url, headers=HEADERS, timeout=DOWNLOAD_TIMEOUT_SECONDS)
    resp.raise_for_status()
    m = re.search(r"file=(https?://[^'\"&]+\.pdf)", resp.text)
    return m.group(1) if m else None


def download_pdf(url, dest_path):
    """Retries with backoff; never raises -- a failed download should skip
    this one circular, not crash the whole run."""
    for attempt in range(1, DOWNLOAD_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=DOWNLOAD_TIMEOUT_SECONDS)
            resp.raise_for_status()
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(resp.content)
            return True
        except Exception as e:
            print(f"  Download attempt {attempt}/{DOWNLOAD_RETRIES} failed: {e}")
            if attempt < DOWNLOAD_RETRIES:
                time.sleep(DOWNLOAD_BACKOFF_SECONDS * attempt)
    return False


def load_manifest():
    return json.load(open(MANIFEST_PATH)) if MANIFEST_PATH.exists() else {}


def save_manifest(manifest):
    CIRCULARS_DIR.mkdir(parents=True, exist_ok=True)
    json.dump(manifest, open(MANIFEST_PATH, "w"), indent=2)


def extract_circular_header(text, fallback_date):
    """Best-effort pull of the new circular's own reference number + date from
    the first page, so the extraction prompt names the real circular instead
    of the fixed 2025/94 one extract_full.py was written for."""
    m = _HEADER_RE.search(text[:1000])
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "reference number not found in source PDF", fallback_date


def build_prompt(circular_ref, circular_date):
    new_ref = f"{circular_ref}, dated {circular_date}"
    if OLD_CIRCULAR_REF not in EXTRACT_PROMPT:
        print("  WARNING: extract_full.PROMPT's hardcoded circular reference has "
              "changed -- extracting with the prompt's existing reference text unmodified.")
        return EXTRACT_PROMPT
    return EXTRACT_PROMPT.replace(OLD_CIRCULAR_REF, new_ref)


def archive_current_outputs():
    """Copies today's obligations_2025_verified.json (and the pre-verification
    obligations_2025.json) into output/archive/ before extraction overwrites
    them, so the previous version is never lost and can serve as the "old"
    side of the diff."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    verified_src = OUTPUT / "obligations_2025_verified.json"
    raw_src = OUTPUT / "obligations_2025.json"
    archived_verified = ARCHIVE_DIR / f"obligations_verified_{today}.json"
    archived_raw = ARCHIVE_DIR / f"obligations_raw_{today}.json"

    if verified_src.exists():
        shutil.copy2(verified_src, archived_verified)
        print(f"  Archived {verified_src.name} -> {archived_verified}")
    if raw_src.exists():
        shutil.copy2(raw_src, archived_raw)
        print(f"  Archived {raw_src.name} -> {archived_raw}")

    old_for_diff = archived_verified if archived_verified.exists() else archived_raw
    return old_for_diff


def run_extraction(pdf_path, circular_ref, circular_date):
    """Reuses extract_full.py's chunk_text() and PROMPT verbatim -- only the
    prompt's circular reference is substituted. Writes to obligations_2025.json,
    the same filename verify.py/enrich.py/operations.py/dashboard.py expect."""
    print(f"  Reading PDF: {pdf_path}")
    full_text = pdf_to_text(str(pdf_path))
    chunks = chunk_text(full_text)
    print(f"  Total chunks: {len(chunks)}")
    prompt_template = build_prompt(circular_ref, circular_date)

    all_obligations = []
    seen_ids = set()
    failed_chunks = []
    for i, chunk in enumerate(chunks):
        write_status("extract", f"chunk {i+1}/{len(chunks)}")
        print(f"  Processing chunk {i+1}/{len(chunks)}...", end=" ", flush=True)
        try:
            result = extract_structured(
                prompt_template.format(excerpt=chunk),
                ObligationList,
                model=EXTRACTION_MODEL,
            )
            new = 0
            for ob in result.obligations:
                if ob.obligation_id not in seen_ids:
                    seen_ids.add(ob.obligation_id)
                    all_obligations.append(ob.model_dump())
                    new += 1
            print(f"found {len(result.obligations)}, added {new} new")
        except Exception as e:
            print(f"ERROR: {e}")
            failed_chunks.append(i + 1)
        time.sleep(2)

    out_path = OUTPUT / "obligations_2025.json"
    json.dump(all_obligations, open(out_path, "w"), indent=2)
    print(f"  Extraction complete: {len(all_obligations)} obligations -> {out_path}")
    if failed_chunks:
        print(f"  Chunks that errored and were skipped: {failed_chunks}")
    return out_path


def process_investment_adviser_circular(cat, row, pdf_path):
    """Runs the new circular through verify -> enrich -> operations -> diff,
    in that order -- matching the codebase's established canonical order
    (enrich writes risk_band/department/risk_points first, then operations'
    keyword-based risk_band write is the final, canonical one; see commit
    284203f). Returns (circular_ref, circular_date, diff_summary, new_count)."""
    full_text = pdf_to_text(str(pdf_path))
    circular_ref, circular_date = extract_circular_header(full_text, fallback_date=row["date"])
    print(f"  Circular reference: {circular_ref}, dated {circular_date}")

    old_for_diff = archive_current_outputs()

    obligations_path = run_extraction(pdf_path, circular_ref, circular_date)

    write_status("verify", f"Verifying {circular_ref} against source PDF")
    print(f"\n  Running verify.py's verify_file()...")
    verify.verify_file(
        obligations_path, str(pdf_path),
        OUTPUT / "obligations_2025_verified.json",
        label=f"{cat} -- {circular_ref}",
    )

    write_status("build_rules", "Enriching risk/department")
    print(f"\n  Running enrich.py...")
    enrich.main()

    write_status("update_register", "Building compliance register, rules, calendar")
    print(f"\n  Running operations.py...")
    operations.main()

    print(f"\n  Diffing against the archived previous version...")
    old_obligations = load_obligations(old_for_diff)
    new_obligations = load_obligations(OUTPUT / "obligations_2025_verified.json")
    report = diff_obligations(old_obligations, new_obligations)
    json.dump(report, open(OUTPUT / "change_impact_report.json", "w"), indent=2)
    s = report["summary"]
    print(f"  Diff: {s['added']} added, {s['modified']} modified, {s['removed']} removed")

    return circular_ref, circular_date, s, len(new_obligations)


def main():
    print("=" * 60)
    print("AUTO PIPELINE -- checking for new SEBI circulars")
    print("=" * 60)
    write_status("search", "Checking SEBI's live circulars listing")
    try:
        alerts, _latest = check_for_new_circulars()
    except Exception as e:
        print(f"ERROR checking for new circulars: {e}")
        write_status("error", f"Search failed: {e}")
        return

    if not alerts:
        print("No new circulars detected. Nothing to do.")
        write_status("complete", "No new circulars detected")
        return

    manifest = load_manifest()
    processed_summaries = []

    for cat, prev, row in alerts:
        landing_url = resolve_url(row["url"])
        print(f"\n--- New circular detected: {cat} -- {row['title']} ({row['date']}) ---")

        if landing_url in manifest:
            print("  Already in manifest -- skipping (dedup guard).")
            continue

        try:
            pdf_url = resolve_pdf_url(landing_url)
        except Exception as e:
            print(f"  ERROR locating PDF on {landing_url}: {e} -- skipping this circular.")
            continue
        if not pdf_url:
            print(f"  Could not locate a PDF link on {landing_url} -- skipping this circular.")
            continue

        local_path = CIRCULARS_DIR / (
            f"{category_slug(cat)}_{circular_date_slug(row['date'])}_{slugify(row['title'])}.pdf"
        )
        write_status("download", f"Downloading {row['title']} ({cat})")
        print(f"  Downloading {pdf_url} -> {local_path}")
        if not download_pdf(pdf_url, local_path):
            print(f"  Failed to download after {DOWNLOAD_RETRIES} attempts -- skipping this circular.")
            write_status("error", f"Download failed for {row['title']}")
            continue

        if cat not in PROCESSABLE_CATEGORIES:
            print(f"  '{cat}' has no downstream extraction wiring yet -- recording download only.")
            manifest[landing_url] = {
                "title": row["title"], "date": row["date"], "source_url": landing_url,
                "pdf_url": pdf_url, "category": cat, "local_path": str(local_path),
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }
            save_manifest(manifest)
            append_event("circular_downloaded", {
                "category": cat, "title": row["title"], "date": row["date"],
                "source_url": landing_url, "note": "download only -- no extraction pipeline wired for this category",
            })
            processed_summaries.append(f"{row['title']} ({cat}, download only)")
            continue

        try:
            circular_ref, circular_date, diff_summary, obligation_count = process_investment_adviser_circular(
                cat, row, local_path
            )
        except Exception as e:
            print(f"  ERROR processing {cat} circular: {e} -- skipping this circular.")
            write_status("error", f"{cat} processing failed: {e}")
            continue

        manifest[landing_url] = {
            "title": row["title"], "date": row["date"], "source_url": landing_url,
            "pdf_url": pdf_url, "category": cat, "local_path": str(local_path),
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
        save_manifest(manifest)

        append_event("auto_pipeline_circular_processed", {
            "category": cat,
            "circular_reference": circular_ref,
            "circular_date": circular_date,
            "title": row["title"],
            "source_url": landing_url,
            "obligation_count": obligation_count,
            "change_summary": diff_summary,
        })

        processed_summaries.append(
            f"{circular_ref} ({cat}, {circular_date}) -- "
            f"{diff_summary['added']} added / {diff_summary['modified']} modified / {diff_summary['removed']} removed"
        )

    if not processed_summaries:
        print("\nNo circulars were newly processed this run.")
        write_status("complete", "No circulars were newly processed this run")
        return

    print("\n--- Committing to git ---")
    status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout
    if not status.strip():
        print("Nothing changed on disk -- skipping commit.")
        write_status("complete", "; ".join(processed_summaries))
        return

    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    commit_msg = "Auto-pipeline: ingest " + "; ".join(processed_summaries)
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=ROOT, check=True)
    branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    print(f"\nCommitted to branch '{branch}' (NOT pushed, NOT merged to main).")
    write_status("complete", "; ".join(processed_summaries))


if __name__ == "__main__":
    main()
