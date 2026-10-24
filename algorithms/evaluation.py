"""
evaluation.py — Heuristic board evaluation for Connect-4.

Calculates a static score for a given board position from the perspective of
a target player (typically the AI).

Evaluation concepts (DAA Unit I & IV):
--------------------------------------
A standard 6 × 7 Connect-4 grid contains exactly 69 unique 4-cell windows
(lines of length 4):
- 24 horizontal windows (4 per row × 6 rows)
- 21 vertical windows (3 per col × 7 cols)
- 12 diagonal-downward windows (3 × 4)
- 12 diagonal-upward windows (3 × 4)
Total = 69 windows.

Every potential winning line must occupy one of these 69 windows.

Scoring heuristic:
------------------
For each window:
- If both AI and opponent have discs in the window, it is blocked (score 0).
- If only AI discs exist:
    - 4 discs: WIN_SCORE (+100,000)
    - 3 discs + 1 empty: THREE_SCORE (+100)
    - 2 discs + 2 empty: TWO_SCORE (+10)
    - 1 disc  + 3 empty: ONE_SCORE (+1)
- If only opponent discs exist:
    - 4 discs: -OPP_WIN_SCORE (-100,000)
    - 3 discs + 1 empty: -OPP_THREE_SCORE (-90)  [high defensive penalty]
    - 2 discs + 2 empty: -OPP_TWO_SCORE (-10)
    - 1 disc  + 3 empty: -OPP_ONE_SCORE (-1)

Center column control:
----------------------
The center column (column 3, 0-indexed) participates in 21 winning windows
(more than any other column). Discs in column 3 receive an additional
CENTER_WEIGHT bonus (+4 per AI disc, -4 per opponent disc).

Complexity:
-----------
- Window generation: O(1) executed once at module load (69 windows).
- evaluate_board: O(69 × 4) = O(276) ≈ O(1) for fixed 6 × 7 board.
                  In terms of board dimensions: O(R · C · K).
- Space complexity: O(1) auxiliary space (no board copies).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Union

from game.board import Board, ROWS, COLS, EMPTY, PLAYER1, PLAYER2
from game.rules import Rules


@dataclass(frozen=True)
class HeuristicWeights:
    """Configurable weights for the heuristic evaluation function."""
    win: int = 100_000
    three: int = 100
    two: int = 10
    one: int = 1
    opp_win: int = 100_000
    opp_three: int = 90
    opp_two: int = 10
    opp_one: int = 1
    center: int = 4


DEFAULT_WEIGHTS = HeuristicWeights()


def _generate_all_windows() -> list[tuple[tuple[int, int], ...]]:
    """Precompute the 69 winning 4-cell coordinate tuples on a 6x7 board."""
    windows: list[tuple[tuple[int, int], ...]] = []

    # 1. Horizontal windows (6 rows × 4 per row = 24)
    for r in range(ROWS):
        for c in range(COLS - 3):
            windows.append(((r, c), (r, c + 1), (r, c + 2), (r, c + 3)))

    # 2. Vertical windows (7 cols × 3 per col = 21)
    for c in range(COLS):
        for r in range(ROWS - 3):
            windows.append(((r, c), (r + 1, c), (r + 2, c), (r + 3, c)))

    # 3. Diagonal ↘ (down-right: 3 × 4 = 12)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            windows.append(((r, c), (r + 1, c + 1), (r + 2, c + 2), (r + 3, c + 3)))

    # 4. Diagonal ↗ (up-right: 3 × 4 = 12)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            windows.append(((r, c), (r - 1, c + 1), (r - 2, c + 2), (r - 3, c + 3)))

    return windows


# Precompute all 69 windows once at module import
ALL_WINDOWS: tuple[tuple[tuple[int, int], ...], ...] = tuple(_generate_all_windows())


def _ensure_board(board: Union[Board, list[list[int]]]) -> Board:
    """Convert a 2D list into a Board instance if needed."""
    if isinstance(board, Board):
        return board
    if isinstance(board, list):
        b = Board()
        b.grid = [row[:] for row in board]
        return b
    raise TypeError(f"Expected Board or list[list[int]], got {type(board).__name__}")


def evaluate_window(
    window_cells: list[int],
    player: int,
    opponent: int,
    weights: HeuristicWeights,
) -> int:
    """Score a single 4-cell window for player.

    Complexity: O(4) = O(1).
    """
    player_count = window_cells.count(player)
    opp_count = window_cells.count(opponent)
    empty_count = window_cells.count(EMPTY)

    # If both players occupy cells in this window, neither can complete 4-in-a-row
    if player_count > 0 and opp_count > 0:
        return 0

    score = 0
    if player_count == 4:
        score += weights.win
    elif player_count == 3 and empty_count == 1:
        score += weights.three
    elif player_count == 2 and empty_count == 2:
        score += weights.two
    elif player_count == 1 and empty_count == 3:
        score += weights.one

    if opp_count == 4:
        score -= weights.opp_win
    elif opp_count == 3 and empty_count == 1:
        score -= weights.opp_three
    elif opp_count == 2 and empty_count == 2:
        score -= weights.opp_two
    elif opp_count == 1 and empty_count == 3:
        score -= weights.opp_one

    return score


def evaluate_board(
    board: Union[Board, list[list[int]]],
    player: int = PLAYER2,
    weights: HeuristicWeights | None = None,
) -> float:
    """Calculate the heuristic score of a board position for player.

    Higher scores indicate a better position for `player`.
    Lower/negative scores indicate an advantage for the opponent.

    Parameters:
    -----------
    board : Board or list[list[int]]
        The Connect-4 board state.
    player : int
        The player whose perspective to evaluate (PLAYER1 or PLAYER2).
    weights : HeuristicWeights | None
        Configuration weights; defaults to DEFAULT_WEIGHTS.

    Returns:
    --------
    float : The aggregate static heuristic score.

    Complexity:
    -----------
    Time:  O(69 × 4) = O(276) ≈ O(1) for fixed 6 × 7 board.
           O(R · C · K) for an R × C board with connection length K.
    Space: O(1) auxiliary space (no board duplication).
    """
    b = _ensure_board(board)
    w = weights if weights is not None else DEFAULT_WEIGHTS
    opponent = Rules.opponent(player)

    grid = b.grid
    total_score = 0

    # 1. Center column preference bonus
    center_col = COLS // 2  # Column index 3
    center_player_discs = 0
    center_opp_discs = 0
    for r in range(ROWS):
        val = grid[r][center_col]
        if val == player:
            center_player_discs += 1
        elif val == opponent:
            center_opp_discs += 1
    total_score += (center_player_discs - center_opp_discs) * w.center

    # 2. Score all 69 windows of length 4
    for window in ALL_WINDOWS:
        cells = [grid[r][c] for r, c in window]
        total_score += evaluate_window(cells, player, opponent, w)

    return float(total_score)
