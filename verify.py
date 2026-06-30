import json
import re
from rapidfuzz import fuzz
from src.ingest import pdf_to_text
from src.config import IA_CIRCULAR_2025, IA_CIRCULAR_2024, OUTPUT

# ---------- text normalization ----------
def normalize(t):
    if not t:
        return ""
    t = t.lower()
    for a, b in [('\u2019', "'"), ('\u2018', "'"), ('\u201c', '"'), ('\u201d', '"'),
                 ('\u2013', '-'), ('\u2014', '-'), ('\u2026', '...')]:
        t = t.replace(a, b)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

def alnum_only(t):
    return re.sub(r'[^a-z0-9]', '', t.lower())

# ---------- grounding: does verbatim_text really exist in the source? ----------
def ground_score(verbatim, source_norm, source_alnum):
    v = normalize(verbatim)
    if not v:
        return 0.0, "empty"
    if v in source_norm:                      # exact match
        return 100.0, "exact"
    va = alnum_only(verbatim)                  # robust to PDF spacing/hyphenation
    if len(va) >= 12 and va in source_alnum:
        return 98.0, "exact_despaced"
    if '...' in v:                             # model quoted "X ... Y"
        parts = [p.strip() for p in v.split('...') if len(p.strip()) >= 8]
        if parts:
            hits = sum(1 for p in parts
                       if p in source_norm or (len(alnum_only(p)) >= 10 and alnum_only(p) in source_alnum))
            frac = hits / len(parts)
            if frac == 1.0:
                return 95.0, "segmented_all"
            if frac >= 0.5:
                return 80.0 * frac + 10, "segmented_partial"
    return float(fuzz.partial_ratio(v, source_norm)), "fuzzy"   # best-substring alignment

def band_for(s):
    return "grounded" if s >= 90 else ("partial" if s >= 75 else "flagged")

# ---------- completeness + clause quality ----------
def completeness(ob):
    fields = ["required_action", "evidence", "trigger", "source_clause", "verbatim_text"]
    filled = sum(1 for f in fields
                 if (ob.get(f) or "").strip() and (ob.get(f) or "").strip().lower() not in ("\u2014", "-", "n/a", "none"))
    return filled / len(fields)

def clause_quality(ob):
    c = (ob.get("source_clause") or "").lower()
    if not c or c in ("\u2014", "-", "n/a"):
        return 0.0
    if re.search(r'\d', c) or any(k in c for k in ["regulation", "para", "clause", "schedule", "annexure", "section"]):
        return 1.0
    return 0.4

def confidence(gscore, ob):
    conf = 0.70 * (gscore / 100.0) + 0.20 * completeness(ob) + 0.10 * clause_quality(ob)
    if gscore < 75:                # if we can't find it in the source, don't trust it
        conf = min(conf, 0.45)
    return round(conf * 100, 1)

def conf_band(conf, gscore):
    if gscore < 75:
        return "Low"
    if conf >= 85:
        return "High"
    if conf >= 70:
        return "Medium"
    return "Low"

# ---------- run verification over one obligation file ----------
def verify_file(obligations_path, pdf_path, out_path, label):
    print(f"\n=== Verifying {label} ===")
    try:
        obligations = json.load(open(obligations_path))
    except FileNotFoundError:
        print(f"  Skipped - {obligations_path} not found.")
        return

    print("  Reading source PDF...")
    source = pdf_to_text(pdf_path)
    source_norm = normalize(source)
    source_alnum = alnum_only(source)

    grounded = partial = flagged = 0
    hi = mid = lo = 0
    for ob in obligations:
        gscore, method = ground_score(ob.get("verbatim_text", ""), source_norm, source_alnum)
        gband = band_for(gscore)
        conf = confidence(gscore, ob)
        cband = conf_band(conf, gscore)
        ob["grounding_score"] = round(gscore, 1)
        ob["grounding_method"] = method
        ob["grounding_band"] = gband
        ob["confidence"] = conf
        ob["confidence_band"] = cband
        grounded += gband == "grounded"; partial += gband == "partial"; flagged += gband == "flagged"
        hi += cband == "High"; mid += cband == "Medium"; lo += cband == "Low"

    json.dump(obligations, open(out_path, "w"), indent=2)

    n = len(obligations)
    pct = lambda x: f"{(100 * x / n):.1f}%" if n else "0%"
    print(f"  Total obligations       : {n}")
    print(f"  Grounded (>=90)         : {grounded}  ({pct(grounded)})")
    print(f"  Partial  (75-89)        : {partial}  ({pct(partial)})")
    print(f"  FLAGGED  (<75)          : {flagged}  ({pct(flagged)})  <- possible hallucinations")
    print(f"  Verifiably traceable    : {pct(grounded + partial)} of all obligations")
    print(f"  Confidence  High/Med/Low: {hi} / {mid} / {lo}")
    print(f"  Saved -> {out_path}")

    flags = [o for o in obligations if o["grounding_band"] == "flagged"]
    if flags:
        print(f"\n  --- {len(flags)} flagged for human review ---")
        for o in flags[:15]:
            print(f"    [{o['obligation_id']}] score={o['grounding_score']}  {o.get('title','')[:55]}")

def main():
    OUTPUT.mkdir(exist_ok=True)
    verify_file(OUTPUT / "obligations_2025.json", IA_CIRCULAR_2025,
                OUTPUT / "obligations_2025_verified.json", "2025 IA circular")
    if (OUTPUT / "obligations_2024.json").exists():
        verify_file(OUTPUT / "obligations_2024.json", IA_CIRCULAR_2024,
                    OUTPUT / "obligations_2024_verified.json", "2024 IA circular")

if __name__ == "__main__":
    main()
