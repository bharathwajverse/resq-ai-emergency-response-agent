from pydantic import BaseModel

class Rule(BaseModel):
    condition: str
    action: str

PREDEFINED_RULES = [
    Rule(condition="victim_count > 5 and severity == 'high'", action="priority = 'critical'"),
    Rule(condition="road_blocked == True", action="avoid_blocked_routes = True"),
    Rule(condition="hospital_capacity <= 0", action="hospital_status = 'unavailable'"),
    Rule(condition="ambulance_available == True and ambulance_capacity >= victim_count", action="ambulance_status = 'feasible'"),
]
