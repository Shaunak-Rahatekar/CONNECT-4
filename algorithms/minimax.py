"""
minimax.py — Recursive Minimax AI for Connect-4.

Implements full adversarial minimax game-tree search over candidate board moves.

Theoretical Foundations (DAA Unit II & IV):
--------------------------------------------
Minimax is a recursive algorithm for decision-making in zero-sum, perfect-information
two-player games. It computes the subgame-perfect equilibrium under the assumption
that both players play optimally:
- MAX (AI): seeks to maximize the evaluation score.
- MIN (Opponent): seeks to minimize the evaluation score.

Recurrence Relation:
--------------------
                 ┌ Utility(s)                     if s is a terminal state (win/loss/draw)
                 │ Heuristic(s)                   if depth limit d = 0 reached
    V(s, d) =    │ max_{a ∈ Actions(s)} V(s', d-1) if Player(s) = MAX (AI)
                 └ min_{a ∈ Actions(s)} V(s', d-1) if Player(s) = MIN (Opponent)
where s' = Result(s, a).

Depth-Aware Terminal Scoring:
-----------------------------
To ensure the AI prefers immediate wins over distant wins, and delays unavoidable
losses as long as possible:
- AI Win:       +1,000,000 + (depth × 1,000)
- Opponent Win: -1,000,000 - (depth × 1,000)
- Draw:         0.0

Complexity:
-----------
- Branching Factor (b): b ≤ 7 (at most 7 columns).
- Search Depth (d): configurable depth limit (e.g. 1 to 4).
- Time Complexity: O(b^d) worst-case node expansions.
    - Depth 1: ≤ 7 nodes (< 1 ms)
    - Depth 2: ≤ 49 nodes (~2 ms)
    - Depth 3: ≤ 343 nodes (~20 ms)
    - Depth 4: ≤ 2,401 nodes (~150-300 ms)
- Space Complexity: O(d) recursion stack depth.
  In-place backtracking with `board.drop_disc()` and `board.undo_last_move()`
  ensures ZERO heap allocations for board duplication.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Union

from game.board import Board, ROWS, COLS, PLAYER1, PLAYER2
from game.rules import Rules
from algorithms.evaluation import evaluate_board, HeuristicWeights, DEFAULT_WEIGHTS

# Preferred column order for deterministic tie-breaking and optimal center exploration
_PREFERRED_COLUMNS: tuple[int, ...] = (3, 2, 4, 1, 5, 0, 6)

TERMINAL_WIN_BASE: float = 1_000_000.0


@dataclass
class MinimaxStats:
    """Internal tracker for search statistics during recursive execution."""
    initial_depth: int
    nodes_visited: int = 0
    recursive_calls: int = 0
    max_depth_reached: int = 0


@dataclass
class MinimaxDecision:
    """Authoritative structured output from a Minimax search."""
    column: int | None
    score: float
    depth: int
    nodes_visited: int
    recursive_calls: int
    max_depth_reached: int
    execution_time_ms: float
    candidate_scores: dict[int, float]
    tree: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": "minimax",
            "column": self.column,
            "score": round(self.score, 2),
            "depth": self.depth,
            "nodes_visited": self.nodes_visited,
            "recursive_calls": self.recursive_calls,
            "max_depth_reached": self.max_depth_reached,
            "execution_time_ms": round(self.execution_time_ms, 3),
            "candidate_scores": {str(c): round(s, 2) for c, s in self.candidate_scores.items()},
            "tree": self.tree,
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


def _minimax_recursive(
    board: Board,
    depth: int,
    is_maximizing: bool,
    ai_player: int,
    weights: HeuristicWeights,
    stats: MinimaxStats,
) -> float:
    """Recursive core of the Minimax algorithm.

    Returns the minimax evaluation value of the subtree.
    """
    stats.nodes_visited += 1
    current_ply = stats.initial_depth - depth
    if current_ply > stats.max_depth_reached:
        stats.max_depth_reached = current_ply

    opponent = Rules.opponent(ai_player)

    # 1. Terminal Check: Inspect if the prior move produced a terminal outcome
    # We inspect the board for any four-in-a-row
    win_state = Rules.check_win(board)
    if win_state is not None:
        if win_state.winner == ai_player:
            return TERMINAL_WIN_BASE + (depth * 1_000.0)
        else:
            return -TERMINAL_WIN_BASE - (depth * 1_000.0)

    # Check for draw (full board with no winner)
    valid_cols = board.get_valid_columns()
    if not valid_cols:
        return 0.0

    # 2. Depth Limit Cut-off: Apply static heuristic evaluation function
    if depth == 0:
        return evaluate_board(board, player=ai_player, weights=weights)

    # Sort columns by center-outward order for optimal move order
    ordered_cols = sorted(valid_cols, key=lambda c: _PREFERRED_COLUMNS.index(c))

    stats.recursive_calls += 1

    if is_maximizing:
        max_eval = -float("inf")
        for col in ordered_cols:
            row = board.drop_disc(col, ai_player)
            if row is not None:
                # Fast check: if this move creates an immediate win, take terminal score directly
                is_win, state = Rules.is_game_over_after_move(board, row, col)
                if is_win and state is not None and state.winner == ai_player:
                    eval_val = TERMINAL_WIN_BASE + (depth * 1_000.0)
                else:
                    eval_val = _minimax_recursive(board, depth - 1, False, ai_player, weights, stats)
                board.undo_last_move()
                if eval_val > max_eval:
                    max_eval = eval_val
        return max_eval
    else:
        min_eval = float("inf")
        for col in ordered_cols:
            row = board.drop_disc(col, opponent)
            if row is not None:
                # Fast check: if opponent move creates an immediate win, take terminal score directly
                is_win, state = Rules.is_game_over_after_move(board, row, col)
                if is_win and state is not None and state.winner == opponent:
                    eval_val = -TERMINAL_WIN_BASE - (depth * 1_000.0)
                else:
                    eval_val = _minimax_recursive(board, depth - 1, True, ai_player, weights, stats)
                board.undo_last_move()
                if eval_val < min_eval:
                    min_eval = eval_val
        return min_eval


def get_minimax_decision(
    board: Union[Board, list[list[int]]],
    depth: int = 3,
    player: int = PLAYER2,
    weights: HeuristicWeights | None = None,
) -> MinimaxDecision:
    """Execute depth-bounded Minimax search and return structured decision statistics.

    Parameters:
    -----------
    board : Board or list[list[int]]
        The Connect-4 board state.
    depth : int
        Search depth limit (default 3, recommended range 1 to 4).
    player : int
        The maximizing player (PLAYER1 or PLAYER2). Defaults to PLAYER2.
    weights : HeuristicWeights | None
        Heuristic weights configuration.

    Returns:
    --------
    MinimaxDecision : Dataclass containing chosen move, evaluation score, nodes visited,
                      recursive calls, max depth, candidate scores, and execution time.
    """
    start_time = time.perf_counter()
    b = _ensure_board(board)
    w = weights if weights is not None else DEFAULT_WEIGHTS
    safe_depth = max(1, min(depth, 5))

    stats = MinimaxStats(initial_depth=safe_depth)

    # Terminal check before search
    if Rules.check_win(b) is not None:
        elapsed = (time.perf_counter() - start_time) * 1000
        return MinimaxDecision(
            column=None,
            score=0.0,
            depth=safe_depth,
            nodes_visited=0,
            recursive_calls=0,
            max_depth_reached=0,
            execution_time_ms=elapsed,
            candidate_scores={},
            tree={"name": "Root", "status": "terminal_game_over"},
        )

    valid_cols = b.get_valid_columns()
    if not valid_cols:
        elapsed = (time.perf_counter() - start_time) * 1000
        return MinimaxDecision(
            column=None,
            score=0.0,
            depth=safe_depth,
            nodes_visited=0,
            recursive_calls=0,
            max_depth_reached=0,
            execution_time_ms=elapsed,
            candidate_scores={},
            tree={"name": "Root", "status": "board_full"},
        )

    # Order root columns center-first for deterministic tie-breaking
    ordered_cols = sorted(valid_cols, key=lambda c: _PREFERRED_COLUMNS.index(c))
    candidate_scores: dict[int, float] = {}
    tree_branches: list[dict[str, Any]] = []

    best_score = -float("inf")
    best_col: int = ordered_cols[0]

    stats.nodes_visited += 1

    # Evaluate each root candidate branch
    for col in ordered_cols:
        row = b.drop_disc(col, player)
        if row is not None:
            # Immediate win check for root move
            is_win, state = Rules.is_game_over_after_move(b, row, col)
            if is_win and state is not None and state.winner == player:
                score = TERMINAL_WIN_BASE + (safe_depth * 1_000.0)
            else:
                score = _minimax_recursive(
                    b,
                    depth=safe_depth - 1,
                    is_maximizing=False,
                    ai_player=player,
                    weights=w,
                    stats=stats,
                )
            b.undo_last_move()

            candidate_scores[col] = score
            tree_branches.append({
                "column": col + 1,
                "score": round(score, 2),
                "is_immediate_win": bool(is_win and state and state.winner == player),
            })

            # Strictly greater ensures deterministic tie-breaking via _PREFERRED_COLUMNS
            if score > best_score:
                best_score = score
                best_col = col

    elapsed = (time.perf_counter() - start_time) * 1000

    tree_data = {
        "depth": safe_depth,
        "chosen_column": best_col + 1,
        "branches": tree_branches,
    }

    return MinimaxDecision(
        column=best_col,
        score=best_score,
        depth=safe_depth,
        nodes_visited=stats.nodes_visited,
        recursive_calls=stats.recursive_calls,
        max_depth_reached=stats.max_depth_reached,
        execution_time_ms=elapsed,
        candidate_scores=candidate_scores,
        tree=tree_data,
    )


def choose_minimax_move(
    board: Union[Board, list[list[int]]],
    depth: int = 3,
    player: int = PLAYER2,
    weights: HeuristicWeights | None = None,
) -> int | None:
    """Convenience wrapper returning solely the chosen column (0 to 6)."""
    decision = get_minimax_decision(board, depth=depth, player=player, weights=weights)
    return decision.column
