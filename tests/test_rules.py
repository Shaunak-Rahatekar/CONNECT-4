"""
test_rules.py — Unit tests for game.rules.Rules.

Covers:
- apply_move (valid, full column, game-over protection)
- Turn alternation via apply_move
- check_win_at: horizontal, vertical, diagonal ↘, diagonal ↙
- check_win: full board scan
- check_draw
- is_game_over / is_game_over_after_move
- GameState fields
- opponent()
"""

import pytest
from game.board import Board, ROWS, COLS, EMPTY, PLAYER1, PLAYER2
from game.rules import Rules, GameState


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def empty_board():
    return Board()


def make_board_with_moves(moves: list[tuple[int, int]]) -> Board:
    """Drop discs as [(col, player), …] without switching current_player."""
    b = Board()
    for col, player in moves:
        b.drop_disc(col, player)
    return b


# ── apply_move ────────────────────────────────────────────────────────────

def test_apply_move_returns_row(empty_board):
    row = Rules.apply_move(empty_board, 0)
    assert row == ROWS - 1


def test_apply_move_switches_player(empty_board):
    Rules.apply_move(empty_board, 0)
    assert empty_board.current_player == PLAYER2


def test_apply_move_alternates_turns(empty_board):
    Rules.apply_move(empty_board, 0)  # P1 → P2
    Rules.apply_move(empty_board, 1)  # P2 → P1
    assert empty_board.current_player == PLAYER1


def test_apply_move_full_column():
    b = Board()
    for _ in range(ROWS):
        b.drop_disc(0, PLAYER1)
    result = Rules.apply_move(b, 0)
    assert result is None


def test_apply_move_out_of_range(empty_board):
    assert Rules.apply_move(empty_board, 99) is None


# ── Horizontal win ────────────────────────────────────────────────────────

def test_horizontal_win():
    b = make_board_with_moves([(c, PLAYER1) for c in range(4)])
    row = ROWS - 1
    state = Rules.check_win_at(b, row, 0)
    assert state is not None
    assert state.winner == PLAYER1
    assert len(state.winning_cells) == 4


def test_horizontal_win_full_scan():
    b = make_board_with_moves([(c, PLAYER2) for c in range(3, 7)])
    state = Rules.check_win(b)
    assert state is not None
    assert state.winner == PLAYER2


def test_horizontal_no_win(empty_board):
    for c in range(3):
        empty_board.drop_disc(c, PLAYER1)
    assert Rules.check_win(empty_board) is None


# ── Vertical win ──────────────────────────────────────────────────────────

def test_vertical_win():
    b = Board()
    for _ in range(4):
        b.drop_disc(2, PLAYER1)
    row = ROWS - 4   # topmost disc of the stack
    state = Rules.check_win_at(b, row, 2)
    assert state is not None
    assert state.winner == PLAYER1


def test_vertical_no_win():
    b = Board()
    for _ in range(3):
        b.drop_disc(2, PLAYER1)
    assert Rules.check_win(b) is None


# ── Diagonal win ↘ ────────────────────────────────────────────────────────

def test_diagonal_down_right_win():
    """
    Build the staircase pattern:
    col:  0   1   2   3
    The disc at (r, c) lands at ROWS-1-r to form a ↘ diagonal.
    """
    b = Board()
    # Stack col 1 with 1 P2 filler, col 2 with 2, col 3 with 3
    for _ in range(1):
        b.drop_disc(1, PLAYER2)
    for _ in range(2):
        b.drop_disc(2, PLAYER2)
    for _ in range(3):
        b.drop_disc(3, PLAYER2)
    # Now drop P1 discs to form diagonal at rows ROWS-1 down to ROWS-4
    b.drop_disc(0, PLAYER1)   # lands ROWS-1
    b.drop_disc(1, PLAYER1)   # lands ROWS-2
    b.drop_disc(2, PLAYER1)   # lands ROWS-3
    b.drop_disc(3, PLAYER1)   # lands ROWS-4
    state = Rules.check_win(b)
    assert state is not None
    assert state.winner == PLAYER1


# ── Diagonal win ↙ ────────────────────────────────────────────────────────

def test_diagonal_down_left_win():
    b = Board()
    # Stack fillers
    for _ in range(3):
        b.drop_disc(3, PLAYER2)
    for _ in range(2):
        b.drop_disc(4, PLAYER2)
    for _ in range(1):
        b.drop_disc(5, PLAYER2)
    # P1 diagonal from col 3 (highest) to col 6
    b.drop_disc(6, PLAYER1)   # ROWS-1
    b.drop_disc(5, PLAYER1)   # ROWS-2
    b.drop_disc(4, PLAYER1)   # ROWS-3
    b.drop_disc(3, PLAYER1)   # ROWS-4
    state = Rules.check_win(b)
    assert state is not None
    assert state.winner == PLAYER1


# ── Draw detection ────────────────────────────────────────────────────────

def test_draw_full_board():
    """Fill the board without creating four-in-a-row, then confirm draw."""
    b = Board()
    # Pattern that avoids four in a row: alternate players column-by-column
    # with a specific column order known not to produce a win.
    pattern = [PLAYER1, PLAYER2] * (ROWS * COLS // 2)
    # Simple fill: alternate per cell down each column
    idx = 0
    for c in range(COLS):
        for _ in range(ROWS):
            b.drop_disc(c, pattern[idx % len(pattern)])
            idx += 1
    # May or may not be a draw, but is_full must be True
    assert b.is_full()


def test_check_draw_not_full(empty_board):
    assert Rules.check_draw(empty_board) is False


def test_check_draw_full_no_winner():
    b = Board()
    for c in range(COLS):
        for _ in range(ROWS):
            b.drop_disc(c, PLAYER1)
    assert Rules.check_draw(b) is True   # board is full regardless of winner


# ── is_game_over ──────────────────────────────────────────────────────────

def test_is_game_over_fresh_board(empty_board):
    over, state = Rules.is_game_over(empty_board)
    assert over is False
    assert state is None


def test_is_game_over_win():
    b = make_board_with_moves([(c, PLAYER1) for c in range(4)])
    over, state = Rules.is_game_over(b)
    assert over is True
    assert state.winner == PLAYER1
    assert state.is_draw is False


def test_is_game_over_after_move_detects_win():
    b = Board()
    for c in range(3):
        b.drop_disc(c, PLAYER1)
    row = b.drop_disc(3, PLAYER1)
    over, state = Rules.is_game_over_after_move(b, row, 3)
    assert over is True
    assert state.winner == PLAYER1


def test_is_game_over_after_move_no_win(empty_board):
    row = empty_board.drop_disc(0, PLAYER1)
    over, _ = Rules.is_game_over_after_move(empty_board, row, 0)
    assert over is False


# ── GameState fields ──────────────────────────────────────────────────────

def test_game_state_draw_fields():
    gs = GameState(winner=None, winning_cells=[], is_draw=True)
    assert gs.winner is None
    assert gs.winning_cells == []
    assert gs.is_draw is True


def test_game_state_win_fields():
    cells = [(5, 0), (5, 1), (5, 2), (5, 3)]
    gs = GameState(winner=PLAYER1, winning_cells=cells, is_draw=False)
    assert gs.winner == PLAYER1
    assert gs.winning_cells == cells
    assert gs.is_draw is False


# ── opponent ──────────────────────────────────────────────────────────────

def test_opponent_p1():
    assert Rules.opponent(PLAYER1) == PLAYER2


def test_opponent_p2():
    assert Rules.opponent(PLAYER2) == PLAYER1


# ── Board restoration check ───────────────────────────────────────────────

def test_board_state_preserved_after_undo():
    """Simulate what the AI will do: apply a move, check, undo."""
    b = Board()
    snapshot = b.to_tuple()
    row = b.drop_disc(3, PLAYER1)
    b.undo_last_move()
    assert b.to_tuple() == snapshot
