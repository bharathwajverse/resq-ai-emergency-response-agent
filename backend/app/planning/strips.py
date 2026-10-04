"""
ResQ-AI STRIPS Automated Planning Domain & Action Operators.

Provides pure deterministic implementation of Stanford Research Institute Problem Solver
(STRIPS) action schemas, ground operators, state transitions, and emergency response
planning domains for classical AI planning.
"""

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple


@dataclass(frozen=True)
class STRIPSAction:
    """
    Classical STRIPS Action Operator.

    Consists of:
    - name: Action identifier
    - params: Action argument names or ground constants
    - preconditions: Predicates that must hold before execution
    - add_effects: Predicates added to state upon execution
    - delete_effects: Predicates removed from state upon execution
    - cost: Numerical step cost (default 1.0)
    - duration_minutes: Estimated execution duration in minutes
    - description: Human-readable action description
    """
    name: str
    params: Tuple[str, ...] = field(default_factory=tuple)
    preconditions: FrozenSet[str] = field(default_factory=frozenset)
    add_effects: FrozenSet[str] = field(default_factory=frozenset)
    delete_effects: FrozenSet[str] = field(default_factory=frozenset)
    cost: float = 1.0
    duration_minutes: float = 5.0
    description: str = ""

    def __post_init__(self) -> None:
        # Guarantee frozen set invariants
        if not isinstance(self.preconditions, frozenset):
            object.__setattr__(self, "preconditions", frozenset(self.preconditions))
        if not isinstance(self.add_effects, frozenset):
            object.__setattr__(self, "add_effects", frozenset(self.add_effects))
        if not isinstance(self.delete_effects, frozenset):
            object.__setattr__(self, "delete_effects", frozenset(self.delete_effects))
        if not isinstance(self.params, tuple):
            object.__setattr__(self, "params", tuple(self.params))

    def is_applicable(self, state: Set[str] | FrozenSet[str]) -> bool:
        """Check if all preconditions hold in the given state."""
        return self.preconditions.issubset(state)

    def apply(self, state: Set[str] | FrozenSet[str]) -> FrozenSet[str]:
        """
        Apply action to state under Closed World Assumption:
        Result(S, a) = (S - delete_effects) U add_effects.
        """
        if not self.is_applicable(state):
            missing = self.preconditions - set(state)
            raise ValueError(
                f"Action '{self.name}' cannot be applied: preconditions {missing} not met."
            )
        return frozenset((set(state) - self.delete_effects) | self.add_effects)

    def ground(self, param_mapping: Dict[str, str]) -> "STRIPSAction":
        """
        Instantiate a parameterized action schema by substituting variable tokens.
        """
        def substitute(pred: str) -> str:
            res = pred
            for var, val in param_mapping.items():
                res = res.replace(var, val)
            return res

        ground_pre = frozenset(substitute(p) for p in self.preconditions)
        ground_add = frozenset(substitute(p) for p in self.add_effects)
        ground_del = frozenset(substitute(p) for p in self.delete_effects)
        ground_params = tuple(param_mapping.get(p, p) for p in self.params)

        ground_name = self.name
        if ground_params:
            ground_name = f"{self.name}({', '.join(ground_params)})"

        return STRIPSAction(
            name=ground_name,
            params=ground_params,
            preconditions=ground_pre,
            add_effects=ground_add,
            delete_effects=ground_del,
            cost=self.cost,
            duration_minutes=self.duration_minutes,
            description=substitute(self.description) if self.description else ground_name,
        )


def create_canonical_action_schemas() -> List[STRIPSAction]:
    """
    Returns the canonical parameterized STRIPS action schemas for emergency response:
    1. DispatchAmbulance(?amb, ?station, ?scene, ?inc)
    2. Navigate(?amb, ?from, ?to)
    3. TreatVictim(?amb, ?inc, ?scene)
    4. TransportVictim(?amb, ?inc, ?scene, ?hosp)
    5. AdmitVictim(?amb, ?hosp, ?inc)
    6. PrepareHospitalBed(?hosp, ?inc, ?scene)
    """
    return [
        STRIPSAction(
            name="DispatchAmbulance",
            params=("?amb", "?station", "?scene", "?inc"),
            preconditions=frozenset({
                "Available(?amb)",
                "At(?amb, ?station)",
                "IncidentReported(?inc, ?scene)",
            }),
            add_effects=frozenset({
                "Dispatched(?amb, ?inc)",
                "EnRoute(?amb, ?station, ?scene)",
            }),
            delete_effects=frozenset({
                "Available(?amb)",
                "At(?amb, ?station)",
            }),
            cost=1.0,
            duration_minutes=3.0,
            description="Dispatch ?amb from ?station to ?scene for ?inc",
        ),
        STRIPSAction(
            name="Navigate",
            params=("?amb", "?from", "?to"),
            preconditions=frozenset({
                "EnRoute(?amb, ?from, ?to)",
            }),
            add_effects=frozenset({
                "At(?amb, ?to)",
            }),
            delete_effects=frozenset({
                "EnRoute(?amb, ?from, ?to)",
            }),
            cost=2.0,
            duration_minutes=8.0,
            description="Navigate ?amb from ?from to ?to",
        ),
        STRIPSAction(
            name="TreatVictim",
            params=("?amb", "?inc", "?scene"),
            preconditions=frozenset({
                "At(?amb, ?scene)",
                "IncidentReported(?inc, ?scene)",
                "Dispatched(?amb, ?inc)",
            }),
            add_effects=frozenset({
                "VictimsTreated(?inc)",
            }),
            delete_effects=frozenset(),
            cost=3.0,
            duration_minutes=12.0,
            description="Treat victims of ?inc at ?scene using ?amb",
        ),
        STRIPSAction(
            name="TransportVictim",
            params=("?amb", "?inc", "?scene", "?hosp"),
            preconditions=frozenset({
                "At(?amb, ?scene)",
                "VictimsTreated(?inc)",
                "Hospital(?hosp)",
                "Dispatched(?amb, ?inc)",
            }),
            add_effects=frozenset({
                "At(?amb, ?hosp)",
                "EnRouteToHosp(?amb, ?hosp)",
            }),
            delete_effects=frozenset({
                "At(?amb, ?scene)",
            }),
            cost=2.5,
            duration_minutes=10.0,
            description="Transport treated victims of ?inc from ?scene to ?hosp in ?amb",
        ),
        STRIPSAction(
            name="PrepareHospitalBed",
            params=("?hosp", "?inc", "?scene"),
            preconditions=frozenset({
                "Hospital(?hosp)",
                "IncidentReported(?inc, ?scene)",
            }),
            add_effects=frozenset({
                "BedPrepared(?hosp, ?inc)",
            }),
            delete_effects=frozenset(),
            cost=1.0,
            duration_minutes=4.0,
            description="Prepare intensive care bed at ?hosp for incoming victims of ?inc",
        ),
        STRIPSAction(
            name="AdmitVictim",
            params=("?amb", "?hosp", "?inc"),
            preconditions=frozenset({
                "At(?amb, ?hosp)",
                "VictimsTreated(?inc)",
                "Hospital(?hosp)",
                "BedPrepared(?hosp, ?inc)",
            }),
            add_effects=frozenset({
                "Admitted(?inc, ?hosp)",
                "Available(?amb)",
            }),
            delete_effects=frozenset({
                "EnRouteToHosp(?amb, ?hosp)",
            }),
            cost=1.5,
            duration_minutes=5.0,
            description="Admit victims of ?inc into ?hosp and release ?amb to available status",
        ),
    ]


def create_emergency_planning_problem(
    ambulance: str = "A1",
    station: str = "Central_Base",
    incident: str = "INC-1",
    scene: str = "Accident_Site",
    hospital: str = "City_General",
    include_bed_prep: bool = True,
) -> Tuple[FrozenSet[str], FrozenSet[str], List[STRIPSAction]]:
    """
    Instantiate a concrete ground STRIPS emergency planning problem.

    Returns:
    (initial_state, goal_state, ground_actions)
    """
    initial_state = frozenset({
        f"Available({ambulance})",
        f"At({ambulance}, {station})",
        f"IncidentReported({incident}, {scene})",
        f"Hospital({hospital})",
    })

    if include_bed_prep:
        goal_state = frozenset({
            f"Admitted({incident}, {hospital})",
            f"Available({ambulance})",
            f"BedPrepared({hospital}, {incident})",
        })
    else:
        goal_state = frozenset({
            f"Admitted({incident}, {hospital})",
            f"Available({ambulance})",
        })

    mapping = {
        "?amb": ambulance,
        "?station": station,
        "?scene": scene,
        "?inc": incident,
        "?hosp": hospital,
        "?from": station,
        "?to": scene,
    }

    schemas = create_canonical_action_schemas()
    ground_actions: List[STRIPSAction] = []

    for s in schemas:
        if s.name == "PrepareHospitalBed" and not include_bed_prep:
            continue
        if s.name == "AdmitVictim" and not include_bed_prep:
            # Drop BedPrepared precondition if bed prep is excluded
            relaxed_pre = frozenset(
                p for p in s.preconditions if not p.startswith("BedPrepared")
            )
            s_relaxed = STRIPSAction(
                name=s.name,
                params=s.params,
                preconditions=relaxed_pre,
                add_effects=s.add_effects,
                delete_effects=s.delete_effects,
                cost=s.cost,
                duration_minutes=s.duration_minutes,
                description=s.description,
            )
            ground_actions.append(s_relaxed.ground(mapping))
        else:
            ground_actions.append(s.ground(mapping))

    return initial_state, goal_state, ground_actions
