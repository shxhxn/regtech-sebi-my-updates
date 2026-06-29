from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class IntermediaryType(str, Enum):
    investment_adviser = "investment_adviser"
    stock_broker = "stock_broker"
    research_analyst = "research_analyst"

class Frequency(str, Enum):
    one_time = "one_time"
    ongoing = "ongoing"
    quarterly = "quarterly"
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

class ObligationList(BaseModel):
    obligations: List[Obligation]
