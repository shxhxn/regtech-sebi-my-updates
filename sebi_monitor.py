"""
Autonomous SEBI circular monitor -- the "perceive" stage of the agentic pipeline.
Checks SEBI's live master-circulars listing for the categories we track. If the
latest circular for a tracked category differs from what we last saw, it raises
a clear alert (and logs the event to the audit trail) instead of silently doing
nothing. This is real automation, not an LLM call -- it costs no API tokens.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from src.config import OUTPUT

LISTING_URL = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=6&smid=0"
TRACKED_CATEGORIES = ["Investment Advisers", "Stock Brokers"]
STATE_PATH = OUTPUT / "known_circulars.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

def fetch_listing_html():
    resp = requests.get(LISTING_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text

def parse_circulars(html, tracked_keywords):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        date_text = cells[0].get_text(strip=True)
        link = cells[1].find("a")
        if not link:
            continue
        title = link.get_text(strip=True)
        href = link.get("href", "")
        if re.match(r"[A-Za-z]{3} \d{1,2}, \d{4}", date_text):
            for kw in tracked_keywords:
                if kw.lower() in title.lower():
                    results.append({"category": kw, "date": date_text, "title": title, "url": href})
                    break
    return results

def latest_per_category(rows):
    latest = {}
    for r in rows:                     # SEBI's listing is newest-first
        if r["category"] not in latest:
            latest[r["category"]] = r
    return latest

def load_known_state():
    return json.load(open(STATE_PATH)) if STATE_PATH.exists() else {}

def save_known_state(state):
    OUTPUT.mkdir(exist_ok=True)
    json.dump(state, open(STATE_PATH, "w"), indent=2)

def main():
    print(f"Checking SEBI's master circulars listing for: {', '.join(TRACKED_CATEGORIES)}")
    try:
        html = fetch_listing_html()
    except Exception as e:
        print(f"ERROR fetching SEBI listing page: {e}")
        return

    rows = parse_circulars(html, TRACKED_CATEGORIES)
    latest = latest_per_category(rows)
    known = load_known_state()

    alerts = []
    for cat, row in latest.items():
        prev = known.get(cat)
        if prev is None or prev.get("url") != row["url"]:
            alerts.append((cat, prev, row))

    if not alerts:
        print("No changes detected -- all tracked circulars match the last known version.")
    else:
        print(f"\n{'='*60}")
        print(f"  {len(alerts)} CHANGE(S) DETECTED")
        print(f"{'='*60}")
        for cat, prev, row in alerts:
            prev_date = prev["date"] if prev else "(not previously tracked)"
            print(f"\n  Category : {cat}")
            print(f"  Was      : {prev_date}")
            print(f"  Now      : {row['date']}  -- {row['title']}")
            url = row['url'] if row['url'].startswith('http') else f"https://www.sebi.gov.in{row['url']}"
            print(f"  URL      : {url}")
            print(f"  ACTION   : download this circular and run extraction to update the obligation graph")

        try:
            from src.audit_log import append_event
            append_event("sebi_monitor_change_detected", {
                "changes": [{"category": c, "new_date": r["date"], "new_url": r["url"]} for c, _, r in alerts]
            })
        except ImportError:
            pass

    for cat, row in latest.items():
        known[cat] = {"date": row["date"], "title": row["title"], "url": row["url"],
                       "last_checked": datetime.now(timezone.utc).isoformat()}
    save_known_state(known)

if __name__ == "__main__":
    main()
