import logging
import time
from typing import Tuple

import util
from game import Actions, Agent, Directions
from logs.search_logger import log_function
from pacman import GameState


class q1b_problem:
    """
    This search problem finds paths through all four corners of a layout.

    You must select a suitable state space and successor function
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
        self._walls = gameState.getWalls()
        self._start = gameState.getPacmanPosition()

        # Collect all dots from the initial food grid
        food = gameState.getFood()
        self._dots = {(x, y) for x in range(food.width) for y in range(food.height) if food[x][y]}

        # It’s allowed that there are zero dots (degenerate), but typically ≥ 1.

    @log_function
    def getStartState(self):
        "*** YOUR CODE HERE ***"
        return self._start
        #util.raiseNotDefined()

    @log_function
    def isGoalState(self, state):
        "*** YOUR CODE HERE ***"
        # Goal is satisfied when we stand on ANY food location
        return state in self._dots
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
            if not self._walls[nx][ny]:  # legal if no wall
                successors.append(((nx, ny), action, 1))

        return successors
        #util.raiseNotDefined()

