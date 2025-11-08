import logging
import random
import time
import math
import util
from game import Actions, Agent, Directions
from logs.search_logger import log_function
from pacman import GameState
from util import manhattanDistance
from collections import deque


def scoreEvaluationFunction(currentGameState):
    """
      This default evaluation function just returns the score of the state.
      The score is the same one displayed in the Pacman GUI.

      This evaluation function is meant for use with adversarial search agents
      (not reflex agents).
    """
    return currentGameState.getScore()

class Q2_Agent(Agent):

    def __init__(self, evalFn = 'scoreEvaluationFunction', depth = '3'):
        self.index = 0 # Pacman is always agent index 0
        self.evaluationFunction = util.lookup(evalFn, globals())
        self.depth = int(depth)

    @log_function
    def getAction(self, gameState: GameState):
        """
            Returns the minimax action from the current gameState using self.depth
            and self.evaluationFunction.

            Here are some method calls that might be useful when implementing minimax.

            gameState.getLegalActions(agentIndex):
            Returns a list of legal actions for an agent
            agentIndex=0 means Pacman, ghosts are >= 1

            gameState.generateSuccessor(agentIndex, action):
            Returns the successor game state after an agent takes an action

            gameState.getNumAgents():
            Returns the total number of agents in the game
        """
        logger = logging.getLogger('root')
        # logger.info('MinimaxAgent')
        "*** YOUR CODE HERE ***"
        #util.raiseNotDefined()
        logger.info('Q2_Agent (ID Alpha–Beta + Beam + TT + Cached Eval)')

        numAgents = gameState.getNumAgents()
        walls = gameState.getWalls()

        # -------- Tunables (adjust if you like) --------
        MAX_MILLIS = 160            # per-move time budget (ms); try 120–200
        BEAM_K = 6                  # keep top-K actions at Pac-Man (MAX) nodes
        MAX_DEPTH = self.depth      # maximum Pac-Man plies to attempt this move
        FOOD_EVAL_CAP = 7           # only check nearest K foods (keeps eval cheap)

        deadline = time.time() + MAX_MILLIS / 1000.0

        # -------- Per-move caches (reset each call) --------
        md_cache = {}   # ((ax,ay),(bx,by)) -> exact maze distance via BFS
        tt = {}         # transposition table: key -> (depthLeft, value)



        # ---------- Helpers ----------

        def maze_distance(a, b):
            """Exact shortest steps in the maze via BFS, with symmetric caching."""
            key = (a, b) if a <= b else (b, a)
            if key in md_cache:
                return md_cache[key]
            if a == b:
                md_cache[key] = 0
                return 0
            q = deque([(a, 0)])
            seen = {a}
            while q:
                (x, y), d = q.popleft()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    # Rely on border walls to keep indices valid in project layouts
                    if walls[nx][ny] or (nx, ny) in seen:
                        continue
                    if (nx, ny) == b:
                        md_cache[key] = d + 1
                        return d + 1
                    seen.add((nx, ny))
                    q.append(((nx, ny), d + 1))
            # Disconnected (should not happen), fall back to Manhattan:
            md_cache[key] = manhattanDistance(a, b)
            return md_cache[key]

           # ====== Move ordering (CRUCIAL for pruning) ======

        def ordered_actions(state, agentIndex):
            """
            Get legal actions(N,S,E,W) 
            If a wall coordinate in an action then its not legal
            """
            acts = state.getLegalActions(agentIndex)
            if not acts:
                return acts

            # Pac-Man (MAX): prefer non-STOP, closer to food, and safer vs nearby ghosts
            if agentIndex == 0: # Pac-Man index is 0
                acts = [a for a in acts if a != Directions.STOP] or acts
                food = state.getFood()
                food_list = [(x, y) for x in range(food.width) for y in range(food.height) if food[x][y]]
                pac = state.getPacmanPosition()
                ghosts = state.getGhostStates()

                def quick_score(a):
                    """
                    ***Pac-Man move***
                    Finds quick score:
                    quick_score(a) = (-d_food_MH, g_pen, succ_score)
                    d_food_MH: Manhattan distance from successor pac pos to nearest food
                    g_pen: Light penalty if any non-scared ghost within 2 steps after the action/move
                        If Manhattan distance from Pac pos to non_scared ghost <= 2 use penalty
                        Example: MH_distance = 1; g_pen -= (3 -1)*10 = -20
                    succ_score: tie-break using successor's built-in score
                    Sort quick score (reverse = True) using first element i.e. d_food_MH and store sorted acts
                        If sorted acts < BEAM_K: do not prune
                        Else: Prune to avoid high growth of branching factor
                        (Example if acts 10 in depth 3 with 2 ghosts then 10 * 4 *4 = 160 nodes per ply
                        (Pac move: ply 0, then ghost1 move: ply 1, then ghost2 move: ply 2)
                        With BEAM_K = 6 it drops tp 6 * 4 * 4 = 96 nodes per ply
                        Across thousands of expansions, this saves time and prevents lag
                        This is a speed-quality tradeoff) 
                    """
                    succ = state.generateSuccessor(0, a)
                    sp = succ.getPacmanPosition()
                    # Manhattan to nearest food (cheap proxy for ordering)
                    if food_list:
                        d_food = min(abs(sp[0] - fx) + abs(sp[1] - fy) for fx, fy in food_list)
                    else:
                        d_food = 0
                    # Light ghost pressure for non-scared ghosts
                    g_pen = 0
                    for g in ghosts:
                        if g.scaredTimer == 0:
                            gx, gy = g.getPosition()
                            gd = abs(int(gx) - sp[0]) + abs(int(gy) - sp[1])
                            if gd <= 2:  # closer ghosts penalize more
                                g_pen -= (3 - gd) * 10
                    # Also include successor score for tie-breaks
                    return (-d_food, g_pen, succ.getScore())

                acts = sorted(acts, key=quick_score, reverse=True)
                # Beam: cap branching factor up front
                if len(acts) > BEAM_K:
                    acts = acts[:BEAM_K]
                return acts

            # Ghosts (MIN): prefer moves that head toward Pac-Man (helps early cutoffs)
            pac = state.getPacmanPosition()

            def ghost_order(a):
                """
                ***Ghost move***
                agentIndex is ordered and stores acts to reduce MH distance from Pac pos
                """
                succ = state.generateSuccessor(agentIndex, a)
                gx, gy = succ.getGhostStates()[agentIndex - 1].getPosition()
                return -(abs(int(gx) - pac[0]) + abs(int(gy) - pac[1]))  # nearer first

            return sorted(acts, key=ghost_order)


        # ====== Strong evaluation (fast, cached where it counts) ======

        def better_eval(state):
            """
            Calculate better_eval after one full ply is done is alphabeta function
            Pac-Man
            Calculate MH distance from Pac pos to all foods and steps to each food with maze_distance
            and store steps in md_cache
            d_food is food with the minimum steps and calculates score 
            and also subtracts len of food(food remaining) to the score 
            After food calculates score for len of capsule(capsules remaining)

            Ghost
            Calculate MH distance to Pac only
            If scared ghost add scared pull to score to chase the ghost
            If MH distance <= 2 then threat_nearby -> true and add penalties to the score
            If threat nearby_true calculate maze_distance steps to capsule 
            and add to md_cache and pull towards capsule score updated
            Return score for each node to calling function(alphabeta)
            """
            # Terminal spikes
            if state.isWin():
                return 1e6
            if state.isLose():
                return -1e6

            score = state.getScore()
            pac = state.getPacmanPosition()

            # Foods
            food = state.getFood()
            foods = [(x, y) for x in range(food.width) for y in range(food.height) if food[x][y]]

            # Capsules
            capsules = state.getCapsules()

            # Ghosts
            ghosts = state.getGhostStates()

            # Food proximity (use exact maze distance, but only for K nearest by Manhattan)
            # Food EVAL capped to 7
            if foods:
                nearest_by_mh = sorted(foods, key=lambda f: abs(pac[0] - f[0]) + abs(pac[1] - f[1]))[:FOOD_EVAL_CAP]
                d_food = min(maze_distance(pac, f) for f in nearest_by_mh)
                score += 6.0 / (1.0 + d_food)   # strong pull toward nearby food
                score -= 2.0 * len(foods)       # fewer foods remaining is better

            # Capsules: smaller negative for remaining capsules (incentivize collecting)
            score -= 3.0 * len(capsules)

            # Ghost interactions
            min_g = float('inf')
            threat_nearby = False
            scared_pull = 0.0
            for g in ghosts:
                gx, gy = g.getPosition()
                gd = abs(int(gx) - pac[0]) + abs(int(gy) - pac[1])  # Manhattan for speed here
                # min_g = min Manhattan(pac, any ghost)
                min_g = min(min_g, gd)
                if g.scaredTimer > 0:
                    # Chase scared ghosts a bit (closer is better)
                    scared_pull += 10.0 / (1.0 + gd)
                else:
                    if gd <= 2: #non scared ghost within 2 steps then threat nearby
                        threat_nearby = True
            score += scared_pull
            # Hard penalties for being close to non-scared ghosts
            if min_g <= 1:
                score -= 300.0
            elif min_g <= 2:
                score -= 40.0

            # If threatened, pull toward nearest capsule via exact path distance
            if threat_nearby and capsules:
                d_cap = min(maze_distance(pac, c) for c in capsules)
                score += 5.0 / (1.0 + d_cap)

            # Return final score
            return score

        evalFn = better_eval  # using stronger evaluation


        def tt_key(state, agentIndex, depthLeft, plyCount):
            """
            key = (agentIndex, depthLeft, plyCount,
            Pac-Man postion,
            tuple((ghost_x, ghost_y, scaredFlag) for each ghost),
            food_count)
            """
            pac = state.getPacmanPosition()
            ghosts = tuple(
                (int(gs.getPosition()[0]), int(gs.getPosition()[1]), 1 if gs.scaredTimer > 0 else 0)
                for gs in state.getGhostStates()
            )
            # Cheap feature: number of foods remaining (keeps key small & useful)
            food = state.getFood()
            food_count = sum(1 for x in range(food.width) for y in range(food.height) if food[x][y])
            return (agentIndex, depthLeft, plyCount, pac, ghosts, food_count)

        # ====== Terminal check ======

        def terminal(state, plyCount, depthLeft):
            """
            Stop if True
            True -> if: depthLeft = 0 || isWin() || isLose() || time > deadline
            """
            # Stop if: depth finished, win/lose, or we ran out of time
            return depthLeft == 0 or state.isWin() or state.isLose() or time.time() > deadline

        # ====== Alpha–beta with deadline, beam ordering, and TT ======

        def alphabeta(state, agentIndex, plyCount, depthLeft, alpha, beta):
            """
            agentIndex change order: Pac-Man -> Ghost1 -> Ghost2 -> Ghost... -> Pac-Man
            After depthLeft = 0 ie one full ply done, terminal state fires and calls better_eval which calculates(see better_eval) 
            and updates bestVal and alpha beta values at each nodes
            """
            # Deadline guard
            if time.time() > deadline:
                return evalFn(state), None

            if terminal(state, plyCount, depthLeft):
                return evalFn(state), None

            key = tt_key(state, agentIndex, depthLeft, plyCount)
            hit = tt.get(key)
            if hit is not None:
                hitDepth, hitVal = hit
                if hitDepth >= depthLeft:
                    return hitVal, None  # reuse cached value
            # Sorted ordered actions
            actions = ordered_actions(state, agentIndex)
            if not actions:
                v = evalFn(state)
                tt[key] = (depthLeft, v)
                return v, None

            # Pac-Man (MAX)
            if agentIndex == 0:
                bestVal = -math.inf
                bestAct = None
                for a in actions:
                    succ = state.generateSuccessor(0, a)
                    #call function recursively with Ghost(agentIndex = 1) for each sorted actions
                    v, _ = alphabeta(succ, 1, plyCount, depthLeft, alpha, beta)
                    if v > bestVal:
                        bestVal, bestAct = v, a
                    if bestVal >= beta:
                        tt[key] = (depthLeft, bestVal)
                        return bestVal, bestAct
                    alpha = max(alpha, bestVal)
                tt[key] = (depthLeft, bestVal)
                return bestVal, bestAct

            # Ghosts (MIN, in sequence)
            else:
                bestVal = math.inf
                bestAct = None
                nextAgent = agentIndex + 1
                nextPly = plyCount
                nextDepth = depthLeft
                # After last ghost, Pac-Man's next ply starts; reduce depth then
                if nextAgent == numAgents:
                    nextAgent = 0
                    nextPly = plyCount + 1
                    nextDepth = depthLeft - 1

                for a in actions:
                    succ = state.generateSuccessor(agentIndex, a)
                    # Call function recursively with nextAgent for each sorted actions
                    # If agentIndex = 1 call nextAgent->Ghost(agentIndex = 2), if terminal then set score to -1e6 and go back to previous agent 
                    # Else if agentIndex = 2 then nextAgent->Pac(agentIndex = 0)
                    v, _ = alphabeta(succ, nextAgent, nextPly, nextDepth, alpha, beta)
                    if v < bestVal:
                        bestVal, bestAct = v, a
                    if bestVal <= alpha:
                        tt[key] = (depthLeft, bestVal)
                        return bestVal, bestAct
                    # Choose action with minimum MH distance to Pac
                    beta = min(beta, bestVal)
                tt[key] = (depthLeft, bestVal)
                return bestVal, bestAct

        # ====== Iterative deepening (1..MAX_DEPTH within deadline) ======

        bestActionOverall = None
        bestValOverall = -math.inf

        for depthGoal in range(1, MAX_DEPTH + 1):
            if time.time() > deadline:
                break

            val, act = alphabeta(gameState, agentIndex=0, plyCount=0,
                                  depthLeft=depthGoal, alpha=-math.inf, beta=math.inf)

            if time.time() > deadline:
                break

            if act is not None:
                bestValOverall, bestActionOverall = val, act

            # if very strong eval, we can stop early
            if bestValOverall > 1e5 or gameState.isWin():
                break

        return bestActionOverall or Directions.STOP