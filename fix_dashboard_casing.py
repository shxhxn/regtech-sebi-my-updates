#!/usr/bin/env python3
"""
Applies the header-casing fixes to dashboard.py so every tab's #### body
header matches its tab label (Title Case) -- the "My register" vs "My
Register" mismatch, plus five siblings it shares the same pattern with.

Safety: every target string is checked to occur EXACTLY once in the file
before anything is written. If a target isn't found exactly once -- meaning
your local dashboard.py has already diverged from what this script expects --
it aborts with a clear message instead of guessing. Nothing is written unless
every single check passes first.

Usage:
    cd ~/Projects/sebi-regtech
    python3 fix_dashboard_casing.py
"""
import sys
from pathlib import Path

TARGET = Path("dashboard.py")

REPLACEMENTS = [
    ('st.markdown("#### What\'s due")',          'st.markdown("#### What\'s Due")'),
    ('st.markdown("#### What changed - 2024 to 2025")', 'st.markdown("#### What Changed - 2024 to 2025")'),
    ('st.markdown("#### My register")',          'st.markdown("#### My Register")'),
    ('st.markdown("#### All obligations")',      'st.markdown("#### All Obligations")'),
    ('st.markdown("#### Pipeline operations")',  'st.markdown("#### Pipeline Operations")'),
    ('st.markdown("#### Executive overview")',   'st.markdown("#### Executive Overview")'),
    ('st.markdown("#### Trust & verification")', 'st.markdown("#### Trust & Verification")'),
    ('st.markdown("#### Audit trail")',          'st.markdown("#### Audit Trail")'),
]

def main():
    if not TARGET.exists():
        sys.exit(f"Can't find {TARGET} in the current directory -- run this from your project root.")

    text = TARGET.read_text()
    problems = []
    for old, _ in REPLACEMENTS:
        n = text.count(old)
        if n != 1:
            problems.append(f"  expected 1 match, found {n}: {old!r}")

    if problems:
        print("Aborting -- nothing written. dashboard.py doesn't match what this script expects:")
        print("\n".join(problems))
        print("\nFix these lines by hand instead, or send me your current dashboard.py and I'll regenerate this.")
        sys.exit(1)

    for old, new in REPLACEMENTS:
        text = text.replace(old, new)

    TARGET.write_text(text)
    print(f"Applied {len(REPLACEMENTS)}/{len(REPLACEMENTS)} header fixes to {TARGET}.")
    print("Restart Streamlit (or let it hot-reload) to see the change.")
    print("Safe to delete this script afterward -- it's a one-time patch, not part of the pipeline.")

if __name__ == "__main__":
    main()
