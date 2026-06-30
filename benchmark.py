"""
Gold-standard accuracy benchmark. Supports multiple labeled sections so you
can re-score section 1 later (e.g. to prove a prompt fix improved recall)
without losing it when you label a second or third section.

USAGE:
  python benchmark.py          -> scores data/gold/section_raw.txt + gold_obligations.json
  python benchmark.py _2       -> scores data/gold/section_raw_2.txt + gold_obligations_2.json
"""
import json
import re
import sys
from pathlib import Path
from rapidfuzz import fuzz
from src.config import OUTPUT

GOLD_DIR = Path("data/gold")
SUFFIX = sys.argv[1] if len(sys.argv) > 1 else ""
SECTION_PATH = GOLD_DIR / f"section_raw{SUFFIX}.txt"
GOLD_PATH = GOLD_DIR / f"gold_obligations{SUFFIX}.json"

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
    print(f"Scoring section: {SECTION_PATH.name}  /  {GOLD_PATH.name}\n")

    if not SECTION_PATH.exists():
        print(f"No section saved yet at {SECTION_PATH}.")
        print(f"Run: python dump_section.py <start> <end> {SUFFIX}")
        return

    if not GOLD_PATH.exists():
        template = {
            "section_label": "DESCRIBE WHICH CLAUSE/TOPIC THIS SECTION COVERS",
            "obligations": [
                {"id": "gold-01", "title": "Short title", "key_phrase": "5-12 distinctive words from the text"}
            ]
        }
        json.dump(template, open(GOLD_PATH, "w"), indent=2)
        print(f"No gold file yet -- created a template at {GOLD_PATH}")
        print(f"Open it, read {SECTION_PATH}, and fill in every real obligation. Then re-run.")
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
            print(f"  MISS   [{g['id']}] {g['title']}   <-- false negative")

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
        for o in fp_list:
            print(f"  [{o['obligation_id']}] {o.get('title','')}")
            print(f"     {o.get('verbatim_text','')[:140]}")

if __name__ == "__main__":
    main()
