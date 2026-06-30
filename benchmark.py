"""
Gold-standard accuracy benchmark.

HOW TO USE:
1. Run `python dump_section.py` (no args) to see the document length and a preview.
2. Pick a clean section (e.g. one numbered clause/topic) and run:
       python dump_section.py <start_char> <end_char>
   This saves that section to data/gold/section_raw.txt and prints a preview.
3. Read data/gold/section_raw.txt yourself and write down EVERY obligation a
   compliance officer would identify in it. Put them in data/gold/gold_obligations.json
   using the template (each entry needs an id, a short title, and a key_phrase --
   a distinctive 5-12 word snippet that should appear in the obligation if it was
   correctly extracted).
4. Run `python benchmark.py` to get precision, recall, and F1 for that section,
   plus a list of any system extractions in scope that don't match your gold list
   (review these by hand -- they are either real misses in your gold list, or
   genuine false positives).
"""
import json
import re
from pathlib import Path
from rapidfuzz import fuzz
from src.config import OUTPUT

GOLD_DIR = Path("data/gold")
SECTION_PATH = GOLD_DIR / "section_raw.txt"
GOLD_PATH = GOLD_DIR / "gold_obligations.json"

def normalize(t):
    if not t:
        return ""
    t = t.lower()
    for a, b in [('\u2019', "'"), ('\u2018', "'"), ('\u201c', '"'), ('\u201d', '"'),
                 ('\u2013', '-'), ('\u2014', '-')]:
        t = t.replace(a, b)
    return re.sub(r'\s+', ' ', t).strip()

def in_scope(verbatim, section_norm):
    v = normalize(verbatim)
    if not v:
        return False
    if v in section_norm:
        return True
    return fuzz.partial_ratio(v, section_norm) >= 75

def find_match(key_phrase, candidates):
    kp = normalize(key_phrase)
    for ob in candidates:
        vt = normalize(ob.get("verbatim_text", ""))
        if kp in vt or fuzz.partial_ratio(kp, vt) >= 80:
            return ob["obligation_id"]
    return None

def main():
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    if not SECTION_PATH.exists():
        print("No section selected yet.")
        print("Run: python dump_section.py            (to see document length)")
        print("Then: python dump_section.py <start> <end>   (to select + save a section)")
        return

    if not GOLD_PATH.exists():
        template = {
            "section_label": "DESCRIBE WHICH CLAUSE/TOPIC THIS SECTION COVERS",
            "obligations": [
                {"id": "gold-01", "title": "Short title of obligation 1",
                 "key_phrase": "5-12 distinctive words that should appear in the extracted verbatim text"},
                {"id": "gold-02", "title": "Short title of obligation 2",
                 "key_phrase": "another distinctive phrase from the section"}
            ]
        }
        json.dump(template, open(GOLD_PATH, "w"), indent=2)
        print(f"No gold file yet -- created a template at {GOLD_PATH}")
        print("Open it, read data/gold/section_raw.txt, and fill in every real obligation. Then re-run this script.")
        return

    section_text = open(SECTION_PATH).read()
    section_norm = normalize(section_text)
    gold = json.load(open(GOLD_PATH))

    sys_path = OUTPUT / "obligations_2025_verified.json"
    if not sys_path.exists():
        sys_path = OUTPUT / "obligations_2025.json"
    system_obs = json.load(open(sys_path))

    in_scope_obs = [o for o in system_obs if in_scope(o.get("verbatim_text", ""), section_norm)]
    print(f"Section: {gold.get('section_label','(unlabeled)')}")
    print(f"System obligations in scope: {len(in_scope_obs)}")
    print(f"Gold obligations to check  : {len(gold['obligations'])}\n")

    tp, fn_list, matched_ids = 0, [], set()
    for g in gold["obligations"]:
        m = find_match(g["key_phrase"], in_scope_obs)
        if m:
            tp += 1
            matched_ids.add(m)
            print(f"  MATCH  [{g['id']}] {g['title']}  ->  {m}")
        else:
            fn_list.append(g)
            print(f"  MISS   [{g['id']}] {g['title']}   <-- system did not extract this (false negative)")

    fp_list = [o for o in in_scope_obs if o["obligation_id"] not in matched_ids]

    precision = tp / (tp + len(fp_list)) if (tp + len(fp_list)) else 0.0
    recall = tp / (tp + len(fn_list)) if (tp + len(fn_list)) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    sep = "=" * 50
    print("\n" + sep)
    print(f"  Precision : {precision:.2f}  ({tp} correct / {tp+len(fp_list)} extracted in scope)")
    print(f"  Recall    : {recall:.2f}  ({tp} found / {tp+len(fn_list)} should exist)")
    print(f"  F1        : {f1:.2f}")
    print(sep)

    if fp_list:
        print(f"\n--- {len(fp_list)} extra extraction(s) in scope not matched to your gold list ---")
        print("Review each: if it's a real obligation you missed labeling, add it to gold_obligations.json")
        print("and re-run. If it's genuinely wrong/hallucinated, it's a true false positive.\n")
        for o in fp_list:
            print(f"  [{o['obligation_id']}] {o.get('title','')}")
            print(f"     {o.get('verbatim_text','')[:140]}")

if __name__ == "__main__":
    main()
