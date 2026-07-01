import json
from rapidfuzz import fuzz
from src.config import OUTPUT

# Text fields get paraphrase tolerance -- two independent extraction runs will
# naturally reword identical source text slightly differently, and that noise
# shouldn't masquerade as a real regulatory change. Structured fields don't
# get this tolerance: a frequency or deadline difference IS the signal, full stop.
TEXT_FIELDS = {"title", "summary", "required_action", "evidence", "verbatim_text"}
TEXT_SIMILARITY_THRESHOLD = 92  # rapidfuzz ratio (0-100); below this = genuinely different wording

def _normalize(t):
    return " ".join((t or "").lower().split())

def load_obligations(path) -> dict:
    with open(path) as f:
        data = json.load(f)
    return {ob["obligation_id"]: ob for ob in data}

def field_changes(old_ob, new_ob):
    changes = {}
    for field in ["title", "summary", "required_action", "evidence", "frequency", "deadline", "verbatim_text"]:
        old_v, new_v = old_ob.get(field), new_ob.get(field)
        if field in TEXT_FIELDS:
            if _normalize(old_v) == _normalize(new_v):
                continue
            sim = fuzz.ratio(_normalize(old_v), _normalize(new_v)) if (old_v and new_v) else 0
            if sim >= TEXT_SIMILARITY_THRESHOLD:
                continue  # near-identical wording -- not treated as a real change
        else:
            if old_v == new_v:
                continue
        changes[field] = {"before": old_v, "after": new_v}
    return changes

def diff_obligations(old: dict, new: dict, use_semantic=True, sem_threshold=0.72):
    old_ids = set(old.keys())
    new_ids = set(new.keys())

    # Pass 1 -- exact ID match (fast, free, deterministic)
    added_ids = new_ids - old_ids
    removed_ids = old_ids - new_ids
    common_ids = old_ids & new_ids

    modified, unchanged = [], []
    for ob_id in common_ids:
        changes = field_changes(old[ob_id], new[ob_id])
        if changes:
            modified.append({"obligation_id": ob_id, "title": new[ob_id]["title"],
                              "match_type": "exact_id", "changes": changes})
        else:
            unchanged.append(ob_id)

    # Pass 2 -- semantic match on the leftovers (catches reworded/renamed obligations
    # that would otherwise wrongly appear as one "removed" + one unrelated "added")
    renamed_count = 0
    if use_semantic and added_ids and removed_ids:
        try:
            from src.semantic_match import match_unmatched
            removed_list = [old[i] for i in removed_ids]
            added_list = [new[i] for i in added_ids]
            sem_matches, leftover_old, leftover_new = match_unmatched(
                removed_list, added_list, threshold=sem_threshold)

            for old_ob, new_ob, score in sem_matches:
                changes = field_changes(old_ob, new_ob)
                if changes:
                    changes["obligation_id"] = {"before": old_ob["obligation_id"], "after": new_ob["obligation_id"]}
                    modified.append({
                        "obligation_id": new_ob["obligation_id"],
                        "title": new_ob["title"],
                        "match_type": "semantic",
                        "semantic_similarity": round(score, 3),
                        "changes": changes
                    })
                else:
                    unchanged.append(new_ob["obligation_id"])
                added_ids.discard(new_ob["obligation_id"])
                removed_ids.discard(old_ob["obligation_id"])
                renamed_count += 1
        except ImportError:
            print("  (sentence-transformers not installed -- skipping semantic matching, exact-ID only)")

    return {
        "summary": {
            "total_2024": len(old), "total_2025": len(new),
            "added": len(added_ids), "removed": len(removed_ids),
            "modified": len(modified), "unchanged": len(unchanged),
            "modified_via_semantic_match": renamed_count
        },
        "added": [new[i] for i in sorted(added_ids)],
        "removed": [old[i] for i in sorted(removed_ids)],
        "modified": modified,
        "unchanged": sorted(unchanged)
    }

def main():
    path_2024 = OUTPUT / "obligations_2024_verified.json"
    if not path_2024.exists():
        path_2024 = OUTPUT / "obligations_2024.json"
    path_2025 = OUTPUT / "obligations_2025_verified.json"
    if not path_2025.exists():
        path_2025 = OUTPUT / "obligations_2025.json"

    if not path_2025.exists():
        print("ERROR: 2025 obligations not found. Run extract_full.py first.")
        return
    if not path_2024.exists():
        print("ERROR: 2024 obligations not found. Run extract_2024.py first.")
        return

    print("Loading obligation graphs...")
    old = load_obligations(path_2024)
    new = load_obligations(path_2025)
    print(f"2024: {len(old)} obligations   2025: {len(new)} obligations")
    print("Matching (exact ID, then semantic for the rest)...")

    report = diff_obligations(old, new)

    report_path = OUTPUT / "change_impact_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    s = report["summary"]
    print(f"\n{'='*55}")
    print("CHANGE IMPACT REPORT: 2024 vs 2025")
    print(f"{'='*55}")
    print(f"  Total obligations 2024     : {s['total_2024']}")
    print(f"  Total obligations 2025     : {s['total_2025']}")
    print(f"  NEW obligations added      : {s['added']}")
    print(f"  Obligations REMOVED        : {s['removed']}")
    print(f"  Obligations MODIFIED       : {s['modified']}  (of which {s['modified_via_semantic_match']} caught only via semantic matching)")
    print(f"  Unchanged                  : {s['unchanged']}")
    print(f"\nFull report saved to: {report_path}")

    semantic_hits = [m for m in report["modified"] if m.get("match_type") == "semantic"]
    if semantic_hits:
        print(f"\n--- {len(semantic_hits)} obligation(s) recognized as the SAME obligation despite ID/wording changes ---")
        for m in semantic_hits:
            old_id = m["changes"]["obligation_id"]["before"]
            print(f"  {old_id}  ->  {m['obligation_id']}   (similarity {m['semantic_similarity']})")

if __name__ == "__main__":
    main()
