"""
Enrichment Layer -- adds risk scoring and department ownership to every
obligation, and produces an executive summary. All deterministic, zero API
tokens. Reads the verified obligations and writes an enriched copy plus a
dashboard summary. Department mapping is rule-based here and can be replaced
by an LLM classification later without changing anything downstream.
"""
import json
from src.config import OUTPUT

PENALTY_WORDS = ["penal", "penalty", "liable", "prosecut", "cancel", "suspend",
                 "fine", "imprison", "action shall be taken", "debar"]
URGENT_FREQ = {"event_driven", "one_time"}

DEPT_RULES = [
    ("Finance",            ["fee", "payment", "bank", "invoice", "refund", "cash", "neft", "rtgs", "advance"]),
    ("Compliance/Audit",   ["audit", "compliance", "record", "register", "report to", "iaasb", "inspection", "certificate"]),
    ("Legal",              ["agreement", "regulation", "consent", "terms and conditions", "code of conduct", "undertaking", "fiduciary"]),
    ("Client Onboarding",  ["kyc", "risk profil", "suitability", "onboard", "client eligibility"]),
    ("Technology/InfoSec", ["website", "cyber", "system", "data", "mobile app", "technolog", "software"]),
    ("Investor Relations", ["complaint", "grievance", "scores", "odr", "investor", "disclosure"]),
]

def has_penalty_language(ob):
    blob = " ".join(str(ob.get(f, "")) for f in ["verbatim_text", "required_action", "summary", "trigger"]).lower()
    return any(w in blob for w in PENALTY_WORDS)

def risk_score(ob):
    score = 0
    if has_penalty_language(ob):
        score += 2
    if (ob.get("deadline") or "").strip():
        score += 1
    if ob.get("frequency") in URGENT_FREQ:
        score += 1
    if ob.get("frequency") == "ongoing":
        score += 1
    band = "Critical" if score >= 3 else "High" if score == 2 else "Medium" if score == 1 else "Low"
    return band, score

def map_department(ob):
    blob = " ".join(str(ob.get(f, "")) for f in ["title", "summary", "required_action", "trigger", "evidence"]).lower()
    scores = {}
    for dept, kws in DEPT_RULES:
        hits = sum(1 for kw in kws if kw in blob)
        if hits:
            scores[dept] = hits
    return max(scores, key=scores.get) if scores else "General Compliance"

def main():
    path = OUTPUT / "obligations_2025_verified.json"
    if not path.exists():
        path = OUTPUT / "obligations_2025.json"
    if not path.exists():
        print("No obligations found. Run extract_full.py first.")
        return

    obligations = json.load(open(path))

    risk_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    dept_counts = {}
    for ob in obligations:
        band, sc = risk_score(ob)
        dept = map_department(ob)
        ob["risk_band"] = band
        ob["risk_points"] = sc
        ob["department"] = dept
        risk_counts[band] += 1
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    # write enriched obligations back to the verified file so every tab benefits
    json.dump(obligations, open(path, "w"), indent=2)

    # executive summary for the dashboard cards
    n = len(obligations)
    grounded = sum(1 for o in obligations if o.get("grounding_band") == "grounded")
    partial = sum(1 for o in obligations if o.get("grounding_band") == "partial")
    with_deadline = sum(1 for o in obligations if (o.get("deadline") or "").strip())
    summary = {
        "total_obligations": n,
        "high_or_critical_risk": risk_counts["Critical"] + risk_counts["High"],
        "with_explicit_deadline": with_deadline,
        "verifiably_traceable_pct": round(100 * (grounded + partial) / n, 1) if n else 0,
        "risk_breakdown": risk_counts,
        "department_breakdown": dict(sorted(dept_counts.items(), key=lambda x: -x[1])),
    }
    json.dump(summary, open(OUTPUT / "executive_summary.json", "w"), indent=2)

    print(f"Enriched {n} obligations.\n")
    print("Risk breakdown:")
    for band in ["Critical", "High", "Medium", "Low"]:
        print(f"  {band:9s}: {risk_counts[band]}")
    print("\nDepartment breakdown:")
    for dept, c in sorted(dept_counts.items(), key=lambda x: -x[1]):
        print(f"  {dept:22s}: {c}")
    print(f"\nWrote enriched obligations -> {path.name}")
    print(f"Wrote executive summary    -> executive_summary.json")

if __name__ == "__main__":
    main()
