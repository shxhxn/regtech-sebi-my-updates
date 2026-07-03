"""
Turns change_impact_report.json's added/modified obligations into a compact
executive narrative -- reusing the same Ollama setup and extract_structured()
wrapper extract_full.py already uses, just with a different Pydantic schema
and a much smaller prompt (diff entries only, never the full circular text).

    python change_narrative.py
"""
import json
from typing import List, Literal

from pydantic import BaseModel, Field

from src.config import OUTPUT, EXTRACTION_MODEL
from src.llm import extract_structured
from src.audit_log import append_event

PROMPT = """You are a SEBI compliance analyst writing an executive summary of a change-impact
report -- not a full obligation list, just what changed between the previous circular and
the new one. Below are only the ADDED and MODIFIED obligations from the diff (unchanged and
merely-reworded items are omitted as noise).

ADDED ({n_added}):
{added}

MODIFIED ({n_modified}):
{modified}

Based only on this, provide:
- an overall severity (Low/Medium/High/Critical) for firms subject to these obligations
- a short "what changed" narrative (2-4 sentences)
- "why it matters" (2-3 sentences on the business/compliance impact)
- who's affected -- the distinct intermediary types these obligations apply to
- required actions -- a de-duplicated list of the concrete actions firms must now take
"""


class ChangeNarrative(BaseModel):
    severity: Literal["Low", "Medium", "High", "Critical"]
    what_changed: str = Field(description="Short narrative of what changed in this circular")
    why_it_matters: str = Field(description="Business/compliance impact of the change")
    whos_affected: List[str] = Field(description="Intermediary types affected, e.g. investment_adviser")
    required_actions: List[str] = Field(description="Aggregated, de-duplicated required actions")


def _format_added(added):
    lines = [
        f"- [{o.get('obligation_id')}] {o.get('title')}: {o.get('required_action', '')}  "
        f"(applies_to: {o.get('applies_to')})"
        for o in added
    ]
    return "\n".join(lines) or "(none)"


def _format_modified(modified):
    lines = [
        f"- [{o.get('obligation_id')}] {o.get('title')}: changed fields = "
        f"{', '.join(o.get('changes', {}).keys())}"
        for o in modified
    ]
    return "\n".join(lines) or "(none)"


def main():
    report_path = OUTPUT / "change_impact_report.json"
    if not report_path.exists():
        print("No change_impact_report.json found. Run the diff step first.")
        return

    report = json.load(open(report_path))
    added = report.get("added", [])
    modified = report.get("modified", [])

    if not added and not modified:
        print("No added or modified obligations in the change report -- nothing to narrate.")
        return

    prompt = PROMPT.format(
        n_added=len(added), added=_format_added(added),
        n_modified=len(modified), modified=_format_modified(modified),
    )

    print(f"Generating change narrative from {len(added)} added + {len(modified)} modified obligation(s)...")
    result = extract_structured(prompt, ChangeNarrative, model=EXTRACTION_MODEL)
    narrative = result.model_dump()

    out_path = OUTPUT / "change_narrative.json"
    json.dump(narrative, open(out_path, "w"), indent=2)
    print(f"Severity: {narrative['severity']}")
    print(f"Saved -> {out_path}")

    append_event("change_narrative_generated", {
        "severity": narrative["severity"],
        "added_count": len(added),
        "modified_count": len(modified),
    })


if __name__ == "__main__":
    main()
