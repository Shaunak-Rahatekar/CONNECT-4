"""
test_engine.py — Unit tests for reusable Connect-4 engine functions.

Covers:
- create_board: empty grid, dimensions, initial player, move count
- make_move: legal moves, gravity drop, turn alternation, player override
- Illegal moves: negative column, too large column, non-integer, full column
- Board atomicity: invalid move does not alter board state or turn
- Winning detection in all 4 directions:
    1. Horizontal (row constant, col varying)
    2. Vertical (col constant, row varying)
    3. Diagonal-downward (↘ top-left to bottom-right)
    4. Diagonal-upward (↗ bottom-left to top-right)
- Non-winning states
- True draw detection (full board with no 4-in-a-row)
- Post-game protection: make_move returns None after win or draw
- get_valid_moves: active columns vs empty when game over
- get_game_status: comprehensive dictionary validation
- Reset behavior via board.reset()
"""

import pytest
from game.board import Board, ROWS, COLS, EMPTY, PLAYER1, PLAYER2
from game.engine import (
    create_board,
    get_valid_moves,
    make_move,
    check_winner,
    is_draw,
    get_game_status,
)


# ---------------------------------------------------------------------------
# 1. create_board
# ---------------------------------------------------------------------------

def test_create_board_initial_state():
    b = create_board()
    assert isinstance(b, Board)
    assert len(b.grid) == ROWS
    assert all(len(row) == COLS for row in b.grid)
    assert all(cell == EMPTY for row in b.grid for cell in row)
    assert b.current_player == PLAYER1
    assert b.move_count == 0
    assert b.get_valid_columns() == list(range(COLS))


# ---------------------------------------------------------------------------
# 2. make_move & Legal moves
# ---------------------------------------------------------------------------

def test_make_move_legal_drop():
    b = create_board()
    # P1 plays col 3 -> lands on bottom row (ROWS - 1)
    row = make_move(b, 3)
    assert row == ROWS - 1
    assert b.grid[ROWS - 1][3] == PLAYER1
    assert b.current_player == PLAYER2
    assert b.move_count == 1
    assert len(b.get_move_history()) == 1


def test_make_move_gravity_stacking():
    b = create_board()
    # P1 plays col 0
    r1 = make_move(b, 0)
    # P2 plays col 0
    r2 = make_move(b, 0)
    assert r1 == ROWS - 1
    assert r2 == ROWS - 2
    assert b.grid[ROWS - 1][0] == PLAYER1
    assert b.grid[ROWS - 2][0] == PLAYER2
    assert b.current_player == PLAYER1
    assert b.move_count == 2


def test_make_move_with_explicit_player():
    b = create_board()
    row = make_move(b, 2, player=PLAYER2)
    assert row == ROWS - 1
    assert b.grid[ROWS - 1][2] == PLAYER2
    # When player is explicitly provided, current_player should remain untouched
    assert b.current_player == PLAYER1


def test_make_move_on_raw_grid():
    grid = [[EMPTY] * COLS for _ in range(ROWS)]
    row = make_move(grid, 4, player=PLAYER1)
    assert row == ROWS - 1
    assert grid[ROWS - 1][4] == PLAYER1

    # Second disc in same column
    row2 = make_move(grid, 4, player=PLAYER2)
    assert row2 == ROWS - 2
    assert grid[ROWS - 2][4] == PLAYER2


# ---------------------------------------------------------------------------
# 3. Illegal moves & Atomicity
# ---------------------------------------------------------------------------

def test_make_move_negative_column_rejected():
    b = create_board()
    snap = b.to_tuple()
    res = make_move(b, -1)
    assert res is None
    assert b.to_tuple() == snap
    assert b.current_player == PLAYER1
    assert b.move_count == 0


def test_make_move_too_large_column_rejected():
    b = create_board()
    snap = b.to_tuple()
    res = make_move(b, 7)
    assert res is None
    assert b.to_tuple() == snap
    assert b.current_player == PLAYER1
    assert b.move_count == 0


def test_make_move_full_column_rejected():
    b = create_board()
    # Fill col 0 completely (6 discs)
    for _ in range(ROWS):
        assert make_move(b, 0) is not None
    assert not b.is_valid_column(0)

    snap = b.to_tuple()
    prev_moves = b.move_count
    # 7th move in full column must be rejected
    res = make_move(b, 0)
    assert res is None
    assert b.to_tuple() == snap
    assert b.move_count == prev_moves


# ---------------------------------------------------------------------------
# 4. Winning connections in all 4 directions
# ---------------------------------------------------------------------------

def test_check_winner_horizontal():
    b = create_board()
    # P1 plays columns 0, 1, 2, 3 on bottom row
    for c in range(4):
        b.drop_disc(c, PLAYER1)
    assert check_winner(b) == PLAYER1
    assert check_winner(b, PLAYER1) is True
    assert check_winner(b, PLAYER2) is False


def test_check_winner_vertical():
    b = create_board()
    # P2 stacks 4 discs in column 4
    for _ in range(4):
        b.drop_disc(4, PLAYER2)
    assert check_winner(b) == PLAYER2
    assert check_winner(b, PLAYER2) is True
    assert check_winner(b, PLAYER1) is False


def test_check_winner_diagonal_downward():
    """
    Diagonal ↘ (top-left to bottom-right):
    (r, c) = (2, 0), (3, 1), (4, 2), (5, 3)
    """
    b = create_board()
    # Col 0: 4 discs total (lowest is row 5, up to row 2)
    for _ in range(3):
        b.drop_disc(0, PLAYER2)  # rows 5, 4, 3
    b.drop_disc(0, PLAYER1)      # row 2

    # Col 1: 3 discs total
    for _ in range(2):
        b.drop_disc(1, PLAYER2)  # rows 5, 4
    b.drop_disc(1, PLAYER1)      # row 3

    # Col 2: 2 discs total
    b.drop_disc(2, PLAYER2)      # row 5
    b.drop_disc(2, PLAYER1)      # row 4

    # Col 3: 1 disc total
    b.drop_disc(3, PLAYER1)      # row 5

    assert check_winner(b) == PLAYER1
    assert check_winner(b, PLAYER1) is True


def test_check_winner_diagonal_upward():
    """
    Diagonal ↗ (bottom-left to top-right):
    (r, c) = (5, 0), (4, 1), (3, 2), (2, 3)
    """
    b = create_board()
    # Col 0: 1 disc (row 5)
    b.drop_disc(0, PLAYER2)      # row 5

    # Col 1: 2 discs
    b.drop_disc(1, PLAYER1)      # row 5
    b.drop_disc(1, PLAYER2)      # row 4

    # Col 2: 3 discs
    b.drop_disc(2, PLAYER1)      # row 5
    b.drop_disc(2, PLAYER1)      # row 4
    b.drop_disc(2, PLAYER2)      # row 3

    # Col 3: 4 discs
    b.drop_disc(3, PLAYER1)      # row 5
    b.drop_disc(3, PLAYER1)      # row 4
    b.drop_disc(3, PLAYER1)      # row 3
    b.drop_disc(3, PLAYER2)      # row 2

    assert check_winner(b) == PLAYER2
    assert check_winner(b, PLAYER2) is True


def test_non_winning_positions():
    b = create_board()
    assert check_winner(b) is None
    # 3 in a row
    for c in range(3):
        b.drop_disc(c, PLAYER1)
    assert check_winner(b) is None
    assert check_winner(b, PLAYER1) is False
    assert check_winner(b, PLAYER2) is False


# ---------------------------------------------------------------------------
# 5. Deterministic Draw Detection
# ---------------------------------------------------------------------------

def create_deterministic_draw_board() -> Board:
    """
    Generate a full 6x7 board with 0 four-in-a-row connections.
    Uses an alternating row pattern verified to produce no 4-in-a-row lines:
    Row 0: 1 2 1 2 1 2 1
    Row 1: 1 2 1 2 1 2 1
    Row 2: 2 1 2 1 2 1 2
    Row 3: 2 1 2 1 2 1 2
    Row 4: 1 2 1 2 1 2 1
    Row 5: 2 1 2 1 2 1 2
    """
    grid = [
        [1, 2, 1, 2, 1, 2, 1],
        [1, 2, 1, 2, 1, 2, 1],
        [2, 1, 2, 1, 2, 1, 2],
        [2, 1, 2, 1, 2, 1, 2],
        [1, 2, 1, 2, 1, 2, 1],
        [2, 1, 2, 1, 2, 1, 2],
    ]
    b = create_board()
    for c in range(COLS):
        for r in range(ROWS - 1, -1, -1):
            b.drop_disc(c, grid[r][c])
    return b


def test_draw_detection():
    b = create_deterministic_draw_board()
    assert b.is_full()
    assert check_winner(b) is None
    assert is_draw(b) is True


def test_is_draw_false_when_board_not_full():
    b = create_board()
    assert is_draw(b) is False


def test_is_draw_false_when_board_full_but_winner_exists():
    b = create_board()
    # Fill entirely with P1 (winner exists)
    for c in range(COLS):
        for _ in range(ROWS):
            b.drop_disc(c, PLAYER1)
    assert b.is_full()
    assert check_winner(b) == PLAYER1
    assert is_draw(b) is False  # Must NOT be a draw if there is a winner!


# ---------------------------------------------------------------------------
# 6. Moves after game has ended & valid moves
# ---------------------------------------------------------------------------

def test_prevent_moves_after_win():
    b = create_board()
    for c in range(4):
        b.drop_disc(c, PLAYER1)
    assert check_winner(b) == PLAYER1

    # Attempt move after win
    res = make_move(b, 5)
    assert res is None
    # get_valid_moves should return empty list
    assert get_valid_moves(b) == []


def test_prevent_moves_after_draw():
    b = create_deterministic_draw_board()
    assert is_draw(b) is True

    res = make_move(b, 0)
    assert res is None
    assert get_valid_moves(b) == []


def test_get_valid_moves_partial_board():
    b = create_board()
    # Fill column 2 completely alternating discs so no 4-in-a-row is formed
    for i in range(ROWS):
        b.drop_disc(2, (i % 2) + 1)
    assert not b.is_valid_column(2)
    assert check_winner(b) is None
    valid = get_valid_moves(b)
    assert 2 not in valid
    assert valid == [0, 1, 3, 4, 5, 6]


# ---------------------------------------------------------------------------
# 7. get_game_status
# ---------------------------------------------------------------------------

def test_get_game_status_in_progress():
    b = create_board()
    make_move(b, 3)
    status = get_game_status(b)
    assert status["status"] == "in_progress"
    assert status["game_over"] is False
    assert status["winner"] is None
    assert status["winning_cells"] == []
    assert status["is_draw"] is False
    assert status["current_player"] == PLAYER2
    assert status["move_count"] == 1
    assert len(status["valid_moves"]) == 7


def test_get_game_status_win():
    b = create_board()
    for c in range(4):
        b.drop_disc(c, PLAYER1)
    status = get_game_status(b)
    assert status["status"] == "win"
    assert status["game_over"] is True
    assert status["winner"] == PLAYER1
    assert len(status["winning_cells"]) == 4
    assert status["valid_moves"] == []


def test_get_game_status_draw():
    b = create_deterministic_draw_board()
    status = get_game_status(b)
    assert status["status"] == "draw"
    assert status["game_over"] is True
    assert status["winner"] is None
    assert status["is_draw"] is True
    assert status["valid_moves"] == []


# ---------------------------------------------------------------------------
# 8. Reset behavior & Move history
# ---------------------------------------------------------------------------

def test_reset_behavior():
    b = create_board()
    make_move(b, 1)
    make_move(b, 2)
    assert b.move_count == 2
    assert len(b.get_move_history()) == 2

    b.reset()
    assert b.move_count == 0
    assert b.current_player == PLAYER1
    assert b.get_valid_columns() == list(range(COLS))
    assert b.get_move_history() == []
    assert all(cell == EMPTY for row in b.grid for cell in row)
