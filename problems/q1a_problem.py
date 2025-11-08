import logging
import time
from typing import Tuple

import util
from game import Actions, Agent, Directions
from logs.search_logger import log_function
from pacman import GameState


class q1a_problem:
    """
    A search problem defines the state space, start state, goal test, successor
    function and cost function.  This search problem can be used to find paths
    to a particular point on the pacman board.

    The state space consists of (x,y) positions in a pacman game.

    Note: this search problem is fully specified; you should NOT change it.
    """
    def __str__(self):
        return str(self.__class__.__module__)

    def __init__(self, gameState: GameState):
        """
        Stores the start and goal.

        gameState: A GameState object (pacman.py)
        costFn: A function from a search state (tuple) to a non-negative number
        goal: A position in the gameState
        """
        self.startingGameState: GameState = gameState
         # Cache walls and start position for quick access
        self._walls = gameState.getWalls()
        self._start = gameState.getPacmanPosition()

        food = gameState.getFood()
        self._goal = None
        for x in range(food.width):
            for y in range(food.height):
                if food[x][y]:
                    self._goal = (x, y)
                    break
            if self._goal is not None:
                break
        assert self._goal is not None
    @log_function
    def getStartState(self):
        "*** YOUR CODE HERE ***"
        return self._start
        #util.raiseNotDefined()


    @log_function
    def isGoalState(self, state):
        "*** YOUR CODE HERE ***"
        return state == self._goal
        #util.raiseNotDefined()

    @log_function
    def getSuccessors(self, state):
        """
        Returns successor states, the actions they require, and a cost of 1.

         As noted in search.py:
             For a given state, this should return a list of triples,
         (successor, action, stepCost), where 'successor' is a
         successor to the current state, 'action' is the action
         required to get there, and 'stepCost' is the incremental
         cost of expanding to that successor
        """
        # ------------------------------------------
        "*** YOUR CODE HERE ***"
        x, y = state
        successors = []
        moves = {
            Directions.NORTH: (0, 1),
            Directions.SOUTH: (0, -1),
            Directions.EAST:  (1, 0),
            Directions.WEST:  (-1, 0),
        }
        for action, (dx, dy) in moves.items():
            nx, ny = x + dx, y + dy
            if not self._walls[nx][ny]:
                successors.append(((nx, ny), action, 1))
        return successors
        #util.raiseNotDefined()


