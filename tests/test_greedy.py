"""
test_greedy.py — Unit tests for Greedy Connect-4 AI and heuristic evaluation.

Covers:
- Immediate winning move detection (Priority 1) across horizontal, vertical, diagonal
- Immediate opponent winning move blocking (Priority 2)
- Preference for win over block when both are present simultaneously
- Center column preference when candidate scores are equivalent
- Legal moves selection (never chooses a full or out-of-range column)
- Terminal board handling (game already won or full board returns None)
- Deterministic behavior across repeated calls
- Heuristic scoring accuracy for open lines and center presence
"""

import pytest
from game.board import Board, ROWS, COLS, EMPTY, PLAYER1, PLAYER2
from game.rules import Rules
from algorithms.evaluation import evaluate_board, HeuristicWeights
from algorithms.greedy import choose_greedy_move, get_greedy_decision, GreedyDecision


# ---------------------------------------------------------------------------
# 1. Immediate Win (Priority 1)
# ---------------------------------------------------------------------------

def test_greedy_takes_immediate_horizontal_win():
    """AI (P2) has 3 in a row horizontally on row 5: cols 0, 1, 2. Col 3 wins."""
    b = Board()
    for c in range(3):
        b.drop_disc(c, PLAYER2)
    # Col 3 is open
    col = choose_greedy_move(b, player=PLAYER2)
    assert col == 3

    decision = get_greedy_decision(b, player=PLAYER2)
    assert decision.column == 3
    assert "Winning move" in decision.reason


def test_greedy_takes_immediate_vertical_win():
    """AI (P2) has 3 stacked in col 4. 4th drop in col 4 wins."""
    b = Board()
    for _ in range(3):
        b.drop_disc(4, PLAYER2)
    col = choose_greedy_move(b, player=PLAYER2)
    assert col == 4


def test_greedy_takes_immediate_diagonal_win():
    """
    AI (P2) has diagonal ↘ setup:
    (2, 0), (3, 1), (4, 2) occupied by P2.
    Col 3 currently has 0 discs, so disc in Col 3 lands at row 5 (not row 5-3=2).
    Let's set up col 3 with 2 filler discs so the next drop in col 3 lands at row 5 - 2 = row 3:
    Winning cell is (5, 3) if (2, 0), (3, 1), (4, 2), (5, 3).
    (2, 0) needs 3 fillers in col 0.
    (3, 1) needs 2 fillers in col 1.
    (4, 2) needs 1 filler in col 2.
    (5, 3) needs 0 fillers in col 3.
    """
    b = Board()
    # Fillers in col 0 (3 fillers)
    for _ in range(3):
        b.drop_disc(0, PLAYER1)
    b.drop_disc(0, PLAYER2)  # row 2

    # Fillers in col 1 (2 fillers)
    for _ in range(2):
        b.drop_disc(1, PLAYER1)
    b.drop_disc(1, PLAYER2)  # row 3

    # Fillers in col 2 (1 filler)
    b.drop_disc(2, PLAYER1)
    b.drop_disc(2, PLAYER2)  # row 4

    # Now drop in col 3 lands at row 5, completing (2,0), (3,1), (4,2), (5,3)
    col = choose_greedy_move(b, player=PLAYER2)
    assert col == 3


# ---------------------------------------------------------------------------
# 2. Immediate Block (Priority 2)
# ---------------------------------------------------------------------------

def test_greedy_blocks_immediate_horizontal_win():
    """Opponent (P1) has cols 1, 2, 3 on bottom row. AI must block col 0 or 4."""
    b = Board()
    for c in [1, 2, 3]:
        b.drop_disc(c, PLAYER1)
    # AI (P2) must block col 0 or 4. Col 4 is preferred over col 0 due to center distance
    col = choose_greedy_move(b, player=PLAYER2)
    assert col in (0, 4)
    decision = get_greedy_decision(b, player=PLAYER2)
    assert "Defensive block" in decision.reason


def test_greedy_blocks_immediate_vertical_win():
    """Opponent (P1) has 3 stacked in col 1. AI must block col 1."""
    b = Board()
    for _ in range(3):
        b.drop_disc(1, PLAYER1)
    col = choose_greedy_move(b, player=PLAYER2)
    assert col == 1
    decision = get_greedy_decision(b, player=PLAYER2)
    assert decision.column == 1
    assert "Defensive block" in decision.reason


# ---------------------------------------------------------------------------
# 3. Win takes priority over block (Priority 1 > Priority 2)
# ---------------------------------------------------------------------------

def test_greedy_prefers_win_over_block():
    """Both AI and Opponent have immediate winning opportunities. AI must take win."""
    b = Board()
    # Opponent (P1) threatens win at col 1 (has 3 stacked)
    for _ in range(3):
        b.drop_disc(1, PLAYER1)

    # AI (P2) threatens win at col 5 (has 3 stacked)
    for _ in range(3):
        b.drop_disc(5, PLAYER2)

    # AI turn: taking col 5 wins the game immediately!
    col = choose_greedy_move(b, player=PLAYER2)
    assert col == 5
    decision = get_greedy_decision(b, player=PLAYER2)
    assert decision.column == 5
    assert "Winning move" in decision.reason


# ---------------------------------------------------------------------------
# 4. Center Preference & Deterministic Tie-Breaking
# ---------------------------------------------------------------------------

def test_greedy_prefers_center_on_empty_board():
    """On an empty board, all columns evaluate equally. AI must choose center (col 3)."""
    b = Board()
    col = choose_greedy_move(b, player=PLAYER2)
    assert col == 3


def test_greedy_deterministic_tie_breaking():
    """Two symmetric candidate columns must break ties deterministically."""
    b = Board()
    # Center column is full
    for _ in range(ROWS):
        b.drop_disc(3, (PLAYER1 if _ % 2 == 0 else PLAYER2))

    # Columns 2 and 4 are symmetric distance 1 from center
    # Deterministic order [3, 2, 4, 1, 5, 0, 6] prefers col 2
    dec1 = get_greedy_decision(b, player=PLAYER2)
    dec2 = get_greedy_decision(b, player=PLAYER2)
    assert dec1.column == dec2.column
    assert dec1.column == 2


# ---------------------------------------------------------------------------
# 5. Legal Move Selection & Full Columns
# ---------------------------------------------------------------------------

def test_greedy_never_picks_full_column():
    """When center column is full, AI picks an available open column."""
    b = Board()
    for i in range(ROWS):
        b.drop_disc(3, (i % 2) + 1)
    assert not b.is_valid_column(3)
    assert Rules.check_win(b) is None
    col = choose_greedy_move(b, player=PLAYER2)
    assert col != 3
    assert col in b.get_valid_columns()


def test_greedy_returns_none_on_full_board():
    """On a completely full board, AI safely returns None."""
    # Verified draw pattern
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

    decision = get_greedy_decision(b, player=PLAYER2)
    assert decision.column is None
    assert choose_greedy_move(b, player=PLAYER2) is None


def test_greedy_returns_none_if_game_already_won():
    """If a winner already exists on the board, AI safely returns None."""
    b = Board()
    for c in range(4):
        b.drop_disc(c, PLAYER1)
    assert Rules.check_win(b) is not None

    decision = get_greedy_decision(b, player=PLAYER2)
    assert decision.column is None
    assert "already over" in decision.reason


# ---------------------------------------------------------------------------
# 6. Heuristic Evaluation Unit Tests
# ---------------------------------------------------------------------------

def test_heuristic_center_bonus():
    b = Board()
    b.drop_disc(3, PLAYER2)  # center col disc
    score = evaluate_board(b, player=PLAYER2)
    # Empty board score was 0; center disc gives +center weight bonus + window contributions
    assert score > 0


def test_heuristic_higher_for_three_in_a_row():
    b_two = Board()
    b_two.drop_disc(0, PLAYER2)
    b_two.drop_disc(1, PLAYER2)

    b_three = Board()
    b_three.drop_disc(0, PLAYER2)
    b_three.drop_disc(1, PLAYER2)
    b_three.drop_disc(2, PLAYER2)

    score_two = evaluate_board(b_two, player=PLAYER2)
    score_three = evaluate_board(b_three, player=PLAYER2)
    assert score_three > score_two


def test_decision_to_dict_format():
    decision = GreedyDecision(
        column=3,
        score=45.0,
        reason="Test reason",
        candidate_scores={0: 1.0, 3: 45.0},
        execution_time_ms=0.5,
    )
    d = decision.to_dict()
    assert d["strategy"] == "greedy"
    assert d["column"] == 3
    assert d["score"] == 45.0
    assert "3" in d["candidate_scores"]
    assert d["execution_time_ms"] == 0.5
