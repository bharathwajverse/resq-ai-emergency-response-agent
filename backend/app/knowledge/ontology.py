"""
ResQ-AI Emergency & Resource Ontology Taxonomies.
Module VI: Knowledge Representation.

Implements formal Description Logic inspired ontology DAGs:
- Transitive is-a subsumption reasoning.
- Mereological part-of composition reasoning.
- Least Common Subsumer (LCS) calculation.
- Cycle detection raising CyclicOntologyError.
- Emergency classification and resource requirement inference.
"""

from __future__ import annotations
from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple


class CyclicOntologyError(ValueError):
    """Raised when an added ontology relation creates a cycle in the taxonomy DAG."""
    pass


class OntologyNode:
    """Represents a concept node within the ontology taxonomy."""
    def __init__(
        self,
        name: str,
        parent: Optional[str] = None,
        description: str = "",
        properties: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.parent = parent
        self.children: Set[str] = set()
        self.parts: Set[str] = set()  # Direct mereological components
        self.description = description
        self.properties: Dict[str, Any] = properties or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "parent": self.parent,
            "children": sorted(list(self.children)),
            "parts": sorted(list(self.parts)),
            "description": self.description,
            "properties": self.properties,
        }

    def __repr__(self) -> str:
        return f"<OntologyNode '{self.name}' parent='{self.parent}' children={len(self.children)}>"


class EmergencyOntology:
    """
    Directed Acyclic Graph (DAG) Knowledge Representation engine.
    Supports subsumption, mereological composition, and least common subsumer reasoning.
    """
    def __init__(self, populate_defaults: bool = True):
        self.nodes: Dict[str, OntologyNode] = {}
        if populate_defaults:
            self._build_default_taxonomies()

    def add_concept(
        self,
        name: str,
        parent: Optional[str] = None,
        description: str = "",
        properties: Optional[Dict[str, Any]] = None,
    ) -> OntologyNode:
        """
        Add a concept to the taxonomy DAG.
        Enforces cycle prevention: if adding parent creates a cycle, raises CyclicOntologyError.
        """
        name = name.strip()
        if parent:
            parent = parent.strip()

        # Check self-loop
        if parent and name == parent:
            raise CyclicOntologyError(
                f"Self-referential relation: '{name}' cannot be its own parent."
            )

        # Ensure parent exists if specified
        if parent and parent not in self.nodes:
            self.nodes[parent] = OntologyNode(name=parent)

        # Check for cyclic subsumption before making modifications
        if parent and name in self.nodes:
            if self.subsumes(parent=name, child=parent):
                raise CyclicOntologyError(
                    f"Cyclic ontology detected: '{name}' already subsumes '{parent}'. "
                    f"Adding '{name}' is-a '{parent}' would create a directed cycle."
                )

        # Retrieve or create child node
        if name not in self.nodes:
            node = OntologyNode(name=name, parent=parent, description=description, properties=properties)
            self.nodes[name] = node
        else:
            node = self.nodes[name]
            if parent:
                # Remove from old parent children set if changing parent
                if node.parent and node.parent in self.nodes:
                    self.nodes[node.parent].children.discard(name)
                node.parent = parent
            if description:
                node.description = description
            if properties:
                node.properties.update(properties)

        # Register child in parent
        if parent:
            self.nodes[parent].children.add(name)

        return node

    def add_part_of(self, part: str, whole: str) -> None:
        """
        Register a mereological part-whole relation: 'part' is a component of 'whole'.
        """
        part = part.strip()
        whole = whole.strip()
        if whole not in self.nodes:
            self.add_concept(whole)
        if part not in self.nodes:
            self.add_concept(part)
        self.nodes[whole].parts.add(part)

    def subsumes(self, parent: str, child: str) -> bool:
        """
        Transitive is-a subsumption check:
        Returns True if 'child' is a specialization of 'parent' (child is-a parent),
        or if 'child' == 'parent' (reflexive property).
        """
        parent = parent.strip()
        child = child.strip()

        if parent not in self.nodes or child not in self.nodes:
            return False

        if parent == child:
            return True

        # Walk upward from child towards roots
        curr = self.nodes[child].parent
        visited: Set[str] = set()
        while curr:
            if curr == parent:
                return True
            if curr in visited:
                break
            visited.add(curr)
            curr_node = self.nodes.get(curr)
            curr = curr_node.parent if curr_node else None

        return False

    def is_a(self, child: str, parent: str) -> bool:
        """Convenience alias for subsumption check: child is-a parent."""
        return self.subsumes(parent=parent, child=child)

    def get_ancestors(self, concept: str) -> Set[str]:
        """Return all transitive ancestors of a concept in the is-a DAG."""
        concept = concept.strip()
        if concept not in self.nodes:
            return set()

        ancestors: Set[str] = set()
        curr = self.nodes[concept].parent
        while curr and curr not in ancestors:
            ancestors.add(curr)
            curr_node = self.nodes.get(curr)
            curr = curr_node.parent if curr_node else None

        return ancestors

    def get_ancestor_path(self, concept: str) -> List[str]:
        """Return ordered path from concept up to root: [concept, parent, ..., root]."""
        concept = concept.strip()
        if concept not in self.nodes:
            return []

        path = [concept]
        curr = self.nodes[concept].parent
        visited: Set[str] = {concept}
        while curr and curr not in visited:
            path.append(curr)
            visited.add(curr)
            curr_node = self.nodes.get(curr)
            curr = curr_node.parent if curr_node else None

        return path

    def get_descendants(self, concept: str) -> Set[str]:
        """Return all transitive descendants of a concept."""
        concept = concept.strip()
        if concept not in self.nodes:
            return set()

        descendants: Set[str] = set()
        queue: deque[str] = deque(self.nodes[concept].children)
        while queue:
            curr = queue.popleft()
            if curr not in descendants:
                descendants.add(curr)
                if curr in self.nodes:
                    queue.extend(self.nodes[curr].children)

        return descendants

    def get_depth(self, concept: str) -> int:
        """Calculate the tree depth of a concept (root nodes have depth 0)."""
        return len(self.get_ancestors(concept))

    def least_common_subsumer(self, concept_a: str, concept_b: str) -> Optional[str]:
        """
        Compute the Least Common Subsumer (LCS) of two concepts:
        LCS(A, B) = argmax_{C in Ancestors(A) & Ancestors(B)} Depth(C)
        """
        concept_a = concept_a.strip()
        concept_b = concept_b.strip()

        if concept_a not in self.nodes or concept_b not in self.nodes:
            return None

        # Candidate subsumers include ancestors and the concepts themselves
        cand_a = self.get_ancestors(concept_a) | {concept_a}
        cand_b = self.get_ancestors(concept_b) | {concept_b}

        common = cand_a.intersection(cand_b)
        if not common:
            return None

        # Sort by descending depth, then alphabetically for determinism
        best = sorted(
            list(common),
            key=lambda c: (-self.get_depth(c), c)
        )
        return best[0]

    def get_parts(self, concept: str, transitive: bool = True) -> List[str]:
        """
        Return the mereological components of a concept.
        If transitive=True, resolves the full part-of transitive closure.
        """
        concept = concept.strip()
        if concept not in self.nodes:
            return []

        if not transitive:
            return sorted(list(self.nodes[concept].parts))

        all_parts: Set[str] = set()
        queue: deque[str] = deque(self.nodes[concept].parts)
        while queue:
            part = queue.popleft()
            if part not in all_parts:
                all_parts.add(part)
                if part in self.nodes:
                    queue.extend(self.nodes[part].parts)

        return sorted(list(all_parts))

    def is_part_of(self, part: str, whole: str) -> bool:
        """Check if 'part' is a direct or transitive component of 'whole'."""
        return part.strip() in self.get_parts(whole.strip(), transitive=True)

    def classify_incident(
        self,
        raw_type: str,
        victims: int = 1,
        severity: str = "medium",
    ) -> str:
        """
        Map natural language descriptions and triage attributes to canonical ontology concepts.
        """
        t = raw_type.lower().strip()

        # Industrial hazards
        if any(w in t for w in ["chemical", "toxic", "radiation", "hazmat", "gas leak"]):
            if "gas" in t:
                return "ToxicGasLeak"
            if "radiation" in t:
                return "RadiationLeak"
            return "ChemicalSpill"

        # Fires
        if any(w in t for w in ["fire", "blaze", "smoke", "burn"]):
            if any(w in t for w in ["industrial", "factory", "refinery", "chemical"]):
                return "IndustrialHazmatFire"
            if any(w in t for w in ["building", "structure", "warehouse", "commercial"]):
                return "StructuralFire"
            return "ResidentialFire"

        # Floods & Storms
        if any(w in t for w in ["flood", "drown", "water", "submerged"]):
            return "FlashFlood" if "flash" in t else "FloodEmergency"
        if any(w in t for w in ["storm", "hurricane", "cyclone", "tornado"]):
            return "SevereStorm"
        if "earthquake" in t:
            return "Earthquake"

        # Traffic accidents
        if any(w in t for w in ["accident", "collision", "crash", "car", "traffic", "vehicle", "highway"]):
            if victims > 3 or "multi" in t or "pileup" in t:
                return "MultiVehicleCollision"
            if "pedestrian" in t:
                return "PedestrianIncident"
            return "RoadTrafficAccident"

        # Medical emergencies
        if any(w in t for w in ["cardiac", "heart", "chest pain", "infarction"]):
            return "CardiacArrest"
        if any(w in t for w in ["respiratory", "asthma", "breathing", "choking"]):
            return "RespiratoryDistress"
        if victims > 4:
            return "MassCasualtyTrauma"
        if "medical" in t:
            return "MedicalEmergency"

        # Check direct concept match in ontology
        for name in self.nodes:
            if name.lower() == t:
                return name

        return "EmergencyEvent"

    def infer_required_resources(
        self,
        emergency_type: str,
        victims: int = 1,
    ) -> List[str]:
        """
        Infer required emergency resources based on ontological subsumption.
        """
        emergency_type = emergency_type.strip()
        resources: List[str] = []

        if self.subsumes("IndustrialHazard", emergency_type) or self.subsumes("IndustrialHazmatFire", emergency_type):
            resources.extend([
                "AdvancedLifeSupportAmbulance",
                "HazmatSpecialist",
                "HazmatProtectiveGear",
            ])
        elif self.subsumes("CardiacEmergency", emergency_type):
            resources.extend([
                "AdvancedLifeSupportAmbulance",
                "Defibrillator",
                "Level1TraumaCenter",
            ])
        elif self.subsumes("TrafficEmergency", emergency_type):
            if victims >= 4:
                resources.extend([
                    "AdvancedLifeSupportAmbulance",
                    "ExtricationGear",
                    "Level1TraumaCenter",
                ])
            else:
                resources.extend([
                    "RoadAmbulance",
                    "ParamedicCrew",
                ])
        elif self.subsumes("FloodEmergency", emergency_type) or self.subsumes("NaturalDisaster", emergency_type):
            resources.extend([
                "SearchAndRescueTeam",
                "RescueHelicopter",
                "MobileFieldClinic",
            ])
        elif self.subsumes("FireEmergency", emergency_type):
            resources.extend([
                "AdvancedLifeSupportAmbulance",
                "SearchAndRescueTeam",
                "OxygenSupplyUnit",
            ])
        else:
            resources.extend(["RoadAmbulance", "CommunityHospital"])

        # Deduplicate preserving order
        seen = set()
        deduped = []
        for r in resources:
            if r not in seen:
                seen.add(r)
                deduped.append(r)
        return deduped

    def to_legacy_dict(self) -> Dict[str, List[str]]:
        """Export simplified legacy tree dictionary for backwards compatibility."""
        return {
            "Emergency": sorted(list(self.get_descendants("EmergencyEvent"))),
            "Resource": sorted(list(self.get_descendants("EmergencyResource"))),
        }

    def _build_default_taxonomies(self) -> None:
        """Construct the authoritative Emergency and Resource taxonomy DAGs."""
        # 1. Emergency Event Taxonomy
        self.add_concept("EmergencyEvent", description="Root category for all emergency incidents")

        # Medical emergencies
        self.add_concept("MedicalEmergency", parent="EmergencyEvent", description="Acute physiological trauma and illness")
        self.add_concept("CardiacEmergency", parent="MedicalEmergency")
        self.add_concept("CardiacArrest", parent="CardiacEmergency")
        self.add_concept("RespiratoryEmergency", parent="MedicalEmergency")
        self.add_concept("RespiratoryDistress", parent="RespiratoryEmergency")
        self.add_concept("MassCasualtyTrauma", parent="MedicalEmergency")

        # Traffic emergencies
        self.add_concept("TrafficEmergency", parent="EmergencyEvent", description="Transportation and vehicular incidents")
        self.add_concept("RoadTrafficAccident", parent="TrafficEmergency")
        self.add_concept("MultiVehicleCollision", parent="RoadTrafficAccident")
        self.add_concept("HighwayRollover", parent="RoadTrafficAccident")
        self.add_concept("PedestrianIncident", parent="TrafficEmergency")

        # Fire emergencies
        self.add_concept("FireEmergency", parent="EmergencyEvent", description="Thermal and structural combustion events")
        self.add_concept("ResidentialFire", parent="FireEmergency")
        self.add_concept("StructuralFire", parent="FireEmergency")
        self.add_concept("IndustrialHazmatFire", parent="FireEmergency")

        # Natural disasters
        self.add_concept("NaturalDisaster", parent="EmergencyEvent", description="Severe environmental disruptions")
        self.add_concept("FloodEmergency", parent="NaturalDisaster")
        self.add_concept("FlashFlood", parent="FloodEmergency")
        self.add_concept("RiverineOverflow", parent="FloodEmergency")
        self.add_concept("SevereStorm", parent="NaturalDisaster")
        self.add_concept("Hurricane", parent="SevereStorm")
        self.add_concept("Tornado", parent="SevereStorm")
        self.add_concept("Earthquake", parent="NaturalDisaster")

        # Industrial hazards
        self.add_concept("IndustrialHazard", parent="EmergencyEvent", description="Chemical, biological, radiological hazards")
        self.add_concept("ChemicalSpill", parent="IndustrialHazard")
        self.add_concept("ToxicGasLeak", parent="IndustrialHazard")
        self.add_concept("RadiationLeak", parent="IndustrialHazard")

        # 2. Resource Taxonomy
        self.add_concept("EmergencyResource", description="Root category for operational emergency response assets")

        # Transport resources
        self.add_concept("TransportResource", parent="EmergencyResource")
        self.add_concept("RoadAmbulance", parent="TransportResource")
        self.add_concept("AdvancedLifeSupportAmbulance", parent="RoadAmbulance")
        self.add_concept("BasicLifeSupportAmbulance", parent="RoadAmbulance")
        self.add_concept("AirAmbulance", parent="TransportResource")
        self.add_concept("RescueHelicopter", parent="AirAmbulance")
        self.add_concept("HeavyRescueVehicle", parent="TransportResource")

        # Medical facilities
        self.add_concept("MedicalFacility", parent="EmergencyResource")
        self.add_concept("Level1TraumaCenter", parent="MedicalFacility")
        self.add_concept("CommunityHospital", parent="MedicalFacility")
        self.add_concept("MobileFieldClinic", parent="MedicalFacility")

        # Emergency personnel
        self.add_concept("EmergencyPersonnel", parent="EmergencyResource")
        self.add_concept("ParamedicCrew", parent="EmergencyPersonnel")
        self.add_concept("TraumaPhysician", parent="EmergencyPersonnel")
        self.add_concept("HazmatSpecialist", parent="EmergencyPersonnel")
        self.add_concept("SearchAndRescueTeam", parent="EmergencyPersonnel")

        # Equipment resources
        self.add_concept("EquipmentResource", parent="EmergencyResource")
        self.add_concept("LifeSupportEquipment", parent="EquipmentResource")
        self.add_concept("Defibrillator", parent="LifeSupportEquipment")
        self.add_concept("PortableVentilator", parent="LifeSupportEquipment")
        self.add_concept("OxygenSupplyUnit", parent="LifeSupportEquipment")
        self.add_concept("ExtricationGear", parent="EquipmentResource")
        self.add_concept("JawsOfLife", parent="ExtricationGear")
        self.add_concept("HazmatProtectiveGear", parent="EquipmentResource")

        # 3. Mereological Composition (part-of)
        self.add_part_of("ParamedicCrew", "AdvancedLifeSupportAmbulance")
        self.add_part_of("Defibrillator", "AdvancedLifeSupportAmbulance")
        self.add_part_of("PortableVentilator", "AdvancedLifeSupportAmbulance")
        self.add_part_of("OxygenSupplyUnit", "AdvancedLifeSupportAmbulance")

        self.add_part_of("ParamedicCrew", "BasicLifeSupportAmbulance")
        self.add_part_of("OxygenSupplyUnit", "BasicLifeSupportAmbulance")

        self.add_part_of("TraumaPhysician", "Level1TraumaCenter")
        self.add_part_of("LifeSupportEquipment", "Level1TraumaCenter")

        self.add_part_of("ExtricationGear", "HeavyRescueVehicle")
        self.add_part_of("JawsOfLife", "HeavyRescueVehicle")
        self.add_part_of("ExtricationGear", "SearchAndRescueTeam")


# Default singleton instance for quick access
default_ontology = EmergencyOntology(populate_defaults=True)

# Legacy backwards-compatible dictionary export
ontology_tree = default_ontology.to_legacy_dict()
