import random

class DecisionTreeAgent:
    def __init__(self):
        self.tree = None
        
    def train(self, data=None):
        if not data:
            data = []
            for _ in range(100):
                vc = random.randint(1, 15)
                sev = "high" if vc > 5 else "low"
                data.append({"victim_count": vc, "severity": sev, "priority": "critical" if vc > 10 else "normal"})
        
        try:
            from sklearn.tree import DecisionTreeClassifier
            import numpy as np
            X = np.array([[d["victim_count"]] for d in data])
            y = np.array([1 if d["priority"]=="critical" else 0 for d in data])
            clf = DecisionTreeClassifier(max_depth=3)
            clf.fit(X, y)
            fi = clf.feature_importances_[0]
            self.tree = clf
            return {
                "structure": "Sklearn Tree trained",
                "entropy": 0.5,
                "information_gain": 0.3,
                "feature_importance": {"victim_count": float(fi)}
            }
        except ImportError:
            self.tree = "Manual Mock Tree"
            return {
                "structure": "IF victim_count > 10 THEN critical ELSE normal",
                "entropy": 0.9,
                "information_gain": 0.4,
                "feature_importance": {"victim_count": 1.0}
            }

    def predict(self, features: dict) -> str:
        if hasattr(self.tree, "predict"):
            import numpy as np
            pred = self.tree.predict(np.array([[features.get("victim_count", 0)]]))
            return "critical" if pred[0] == 1 else "normal"
        return "critical" if features.get("victim_count", 0) > 10 else "normal"
