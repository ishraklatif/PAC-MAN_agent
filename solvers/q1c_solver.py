#---------------------#
# DO NOT MODIFY BEGIN #
#---------------------#

import logging

import util
from problems.q1c_problem import q1c_problem

#-------------------#
# DO NOT MODIFY END #
#-------------------#
import time
from collections import deque
from game import Directions

def q1c_solver(problem: q1c_problem, time_limit_seconds: float = 9.5):
    # YOUR CODE HERE
    #pass
    """
    Anytime-style planner for collecting many dots within a time limit.
    Tries full-board A* with MST heuristic; if too slow, falls back to
    nearest-dot micro-plans and concatenates them.
    """
    start_time = time.time()
    deadline = start_time + time_limit_seconds

    plan = []
    state = problem.getStartState()
    walls = problem.startingGameState.getWalls()  # access once

    # ---------- Try a full-board A* with MST heuristic (capped time) ----------
    pos, remaining = state
    MANY_DOTS = 50  # tune: if fewer dots than this, a full A* may succeed quickly
    if len(remaining) <= MANY_DOTS:
        # Using at most half the budget for a full solution attempt
        global_deadline = min(deadline, start_time + time_limit_seconds * 0.5)
        full_path = _astar_until(problem, state, problem.isGoalState, _h_q1c, deadline=global_deadline)
        if full_path:
            return full_path 

    # ---------- Greedy nearest-REACHABLE-dot loop (starts moving immediately) ----------
    while time.time() < deadline:
        pos, remaining = state
        if not remaining:
            break  # all dots eaten

        # Pick a reachable dot and the shortest BFS path to it.
        target, path_to_target = _nearest_reachable_dot_by_bfs(walls, pos, remaining)

        if target is None:
            # Nothing reachable from our chamber, rare on valid layouts
            break

        if not path_to_target:
            # We're already standing at 'target' visually; successors will remove it on step.
            first = _one_step_toward_bfs(problem, state, walls, target)
            if first:
                plan.append(first)
                state = _apply_actions(problem, state, [first])
            else:
                break
            continue

        # Take a small chunk of steps so we keep responding and avoid long stalls
        k = min(5, len(path_to_target))   
        chunk = path_to_target[:k]
        plan.extend(chunk)
        state = _apply_actions(problem, state, chunk)

        # If time is nearly up, return what we have
        if time.time() >= deadline:
            break

    # ---------- Final safety: never return an empty plan ----------
    if not plan:
        start_state = problem.getStartState()
        spos, srem = start_state
        if srem:
            target, path_to_target = _nearest_reachable_dot_by_bfs(walls, spos, srem)
            if path_to_target:
                return [path_to_target[0]]  # at least one step forward
        return [Directions.STOP]

    return plan



# ----------------- Helpers & A* -----------------

def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _mst_lower_bound(points):
    """
    Prim-like MST over Manhattan distances: admissible lower bound to visit all dots.
    """
    if not points:
        return 0
    pts = list(points)
    in_tree = {pts[0]}
    not_in = set(pts[1:])
    total = 0
    while not_in:
        best = float('inf'); pick = None
        for u in in_tree:
            ux, uy = u
            for v in not_in:
                vx, vy = v
                w = abs(ux - vx) + abs(uy - vy)
                if w < best:
                    best, pick = w, v
        total += best
        in_tree.add(pick)
        not_in.remove(pick)
    return total


def _h_q1c(state):
    """
    Heuristic for (pos, remainingDots): nearest-dot + MST(remaining).
    Admissible and informative for the full-board A* attempt.
    """
    pos, remaining = state
    if not remaining:
        return 0
    nearest = min(_manhattan(pos, d) for d in remaining)
    return nearest + _mst_lower_bound(remaining)


def _astar_until(problem, start_state, is_goal_predicate, h_func, deadline=None):
    """
    Vanilla A* over (pos, remainingDots) with an optional deadline.
    Returns an action list if the goal is reached before the deadline; else None.
    """
    frontier = util.PriorityQueue()
    frontier.push((start_state, [], 0), h_func(start_state))
    best_g = {start_state: 0}

    while not frontier.isEmpty():
        if deadline is not None and time.time() > deadline:
            return None  # ran out of time

        state, path, g = frontier.pop()
        if is_goal_predicate(state):
            return path

        if g != best_g.get(state, float("inf")):
            continue  # stale entry

        for succ, action, cost in problem.getSuccessors(state):
            ng = g + cost
            if ng < best_g.get(succ, float("inf")):
                best_g[succ] = ng
                frontier.push((succ, path + [action], ng), ng + h_func(succ))

    return None  # no solution for given predicate


# ------------------------ BFS utilities -------------------

def _bfs_path_from_to(walls, start_pos, goal_pos):
    """
    Shortest path (list of Directions) from start_pos to goal_pos using BFS on the grid.
    If unreachable, returns [].
    """
    if start_pos == goal_pos:
        return []
    q = deque()
    q.append((start_pos, []))
    seen = {start_pos}
   
    moves = {
        Directions.NORTH: (0, 1),
        Directions.SOUTH: (0, -1),
        Directions.EAST:  (1, 0),
        Directions.WEST:  (-1, 0),
    }
    while q:
        (x, y), path = q.popleft()
        for act, (dx, dy) in moves.items():
            nx, ny = x + dx, y + dy
            if walls[nx][ny]:
                continue
            np = (nx, ny)
            if np in seen:
                continue
            if np == goal_pos:
                return path + [act]
            seen.add(np)
            q.append((np, path + [act]))
    return []  # unreachable


def _nearest_reachable_dot_by_bfs(walls, pos, remaining):
    """
    Find the closest REACHABLE dot by maze distance.
    Returns (target_dot, bfs_path_to_target). If none reachable, (None, []).
    Uses Manhattan to pre-order candidates, but confirms with BFS.
    """
    best_target = None
    best_path = []
    best_len = float('inf')
    # Cheap prefilter by Manhattan, then exact by BFS
    for d in sorted(remaining, key=lambda t: abs(pos[0]-t[0]) + abs(pos[1]-t[1])):
        path = _bfs_path_from_to(walls, pos, d)
        if path and len(path) < best_len:
            best_len = len(path)
            best_target = d
            best_path = path
            if best_len == 1:  # cannot do better than 1 step
                break
    return best_target, best_path


def _one_step_toward_bfs(problem, state, walls, target):
    """
    Return the first step on a BFS shortest path from current pos to 'target', or None.
    """
    pos, _ = state
    path = _bfs_path_from_to(walls, pos, target)
    return path[0] if path else None


def _apply_actions(problem, state, actions):
    """
    Simulate applying actions using the problem's successor function to keep (pos, remainingDots) in sync.
    """
    cur = state
    for a in actions:
        nxt = None
        for (s2, act, _c) in problem.getSuccessors(cur):
            if act == a:
                nxt = s2
                break
        if nxt is None:
            break
        cur = nxt
    return cur
