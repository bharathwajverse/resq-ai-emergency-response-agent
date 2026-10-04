"""
ResQ-AI Uncertainty & Bayesian Risk Schemas.
Pydantic v2 schemas for probabilistic risk reasoning and exact Bayesian inference.
"""

from enum import Enum
from typing import Dict
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskAnalysisRequest(BaseModel):
    weather: str = "Clear"
    road_condition: str = "Clear"
    victim_count: int = Field(default=1, ge=0)
    concurrent_incidents: int = Field(default=1, ge=1)


class RiskAnalysisResponse(BaseModel):
    delay_prob_given_rain: float = Field(..., description="P(Delay=Severe | Weather=HeavyStorm)")
    high_severity_prob_given_victims: float = Field(..., description="P(Severity=Critical | Victims > 5)")
    hospital_overload_prob: float = Field(..., description="P(Hospital=Overloaded | Incidents > 1)")
    composite_risk_score: float = Field(..., ge=0.0, le=100.0, description="Composite score 0-100")
    risk_level: RiskLevel
    factor_contributions: Dict[str, float]
    disclaimer: str = "Educational simulation - not for real-world emergency dispatch."
    execution_time_ms: float
