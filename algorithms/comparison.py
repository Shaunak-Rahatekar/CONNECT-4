"""
comparison.py — Automated comparison framework for Connect-4 AI search algorithms.

Compares identical board positions across:
1. Minimax without pruning
2. Alpha-Beta Pruning without move ordering (natural order, no cache)
3. Alpha-Beta Pruning with move ordering (no cache)
4. Alpha-Beta Pruning with move ordering + Transposition Table (memoization)

All four runs execute under identical search depth, terminal scoring constants,
and static heuristic weights to provide strict empirical comparisons.
"""

from __future__ import annotations
import time
from typing import Any, Union

from game.board import Board, PLAYER2
from algorithms.minimax import get_minimax_decision, MinimaxDecision
from algorithms.alphabeta import get_alphabeta_decision, AlphaBetaDecision
from algorithms.transposition_table import TranspositionTable


def compare_algorithms(
    board: Union[Board, list[list[int]]],
    depth: int = 3,
    player: int = PLAYER2,
    repeats: int = 1,
) -> dict[str, Any]:
    """Execute all search strategies on the exact same board position.

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
        - Results for Minimax, Alpha-Beta (no ordering), Alpha-Beta (with ordering),
          and Alpha-Beta with Transposition Table
        - Pruning reduction percentage
        - Measured speedup ratios
        - Cache hit rate and memory consumption
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

    # 2. Alpha-Beta without move ordering (no cache)
    ab_no_ord: AlphaBetaDecision = get_alphabeta_decision(
        board,
        depth=safe_depth,
        player=player,
        use_move_ordering=False,
        use_transposition_table=False,
    )
    if safe_repeats > 1:
        total_time = 0.0
        for _ in range(safe_repeats):
            t0 = time.perf_counter()
            get_alphabeta_decision(
                board,
                depth=safe_depth,
                player=player,
                use_move_ordering=False,
                use_transposition_table=False,
            )
            total_time += (time.perf_counter() - t0) * 1000.0
        ab_no_ord_time = total_time / safe_repeats
    else:
        ab_no_ord_time = ab_no_ord.execution_time_ms

    # 3. Alpha-Beta with move ordering (no cache)
    ab_ord: AlphaBetaDecision = get_alphabeta_decision(
        board,
        depth=safe_depth,
        player=player,
        use_move_ordering=True,
        use_transposition_table=False,
    )
    if safe_repeats > 1:
        total_time = 0.0
        for _ in range(safe_repeats):
            t0 = time.perf_counter()
            get_alphabeta_decision(
                board,
                depth=safe_depth,
                player=player,
                use_move_ordering=True,
                use_transposition_table=False,
            )
            total_time += (time.perf_counter() - t0) * 1000.0
        ab_ord_time = total_time / safe_repeats
    else:
        ab_ord_time = ab_ord.execution_time_ms

    # 4. Alpha-Beta with move ordering + Transposition Table (with cache)
    tt_instance = TranspositionTable(max_entries=100_000)
    ab_tt: AlphaBetaDecision = get_alphabeta_decision(
        board,
        depth=safe_depth,
        player=player,
        use_move_ordering=True,
        use_transposition_table=True,
        transposition_table=tt_instance,
    )
    if safe_repeats > 1:
        total_time = 0.0
        for _ in range(safe_repeats):
            fresh_tt = TranspositionTable(max_entries=100_000)
            t0 = time.perf_counter()
            get_alphabeta_decision(
                board,
                depth=safe_depth,
                player=player,
                use_move_ordering=True,
                use_transposition_table=True,
                transposition_table=fresh_tt,
            )
            total_time += (time.perf_counter() - t0) * 1000.0
        ab_tt_time = total_time / safe_repeats
    else:
        ab_tt_time = ab_tt.execution_time_ms

    # Validation: All algorithms must produce identical optimal evaluation score
    score_match_no_ord = abs(mm_decision.score - ab_no_ord.score) < 1e-4
    score_match_ord = abs(mm_decision.score - ab_ord.score) < 1e-4
    score_match_tt = abs(mm_decision.score - ab_tt.score) < 1e-4

    # Calculate node reduction percentages vs Minimax baseline
    def calc_reduction(baseline_nodes: int, test_nodes: int) -> float:
        if baseline_nodes <= 0:
            return 0.0
        return round(((baseline_nodes - test_nodes) / baseline_nodes) * 100.0, 1)

    reduction_no_ord = calc_reduction(mm_decision.nodes_visited, ab_no_ord.nodes_visited)
    reduction_ord = calc_reduction(mm_decision.nodes_visited, ab_ord.nodes_visited)
    reduction_tt = calc_reduction(mm_decision.nodes_visited, ab_tt.nodes_visited)

    speedup_no_ord = round(mm_time / ab_no_ord_time, 2) if ab_no_ord_time > 0 else 1.0
    speedup_ord = round(mm_time / ab_ord_time, 2) if ab_ord_time > 0 else 1.0
    speedup_tt = round(mm_time / ab_tt_time, 2) if ab_tt_time > 0 else 1.0

    # Reduction of TT caching over Alpha-Beta without cache
    tt_vs_ab_reduction = calc_reduction(ab_ord.nodes_visited, ab_tt.nodes_visited)

    return {
        "depth": safe_depth,
        "repeats": safe_repeats,
        "scores_match": score_match_no_ord and score_match_ord and score_match_tt,
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
                "cache_hits": 0,
                "cache_misses": 0,
                "hit_rate_pct": 0.0,
                "execution_time_ms": round(mm_time, 3),
                "node_reduction_pct": 0.0,
                "speedup_ratio": 1.0,
                "memory_kb": 0.0,
                "memory_is_estimate": False,
            },
            "alphabeta_no_ordering": {
                "name": "Alpha-Beta (Natural Order)",
                "column": ab_no_ord.column,
                "column_1based": (ab_no_ord.column + 1) if ab_no_ord.column is not None else None,
                "score": round(ab_no_ord.score, 2),
                "nodes_visited": ab_no_ord.nodes_visited,
                "recursive_calls": ab_no_ord.recursive_calls,
                "cutoffs": ab_no_ord.cutoffs,
                "cache_hits": 0,
                "cache_misses": 0,
                "hit_rate_pct": 0.0,
                "execution_time_ms": round(ab_no_ord_time, 3),
                "node_reduction_pct": reduction_no_ord,
                "speedup_ratio": speedup_no_ord,
                "memory_kb": 0.0,
                "memory_is_estimate": False,
            },
            "alphabeta_with_ordering": {
                "name": "Alpha-Beta (No Cache)",
                "column": ab_ord.column,
                "column_1based": (ab_ord.column + 1) if ab_ord.column is not None else None,
                "score": round(ab_ord.score, 2),
                "nodes_visited": ab_ord.nodes_visited,
                "recursive_calls": ab_ord.recursive_calls,
                "cutoffs": ab_ord.cutoffs,
                "cache_hits": 0,
                "cache_misses": 0,
                "hit_rate_pct": 0.0,
                "execution_time_ms": round(ab_ord_time, 3),
                "node_reduction_pct": reduction_ord,
                "speedup_ratio": speedup_ord,
                "memory_kb": 0.0,
                "memory_is_estimate": False,
            },
            "alphabeta_with_tt": {
                "name": "Alpha-Beta + Transposition Table",
                "column": ab_tt.column,
                "column_1based": (ab_tt.column + 1) if ab_tt.column is not None else None,
                "score": round(ab_tt.score, 2),
                "nodes_visited": ab_tt.nodes_visited,
                "recursive_calls": ab_tt.recursive_calls,
                "cutoffs": ab_tt.cutoffs,
                "cache_hits": ab_tt.cache_hits,
                "cache_misses": ab_tt.cache_misses,
                "hit_rate_pct": ab_tt.hit_rate_pct,
                "execution_time_ms": round(ab_tt_time, 3),
                "node_reduction_pct": reduction_tt,
                "speedup_ratio": speedup_tt,
                "reduction_vs_uncached_pct": tt_vs_ab_reduction,
                "tt_entries": ab_tt.tt_entries,
                "memory_kb": ab_tt.tt_memory_kb,
                "memory_is_estimate": True,
            },
        },
    }
