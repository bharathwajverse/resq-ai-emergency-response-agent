"""
ResQ-AI Central Knowledge Base Container.
Module VI: Knowledge Representation.

Integrates Semantic Frames, Ontology Taxonomies, Domain Relationships,
and Graph Export into a unified reasoning and query façade.
Preserves backwards compatibility with legacy fact/rule key-value operations.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Set, Union

from app.knowledge.frames import (
    Frame,
    IncidentFrame,
    AmbulanceFrame,
    HospitalFrame,
    RoadFrame,
    ResourceFrame,
    create_canonical_frames,
)
from app.knowledge.ontology import EmergencyOntology, default_ontology
from app.knowledge.relationships import (
    relationships,
    get_required_resources_for_type,
    is_hospital_compatible,
)
from app.knowledge.graph_export import KnowledgeGraphExporter


class KnowledgeBase:
    """
    Unified Knowledge Base container for ResQ-AI.
    Combines frame-based memory, Description Logic ontology reasoning,
    and fact-rule working memory.
    """
    def __init__(
        self,
        ontology: Optional[EmergencyOntology] = None,
        load_canonical_prototypes: bool = True,
    ):
        # Legacy fact and rule stores
        self.facts: Dict[str, Any] = {}
        self.rules: List[Any] = []

        # Frame repository (indexed by frame name)
        self.frames: Dict[str, Frame] = {}

        # Ontology reasoning engine
        self.ontology: EmergencyOntology = ontology or default_ontology

        if load_canonical_prototypes:
            for name, proto in create_canonical_frames().items():
                self.register_frame(proto)

    # -------------------------------------------------------------------------
    # Legacy Fact and Rule Interface
    # -------------------------------------------------------------------------

    def add_fact(self, key: str, value: Any) -> None:
        """Register a ground fact in working memory."""
        self.facts[key] = value

    def add_rule(self, rule: Any) -> None:
        """Register an operational production rule."""
        self.rules.append(rule)

    def query(self, key: str) -> Any:
        """Query fact value by key."""
        return self.facts.get(key)

    # -------------------------------------------------------------------------
    # Frame Management
    # -------------------------------------------------------------------------

    def register_frame(self, frame: Frame) -> None:
        """Register or update a semantic frame in the knowledge base."""
        self.frames[frame.name] = frame

    def get_frame(self, name: str) -> Optional[Frame]:
        """Retrieve a semantic frame by identifier."""
        return self.frames.get(name)

    def remove_frame(self, name: str) -> None:
        """Remove a semantic frame from the repository."""
        if name in self.frames:
            del self.frames[name]

    def list_frames(self, category: Optional[str] = None) -> List[Frame]:
        """List all registered frames, optionally filtered by category."""
        if category is None:
            return list(self.frames.values())
        return [f for f in self.frames.values() if f.category == category]

    # -------------------------------------------------------------------------
    # Ontology Facade Queries
    # -------------------------------------------------------------------------

    def subsumes(self, parent: str, child: str) -> bool:
        """Transitive subsumption query: does parent subsume child?"""
        return self.ontology.subsumes(parent=parent, child=child)

    def is_a(self, child: str, parent: str) -> bool:
        """Convenience alias: is child an instance/specialization of parent?"""
        return self.ontology.is_a(child=child, parent=parent)

    def least_common_subsumer(self, concept_a: str, concept_b: str) -> Optional[str]:
        """Calculate the Least Common Subsumer between two emergency concepts."""
        return self.ontology.least_common_subsumer(concept_a, concept_b)

    def classify_incident(
        self,
        raw_type: str,
        victims: int = 1,
        severity: str = "medium",
    ) -> str:
        """Classify natural emergency description into taxonomy concept."""
        return self.ontology.classify_incident(raw_type, victims=victims, severity=severity)

    def infer_required_resources(
        self,
        emergency_type: str,
        victims: int = 1,
    ) -> List[str]:
        """Infer required equipment and specialist resources for an emergency."""
        return self.ontology.infer_required_resources(emergency_type, victims=victims)

    # -------------------------------------------------------------------------
    # Operational Queries & CSP Bridge
    # -------------------------------------------------------------------------

    def query_available_ambulances(
        self,
        min_capacity: int = 1,
        required_equipment: Optional[str] = None,
    ) -> List[Frame]:
        """
        Query available ambulances meeting victim capacity and equipment level.
        Uses procedural attachments (available_capacity) to filter units.
        """
        results: List[Frame] = []
        for frame in self.list_frames(category="ambulance"):
            status = str(frame.get("status") or "").lower()
            if status != "available":
                continue

            avail_cap = frame.get("available_capacity") or 0
            if avail_cap < min_capacity:
                continue

            if required_equipment:
                eq = str(frame.get("equipment_level") or "").upper()
                if required_equipment.upper() == "ALS" and eq != "ALS":
                    continue

            results.append(frame)

        return results

    def query_available_hospitals(
        self,
        required_trauma_level: int = 1,
        min_beds: int = 1,
    ) -> List[Frame]:
        """
        Query non-diverted hospitals with sufficient available emergency intake beds.
        """
        results: List[Frame] = []
        for frame in self.list_frames(category="hospital"):
            status = str(frame.get("status") or "").lower()
            if status in ["divert", "full"]:
                continue

            avail_beds = frame.get("available_beds") or 0
            if avail_beds < min_beds:
                continue

            trauma = frame.get("trauma_level") or 1
            if trauma > required_trauma_level:
                continue

            results.append(frame)

        return results

    def query_incident_requirements(self, incident_frame_id: str) -> Dict[str, Any]:
        """
        Derive comprehensive equipment, personnel, and facility requirements for an incident.
        Combines frame state with ontology inference and relationship catalogs.
        """
        incident = self.get_frame(incident_frame_id)
        if not incident:
            return {}

        etype = incident.get("emergency_type") or "Medical Emergency"
        victims = incident.get("victim_count") or 1
        sev = incident.get("severity") or "medium"

        # Classify via ontology
        canonical_class = self.classify_incident(str(etype), victims=victims, severity=str(sev))

        # Ontology resource requirements
        ontology_resources = self.infer_required_resources(canonical_class, victims=victims)

        # Catalog relationships
        catalog_resources = get_required_resources_for_type(canonical_class)

        all_resources = list(dict.fromkeys(ontology_resources + catalog_resources))

        return {
            "incident_id": incident.name,
            "canonical_concept": canonical_class,
            "subsumed_by_mass_casualty": self.subsumes("MassCasualtyTrauma", canonical_class),
            "subsumed_by_traffic": self.subsumes("TrafficEmergency", canonical_class),
            "subsumed_by_hazmat": self.subsumes("IndustrialHazard", canonical_class),
            "required_resources": all_resources,
            "min_ambulance_capacity": victims,
            "requires_als": any(r in ["AdvancedLifeSupportAmbulance", "Defibrillator", "PortableVentilator"] for r in all_resources),
            "priority": incident.get("priority"),
        }

    # -------------------------------------------------------------------------
    # ORM Model Hydration
    # -------------------------------------------------------------------------

    def hydrate_from_models(
        self,
        incidents: Optional[List[Any]] = None,
        ambulances: Optional[List[Any]] = None,
        hospitals: Optional[List[Any]] = None,
        roads: Optional[List[Any]] = None,
        resources: Optional[List[Any]] = None,
    ) -> None:
        """Hydrate knowledge base frames from SQLAlchemy ORM entities."""
        if incidents:
            for inc in incidents:
                self.register_frame(IncidentFrame.from_orm(inc))
        if ambulances:
            for amb in ambulances:
                self.register_frame(AmbulanceFrame.from_orm(amb))
        if hospitals:
            for hosp in hospitals:
                self.register_frame(HospitalFrame.from_orm(hosp))
        if roads:
            for road in roads:
                self.register_frame(RoadFrame.from_orm(road))
        if resources:
            for res in resources:
                self.register_frame(ResourceFrame.from_orm(res))

    # -------------------------------------------------------------------------
    # Knowledge Graph Visualization Exporter
    # -------------------------------------------------------------------------

    def export_graph(
        self,
        format: str = "json",
        subgraph: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Serialize current knowledge base to specified visualization format.
        format: 'json', 'cytoscape', or 'd3'
        subgraph: None (combined), 'ontology', or 'operational'
        """
        exporter = KnowledgeGraphExporter(
            frames=list(self.frames.values()),
            ontology=self.ontology,
        )

        fmt = format.lower()
        if fmt == "cytoscape":
            return exporter.to_cytoscape(subgraph=subgraph).model_dump()
        elif fmt == "d3":
            return exporter.to_d3(subgraph=subgraph).model_dump()
        else:
            if subgraph == "ontology":
                return exporter.export_ontology_subgraph().model_dump()
            elif subgraph == "operational":
                return exporter.export_operational_subgraph().model_dump()
            return exporter.export_combined_graph().model_dump()

    def export_all_facts(self) -> List[str]:
        """Aggregate all ground facts from both key-value store and frames."""
        fact_strings: List[str] = []
        for k, v in self.facts.items():
            fact_strings.append(f"{k} = {v}")
        for frame in self.frames.values():
            fact_strings.extend(frame.to_facts())
        return sorted(list(set(fact_strings)))
