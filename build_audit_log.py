"""
Builds (or extends) the audit log from whatever pipeline outputs already exist
on disk, using each file's real modification time as the event timestamp.
Safe to re-run -- it won't duplicate an event_type that's already logged.
"""
import json
from datetime import datetime, timezone
from src.audit_log import append_event, load_log, verify_chain
from src.config import OUTPUT

def already_logged(event_type):
    return any(e["event_type"] == event_type for e in load_log())

def mtime_iso(path):
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()

def main():
    events_added = 0

    p = OUTPUT / "obligations_2025_verified.json"
    if not p.exists():
        p = OUTPUT / "obligations_2025.json"
    if p.exists() and not already_logged("extraction_2025"):
        data = json.load(open(p))
        grounded = sum(1 for o in data if o.get("grounding_band") == "grounded")
        flagged = sum(1 for o in data if o.get("grounding_band") == "flagged")
        append_event("extraction_2025", {
            "obligation_count": len(data),
            "grounded": grounded,
            "flagged_for_review": flagged,
            "source_circular": "SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/94"
        }, timestamp=mtime_iso(p))
        events_added += 1

    p = OUTPUT / "obligations_2024_verified.json"
    if not p.exists():
        p = OUTPUT / "obligations_2024.json"
    if p.exists() and not already_logged("extraction_2024"):
        data = json.load(open(p))
        append_event("extraction_2024", {
            "obligation_count": len(data),
            "source_circular": "SEBI/HO/MIRSD-PoD-1/P/CIR/2024/50"
        }, timestamp=mtime_iso(p))
        events_added += 1

    p = OUTPUT / "change_impact_report.json"
    if p.exists() and not already_logged("diff_2024_2025"):
        data = json.load(open(p))
        append_event("diff_2024_2025", data["summary"], timestamp=mtime_iso(p))
        events_added += 1

    p = OUTPUT / "compliance_register.json"
    if p.exists() and not already_logged("operations_register_built"):
        data = json.load(open(p))
        append_event("operations_register_built", {
            "register_rows": len(data)
        }, timestamp=mtime_iso(p))
        events_added += 1

    p = OUTPUT / "executable_rules.json"
    if p.exists() and not already_logged("executable_rules_built"):
        data = json.load(open(p))
        append_event("executable_rules_built", {
            "rule_count": len(data)
        }, timestamp=mtime_iso(p))
        events_added += 1

    print(f"Added {events_added} new event(s) to the audit log.")
    log = load_log()
    print(f"Total events in chain: {len(log)}")

    valid, broken_at = verify_chain()
    print(f"Chain integrity check: {'VALID' if valid else f'BROKEN at index {broken_at}'}")

    print("\n--- Event log ---")
    for e in log:
        print(f"  [{e['index']}] {e['timestamp'][:19]}  {e['event_type']:28s} {e['details']}")

if __name__ == "__main__":
    main()
