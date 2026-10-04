"""
ResQ-AI Knowledge Representation Schemas.
Pydantic v2 schemas for semantic frames, ontology taxonomies, subsumption reasoning,
and multi-format knowledge graph export.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from app.schemas.common import BaseSchema


# ---------------------------------------------------------
# Semantic Frame Schemas
# ---------------------------------------------------------

class FrameSlotSchema(BaseSchema):
    """Schema representing an individual slot with its facets."""
    name: str
    value: Optional[Any] = None
    default: Optional[Any] = None
    has_constraint: bool = False
    has_if_needed: bool = False
    has_if_added: bool = False
    has_if_removed: bool = False
    doc: Optional[str] = None


class FrameDetailSchema(BaseSchema):
    """Schema representing a complete semantic frame and its slots."""
    name: str
    parent_name: Optional[str] = None
    category: Optional[str] = None
    slots: Dict[str, FrameSlotSchema] = Field(default_factory=dict)
    resolved_values: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------
# Ontology & Subsumption Schemas
# ---------------------------------------------------------

class OntologyTaxonomyNode(BaseSchema):
    """Node in an ontology taxonomy DAG."""
    name: str
    parent: Optional[str] = None
    children: List[str] = Field(default_factory=list)
    depth: int = 0
    description: Optional[str] = None
    parts: List[str] = Field(default_factory=list)


class OntologyTaxonomyResponse(BaseSchema):
    """Hierarchical taxonomy representation for frontend trees."""
    root: str
    taxonomy_type: str = "emergency"
    nodes: Dict[str, OntologyTaxonomyNode] = Field(default_factory=dict)
    total_concepts: int = 0


class SubsumptionCheckRequest(BaseSchema):
    """Request payload for subsumption verification."""
    parent: str
    child: str


class SubsumptionCheckResponse(BaseSchema):
    """Response payload for concept subsumption check."""
    parent: str
    child: str
    is_subsumed: bool
    ancestor_path: List[str] = Field(default_factory=list)
    distance: Optional[int] = None


class LCSRequest(BaseSchema):
    """Request payload for Least Common Subsumer calculation."""
    concept_a: str
    concept_b: str


class LCSResponse(BaseSchema):
    """Response payload for Least Common Subsumer."""
    concept_a: str
    concept_b: str
    least_common_subsumer: Optional[str] = None
    depth: Optional[int] = None


class MereologyQueryRequest(BaseSchema):
    """Request payload for part-whole queries."""
    concept: str


class MereologyQueryResponse(BaseSchema):
    """Response payload for mereological composition queries."""
    concept: str
    parts: List[str] = Field(default_factory=list)
    sub_parts: List[str] = Field(default_factory=list)


# ---------------------------------------------------------
# Knowledge Graph Visualization Schemas
# ---------------------------------------------------------

class KnowledgeGraphNode(BaseSchema):
    """Node in the ResQ-AI knowledge graph."""
    id: str
    label: str
    category: str = Field(description="incident, ambulance, hospital, road, resource, ontology_class")
    node_type: str = Field(description="Specific subtype or class name")
    status: Optional[str] = None
    severity: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    position: Optional[Dict[str, float]] = None


class KnowledgeGraphEdge(BaseSchema):
    """Edge in the ResQ-AI knowledge graph."""
    id: str
    source: str
    target: str
    relationship: str = Field(description="is_a, part_of, allocated_to, located_at, connected_to, requires")
    edge_type: str = Field(description="taxonomy, mereology, allocation, spatial, operational")
    weight: Optional[float] = 1.0
    properties: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphExport(BaseSchema):
    """Comprehensive graph serialization format."""
    graph_id: str = "resq_knowledge_graph"
    nodes: List[KnowledgeGraphNode] = Field(default_factory=list)
    edges: List[KnowledgeGraphEdge] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CytoscapeGraphResponse(BaseSchema):
    """Cytoscape.js compatible graph format."""
    elements: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=lambda: {"nodes": [], "edges": []}
    )


class D3GraphResponse(BaseSchema):
    """D3.js force layout compatible graph format."""
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    links: List[Dict[str, Any]] = Field(default_factory=list)
