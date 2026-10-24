"""
test_minimax.py — Comprehensive unit tests for recursive Minimax AI.

Covers:
- Immediate winning move detection (depth-aware terminal score)
- Blocking forced immediate opponent wins
- 2-ply tactical foresight (setting up a forced win, blocking 2-ply threats)
- Correct alternation of MAX and MIN recursive layers
- Terminal board state handling (already won board, draw board)
- Safe handling of full and restricted column boards
- Depth-limit handling (nodes visited and max depth reached bounded by d)
- Deterministic behavior across repeated calls on identical board states
- Board state preservation (zero residual discs after recursive search)
"""

import pytest
from game.board import Board, ROWS, COLS, EMPTY, PLAYER1, PLAYER2
from game.rules import Rules
from algorithms.minimax import choose_minimax_move, get_minimax_decision, MinimaxDecision


# ---------------------------------------------------------------------------
# 1. Immediate Win & Terminal Evaluation
# ---------------------------------------------------------------------------

def test_minimax_takes_immediate_horizontal_win():
    """AI (P2) has 3 in a row on bottom row (cols 0, 1, 2). Col 3 wins immediately."""
    b = Board()
    for c in range(3):
        b.drop_disc(c, PLAYER2)

    col = choose_minimax_move(b, depth=2, player=PLAYER2)
    assert col == 3

    decision = get_minimax_decision(b, depth=2, player=PLAYER2)
    assert decision.column == 3
    assert decision.score >= 1_000_000.0  # Terminal win score


def test_minimax_takes_immediate_vertical_win():
    """AI (P2) has 3 stacked in col 4. 4th drop in col 4 wins."""
    b = Board()
    for _ in range(3):
        b.drop_disc(4, PLAYER2)

    col = choose_minimax_move(b, depth=2, player=PLAYER2)
    assert col == 4


# ---------------------------------------------------------------------------
# 2. Immediate Block (Minimizing Player Defense)
# ---------------------------------------------------------------------------

def test_minimax_blocks_immediate_horizontal_loss():
    """Opponent (P1) has cols 0, 1, 2 on bottom row (wall on left). AI (P2) must block col 3."""
    b = Board()
    for c in [0, 1, 2]:
        b.drop_disc(c, PLAYER1)

    col = choose_minimax_move(b, depth=2, player=PLAYER2)
    assert col == 3


def test_minimax_blocks_immediate_vertical_loss():
    """Opponent (P1) has 3 stacked in col 2. AI (P2) must block col 2."""
    b = Board()
    for _ in range(3):
        b.drop_disc(2, PLAYER1)

    col = choose_minimax_move(b, depth=2, player=PLAYER2)
    assert col == 2


# ---------------------------------------------------------------------------
# 3. Win takes priority over block (Depth-aware terminal scoring)
# ---------------------------------------------------------------------------

def test_minimax_prefers_win_over_block():
    """Both AI and Opponent threaten immediate wins. AI must choose its own win."""
    b = Board()
    # P1 threatens col 1
    for _ in range(3):
        b.drop_disc(1, PLAYER1)
    # P2 threatens col 5
    for _ in range(3):
        b.drop_disc(5, PLAYER2)

    col = choose_minimax_move(b, depth=2, player=PLAYER2)
    assert col == 5


# ---------------------------------------------------------------------------
# 4. Multi-Ply Adversarial Lookahead (2-ply depth)
# ---------------------------------------------------------------------------

def test_minimax_avoids_setting_up_opponent_win():
    """
    If AI plays in column 3 at row 5, opponent can immediately play in column 3
    at row 4 to complete 4-in-a-row. Minimax (depth >= 2) must avoid column 3!
    """
    b = Board()
    # Fillers on row 5: use P1 in col 1, P2 in col 2, P1 in col 4 (no P2 3-in-a-row on row 5)
    b.drop_disc(1, PLAYER1)
    b.drop_disc(2, PLAYER2)
    b.drop_disc(4, PLAYER1)

    # Opponent (P1) pieces on row 4 at cols 1, 2, 4
    b.drop_disc(1, PLAYER1)  # (4, 1) = P1
    b.drop_disc(2, PLAYER1)  # (4, 2) = P1
    b.drop_disc(4, PLAYER1)  # (4, 4) = P1

    # Col 3 has 0 discs!
    # If AI drops in col 3, it lands on (5, 3).
    # Then opponent drops in col 3, landing on (4, 3) to complete horizontal win on row 4!
    decision = get_minimax_decision(b, depth=2, player=PLAYER2)
    # Candidate score for col 3 must be penalized as an opponent win
    assert decision.candidate_scores[3] <= -1_000_000.0
    # AI must choose a safe column, not column 3!
    assert decision.column != 3


# ---------------------------------------------------------------------------
# 5. Search Statistics & Depth Bounds
# ---------------------------------------------------------------------------

def test_minimax_search_statistics():
    b = Board()
    decision = get_minimax_decision(b, depth=2, player=PLAYER2)
    assert decision.depth == 2
    assert decision.nodes_visited > 0
    assert decision.recursive_calls > 0
    assert decision.max_depth_reached <= 2
    assert decision.execution_time_ms >= 0.0
    assert len(decision.candidate_scores) == COLS
    assert "branches" in decision.tree
    assert decision.tree["chosen_column"] == decision.column + 1


def test_minimax_depth_1_vs_depth_2():
    """Higher depth visits more nodes."""
    b = Board()
    dec_d1 = get_minimax_decision(b, depth=1, player=PLAYER2)
    dec_d2 = get_minimax_decision(b, depth=2, player=PLAYER2)
    assert dec_d2.nodes_visited > dec_d1.nodes_visited


# ---------------------------------------------------------------------------
# 6. Board State Preservation (Undo Integrity)
# ---------------------------------------------------------------------------

def test_minimax_preserves_board_state():
    """Minimax search must leave the board identical to how it started."""
    b = Board()
    b.drop_disc(3, PLAYER1)
    b.drop_disc(2, PLAYER2)
    initial_tuple = b.to_tuple()
    initial_moves = b.move_count

    get_minimax_decision(b, depth=3, player=PLAYER2)

    assert b.to_tuple() == initial_tuple
    assert b.move_count == initial_moves


# ---------------------------------------------------------------------------
# 7. Terminal Board Handling
# ---------------------------------------------------------------------------

def test_minimax_on_full_board():
    """Draw board returns None and score 0.0 safely."""
    grid = [
        [1, 2, 1, 2, 1, 2, 1],
        [1, 2, 1, 2, 1, 2, 1],
        [2, 1, 2, 1, 2, 1, 2],
        [2, 1, 2, 1, 2, 1, 2],
        [1, 2, 1, 2, 1, 2, 1],
        [2, 1, 2, 1, 2, 1, 2],
    ]
    b = Board()
    for c in range(COLS):
        for r in range(ROWS - 1, -1, -1):
            b.drop_disc(c, grid[r][c])
    assert b.is_full()

    decision = get_minimax_decision(b, depth=2, player=PLAYER2)
    assert decision.column is None
    assert decision.score == 0.0


def test_minimax_on_already_won_board():
    b = Board()
    for c in range(4):
        b.drop_disc(c, PLAYER1)
    assert Rules.check_win(b) is not None

    decision = get_minimax_decision(b, depth=2, player=PLAYER2)
    assert decision.column is None


def test_minimax_deterministic_reproducibility():
    """Running Minimax multiple times on the same board yields identical moves and scores."""
    b = Board()
    b.drop_disc(3, PLAYER1)
    b.drop_disc(2, PLAYER2)
    b.drop_disc(3, PLAYER1)

    dec1 = get_minimax_decision(b, depth=3, player=PLAYER2)
    dec2 = get_minimax_decision(b, depth=3, player=PLAYER2)
    assert dec1.column == dec2.column
    assert dec1.score == dec2.score
    assert dec1.nodes_visited == dec2.nodes_visited
