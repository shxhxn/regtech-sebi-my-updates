from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from enum import Enum


class IntermediaryType(str, Enum):
    investment_adviser = "investment_adviser"
    stock_broker = "stock_broker"
    research_analyst = "research_analyst"


class Frequency(str, Enum):
    one_time = "one_time"
    ongoing = "ongoing"
    monthly = "monthly"
    quarterly = "quarterly"
    half_yearly = "half_yearly"
    annual = "annual"
    event_driven = "event_driven"
    not_specified = "not_specified"


class Obligation(BaseModel):
    obligation_id: str = Field(description="Short slug, e.g. 'ia-risk-profiling-01'")
    title: str = Field(description="Short human-readable name of the obligation")
    summary: str = Field(description="Plain-language description of what the IA must do")
    applies_to: List[IntermediaryType] = Field(description="Which intermediary categories this binds")
    trigger: str = Field(description="The condition that makes this obligation apply")
    required_action: str = Field(description="The concrete action required to comply")
    evidence: str = Field(description="What record or document would prove this is met")
    frequency: Frequency
    deadline: Optional[str] = Field(default=None, description="Explicit time limit e.g. 'within 30 days', else null")
    source_clause: str = Field(description="Exact clause/para number, e.g. 'Para 7.2'")
    source_circular: str = Field(description="Circular number and date this came from")
    verbatim_text: str = Field(description="Exact sentence(s) from the circular stating this obligation")

    @model_validator(mode="before")
    @classmethod
    def fix_obligation_id_typo(cls, data):
        """
        The 7B model occasionally misspells the 'obligation_id' KEY itself
        (seen in practice: 'obligigation_id'). If the correct key is missing
        but a near-miss variant is present, rename it instead of dropping the
        whole obligation over a typo in a key name.
        """
        if isinstance(data, dict) and not data.get("obligation_id"):
            for key in list(data.keys()):
                kl = key.lower()
                if key != "obligation_id" and "oblig" in kl and "id" in kl:
                    data["obligation_id"] = data.pop(key)
                    break
        return data

    @field_validator("verbatim_text", "source_clause", "source_circular", mode="before")
    @classmethod
    def coerce_list_to_str(cls, v):
        """
        The 7B model sometimes returns these fields as a list of strings
        instead of a single string (happens on bullet-point source text).
        Join rather than crash so the rest of the chunk's obligations survive.
        """
        if isinstance(v, list):
            return " ".join(str(item) for item in v)
        return v

    @field_validator("applies_to", mode="before")
    @classmethod
    def filter_invalid_intermediary(cls, v):
        """
        The 7B model occasionally hallucinates enum values not in our schema
        (e.g. 'portfolio_manager'). Filter out unknowns instead of crashing the
        whole obligation -- an empty list is better than losing a valid record.
        """
        if not isinstance(v, list):
            return v
        valid = {e.value for e in IntermediaryType}
        return [item for item in v if item in valid]

    @field_validator("frequency", mode="before")
    @classmethod
    def coerce_invalid_frequency(cls, v):
        """
        The 7B model sometimes invents compound frequency values not in our
        enum (e.g. 'one_time_and_on_request', 'initial_and_on_request')
        instead of picking one. Map to the closest valid value rather than
        crashing the whole chunk -- an imperfect frequency beats losing the
        obligation entirely.
        """
        if isinstance(v, str):
            valid = {e.value for e in Frequency}
            if v in valid:
                return v
            vl = v.lower()
            if "request" in vl or "trigger" in vl or "event" in vl:
                return "event_driven"
            if "one_time" in vl or "onetime" in vl or "one-time" in vl:
                return "one_time"
            if "ongoing" in vl or "continuous" in vl:
                return "ongoing"
            if "quarter" in vl:
                return "quarterly"
            if "half" in vl and "year" in vl:
                return "half_yearly"
            if "month" in vl:
                return "monthly"
            if "annual" in vl or "year" in vl:
                return "annual"
            return "not_specified"
        return v


class ObligationList(BaseModel):
    obligations: List[Obligation]

    @model_validator(mode="before")
    @classmethod
    def drop_unsalvageable_items(cls, data):
        """
        The model occasionally corrupts ONE obligation in an otherwise-good
        batch -- e.g. an unescaped quote inside verbatim_text breaks the
        object boundary, spilling the rest of that object's content out as
        stray, malformed array elements (still syntactically valid JSON,
        just the wrong shape). Pydantic's default behaviour fails the WHOLE
        list over that one bad item, discarding perfectly good sibling
        obligations along with it.

        Instead: validate each item independently (still running every
        per-field coercion defined on Obligation above) and keep only the
        ones that pass. A single corrupted entry now costs just itself.
        """
        if not isinstance(data, dict):
            return data
        raw_items = data.get("obligations")
        if not isinstance(raw_items, list):
            return data
        kept = []
        dropped = 0
        for item in raw_items:
            if not isinstance(item, dict):
                dropped += 1
                continue
            try:
                kept.append(Obligation.model_validate(item))
            except Exception:
                dropped += 1
                continue
        if dropped:
            print(f"  [schema] dropped {dropped} unsalvageable obligation(s) from this response, kept {len(kept)}")
        data["obligations"] = kept
        return data
