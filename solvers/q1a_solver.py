#---------------------#
# DO NOT MODIFY BEGIN #
#---------------------#

import logging

import util
from problems.q1a_problem import q1a_problem

def q1a_solver(problem: q1a_problem):
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
#     while not terminate:
#         num_expansions += 1
#         terminate, maybe_path = astar_loop_body(problem, astarData)
#         if maybe_path is not None: # Had to modify to prevent crash, if we found a path extra check 
#             result = maybe_path
#     print(f'Number of node expansions: {num_expansions}')
#     return result
class AStarData:
    # YOUR CODE HERE
    def __init__(self):
        # pass
        self.frontier = util.PriorityQueue()  # holds (state, path, g) with priority f
        self.best_g = {}                      # dict: state -> best g found so far
        self.goal = None                      # (gx, gy)

def astar_initialise(problem: q1a_problem):
    # YOUR CODE HERE
    data = AStarData()
    start = problem.getStartState()
    data.goal = problem._goal  # goal coordinate from the problem
    data.best_g[start] = 0
    # seed frontier with start
    f0 = astar_heuristic(start, data.goal)
    data.frontier.push((start, [], 0), f0)
    return data

def astar_loop_body(problem: q1a_problem, data: AStarData):
    # YOUR CODE HERE
    # util.raiseNotDefined()  # Delete this line
    """
    Performs one A* expansion step.
    Returns:
      (terminate: bool, path_or_none: list|None)
      - If goal popped: (True, path)
      - If frontier empty: (True, [])
      - Otherwise: (False, None)
    """
    if data.frontier.isEmpty():
        return True, []  # no solution

    state, path, g = data.frontier.pop()

    # Goal reached?
    if problem.isGoalState(state):
        return True, path

    # Skip stale entries
    if g != data.best_g.get(state, float("inf")):
        return False, None

    # Expand
    for succ, action, cost in problem.getSuccessors(state):
        ng = g + cost
        if ng < data.best_g.get(succ, float("inf")):
            data.best_g[succ] = ng
            f = ng + astar_heuristic(succ, data.goal)
            data.frontier.push((succ, path + [action], ng), f)

    return False, None

def astar_heuristic(current, goal):
    # YOUR CODE HERE
    # return 0
    x, y = current
    gx, gy = goal
    return abs(x - gx) + abs(y - gy)
