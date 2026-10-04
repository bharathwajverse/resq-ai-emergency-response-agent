"""
ResQ-AI Knowledge Representation Package.
Module VI: Knowledge Representation.

Centralized exports for semantic frames, ontology taxonomies,
relational rules, and knowledge graph exporters.
"""

from app.knowledge.frames import (
    Facet,
    Slot,
    Frame,
    IncidentFrame,
    AmbulanceFrame,
    HospitalFrame,
    RoadFrame,
    ResourceFrame,
    create_canonical_frames,
    create_frames,
)
from app.knowledge.ontology import (
    CyclicOntologyError,
    OntologyNode,
    EmergencyOntology,
    default_ontology,
    ontology_tree,
)
from app.knowledge.relationships import (
    relationships,
    RESOURCE_REQUIREMENTS,
    get_required_resources_for_type,
    is_hospital_compatible,
)
from app.knowledge.graph_export import (
    CANONICAL_COORDINATES,
    KnowledgeGraphExporter,
)
from app.knowledge.knowledge_base import (
    KnowledgeBase,
)

__all__ = [
    "Facet",
    "Slot",
    "Frame",
    "IncidentFrame",
    "AmbulanceFrame",
    "HospitalFrame",
    "RoadFrame",
    "ResourceFrame",
    "create_canonical_frames",
    "create_frames",
    "CyclicOntologyError",
    "OntologyNode",
    "EmergencyOntology",
    "default_ontology",
    "ontology_tree",
    "relationships",
    "RESOURCE_REQUIREMENTS",
    "get_required_resources_for_type",
    "is_hospital_compatible",
    "CANONICAL_COORDINATES",
    "KnowledgeGraphExporter",
    "KnowledgeBase",
]
