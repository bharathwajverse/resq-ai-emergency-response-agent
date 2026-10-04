from app.agent.llm_service import LLMService
from app.inference.engine import InferenceEngine
from app.inference.rules import PREDEFINED_RULES
from app.uncertainty.bayesian import calculate_risk
from app.planning.hierarchical import HTNPlanner

class Orchestrator:
    def __init__(self):
        self.state = {
            "incident": None,
            "resources": [],
            "facts": {},
            "inferences": [],
            "risk": {},
            "current_plan": [],
            "decision": None
        }
        self.llm = LLMService()
        self.planner = HTNPlanner()
        
    def process(self, text: str):
        inc = self.llm.parse_incident(text)
        self.state["incident"] = inc.model_dump()
        self.state["facts"]["victim_count"] = inc.victim_count
        self.state["facts"]["severity"] = inc.severity
        
        engine = InferenceEngine(self.state["facts"], PREDEFINED_RULES)
        inf_res = engine.forward_chain()
        self.state["facts"] = inf_res["facts"]
        self.state["inferences"] = inf_res["logs"]
        
        self.state["risk"] = calculate_risk(self.state["facts"])
        
        plan_res = self.planner.plan(self.state["facts"], {"status": "Complete"})
        self.state["current_plan"] = plan_res["final_plan"]
        
        self.state["decision"] = "Dispatch resources"
        explanation = self.llm.generate_explanation({"decision": self.state["decision"]})
        
        return {
            "status": "success",
            "incident": self.state["incident"],
            "inferences": self.state["inferences"],
            "risk": self.state["risk"],
            "plan": self.state["current_plan"],
            "explanation": explanation
        }
