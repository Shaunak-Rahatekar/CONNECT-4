"""
engine.py — High-level, reusable Connect-4 game engine functions.

Provides canonical procedural wrappers around the modular Board and Rules
classes, exposing a clean, functional interface suitable for both local game
play and future AI algorithmic evaluations.

Exposed functions:
------------------
- create_board() -> Board
- get_valid_moves(board) -> list[int]
- make_move(board, column, player) -> int | None
- check_winner(board, player) -> bool | int | None
- is_draw(board) -> bool
- get_game_status(board) -> dict

Complexity notes (Unit I — DAA)
---------------------------------
- create_board    : O(ROWS × COLS) time and space → O(42) ≈ O(1).
- get_valid_moves : O(COLS) time, O(COLS) space → checks top cell of each col.
- make_move       : O(ROWS) time, O(1) space → finds lowest empty row.
- check_winner    : O(ROWS × COLS) time, O(1) aux space → directional scans.
- is_draw         : O(ROWS × COLS) time, O(1) aux space → checks full + no win.
- get_game_status : O(ROWS × COLS) time, O(1) aux space → aggregates status.
"""

from __future__ import annotations
from typing import Union

from game.board import Board, ROWS, COLS, EMPTY, PLAYER1, PLAYER2
from game.rules import Rules, GameState


def _ensure_board(board: Union[Board, list[list[int]]]) -> Board:
    """Helper to convert a 2D grid into a Board instance if necessary."""
    if isinstance(board, Board):
        return board
    if isinstance(board, list):
        b = Board()
        b.grid = [row[:] for row in board]
        return b
    raise TypeError(f"Expected Board or list[list[int]], got {type(board).__name__}")


def create_board() -> Board:
    """Create and return a new empty 6 × 7 Connect-4 board.

    Initialises all cells to EMPTY (0) and sets PLAYER1 to move first.

    Complexity:
        Time:  O(ROWS × COLS) = O(42) ≈ O(1)
        Space: O(ROWS × COLS) = O(42) ≈ O(1)
    """
    return Board()


def get_valid_moves(board: Union[Board, list[list[int]]]) -> list[int]:
    """Return a list of column indices [0..6] that are legal to play into.

    If the game is already in a terminal state (win or draw), no moves are
    valid and an empty list is returned to prevent moves after game end.

    Complexity:
        Time:  O(ROWS × COLS) in worst case (terminal check) or O(COLS)
        Space: O(COLS) for the returned list of columns
    """
    b = _ensure_board(board)
    # If the game is already won or drawn, no moves are allowed
    if check_winner(b) is not None or is_draw(b):
        return []
    return b.get_valid_columns()


def make_move(
    board: Union[Board, list[list[int]]],
    column: int,
    player: int | None = None,
) -> int | None:
    """Place a disc into column for the given player.

    Parameters:
    -----------
    board : Board or list[list[int]]
        The board to update in place.
    column : int
        The target column (0 to COLS - 1).
    player : int | None
        PLAYER1 (1) or PLAYER2 (2). If None and board is a Board instance,
        defaults to board.current_player.

    Returns:
    --------
    int | None : The row index (0..5) where the disc landed, or None if the
                 move was illegal (out of bounds, column full, or game over).

    Guarantees:
    -----------
    - Gravity: the piece falls to the lowest unoccupied cell.
    - Atomicity: the board is not modified if the move is invalid or if the
      game is already over.
    - Turn alternation: if board is a Board instance and player is None,
      switches board.current_player after a successful placement.

    Complexity:
        Time:  O(ROWS) to find open row, plus O(ROWS × COLS) terminal check
        Space: O(1) auxiliary space
    """
    if column < 0 or column >= COLS:
        return None

    # Disallow moves if game is already over
    if check_winner(board) is not None or is_draw(board):
        return None

    if isinstance(board, Board):
        if not board.is_valid_column(column):
            return None
        active_player = player if player is not None else board.current_player
        row = board.drop_disc(column, active_player)
        if row is not None and player is None:
            board.switch_player()
        return row
    elif isinstance(board, list):
        if player is None:
            raise ValueError("Player must be specified when board is a raw 2D list.")
        # Check column top cell
        if board[0][column] != EMPTY:
            return None
        # Gravity: scan bottom-up
        for r in range(ROWS - 1, -1, -1):
            if board[r][column] == EMPTY:
                board[r][column] = player
                return r
        return None
    else:
        raise TypeError(f"Unsupported board type: {type(board).__name__}")


def check_winner(
    board: Union[Board, list[list[int]]],
    player: int | None = None,
) -> Union[bool, int, None]:
    """Check for a 4-in-a-row connection on the board.

    Parameters:
    -----------
    board : Board or list[list[int]]
        The Connect-4 board.
    player : int | None
        - If specified (PLAYER1 or PLAYER2), returns True if that specific
          player has four in a row, False otherwise.
        - If None, returns the winning player (1 or 2), or None if no winner.

    Complexity:
        Time:  O(ROWS × COLS) directional scan across the grid
        Space: O(1) auxiliary space
    """
    b = _ensure_board(board)
    state = Rules.check_win(b)
    if player is not None:
        if state is not None and state.winner == player:
            return True
        return False
    else:
        return state.winner if state is not None else None


def is_draw(board: Union[Board, list[list[int]]]) -> bool:
    """Return True if the board is completely full and neither player has won.

    Complexity:
        Time:  O(ROWS × COLS)
        Space: O(1) auxiliary space
    """
    b = _ensure_board(board)
    if not b.is_full():
        return False
    return Rules.check_win(b) is None


def get_game_status(board: Union[Board, list[list[int]]]) -> dict:
    """Return a comprehensive dictionary representing the authoritative game state.

    Complexity:
        Time:  O(ROWS × COLS)
        Space: O(1) auxiliary space
    """
    b = _ensure_board(board)
    win_state = Rules.check_win(b)
    has_win = win_state is not None
    winner = win_state.winner if has_win else None
    winning_cells = list(win_state.winning_cells) if has_win else []
    draw = is_draw(b)
    game_over = has_win or draw

    status_str = "win" if has_win else ("draw" if draw else "in_progress")
    valid_moves = [] if game_over else b.get_valid_columns()

    return {
        "status": status_str,
        "game_over": game_over,
        "winner": winner,
        "winning_cells": winning_cells,
        "is_draw": draw,
        "valid_moves": valid_moves,
        "current_player": b.current_player,
        "move_count": b.move_count,
    }
