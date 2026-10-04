"""
ResQ-AI CSP Problem Formulation.
Module IV: Constraint Satisfaction Problem.
Defines variables, domains, and formal constraints for emergency ambulance/hospital dispatch.
"""

from typing import List, Dict, Any, Optional, Set, Callable, Tuple
from dataclasses import dataclass, field
from app.search.graph import RoadGraph


@dataclass
class IncidentSpec:
    id: str
    location: str
    victim_count: int
    severity: str = "High"
    required_specialties: List[str] = field(default_factory=list)


@dataclass
class AmbulanceSpec:
    code: str
    status: str
    capacity: int
    location: str


@dataclass
class HospitalSpec:
    code: str
    name: str
    location: str
    available_emergency_beds: int
    specialties: List[str] = field(default_factory=list)


class DispatchCSP:
    """
    Formal CSP representation for emergency response resource allocation.
    Variables:
      - 'ambulance': Ambulance code
      - 'hospital': Hospital code
      - 'route': Sequence of node IDs
    """

    def __init__(
        self,
        incident: IncidentSpec,
        ambulances: Optional[List[AmbulanceSpec]] = None,
        hospitals: Optional[List[HospitalSpec]] = None,
        graph: Optional[RoadGraph] = None,
    ):
        self.incident = incident
        self.graph = graph or RoadGraph.build_canonical_network()

        # Canonical default fleet if not provided
        self.ambulances = ambulances or [
            AmbulanceSpec(code="A1", status="Available", capacity=4, location="A1"),
            AmbulanceSpec(code="A2", status="Available", capacity=6, location="A2"),
            AmbulanceSpec(code="A3", status="Maintenance", capacity=6, location="A3"),
        ]

        # Canonical default hospitals if not provided
        self.hospitals = hospitals or [
            HospitalSpec(code="H1", name="City General Hospital", location="H1", available_emergency_beds=15, specialties=["Trauma", "ICU"]),
            HospitalSpec(code="H2", name="St. Jude Clinic", location="H2", available_emergency_beds=5, specialties=["General", "Pediatrics"]),
        ]

        self.variables: List[str] = ["ambulance", "hospital"]
        self.domains: Dict[str, List[Any]] = {
            "ambulance": [a.code for a in self.ambulances],
            "hospital": [h.code for h in self.hospitals],
        }

        self.rejected_candidates: List[Dict[str, str]] = []

    def get_ambulance(self, code: str) -> Optional[AmbulanceSpec]:
        for a in self.ambulances:
            if a.code == code:
                return a
        return None

    def get_hospital(self, code: str) -> Optional[HospitalSpec]:
        for h in self.hospitals:
            if h.code == code:
                return h
        return None

    def check_ambulance_constraints(self, amb_code: str) -> Tuple[bool, str]:
        """
        Validates individual ambulance constraints:
        1. Operational availability: status must be 'Available'
        2. Capacity: capacity >= incident victim_count
        """
        amb = self.get_ambulance(amb_code)
        if not amb:
            return False, f"Ambulance {amb_code} does not exist in registry"

        if amb.status.lower() != "available":
            return False, f"Status is {amb.status}"

        if amb.capacity < self.incident.victim_count:
            return False, f"Capacity {amb.capacity} insufficient for {self.incident.victim_count} victims"

        return True, "Valid"

    def check_hospital_constraints(self, hosp_code: str) -> Tuple[bool, str]:
        """
        Validates individual hospital constraints:
        1. Available emergency bed capacity >= incident victim_count
        """
        hosp = self.get_hospital(hosp_code)
        if not hosp:
            return False, f"Hospital {hosp_code} does not exist in registry"

        if hosp.available_emergency_beds < self.incident.victim_count:
            return False, f"Emergency capacity {hosp.available_emergency_beds} insufficient for {self.incident.victim_count} victims"

        return True, "Valid"

    def check_binary_constraints(self, amb_code: str, hosp_code: str) -> Tuple[bool, str]:
        """
        Validates joint binary constraints between ambulance and hospital:
        1. Route feasibility: unblocked path must exist from ambulance base to incident, and incident to hospital.
        """
        amb = self.get_ambulance(amb_code)
        hosp = self.get_hospital(hosp_code)
        if not amb or not hosp:
            return False, "Invalid entity references"

        # Check connectivity on graph
        from app.search.astar import AStarSearch
        finder = AStarSearch()

        leg1 = finder.search(self.graph, amb.location, self.incident.location)
        if not leg1.success:
            return False, f"No viable unblocked route from {amb.location} to incident at {self.incident.location}"

        leg2 = finder.search(self.graph, self.incident.location, hosp.location)
        if not leg2.success:
            return False, f"No viable unblocked route from incident at {self.incident.location} to hospital at {hosp.location}"

        return True, "Valid"
