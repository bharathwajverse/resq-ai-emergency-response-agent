from app.agent.llm_service import IncidentData

def parse(text: str) -> IncidentData:
    text = text.lower()
    sev = "high" if "severe" in text or "massive" in text else "low"
    typ = "Fire" if "fire" in text else "Medical Emergency"
    return IncidentData(type=typ, severity=sev, victim_count=5, location="Downtown")
