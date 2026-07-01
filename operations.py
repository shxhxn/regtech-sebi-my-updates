"""
Operations Layer -- turns the static obligation graph into a working compliance
SYSTEM: a register to track fulfilment status, executable rule objects a real
system could enforce, and a calendar view grouped by how often each obligation
recurs. This directly targets SEBI's second named challenge: "ongoing compliance
management... mapping each obligation to evidence of fulfilment, maintaining
audit trails, and identifying compliance gaps."
"""
import json
from datetime import datetime
from pathlib import Path
from src.config import OUTPUT

# Deterministic, keyword-based risk scoring -- same "no AI in the check itself"
# philosophy as the grounding verifier: explainable and reproducible, every
# obligation's band traces back to a specific reason, not a black-box score.
# A real compliance/legal team would refine these weights; this is a
# reasonable, defensible starting point, not a definitive regulatory opinion.
CRITICAL_KEYWORDS = [
    "shall not", "prohibited", "penalty", "suspension", "cancellation",
    "fraud", "mis-sell", "misselling", "client fund", "client money",
    "segregat", "misappropriat", "money laundering", "insider trading",
]
HIGH_KEYWORDS = [
    "disclos", "risk profil", "fee", "conflict of interest", "grievance",
    "advertisement", "misleading", "suitability", "kyc", "consent",
]

def score_risk(ob):
    """Critical/High: content-based, from keywords signalling enforcement
    teeth or client-harm potential. Medium: has a real deadline or recurring
    cadence but no red-flag content. Low: everything else (mostly
    administrative/record-keeping duties)."""
    text = " ".join([
        ob.get("required_action") or "",
        ob.get("verbatim_text") or "",
        ob.get("trigger") or "",
        ob.get("title") or "",
    ]).lower()

    if any(k in text for k in CRITICAL_KEYWORDS):
        return "Critical"
    if any(k in text for k in HIGH_KEYWORDS):
        return "High"
    if ob.get("deadline") or ob.get("frequency") in ("monthly", "quarterly", "half_yearly", "annual", "event_driven"):
        return "Medium"
    return "Low"

def load_obligations():
    path = OUTPUT / "obligations_2025_verified.json"
    if not path.exists():
        path = OUTPUT / "obligations_2025.json"
    return path, json.load(open(path))

def build_register(obligations):
    """One row per obligation: status, owner, evidence, audit fields.
    Status starts 'pending_review' -- this is the live system a real firm
    would populate; we ship the structure, not fabricated firm data."""
    register = []
    for ob in obligations:
        register.append({
            "obligation_id": ob["obligation_id"],
            "title": ob["title"],
            "status": "pending_review",          # pending_review | compliant | overdue | not_applicable
            "owner": "",
            "evidence_attached": False,
            "evidence_notes": "",
            "last_reviewed": None,
            "frequency": ob.get("frequency"),
            "deadline": ob.get("deadline"),
            "source_clause": ob.get("source_clause"),
            "risk_band": ob.get("risk_band"),
            "confidence_band": ob.get("grounding_band", "Unverified"),
        })
    return register

def build_executable_rules(obligations):
    """Each obligation becomes a machine-actionable rule object: trigger,
    required evidence, deadline logic, and an action if the rule is breached.
    This is the literal artifact the problem statement asks for: 'programmable,
    auditable compliance logic' -- not prose, a structured object a real
    compliance engine could ingest and enforce."""
    rules = []
    for ob in obligations:
        rules.append({
            "rule_id": f"rule-{ob['obligation_id']}",
            "obligation_id": ob["obligation_id"],
            "applies_to": ob.get("applies_to", []),
            "trigger": ob.get("trigger"),
            "required_action": ob.get("required_action"),
            "required_evidence": ob.get("evidence"),
            "frequency": ob.get("frequency"),
            "deadline_rule": ob.get("deadline") or "not time-bound",
            "on_breach": "flag_for_compliance_review",
            "source_clause": ob.get("source_clause"),
            "source_circular": ob.get("source_circular"),
        })
    return rules

def build_calendar(obligations):
    """Group obligations by recurrence so a compliance officer can see,
    at a glance, what category of obligation needs attention how often."""
    buckets = {}
    for ob in obligations:
        freq = ob.get("frequency", "not_specified")
        buckets.setdefault(freq, []).append({
            "obligation_id": ob["obligation_id"],
            "title": ob["title"],
            "deadline": ob.get("deadline"),
        })
    order = ["monthly", "quarterly", "half_yearly", "annual", "event_driven", "one_time", "ongoing", "not_specified"]
    return {k: buckets[k] for k in order if k in buckets}

def main():
    src_path, obligations = load_obligations()
    print(f"Loaded {len(obligations)} obligations from {src_path.name}.\n")

    # Score risk and write it directly onto each obligation, persisted back to
    # the same file we loaded from. The dashboard reads risk_band straight off
    # the obligation records (not from the register JSON) -- this write-back
    # is what actually makes the risk badges and distribution bar appear.
    for ob in obligations:
        ob["risk_band"] = score_risk(ob)
    json.dump(obligations, open(src_path, "w"), indent=2)

    register = build_register(obligations)
    rules = build_executable_rules(obligations)
    calendar = build_calendar(obligations)

    OUTPUT.mkdir(exist_ok=True)
    json.dump(register, open(OUTPUT / "compliance_register.json", "w"), indent=2)
    json.dump(rules, open(OUTPUT / "executable_rules.json", "w"), indent=2)
    json.dump(calendar, open(OUTPUT / "compliance_calendar.json", "w"), indent=2)

    risk_counts = {}
    for ob in obligations:
        risk_counts[ob["risk_band"]] = risk_counts.get(ob["risk_band"], 0) + 1

    print(f"Risk scored          : {dict(sorted(risk_counts.items()))}")
    print(f"                      -> written back into {src_path.name}")
    print(f"Compliance register : {len(register)} rows  -> output/compliance_register.json")
    print(f"Executable rules     : {len(rules)} rules  -> output/executable_rules.json")
    print(f"Calendar buckets     : {list(calendar.keys())}")
    print("                       -> output/compliance_calendar.json")

    print(f"\n--- Calendar breakdown ---")
    for freq, items in calendar.items():
        print(f"  {freq:15s} : {len(items)} obligation(s)")

    print(f"\n--- Sample executable rule ---")
    print(json.dumps(rules[0], indent=2))

if __name__ == "__main__":
    main()
