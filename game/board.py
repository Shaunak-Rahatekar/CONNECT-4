"""
board.py — Connect-4 board representation and state management.

The board is a 6-row × 7-column grid.  Row 0 is the TOP of the visual
board; row 5 is the BOTTOM.  Gravity means a dropped disc occupies the
highest-numbered (lowest visual) empty row in a column.

Cell values
-----------
0  : empty
1  : Player 1 (human or AI — "Red")
2  : Player 2 (human or AI — "Yellow")

This module is intentionally independent of Flask so it can be imported
and tested without starting the web server.

Complexity notes (Unit I — DAA)
---------------------------------
- Board creation     : O(ROWS × COLS) time and space  → O(42) ≈ O(1) for
                       a fixed-size board, but noted as O(R·C) for generality.
- drop_disc          : O(ROWS) — scans from bottom to find landing row.
- get_valid_columns  : O(COLS) — checks each column header once.
- copy              : O(ROWS × COLS) — deep copies every cell.
- to_tuple / hash    : O(ROWS × COLS) — serialises the entire grid for use
                       as a dictionary key in the transposition table
                       (Prompt 6).
"""

from __future__ import annotations

ROWS: int = 6
COLS: int = 7

EMPTY:    int = 0
PLAYER1:  int = 1
PLAYER2:  int = 2


class Board:
    """Mutable representation of a Connect-4 board."""

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        """Initialise an empty 6 × 7 board and set Player 1 to move first."""
        self.grid: list[list[int]] = [
            [EMPTY] * COLS for _ in range(ROWS)
        ]
        self.current_player: int = PLAYER1
        self.move_count: int = 0
        # History stored as list of (column, row) tuples for undo support.
        self._history: list[tuple[int, int]] = []
        # Detailed move history with player, coordinates, and move sequence.
        self.move_history: list[dict] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_cell(self, row: int, col: int) -> int:
        """Return the value at (row, col).  O(1)."""
        return self.grid[row][col]

    def is_valid_column(self, col: int) -> bool:
        """Return True when col is in range and has at least one empty cell.

        A column is full when its top cell (row 0) is occupied.
        Time: O(1).
        """
        if col < 0 or col >= COLS:
            return False
        return self.grid[0][col] == EMPTY

    def get_valid_columns(self) -> list[int]:
        """Return the list of columns that can accept a disc.  O(COLS)."""
        return [c for c in range(COLS) if self.is_valid_column(c)]

    def get_next_open_row(self, col: int) -> int | None:
        """Return the lowest empty row index in col, or None if full.

        Scans from the bottom (highest index) upward.  O(ROWS).
        """
        for row in range(ROWS - 1, -1, -1):
            if self.grid[row][col] == EMPTY:
                return row
        return None

    def drop_disc(self, col: int, player: int) -> int | None:
        """Place a disc for *player* in *col* using gravity.

        Returns the row where the disc landed, or None if the column is
        full or the column index is out of range.  Does NOT enforce whose
        turn it is — that is the responsibility of the caller (Rules).

        Time: O(ROWS).
        """
        if col < 0 or col >= COLS:
            return None
        row = self.get_next_open_row(col)
        if row is None:
            return None
        self.grid[row][col] = player
        self._history.append((col, row))
        self.move_count += 1
        self.move_history.append({
            "move_number": self.move_count,
            "player": player,
            "col": col,
            "row": row,
        })
        return row

    def undo_last_move(self) -> tuple[int, int] | None:
        """Remove the most recently placed disc.

        Returns (col, row) of the undone move, or None if the board is
        already empty.  Used by the AI search to restore board state
        without copying.  O(1).
        """
        if not self._history:
            return None
        col, row = self._history.pop()
        self.grid[row][col] = EMPTY
        self.move_count -= 1
        if self.move_history:
            self.move_history.pop()
        return col, row

    def switch_player(self) -> None:
        """Toggle current_player between PLAYER1 and PLAYER2.  O(1)."""
        self.current_player = (
            PLAYER2 if self.current_player == PLAYER1 else PLAYER1
        )

    def is_full(self) -> bool:
        """Return True when every cell is occupied.  O(COLS)."""
        return len(self.get_valid_columns()) == 0

    def reset(self) -> None:
        """Clear the board and restart from Player 1.  O(ROWS × COLS)."""
        self.grid = [[EMPTY] * COLS for _ in range(ROWS)]
        self.current_player = PLAYER1
        self.move_count = 0
        self._history.clear()
        self.move_history.clear()

    def copy(self) -> "Board":
        """Return a deep copy of this board.  O(ROWS × COLS).

        The copy shares no mutable state with the original.
        """
        new_board = Board()
        new_board.grid = [row[:] for row in self.grid]
        new_board.current_player = self.current_player
        new_board.move_count = self.move_count
        new_board._history = self._history[:]
        new_board.move_history = [dict(entry) for entry in self.move_history]
        return new_board

    def get_move_history(self) -> list[dict]:
        """Return a copy of the move history recorded so far.  O(N)."""
        return [dict(entry) for entry in self.move_history]

    def to_tuple(self) -> tuple:
        """Return an immutable, hashable representation of the grid.

        Used as a dictionary key in the transposition table.  O(ROWS × COLS).
        """
        return tuple(tuple(row) for row in self.grid)

    def to_list(self) -> list[list[int]]:
        """Return the grid as a plain nested list (for JSON serialisation)."""
        return [row[:] for row in self.grid]

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        lines = []
        for row in self.grid:
            lines.append(" ".join(str(cell) for cell in row))
        return "\n".join(lines)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Board):
            return NotImplemented
        return self.grid == other.grid

    def __hash__(self) -> int:
        return hash(self.to_tuple())
