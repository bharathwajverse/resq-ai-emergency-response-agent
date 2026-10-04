# FAI Mapping

| FAI Module | Topic | Source Files | UI Pages | Key Classes/Functions |
|---|---|---|---|---|
| Module II | Uninformed Search | backend/app/search/ucs.py, dls.py, ids.py | Route Search, Algorithms Lab | UCS.search(), DLS.search(), IDS.search() |
| Module III | Informed Search | backend/app/search/astar.py, best_first.py, hill_climbing.py, beam_search.py | Route Search, Algorithms Lab | AStar.search(), BestFirst.search(), ... |
| Module IV | CSP/Optimal Decision | backend/app/csp/solver.py, mcts.py, alpha_beta.py | Resource Allocation, Algorithms Lab | CSPSolver.solve(), MCTS.search(), ... |
| Module V | Inference | backend/app/inference/engine.py, resolution.py | Agent Console, Algorithms Lab | ForwardChaining.infer(), BackwardChaining.query() |
| Module VI | Knowledge Rep | backend/app/knowledge/knowledge_base.py, frames.py, ontology.py | Dashboard, Agent Console | KnowledgeBase, Frame, Ontology |
| Module VII | Planning | backend/app/planning/state_space.py, partial_order.py, hierarchical.py | Planning, Algorithms Lab | StateSpacePlanner, POPPlanner, HTNPlanner |
| Module VIII | Uncertainty | backend/app/uncertainty/bayesian.py | Risk Analysis | BayesianRiskEngine.calculate() |
| Module IX | Learning | backend/app/learning/decision_tree.py | Algorithms Lab | DecisionTreeLearner.train(), .predict() |
