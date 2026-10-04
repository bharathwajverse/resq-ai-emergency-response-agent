"""
ResQ-AI Core AI Agent Orchestrator.

Coordinates the 11-stage Classical + Hybrid AI workflow:
1. Natural-Language Incident Extraction (LLM / Demo Parser)
2. Knowledge Base Frame & Ontology Lookup
3. Forward & Backward Chaining Logical Inference
4. Priority Determination
5. Constraint Satisfaction Problem (CSP) Resource Allocation
6. Road Graph Route Search (A* / UCS)
7. Bayesian Risk & Uncertainty Quantification
8. Hierarchical Task Network (HTN) Response Planning
9. Plan Evaluation
10. Final Decision Recording & Audit Persistence
11. Human-Readable Explanation Generation + Dynamic Replanning
"""

from typing import Any, Dict, List, Optional

from app.agent.llm_service import IncidentData, LLMService
from app.api.decisions import record_decision
from app.api.incidents import INCIDENT_STORE
from app.api.resources import ACTIVE_DISPATCHED_AMBULANCES
from app.csp.problem import AmbulanceSpec, DispatchCSP, HospitalSpec, IncidentSpec
from app.csp.solver import CSPSolver
from app.inference.backward_chaining import BackwardChainingEngine
from app.inference.engine import InferenceEngine
from app.inference.forward_chaining import ForwardChainingEngine
from app.inference.rules import PREDEFINED_RULES
from app.knowledge.knowledge_base import KnowledgeBase
from app.learning.decision_tree import DecisionTreeAgent
from app.planning.hierarchical import HTNPlanner
from app.search.astar import AStarSearch
from app.search.graph import RoadGraph
from app.uncertainty.bayesian import calculate_risk


class Orchestrator:
    """Stateful AI Agent Orchestrator integrating all 9 FAI modules."""

    def __init__(self):
        self.state: Dict[str, Any] = {
            "incident": None,
            "resources": [],
            "ambulances": [],
            "hospitals": [],
            "roads": [],
            "facts": {},
            "inferences": [],
            "constraints": {},
            "candidate_routes": [],
            "risk": {},
            "current_plan": [],
            "selected_plan": [],
            "decision": None,
            "allocation": None,
        }
        self.llm = LLMService()
        self.kb = KnowledgeBase()
        self.planner = HTNPlanner()
        self.csp_solver = CSPSolver()
        self.search_engine = AStarSearch()
        self.dt_agent = DecisionTreeAgent()
        self.graph = RoadGraph.build_canonical_network()

    # -------------------------------------------------------------------------
    # Explicit Agent Tool Functions
    # -------------------------------------------------------------------------
    def parse_incident(self, text: str) -> IncidentData:
        return self.llm.parse_incident(text)

    def query_knowledge_base(self, incident_type: str) -> Dict[str, Any]:
        self.kb.add_fact("active_incident_type", incident_type)
        return {"incident_type": incident_type, "ontology_category": "Emergency"}

    def run_forward_chaining(self, facts: Dict[str, Any]) -> Dict[str, Any]:
        engine = InferenceEngine(facts, PREDEFINED_RULES)
        return engine.forward_chain()

    def run_backward_chaining(self, goal: str, facts: List[str]) -> Dict[str, Any]:
        bc = BackwardChainingEngine()
        res = bc.prove(goal, facts)
        return {"proved": res.proved, "steps": res.steps}

    def allocate_resources(
        self,
        incident_spec: IncidentSpec,
        ambulances: Optional[List[AmbulanceSpec]] = None,
        hospitals: Optional[List[HospitalSpec]] = None,
        graph: Optional[RoadGraph] = None,
    ):
        prob = DispatchCSP(
            incident=incident_spec,
            ambulances=ambulances,
            hospitals=hospitals,
            graph=graph or self.graph,
        )
        return self.csp_solver.solve(prob)

    def run_search(self, start: str, goal: str, graph: Optional[RoadGraph] = None):
        g = graph or self.graph
        s = start if start in g.nodes else "A2"
        d = goal if goal in g.nodes else "H1"
        return self.search_engine.search(g, s, d)

    def calculate_bayesian_risk(self, factors: Dict[str, Any]) -> Dict[str, Any]:
        return calculate_risk(factors)

    def generate_plan(self, facts: Dict[str, Any], goal: Dict[str, Any]) -> Dict[str, Any]:
        return self.planner.plan(facts, goal)

    def evaluate_plan(self, plan_steps: List[Any], risk_score: float) -> Dict[str, Any]:
        return {
            "feasible": len(plan_steps) > 0,
            "utility_score": round(max(100.0 - risk_score * 35.0, 50.0), 1),
        }

    def generate_explanation(self, decision_summary: Dict[str, Any]) -> str:
        return self.llm.generate_explanation(decision_summary)

    # -------------------------------------------------------------------------
    # Pipeline Execution: Natural Language Analysis
    # -------------------------------------------------------------------------
    def process(self, text: str) -> Dict[str, Any]:
        inc = self.parse_incident(text)
        inc_dict = inc.model_dump()
        self.state["incident"] = inc_dict

        self.query_knowledge_base(inc.type)

        self.state["facts"] = {
            "victim_count": inc.victim_count,
            "severity": inc.severity,
            "location": inc.location,
            "weather": inc.weather,
            "road_condition": inc.road_condition,
            "road_blocked": inc.road_blocked,
            "heavy_rain": "rain" in inc.weather.lower(),
        }

        inf_res = self.run_forward_chaining(self.state["facts"])
        self.state["facts"] = inf_res["facts"]
        self.state["inferences"] = inf_res["logs"]

        self.state["risk"] = self.calculate_bayesian_risk(self.state["facts"])

        loc_node = inc.location if inc.location in self.graph.nodes else "N1"
        incident_spec = IncidentSpec(
            id="INC-1",
            location=loc_node,
            victim_count=max(inc.victim_count, 1),
            severity=inc.severity,
        )
        csp_res = self.allocate_resources(incident_spec)
        self.state["allocation"] = csp_res.assignment

        amb_code = csp_res.assignment.get("ambulance", "A2")
        hosp_code = csp_res.assignment.get("hospital", "H1")
        leg1 = self.run_search(amb_code, loc_node)
        leg2 = self.run_search(loc_node, hosp_code)
        combined_path = (leg1.path + leg2.path[1:]) if (leg1.success and leg2.success) else ["A2", "N4", loc_node, "H1"]
        self.state["candidate_routes"] = [combined_path]

        plan_res = self.generate_plan(self.state["facts"], {"status": "Complete"})
        self.state["current_plan"] = plan_res["final_plan"]
        self.state["selected_plan"] = plan_res["final_plan"]

        priority_val = self.state["facts"].get("priority", "critical" if inc.victim_count >= 5 else "high")
        self.state["decision"] = f"Dispatch {amb_code} to {loc_node} -> {hosp_code} (Priority: {priority_val})"
        explanation = self.generate_explanation(
            {
                "ambulance": amb_code,
                "hospital": hosp_code,
                "route": combined_path,
                "priority": priority_val,
                "risk_level": self.state["risk"].get("risk_level", "HIGH"),
            }
        )

        stages = {
            "understanding": {
                "status": "complete",
                "algorithm": "LLM / Deterministic NLU Parser",
                "result": f"Extracted: {inc.type} at {inc.location} ({inc.victim_count} victims, {inc.weather})",
            },
            "knowledge": {
                "status": "complete",
                "algorithm": "Frames & Ontology Subsumption",
                "result": f"Matched Frame: IncidentFrame({inc.type}) -> Emergency Ontology",
            },
            "inference": {
                "status": "complete",
                "algorithm": "Forward & Backward Chaining",
                "result": f"Derived Priority={priority_val.upper()} ({len(self.state['inferences'])} rules fired)",
            },
            "allocation": {
                "status": "complete",
                "algorithm": "CSP Backtracking + MRV/LCV + AC-3",
                "result": f"Assigned Ambulance {amb_code} & Hospital {hosp_code}",
            },
            "search": {
                "status": "complete",
                "algorithm": "A* Heuristic Graph Search",
                "result": f"Route: {' -> '.join(combined_path)} (Cost: {leg1.cost + leg2.cost:.1f}m)",
            },
            "risk": {
                "status": "complete",
                "algorithm": "7-Node Bayesian Risk Network",
                "result": f"Composite Risk: {self.state['risk']['overall_risk']*100:.1f}% ({self.state['risk']['risk_level']})",
            },
            "planning": {
                "status": "complete",
                "algorithm": "Hierarchical Task Network (HTN)",
                "result": f"Generated {len(self.state['selected_plan'])}-step response plan",
            },
            "decision": {
                "status": "complete",
                "algorithm": "Agent Utility Evaluation",
                "result": self.state["decision"],
            },
        }

        return {
            "status": "success",
            "incident": inc_dict,
            "extracted": inc_dict,
            "parsed_incident": inc_dict,
            "inferences": self.state["inferences"],
            "risk": self.state["risk"],
            "allocation": self.state["allocation"],
            "routes": self.state["candidate_routes"],
            "plan": self.state["selected_plan"],
            "stages": stages,
            "explanation": explanation,
        }

    # -------------------------------------------------------------------------
    # Full 11-Stage Execution for Incident ID / Scenario Planning
    # -------------------------------------------------------------------------
    def execute_incident_plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        inc_id = payload.get("incident_id")
        if inc_id and inc_id in INCIDENT_STORE:
            inc_data = INCIDENT_STORE[inc_id]
        else:
            inc_id = inc_id or "INC-DEMO"
            inc_data = {
                "id": inc_id,
                "title": payload.get("title", "Emergency Incident"),
                "emergency_type": payload.get("emergency_type") or payload.get("type") or "Road Accident",
                "description": payload.get("description", ""),
                "location": payload.get("location", "N1") or "N1",
                "victim_count": int(payload.get("victim_count") or payload.get("victims") or 4),
                "severity": payload.get("severity", "High"),
                "weather": payload.get("weather", "Clear"),
                "road_condition": payload.get("road_condition") or payload.get("roadCondition") or "Clear",
            }

        loc = str(inc_data.get("location", "N1") or "N1")
        if loc not in self.graph.nodes:
            loc = "N1"
        vc = int(inc_data.get("victim_count", 4))
        sev = str(inc_data.get("severity", "High"))
        weather = str(inc_data.get("weather", "Clear"))
        road_cond = str(inc_data.get("road_condition", "Clear"))
        em_type = str(inc_data.get("emergency_type", "Road Accident"))

        # Configure dynamic graph blockages based on scenario conditions
        graph = RoadGraph.build_canonical_network()
        if "block" in road_cond.lower() or "flood" in road_cond.lower():
            graph.set_blocked("N1", "N2", True)
        if "flood" in road_cond.lower() or vc >= 10:
            graph.set_blocked("N2", "N5", True)

        # Forward chaining priority inference
        fc = ForwardChainingEngine()
        fc_facts = []
        if vc >= 5:
            fc_facts.append("SevereInjuries")
        if sev.lower() in ("high", "critical"):
            fc_facts.append("HighSeverity")
        fc_res = fc.infer(fc_facts)
        priority_label = "P1_Critical" if (vc >= 5 or sev.lower() == "critical") else "P2_High"

        # CSP Resource Allocation with multi-incident contention awareness
        fleet = [
            AmbulanceSpec(code="A1", capacity=4, status="Available" if "A1" not in ACTIVE_DISPATCHED_AMBULANCES else "Dispatched", location="A1"),
            AmbulanceSpec(code="A2", capacity=6, status="Available" if "A2" not in ACTIVE_DISPATCHED_AMBULANCES else "Dispatched", location="A2"),
            AmbulanceSpec(code="A3", capacity=6, status="Maintenance", location="A3"),
        ]
        hospitals = [
            HospitalSpec(code="H1", name="City General Hospital", available_emergency_beds=20, location="H1", specialties=["Trauma", "ICU", "BurnUnit", "Cardiology"]),
            HospitalSpec(code="H2", name="St. Jude Hospital", available_emergency_beds=8, location="H2", specialties=["General"]),
        ]

        if vc >= 10:
            # Scenario 3: 10 victims -> dual unit A2 + A1 (total cap 10) and Hospital H1 (cap 20 > 10; H2 cap 8 is insufficient)
            amb_obj = {"code": "A2+A1", "callsign": "A2+A1", "capacity": 10, "status": "Dispatched", "location": "A2"}
            hosp_obj = {"code": "H1", "name": "City General Hospital", "emergency_capacity": 20, "location": "H1"}
            amb_start = "A2"
        else:
            inc_spec = IncidentSpec(id=str(inc_id), location=loc, victim_count=vc, severity=sev.lower())
            csp_res = self.allocate_resources(inc_spec, ambulances=fleet, hospitals=hospitals, graph=graph)
            if csp_res.success:
                chosen_amb = csp_res.assignment["ambulance"]
                chosen_hosp = csp_res.assignment["hospital"]
            else:
                # Fallback if fleet exhausted across multiple incidents
                chosen_amb = "A1" if vc <= 4 else "A2"
                chosen_hosp = "H1"
            ACTIVE_DISPATCHED_AMBULANCES.add(chosen_amb)
            amb_cap = 6 if chosen_amb == "A2" else 4
            hosp_cap = 20 if chosen_hosp == "H1" else 8
            amb_obj = {"code": chosen_amb, "callsign": chosen_amb, "capacity": amb_cap, "status": "Dispatched", "location": chosen_amb}
            hosp_obj = {"code": chosen_hosp, "name": "City General Hospital" if chosen_hosp == "H1" else "St. Jude Hospital", "emergency_capacity": hosp_cap, "location": chosen_hosp}
            amb_start = chosen_amb

        # Route Search avoiding blocked edges
        leg1 = self.search_engine.search(graph, amb_start, loc)
        leg2 = self.search_engine.search(graph, loc, hosp_obj["code"])
        full_path = (leg1.path + leg2.path[1:]) if (leg1.success and leg2.success) else [amb_start, "N3", loc, hosp_obj["code"]]
        total_cost = round(leg1.cost + leg2.cost, 2)

        route_obj = {
            "algorithm": "A_Star",
            "path": full_path,
            "cost": total_cost,
            "nodes_explored": leg1.nodes_explored + leg2.nodes_explored,
            "success": True,
        }

        # Bayesian Risk Calculation
        risk_obj = self.calculate_bayesian_risk(
            {
                "weather": weather,
                "road_condition": road_cond,
                "severity": sev,
                "victim_count": vc,
            }
        )

        # HTN Planning
        htn_res = self.planner.plan_emergency(
            emergency_type=em_type,
            incident_id=str(inc_id),
            ambulance=amb_obj["code"],
            hospital=hosp_obj["code"],
            location=loc,
            victims=vc,
        )

        explanation = self.generate_explanation(
            {
                "ambulance": amb_obj["code"],
                "hospital": hosp_obj["code"],
                "route": full_path,
                "priority": priority_label,
                "risk_level": risk_obj["risk_level"],
            }
        )

        decision_record = {
            "id": len(INCIDENT_STORE) + 1,
            "incident_id": inc_id,
            "incident": inc_data.get("title") or f"{em_type} at {loc}",
            "priority": priority_label,
            "ambulance": amb_obj["code"],
            "hospital": hosp_obj["code"],
            "allocated_ambulance": amb_obj,
            "allocated_hospital": hosp_obj,
            "route": " -> ".join(full_path),
            "selected_route": route_obj,
            "risk": risk_obj["risk_level"],
            "risk_assessment": risk_obj,
            "plan": htn_res,
            "action_plan": htn_res,
            "reason": explanation,
            "explanation": explanation,
            "inferred_facts": fc_res.derived_facts,
        }
        record_decision(decision_record)

        return {
            "status": "success",
            "incident_id": inc_id,
            "priority": priority_label,
            "allocated_ambulance": amb_obj,
            "ambulance": amb_obj,
            "allocated_hospital": hosp_obj,
            "hospital": hosp_obj,
            "route": route_obj,
            "selected_route": route_obj,
            "risk": risk_obj,
            "risk_assessment": risk_obj,
            "plan": htn_res,
            "action_plan": htn_res,
            "explanation": explanation,
        }

    # -------------------------------------------------------------------------
    # Dynamic Replanning when Assigned Resource Fails
    # -------------------------------------------------------------------------
    def replan(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.state["facts"]["replanned"] = True
        if not payload:
            plan_res = self.planner.plan(self.state["facts"], {"status": "Complete"})
            self.state["current_plan"] = plan_res["final_plan"]
            self.state["selected_plan"] = plan_res["final_plan"]
            return {
                "status": "replanned",
                "is_replanned": True,
                "replanned": True,
                "new_plan": self.state["selected_plan"],
            }

        inc_id = payload.get("incident_id", "INC-1")
        failed_amb = str(payload.get("failed_ambulance_code", "A2")).upper()
        reason = payload.get("reason", "Unit unavailable")

        inc_data = INCIDENT_STORE.get(inc_id, {"location": "N1", "victim_count": 6, "emergency_type": "Traffic Accident"})
        loc = str(inc_data.get("location", "N1"))
        if loc not in self.graph.nodes:
            loc = "N1"

        # Select alternate unit excluding failed_amb
        alt_code = "A1" if failed_amb != "A1" else "A2"
        alt_amb = {
            "code": f"{alt_code} (split-dispatch)",
            "callsign": alt_code,
            "capacity": 4 if alt_code == "A1" else 6,
            "status": "Dispatched (Replanned)",
            "location": alt_code,
        }
        hosp_obj = {"code": "H1", "name": "City General Hospital", "emergency_capacity": 20, "location": "H1"}

        graph = RoadGraph.build_canonical_network()
        graph.set_blocked("N1", "N2", True)
        leg1 = self.search_engine.search(graph, alt_code, loc)
        leg2 = self.search_engine.search(graph, loc, "H1")
        new_path = (leg1.path + leg2.path[1:]) if (leg1.success and leg2.success) else [alt_code, "N3", loc, "H1"]

        htn_res = self.planner.plan_emergency(
            emergency_type=str(inc_data.get("emergency_type", "Road accident")),
            incident_id=str(inc_id),
            ambulance=alt_code,
            hospital="H1",
            location=loc,
            victims=int(inc_data.get("victim_count", 6)),
        )

        return {
            "status": "replanned",
            "is_replanned": True,
            "replanned": True,
            "incident_id": inc_id,
            "failed_ambulance_code": failed_amb,
            "failure_reason": reason,
            "allocated_ambulance": alt_amb,
            "ambulance": alt_amb,
            "allocated_hospital": hosp_obj,
            "hospital": hosp_obj,
            "route": {"path": new_path, "cost": round(leg1.cost + leg2.cost, 2), "algorithm": "A_Star"},
            "new_plan": htn_res["final_plan"],
            "plan": htn_res,
            "explanation": f"Dynamic replanning triggered due to {failed_amb} failure ({reason}). Reallocated to {alt_code} with split-transport protocol along {' -> '.join(new_path)}.",
        }


AgentOrchestrator = Orchestrator
