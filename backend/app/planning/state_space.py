from typing import List, Dict, Any

class StateSpacePlanner:
    def __init__(self, initial_state: Dict[str, Any], goal_state: Dict[str, Any], actions: List[Dict[str, Any]]):
        self.initial_state = initial_state
        self.goal_state = goal_state
        self.actions = actions
        
    def plan(self) -> List[str]:
        queue = [(self.initial_state, [])]
        visited = []
        
        while queue:
            state, path = queue.pop(0)
            
            is_goal = True
            for k, v in self.goal_state.items():
                if state.get(k) != v:
                    is_goal = False
                    break
            if is_goal: return path
            
            if state in visited: continue
            visited.append(state)
            
            for action in self.actions:
                pre_met = True
                for k, v in action.get("preconditions", {}).items():
                    if state.get(k) != v: pre_met = False
                
                if pre_met:
                    new_state = state.copy()
                    for k, v in action.get("effects", {}).items():
                        new_state[k] = v
                    queue.append((new_state, path + [action["name"]]))
        return []
