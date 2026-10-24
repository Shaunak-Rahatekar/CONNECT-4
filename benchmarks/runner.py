"""
runner.py — Automated benchmark execution engine for Connect-4 AI algorithms.

Design and Analysis of Algorithms (DAA Unit I, II, III & IV):
--------------------------------------------------------------
Executes strictly controlled, reproducible performance benchmarks comparing:
1. Minimax (No Pruning): Full game-tree expansion baseline O(b^d).
2. Alpha-Beta (Natural Order, No Cache): Pruning baseline under standard move traversal.
3. Alpha-Beta (Move Ordering, No Cache): Pruning enhanced by tactical and center-bias heuristics.
4. Alpha-Beta + Transposition Table: Pruning + Memoization over game DAG transpositions.

Methodology:
------------
- Controlled Inputs: Identical board states cloned independently for every algorithm run.
- Isolation: Benchmarks run entirely on detached board instances; the active game session
  is never mutated or accessed.
- Statistical Aggregation: Repeated runs (configurable 1 to 5 repeats) with median time
  reporting to eliminate operating-system scheduling jitter.
- Exact vs. Estimated Accounting: Search statistics (nodes, recursive calls, cutoffs, cache hits)
  are strictly exact counters. Memory is reported with exact dictionary overhead plus
  clearly labeled per-entry CPython object estimates.
"""

from __future__ import annotations
import statistics
import time
from typing import Any

from game.board import Board, PLAYER2
from algorithms.minimax import get_minimax_decision, MinimaxDecision
from algorithms.alphabeta import get_alphabeta_decision, AlphaBetaDecision
from algorithms.transposition_table import TranspositionTable
from benchmarks.positions import BENCHMARK_POSITIONS, get_position, BenchmarkPosition


def run_position_benchmark(
    position_or_id: str | BenchmarkPosition,
    depth: int = 3,
    repeats: int = 3,
) -> dict[str, Any]:
    """Execute all four algorithm variants on a single benchmark position.

    Parameters:
    -----------
    position_or_id : str or BenchmarkPosition
        Identifier or position descriptor to evaluate.
    depth : int
        Search depth limit (clamped 1 to 4 for responsive benchmarking).
    repeats : int
        Number of timed repetitions for statistical stability (default 3, median reported).

    Returns:
    --------
    dict[str, Any] : Detailed comparison report with timing, node counts, cutoffs,
                     cache metrics, and reduction percentages.
    """
    if isinstance(position_or_id, str):
        pos = get_position(position_or_id)
    else:
        pos = position_or_id

    safe_depth = max(1, min(depth, 4))
    safe_repeats = max(1, min(repeats, 5))
    player = pos.player_to_move

    # 1. Minimax Baseline
    mm_times: list[float] = []
    mm_decision: MinimaxDecision | None = None
    for _ in range(safe_repeats):
        b_clone = pos.create_board()
        t0 = time.perf_counter()
        mm_decision = get_minimax_decision(b_clone, depth=safe_depth, player=player)
        mm_times.append((time.perf_counter() - t0) * 1000.0)

    mm_median_time = statistics.median(mm_times)
    assert mm_decision is not None

    # 2. Alpha-Beta without move ordering (natural order, no cache)
    ab_no_ord_times: list[float] = []
    ab_no_ord_decision: AlphaBetaDecision | None = None
    for _ in range(safe_repeats):
        b_clone = pos.create_board()
        t0 = time.perf_counter()
        ab_no_ord_decision = get_alphabeta_decision(
            b_clone,
            depth=safe_depth,
            player=player,
            use_move_ordering=False,
            use_transposition_table=False,
        )
        ab_no_ord_times.append((time.perf_counter() - t0) * 1000.0)

    ab_no_ord_median_time = statistics.median(ab_no_ord_times)
    assert ab_no_ord_decision is not None

    # 3. Alpha-Beta with move ordering (no cache)
    ab_ord_times: list[float] = []
    ab_ord_decision: AlphaBetaDecision | None = None
    for _ in range(safe_repeats):
        b_clone = pos.create_board()
        t0 = time.perf_counter()
        ab_ord_decision = get_alphabeta_decision(
            b_clone,
            depth=safe_depth,
            player=player,
            use_move_ordering=True,
            use_transposition_table=False,
        )
        ab_ord_times.append((time.perf_counter() - t0) * 1000.0)

    ab_ord_median_time = statistics.median(ab_ord_times)
    assert ab_ord_decision is not None

    # 4. Alpha-Beta with move ordering + Transposition Table (with cache)
    ab_tt_times: list[float] = []
    ab_tt_decision: AlphaBetaDecision | None = None
    for _ in range(safe_repeats):
        b_clone = pos.create_board()
        fresh_tt = TranspositionTable(max_entries=100_000)
        t0 = time.perf_counter()
        ab_tt_decision = get_alphabeta_decision(
            b_clone,
            depth=safe_depth,
            player=player,
            use_move_ordering=True,
            use_transposition_table=True,
            transposition_table=fresh_tt,
        )
        ab_tt_times.append((time.perf_counter() - t0) * 1000.0)

    ab_tt_median_time = statistics.median(ab_tt_times)
    assert ab_tt_decision is not None

    # Score equivalence verification across all 4 configurations
    scores_match = (
        abs(mm_decision.score - ab_no_ord_decision.score) < 1e-4 and
        abs(mm_decision.score - ab_ord_decision.score) < 1e-4 and
        abs(mm_decision.score - ab_tt_decision.score) < 1e-4
    )

    def calc_reduction(base_nodes: int, test_nodes: int) -> float:
        if base_nodes <= 0:
            return 0.0
        return round(((base_nodes - test_nodes) / base_nodes) * 100.0, 1)

    red_no_ord = calc_reduction(mm_decision.nodes_visited, ab_no_ord_decision.nodes_visited)
    red_ord = calc_reduction(mm_decision.nodes_visited, ab_ord_decision.nodes_visited)
    red_tt = calc_reduction(mm_decision.nodes_visited, ab_tt_decision.nodes_visited)

    speedup_no_ord = round(mm_median_time / ab_no_ord_median_time, 2) if ab_no_ord_median_time > 0 else 1.0
    speedup_ord = round(mm_median_time / ab_ord_median_time, 2) if ab_ord_median_time > 0 else 1.0
    speedup_tt = round(mm_median_time / ab_tt_median_time, 2) if ab_tt_median_time > 0 else 1.0

    return {
        "position": {
            "id": pos.id,
            "name": pos.name,
            "description": pos.description,
            "phase": pos.phase,
            "player_to_move": player,
        },
        "depth": safe_depth,
        "repeats": safe_repeats,
        "aggregation_method": "median",
        "scores_match": scores_match,
        "optimal_score": round(mm_decision.score, 2),
        "results": {
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
                "execution_time_ms": round(mm_median_time, 3),
                "node_reduction_pct": 0.0,
                "speedup_ratio": 1.0,
                "memory_kb": 0.0,
                "memory_is_estimate": False,
            },
            "alphabeta_no_ordering": {
                "name": "Alpha-Beta (Natural Order)",
                "column": ab_no_ord_decision.column,
                "column_1based": (ab_no_ord_decision.column + 1) if ab_no_ord_decision.column is not None else None,
                "score": round(ab_no_ord_decision.score, 2),
                "nodes_visited": ab_no_ord_decision.nodes_visited,
                "recursive_calls": ab_no_ord_decision.recursive_calls,
                "cutoffs": ab_no_ord_decision.cutoffs,
                "cache_hits": 0,
                "cache_misses": 0,
                "hit_rate_pct": 0.0,
                "execution_time_ms": round(ab_no_ord_median_time, 3),
                "node_reduction_pct": red_no_ord,
                "speedup_ratio": speedup_no_ord,
                "memory_kb": 0.0,
                "memory_is_estimate": False,
            },
            "alphabeta_with_ordering": {
                "name": "Alpha-Beta (No Cache)",
                "column": ab_ord_decision.column,
                "column_1based": (ab_ord_decision.column + 1) if ab_ord_decision.column is not None else None,
                "score": round(ab_ord_decision.score, 2),
                "nodes_visited": ab_ord_decision.nodes_visited,
                "recursive_calls": ab_ord_decision.recursive_calls,
                "cutoffs": ab_ord_decision.cutoffs,
                "cache_hits": 0,
                "cache_misses": 0,
                "hit_rate_pct": 0.0,
                "execution_time_ms": round(ab_ord_median_time, 3),
                "node_reduction_pct": red_ord,
                "speedup_ratio": speedup_ord,
                "memory_kb": 0.0,
                "memory_is_estimate": False,
            },
            "alphabeta_with_tt": {
                "name": "Alpha-Beta + Transposition Table",
                "column": ab_tt_decision.column,
                "column_1based": (ab_tt_decision.column + 1) if ab_tt_decision.column is not None else None,
                "score": round(ab_tt_decision.score, 2),
                "nodes_visited": ab_tt_decision.nodes_visited,
                "recursive_calls": ab_tt_decision.recursive_calls,
                "cutoffs": ab_tt_decision.cutoffs,
                "cache_hits": ab_tt_decision.cache_hits,
                "cache_misses": ab_tt_decision.cache_misses,
                "hit_rate_pct": ab_tt_decision.hit_rate_pct,
                "execution_time_ms": round(ab_tt_median_time, 3),
                "node_reduction_pct": red_tt,
                "speedup_ratio": speedup_tt,
                "reduction_vs_uncached_pct": calc_reduction(ab_ord_decision.nodes_visited, ab_tt_decision.nodes_visited),
                "tt_entries": ab_tt_decision.tt_entries,
                "memory_kb": ab_tt_decision.tt_memory_kb,
                "memory_is_estimate": True,
            },
        },
    }


def run_depth_scaling_benchmark(
    position_id: str | BenchmarkPosition = "opening_center",
    max_depth: int = 4,
    repeats: int = 2,
) -> dict[str, Any]:
    """Evaluate performance across depth range 1 to max_depth.

    Formats chart-ready datasets for:
    - Time vs. Depth (ms)
    - Nodes Visited vs. Depth
    - Cache Hit Rate vs. Depth (%)
    - Memory Consumption vs. Config (KB)
    """
    safe_max_depth = max(1, min(max_depth, 4))
    if isinstance(position_id, str):
        pos = get_position(position_id)
    else:
        pos = position_id

    depth_labels = [f"Depth {d}" for d in range(1, safe_max_depth + 1)]

    # Time series (ms)
    time_series: dict[str, list[float]] = {
        "minimax": [],
        "alphabeta_no_ordering": [],
        "alphabeta_with_ordering": [],
        "alphabeta_with_tt": [],
    }

    # Node count series
    node_series: dict[str, list[int]] = {
        "minimax": [],
        "alphabeta_no_ordering": [],
        "alphabeta_with_ordering": [],
        "alphabeta_with_tt": [],
    }

    # Cutoffs series
    cutoff_series: dict[str, list[int]] = {
        "alphabeta_no_ordering": [],
        "alphabeta_with_ordering": [],
        "alphabeta_with_tt": [],
    }

    # TT metrics series
    tt_hit_rate_series: list[float] = []
    tt_memory_series: list[float] = []

    for d in range(1, safe_max_depth + 1):
        report = run_position_benchmark(pos, depth=d, repeats=repeats)
        res = report["results"]

        for alg_key in ("minimax", "alphabeta_no_ordering", "alphabeta_with_ordering", "alphabeta_with_tt"):
            time_series[alg_key].append(res[alg_key]["execution_time_ms"])
            node_series[alg_key].append(res[alg_key]["nodes_visited"])

        for ab_key in ("alphabeta_no_ordering", "alphabeta_with_ordering", "alphabeta_with_tt"):
            cutoff_series[ab_key].append(res[ab_key]["cutoffs"])

        tt_hit_rate_series.append(res["alphabeta_with_tt"]["hit_rate_pct"])
        tt_memory_series.append(res["alphabeta_with_tt"]["memory_kb"])

    # Create friendly aliases for frontend consumption
    time_series["alphabeta_natural"] = time_series["alphabeta_no_ordering"]
    time_series["alphabeta_ordered"] = time_series["alphabeta_with_ordering"]
    time_series["alphabeta_tt"] = time_series["alphabeta_with_tt"]

    node_series["alphabeta_natural"] = node_series["alphabeta_no_ordering"]
    node_series["alphabeta_ordered"] = node_series["alphabeta_with_ordering"]
    node_series["alphabeta_tt"] = node_series["alphabeta_with_tt"]

    cutoff_series["alphabeta_natural"] = cutoff_series["alphabeta_no_ordering"]
    cutoff_series["alphabeta_ordered"] = cutoff_series["alphabeta_with_ordering"]
    cutoff_series["alphabeta_tt"] = cutoff_series["alphabeta_with_tt"]

    memory_kb_dict = {
        "minimax": [0.0] * safe_max_depth,
        "alphabeta_natural": [0.0] * safe_max_depth,
        "alphabeta_ordered": [0.0] * safe_max_depth,
        "alphabeta_tt": tt_memory_series,
        "alphabeta_with_tt": tt_memory_series,
    }

    return {
        "position": {
            "id": pos.id,
            "name": pos.name,
            "phase": pos.phase,
        },
        "max_depth": safe_max_depth,
        "repeats": repeats,
        "depths": list(range(1, safe_max_depth + 1)),
        "depth_labels": depth_labels,
        "time_ms": time_series,
        "nodes": node_series,
        "cutoffs": cutoff_series,
        "memory_kb": memory_kb_dict,
        "charts": {
            "time_vs_depth": {
                "title": "Execution Time vs. Search Depth (ms)",
                "x_label": "Search Depth (Ply)",
                "y_label": "Execution Time (ms)",
                "labels": depth_labels,
                "series": [
                    {"label": "Minimax (No Pruning)", "data": time_series["minimax"], "color": "#ef4444"},
                    {"label": "Alpha-Beta (Natural Order)", "data": time_series["alphabeta_no_ordering"], "color": "#f59e0b"},
                    {"label": "Alpha-Beta (No Cache)", "data": time_series["alphabeta_with_ordering"], "color": "#38bdf8"},
                    {"label": "Alpha-Beta + Transposition Table", "data": time_series["alphabeta_with_tt"], "color": "#34d399"},
                ],
            },
            "nodes_vs_depth": {
                "title": "Nodes Visited vs. Search Depth",
                "x_label": "Search Depth (Ply)",
                "y_label": "Total Nodes Evaluated",
                "labels": depth_labels,
                "series": [
                    {"label": "Minimax (No Pruning)", "data": node_series["minimax"], "color": "#ef4444"},
                    {"label": "Alpha-Beta (Natural Order)", "data": node_series["alphabeta_no_ordering"], "color": "#f59e0b"},
                    {"label": "Alpha-Beta (No Cache)", "data": node_series["alphabeta_with_ordering"], "color": "#38bdf8"},
                    {"label": "Alpha-Beta + Transposition Table", "data": node_series["alphabeta_with_tt"], "color": "#34d399"},
                ],
            },
            "cutoffs_vs_depth": {
                "title": "Branch Cutoffs vs. Search Depth",
                "x_label": "Search Depth (Ply)",
                "y_label": "Cutoffs Triggered",
                "labels": depth_labels,
                "series": [
                    {"label": "Alpha-Beta (Natural Order)", "data": cutoff_series["alphabeta_no_ordering"], "color": "#f59e0b"},
                    {"label": "Alpha-Beta (No Cache)", "data": cutoff_series["alphabeta_with_ordering"], "color": "#38bdf8"},
                    {"label": "Alpha-Beta + Transposition Table", "data": cutoff_series["alphabeta_with_tt"], "color": "#34d399"},
                ],
            },
            "memory_by_config": {
                "title": f"Estimated Memory Consumption at Depth {safe_max_depth} (KB)",
                "x_label": "Algorithm Configuration",
                "y_label": "Memory (KB, estimated)",
                "labels": ["Minimax", "Alpha-Beta (Natural)", "Alpha-Beta (No Cache)", "Alpha-Beta + TT"],
                "data": [
                    0.0,
                    0.0,
                    0.0,
                    tt_memory_series[-1] if tt_memory_series else 0.0,
                ],
                "color": "#a855f7",
                "is_estimate": True,
            },
        },
    }
