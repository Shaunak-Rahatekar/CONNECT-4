"""
algorithms package — AI opponents for Connect-4.

Exported modules and utilities:
- greedy: Greedy heuristic decision maker
- minimax: Recursive Minimax search
- evaluation: Static heuristic evaluation functions and configurable weights
"""

from algorithms.greedy import (
    choose_greedy_move,
    get_greedy_decision,
    GreedyDecision,
)
from algorithms.minimax import (
    choose_minimax_move,
    get_minimax_decision,
    MinimaxDecision,
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
    "choose_minimax_move",
    "get_minimax_decision",
    "MinimaxDecision",
    "evaluate_board",
    "HeuristicWeights",
    "DEFAULT_WEIGHTS",
]
