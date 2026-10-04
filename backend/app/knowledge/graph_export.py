"""
ResQ-AI Knowledge Graph Visualization Serializer.
Module VI: Knowledge Representation.

Aggregates semantic frames, ontology DAGs, road topology, and active resource allocations
into unified graph representations for Cytoscape.js, D3.js force layouts, and standard JSON.
"""

from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Set, Union

from app.knowledge.frames import (
    Frame,
    IncidentFrame,
    AmbulanceFrame,
    HospitalFrame,
    RoadFrame,
    ResourceFrame,
)
from app.knowledge.ontology import EmergencyOntology, default_ontology
from app.schemas.knowledge import (
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    KnowledgeGraphExport,
    CytoscapeGraphResponse,
    D3GraphResponse,
)


# Canonical 2D spatial layout coordinates for road vertices and facilities
CANONICAL_COORDINATES: Dict[str, Dict[str, float]] = {
    "A1": {"x": 60.0, "y": 100.0},
    "A2": {"x": 80.0, "y": 280.0},
    "A3": {"x": 40.0, "y": 190.0},
    "H1": {"x": 340.0, "y": 90.0},
    "H2": {"x": 360.0, "y": 260.0},
    "N1": {"x": 120.0, "y": 110.0},
    "N2": {"x": 180.0, "y": 170.0},
    "N3": {"x": 240.0, "y": 210.0},
    "N4": {"x": 200.0, "y": 80.0},
    "N5": {"x": 280.0, "y": 150.0},
}


class KnowledgeGraphExporter:
    """
    Constructs multi-format serializations of the ResQ-AI knowledge network.
    Combines operational entities, spatial topologies, and ontology concepts.
    """
    def __init__(
        self,
        frames: Optional[List[Frame]] = None,
        ontology: Optional[EmergencyOntology] = None,
        graph_id: str = "resq_knowledge_graph",
    ):
        self.graph_id = graph_id
        self.frames: List[Frame] = list(frames or [])
        self.ontology: EmergencyOntology = ontology or default_ontology
        self._nodes: Dict[str, KnowledgeGraphNode] = {}
        self._edges: Dict[str, KnowledgeGraphEdge] = {}

    def add_frame(self, frame: Frame) -> None:
        """Register a semantic frame for graph inclusion."""
        self.frames.append(frame)

    def set_frames(self, frames: List[Frame]) -> None:
        """Set the active list of frames."""
        self.frames = list(frames)

    def _build_ontology_graph(self) -> None:
        """Populate nodes and edges from the concept taxonomy DAG."""
        for name, node in self.ontology.nodes.items():
            depth = self.ontology.get_depth(name)
            # Layout ontology concepts in a hierarchical grid
            x_pos = 500.0 + (depth * 90.0)
            # Hash-based vertical spread for determinism
            hash_idx = sum(ord(c) for c in name) % 15
            y_pos = 40.0 + (hash_idx * 35.0)

            node_schema = KnowledgeGraphNode(
                id=f"ont_{name}",
                label=name,
                category="ontology_class",
                node_type="Concept",
                status="active",
                properties={
                    "description": node.description,
                    "depth": depth,
                    "is_root": node.parent is None,
                },
                position={"x": float(x_pos), "y": float(y_pos)},
            )
            self._nodes[node_schema.id] = node_schema

            # is-a subsumption edges
            if node.parent:
                edge_id = f"edge_isa_{name}_{node.parent}"
                self._edges[edge_id] = KnowledgeGraphEdge(
                    id=edge_id,
                    source=f"ont_{name}",
                    target=f"ont_{node.parent}",
                    relationship="is_a",
                    edge_type="taxonomy",
                    weight=1.0,
                    properties={"transitive": True},
                )

            # part-of mereological edges
            for part in node.parts:
                edge_id = f"edge_partof_{part}_{name}"
                self._edges[edge_id] = KnowledgeGraphEdge(
                    id=edge_id,
                    source=f"ont_{part}",
                    target=f"ont_{name}",
                    relationship="part_of",
                    edge_type="mereology",
                    weight=1.0,
                    properties={"composition": True},
                )

    def _build_operational_graph(self) -> None:
        """Populate nodes and edges from active operational frames."""
        for frame in self.frames:
            cat = frame.category or "entity"
            frame_id = str(frame.name)
            node_id = f"op_{frame_id}"

            # Location and spatial coordinates
            loc = frame.get("location") or frame.get("current_location") or frame.get("source_node")
            pos = CANONICAL_COORDINATES.get(str(loc))

            props = frame.to_dict()

            if isinstance(frame, IncidentFrame) or cat == "incident":
                severity = str(frame.get("severity") or "medium")
                status = str(frame.get("status") or "reported")
                self._nodes[node_id] = KnowledgeGraphNode(
                    id=node_id,
                    label=f"Incident ({frame.get('emergency_type') or 'Emergency'})",
                    category="incident",
                    node_type=str(frame.get("emergency_type") or "Incident"),
                    severity=severity,
                    status=status,
                    properties=props,
                    position=pos,
                )

                # Link incident to location
                if loc and f"op_{loc}" in self._nodes:
                    edge_id = f"edge_located_{frame_id}_{loc}"
                    self._edges[edge_id] = KnowledgeGraphEdge(
                        id=edge_id,
                        source=node_id,
                        target=f"op_{loc}",
                        relationship="located_at",
                        edge_type="spatial",
                    )

                # Link to assigned ambulance
                amb = frame.get("assigned_ambulance")
                if amb:
                    edge_id = f"edge_alloc_amb_{frame_id}_{amb}"
                    self._edges[edge_id] = KnowledgeGraphEdge(
                        id=edge_id,
                        source=node_id,
                        target=f"op_Ambulance_{amb}" if not amb.startswith("op_") else amb,
                        relationship="allocated_to",
                        edge_type="allocation",
                    )

                # Link to assigned hospital
                hosp = frame.get("assigned_hospital")
                if hosp:
                    edge_id = f"edge_alloc_hosp_{frame_id}_{hosp}"
                    self._edges[edge_id] = KnowledgeGraphEdge(
                        id=edge_id,
                        source=node_id,
                        target=f"op_Hospital_{hosp}" if not hosp.startswith("op_") else hosp,
                        relationship="destined_for",
                        edge_type="allocation",
                    )

                # Link to ontology concept if present
                etype = frame.get("emergency_type")
                if etype:
                    classified = self.ontology.classify_incident(str(etype))
                    ont_id = f"ont_{classified}"
                    if ont_id in self._nodes:
                        edge_id = f"edge_class_{frame_id}_{classified}"
                        self._edges[edge_id] = KnowledgeGraphEdge(
                            id=edge_id,
                            source=node_id,
                            target=ont_id,
                            relationship="is_a",
                            edge_type="taxonomy",
                        )

            elif isinstance(frame, AmbulanceFrame) or cat == "ambulance":
                code = str(frame.get("code") or frame_id)
                status = str(frame.get("status") or "available")
                self._nodes[node_id] = KnowledgeGraphNode(
                    id=node_id,
                    label=f"Ambulance {code}",
                    category="ambulance",
                    node_type="RoadAmbulance",
                    status=status,
                    properties=props,
                    position=pos or CANONICAL_COORDINATES.get(code),
                )
                eq = frame.get("equipment_level") or "ALS"
                ont_concept = "AdvancedLifeSupportAmbulance" if eq == "ALS" else "BasicLifeSupportAmbulance"
                if f"ont_{ont_concept}" in self._nodes:
                    edge_id = f"edge_class_{code}_{ont_concept}"
                    self._edges[edge_id] = KnowledgeGraphEdge(
                        id=edge_id,
                        source=node_id,
                        target=f"ont_{ont_concept}",
                        relationship="is_a",
                        edge_type="taxonomy",
                    )

            elif isinstance(frame, HospitalFrame) or cat == "hospital":
                code = str(frame.get("code") or frame_id)
                name = str(frame.get("name") or f"Hospital {code}")
                status = str(frame.get("status") or "open")
                self._nodes[node_id] = KnowledgeGraphNode(
                    id=node_id,
                    label=name,
                    category="hospital",
                    node_type="Level1TraumaCenter",
                    status=status,
                    properties=props,
                    position=pos or CANONICAL_COORDINATES.get(code),
                )
                if "ont_Level1TraumaCenter" in self._nodes:
                    edge_id = f"edge_class_{code}_TraumaCenter"
                    self._edges[edge_id] = KnowledgeGraphEdge(
                        id=edge_id,
                        source=node_id,
                        target="ont_Level1TraumaCenter",
                        relationship="is_a",
                        edge_type="taxonomy",
                    )

            elif isinstance(frame, RoadFrame) or cat == "road":
                u = str(frame.get("source_node") or "")
                v = str(frame.get("target_node") or "")
                is_blocked = bool(frame.get("is_blocked"))
                cost = frame.get("effective_cost")
                edge_id = f"edge_road_{u}_{v}"

                # Ensure source and target nodes exist in graph
                for node_name in [u, v]:
                    if node_name and f"op_{node_name}" not in self._nodes:
                        self._nodes[f"op_{node_name}"] = KnowledgeGraphNode(
                            id=f"op_{node_name}",
                            label=f"Intersection {node_name}",
                            category="road_node",
                            node_type="Intersection",
                            position=CANONICAL_COORDINATES.get(node_name),
                        )

                self._edges[edge_id] = KnowledgeGraphEdge(
                    id=edge_id,
                    source=f"op_{u}",
                    target=f"op_{v}",
                    relationship="connected_to",
                    edge_type="spatial",
                    weight=float(cost) if cost != float("inf") else 999.0,
                    properties={
                        "is_blocked": is_blocked,
                        "distance": frame.get("distance"),
                        "traffic_factor": frame.get("traffic_factor"),
                        "risk_factor": frame.get("risk_factor"),
                        "effective_cost": cost,
                    },
                )

            elif isinstance(frame, ResourceFrame) or cat == "resource":
                name = str(frame.get("name") or "Resource")
                self._nodes[node_id] = KnowledgeGraphNode(
                    id=node_id,
                    label=name,
                    category="resource",
                    node_type=str(frame.get("category") or "Equipment"),
                    properties=props,
                    position=pos,
                )

    def export_combined_graph(self) -> KnowledgeGraphExport:
        """Construct full multi-layer knowledge graph."""
        self._nodes.clear()
        self._edges.clear()
        self._build_ontology_graph()
        self._build_operational_graph()

        return KnowledgeGraphExport(
            graph_id=self.graph_id,
            nodes=list(self._nodes.values()),
            edges=list(self._edges.values()),
            metadata={
                "total_nodes": len(self._nodes),
                "total_edges": len(self._edges),
                "ontology_nodes": sum(1 for n in self._nodes.values() if n.category == "ontology_class"),
                "operational_nodes": sum(1 for n in self._nodes.values() if n.category != "ontology_class"),
            },
        )

    def export_ontology_subgraph(self) -> KnowledgeGraphExport:
        """Construct graph containing only ontology taxonomy and mereology."""
        self._nodes.clear()
        self._edges.clear()
        self._build_ontology_graph()

        return KnowledgeGraphExport(
            graph_id=f"{self.graph_id}_ontology",
            nodes=list(self._nodes.values()),
            edges=list(self._edges.values()),
            metadata={"subgraph": "ontology", "total_nodes": len(self._nodes), "total_edges": len(self._edges)},
        )

    def export_operational_subgraph(self) -> KnowledgeGraphExport:
        """Construct graph containing only live operational entities and spatial links."""
        self._nodes.clear()
        self._edges.clear()
        self._build_operational_graph()

        return KnowledgeGraphExport(
            graph_id=f"{self.graph_id}_operational",
            nodes=list(self._nodes.values()),
            edges=list(self._edges.values()),
            metadata={"subgraph": "operational", "total_nodes": len(self._nodes), "total_edges": len(self._edges)},
        )

    def export_subgraph(self, category: str) -> KnowledgeGraphExport:
        """Filter graph nodes and matching edges by category."""
        full_graph = self.export_combined_graph()
        filtered_nodes = [n for n in full_graph.nodes if n.category == category]
        valid_ids = {n.id for n in filtered_nodes}
        filtered_edges = [
            e for e in full_graph.edges
            if e.source in valid_ids and e.target in valid_ids
        ]
        return KnowledgeGraphExport(
            graph_id=f"{self.graph_id}_{category}",
            nodes=filtered_nodes,
            edges=filtered_edges,
            metadata={"category": category, "total_nodes": len(filtered_nodes), "total_edges": len(filtered_edges)},
        )

    def to_json(self) -> Dict[str, Any]:
        """Export standard JSON dictionary."""
        return self.export_combined_graph().model_dump()

    def to_cytoscape(self, subgraph: Optional[str] = None) -> CytoscapeGraphResponse:
        """
        Export Cytoscape.js format:
        {
          "elements": {
            "nodes": [{"data": {...}, "position": {...}}],
            "edges": [{"data": {...}}]
          }
        }
        """
        if subgraph == "ontology":
            graph = self.export_ontology_subgraph()
        elif subgraph == "operational":
            graph = self.export_operational_subgraph()
        else:
            graph = self.export_combined_graph()

        cyto_nodes: List[Dict[str, Any]] = []
        for n in graph.nodes:
            item: Dict[str, Any] = {
                "data": {
                    "id": n.id,
                    "label": n.label,
                    "category": n.category,
                    "node_type": n.node_type,
                    "status": n.status,
                    "severity": n.severity,
                    **n.properties,
                }
            }
            if n.position:
                item["position"] = n.position
            cyto_nodes.append(item)

        cyto_edges: List[Dict[str, Any]] = []
        for e in graph.edges:
            cyto_edges.append({
                "data": {
                    "id": e.id,
                    "source": e.source,
                    "target": e.target,
                    "label": e.relationship,
                    "relationship": e.relationship,
                    "edge_type": e.edge_type,
                    "weight": e.weight,
                    **e.properties,
                }
            })

        return CytoscapeGraphResponse(elements={"nodes": cyto_nodes, "edges": cyto_edges})

    def to_d3(self, subgraph: Optional[str] = None) -> D3GraphResponse:
        """
        Export D3.js force layout format:
        {
          "nodes": [{"id": ..., "name": ..., "group": ...}],
          "links": [{"source": ..., "target": ..., "type": ...}]
        }
        """
        if subgraph == "ontology":
            graph = self.export_ontology_subgraph()
        elif subgraph == "operational":
            graph = self.export_operational_subgraph()
        else:
            graph = self.export_combined_graph()

        d3_nodes: List[Dict[str, Any]] = []
        for n in graph.nodes:
            node_dict: Dict[str, Any] = {
                "id": n.id,
                "name": n.label,
                "group": n.category,
                "category": n.category,
                "node_type": n.node_type,
                "status": n.status,
                "severity": n.severity,
            }
            if n.position:
                node_dict["x"] = n.position.get("x")
                node_dict["y"] = n.position.get("y")
            d3_nodes.append(node_dict)

        d3_links: List[Dict[str, Any]] = []
        for e in graph.edges:
            d3_links.append({
                "source": e.source,
                "target": e.target,
                "type": e.relationship,
                "value": e.weight or 1.0,
                "edge_type": e.edge_type,
            })

        return D3GraphResponse(nodes=d3_nodes, links=d3_links)
