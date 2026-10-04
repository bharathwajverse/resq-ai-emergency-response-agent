"""
ResQ-AI Hierarchical Task Network (HTN) Planner.

Implements hierarchical decomposition of high-level emergency compound tasks into
executable primitive operations across 5 specialized incident domains:
1. DecomposeRoadAccident
2. DecomposeFireResponse
3. DecomposeFloodResponse
4. DecomposeMedicalEmergency
5. DecomposeMultiIncident

Maintains recursive decomposition trees, step dependencies, resource bindings,
and full backward compatibility with the ResQ-AI Agent Orchestrator and frontend.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union


@dataclass
class Task:
    """Task in a Hierarchical Task Network (either Compound or Primitive)."""
    name: str
    task_type: str  # 'compound' or 'primitive'
    parameters: Dict[str, Any] = field(default_factory=dict)
    subtasks: List["Task"] = field(default_factory=list)
    method_name: Optional[str] = None
    est_time_min: float = 5.0

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "task": self.name,
            "type": self.task_type,
            "parameters": self.parameters,
            "est_time_min": self.est_time_min,
        }
        if self.method_name:
            res["method"] = self.method_name
        if self.subtasks:
            res["subtasks"] = [st.to_dict() for st in self.subtasks]
        return res


@dataclass
class HTNMethod:
    """Decomposition method defining how a compound task expands into subtasks."""
    name: str
    compound_task_name: str
    applicable_types: List[str]
    decompose_fn: Callable[[Dict[str, Any]], List[Task]]


class HTNPlanner:
    """
    Deterministic Hierarchical Task Network (HTN) Planner for emergency dispatch.
    """

    def __init__(self) -> None:
        self.methods: Dict[str, HTNMethod] = {
            "DecomposeRoadAccident": HTNMethod(
                name="DecomposeRoadAccident",
                compound_task_name="ResolveEmergency",
                applicable_types=["road accident", "traffic", "collision", "vehicle", "road_accident"],
                decompose_fn=self._method_road_accident,
            ),
            "DecomposeFireResponse": HTNMethod(
                name="DecomposeFireResponse",
                compound_task_name="ResolveEmergency",
                applicable_types=["fire", "burn", "explosion", "fire response", "fire_response"],
                decompose_fn=self._method_fire_response,
            ),
            "DecomposeFloodResponse": HTNMethod(
                name="DecomposeFloodResponse",
                compound_task_name="ResolveEmergency",
                applicable_types=["flood", "flash flood", "water", "flood response", "flood_response"],
                decompose_fn=self._method_flood_response,
            ),
            "DecomposeMedicalEmergency": HTNMethod(
                name="DecomposeMedicalEmergency",
                compound_task_name="ResolveEmergency",
                applicable_types=["medical", "cardiac", "stroke", "medical emergency", "medical_emergency"],
                decompose_fn=self._method_medical_emergency,
            ),
            "DecomposeMultiIncident": HTNMethod(
                name="DecomposeMultiIncident",
                compound_task_name="ResolveEmergency",
                applicable_types=["multi", "multi-incident", "mass casualty", "multiple", "multi_incident"],
                decompose_fn=self._method_multi_incident,
            ),
        }

    # -------------------------------------------------------------------------
    # Specialized Decomposition Methods
    # -------------------------------------------------------------------------

    def _method_road_accident(self, ctx: Dict[str, Any]) -> List[Task]:
        """Decompose road accident into traffic control, extrication, and trauma transport."""
        amb = ctx.get("ambulance", "A2")
        hosp = ctx.get("hospital", "City_General")
        scene = ctx.get("location", "Accident_Site")
        station = ctx.get("station", "Central_Base")
        victims = ctx.get("victims", 6)

        return [
            Task(
                name="Assess Scene Safety & Hazard",
                task_type="primitive",
                parameters={"hazard": "traffic_hazard", "scene": scene, "police_alert": True},
                est_time_min=2.0,
            ),
            Task(
                name=f"Dispatch Ambulance {amb}",
                task_type="primitive",
                parameters={"resource": amb, "station": station, "destination": scene, "capacity": 6},
                est_time_min=3.0,
            ),
            Task(
                name="Deploy Police Traffic Control & Perimeter",
                task_type="primitive",
                parameters={"agency": "Police", "perimeter": True, "detour_active": True},
                est_time_min=4.0,
            ),
            Task(
                name=f"Navigate {amb} to Accident Scene",
                task_type="primitive",
                parameters={"resource": amb, "origin": station, "destination": scene},
                est_time_min=8.0,
            ),
            Task(
                name=f"Triage and Treat Victims on Scene ({victims} victims)",
                task_type="primitive",
                parameters={"protocol": "C-spine immobilization and trauma stabilization", "victims": victims},
                est_time_min=12.0,
            ),
            Task(
                name=f"Transfer Victims to {hosp}",
                task_type="primitive",
                parameters={"resource": amb, "origin": scene, "destination": hosp, "specialty": "Level 1 Trauma"},
                est_time_min=10.0,
            ),
            Task(
                name=f"Unload and Admit Victims at {hosp}",
                task_type="primitive",
                parameters={"hospital": hosp, "department": "Emergency Trauma Bay", "release_resource": amb},
                est_time_min=5.0,
            ),
        ]

    def _method_fire_response(self, ctx: Dict[str, Any]) -> List[Task]:
        """Decompose fire response into thermal containment, burn stabilization, and burn ICU admission."""
        amb = ctx.get("ambulance", "A1")
        hosp = ctx.get("hospital", "City_General_Burn_Unit")
        scene = ctx.get("location", "Fire_Scene")
        station = ctx.get("station", "Central_Base")
        victims = ctx.get("victims", 4)

        return [
            Task(
                name="Assess Fire Hazard & Toxic Fumes",
                task_type="primitive",
                parameters={"hazard": "smoke_and_toxic_fumes", "scene": scene, "thermal_perimeter": True},
                est_time_min=3.0,
            ),
            Task(
                name=f"Dispatch Ambulance {amb} with Burn Response Gear",
                task_type="primitive",
                parameters={"resource": amb, "station": station, "destination": scene, "gear": "burn_kit"},
                est_time_min=3.0,
            ),
            Task(
                name="Coordinate Fire Department Containment & Exclusion Zone",
                task_type="primitive",
                parameters={"agency": "Fire Service", "exclusion_radius_meters": 150},
                est_time_min=5.0,
            ),
            Task(
                name=f"Navigate {amb} via Thermal Safe Corridor to Scene",
                task_type="primitive",
                parameters={"resource": amb, "origin": station, "destination": scene},
                est_time_min=7.0,
            ),
            Task(
                name=f"Triage & Burn Stabilization Protocol ({victims} victims)",
                task_type="primitive",
                parameters={"protocol": "Airway inhalation support and fluid resuscitation", "victims": victims},
                est_time_min=15.0,
            ),
            Task(
                name=f"Transfer Burn Patients to {hosp}",
                task_type="primitive",
                parameters={"resource": amb, "origin": scene, "destination": hosp, "specialty": "Burn ICU"},
                est_time_min=12.0,
            ),
            Task(
                name=f"Admit to {hosp} Specialized Burn Trauma Unit",
                task_type="primitive",
                parameters={"hospital": hosp, "department": "Critical Care Burn ICU", "release_resource": amb},
                est_time_min=6.0,
            ),
        ]

    def _method_flood_response(self, ctx: Dict[str, Any]) -> List[Task]:
        """Decompose flood response into swiftwater recon, all-terrain transit, and hypothermia care."""
        amb = ctx.get("ambulance", "A2")
        hosp = ctx.get("hospital", "City_General")
        scene = ctx.get("location", "Flood_Zone")
        station = ctx.get("station", "East_Station")
        victims = ctx.get("victims", 10)

        return [
            Task(
                name="Assess Submerged Roadways & Water Depth",
                task_type="primitive",
                parameters={"hazard": "floodwater_hazard", "scene": scene, "water_depth_gauge": True},
                est_time_min=4.0,
            ),
            Task(
                name=f"Dispatch High-Clearance Rescue Unit {amb}",
                task_type="primitive",
                parameters={"resource": amb, "station": station, "destination": scene, "type": "All-Terrain"},
                est_time_min=3.0,
            ),
            Task(
                name="Stage Swiftwater Rescue Boats & Floatation Teams",
                task_type="primitive",
                parameters={"agency": "Water Rescue", "equipment": "inflatable_rafts_and_winches"},
                est_time_min=6.0,
            ),
            Task(
                name=f"Navigate {amb} along Elevated Highland Detour to Scene",
                task_type="primitive",
                parameters={"resource": amb, "origin": station, "destination": scene, "avoid_submerged": True},
                est_time_min=11.0,
            ),
            Task(
                name=f"Administer Active Rewarming & Hypothermia Protocol ({victims} victims)",
                task_type="primitive",
                parameters={"protocol": "Thermal blankets, core rewarming, and oxygenation", "victims": victims},
                est_time_min=14.0,
            ),
            Task(
                name=f"Evacuate and Transfer Priority Patients to {hosp}",
                task_type="primitive",
                parameters={"resource": amb, "origin": scene, "destination": hosp, "specialty": "Acute Care"},
                est_time_min=10.0,
            ),
            Task(
                name=f"Admit Flood Victims to {hosp} Overflow Care",
                task_type="primitive",
                parameters={"hospital": hosp, "department": "Emergency Overflow Unit", "release_resource": amb},
                est_time_min=5.0,
            ),
        ]

    def _method_medical_emergency(self, ctx: Dict[str, Any]) -> List[Task]:
        """Decompose acute medical crisis into rapid telemetry, ALS dispatch, and cath lab prep."""
        amb = ctx.get("ambulance", "A1")
        hosp = ctx.get("hospital", "City_General")
        scene = ctx.get("location", "Medical_Scene")
        station = ctx.get("station", "Central_Base")
        victims = ctx.get("victims", 2)

        return [
            Task(
                name="Perform Rapid Medical Telemetry & Patient Assessment",
                task_type="primitive",
                parameters={"hazard": "acute_medical_crisis", "scene": scene, "telemetry_online": True},
                est_time_min=2.0,
            ),
            Task(
                name=f"Dispatch Advanced Life Support (ALS) Unit {amb}",
                task_type="primitive",
                parameters={"resource": amb, "station": station, "destination": scene, "type": "ALS"},
                est_time_min=2.0,
            ),
            Task(
                name=f"Alert {hosp} Emergency Resuscitation & Cath Lab",
                task_type="primitive",
                parameters={"hospital": hosp, "department": "Cardiac Cath Lab Standby"},
                est_time_min=3.0,
            ),
            Task(
                name=f"Priority Code 3 Siren Navigation to Scene ({amb})",
                task_type="primitive",
                parameters={"resource": amb, "origin": station, "destination": scene, "code": "Code 3"},
                est_time_min=6.0,
            ),
            Task(
                name=f"Administer IV Resuscitation and Cardiac Monitoring ({victims} victims)",
                task_type="primitive",
                parameters={"protocol": "12-Lead ECG, defibrillation, and cardiac drugs", "victims": victims},
                est_time_min=10.0,
            ),
            Task(
                name=f"Rapid Transit to {hosp} Emergency Suite",
                task_type="primitive",
                parameters={"resource": amb, "origin": scene, "destination": hosp, "specialty": "Cardiology"},
                est_time_min=7.0,
            ),
            Task(
                name=f"Direct Handover to {hosp} Resuscitation Team",
                task_type="primitive",
                parameters={"hospital": hosp, "department": "Resuscitation Suite", "release_resource": amb},
                est_time_min=4.0,
            ),
        ]

    def _method_multi_incident(self, ctx: Dict[str, Any]) -> List[Task]:
        """Decompose multi-casualty disaster into dual ambulance dispatch and START triage."""
        hosp1 = ctx.get("hospital", "City_General")
        hosp2 = "St_Jude_Emergency"
        scene = ctx.get("location", "Disaster_Site")
        victims = ctx.get("victims", 12)

        return [
            Task(
                name="Establish Mass Casualty Incident Command System (ICS)",
                task_type="primitive",
                parameters={"hazard": "mass_casualty_incident", "scene": scene, "ics_command": True},
                est_time_min=3.0,
            ),
            Task(
                name="Dispatch Multi-Unit Ambulance Fleet (A1 & A2)",
                task_type="primitive",
                parameters={"resources": ["A1", "A2"], "destination": scene, "dual_deployment": True},
                est_time_min=3.0,
            ),
            Task(
                name="Establish Colored Triage Tarps (Red, Yellow, Green, Black)",
                task_type="primitive",
                parameters={"protocol": "START Triage Staging Area", "scene": scene},
                est_time_min=5.0,
            ),
            Task(
                name="Multi-Unit Coordinated Navigation to Staging Area",
                task_type="primitive",
                parameters={"resources": ["A1", "A2"], "destination": scene},
                est_time_min=8.0,
            ),
            Task(
                name=f"Execute START Mass Casualty Triage ({victims} victims)",
                task_type="primitive",
                parameters={"protocol": "Simple Triage and Rapid Treatment", "victims": victims},
                est_time_min=15.0,
            ),
            Task(
                name=f"Distributed Patient Transport to {hosp1} and {hosp2}",
                task_type="primitive",
                parameters={"destinations": [hosp1, hosp2], "split_allocation": True},
                est_time_min=12.0,
            ),
            Task(
                name=f"Dual Hospital Handover and Resource Demobilization",
                task_type="primitive",
                parameters={"hospitals": [hosp1, hosp2], "status": "Incident Resolved"},
                est_time_min=6.0,
            ),
        ]

    # -------------------------------------------------------------------------
    # Core HTN Planner Logic
    # -------------------------------------------------------------------------

    def select_method(self, emergency_type: str) -> HTNMethod:
        """Select decomposition method matching emergency type string."""
        normalized = emergency_type.strip().lower()
        for method in self.methods.values():
            for kw in method.applicable_types:
                if kw in normalized or normalized in kw:
                    return method
        # Default fallback
        return self.methods["DecomposeRoadAccident"]

    def plan_emergency(
        self,
        emergency_type: str = "Road accident",
        incident_id: Optional[str] = "INC-1",
        ambulance: str = "A2",
        hospital: str = "City_General",
        location: str = "North_Junction",
        station: str = "Central_Base",
        victims: int = 6,
    ) -> Dict[str, Any]:
        """
        Generate a complete hierarchical response plan for an emergency incident.
        """
        method = self.select_method(emergency_type)
        context = {
            "incident_id": incident_id,
            "emergency_type": emergency_type,
            "ambulance": ambulance,
            "hospital": hospital,
            "location": location,
            "station": station,
            "victims": victims,
        }

        # 1. Expand root compound task using chosen method
        root_task = Task(
            name="ResolveEmergency",
            task_type="compound",
            parameters=context,
            method_name=method.name,
        )
        primitive_subtasks = method.decompose_fn(context)
        root_task.subtasks = primitive_subtasks

        # 2. Extract linear plan, dependencies, and action steps
        actions_list: List[Dict[str, Any]] = []
        final_plan_names: List[str] = []
        dependencies_dict: Dict[str, List[str]] = {}
        total_duration = 0.0

        for idx, subtask in enumerate(primitive_subtasks, start=1):
            final_plan_names.append(subtask.name)
            total_duration += subtask.est_time_min

            # Realistic task dependency network:
            # Step 1 (Assess): no dependencies
            # Step 2 (Dispatch): depends on 1
            # Step 3 (Perimeter / Prep): depends on 1 (parallel with dispatch)
            # Step 4 (Navigate): depends on 2
            # Step 5 (Triage/Treat): depends on 4
            # Step 6 (Transfer): depends on 5
            # Step 7 (Admit): depends on 3 (prep ready) and 6 (arrival)
            if idx == 1:
                deps = []
            elif idx in (2, 3):
                deps = [1]
            elif idx == 4:
                deps = [2]
            elif idx == 5:
                deps = [4]
            elif idx == 6:
                deps = [5]
            else:  # idx == 7
                deps = [3, 6]

            # Dependencies dictionary for orchestrator
            dependencies_dict[subtask.name] = [
                primitive_subtasks[d - 1].name for d in deps if d <= len(primitive_subtasks)
            ]

            # Status for frontend Planning.jsx:
            # Step 1 is done, step 2 active, remainder pending
            if idx == 1:
                status = "done"
            elif idx == 2:
                status = "active"
            else:
                status = "pending"

            action_step = {
                "id": idx,
                "step": idx,
                "action": subtask.name,
                "status": status,
                "dependencies": deps,
                "resource": subtask.parameters.get("resource"),
                "origin": subtask.parameters.get("origin") or station,
                "destination": subtask.parameters.get("destination") or hospital,
                "est_time_min": subtask.est_time_min,
                "details": subtask.parameters,
            }
            actions_list.append(action_step)

        initial_state = [
            f"Incident {incident_id} reported ({emergency_type})",
            f"Location: {location}, Victims: {victims}",
            f"Resource {ambulance} at {station}",
            f"Hospital {hospital} operational",
        ]
        goal_state = [
            f"Victims treated and safely admitted to {hospital}",
            f"Scene {location} secured",
            f"Resource {ambulance} returned to service",
        ]

        return {
            "initial_state": initial_state,
            "goal_state": goal_state,
            "initialState": f"Incident {incident_id} ({emergency_type}) at {location} with {victims} victims",
            "goal": f"Victims treated and admitted to {hospital}, scene secured",
            "actions": actions_list,
            "final_plan": final_plan_names,
            "dependencies": dependencies_dict,
            "decomposition_tree": root_task.to_dict(),
            "estimated_duration_minutes": total_duration,
            "method": method.name,
            "success": True,
        }

    def plan(
        self,
        initial: Optional[Any] = None,
        goal: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Backward-compatible plan() method for Orchestrator and API.
        """
        # Extract incident info from initial if given as a dictionary
        emergency_type = "Road accident"
        incident_id = "INC-1"
        location = "North_Junction"
        victims = 6

        if isinstance(initial, dict):
            emergency_type = initial.get("emergency_type") or initial.get("type") or "Road accident"
            incident_id = initial.get("incident_id") or "INC-1"
            location = initial.get("location") or "North_Junction"
            victims = initial.get("victim_count") or initial.get("victims") or 6

        return self.plan_emergency(
            emergency_type=emergency_type,
            incident_id=incident_id,
            location=location,
            victims=victims,
        )
