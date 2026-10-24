"""
greedy.py — Greedy Heuristic AI for Connect-4.

Implements a depth-1 tactical decision maker that evaluates candidate moves
using immediate priorities and static heuristic position scoring.

Move-Selection Priorities (DAA Unit IV — Greedy Strategy):
----------------------------------------------------------
1. Immediate Win: Take any legal move that completes four-in-a-row right now.
2. Immediate Block: Block any column where the opponent would win on their next turn.
3. Heuristic Maximisation: Evaluate the board position resulting from each candidate
   move using `evaluate_board()` (open 3s, open 2s, center presence).
4. Center Preference: If multiple moves yield equal tactical value, prefer the
   column closest to the center (column 3).
5. Deterministic Tie-Breaking: Use fixed column priority order [3, 2, 4, 1, 5, 0, 6]
   to ensure 100% reproducible behavior across runs.

Terminal and Full Board Safety:
-------------------------------
If no valid moves exist or the board is in a terminal state (win or draw),
returns `None` without modifying the board.

Complexity (DAA Unit I & IV):
-----------------------------
- Candidate moves: at most C = 7 moves.
- Simulation cost: O(ROWS) to drop + O(1) undo per candidate.
- Win check per candidate: O(1) via Rules.check_win_at.
- Heuristic evaluation per candidate: O(69 windows × 4) = O(276) ≈ O(1).
- Total time complexity: O(C · (ROWS + R·C·K)) = O(7 · (6 + 69·4)) ≈ O(1)
  bound for fixed 6 × 7 board. Typically executes in < 1 ms.
- Auxiliary space: O(C) for candidate scores dictionary. ZERO board copies:
  all simulations use `board.drop_disc()` and `board.undo_last_move()`.
"""

from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Union

from game.board import Board, ROWS, COLS, PLAYER1, PLAYER2
from game.rules import Rules
from algorithms.evaluation import evaluate_board, HeuristicWeights, DEFAULT_WEIGHTS

# Preferred column ordering: center column first, moving symmetrically outward
# with deterministic lower-index tie-breaking.
_COLUMN_PREFERENCE_ORDER: tuple[int, ...] = (3, 2, 4, 1, 5, 0, 6)


@dataclass
class GreedyDecision:
    """Detailed record of a Greedy AI decision."""
    column: int | None
    score: float
    reason: str
    candidate_scores: dict[int, float]
    execution_time_ms: float

    def to_dict(self) -> dict:
        return {
            "strategy": "greedy",
            "column": self.column,
            "score": round(self.score, 2),
            "reason": self.reason,
            "candidate_scores": {str(c): round(s, 2) for c, s in self.candidate_scores.items()},
            "execution_time_ms": round(self.execution_time_ms, 3),
        }


def _ensure_board(board: Union[Board, list[list[int]]]) -> Board:
    """Helper to convert a 2D list into a Board instance if needed."""
    if isinstance(board, Board):
        return board
    if isinstance(board, list):
        b = Board()
        b.grid = [row[:] for row in board]
        return b
    raise TypeError(f"Expected Board or list[list[int]], got {type(board).__name__}")


def get_greedy_decision(
    board: Union[Board, list[list[int]]],
    player: int = PLAYER2,
    weights: HeuristicWeights | None = None,
) -> GreedyDecision:
    """Compute the optimal Greedy move with tactical priorities and reasoning.

    Parameters:
    -----------
    board : Board or list[list[int]]
        The Connect-4 board to evaluate.
    player : int
        The player making the move (PLAYER1 or PLAYER2). Defaults to PLAYER2.
    weights : HeuristicWeights | None
        Heuristic weight configuration.

    Returns:
    --------
    GreedyDecision : Record with selected column, heuristic score, explanation,
                     candidate move scores, and measured execution time.
    """
    start_time = time.perf_counter()
    b = _ensure_board(board)
    w = weights if weights is not None else DEFAULT_WEIGHTS
    opponent = Rules.opponent(player)

    # 1. Safety check: Check if game is already terminal or board is full
    if Rules.check_win(b) is not None:
        elapsed = (time.perf_counter() - start_time) * 1000
        return GreedyDecision(
            column=None,
            score=0.0,
            reason="Game is already over (winner exists).",
            candidate_scores={},
            execution_time_ms=elapsed,
        )

    valid_cols = b.get_valid_columns()
    if not valid_cols:
        elapsed = (time.perf_counter() - start_time) * 1000
        return GreedyDecision(
            column=None,
            score=0.0,
            reason="No legal moves available (board full).",
            candidate_scores={},
            execution_time_ms=elapsed,
        )

    candidate_scores: dict[int, float] = {}

    # Sort valid columns according to center-preference rank as baseline
    ranked_valid_cols = sorted(valid_cols, key=lambda c: _COLUMN_PREFERENCE_ORDER.index(c))

    # -----------------------------------------------------------------------
    # Priority 1: Take an immediate winning move whenever available
    # -----------------------------------------------------------------------
    for col in ranked_valid_cols:
        row = b.drop_disc(col, player)
        if row is not None:
            is_win, state = Rules.is_game_over_after_move(b, row, col)
            b.undo_last_move()
            if is_win and state is not None and state.winner == player:
                candidate_scores[col] = float(w.win)
                elapsed = (time.perf_counter() - start_time) * 1000
                return GreedyDecision(
                    column=col,
                    score=float(w.win),
                    reason=f"Winning move detected: completes 4-in-a-row in column {col + 1}.",
                    candidate_scores={c: (float(w.win) if c == col else 0.0) for c in valid_cols},
                    execution_time_ms=elapsed,
                )

    # -----------------------------------------------------------------------
    # Priority 2: Block opponent's immediate winning move
    # -----------------------------------------------------------------------
    opponent_threat_cols: list[int] = []
    for col in ranked_valid_cols:
        row = b.drop_disc(col, opponent)
        if row is not None:
            is_win, state = Rules.is_game_over_after_move(b, row, col)
            b.undo_last_move()
            if is_win and state is not None and state.winner == opponent:
                opponent_threat_cols.append(col)

    if opponent_threat_cols:
        # Block the most threatening column (preferring center if multiple)
        block_col = opponent_threat_cols[0]
        block_score = float(w.win - 100)
        candidate_scores[block_col] = block_score
        elapsed = (time.perf_counter() - start_time) * 1000
        return GreedyDecision(
            column=block_col,
            score=block_score,
            reason=f"Defensive block: prevents opponent win in column {block_col + 1}.",
            candidate_scores={c: (block_score if c == block_col else 0.0) for c in valid_cols},
            execution_time_ms=elapsed,
        )

    # -----------------------------------------------------------------------
    # Priority 3 & 4: Heuristic position evaluation + Center preference
    # -----------------------------------------------------------------------
    for col in valid_cols:
        row = b.drop_disc(col, player)
        if row is not None:
            score = evaluate_board(b, player, w)
            b.undo_last_move()
            candidate_scores[col] = score

    # Select candidate with highest score; break ties via center rank
    best_col = max(
        valid_cols,
        key=lambda c: (
            candidate_scores[c],
            -_COLUMN_PREFERENCE_ORDER.index(c)
        ),
    )
    best_score = candidate_scores[best_col]

    elapsed = (time.perf_counter() - start_time) * 1000
    reason_text = (
        f"Tactical heuristic evaluation (score: {best_score:+.1f}). "
        f"Selected column {best_col + 1} with center-bias."
    )

    return GreedyDecision(
        column=best_col,
        score=best_score,
        reason=reason_text,
        candidate_scores=candidate_scores,
        execution_time_ms=elapsed,
    )


def choose_greedy_move(
    board: Union[Board, list[list[int]]],
    player: int = PLAYER2,
    weights: HeuristicWeights | None = None,
) -> int | None:
    """Convenience function returning solely the chosen column index (0-6).

    Returns None if no moves are available or the game has ended.

    Complexity: O(1) bound (< 1 ms).
    """
    decision = get_greedy_decision(board, player, weights)
    return decision.column
