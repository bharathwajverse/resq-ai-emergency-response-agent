from typing import Any, Dict, List

class InferenceEngine:
    def __init__(self, facts: Dict[str, Any], rules: List[Any]):
        self.facts = facts.copy()
        self.rules = rules
        self.logs = []

    def _eval_condition(self, condition_str: str) -> bool:
        local_vars = self.facts.copy()
        try:
            cond = condition_str.replace("true", "True").replace("false", "False")
            cond = cond.replace(" AND ", " and ").replace(" OR ", " or ")
            return bool(eval(cond, {}, local_vars))
        except Exception:
            return False

    def forward_chain(self) -> Dict[str, Any]:
        changed = True
        inferred = []
        while changed:
            changed = False
            for rule in self.rules:
                if self._eval_condition(rule.condition):
                    if "=" in rule.action:
                        var, val = [x.strip() for x in rule.action.split("=", 1)]
                        val_clean = val.strip("'\"")
                        if val_clean.isdigit(): 
                            parsed_val = int(val_clean)
                        elif val_clean.lower() == 'true': 
                            parsed_val = True
                        elif val_clean.lower() == 'false': 
                            parsed_val = False
                        else:
                            parsed_val = val_clean
                        
                        if var not in self.facts or self.facts[var] != parsed_val:
                            self.facts[var] = parsed_val
                            inferred.append(f"{var}={parsed_val}")
                            self.logs.append(f"Fired: IF {rule.condition} THEN {rule.action}")
                            changed = True
        return {"facts": self.facts, "logs": self.logs, "inferred": inferred}

    def backward_chain(self, goal_var: str) -> Dict[str, Any]:
        # Simple recursive backward chaining
        def prove(var, visited):
            if var in self.facts:
                return True
            if var in visited:
                return False
            visited.add(var)
            for rule in self.rules:
                if "=" in rule.action:
                    r_var, r_val = [x.strip() for x in rule.action.split("=", 1)]
                    if r_var == var:
                        self.logs.append(f"Trying to prove {var} via rule: IF {rule.condition} THEN {rule.action}")
                        if self._eval_condition(rule.condition):
                            val_clean = r_val.strip("'\"")
                            if val_clean.isdigit(): parsed = int(val_clean)
                            elif val_clean.lower() == 'true': parsed = True
                            elif val_clean.lower() == 'false': parsed = False
                            else: parsed = val_clean
                            self.facts[var] = parsed
                            self.logs.append(f"Proved {var} = {parsed}")
                            return True
            return False
        
        result = prove(goal_var, set())
        return {"goal": goal_var, "proved": result, "value": self.facts.get(goal_var), "logs": self.logs}