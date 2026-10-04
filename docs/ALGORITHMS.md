# Algorithms

## Uninformed Search

### UCS (Uniform Cost Search)
- **Description**: Explores the state space by expanding the lowest path-cost node first. Guaranteed to find the optimal path if all step costs are non-negative.
- **Pseudocode**:
  ```
  frontier = PriorityQueue(start_node)
  explored = set()
  while frontier is not empty:
      node = frontier.pop()
      if is_goal(node): return path
      explored.add(node)
      for child in node.expand():
          if child not in explored and child not in frontier:
              frontier.push(child, cost)
          else if child in frontier with higher cost:
              frontier.update(child, cost)
  ```
- **Time/Space complexity**: Time O(b^(1 + floor(C*/e))), Space O(b^(1 + floor(C*/e)))
- **How it's used in ResQ-AI**: Used for baseline route search when traffic heuristic data is missing.
- **Example input/output**: Input: `start=H1, end=H2`. Output: `[H1, N1, N2, H2]` with cost `12.0`.

### DLS (Depth-Limited Search)
- **Description**: A variation of Depth-First Search with a predetermined depth limit `l` to prevent infinite paths.
- **Pseudocode**:
  ```
  def DLS(node, depth):
      if is_goal(node): return path
      if depth == 0: return cutoff
      cutoff_occurred = false
      for child in node.expand():
          result = DLS(child, depth-1)
          if result == cutoff: cutoff_occurred = true
          else if result != failure: return result
      return cutoff if cutoff_occurred else failure
  ```
- **Time/Space complexity**: Time O(b^l), Space O(bl)
- **How it's used in ResQ-AI**: Memory-efficient exploration of localized road networks.
- **Example input/output**: Input: `start=N1, depth=2`. Output: `[N1, N2]`.

### IDS (Iterative Deepening Search)
- **Description**: Repeatedly runs DLS with increasing depth limits until the goal is found.
- **Pseudocode**:
  ```
  for depth = 0 to infinity:
      result = DLS(start_node, depth)
      if result != cutoff: return result
  ```
- **Time/Space complexity**: Time O(b^d), Space O(bd)
- **How it's used in ResQ-AI**: Searching for the nearest available ambulance when exact distance is unknown but memory is tight.
- **Example input/output**: Input: `start=Incident1`. Output: `Ambulance A2 at depth 3`.

## Informed Search

### A* Search
- **Description**: Best-first search evaluating nodes using f(n) = g(n) + h(n), where g(n) is the cost so far and h(n) is the estimated cost to the goal.
- **Pseudocode**:
  ```
  frontier = PriorityQueue(start_node, f(start_node))
  while frontier is not empty:
      node = frontier.pop()
      if is_goal(node): return path
      for child in node.expand():
          g = node.g + cost(node, child)
          f = g + heuristic(child, goal)
          if child not in frontier or g < child.g:
              frontier.push(child, f)
  ```
- **Time/Space complexity**: Time O(b^d), Space O(b^d)
- **How it's used in ResQ-AI**: Primary algorithm for finding the fastest routes considering travel time and traffic factor.
- **Example input/output**: Input: `start=A1, end=Incident`. Output: `Path minimizing (time * traffic)`.

### Best First Search
- **Description**: Greedy search evaluating nodes solely by the heuristic function f(n) = h(n).
- **Pseudocode**:
  ```
  frontier = PriorityQueue(start_node, h(start_node))
  while frontier is not empty:
      node = frontier.pop()
      if is_goal(node): return path
      for child in node.expand():
          frontier.push(child, h(child, goal))
  ```
- **Time/Space complexity**: Time O(b^m), Space O(b^m) (worst case)
- **How it's used in ResQ-AI**: Rapid, non-optimal route estimation for UI feedback.
- **Example input/output**: Input: `start=H1, end=N5`. Output: `Fastest estimated path, ignoring actual edge costs`.

### Hill Climbing
- **Description**: Local search that continually moves in the direction of increasing value/decreasing cost.
- **Pseudocode**:
  ```
  current = initial_state
  while true:
      neighbor = highest_valued_successor(current)
      if value(neighbor) <= value(current): return current
      current = neighbor
  ```
- **Time/Space complexity**: Time O(infinity) if continuous, Space O(1)
- **How it's used in ResQ-AI**: Optimizing resource distribution locally without a global rebuild.
- **Example input/output**: Input: `Current allocation`. Output: `Slightly improved local allocation`.

### Beam Search
- **Description**: Explores a graph by expanding only the top `k` most promising nodes at each level.
- **Pseudocode**:
  ```
  nodes = {initial_state}
  while not empty(nodes):
      next_nodes = set()
      for node in nodes:
          next_nodes.add_all(expand(node))
      nodes = top_k(next_nodes)
      if contains_goal(nodes): return goal
  ```
- **Time/Space complexity**: Time O(k * b * m), Space O(k * b)
- **How it's used in ResQ-AI**: Managing large-scale response plans where A* runs out of memory.
- **Example input/output**: Input: `start=A1, k=3`. Output: `Good, but potentially sub-optimal path`.

## Constraint Satisfaction (CSP) & Optimal Decision

### CSP Backtracking
- **Description**: Solves problems by trying assignments and backtracking when a constraint is violated.
- **Pseudocode**:
  ```
  def backtrack(assignment):
      if assignment is complete: return assignment
      var = select_unassigned_variable()
      for value in order_domain_values(var):
          if consistent(value, assignment):
              add value to assignment
              result = backtrack(assignment)
              if result != failure: return result
              remove value from assignment
      return failure
  ```
- **Time/Space complexity**: Time O(d^n), Space O(n)
- **How it's used in ResQ-AI**: Allocating ambulances to incidents respecting capacities and types.
- **Example input/output**: Input: `Incidents={I1}, Ambulances={A1, A2}`. Output: `{I1: A1}`.

### MCTS (Monte Carlo Tree Search)
- **Description**: Uses random sampling to determine the most promising moves in a search space.
- **Pseudocode**:
  ```
  def mcts(state):
      for _ in range(iterations):
          leaf = traverse(state)
          simulation_result = rollout(leaf)
          backpropagate(leaf, simulation_result)
      return best_child(state)
  ```
- **Time/Space complexity**: Time O(iterations * depth), Space O(tree size)
- **How it's used in ResQ-AI**: Deciding on high-level response strategies in uncertain disaster scenarios.
- **Example input/output**: Input: `Current disaster state`. Output: `Best high-level action (e.g., Evacuate)`.

### Alpha-Beta Pruning
- **Description**: Minimax algorithm optimization that prunes branches that cannot influence the final decision.
- **Pseudocode**:
  ```
  def alpha_beta(node, depth, alpha, beta, maximizingPlayer):
      if depth == 0 or is_terminal(node): return value(node)
      if maximizingPlayer:
          value = -inf
          for child in node:
              value = max(value, alpha_beta(child, depth-1, alpha, beta, False))
              alpha = max(alpha, value)
              if value >= beta: break
          return value
      else:
          # minimizing player logic similarly with beta
  ```
- **Time/Space complexity**: Time O(b^(d/2)), Space O(d)
- **How it's used in ResQ-AI**: Evaluating worst-case adversarial scenarios (e.g. cascading failures).
- **Example input/output**: Input: `Infrastructure state`. Output: `Most robust allocation against failures`.

## Inference

### Forward Chaining
- **Description**: Data-driven inference starting from known facts to derive new conclusions.
- **Pseudocode**:
  ```
  while new facts can be inferred:
      for rule in rules:
          if premises(rule) are true: add conclusion(rule) to facts
  ```
- **Time/Space complexity**: Time O(n * m), Space O(f)
- **How it's used in ResQ-AI**: Determining overall incident severity based on incoming sensor/user reports.
- **Example input/output**: Input: `[Fire=True, Wind=High]`. Output: `Severity=Critical`.

### Backward Chaining
- **Description**: Goal-driven inference working backward from a goal to see if the premises are supported.
- **Pseudocode**:
  ```
  def ask(goal):
      if goal in facts: return true
      for rule in rules concluding goal:
          if all(ask(p) for p in premises(rule)): return true
      return false
  ```
- **Time/Space complexity**: Time O(n * m), Space O(f)
- **How it's used in ResQ-AI**: Verifying if a specific response protocol needs to be activated.
- **Example input/output**: Input: `Goal=Evacuate_Zone_A`. Output: `True`.

### Resolution
- **Description**: A rule of inference leading to a refutation theorem-proving technique for sentences in propositional logic.
- **Pseudocode**:
  ```
  clauses = CNF(KB AND NOT alpha)
  while True:
      new_clauses = resolve pairs of clauses
      if empty_clause in new_clauses: return True
      if new_clauses subset of clauses: return False
  ```
- **Time/Space complexity**: Exponential in worst case.
- **How it's used in ResQ-AI**: Advanced logical consistency checks in the knowledge base.
- **Example input/output**: Input: `KB={A->B, A}, Query=B`. Output: `True`.

## Uncertainty

### Bayesian Network
- **Description**: Directed acyclic graph representing a set of variables and their conditional dependencies.
- **Pseudocode**:
  ```
  def calculate_probability(query, evidence):
      return sum(probabilities matching query & evidence) / sum(probabilities matching evidence)
  ```
- **Time/Space complexity**: NP-hard for exact inference in general networks.
- **How it's used in ResQ-AI**: Calculating risk factors on roads (e.g., accident probability given weather).
- **Example input/output**: Input: `Weather=Rain`. Output: `P(Accident)=0.4`.

## Planning

### State-Space Planning
- **Description**: Finding a sequence of actions through a state space to reach a goal.
- **Pseudocode**:
  ```
  Use A* or BFS on state transitions defined by Action(Preconditions, Effects)
  ```
- **Time/Space complexity**: Exponential in number of state variables.
- **How it's used in ResQ-AI**: Sequential generation of single-incident response steps.
- **Example input/output**: Input: `State={Fire}`. Output: `[Dispatch_Firetruck, Use_Extinguisher]`.

### Partial-Order Planning (POP)
- **Description**: Planning without strictly ordering actions unless necessary, searching the space of plans.
- **Pseudocode**:
  ```
  plan = {Start, Finish}
  while open_preconditions:
      resolve an open precondition by adding an action or linking an existing one
      resolve threats by adding ordering constraints
  ```
- **Time/Space complexity**: NP-hard
- **How it's used in ResQ-AI**: Coordinating multiple independent response teams simultaneously.
- **Example input/output**: Input: `Goal={Fire_Out, Patient_Treated}`. Output: `Unordered parallel plan`.

### Hierarchical Planning (HTN)
- **Description**: Decomposing high-level tasks into smaller sub-tasks until primitive actions are reached.
- **Pseudocode**:
  ```
  def htn_plan(tasks):
      if empty(tasks): return []
      task = tasks[0]
      if is_primitive(task): return [task] + htn_plan(tasks[1:])
      for method in methods_for(task):
          subplan = htn_plan(method.subtasks + tasks[1:])
          if subplan != failure: return subplan
  ```
- **Time/Space complexity**: Varies based on task hierarchy depth/breadth.
- **How it's used in ResQ-AI**: High-level incident management (e.g., `Manage_Earthquake` -> `Triage`, `Clear_Roads`).
- **Example input/output**: Input: `Task=Manage_Accident`. Output: `[Dispatch_Ambulance, Inform_Hospital]`.

## Learning

### Decision Tree
- **Description**: Predictive model splitting data on features to maximize information gain.
- **Pseudocode**:
  ```
  def build_tree(data):
      if data pure: return Leaf(class)
      best_feature = max(information_gain)
      node = Node(best_feature)
      for value in values(best_feature):
          node.add_child(build_tree(subset(data, value)))
      return node
  ```
- **Time/Space complexity**: Time O(n * d * log(n)), Space O(tree_nodes)
- **How it's used in ResQ-AI**: Predicting priority level of an incident based on keywords and historical data.
- **Example input/output**: Input: `Features=[Smoke, Casualties]`. Output: `Priority=High`.
