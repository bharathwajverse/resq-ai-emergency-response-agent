"""
ResQ-AI Horn Clause Rules and Canonical Emergency Rule Catalog.
Module V: Classical Logical Inference.

Defines the HornRule model, the 8 canonical operational Horn clauses (R1-R8),
priority escalation rules, and backwards-compatible legacy Rule models.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from app.inference.facts import Fact


# ============================================================================
# Legacy Pydantic Rule (Retained for Orchestrator Backward Compatibility)
# ============================================================================

class Rule(BaseModel):
    condition: str
    action: str


PREDEFINED_RULES = [
    Rule(condition="victim_count > 5 and severity == 'high'", action="priority = 'critical'"),
    Rule(condition="road_blocked == True", action="avoid_blocked_routes = True"),
    Rule(condition="hospital_capacity <= 0", action="hospital_status = 'unavailable'"),
    Rule(condition="ambulance_available == True and ambulance_capacity >= victim_count", action="ambulance_status = 'feasible'"),
]


# ============================================================================
# Formal Horn Clause Rule Representation
# ============================================================================

class HornRule:
    """
    Represents a definite Horn clause:
    P1 ^ P2 ^ ... ^ Pk => C
    
    where each Pi is an antecedent premise Fact and C is the consequent head Fact.
    """

    def __init__(
        self,
        rule_id: str,
        name: str,
        premises: List[Fact],
        consequent: Fact,
        description: str = "",
    ):
        self.rule_id = rule_id
        self.name = name
        self.premises = list(premises)
        self.consequent = consequent
        self.description = description

    @property
    def variables(self) -> Set[str]:
        """Returns set of all variable symbols present across premises and consequent."""
        vars_set: Set[str] = set()
        for p in self.premises:
            vars_set.update(p.variables)
        vars_set.update(self.consequent.variables)
        return vars_set

    def instantiate(self, bindings: Dict[str, str]) -> HornRule:
        """Returns a new HornRule with variables substituted by bindings."""
        new_premises = [p.substitute(bindings) for p in self.premises]
        new_consequent = self.consequent.substitute(bindings)
        return HornRule(
            rule_id=self.rule_id,
            name=self.name,
            premises=new_premises,
            consequent=new_consequent,
            description=self.description,
        )

    def to_cnf_clause(self) -> Set[str]:
        """
        Converts this Horn clause into CNF propositional/ground literal set:
        (not P1 or not P2 or ... or C).
        """
        literals: Set[str] = set()
        for p in self.premises:
            p_str = str(p)
            neg = p_str[1:] if p_str.startswith("~") else f"~{p_str}"
            literals.add(neg)
        literals.add(str(self.consequent))
        return literals

    def to_string(self) -> str:
        premises_str = " AND ".join(str(p) for p in self.premises) if self.premises else "TRUE"
        return f"IF {premises_str} THEN {str(self.consequent)}"

    def __str__(self) -> str:
        return f"{self.rule_id} [{self.name}]: {self.to_string()}"

    def __repr__(self) -> str:
        return f"HornRule({self.rule_id}, {self.name}, {self.to_string()})"


# ============================================================================
# The 8 Canonical Emergency Horn Clause Rules (R1 - R8)
# ============================================================================

R1_LANDSLIDE = HornRule(
    rule_id="R1",
    name="Landslide Risk",
    premises=[Fact("HeavyRain"), Fact("MountainRoad", ("?r",))],
    consequent=Fact("HighLandslideRisk", ("?r",)),
    description="Severe downpours on steep terrain trigger landslide warning protocols.",
)

R2_TRAUMA_CENTER = HornRule(
    rule_id="R2",
    name="Trauma Center Required",
    premises=[Fact("SevereInjuries")],
    consequent=Fact("TraumaCenterRequired"),
    description="Multi-casualty incidents mandate routing to Level 1 Trauma Center.",
)

R3_ROAD_IMPASSABLE = HornRule(
    rule_id="R3",
    name="Road Impassability",
    premises=[Fact("RoadFlooded", ("?r",))],
    consequent=Fact("RoadImpassable", ("?r",)),
    description="Submerged road segments cannot be traversed by emergency vehicles.",
)

R4_REROUTE = HornRule(
    rule_id="R4",
    name="Reroute Trigger",
    premises=[Fact("RoadImpassable", ("?r",)), Fact("OnDispatchRoute", ("?r",))],
    consequent=Fact("RerouteRequired"),
    description="Blocked edges on an active transit path force path invalidation and rerouting.",
)

R5_HAZMAT = HornRule(
    rule_id="R5",
    name="Hazmat Protocol",
    premises=[Fact("Fire"), Fact("ChemicalWarehouse")],
    consequent=Fact("HazmatProtocol"),
    description="Industrial chemical fires require hazardous materials containment response.",
)

R6_DISPATCH_DELAY = HornRule(
    rule_id="R6",
    name="Dispatch Delay",
    premises=[Fact("HighTraffic"), Fact("RushHour")],
    consequent=Fact("DispatchDelayLikely"),
    description="Coincident traffic congestion and peak hours increase expected transit duration.",
)

R7_REFUEL = HornRule(
    rule_id="R7",
    name="Ambulance Refuel",
    premises=[Fact("LowFuel", ("?a",))],
    consequent=Fact("RefuelRequired", ("?a",)),
    description="Ambulances below 20% fuel cannot be safely dispatched without prior refuel.",
)

R8_HOSPITAL_DIVERT = HornRule(
    rule_id="R8",
    name="Hospital Diversion",
    premises=[Fact("CriticalIncident"), Fact("HospitalAtCapacity", ("?h",))],
    consequent=Fact("DivertToSecondaryHospital", ("?h",)),
    description="Saturated emergency rooms force diversion of critical patients to backup clinics.",
)


# ============================================================================
# Auxiliary Priority & Operational Rules (R9 - R11)
# ============================================================================

R9_CRITICAL_PRIORITY = HornRule(
    rule_id="R9",
    name="Critical Priority Escalation",
    premises=[Fact("SevereInjuries"), Fact("HighSeverity")],
    consequent=Fact("Priority", ("critical",)),
    description="Severe injuries coupled with high severity escalate incident priority to critical.",
)

R10_HIGH_PRIORITY = HornRule(
    rule_id="R10",
    name="High Priority Escalation",
    premises=[Fact("TraumaCenterRequired")],
    consequent=Fact("Priority", ("high",)),
    description="Trauma center requirement mandates high incident priority.",
)

R11_AVOID_BLOCKED = HornRule(
    rule_id="R11",
    name="Avoid Blocked Route",
    premises=[Fact("RoadBlocked", ("?r",))],
    consequent=Fact("AvoidRoute", ("?r",)),
    description="Identified road blockages must be avoided by routing algorithms.",
)


CANONICAL_HORN_RULES: List[HornRule] = [
    R1_LANDSLIDE,
    R2_TRAUMA_CENTER,
    R3_ROAD_IMPASSABLE,
    R4_REROUTE,
    R5_HAZMAT,
    R6_DISPATCH_DELAY,
    R7_REFUEL,
    R8_HOSPITAL_DIVERT,
]

ALL_OPERATIONAL_RULES: List[HornRule] = [
    R1_LANDSLIDE,
    R2_TRAUMA_CENTER,
    R3_ROAD_IMPASSABLE,
    R4_REROUTE,
    R5_HAZMAT,
    R6_DISPATCH_DELAY,
    R7_REFUEL,
    R8_HOSPITAL_DIVERT,
    R9_CRITICAL_PRIORITY,
    R10_HIGH_PRIORITY,
    R11_AVOID_BLOCKED,
]

CANONICAL_RULES = CANONICAL_HORN_RULES
