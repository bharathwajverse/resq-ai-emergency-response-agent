from typing import Dict, List, Any

class KnowledgeBase:
    def __init__(self):
        self.facts: Dict[str, Any] = {}
        self.rules: List[Any] = []
        
    def add_fact(self, key: str, value: Any):
        self.facts[key] = value
        
    def add_rule(self, rule: Any):
        self.rules.append(rule)
        
    def query(self, key: str) -> Any:
        return self.facts.get(key)
