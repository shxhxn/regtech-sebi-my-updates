#!/usr/bin/env python3
"""
Fixes "Register status overview" in the Pipeline Operations tab, which was
reading from compliance_register.json's "status" field -- hardcoded to
"pending_review" for every row by operations.py and never updated -- instead
of from compliance_status.json, the file My Register actually writes to when
you mark something Compliant/In progress/N/A. As shipped, this stat could
never show anything but 100% pending_review, contradicting whatever you'd
actually marked elsewhere in the app.

Safety: same pattern as fix_dashboard_casing.py -- the target block is
checked to occur EXACTLY once before anything is written. Aborts cleanly
otherwise.

Usage:
    cd ~/Projects/sebi-regtech
    python3 fix_register_status.py
"""
import sys
from pathlib import Path

TARGET = Path("dashboard.py")

OLD = '''        statuses = {}
        for r_ in register:
            statuses[r_["status"]] = statuses.get(r_["status"], 0) + 1
        st.write(statuses)'''

NEW = '''        saved_status = load_json("compliance_status.json") or {}
        statuses = {}
        for r_ in register:
            live_status = saved_status.get(r_["obligation_id"], "Not started")
            statuses[live_status] = statuses.get(live_status, 0) + 1
        st.write(statuses)'''

def main():
    if not TARGET.exists():
        sys.exit(f"Can't find {TARGET} in the current directory -- run this from your project root.")

    text = TARGET.read_text()
    n = text.count(OLD)
    if n != 1:
        print(f"Aborting -- nothing written. Expected 1 match, found {n}.")
        print("Your dashboard.py doesn't match what this script expects -- fix by hand instead,")
        print("or send me your current dashboard.py and I'll regenerate this.")
        sys.exit(1)

    TARGET.write_text(text.replace(OLD, NEW))
    print("Applied 1/1 fix to dashboard.py -- Register status overview now reads live status.")
    print("Restart Streamlit (or let it hot-reload) to see the change.")

if __name__ == "__main__":
    main()
