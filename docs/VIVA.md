# Viva Voce Guide

1. **Project Overview**: What is ResQ-AI? How does it work?
   - ResQ-AI is a hybrid AI emergency response system. It uses an LLM-based agent orchestrator to understand user requests and delegates complex reasoning (routing, planning, allocation) to classical AI algorithms (A*, CSP, Decision Trees) interacting with a PostgreSQL database.

2. **AI Agent**: What is an AI Agent? How does your agent work? What are agent tools?
   - An AI Agent is an autonomous system that perceives its environment and takes actions to achieve goals. Our agent uses an LLM for natural language understanding and orchestrates execution via tools. Tools are specialized functions (like `find_route` or `allocate_resources`) the agent can invoke to perform deterministic tasks.

3. **Why LLM**: Why use an LLM? What does it do? What does it NOT do?
   - We use an LLM for entity extraction, intent recognition, and human-like interaction. It translates natural language into tool calls. It does NOT perform graph search, constraint satisfaction, or exact mathematical routing, as LLMs are prone to hallucination in precise logic tasks.

4. **Why Classical AI**: Why use classical AI? How is it different from LLM?
   - Classical AI provides deterministic, verifiable, and mathematically optimal solutions (e.g., shortest paths, guaranteed constraint satisfaction). Unlike LLMs which generate probabilistic text, classical AI follows explicit algorithmic rules.

5. **Search Algorithms**: 
   - **Explain UCS. When is it optimal?**: UCS expands nodes by lowest path cost. It is optimal when step costs vary and are non-negative.
   - **Explain A*. What makes a good heuristic? Is your heuristic admissible?**: A* uses actual cost + heuristic estimation to guide search. A good heuristic closely approximates the real cost. Yes, our heuristic (straight-line distance / max speed) never overestimates the true travel time, making it admissible.
   - **Explain DLS vs IDS. When to use each?**: DLS explores to a fixed depth limit. IDS repeatedly runs DLS with increasing limits. Use IDS when memory is limited but you need the completeness of BFS.
   - **Explain Best First, Hill Climbing, Beam Search. Differences?**: Best First evaluates purely by heuristic. Hill Climbing only moves to immediately better neighbors (local search). Beam Search is a constrained BFS that only expands the top `k` nodes at each level to save memory.

6. **Inference**: 
   - **What is forward chaining? When to use?**: Data-driven logic starting from known facts to derive conclusions. Use when new data arrives and you want to see all implications.
   - **What is backward chaining? When to use?**: Goal-driven logic starting from a hypothesis to check if facts support it. Use when you have a specific question (e.g., "Is it safe?") and want to prove it.
   - **What is resolution? How does it work?**: A proof by contradiction method in propositional logic. It works by negating the theorem, converting the KB to CNF, and repeatedly applying the resolution rule until an empty clause is found.

7. **CSP**: 
   - **What is a CSP? Variables, domains, constraints?**: A Constraint Satisfaction Problem. Variables (e.g., incidents) need values from Domains (e.g., available ambulances), satisfying Constraints (e.g., ambulance capacity >= incident casualties).
   - **How does backtracking work? What is constraint propagation?**: Backtracking tries assignments sequentially, reverting when a constraint is violated. Constraint propagation proactively reduces domains of unassigned variables based on current assignments.
   - **Explain MCTS and Alpha-Beta**: MCTS uses random simulations to find promising paths in huge search spaces. Alpha-Beta pruning optimizes minimax game trees by cutting off branches that cannot affect the final outcome.

8. **Bayesian Reasoning**: 
   - **What is Bayesian reasoning? What is P(A|B)?**: Reasoning using probability to handle uncertainty. P(A|B) is the conditional probability of event A given that B is true.
   - **How do you calculate risk?**: By updating the prior probability of an incident using Bayesian Networks based on real-time evidence (like weather or traffic).
   - **Why label as simulated?**: Because in a real system, probabilities require vast historical data and continuous sensor streams, which are currently simulated for demonstration.

9. **Planning**: 
   - **What is state-space planning?**: Finding a sequence of actions from an initial state to a goal state using standard search algorithms.
   - **What is partial-order planning? Why is it better?**: Planning that only orders actions when strictly necessary. It's better for avoiding early commitment and allowing independent actions to be executed concurrently.
   - **What is hierarchical planning?**: Breaking high-level complex tasks down into progressively smaller, concrete sub-tasks.

10. **Learning**: 
    - **What is a decision tree? How does it learn?**: A supervised learning model that splits data into branches. It learns by choosing splits that maximize data purity at each node.
    - **What is entropy? Information gain?**: Entropy measures impurity or randomness in data. Information gain is the reduction in entropy after a split.
    - **How do you predict priority?**: The decision tree uses incident features (like keyword presence or severity) and traverses the learned splits to classify priority.

11. **Limitations**: What are the limitations of this system?
    - Heuristics may fail under extreme dynamic conditions. The simulated environment lacks the chaos of real-time multi-agent communication drops, and the LLM can occasionally misinterpret complex nested commands.

12. **Future Enhancements**: What would you add next?
    - Integration with live maps/traffic APIs, multi-agent reinforcement learning for continuous routing adjustments, and mobile apps for field responders.
