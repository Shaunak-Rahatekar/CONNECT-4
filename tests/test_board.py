"""
test_board.py — Unit tests for game.board.Board.

Covers:
- Board initialisation (dimensions, default values)
- is_valid_column edge cases
- get_next_open_row and gravity
- drop_disc (normal, full column, out-of-range)
- undo_last_move
- switch_player
- is_full
- reset
- copy (deep independence)
- to_tuple / hash
- __eq__
"""

import pytest
from game.board import Board, ROWS, COLS, EMPTY, PLAYER1, PLAYER2


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def empty_board() -> Board:
    return Board()


@pytest.fixture
def partial_board() -> Board:
    """Board with a few discs in column 3."""
    b = Board()
    b.drop_disc(3, PLAYER1)
    b.drop_disc(3, PLAYER2)
    b.drop_disc(3, PLAYER1)
    return b


# ── Initialisation ────────────────────────────────────────────────────────

def test_board_dimensions(empty_board):
    assert len(empty_board.grid) == ROWS
    for row in empty_board.grid:
        assert len(row) == COLS


def test_board_all_empty(empty_board):
    for r in range(ROWS):
        for c in range(COLS):
            assert empty_board.grid[r][c] == EMPTY


def test_initial_player(empty_board):
    assert empty_board.current_player == PLAYER1


def test_initial_move_count(empty_board):
    assert empty_board.move_count == 0


# ── is_valid_column ───────────────────────────────────────────────────────

def test_valid_column_range(empty_board):
    for c in range(COLS):
        assert empty_board.is_valid_column(c) is True


def test_invalid_column_negative(empty_board):
    assert empty_board.is_valid_column(-1) is False


def test_invalid_column_too_large(empty_board):
    assert empty_board.is_valid_column(COLS) is False


def test_full_column_invalid():
    b = Board()
    for _ in range(ROWS):
        b.drop_disc(0, PLAYER1)
    assert b.is_valid_column(0) is False


# ── get_next_open_row ─────────────────────────────────────────────────────

def test_open_row_empty_column(empty_board):
    assert empty_board.get_next_open_row(0) == ROWS - 1


def test_open_row_after_drops(partial_board):
    # 3 discs in col 3 → next row = ROWS - 4
    assert partial_board.get_next_open_row(3) == ROWS - 4


def test_open_row_full_column():
    b = Board()
    for _ in range(ROWS):
        b.drop_disc(0, PLAYER1)
    assert b.get_next_open_row(0) is None


# ── drop_disc ─────────────────────────────────────────────────────────────

def test_drop_disc_returns_bottom_row(empty_board):
    row = empty_board.drop_disc(0, PLAYER1)
    assert row == ROWS - 1


def test_drop_disc_stacks_gravity():
    b = Board()
    r1 = b.drop_disc(0, PLAYER1)
    r2 = b.drop_disc(0, PLAYER2)
    assert r1 == ROWS - 1
    assert r2 == ROWS - 2


def test_drop_disc_records_player():
    b = Board()
    row = b.drop_disc(2, PLAYER2)
    assert b.grid[row][2] == PLAYER2


def test_drop_disc_increments_move_count(empty_board):
    empty_board.drop_disc(0, PLAYER1)
    assert empty_board.move_count == 1


def test_drop_disc_full_column_returns_none():
    b = Board()
    for _ in range(ROWS):
        b.drop_disc(0, PLAYER1)
    assert b.drop_disc(0, PLAYER1) is None


def test_drop_disc_out_of_range(empty_board):
    assert empty_board.drop_disc(99, PLAYER1) is None


# ── undo_last_move ────────────────────────────────────────────────────────

def test_undo_restores_cell():
    b = Board()
    row = b.drop_disc(1, PLAYER1)
    b.undo_last_move()
    assert b.grid[row][1] == EMPTY


def test_undo_decrements_move_count():
    b = Board()
    b.drop_disc(1, PLAYER1)
    b.undo_last_move()
    assert b.move_count == 0


def test_undo_returns_col_row():
    b = Board()
    row = b.drop_disc(4, PLAYER1)
    result = b.undo_last_move()
    assert result == (4, row)


def test_undo_empty_board(empty_board):
    assert empty_board.undo_last_move() is None


# ── switch_player ─────────────────────────────────────────────────────────

def test_switch_player_p1_to_p2(empty_board):
    empty_board.switch_player()
    assert empty_board.current_player == PLAYER2


def test_switch_player_p2_to_p1(empty_board):
    empty_board.current_player = PLAYER2
    empty_board.switch_player()
    assert empty_board.current_player == PLAYER1


# ── get_valid_columns ─────────────────────────────────────────────────────

def test_get_valid_columns_full_board():
    b = Board()
    # fill all columns
    for c in range(COLS):
        for _ in range(ROWS):
            b.drop_disc(c, PLAYER1)
    assert b.get_valid_columns() == []


def test_get_valid_columns_partial():
    b = Board()
    for _ in range(ROWS):
        b.drop_disc(0, PLAYER1)   # fill col 0 only
    valid = b.get_valid_columns()
    assert 0 not in valid
    assert all(c in valid for c in range(1, COLS))


# ── is_full ───────────────────────────────────────────────────────────────

def test_is_full_empty(empty_board):
    assert empty_board.is_full() is False


def test_is_full_when_filled():
    b = Board()
    for c in range(COLS):
        for _ in range(ROWS):
            b.drop_disc(c, PLAYER1)
    assert b.is_full() is True


# ── reset ─────────────────────────────────────────────────────────────────

def test_reset_clears_grid(partial_board):
    partial_board.reset()
    for r in range(ROWS):
        for c in range(COLS):
            assert partial_board.grid[r][c] == EMPTY


def test_reset_clears_move_count(partial_board):
    partial_board.reset()
    assert partial_board.move_count == 0


def test_reset_restores_player1(partial_board):
    partial_board.current_player = PLAYER2
    partial_board.reset()
    assert partial_board.current_player == PLAYER1


def test_reset_clears_history(partial_board):
    partial_board.reset()
    assert partial_board._history == []


# ── copy ──────────────────────────────────────────────────────────────────

def test_copy_is_equal(partial_board):
    clone = partial_board.copy()
    assert clone == partial_board


def test_copy_is_independent():
    b = Board()
    b.drop_disc(0, PLAYER1)
    clone = b.copy()
    clone.drop_disc(1, PLAYER2)
    # Original must not be modified
    assert b.grid[ROWS - 1][1] == EMPTY


def test_copy_history_independence():
    b = Board()
    b.drop_disc(0, PLAYER1)
    clone = b.copy()
    clone.undo_last_move()
    assert b.move_count == 1   # original unaffected


# ── to_tuple / hash ───────────────────────────────────────────────────────

def test_to_tuple_type(empty_board):
    t = empty_board.to_tuple()
    assert isinstance(t, tuple)
    assert all(isinstance(row, tuple) for row in t)


def test_to_tuple_changes_after_drop():
    b = Board()
    t1 = b.to_tuple()
    b.drop_disc(3, PLAYER1)
    t2 = b.to_tuple()
    assert t1 != t2


def test_hash_usable_as_dict_key(empty_board):
    d = {empty_board.to_tuple(): 42}
    assert d[empty_board.to_tuple()] == 42


# ── __eq__ ────────────────────────────────────────────────────────────────

def test_eq_same_state():
    b1 = Board()
    b2 = Board()
    b1.drop_disc(0, PLAYER1)
    b2.drop_disc(0, PLAYER1)
    assert b1 == b2


def test_eq_different_state():
    b1 = Board()
    b2 = Board()
    b1.drop_disc(0, PLAYER1)
    b2.drop_disc(1, PLAYER1)
    assert b1 != b2


def test_eq_non_board(empty_board):
    assert empty_board.__eq__("not a board") is NotImplemented
