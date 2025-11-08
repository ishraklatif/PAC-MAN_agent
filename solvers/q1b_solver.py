#---------------------#
# DO NOT MODIFY BEGIN #
#---------------------#

import logging

import util
from problems.q1b_problem import q1b_problem

def q1b_solver(problem: q1b_problem):
    astarData = astar_initialise(problem)
    num_expansions = 0
    terminate = False
    while not terminate:
        num_expansions += 1
        terminate, result = astar_loop_body(problem, astarData)
    print(f'Number of node expansions: {num_expansions}')
    return result
   
#-------------------#
# DO NOT MODIFY END #
#-------------------#
 # result = []
    # modified block
    # while not terminate:
    #     num_expansions += 1
    #     terminate, maybe_path = astar_loop_body(problem, astarData)
    #     if maybe_path is not None: # Had to modify to prevent crash, if we found a path extra check
    #         result = maybe_path
    # print(f'Number of node expansions: {num_expansions}')
    # return result
class AStarData:
    # YOUR CODE HERE
    def __init__(self):
        self.frontier = util.PriorityQueue()   # stores (state, path, g) keyed by f
        self.best_g   = {}                     # state -> best g
        self.heur     = None                   # function: h(state)
        self.final    = None                   # final path (list of actions), optional                    # set of (x,y) food positions

def astar_initialise(problem: q1b_problem):
    # YOUR CODE HERE
    """
    Initialise A*:
      - start state from problem
      - best_g, frontier with f = g + h
      - heuristic closes over the corners from the problem
    """
    D = AStarData()
    s0 = problem.getStartState()
    D.best_g[s0] = 0

    # Build a heuristic that knows the four corners.
    # Expect the state shape: ((x,y), visitedTupleOf4Bools)
    # If your q1b_problem exposes corners, prefer that (e.g., problem.corners).
    try:
        corners = tuple(problem.corners)  # e.g., ((1,1),(1,5),(5,1),(5,5))
    except Exception:
        # Fallback: derive corners from the starting layout if your problem provides it.
        # (Adjust to your actual API if needed.)
        walls = problem.startingGameState.getWalls()
        maxX, maxY = walls.width - 2, walls.height - 2
        corners = ((1,1), (1,maxY), (maxX,1), (maxX,maxY))

    def h(state):
        return astar_heuristic(state, corners)

    D.heur = h
    f0 = 0 + D.heur(s0)
    D.frontier.push((s0, [], 0), f0)
    return D

def astar_loop_body(problem: q1b_problem, D: AStarData):
    """
    One expansion step of A*.
    Returns:
      (terminate: bool, result: list|None)
      - (False, None) while searching
      - (True, path) on success
      - (True, []) if frontier empties (no solution)
    This contract lets the unmodified q1b_solver work safely.
    """
    if D.frontier.isEmpty():
        return True, D.final or []  # graceful no-solution

    state, path, g = D.frontier.pop()

    # If this entry is stale (there is a better g), skip it
    if g != D.best_g.get(state, float("inf")):
        return False, None

    # Goal test MUST use problem's definition (visit all corners)
    if problem.isGoalState(state):
        D.final = path
        return True, path

    # Expand successors; each successor: (succState, action, stepCost)
    succs = list(problem.getSuccessors(state))

    # Optional: light ordering by heuristic for nicer behavior
    succs.sort(key=lambda triple: D.heur(triple[0]))

    for succ, action, cost in succs:
        ng = g + cost
        if ng < D.best_g.get(succ, float("inf")):
            D.best_g[succ] = ng
            f = ng + D.heur(succ)
            D.frontier.push((succ, path + [action], ng), f)

    return False, None

def astar_heuristic(state, corners):
    """
    Admissible heuristic for corners:
      state = ((x,y), visitedTupleOf4Bools)
      h = max Manhattan distance to any UNVISITED corner
    (You can also use MST over remaining corners for a tighter h, but max distance
     is simple and admissible.)
    """
    # Unpack state robustly
    if isinstance(state, tuple) and len(state) == 2 and isinstance(state[1], tuple):
        (x, y), visited = state
    else:
        # Fallback if your state is just (x,y)
        (x, y) = state
        visited = (False, False, False, False)

    # Build list of remaining corners
    remaining = []
    for idx, c in enumerate(corners):
        if not visited[idx]:
            remaining.append(c)

    if not remaining:
        return 0

    # Use max Manhattan to remaining corners (admissible)
    return max(abs(x - cx) + abs(y - cy) for (cx, cy) in remaining)