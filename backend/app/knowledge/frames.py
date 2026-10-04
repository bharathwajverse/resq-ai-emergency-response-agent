class Frame:
    def __init__(self, name: str, slots: dict):
        self.name = name
        self.slots = slots

def create_frames():
    return {
        "Incident": Frame("Incident", {"type": "Emergency", "location": None, "severity": "low"}),
        "Ambulance": Frame("Ambulance", {"capacity": 2, "status": "available", "location": None}),
        "Hospital": Frame("Hospital", {"capacity": 100, "status": "open", "location": None}),
        "Road": Frame("Road", {"blocked": False, "traffic": "low"}),
        "Emergency Resource": Frame("Emergency Resource", {"type": "General", "available": True})
    }
