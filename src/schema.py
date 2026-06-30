from pydantic import BaseModel, Field, field_validator
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
        The 7B model occasionally halluccinates enum values not in our schema
        (e.g. 'portfolio_manager'). Filter out unknowns instead of crashing the
        whole obligation -- an empty list is better than losing a valid record.
        """
        if not isinstance(v, list):
            return v
        valid = {e.value for e in IntermediaryType}
        return [item for item in v if item in valid]


class ObligationList(BaseModel):
    obligations: List[Obligation]
