"""
Extracts obligations from the 2024 IA master circular. Mirrors extract_full.py's
batching, resume, and failed-chunk-recovery pattern, so the 2024 run gets the
same reliability guarantees as the 2025 run.

Previously this file was a near-copy of extract_full.py that kept the *2025*
circular name/date hardcoded in its prompt -- meaning the model was told it
was reading the wrong circular while actually processing 2024 text. Fixed
below. It also had leftover Groq-era "429 rate limit" handling that makes no
sense for local Ollama (no external rate limit exists) -- replaced with the
same generic failure handling extract_full.py uses.

Your existing output/obligations_2024.json is unaffected by this fix -- it
was already extracted successfully. This only matters if you re-run this
script from scratch, or reuse it as a template for a future circular.

    python extract_2024.py            # first run, or resume if interrupted
"""
import json
import time
from src.ingest import pdf_to_text
from src.schema import ObligationList
from src.llm import extract_structured
from src.config import IA_CIRCULAR_2024, EXTRACTION_MODEL, OUTPUT

# Same thermal-batching rationale as extract_full.py -- stop after this many
# chunks per run so the Mac can cool, rather than running everything in one
# unbroken pass.
CHUNKS_PER_RUN = 14

PROMPT = """You are a SEBI compliance analyst. Below is an excerpt from the SEBI Master Circular
for Investment Advisers (SEBI/HO/MIRSD-PoD-1/P/CIR/2024/50, dated 21-May-2024).

Extract every distinct regulatory OBLIGATION an Investment Adviser must comply with in this excerpt.
For each obligation capture the exact source clause number and the verbatim text that states it.
Do NOT invent obligations not present in the text. If none are present, return an empty list.

CRITICAL EXTRACTION RULES -- follow these strictly:
1. Extract each distinct requirement as its OWN separate obligation, even if it appears in the
   same paragraph or sentence cluster as another requirement. Do NOT merge multiple requirements
   into a single obligation.
2. Pay special attention to a "shall" sentence immediately followed by a "shall not" sentence in
   the same paragraph (e.g. "IAs shall accept fees via X. IAs shall not accept cash deposits.") --
   these are TWO separate obligations, not one.
3. Each lettered or numbered sub-clause -- (a), (b), (c) or i, ii, iii or step 1, step 2 -- is its
   own separate obligation, even if closely related to the one before it.
4. Check footnotes carefully. If a footnote contains its own requirement or deadline (often marked
   with a superscript number in the text), extract it as a separate obligation with its own
   source_clause noting it is a footnote.
5. When in doubt, extract MORE granular obligations rather than merging them -- under-extraction
   (missing an obligation) is a worse error than over-extraction (a few closely related items).

EXCERPT:
---
{excerpt}
---
"""

def chunk_text(text: str, chunk_size: int = 3000, overlap: int = 200):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def _record_failed_chunk(n):
    """Persist failed chunk numbers across runs/batches so a failure is never
    silently lost in scrollback -- recover_chunks_2024.py reads this file."""
    fc_path = OUTPUT / "failed_chunks_2024.json"
    existing = json.load(open(fc_path)) if fc_path.exists() else []
    if n not in existing:
        existing.append(n)
    with open(fc_path, "w") as f:
        json.dump(sorted(existing), f)

def main():
    OUTPUT.mkdir(exist_ok=True)
    out_path = OUTPUT / "obligations_2024.json"

    if out_path.exists():
        with open(out_path) as f:
            existing = json.load(f)
        seen_ids = {ob["obligation_id"] for ob in existing}
        all_obligations = existing
        print(f"Resuming -- {len(all_obligations)} obligations already saved")
    else:
        all_obligations = []
        seen_ids = set()

    progress_path = OUTPUT / "progress_2024.json"
    if progress_path.exists():
        with open(progress_path) as f:
            start_chunk = json.load(f)["next_chunk"]
        print(f"Resuming from chunk {start_chunk + 1}")
    else:
        start_chunk = 0

    print("Reading 2024 PDF...")
    full_text = pdf_to_text(IA_CIRCULAR_2024)
    chunks = chunk_text(full_text)
    print(f"Total chunks: {len(chunks)}, processing from chunk {start_chunk + 1}")
    print(f"This run will process up to {CHUNKS_PER_RUN} chunks, then stop so the Mac can cool.\n")

    processed_this_run = 0
    last_done = start_chunk
    failed_chunks = []

    for i, chunk in enumerate(chunks):
        if i < start_chunk:
            continue
        if processed_this_run >= CHUNKS_PER_RUN:
            break
        processed_this_run += 1

        print(f"Processing chunk {i+1}/{len(chunks)}...", end=" ", flush=True)
        try:
            result = extract_structured(
                PROMPT.format(excerpt=chunk),
                ObligationList,
                model=EXTRACTION_MODEL
            )
            new = 0
            for ob in result.obligations:
                if ob.obligation_id not in seen_ids:
                    seen_ids.add(ob.obligation_id)
                    all_obligations.append(ob.model_dump())
                    new += 1
            print(f"found {len(result.obligations)}, added {new} new")
        except Exception as e:
            # No Groq-style 429 handling -- there's no external rate limit on
            # local Ollama. Any failure here (timeout, OOM, malformed output
            # that survived schema coercion, etc.) is recorded and skipped,
            # same as extract_full.py, so recover_chunks_2024.py can retry it.
            print(f"ERROR: {e}")
            failed_chunks.append(i + 1)
            _record_failed_chunk(i + 1)

        with open(out_path, "w") as f:
            json.dump(all_obligations, f, indent=2)
        with open(progress_path, "w") as f:
            json.dump({"next_chunk": i + 1}, f)
        last_done = i + 1

        time.sleep(2)

    remaining = len(chunks) - last_done
    print()
    if remaining > 0:
        print(f"Batch complete -- {last_done}/{len(chunks)} chunks done, {remaining} remaining.")
        print(f"Let the Mac cool for a few minutes, then run  python extract_2024.py  again to continue.")
    else:
        print(f"All {len(chunks)} chunks complete!")
    print(f"Total unique obligations so far: {len(all_obligations)}")
    print(f"Saved to: {out_path}")
    if failed_chunks:
        print(f"Chunks that errored and were skipped this run: {failed_chunks}")
        print(f"Once all batches are done, run  python recover_chunks_2024.py  to patch these in.")

if __name__ == "__main__":
    main()
