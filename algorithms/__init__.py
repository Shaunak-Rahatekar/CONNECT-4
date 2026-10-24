"""
algorithms package — AI opponents for Connect-4.

Exported modules and utilities:
- greedy: Greedy heuristic decision maker
- evaluation: Static heuristic evaluation functions and configurable weights
"""

from algorithms.greedy import (
    choose_greedy_move,
    get_greedy_decision,
    GreedyDecision,
)
from algorithms.evaluation import (
    evaluate_board,
    HeuristicWeights,
    DEFAULT_WEIGHTS,
)

__all__ = [
    "choose_greedy_move",
    "get_greedy_decision",
    "GreedyDecision",
    "evaluate_board",
    "HeuristicWeights",
    "DEFAULT_WEIGHTS",
]
