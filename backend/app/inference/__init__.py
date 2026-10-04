"""
ResQ-AI Module V: Classical Logical Inference Package.

Exports:
- Fact, WorkingMemory
- HornRule, Rule, PREDEFINED_RULES, CANONICAL_HORN_RULES, ALL_OPERATIONAL_RULES
- ForwardChainingEngine
- BackwardChainingEngine
- PropositionalResolutionEngine, resolve, demonstrate_resolution
- InferenceEngine (Unified Façade)
"""

from app.inference.facts import Fact, WorkingMemory
from app.inference.rules import (
    HornRule,
    Rule,
    PREDEFINED_RULES,
    CANONICAL_HORN_RULES,
    ALL_OPERATIONAL_RULES,
    CANONICAL_RULES,
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
)
from app.inference.forward_chaining import ForwardChainingEngine
from app.inference.backward_chaining import BackwardChainingEngine
from app.inference.resolution import (
    PropositionalResolutionEngine,
    resolve,
    demonstrate_resolution,
)
from app.inference.engine import InferenceEngine

__all__ = [
    "Fact",
    "WorkingMemory",
    "HornRule",
    "Rule",
    "PREDEFINED_RULES",
    "CANONICAL_HORN_RULES",
    "ALL_OPERATIONAL_RULES",
    "CANONICAL_RULES",
    "R1_LANDSLIDE",
    "R2_TRAUMA_CENTER",
    "R3_ROAD_IMPASSABLE",
    "R4_REROUTE",
    "R5_HAZMAT",
    "R6_DISPATCH_DELAY",
    "R7_REFUEL",
    "R8_HOSPITAL_DIVERT",
    "R9_CRITICAL_PRIORITY",
    "R10_HIGH_PRIORITY",
    "R11_AVOID_BLOCKED",
    "ForwardChainingEngine",
    "BackwardChainingEngine",
    "PropositionalResolutionEngine",
    "resolve",
    "demonstrate_resolution",
    "InferenceEngine",
]
