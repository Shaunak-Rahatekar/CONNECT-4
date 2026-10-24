"""
comparison.py — Automated comparison framework for Connect-4 AI search algorithms.

Compares identical board positions across:
1. Minimax without pruning
2. Alpha-Beta Pruning without move ordering
3. Alpha-Beta Pruning with move ordering

All three runs execute under identical search depth, terminal scoring constants,
and static heuristic weights to provide strict empirical comparisons.
"""

from __future__ import annotations
import time
from typing import Any, Union

from game.board import Board, PLAYER2
from algorithms.minimax import get_minimax_decision, MinimaxDecision
from algorithms.alphabeta import get_alphabeta_decision, AlphaBetaDecision


def compare_algorithms(
    board: Union[Board, list[list[int]]],
    depth: int = 3,
    player: int = PLAYER2,
    repeats: int = 1,
) -> dict[str, Any]:
    """Execute all three search strategies on the exact same board position.

    Parameters:
    -----------
    board : Board or list[list[int]]
        The Connect-4 board position to evaluate.
    depth : int
        Search depth limit (1 to 5).
    player : int
        Maximizing player (PLAYER1 or PLAYER2). Defaults to PLAYER2.
    repeats : int
        Number of repeated timed runs for statistical stability when execution time
        is very small (< 10 ms). Default 1.

    Returns:
    --------
    dict[str, Any] : Structured comparison report including:
        - Results for Minimax, Alpha-Beta (no ordering), Alpha-Beta (with ordering)
        - Pruning reduction percentage
        - Measured speedup ratios
        - Consistency validation (checking that scores are equivalent)
    """
    safe_depth = max(1, min(depth, 5))
    safe_repeats = max(1, min(repeats, 10))

    # 1. Minimax Baseline
    mm_decision: MinimaxDecision = get_minimax_decision(board, depth=safe_depth, player=player)
    if safe_repeats > 1:
        total_time = 0.0
        for _ in range(safe_repeats):
            t0 = time.perf_counter()
            get_minimax_decision(board, depth=safe_depth, player=player)
            total_time += (time.perf_counter() - t0) * 1000.0
        mm_time = total_time / safe_repeats
    else:
        mm_time = mm_decision.execution_time_ms

    # 2. Alpha-Beta without move ordering
    ab_no_ord: AlphaBetaDecision = get_alphabeta_decision(
        board,
        depth=safe_depth,
        player=player,
        use_move_ordering=False,
    )
    if safe_repeats > 1:
        total_time = 0.0
        for _ in range(safe_repeats):
            t0 = time.perf_counter()
            get_alphabeta_decision(board, depth=safe_depth, player=player, use_move_ordering=False)
            total_time += (time.perf_counter() - t0) * 1000.0
        ab_no_ord_time = total_time / safe_repeats
    else:
        ab_no_ord_time = ab_no_ord.execution_time_ms

    # 3. Alpha-Beta with move ordering
    ab_ord: AlphaBetaDecision = get_alphabeta_decision(
        board,
        depth=safe_depth,
        player=player,
        use_move_ordering=True,
    )
    if safe_repeats > 1:
        total_time = 0.0
        for _ in range(safe_repeats):
            t0 = time.perf_counter()
            get_alphabeta_decision(board, depth=safe_depth, player=player, use_move_ordering=True)
            total_time += (time.perf_counter() - t0) * 1000.0
        ab_ord_time = total_time / safe_repeats
    else:
        ab_ord_time = ab_ord.execution_time_ms

    # Validation: Both algorithms must produce identical optimal evaluation score
    score_match_no_ord = abs(mm_decision.score - ab_no_ord.score) < 1e-4
    score_match_ord = abs(mm_decision.score - ab_ord.score) < 1e-4

    # Calculate node reduction percentages vs Minimax baseline
    def calc_reduction(baseline_nodes: int, test_nodes: int) -> float:
        if baseline_nodes <= 0:
            return 0.0
        return round(((baseline_nodes - test_nodes) / baseline_nodes) * 100.0, 1)

    reduction_no_ord = calc_reduction(mm_decision.nodes_visited, ab_no_ord.nodes_visited)
    reduction_ord = calc_reduction(mm_decision.nodes_visited, ab_ord.nodes_visited)

    speedup_no_ord = round(mm_time / ab_no_ord_time, 2) if ab_no_ord_time > 0 else 1.0
    speedup_ord = round(mm_time / ab_ord_time, 2) if ab_ord_time > 0 else 1.0

    return {
        "depth": safe_depth,
        "repeats": safe_repeats,
        "scores_match": score_match_no_ord and score_match_ord,
        "optimal_score": round(mm_decision.score, 2),
        "algorithms": {
            "minimax": {
                "name": "Minimax (No Pruning)",
                "column": mm_decision.column,
                "column_1based": (mm_decision.column + 1) if mm_decision.column is not None else None,
                "score": round(mm_decision.score, 2),
                "nodes_visited": mm_decision.nodes_visited,
                "recursive_calls": mm_decision.recursive_calls,
                "cutoffs": 0,
                "execution_time_ms": round(mm_time, 3),
                "node_reduction_pct": 0.0,
                "speedup_ratio": 1.0,
            },
            "alphabeta_no_ordering": {
                "name": "Alpha-Beta (Natural Order)",
                "column": ab_no_ord.column,
                "column_1based": (ab_no_ord.column + 1) if ab_no_ord.column is not None else None,
                "score": round(ab_no_ord.score, 2),
                "nodes_visited": ab_no_ord.nodes_visited,
                "recursive_calls": ab_no_ord.recursive_calls,
                "cutoffs": ab_no_ord.cutoffs,
                "execution_time_ms": round(ab_no_ord_time, 3),
                "node_reduction_pct": reduction_no_ord,
                "speedup_ratio": speedup_no_ord,
            },
            "alphabeta_with_ordering": {
                "name": "Alpha-Beta (Move Ordering)",
                "column": ab_ord.column,
                "column_1based": (ab_ord.column + 1) if ab_ord.column is not None else None,
                "score": round(ab_ord.score, 2),
                "nodes_visited": ab_ord.nodes_visited,
                "recursive_calls": ab_ord.recursive_calls,
                "cutoffs": ab_ord.cutoffs,
                "execution_time_ms": round(ab_ord_time, 3),
                "node_reduction_pct": reduction_ord,
                "speedup_ratio": speedup_ord,
            },
        },
    }
