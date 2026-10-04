class HTNPlanner:
    def plan(self, initial, goal):
        return {
            "initial_state": initial,
            "goal_state": goal,
            "actions": ["Assess Incident", "Allocate Resources", "Navigate", "Transfer Victims", "Complete"],
            "dependencies": {"Allocate Resources": ["Assess Incident"], "Navigate": ["Allocate Resources"]},
            "final_plan": ["Assess Incident", "Allocate Resources", "Navigate", "Transfer Victims", "Complete"]
        }
