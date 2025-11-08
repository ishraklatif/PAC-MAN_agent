# PAC-MAN_agent
Q1(c)
Introduction:

The problem required designing a search agent for the Pac-Man to plan its path for collecting all food in a given layout. The state space is exponential in the number of dots as the state includes both the Pac-Man’s current coordinate and the coordinates of the uneaten food and it takes a lot of branches therefore the best solution was to solve the TSP on the grid layout. So I implemented a search agent that uses A* search for small boards and switches to BFS for larger boards to complete the search in the time limit.

Method:
Problem Representation:

State(coord- Pac-Man, coord- remainingDots)
getStartState(start coord- Pac-Man, frozenset of coord- allDots)
isGoalState returns len of set of dots as zero
getSuccessor expands moves in 4 directions and removes a dot from the set if Pac-Man’s position is on a dot, saves the new coordinate of Pac-Man, coords of remainingDots, move direction and unit cost in the successors[] list.

Algorithmic approach:

A* search:
When number of dots <=50 and cap to 50% of the time budget. If it finds a path we’re done.  It uses a strong heuristic:
h(state) =mind∈remaining⁡  Manhattan(position,d) + MST(remaining)
BFS:
If A* fails, or more than 50 dots, use nearest reachable dot by bfs using BFS maze distance to avoid wall induced confusion leading to oscillation. Execute small chunks of steps (5 or less) along the BFS path and update state and repeat. Used a fall back guard to prevent throwing out of actions.
Pseudocode:
function Q1C_SOLVER(problem, time_limit):
    state ← problem.getStartState()
    if |remainingDots| ≤ 50:
        path ← A*_search(state, isGoal=allDotsEaten, heuristic=h_q1c, deadline=time_limit/2)
        if path found: return path

    plan ← [ ]
    while time remains and remainingDots is not null:
        target, bfsPath ← nearestReachableDotByBFS(state)
        if bfsPath empty: return at least one step
        chunk ← first k steps of bfsPath
        append chunk to plan
        state ← applyActions(state, chunk)
    if plan empty: return [STOP]
    return plan
 
Results 

Correctness:

On smaller layouts A* succeeds faster, whereas on larger layouts A* typically times out and BFS takes over immediately and consistently clears dots.
On challenging layouts where wall induced confusion might arise using Manhattan, BFS targets reachable dots to avoid oscillations

Performance:

Time: BFS microplans run in milliseconds per step, while A* consumes more time but is capped in a threshold.
Path Quality: BFS is not optimal as it visits visited areas but clears board in time.
Safety: Implemented safe guard to return at least one step to avoid a crash.

Discussion:

Strengths: Hybrid use of 2 algorithms balances optimality and scalability.
Admissible MST-based heuristics improves A* search on smaller layouts/<=50 dots, while BFS ensures progress on larger layouts solving confusions and 5 steps chunks keeps agent responsive and prevents long blocking computations.

Weakness: BFS may choose suboptimal paths and thus longer tours. Memory overhead of storing dots sets in states makes A* not feasible beyond 50+ dots. My chunk size for BFS, dot threshold and time threshold was empirically tuned, not theoretically optimal.

Alternative attempts: I initially used Manhattan nearest dot selection for greedy mode, this led to confusion in closed layouts where the nearest dot was behind a closed wall. I also tried planning longer BFS paths to each dot but this made the Pac_Man unresponsive, the chunked approach was a fair trade off. 

Conclusion:

Q1(c) involved difficulty of scaling optimal search to scaled spaces. Combining A* for smaller layouts and greed BFS nearest dot micro plans for scaled layouts, the agent was balanced with strengths with fair trade off weakness. Noted lessons were Manhattan is not reliable in closed layout or maze with critical distance. Jumping algorithms is highly effective when searched in a strict time limit. 














  
Q2
Introduction:

The problem required designing a search agent for the Pac-Man to plan its path for collecting all food in a given layout and reasons against ghost agents. Used minmax with alpha-beta pruning with optimisation of high branching factors in long corridors and many junctions and also deep moves trees using speed-quality tradeoff.

Method:
Problem Representation:

Game tree: Alternating MAX(Pac-Man) and MIN(Ghosts) layers
Depth account: Depth tracks Pac-Man plies, after all ghosts act the depth decreases
Terminal States: isWin, isLose or depth limit reached
Evaluation: Scores for different environment used as numeric heuristic

Algorithmic approach and optimisation:

Alpha Beta with iterative deepening
Used MAX_MILLIS = 160ms to set a deadline from start time, where the agent returns the best actions from the deepest fully completed search, this removed the problem of nodes with high branching factors to be explored till deadline and achieving depth 3 in easier nodes.
Alpha Beta with ordered actions
For Pac-Man, quick_score uses Manhattan distance from food, penalty for getting close to non-scared ghosts and successor score to order the actions. Ghost orders actions with moves with minimum Manhattan distance to Pac-Man. This ordering is computationally cheap.
Beam search at MAX nodes
Before recursing at Pac-Man nodes, ordered actions discards moves greater than BEAM_K to avoid high branching factor, a tradeoff for speedy computation. During recursion computation cost is reduced.
Tiny Transposition Table per action
Uses key = (agentIndex, depthLeft, plyCount, Pac-Man pos, tuple((ghost_x, ghost_y, scaredFlag) for each ghost), food_count). This key reduces duplicate work across adjacent branches.
Strong Evaluation with caching
Maze distance to food/capsules is more accurate than Manhattan, but computationally expensive, to keep consistency of increasing speed with fewer computation number of foods is capped. BFS is cached in md_cache -> stores maze distances of food/capsules coordinates capped to K nearest foods for Pac-Man and Manhattan distance to Pac-Man for ghosts; and any repeated query for these distances will be reused. Evaluation considers base score, food proximity(pull), fewer foods(reward), capsule pull when under threat, scared ghost attraction and strong penalties for proximity to non-scared ghosts.





Pseudocode:
function GET_ACTION(state):
    deadline ← now + 160ms
    bestAction ← STOP
    for depth = 1 .. MAX_DEPTH:
        (v, a) ← ALPHABETA(state, agent=0, ply=0, depthLeft=depth, α=-∞, β=+∞)
        if now > deadline: break
        if a ≠ None: bestAction ← a
    return bestAction

function ALPHABETA(s, i, ply, depthLeft, α, β):
    if timeout or depthLeft=0 or s is terminal: return EVAL(s), None

    key ← (i, depthLeft, ply, pac, ghosts, foodCount)
    if TT contains key with storedDepth ≥ depthLeft: return storedValue, None

    A ← ORDERED_ACTIONS(s, i)
    if A empty: return EVAL(s), None

    if i = 0 (MAX, Pac-Man):
        A ← BEAM_TOP_K(A, K=6)
        best ← -∞; bestAct ← None
        for a in A:
            v, _ ← ALPHABETA(succ(s,i,a), i=1, ply, depthLeft, α, β)
            best ← max(best, v); bestAct ← a if updated
            if best ≥ β: store TT; return best, bestAct
            α ← max(α, best)
        store TT; return best, bestAct
    else (MIN, ghosts):
        nextI ← i+1 (wrap to Pac-Man, and depthLeft−− after last ghost)
        best ← +∞; bestAct ← None
        for a in ORDERED_ACTIONS(s, i):
            v, _ ← ALPHABETA(succ(s,i,a), nextI, nextPly, nextDepth, α, β)
            best ← min(best, v); bestAct ← a if updated
            if best ≤ α: store TT; return best, bestAct
            β ← min(β, best)
        store TT; return best, bestAct






Results:
Qualitative
On some layouts the alpha-beta approach with fixed depth produced lagging, adding the deadline produces decisions faster. The gameplay remains strong with depth of 3 on simple nodes and depth of 2 on spiky ones. Stronger evaluation pulls, rewards and penalises score to set accurate heuristics

Quantitative
Adding ordered actions with beam reduced expansions of nodes thus increasing speed. Compared to fixed depth agent this agent consistently scores higher due to avoiding think-time timeouts and making timely decisions to reach capsule/food.


Discussion
Some layouts amplify branching(many junctions, more legal actions). With several ghosts, a fixed depth alpha-beta approach explores deep multi-agent trees, and when move order is weak, pruning is inefficient. Any expensive evaluation multiplies across a high number of nodes, causing lag. The optimisations using iterative deepening + deadline ensures an action on time without hardcoding a shallow depth. Move ordering makes alpha-beta prune effectively by exploring the good actions. The transposition table keeps track and avoids recalculating similar branches that arise in some cases due to all ghosts’ symmetric nature. Cached maze distances and food cap keeps the evaluation informative and cheap.

Trade-offs
The beam can occasionally prune better actions if the quick ordering is not optimal, however with k=6 the loss is rare. The time budget restricts some nodes to reach only a depth of 2 instead of 3 a fair trade-off to avoid lag. 

Conclusion:
The optimised agent is more efficient than the basic agent with fixed depth alpha-beta core. Time budgeted iterative deepening, strong action ordering, beam pruning, TT caching and a cached maze-distance evaluation proved to be a reliable core for the agent. On difficult layouts it does not lag and makes effective decisions on time. The main conclusion after solving the problem was controlling latency using deadlines and iterative deepening, then compensating using pruning and caching. Also well targeted heuristics using ordering and beam cap proved to be better than expensive computation. Efficient caching converts expensive computation in BFS distances into cheap and reusable helper. 











I acknowledge that I have used AI: ChatGPT to help me in the assignment: https://chatgpt.com/
I used prompts to explain time and space complexity of the algorithms taught in class that could be used to solve the problems and selected the best algorithm. I used AI to generate a pseudo code for each algorithm and used it to trace the calculations and then applied that in my code. I also used AI to optimize the structure of my code and debug errors for unexpected outputs so that I could focus more on the algorithmic approach used to solve each problem.















Q2
Introduction:

The problem required designing a search agent for the Pac-Man to plan its path for collecting all food in a given layout and reasons against ghost agents. Used minmax with alpha-beta pruning with optimisation of high branching factors in long corridors and many junctions and also deep moves trees using speed-quality tradeoff.

Method:
Problem Representation:

Game tree: Alternating MAX(Pac-Man) and MIN(Ghosts) layers
Depth account: Depth tracks Pac-Man plies, after all ghosts act the depth decreases
Terminal States: isWin, isLose or depth limit reached
Evaluation: Scores for different environment used as numeric heuristic

Algorithmic approach and optimisation:

Alpha Beta with iterative deepening
Used MAX_MILLIS = 160ms to set a deadline from start time, where the agent returns the best actions from the deepest fully completed search, this removed the problem of nodes with high branching factors to be explored till deadline and achieving depth 3 in easier nodes.
Alpha Beta with ordered actions
For Pac-Man, quick_score uses Manhattan distance from food, penalty for getting close to non-scared ghosts and successor score to order the actions. Ghost orders actions with moves with minimum Manhattan distance to Pac-Man. This ordering is computationally cheap.
Beam search at MAX nodes
Before recursing at Pac-Man nodes, ordered actions discards moves greater than BEAM_K to avoid high branching factor, a tradeoff for speedy computation. During recursion computation cost is reduced.
Tiny Transposition Table per action
Uses key = (agentIndex, depthLeft, plyCount, Pac-Man pos, tuple((ghost_x, ghost_y, scaredFlag) for each ghost), food_count). This key reduces duplicate work across adjacent branches.
Strong Evaluation with caching
Maze distance to food/capsules is more accurate than Manhattan, but computationally expensive, to keep consistency of increasing speed with fewer computation number of foods is capped. BFS is cached in md_cache -> stores maze distances of food/capsules coordinates capped to K nearest foods for Pac-Man and Manhattan distance to Pac-Man for ghosts; and any repeated query for these distances will be reused. Evaluation considers base score, food proximity(pull), fewer foods(reward), capsule pull when under threat, scared ghost attraction and strong penalties for proximity to non-scared ghosts.





Pseudocode:
function GET_ACTION(state):
    deadline ← now + 160ms
    bestAction ← STOP
    for depth = 1 .. MAX_DEPTH:
        (v, a) ← ALPHABETA(state, agent=0, ply=0, depthLeft=depth, α=-∞, β=+∞)
        if now > deadline: break
        if a ≠ None: bestAction ← a
    return bestAction

function ALPHABETA(s, i, ply, depthLeft, α, β):
    if timeout or depthLeft=0 or s is terminal: return EVAL(s), None

    key ← (i, depthLeft, ply, pac, ghosts, foodCount)
    if TT contains key with storedDepth ≥ depthLeft: return storedValue, None

    A ← ORDERED_ACTIONS(s, i)
    if A empty: return EVAL(s), None

    if i = 0 (MAX, Pac-Man):
        A ← BEAM_TOP_K(A, K=6)
        best ← -∞; bestAct ← None
        for a in A:
            v, _ ← ALPHABETA(succ(s,i,a), i=1, ply, depthLeft, α, β)
            best ← max(best, v); bestAct ← a if updated
            if best ≥ β: store TT; return best, bestAct
            α ← max(α, best)
        store TT; return best, bestAct
    else (MIN, ghosts):
        nextI ← i+1 (wrap to Pac-Man, and depthLeft−− after last ghost)
        best ← +∞; bestAct ← None
        for a in ORDERED_ACTIONS(s, i):
            v, _ ← ALPHABETA(succ(s,i,a), nextI, nextPly, nextDepth, α, β)
            best ← min(best, v); bestAct ← a if updated
            if best ≤ α: store TT; return best, bestAct
            β ← min(β, best)
        store TT; return best, bestAct






Results:
Qualitative
On some layouts the alpha-beta approach with fixed depth produced lagging, adding the deadline produces decisions faster. The gameplay remains strong with depth of 3 on simple nodes and depth of 2 on spiky ones. Stronger evaluation pulls, rewards and penalises score to set accurate heuristics

Quantitative
Adding ordered actions with beam reduced expansions of nodes thus increasing speed. Compared to fixed depth agent this agent consistently scores higher due to avoiding think-time timeouts and making timely decisions to reach capsule/food.


Discussion
Some layouts amplify branching(many junctions, more legal actions). With several ghosts, a fixed depth alpha-beta approach explores deep multi-agent trees, and when move order is weak, pruning is inefficient. Any expensive evaluation multiplies across a high number of nodes, causing lag. The optimisations using iterative deepening + deadline ensures an action on time without hardcoding a shallow depth. Move ordering makes alpha-beta prune effectively by exploring the good actions. The transposition table keeps track and avoids recalculating similar branches that arise in some cases due to all ghosts’ symmetric nature. Cached maze distances and food cap keeps the evaluation informative and cheap.

Trade-offs
The beam can occasionally prune better actions if the quick ordering is not optimal, however with k=6 the loss is rare. The time budget restricts some nodes to reach only a depth of 2 instead of 3 a fair trade-off to avoid lag. 

Conclusion:
The optimised agent is more efficient than the basic agent with fixed depth alpha-beta core. Time budgeted iterative deepening, strong action ordering, beam pruning, TT caching and a cached maze-distance evaluation proved to be a reliable core for the agent. On difficult layouts it does not lag and makes effective decisions on time. The main conclusion after solving the problem was controlling latency using deadlines and iterative deepening, then compensating using pruning and caching. Also well targeted heuristics using ordering and beam cap proved to be better than expensive computation. Efficient caching converts expensive computation in BFS distances into cheap and reusable helper. 

