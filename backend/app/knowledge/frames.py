"""
ResQ-AI Semantic Frame System.
Module VI: Knowledge Representation.

Implements Marvin Minsky's 1974 Semantic Frame theory:
- Frames: concept and instance structures with hierarchical prototype inheritance.
- Slots: named attributes with multi-faceted governance.
- Facets: value, default, constraint, if-needed (lazy derivation demon),
  if-added (reactive action demon), if-removed (cleanup demon).
- Canonical domain frames: IncidentFrame, AmbulanceFrame, HospitalFrame,
  RoadFrame, ResourceFrame.
"""

from __future__ import annotations
import copy
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union


class Facet(str, Enum):
    """Marvin Minsky's standard frame slot facets."""
    VALUE = "value"
    DEFAULT = "default"
    CONSTRAINT = "constraint"
    IF_NEEDED = "if_needed"
    IF_ADDED = "if_added"
    IF_REMOVED = "if_removed"


class Slot:
    """
    Represents an individual slot within a semantic frame.
    Governed by value, default, constraint, and procedural attachments.
    """
    def __init__(
        self,
        name: str,
        value: Any = None,
        default: Any = None,
        constraint: Optional[Callable[[Any], bool]] = None,
        if_needed: Optional[Callable[["Frame", str], Any]] = None,
        if_added: Optional[Callable[["Frame", str, Any], None]] = None,
        if_removed: Optional[Callable[["Frame", str], None]] = None,
        doc: str = "",
    ):
        self.name = name
        self.value = value
        self.default = default
        self.constraint = constraint
        self.if_needed = if_needed
        self.if_added = if_added
        self.if_removed = if_removed
        self.doc = doc

    def copy(self) -> Slot:
        """Create a detached replica of this slot for child frame inheritance."""
        return Slot(
            name=self.name,
            value=copy.deepcopy(self.value) if self.value is not None else None,
            default=copy.deepcopy(self.default) if self.default is not None else None,
            constraint=self.constraint,
            if_needed=self.if_needed,
            if_added=self.if_added,
            if_removed=self.if_removed,
            doc=self.doc,
        )


class Frame:
    """
    Base Minsky Semantic Frame representation.
    Supports hierarchical inheritance from parent prototype frames,
    slot registration, procedural attachments, and logical fact export.
    """
    def __init__(
        self,
        name: str,
        slots: Optional[Union[Dict[str, Any], Dict[str, Slot]]] = None,
        parent: Optional[Frame] = None,
        category: Optional[str] = None,
    ):
        self.name = name
        self.parent = parent
        self.category = category or (parent.category if parent else None)
        self.slots: Dict[str, Slot] = {}

        if slots:
            for k, v in slots.items():
                if isinstance(v, Slot):
                    self.slots[k] = v
                else:
                    self.slots[k] = Slot(name=k, value=v)

    def add_slot(self, slot: Slot) -> None:
        """Add or overwrite a slot definition in this frame."""
        self.slots[slot.name] = slot

    def has_slot(self, slot_name: str) -> bool:
        """Check if this frame or any ancestor defines the given slot."""
        if slot_name in self.slots:
            return True
        if self.parent is not None:
            return self.parent.has_slot(slot_name)
        return False

    def get_slot_definition(self, slot_name: str) -> Optional[Slot]:
        """Retrieve the slot definition from this frame or closest ancestor."""
        if slot_name in self.slots:
            return self.slots[slot_name]
        if self.parent is not None:
            return self.parent.get_slot_definition(slot_name)
        return None

    def get(self, slot_name: str, evaluate_if_needed: bool = True) -> Any:
        """
        Resolve a slot value following Minsky's evaluation protocol:
        1. If local slot has explicit value != None, return it.
        2. If evaluate_if_needed and if_needed procedural attachment exists, run it.
        3. If local default != None, return it.
        4. Traverse to parent prototype frame recursively.
        5. Return None if unresolved.
        """
        if slot_name in self.slots:
            slot = self.slots[slot_name]
            if slot.value is not None:
                return slot.value
            if evaluate_if_needed and slot.if_needed is not None:
                derived = slot.if_needed(self, slot_name)
                if derived is not None:
                    return derived
            if slot.default is not None:
                return slot.default

        if self.parent is not None:
            return self.parent.get(slot_name, evaluate_if_needed=evaluate_if_needed)

        return None

    def set(self, slot_name: str, value: Any) -> None:
        """
        Assign a slot value. Validates constraints and fires if_added demon.
        If slot was inherited from parent, clones it into local frame.
        """
        if slot_name not in self.slots:
            ancestor_slot = self.get_slot_definition(slot_name)
            if ancestor_slot is not None:
                slot = ancestor_slot.copy()
                slot.value = None
                self.slots[slot_name] = slot
            else:
                slot = Slot(name=slot_name)
                self.slots[slot_name] = slot
        else:
            slot = self.slots[slot_name]

        # Enforce domain constraint
        if slot.constraint is not None:
            is_valid = slot.constraint(value)
            if not is_valid:
                raise ValueError(
                    f"Constraint validation failed for slot '{slot_name}' "
                    f"with value '{value}' in frame '{self.name}'."
                )

        slot.value = value

        # Fire if_added procedural attachment
        if slot.if_added is not None:
            slot.if_added(self, slot_name, value)

    def remove(self, slot_name: str) -> None:
        """Clear a slot value and invoke if_removed procedural attachment."""
        if slot_name in self.slots:
            slot = self.slots[slot_name]
            if slot.if_removed is not None:
                slot.if_removed(self, slot_name)
            slot.value = None

    def get_all_slot_names(self) -> Set[str]:
        """Collect all slot names defined across this frame and ancestor chain."""
        names = set(self.slots.keys())
        if self.parent is not None:
            names.update(self.parent.get_all_slot_names())
        return names

    def to_dict(self) -> Dict[str, Any]:
        """Serialize all resolved slot values to a dictionary."""
        result: Dict[str, Any] = {}
        for name in sorted(self.get_all_slot_names()):
            result[name] = self.get(name)
        return result

    def to_facts(self) -> List[str]:
        """
        Serialize populated slots to FOL-inspired ground fact strings for Module V inference.
        Example: 'VictimCount(INC001, 6)' or 'Severity(INC001, critical)'
        """
        facts: List[str] = []
        clean_name = self.name.replace(" ", "_").replace("-", "_")
        for slot_name in sorted(self.get_all_slot_names()):
            val = self.get(slot_name)
            if val is not None:
                val_str = str(val).strip().replace(" ", "_")
                # Capitalize slot name for FOL predicate convention
                pred = "".join(word.capitalize() for word in slot_name.split("_"))
                facts.append(f"{pred}({clean_name}, {val_str})")
        return facts

    def instantiate(self, instance_name: str, **slot_overrides) -> Frame:
        """Create a new child frame inheriting from this frame."""
        child = Frame(name=instance_name, parent=self, category=self.category)
        for k, v in slot_overrides.items():
            child.set(k, v)
        return child

    def __getitem__(self, item: str) -> Any:
        return self.get(item)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __contains__(self, item: str) -> bool:
        return self.has_slot(item)

    def __repr__(self) -> str:
        parent_name = self.parent.name if self.parent else "None"
        return f"<Frame '{self.name}' parent='{parent_name}' slots={list(self.slots.keys())}>"


# -----------------------------------------------------------------------------
# Canonical Domain Frames
# -----------------------------------------------------------------------------

def _validate_non_empty_str(v: Any) -> bool:
    return isinstance(v, str) and len(v.strip()) > 0

def _validate_non_negative_int(v: Any) -> bool:
    return isinstance(v, int) and v >= 0

def _validate_positive_int(v: Any) -> bool:
    return isinstance(v, int) and v >= 1

def _validate_positive_float(v: Any) -> bool:
    return (isinstance(v, (int, float))) and float(v) > 0.0

def _validate_bool(v: Any) -> bool:
    return isinstance(v, bool)


# 1. Incident Frame & Procedural Attachments

def _incident_victim_if_added(frame: Frame, slot_name: str, val: Any) -> None:
    """Reactive triage demon: victim count > 5 escalates severity to 'critical'."""
    if isinstance(val, (int, float)) and val > 5:
        frame.set("severity", "critical")

def _incident_priority_if_needed(frame: Frame, slot_name: str) -> Any:
    """Lazy derivation demon: computes priority from victim count and severity."""
    victims = frame.get("victim_count", evaluate_if_needed=False) or 0
    sev = str(frame.get("severity", evaluate_if_needed=False) or "medium").lower()
    if victims > 5 or sev == "critical":
        return "critical"
    if sev == "high" or victims > 2:
        return "high"
    if sev == "medium":
        return "medium"
    return "low"

def _incident_ambulance_if_added(frame: Frame, slot_name: str, val: Any) -> None:
    """Reactive dispatch demon: assigning ambulance updates incident status."""
    if val and frame.get("status") == "reported":
        frame.set("status", "dispatched")


class IncidentFrame(Frame):
    """Semantic frame representing emergency incidents with triage demons."""
    def __init__(
        self,
        name: str = "IncidentPrototype",
        parent: Optional[Frame] = None,
        **initial_values,
    ):
        super().__init__(name=name, parent=parent, category="incident")
        self._init_incident_slots()
        for k, v in initial_values.items():
            self.set(k, v)

    def _init_incident_slots(self) -> None:
        self.add_slot(Slot("incident_id", default="", constraint=_validate_non_empty_str))
        self.add_slot(Slot("emergency_type", default="Medical Emergency"))
        self.add_slot(Slot("location", default="N1"))
        self.add_slot(Slot(
            "victim_count",
            default=1,
            constraint=_validate_non_negative_int,
            if_added=_incident_victim_if_added,
        ))
        self.add_slot(Slot(
            "severity",
            default="medium",
            constraint=lambda v: str(v).lower() in ["low", "medium", "high", "critical"],
        ))
        self.add_slot(Slot(
            "weather",
            default="clear",
            constraint=lambda v: str(v).lower() in ["clear", "rain", "heavy_rain", "storm", "fog"],
        ))
        self.add_slot(Slot("road_blocked", default=False, constraint=_validate_bool))
        self.add_slot(Slot(
            "priority",
            default=None,
            if_needed=_incident_priority_if_needed,
            constraint=lambda v: str(v).lower() in ["low", "medium", "high", "critical"],
        ))
        self.add_slot(Slot(
            "assigned_ambulance",
            default=None,
            if_added=_incident_ambulance_if_added,
        ))
        self.add_slot(Slot("assigned_hospital", default=None))
        self.add_slot(Slot(
            "status",
            default="reported",
            constraint=lambda v: str(v).lower() in ["reported", "triaged", "dispatched", "resolved"],
        ))

    @classmethod
    def from_orm(cls, incident: Any) -> IncidentFrame:
        """Hydrate an IncidentFrame from an SQLAlchemy Incident ORM instance."""
        inst = cls(name=f"Incident_{getattr(incident, 'id', 'new')}")
        inst.set("incident_id", str(getattr(incident, "id", "")))
        inst.set("emergency_type", getattr(incident, "emergency_type", "Medical Emergency"))
        inst.set("location", getattr(incident, "location", "N1"))
        inst.set("victim_count", getattr(incident, "victim_count", 1))
        inst.set("severity", str(getattr(incident, "severity", "medium")).lower())
        inst.set("weather", str(getattr(incident, "weather", "clear")).lower())
        inst.set("road_blocked", bool(getattr(incident, "road_condition", "") == "Blocked"))
        inst.set("status", str(getattr(incident, "status", "reported")).lower())
        if getattr(incident, "priority", None):
            inst.set("priority", str(incident.priority).lower())
        return inst


# 2. Ambulance Frame & Procedural Attachments

def _ambulance_status_if_added(frame: Frame, slot_name: str, val: Any) -> None:
    """Reactive maintenance demon: setting status to maintenance clears active patient load."""
    if str(val).lower() == "maintenance":
        slot = frame.slots.get("current_patients")
        if slot is not None:
            slot.value = 0

def _ambulance_patients_if_added(frame: Frame, slot_name: str, val: Any) -> None:
    """Reactive dispatch demon: reaching capacity changes status to dispatched."""
    cap = frame.get("capacity") or 4
    if isinstance(val, (int, float)) and val >= cap:
        frame.set("status", "dispatched")

def _ambulance_capacity_if_needed(frame: Frame, slot_name: str) -> Any:
    """Lazy capacity derivation demon: calculates remaining available victim slots."""
    cap = frame.get("capacity", evaluate_if_needed=False) or 0
    patients = frame.get("current_patients", evaluate_if_needed=False) or 0
    return max(0, cap - patients)


class AmbulanceFrame(Frame):
    """Semantic frame representing ambulance dispatch units."""
    def __init__(
        self,
        name: str = "AmbulancePrototype",
        parent: Optional[Frame] = None,
        **initial_values,
    ):
        super().__init__(name=name, parent=parent, category="ambulance")
        self._init_ambulance_slots()
        for k, v in initial_values.items():
            self.set(k, v)

    def _init_ambulance_slots(self) -> None:
        self.add_slot(Slot("code", default="A1", constraint=_validate_non_empty_str))
        self.add_slot(Slot("callsign", default=""))
        self.add_slot(Slot("current_location", default="A1"))
        self.add_slot(Slot("capacity", default=4, constraint=_validate_positive_int))
        self.add_slot(Slot(
            "status",
            default="available",
            constraint=lambda v: str(v).lower() in ["available", "dispatched", "maintenance"],
            if_added=_ambulance_status_if_added,
        ))
        self.add_slot(Slot(
            "equipment_level",
            default="ALS",
            constraint=lambda v: str(v).upper() in ["ALS", "BLS"],
        ))
        self.add_slot(Slot(
            "current_patients",
            default=0,
            constraint=_validate_non_negative_int,
            if_added=_ambulance_patients_if_added,
        ))
        self.add_slot(Slot(
            "available_capacity",
            default=None,
            if_needed=_ambulance_capacity_if_needed,
        ))

    @classmethod
    def from_orm(cls, ambulance: Any) -> AmbulanceFrame:
        """Hydrate an AmbulanceFrame from an SQLAlchemy Ambulance ORM instance."""
        inst = cls(name=f"Ambulance_{getattr(ambulance, 'code', 'unit')}")
        inst.set("code", str(getattr(ambulance, "code", "A1")))
        inst.set("callsign", str(getattr(ambulance, "callsign", "")))
        inst.set("current_location", str(getattr(ambulance, "current_location", "A1")))
        inst.set("capacity", int(getattr(ambulance, "capacity", 4)))
        inst.set("status", str(getattr(ambulance, "status", "available")).lower())
        inst.set("equipment_level", str(getattr(ambulance, "equipment_level", "ALS")).upper())
        return inst


# 3. Hospital Frame & Procedural Attachments

def _hospital_occupied_if_added(frame: Frame, slot_name: str, val: Any) -> None:
    """Reactive diversion demon: fully occupied hospital switches status to 'full'."""
    cap = frame.get("emergency_capacity") or 20
    if isinstance(val, (int, float)) and val >= cap:
        frame.set("status", "full")

def _hospital_available_beds_if_needed(frame: Frame, slot_name: str) -> Any:
    """Lazy bed derivation demon: computes available emergency intake capacity."""
    cap = frame.get("emergency_capacity", evaluate_if_needed=False) or 0
    occ = frame.get("occupied_beds", evaluate_if_needed=False) or 0
    return max(0, cap - occ)


class HospitalFrame(Frame):
    """Semantic frame representing hospital facilities and intake capacity."""
    def __init__(
        self,
        name: str = "HospitalPrototype",
        parent: Optional[Frame] = None,
        **initial_values,
    ):
        super().__init__(name=name, parent=parent, category="hospital")
        self._init_hospital_slots()
        for k, v in initial_values.items():
            self.set(k, v)

    def _init_hospital_slots(self) -> None:
        self.add_slot(Slot("code", default="H1", constraint=_validate_non_empty_str))
        self.add_slot(Slot("name", default=""))
        self.add_slot(Slot("location", default="H1"))
        self.add_slot(Slot("emergency_capacity", default=20, constraint=_validate_positive_int))
        self.add_slot(Slot(
            "occupied_beds",
            default=0,
            constraint=_validate_non_negative_int,
            if_added=_hospital_occupied_if_added,
        ))
        self.add_slot(Slot(
            "available_beds",
            default=None,
            if_needed=_hospital_available_beds_if_needed,
        ))
        self.add_slot(Slot(
            "trauma_level",
            default=1,
            constraint=lambda v: v in [1, 2, 3],
        ))
        self.add_slot(Slot("specialties", default=["Trauma"]))
        self.add_slot(Slot(
            "status",
            default="open",
            constraint=lambda v: str(v).lower() in ["open", "divert", "full"],
        ))

    @classmethod
    def from_orm(cls, hospital: Any) -> HospitalFrame:
        """Hydrate a HospitalFrame from an SQLAlchemy Hospital ORM instance."""
        inst = cls(name=f"Hospital_{getattr(hospital, 'code', 'facility')}")
        inst.set("code", str(getattr(hospital, "code", "H1")))
        inst.set("name", str(getattr(hospital, "name", "")))
        inst.set("location", str(getattr(hospital, "location", "H1")))
        inst.set("emergency_capacity", int(getattr(hospital, "emergency_capacity", 20)))
        avail = getattr(hospital, "available_emergency_beds", None)
        cap = int(getattr(hospital, "emergency_capacity", 20))
        if avail is not None:
            inst.set("occupied_beds", max(0, cap - int(avail)))
        else:
            inst.set("occupied_beds", int(getattr(hospital, "current_occupancy", 0)))
        inst.set("trauma_level", 1)
        inst.set("specialties", list(getattr(hospital, "specialties", ["Trauma"])))
        inst.set("status", "open")
        return inst


# 4. Road Frame & Procedural Attachments

def _road_cost_if_needed(frame: Frame, slot_name: str) -> Any:
    """Lazy cost derivation demon: calculates effective traversal cost accounting for blockage."""
    if frame.get("is_blocked", evaluate_if_needed=False):
        return float("inf")
    d = frame.get("distance", evaluate_if_needed=False) or 1.0
    t = frame.get("traffic_factor", evaluate_if_needed=False) or 1.0
    r = frame.get("risk_factor", evaluate_if_needed=False) or 0.0
    return round(float(d) * float(t) * (1.0 + float(r)), 4)

def _road_travel_time_if_needed(frame: Frame, slot_name: str) -> Any:
    """Lazy travel time demon: calculates expected transit minutes at speed limit."""
    d = frame.get("distance", evaluate_if_needed=False) or 1.0
    t = frame.get("traffic_factor", evaluate_if_needed=False) or 1.0
    return round((float(d) / 50.0) * 60.0 * float(t), 4)


class RoadFrame(Frame):
    """Semantic frame representing road segments and dynamic traversal costs."""
    def __init__(
        self,
        name: str = "RoadPrototype",
        parent: Optional[Frame] = None,
        **initial_values,
    ):
        super().__init__(name=name, parent=parent, category="road")
        self._init_road_slots()
        for k, v in initial_values.items():
            self.set(k, v)

    def _init_road_slots(self) -> None:
        self.add_slot(Slot("road_id", default=""))
        self.add_slot(Slot("source_node", default=""))
        self.add_slot(Slot("target_node", default=""))
        self.add_slot(Slot("distance", default=1.0, constraint=_validate_positive_float))
        self.add_slot(Slot(
            "traffic_factor",
            default=1.0,
            constraint=lambda v: isinstance(v, (int, float)) and float(v) >= 1.0,
        ))
        self.add_slot(Slot(
            "risk_factor",
            default=0.0,
            constraint=lambda v: isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0,
        ))
        self.add_slot(Slot("is_blocked", default=False, constraint=_validate_bool))
        self.add_slot(Slot(
            "effective_cost",
            default=None,
            if_needed=_road_cost_if_needed,
        ))
        self.add_slot(Slot(
            "travel_time_min",
            default=None,
            if_needed=_road_travel_time_if_needed,
        ))

    @classmethod
    def from_orm(cls, road: Any) -> RoadFrame:
        """Hydrate a RoadFrame from an SQLAlchemy Road ORM instance."""
        inst = cls(name=f"Road_{getattr(road, 'source_node', '')}_{getattr(road, 'target_node', '')}")
        inst.set("road_id", str(getattr(road, "id", "")))
        inst.set("source_node", str(getattr(road, "source_node", "")))
        inst.set("target_node", str(getattr(road, "target_node", "")))
        inst.set("distance", float(getattr(road, "distance", 1.0)))
        inst.set("traffic_factor", float(getattr(road, "traffic_factor", 1.0)))
        inst.set("risk_factor", float(getattr(road, "risk_factor", 0.0)))
        inst.set("is_blocked", bool(getattr(road, "is_blocked", False)))
        return inst


# 5. Resource Frame & Procedural Attachments

def _resource_allocated_if_added(frame: Frame, slot_name: str, val: Any) -> None:
    """Reactive inventory demon: asserts allocated quantity does not exceed total stock."""
    tot = frame.get("quantity_total") or 0
    if isinstance(val, (int, float)) and val > tot:
        raise ValueError(f"quantity_allocated ({val}) cannot exceed quantity_total ({tot}).")

def _resource_available_if_needed(frame: Frame, slot_name: str) -> Any:
    """Lazy stock derivation demon: computes currently free inventory count."""
    tot = frame.get("quantity_total", evaluate_if_needed=False) or 0
    alloc = frame.get("quantity_allocated", evaluate_if_needed=False) or 0
    return max(0, tot - alloc)


class ResourceFrame(Frame):
    """Semantic frame representing emergency equipment and supplies."""
    def __init__(
        self,
        name: str = "ResourcePrototype",
        parent: Optional[Frame] = None,
        **initial_values,
    ):
        super().__init__(name=name, parent=parent, category="resource")
        self._init_resource_slots()
        for k, v in initial_values.items():
            self.set(k, v)

    def _init_resource_slots(self) -> None:
        self.add_slot(Slot("resource_id", default=""))
        self.add_slot(Slot("name", default=""))
        self.add_slot(Slot(
            "category",
            default="Medical",
            constraint=lambda v: str(v).capitalize() in ["Medical", "Rescue", "Hazmat", "Transport"],
        ))
        self.add_slot(Slot("quantity_total", default=10, constraint=_validate_non_negative_int))
        self.add_slot(Slot(
            "quantity_allocated",
            default=0,
            constraint=_validate_non_negative_int,
            if_added=_resource_allocated_if_added,
        ))
        self.add_slot(Slot(
            "quantity_available",
            default=None,
            if_needed=_resource_available_if_needed,
        ))
        self.add_slot(Slot("location", default="H1"))

    @classmethod
    def from_orm(cls, res: Any) -> ResourceFrame:
        """Hydrate a ResourceFrame from an SQLAlchemy Resource ORM instance."""
        inst = cls(name=f"Resource_{getattr(res, 'name', 'item')}")
        inst.set("resource_id", str(getattr(res, "id", "")))
        inst.set("name", str(getattr(res, "name", "")))
        inst.set("category", str(getattr(res, "category", "Medical")))
        inst.set("quantity_total", int(getattr(res, "quantity_total", 10)))
        avail = int(getattr(res, "quantity_available", 10))
        tot = int(getattr(res, "quantity_total", 10))
        inst.set("quantity_allocated", max(0, tot - avail))
        inst.set("location", str(getattr(res, "location", "H1")))
        return inst


def create_canonical_frames() -> Dict[str, Frame]:
    """Create and return canonical prototype frames."""
    return {
        "Incident": IncidentFrame("Incident"),
        "Ambulance": AmbulanceFrame("Ambulance"),
        "Hospital": HospitalFrame("Hospital"),
        "Road": RoadFrame("Road"),
        "Emergency Resource": ResourceFrame("Emergency Resource"),
    }


def create_frames() -> Dict[str, Frame]:
    """Factory preserving backwards compatibility with existing signature."""
    return create_canonical_frames()
