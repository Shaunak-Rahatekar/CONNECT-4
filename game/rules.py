"""
rules.py — Connect-4 game-rule enforcement and win/draw detection.

This module is intentionally independent of Flask.

Win detection checks all four directions from every cell that was last
filled so the check is focused rather than scanning the entire board on
every call.

Complexity notes (Unit I — DAA)
---------------------------------
- check_win_at      : O(ROWS + COLS) in the worst case — it checks four
                      directions from a single cell, each scan bounded by
                      board dimensions.  For a fixed 6 × 7 board this is
                      effectively O(1).
- check_win (full)  : O(ROWS × COLS) — called when no specific cell is
                      available.
- apply_move        : O(ROWS) — delegates to Board.drop_disc.
- get_winner_info   : O(1) — reads cached state.
"""

from __future__ import annotations

from game.board import Board, ROWS, COLS, EMPTY, PLAYER1, PLAYER2


# ── Direction vectors ──────────────────────────────────────────────────────
# (row_delta, col_delta) pairs covering horizontal, vertical, and both
# diagonals.  Each direction is checked bi-directionally (positive and
# negative) so we need only four vectors instead of eight.
_DIRECTIONS: list[tuple[int, int]] = [
    (0, 1),   # horizontal
    (1, 0),   # vertical
    (1, 1),   # diagonal ↘
    (1, -1),  # diagonal ↙
]


class GameState:
    """Lightweight record of a completed game outcome."""

    __slots__ = ("winner", "winning_cells", "is_draw")

    def __init__(
        self,
        winner: int | None,
        winning_cells: list[tuple[int, int]],
        is_draw: bool,
    ) -> None:
        self.winner = winner                  # PLAYER1, PLAYER2, or None
        self.winning_cells = winning_cells    # list of (row, col) tuples
        self.is_draw = is_draw


class Rules:
    """Stateless helper that enforces Connect-4 rules on a Board object.

    All methods are class-level or static so no Rules instance needs to be
    stored alongside a Board.
    """

    # ------------------------------------------------------------------
    # Move application
    # ------------------------------------------------------------------

    @staticmethod
    def apply_move(board: Board, col: int) -> int | None:
        """Drop a disc for board.current_player into col.

        Validates the move, places the disc, and switches the current
        player.  Returns the landing row on success, or None if the move
        is illegal (column full or out of range).

        Does NOT check for game-over — callers must verify that
        is_game_over() returns False before calling this method.
        """
        if not board.is_valid_column(col):
            return None
        player = board.current_player
        row = board.drop_disc(col, player)
        if row is not None:
            board.switch_player()
        return row

    # ------------------------------------------------------------------
    # Win detection
    # ------------------------------------------------------------------

    @staticmethod
    def check_win_at(board: Board, row: int, col: int) -> GameState | None:
        """Check whether the disc at (row, col) completes four in a row.

        Returns a GameState if a win is found, otherwise None.
        Time: O(ROWS + COLS) worst case — O(1) for a fixed board.
        """
        player = board.grid[row][col]
        if player == EMPTY:
            return None

        for dr, dc in _DIRECTIONS:
            cells = Rules._collect_line(board, row, col, dr, dc)
            if len(cells) >= 4:
                cells.sort(key=lambda pt: (pt[0], pt[1]))
                return GameState(
                    winner=player,
                    winning_cells=cells[:4],  # first four in line order
                    is_draw=False,
                )
        return None

    @staticmethod
    def check_win(board: Board) -> GameState | None:
        """Scan the full board for any four-in-a-row.

        Returns a GameState on the first win found, otherwise None.
        Time: O(ROWS × COLS).

        This is the fallback when no specific last-move cell is available.
        """
        for r in range(ROWS):
            for c in range(COLS):
                if board.grid[r][c] != EMPTY:
                    result = Rules.check_win_at(board, r, c)
                    if result is not None:
                        return result
        return None

    @staticmethod
    def check_draw(board: Board) -> bool:
        """Return True when the board is full and there is no winner."""
        return board.is_full()

    @staticmethod
    def is_game_over(board: Board) -> tuple[bool, GameState | None]:
        """Return (is_over, GameState | None).

        is_over is True when the game has ended by win or draw.
        GameState carries the winner and winning cells (or is_draw=True).
        """
        win = Rules.check_win(board)
        if win is not None:
            return True, win
        if Rules.check_draw(board):
            return True, GameState(winner=None, winning_cells=[], is_draw=True)
        return False, None

    @staticmethod
    def is_game_over_after_move(
        board: Board, row: int, col: int
    ) -> tuple[bool, GameState | None]:
        """Faster game-over check when the last-move location is known.

        Only inspects lines passing through (row, col).  Avoids a full
        board scan.  Time: O(ROWS + COLS) ≈ O(1) for a fixed board.
        """
        win = Rules.check_win_at(board, row, col)
        if win is not None:
            return True, win
        if Rules.check_draw(board):
            return True, GameState(winner=None, winning_cells=[], is_draw=True)
        return False, None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_line(
        board: Board,
        row: int,
        col: int,
        dr: int,
        dc: int,
    ) -> list[tuple[int, int]]:
        """Return all consecutive same-player cells through (row, col) in
        direction (dr, dc) and its opposite.

        Time: O(max(ROWS, COLS)).
        """
        player = board.grid[row][col]
        cells: list[tuple[int, int]] = [(row, col)]

        # Positive direction
        r, c = row + dr, col + dc
        while 0 <= r < ROWS and 0 <= c < COLS and board.grid[r][c] == player:
            cells.append((r, c))
            r += dr
            c += dc

        # Negative direction
        r, c = row - dr, col - dc
        while 0 <= r < ROWS and 0 <= c < COLS and board.grid[r][c] == player:
            cells.append((r, c))
            r -= dr
            c -= dc

        return cells

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def opponent(player: int) -> int:
        """Return the other player's constant.  O(1)."""
        return PLAYER2 if player == PLAYER1 else PLAYER1
