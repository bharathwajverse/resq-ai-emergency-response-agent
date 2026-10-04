"""
ResQ-AI CSP Solver Implementation.
Module IV: Constraint Satisfaction Problem.
Features:
- Backtracking search with MRV (Minimum Remaining Values) heuristic
- LCV (Least Constraining Value) value ordering
- Forward Checking constraint propagation
- AC-3 (Arc Consistency Algorithm #3)
- Multi-incident resource mutual exclusion
"""

import time
from collections import deque
from typing import Dict, List, Any, Optional, Tuple, Set
from copy import deepcopy

from app.schemas.csp import CSPSolveResponse, CandidateRejection
from app.csp.problem import DispatchCSP, IncidentSpec, AmbulanceSpec, HospitalSpec
from app.search.astar import AStarSearch


class CSPSolver:
    """Constraint Satisfaction Problem Solver with heuristics and propagation."""

    def __init__(self, use_ac3: bool = True, use_forward_checking: bool = True):
        self.use_ac3 = use_ac3
        self.use_forward_checking = use_forward_checking
        self.astar = AStarSearch()

    def solve(self, csp: DispatchCSP) -> CSPSolveResponse:
        start_time = time.perf_counter()
        nodes_explored = 0
        backtracks = 0
        rejected_candidates: List[CandidateRejection] = []

        # 1. Domain Pre-filtering (Unary Constraints)
        domains = deepcopy(csp.domains)

        # Filter ambulance unary constraints
        valid_ambs = []
        for amb_code in domains["ambulance"]:
            is_valid, reason = csp.check_ambulance_constraints(amb_code)
            if is_valid:
                valid_ambs.append(amb_code)
            else:
                rejected_candidates.append(CandidateRejection(candidate=amb_code, reason=reason))
        domains["ambulance"] = valid_ambs

        # Filter hospital unary constraints
        valid_hosps = []
        for hosp_code in domains["hospital"]:
            is_valid, reason = csp.check_hospital_constraints(hosp_code)
            if is_valid:
                valid_hosps.append(hosp_code)
            else:
                rejected_candidates.append(CandidateRejection(candidate=hosp_code, reason=reason))
        domains["hospital"] = valid_hosps

        # If any domain is empty immediately, fail
        if not domains["ambulance"] or not domains["hospital"]:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return CSPSolveResponse(
                success=False,
                assignment={},
                nodes_explored=0,
                backtracks=0,
                rejected_candidates=rejected_candidates,
                execution_time_ms=duration_ms,
                explanation="No valid allocation: one or more variable domains became empty during unary constraint filtering.",
            )

        # 2. AC-3 Arc Consistency Propagation
        if self.use_ac3:
            ac3_success = self._run_ac3(csp, domains, rejected_candidates)
            if not ac3_success:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                return CSPSolveResponse(
                    success=False,
                    assignment={},
                    nodes_explored=0,
                    backtracks=0,
                    rejected_candidates=rejected_candidates,
                    execution_time_ms=duration_ms,
                    explanation="AC-3 arc consistency detected domain exhaustion across binary routing constraints.",
                )

        # 3. Backtracking Search with MRV & Forward Checking
        assignment: Dict[str, Any] = {}

        def select_unassigned_variable(current_assignment: Dict[str, Any], current_domains: Dict[str, List[Any]]) -> str:
            """MRV (Minimum Remaining Values): choose variable with fewest domain values."""
            unassigned = [v for v in csp.variables if v not in current_assignment]
            return min(unassigned, key=lambda var: len(current_domains[var]))

        def order_domain_values(var: str, current_domains: Dict[str, List[Any]]) -> List[Any]:
            """LCV (Least Constraining Value) ordering heuristic."""
            values = current_domains[var]
            if var == "ambulance":
                # Prefer available ambulances with closest distance to incident
                def amb_priority(code: str) -> float:
                    amb = csp.get_ambulance(code)
                    if not amb:
                        return float("inf")
                    return csp.graph.heuristic(amb.location, csp.incident.location)
                return sorted(values, key=amb_priority)
            elif var == "hospital":
                # Prefer hospitals closer to incident
                def hosp_priority(code: str) -> float:
                    hosp = csp.get_hospital(code)
                    if not hosp:
                        return float("inf")
                    return csp.graph.heuristic(csp.incident.location, hosp.location)
                return sorted(values, key=hosp_priority)
            return values

        def backtrack(current_assignment: Dict[str, Any], current_domains: Dict[str, List[Any]]) -> Optional[Dict[str, Any]]:
            nonlocal nodes_explored, backtracks

            if len(current_assignment) == len(csp.variables):
                return current_assignment

            var = select_unassigned_variable(current_assignment, current_domains)
            nodes_explored += 1

            for val in order_domain_values(var, current_domains):
                # Consistency check with current partial assignment
                consistent = True
                if var == "hospital" and "ambulance" in current_assignment:
                    is_ok, reason = csp.check_binary_constraints(current_assignment["ambulance"], val)
                    if not is_ok:
                        consistent = False
                elif var == "ambulance" and "hospital" in current_assignment:
                    is_ok, reason = csp.check_binary_constraints(val, current_assignment["hospital"])
                    if not is_ok:
                        consistent = False

                if consistent:
                    current_assignment[var] = val
                    new_domains = deepcopy(current_domains)

                    if self.use_forward_checking:
                        # Forward Checking: prune incompatible values from other variable domains
                        if var == "ambulance" and "hospital" not in current_assignment:
                            new_hosps = []
                            for h in new_domains["hospital"]:
                                is_ok, _ = csp.check_binary_constraints(val, h)
                                if is_ok:
                                    new_hosps.append(h)
                            new_domains["hospital"] = new_hosps
                            if not new_domains["hospital"]:
                                # Domain exhausted, backtrack
                                del current_assignment[var]
                                backtracks += 1
                                continue

                    result = backtrack(current_assignment, new_domains)
                    if result is not None:
                        return result

                    # Undo assignment
                    del current_assignment[var]
                    backtracks += 1

            return None

        final_assignment = backtrack(assignment, domains)
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        if final_assignment:
            # Construct complete multi-leg route: Amb -> Incident -> Hospital
            amb_code = final_assignment["ambulance"]
            hosp_code = final_assignment["hospital"]
            amb = csp.get_ambulance(amb_code)
            hosp = csp.get_hospital(hosp_code)

            leg1 = self.astar.search(csp.graph, amb.location, csp.incident.location)
            leg2 = self.astar.search(csp.graph, csp.incident.location, hosp.location)

            full_route = []
            if leg1.success and leg2.success:
                # Merge paths without duplicate intermediate node
                full_route = leg1.path + leg2.path[1:]

            final_assignment["route"] = full_route
            total_route_cost = round(leg1.cost + leg2.cost, 4)
            final_assignment["route_cost"] = total_route_cost

            explanation = (
                f"Assigned Ambulance {amb_code} (Capacity: {amb.capacity}) and "
                f"Hospital {hosp_code} ({hosp.name}) for incident at {csp.incident.location} "
                f"with {csp.incident.victim_count} victim(s). Full route: {' -> '.join(full_route)}."
            )

            return CSPSolveResponse(
                success=True,
                assignment=final_assignment,
                nodes_explored=nodes_explored,
                backtracks=backtracks,
                rejected_candidates=rejected_candidates,
                execution_time_ms=duration_ms,
                explanation=explanation,
            )
        else:
            return CSPSolveResponse(
                success=False,
                assignment={},
                nodes_explored=nodes_explored,
                backtracks=backtracks,
                rejected_candidates=rejected_candidates,
                execution_time_ms=duration_ms,
                explanation="Backtracking search exhausted all combinations without finding a consistent assignment.",
            )

    def _run_ac3(
        self,
        csp: DispatchCSP,
        domains: Dict[str, List[Any]],
        rejected_candidates: List[CandidateRejection],
    ) -> bool:
        """
        Executes AC-3 arc consistency between 'ambulance' and 'hospital' variables.
        Returns False if any domain is wiped out, True otherwise.
        """
        queue = deque([
            ("ambulance", "hospital"),
            ("hospital", "ambulance"),
        ])

        while queue:
            xi, xj = queue.popleft()
            revised = False

            values_to_keep = []
            for val_i in domains[xi]:
                # Check if there exists ANY value in xj that satisfies binary constraint
                has_support = False
                for val_j in domains[xj]:
                    amb_val = val_i if xi == "ambulance" else val_j
                    hosp_val = val_j if xi == "ambulance" else val_i
                    is_ok, _ = csp.check_binary_constraints(amb_val, hosp_val)
                    if is_ok:
                        has_support = True
                        break

                if has_support:
                    values_to_keep.append(val_i)
                else:
                    revised = True
                    rejected_candidates.append(
                        CandidateRejection(
                            candidate=str(val_i),
                            reason=f"AC-3 arc consistency pruned: no supporting valid partner in {xj}",
                        )
                    )

            if revised:
                domains[xi] = values_to_keep
                if not domains[xi]:
                    return False
                # Re-add opposing arc
                queue.append((xj, xi))

        return True

    def solve_multi_incident(
        self,
        incidents: List[IncidentSpec],
        ambulances: Optional[List[AmbulanceSpec]] = None,
        hospitals: Optional[List[HospitalSpec]] = None,
        graph: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Multi-incident dispatch enforcing mutual exclusion:
        No two incidents can be assigned the same ambulance simultaneously.
        """
        results = {}
        assigned_ambulances: Set[str] = set()

        for inc in incidents:
            # Filter available fleet excluding already assigned ambulances
            current_fleet = [
                a for a in (ambulances or [
                    AmbulanceSpec(code="A1", status="Available", capacity=4, location="A1"),
                    AmbulanceSpec(code="A2", status="Available", capacity=6, location="A2"),
                    AmbulanceSpec(code="A3", status="Maintenance", capacity=6, location="A3"),
                ])
                if a.code not in assigned_ambulances
            ]

            csp = DispatchCSP(
                incident=inc,
                ambulances=current_fleet,
                hospitals=hospitals,
                graph=graph,
            )
            sol = self.solve(csp)
            results[inc.id] = sol
            if sol.success and "ambulance" in sol.assignment:
                assigned_ambulances.add(sol.assignment["ambulance"])

        return {
            "success": all(s.success for s in results.values()),
            "incident_solutions": results,
            "assigned_ambulances": list(assigned_ambulances),
        }
