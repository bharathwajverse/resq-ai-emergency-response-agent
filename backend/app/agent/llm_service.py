import os
from pydantic import BaseModel

class IncidentData(BaseModel):
    type: str
    severity: str
    victim_count: int
    location: str

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.demo_mode = not bool(self.api_key)
        
    def parse_incident(self, text: str) -> IncidentData:
        if self.demo_mode:
            from app.agent.demo_parser import parse
            return parse(text)
        return IncidentData(type="Unknown", severity="low", victim_count=0, location="Unknown")
        
    def generate_explanation(self, decision: dict) -> str:
        return f"Decision made based on: {decision}"
