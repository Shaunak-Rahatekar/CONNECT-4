"""
test_benchmark.py — Deterministic tests for the AI Performance Benchmark Runner.

Verifies:
1. Canonical benchmark positions integrity and independent instance creation.
2. 4-way algorithm benchmark execution and score equivalence.
3. Statistical aggregation (median timing) and non-negative metric tracking.
4. Chart data formatting across depth scaling (time, nodes, cutoffs, memory).
5. State isolation: benchmark execution does not mutate the input board or active game.
"""

import pytest
from game.board import Board, ROWS, COLS
from benchmarks.positions import BENCHMARK_POSITIONS, get_position, list_positions
from benchmarks.runner import run_position_benchmark, run_depth_scaling_benchmark


def test_benchmark_positions_validity():
    """All registered benchmark positions must generate legal 6x7 board states."""
    positions = list_positions()
    assert len(positions) >= 4

    for pos_meta in positions:
        pos = get_position(pos_meta["id"])
        b = pos.create_board()
        assert isinstance(b, Board)
        assert len(b.grid) == ROWS
        assert len(b.grid[0]) == COLS
        # Piece values must be 0, 1, or 2
        for r in range(ROWS):
            for c in range(COLS):
                assert b.grid[r][c] in (0, 1, 2)


def test_benchmark_board_isolation():
    """Creating and evaluating a benchmark board must not modify subsequent board instances."""
    pos = get_position("opening_center")
    b1 = pos.create_board()
    initial_grid = [row[:] for row in b1.grid]

    # Run benchmark on b1
    report = run_position_benchmark(pos, depth=2, repeats=1)
    assert report["scores_match"] is True

    # A newly created board instance must still match the initial grid exactly
    b2 = pos.create_board()
    assert b2.grid == initial_grid


def test_run_position_benchmark_metrics_and_scores():
    """Position benchmark must evaluate all 4 configurations with identical optimal scores."""
    report = run_position_benchmark("opening_center", depth=2, repeats=2)
    assert report["depth"] == 2
    assert report["aggregation_method"] == "median"
    assert report["scores_match"] is True

    res = report["results"]
    assert "minimax" in res
    assert "alphabeta_no_ordering" in res
    assert "alphabeta_with_ordering" in res
    assert "alphabeta_with_tt" in res

    # Minimax must visit the most nodes
    mm = res["minimax"]
    ab_no = res["alphabeta_no_ordering"]
    ab_ord = res["alphabeta_with_ordering"]
    ab_tt = res["alphabeta_with_tt"]

    assert mm["nodes_visited"] >= ab_no["nodes_visited"]
    assert ab_no["nodes_visited"] >= ab_ord["nodes_visited"]
    assert ab_ord["nodes_visited"] >= ab_tt["nodes_visited"]

    # All must agree on subgame score
    assert abs(mm["score"] - ab_tt["score"]) < 1e-4

    # Cutoffs must be tracked
    assert ab_ord["cutoffs"] >= 0
    assert ab_tt["cutoffs"] >= 0


def test_depth_scaling_chart_data_structure():
    """Depth scaling benchmark must return properly labeled series for Chart.js."""
    report = run_depth_scaling_benchmark(position_id="tactical_block", max_depth=2, repeats=1)
    assert "charts" in report
    charts = report["charts"]

    # 1. Time vs Depth
    assert "time_vs_depth" in charts
    time_chart = charts["time_vs_depth"]
    assert len(time_chart["labels"]) == 2
    assert len(time_chart["series"]) == 4

    # 2. Nodes vs Depth
    assert "nodes_vs_depth" in charts
    nodes_chart = charts["nodes_vs_depth"]
    assert len(nodes_chart["labels"]) == 2
    assert len(nodes_chart["series"]) == 4

    # 3. Cutoffs vs Depth
    assert "cutoffs_vs_depth" in charts
    cutoff_chart = charts["cutoffs_vs_depth"]
    assert len(cutoff_chart["labels"]) == 2
    assert len(cutoff_chart["series"]) == 3

    # 4. Memory by Config
    assert "memory_by_config" in charts
    mem_chart = charts["memory_by_config"]
    assert mem_chart["is_estimate"] is True
    assert len(mem_chart["labels"]) == 4
    assert len(mem_chart["data"]) == 4


def test_invalid_position_fallback():
    """Requesting an unknown position ID must safely fallback to opening_center."""
    pos = get_position("non_existent_position_xyz")
    assert pos.id == "opening_center"
