import json
from pathlib import Path
from src.config import OUTPUT

def load_obligations(path: str) -> dict:
    """Load obligations from JSON and index them by obligation_id."""
    with open(path) as f:
        data = json.load(f)
    return {ob["obligation_id"]: ob for ob in data}

def normalize_id(ob_id: str) -> str:
    """Strip trailing numbers so we can match ia-risk-01 with ia-risk-02."""
    parts = ob_id.rsplit("-", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0]
    return ob_id

def diff_obligations(old: dict, new: dict) -> dict:
    """Compare two obligation graphs and return a structured change report."""

    old_ids = set(old.keys())
    new_ids = set(new.keys())

    # Exact ID matches
    added_ids = new_ids - old_ids
    removed_ids = old_ids - new_ids
    common_ids = old_ids & new_ids

    # Find modified obligations (same ID, different content)
    modified = []
    unchanged = []
    for ob_id in common_ids:
        old_ob = old[ob_id]
        new_ob = new[ob_id]
        changes = {}
        for field in ["title", "summary", "required_action", "evidence", "frequency", "deadline", "verbatim_text"]:
            if old_ob.get(field) != new_ob.get(field):
                changes[field] = {
                    "before": old_ob.get(field),
                    "after": new_ob.get(field)
                }
        if changes:
            modified.append({
                "obligation_id": ob_id,
                "title": new_ob["title"],
                "changes": changes
            })
        else:
            unchanged.append(ob_id)

    return {
        "summary": {
            "total_2024": len(old),
            "total_2025": len(new),
            "added": len(added_ids),
            "removed": len(removed_ids),
            "modified": len(modified),
            "unchanged": len(unchanged)
        },
        "added": [new[i] for i in sorted(added_ids)],
        "removed": [old[i] for i in sorted(removed_ids)],
        "modified": modified,
        "unchanged": sorted(unchanged)
    }

def main():
    path_2024 = OUTPUT / "obligations_2024.json"
    path_2025 = OUTPUT / "obligations_2025.json"

    if not path_2025.exists():
        print("ERROR: obligations_2025.json not found. Run extract_full.py first.")
        return

    if not path_2024.exists():
        print("ERROR: obligations_2024.json not found. Run extract_full.py on the 2024 circular first.")
        return

    print("Loading obligation graphs...")
    old = load_obligations(path_2024)
    new = load_obligations(path_2025)

    print(f"2024: {len(old)} obligations")
    print(f"2025: {len(new)} obligations")

    report = diff_obligations(old, new)

    # Save report
    report_path = OUTPUT / "change_impact_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    s = report["summary"]
    print(f"\n{'='*50}")
    print(f"CHANGE IMPACT REPORT: 2024 vs 2025")
    print(f"{'='*50}")
    print(f"  Total obligations 2024 : {s['total_2024']}")
    print(f"  Total obligations 2025 : {s['total_2025']}")
    print(f"  NEW obligations added  : {s['added']}")
    print(f"  Obligations REMOVED    : {s['removed']}")
    print(f"  Obligations MODIFIED   : {s['modified']}")
    print(f"  Unchanged              : {s['unchanged']}")
    print(f"\nFull report saved to: {report_path}")

    # Print modified details
    if report["modified"]:
        print(f"\nMODIFIED OBLIGATIONS:")
        for ob in report["modified"]:
            print(f"\n  [{ob['obligation_id']}] {ob['title']}")
            for field, change in ob["changes"].items():
                print(f"    {field}:")
                print(f"      BEFORE: {change['before']}")
                print(f"      AFTER : {change['after']}")

    # Print new obligations
    if report["added"]:
        print(f"\nNEW OBLIGATIONS IN 2025:")
        for ob in report["added"]:
            print(f"  + [{ob['obligation_id']}] {ob['title']}")

    # Print removed obligations
    if report["removed"]:
        print(f"\nOBLIGATIONS REMOVED IN 2025:")
        for ob in report["removed"]:
            print(f"  - [{ob['obligation_id']}] {ob['title']}")

if __name__ == "__main__":
    main()