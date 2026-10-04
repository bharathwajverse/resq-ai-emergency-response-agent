"""
ResQ-AI Planning REST API Router.

Provides endpoints for automated classical and hierarchical response planning:
- POST /api/planning/generate: Generates response plans across Hierarchical (HTN),
  State-Space (STRIPS BFS/Heuristic), and Partial-Order Planning (POP) paradigms.
- Handles empty/default payloads from frontend Planning.jsx seamlessly.
- Optionally integrates with database models (Incident, ResponsePlan) when available.
"""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.incident import Incident
from app.models.response_plan import ResponsePlan
from app.planning.htn import HTNPlanner
from app.planning.pop import PartialOrderPlanner
from app.planning.state_space import StateSpacePlanner
from app.planning.strips import create_emergency_planning_problem
from app.schemas.planning import (
    PlanActionStep,
    PlanCausalLink,
    PlanGenerateRequest,
    PlanGenerateResponse,
    PlanParadigm,
)

router = APIRouter()
htn_planner = HTNPlanner()
pop_planner = PartialOrderPlanner()


@router.post("/generate", response_model=PlanGenerateResponse)
def generate_plan(
    req: PlanGenerateRequest = Body(default_factory=PlanGenerateRequest),
    db: Optional[Session] = Depends(get_db),
) -> PlanGenerateResponse:
    """
    Generate an emergency response plan using the requested paradigm:
    - Hierarchical: Hierarchical Task Network decomposing compound tasks
    - State-Space: Forward progression STRIPS state-space search with BFS/A*
    - Partial-Order: Least-commitment POP with causal links and threat resolution
    """
    # 1. Resolve incident attributes from request or database
    incident_id = req.incident_id or f"INC-{uuid.uuid4().hex[:6].upper()}"
    emergency_type = req.emergency_type or "Road accident"
    start_node = req.start_node or "Central_Base"
    destination_node = req.destination_node or "Accident_Site"
    hospital_node = "City_General"
    victim_count = 4

    if db is not None and req.incident_id:
        try:
            db_incident = db.query(Incident).filter(
                Incident.id == uuid.UUID(req.incident_id)
            ).first()
            if db_incident:
                emergency_type = db_incident.emergency_type or emergency_type
                destination_node = db_incident.location or destination_node
                victim_count = db_incident.victim_count or victim_count
        except Exception:
            # Fall back to deterministic defaults on invalid UUID or DB query error
            pass

    # 2. Paradigm: HIERARCHICAL (HTN)
    if req.paradigm == PlanParadigm.HIERARCHICAL:
        htn_res = htn_planner.plan_emergency(
            emergency_type=emergency_type,
            incident_id=incident_id,
            ambulance="A2",
            hospital=hospital_node,
            location=destination_node,
            station=start_node,
            victims=victim_count,
        )

        steps: List[PlanActionStep] = [
            PlanActionStep(
                step=act["step"],
                id=act["id"],
                action=act["action"],
                status=act.get("status", "pending"),
                dependencies=act.get("dependencies", []),
                resource=act.get("resource"),
                origin=act.get("origin"),
                destination=act.get("destination"),
                est_time_min=act.get("est_time_min"),
                details=act.get("details"),
            )
            for act in htn_res["actions"]
        ]

        response = PlanGenerateResponse(
            plan_id=str(uuid.uuid4()),
            paradigm=PlanParadigm.HIERARCHICAL,
            initial_state=htn_res["initial_state"],
            goal_state=htn_res["goal_state"],
            initialState=htn_res["initialState"],
            goal=htn_res["goal"],
            actions=steps,
            dependencies=[
                {"action": k, "depends_on": ",".join(v)}
                for k, v in htn_res["dependencies"].items()
            ],
            decomposition_tree=htn_res["decomposition_tree"],
            estimated_duration_minutes=htn_res["estimated_duration_minutes"],
            nodes_explored=len(steps),
            success=True,
        )

    # 3. Paradigm: STATE-SPACE (STRIPS Progression BFS / Heuristic)
    elif req.paradigm == PlanParadigm.STATE_SPACE:
        init_s, goal_s, ground_acts = create_emergency_planning_problem(
            ambulance="A1",
            station=start_node,
            incident=incident_id,
            scene=destination_node,
            hospital=hospital_node,
            include_bed_prep=True,
        )

        planner = StateSpacePlanner(
            initial_state=init_s,
            goal_state=goal_s,
            actions=ground_acts,
        )
        strat = req.search_strategy or "bfs"
        detailed_res = planner.plan_detailed(search_strategy=strat)

        steps: List[PlanActionStep] = []
        for idx, act in enumerate(detailed_res.actions, start=1):
            act_name = act.name if hasattr(act, "name") else str(act)
            dur = act.duration_minutes if hasattr(act, "duration_minutes") else 5.0
            steps.append(
                PlanActionStep(
                    step=idx,
                    id=idx,
                    action=act_name,
                    status="done" if idx == 1 else ("active" if idx == 2 else "pending"),
                    dependencies=[idx - 1] if idx > 1 else [],
                    resource="A1",
                    origin=start_node if idx <= 2 else destination_node,
                    destination=destination_node if idx <= 3 else hospital_node,
                    est_time_min=dur,
                    details={"cost": act.cost if hasattr(act, "cost") else 1.0},
                )
            )

        init_list = sorted(list(init_s))
        goal_list = sorted(list(goal_s))

        response = PlanGenerateResponse(
            plan_id=str(uuid.uuid4()),
            paradigm=PlanParadigm.STATE_SPACE,
            initial_state=init_list,
            goal_state=goal_list,
            initialState=f"Available(A1) at {start_node}, Incident at {destination_node}",
            goal=f"Admitted at {hospital_node}, BedPrepared, Available(A1)",
            actions=steps,
            dependencies=[
                {"action": step.action, "depends_on": str(step.dependencies)}
                for step in steps
            ],
            estimated_duration_minutes=detailed_res.duration_minutes,
            nodes_explored=detailed_res.nodes_explored,
            success=detailed_res.success,
        )

    # 4. Paradigm: PARTIAL-ORDER (POP)
    elif req.paradigm == PlanParadigm.PARTIAL_ORDER:
        init_s, goal_s, ground_acts = create_emergency_planning_problem(
            ambulance="A1",
            station=start_node,
            incident=incident_id,
            scene=destination_node,
            hospital=hospital_node,
            include_bed_prep=True,
        )

        pop_res = pop_planner.solve(
            initial_state=init_s,
            goal_state=goal_s,
            domain_actions=ground_acts,
        )

        steps: List[PlanActionStep] = []
        for idx, act_name in enumerate(pop_res.linearized_plan, start=1):
            act_obj = pop_res.actions.get(act_name)
            dur = act_obj.duration_minutes if act_obj else 5.0
            # Dependencies from ordering constraints
            prev_deps = [
                pop_res.linearized_plan.index(oc.before_id) + 1
                for oc in pop_res.orderings
                if oc.after_id == act_name and oc.before_id in pop_res.linearized_plan
            ]
            steps.append(
                PlanActionStep(
                    step=idx,
                    id=idx,
                    action=act_name,
                    status="done" if idx == 1 else ("active" if idx == 2 else "pending"),
                    dependencies=sorted(list(set(prev_deps))),
                    resource="A1",
                    origin=start_node if idx <= 2 else destination_node,
                    destination=destination_node if idx <= 3 else hospital_node,
                    est_time_min=dur,
                    details={"action_id": act_name},
                )
            )

        causal_schema_links = [
            PlanCausalLink(
                source_action=cl.source_id,
                condition=cl.condition,
                target_action=cl.target_id,
            )
            for cl in pop_res.causal_links
        ]

        init_list = sorted(list(init_s))
        goal_list = sorted(list(goal_s))

        response = PlanGenerateResponse(
            plan_id=str(uuid.uuid4()),
            paradigm=PlanParadigm.PARTIAL_ORDER,
            initial_state=init_list,
            goal_state=goal_list,
            initialState=f"Available(A1) at {start_node}, Incident at {destination_node}",
            goal=f"Admitted at {hospital_node}, BedPrepared, Available(A1)",
            actions=steps,
            dependencies=[
                {"before": oc.before_id, "after": oc.after_id}
                for oc in pop_res.orderings
            ],
            causal_links=causal_schema_links,
            estimated_duration_minutes=pop_res.estimated_duration_minutes,
            nodes_explored=len(pop_res.actions),
            success=pop_res.success,
        )

    else:
        # Fallback default
        return generate_plan(
            req=PlanGenerateRequest(paradigm=PlanParadigm.HIERARCHICAL),
            db=db,
        )

    # 5. Optionally persist ResponsePlan in database if DB session available
    if db is not None:
        try:
            inc_uuid = None
            if req.incident_id:
                try:
                    inc_uuid = uuid.UUID(req.incident_id)
                except Exception:
                    pass
            new_plan_record = ResponsePlan(
                incident_id=inc_uuid,
                plan_type=req.paradigm.value,
                status="Generated",
                initial_state=response.initial_state,
                goal_state=response.goal_state,
                actions=[s.model_dump() for s in response.actions],
                dependencies=response.dependencies,
                estimated_duration_minutes=response.estimated_duration_minutes,
            )
            db.add(new_plan_record)
            db.commit()
            db.refresh(new_plan_record)
            response.plan_id = str(new_plan_record.id)
        except Exception:
            # Non-blocking DB persistence failure
            pass

    return response
