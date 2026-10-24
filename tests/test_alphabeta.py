"""
test_alphabeta.py — Deterministic correctness and performance tests for Alpha-Beta Pruning.

Covers:
- Immediate winning move detection (horizontal & vertical).
- Immediate loss blocking (horizontal & vertical).
- Preference for win over block.
- Equivalence of evaluation score between Minimax and Alpha-Beta.
- Verification that Alpha-Beta Pruning records cutoffs and reduces nodes visited.
- Verification that move ordering preserves the Minimax score.
- Verification that the original board is perfectly preserved after search.
- Edge cases: full board, already-won board.
- Integration test for compare_algorithms framework.
"""

import pytest
from game.board import Board, ROWS, COLS, PLAYER1, PLAYER2
from algorithms.minimax import get_minimax_decision
from algorithms.alphabeta import (
    get_alphabeta_decision,
    choose_alphabeta_move,
    TERMINAL_WIN_BASE,
)
from algorithms.comparison import compare_algorithms


def test_alphabeta_takes_immediate_horizontal_win():
    """Alpha-Beta AI must immediately take an unblocked 4-in-a-row horizontal win."""
    board = Board()
    # P2 (Yellow) has 3 in a row on bottom row (row 5): cols 1, 2, 3
    # P1 has discs at cols 0, 5, 6
    board.drop_disc(1, PLAYER2)
    board.drop_disc(2, PLAYER2)
    board.drop_disc(3, PLAYER2)
    board.drop_disc(0, PLAYER1)
    board.drop_disc(5, PLAYER1)
    board.drop_disc(6, PLAYER1)

    decision = get_alphabeta_decision(board, depth=2, player=PLAYER2)
    # Col 4 completes the horizontal connection (row 5, cols 1, 2, 3, 4)
    assert decision.column == 4
    assert decision.score >= TERMINAL_WIN_BASE


def test_alphabeta_takes_immediate_vertical_win():
    """Alpha-Beta AI must immediately drop the 4th disc in a vertical column."""
    board = Board()
    # P2 has 3 discs stacked in column 3
    board.drop_disc(3, PLAYER2)
    board.drop_disc(3, PLAYER2)
    board.drop_disc(3, PLAYER2)
    # P1 has discs elsewhere
    board.drop_disc(0, PLAYER1)
    board.drop_disc(1, PLAYER1)
    board.drop_disc(2, PLAYER1)

    decision = get_alphabeta_decision(board, depth=2, player=PLAYER2)
    assert decision.column == 3
    assert decision.score >= TERMINAL_WIN_BASE


def test_alphabeta_blocks_immediate_horizontal_loss():
    """Alpha-Beta AI must block opponent's 3-in-a-row threat to prevent an immediate loss."""
    board = Board()
    # P1 (Red) has discs at cols 0, 1, 2 on bottom row (row 5)
    # Column 3 is open and would give P1 an immediate win
    board.drop_disc(0, PLAYER1)
    board.drop_disc(1, PLAYER1)
    board.drop_disc(2, PLAYER1)
    # P2 has filler discs at cols 5, 6
    board.drop_disc(5, PLAYER2)
    board.drop_disc(6, PLAYER2)

    decision = get_alphabeta_decision(board, depth=3, player=PLAYER2)
    assert decision.column == 3


def test_alphabeta_blocks_immediate_vertical_loss():
    """Alpha-Beta AI must drop a disc directly on top of opponent's 3-disc vertical stack."""
    board = Board()
    # P1 has 3 stacked discs in column 2
    board.drop_disc(2, PLAYER1)
    board.drop_disc(2, PLAYER1)
    board.drop_disc(2, PLAYER1)
    # P2 has discs elsewhere
    board.drop_disc(0, PLAYER2)
    board.drop_disc(1, PLAYER2)

    decision = get_alphabeta_decision(board, depth=2, player=PLAYER2)
    assert decision.column == 2


def test_alphabeta_prefers_win_over_block():
    """When both an immediate win and a required block exist, Alpha-Beta must choose to win."""
    board = Board()
    # P2 can win in column 1
    board.drop_disc(1, PLAYER2)
    board.drop_disc(1, PLAYER2)
    board.drop_disc(1, PLAYER2)

    # P1 could win in column 4
    board.drop_disc(4, PLAYER1)
    board.drop_disc(4, PLAYER1)
    board.drop_disc(4, PLAYER1)

    decision = get_alphabeta_decision(board, depth=2, player=PLAYER2)
    assert decision.column == 1
    assert decision.score >= TERMINAL_WIN_BASE


def test_alphabeta_matches_minimax_score_on_empty_board():
    """Alpha-Beta Pruning must yield the identical minimax score as unpruned Minimax."""
    board = Board()
    for depth in (1, 2, 3):
        mm = get_minimax_decision(board, depth=depth, player=PLAYER2)
        ab_no_ord = get_alphabeta_decision(board, depth=depth, player=PLAYER2, use_move_ordering=False)
        ab_ord = get_alphabeta_decision(board, depth=depth, player=PLAYER2, use_move_ordering=True)

        assert abs(mm.score - ab_no_ord.score) < 1e-4, f"Score mismatch at depth {depth} (no ord)"
        assert abs(mm.score - ab_ord.score) < 1e-4, f"Score mismatch at depth {depth} (ord)"


def test_alphabeta_matches_minimax_score_on_tactical_board():
    """On a non-empty mid-game board, Minimax and Alpha-Beta must evaluate identical optimal scores."""
    board = Board()
    # Drop some introductory moves
    board.drop_disc(3, PLAYER1)
    board.drop_disc(3, PLAYER2)
    board.drop_disc(2, PLAYER1)
    board.drop_disc(4, PLAYER2)
    board.drop_disc(2, PLAYER1)

    mm = get_minimax_decision(board, depth=3, player=PLAYER2)
    ab = get_alphabeta_decision(board, depth=3, player=PLAYER2, use_move_ordering=True)

    assert abs(mm.score - ab.score) < 1e-4
    assert ab.column in board.get_valid_columns()


def test_alphabeta_records_cutoffs_and_reduces_nodes():
    """Alpha-Beta must prune dominated subtrees, recording cutoffs and fewer nodes than Minimax."""
    board = Board()
    # Play opening center moves
    board.drop_disc(3, PLAYER1)
    board.drop_disc(3, PLAYER2)

    depth = 3
    mm = get_minimax_decision(board, depth=depth, player=PLAYER2)
    ab = get_alphabeta_decision(board, depth=depth, player=PLAYER2, use_move_ordering=True)

    # Pruning must record cutoffs and visit strictly fewer nodes than Minimax
    assert ab.cutoffs > 0, f"Expected cutoffs > 0, got {ab.cutoffs}"
    assert ab.nodes_visited < mm.nodes_visited, (
        f"Alpha-Beta nodes ({ab.nodes_visited}) should be strictly less than Minimax ({mm.nodes_visited})"
    )


def test_move_ordering_preserves_score_and_affects_search():
    """Move ordering must preserve exact minimax value while changing search performance."""
    board = Board()
    board.drop_disc(3, PLAYER1)
    board.drop_disc(2, PLAYER2)
    board.drop_disc(3, PLAYER1)

    depth = 3
    ab_no_ord = get_alphabeta_decision(board, depth=depth, player=PLAYER2, use_move_ordering=False)
    ab_ord = get_alphabeta_decision(board, depth=depth, player=PLAYER2, use_move_ordering=True)

    # Scores must be identical
    assert abs(ab_no_ord.score - ab_ord.score) < 1e-4
    # Cutoffs must occur
    assert ab_ord.cutoffs > 0


def test_alphabeta_preserves_board_state():
    """The game board must be restored to its exact original state after search."""
    board = Board()
    board.drop_disc(3, PLAYER1)
    board.drop_disc(2, PLAYER2)
    initial_tuple = board.to_tuple()
    initial_move_count = board.move_count

    _ = get_alphabeta_decision(board, depth=3, player=PLAYER2, use_move_ordering=True)

    assert board.to_tuple() == initial_tuple
    assert board.move_count == initial_move_count


def test_alphabeta_on_full_board():
    """Alpha-Beta must gracefully return None when the board is completely full."""
    board = Board()
    # Fill board without 4-in-a-row
    p = [PLAYER1, PLAYER2]
    for c in range(COLS):
        for r in range(ROWS):
            board.drop_disc(c, p[(r + (c % 2)) % 2])

    assert board.is_full()
    decision = get_alphabeta_decision(board, depth=3, player=PLAYER2)
    assert decision.column is None
    assert decision.score == 0.0


def test_alphabeta_on_already_won_board():
    """Alpha-Beta must return None when the board is already in a terminal won state."""
    board = Board()
    board.drop_disc(0, PLAYER1)
    board.drop_disc(1, PLAYER1)
    board.drop_disc(2, PLAYER1)
    board.drop_disc(3, PLAYER1)  # P1 has won

    decision = get_alphabeta_decision(board, depth=3, player=PLAYER2)
    assert decision.column is None
    assert decision.nodes_visited == 0


def test_compare_algorithms_framework():
    """Test that compare_algorithms returns expected structure with matching scores."""
    board = Board()
    board.drop_disc(3, PLAYER1)

    result = compare_algorithms(board, depth=2, player=PLAYER2, repeats=1)
    assert result["scores_match"] is True
    assert "minimax" in result["algorithms"]
    assert "alphabeta_no_ordering" in result["algorithms"]
    assert "alphabeta_with_ordering" in result["algorithms"]

    mm_info = result["algorithms"]["minimax"]
    ab_info = result["algorithms"]["alphabeta_with_ordering"]

    assert mm_info["score"] == ab_info["score"]
    assert ab_info["nodes_visited"] <= mm_info["nodes_visited"]
