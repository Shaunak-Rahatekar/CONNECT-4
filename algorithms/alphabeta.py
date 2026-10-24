"""
alphabeta.py — Alpha-Beta Pruning AI for Connect-4.

Implements the Alpha-Beta Pruning optimization over the Minimax game-tree search.

Theoretical Foundations (DAA Unit II & IV):
--------------------------------------------
Alpha-Beta Pruning is an adversarial search optimization that computes the identical
subgame-perfect minimax value while eliminating (pruning) branches that cannot influence
the final decision.

Core Invariant:
---------------
Let [α, β] be the current search window:
- α (alpha): the minimum score the maximizing player is guaranteed to achieve.
- β (beta):  the maximum score the minimizing player allows the maximizing player to achieve.

Pruning Condition:
------------------
Whenever a child node returns a value such that:
    β ≤ α
the parent node immediately terminates exploration of its remaining siblings (cutoff).
- At a MAX node: if val ≥ β, the minimizing ancestor above would never choose this branch;
  hence remaining siblings are pruned.
- At a MIN node: if val ≤ α, the maximizing ancestor above already has a superior choice;
  hence remaining siblings are pruned.

Why Alpha-Beta Preserves the Minimax Value:
-------------------------------------------
Pruning only discards branches whose values are mathematically proven to be dominated by
an already-evaluated alternative. Therefore:
    V_alphabeta(s, d) ≡ V_minimax(s, d)
The chosen move is guaranteed to achieve the same minimax-optimal evaluation.

Move Ordering & Complexity:
---------------------------
- Worst-Case Time Complexity: O(b^d)
  Occurs when moves are evaluated worst-to-first, resulting in 0 cutoffs.
- Best-Case Time Complexity: O(b^(d/2))
  Occurs when the optimal move is always evaluated first. The effective branching factor
  drops from b to √b (for Connect-4, from ~7 down to ~2.65).
  Under best-case ordering, search depth can be doubled within the same computational budget.
- Space Complexity: O(d)
  Depth-first search with in-place backtracking (`board.drop_disc()` / `board.undo_last_move()`).
  Requires zero heap allocations for board cloning.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Union

from game.board import Board, ROWS, COLS, PLAYER1, PLAYER2
from game.rules import Rules
from algorithms.evaluation import evaluate_board, HeuristicWeights, DEFAULT_WEIGHTS
from algorithms.minimax import TERMINAL_WIN_BASE, _ensure_board

# Center-outward column preference for Connect-4
_CENTER_FIRST_COLUMNS: tuple[int, ...] = (3, 2, 4, 1, 5, 0, 6)


@dataclass
class AlphaBetaStats:
    """Tracker for search statistics and pruning efficiency."""
    initial_depth: int
    nodes_visited: int = 0
    recursive_calls: int = 0
    cutoffs: int = 0
    max_depth_reached: int = 0


@dataclass
class AlphaBetaDecision:
    """Authoritative structured output from an Alpha-Beta search."""
    column: int | None
    score: float
    depth: int
    nodes_visited: int
    recursive_calls: int
    cutoffs: int
    max_depth_reached: int
    execution_time_ms: float
    use_move_ordering: bool
    candidate_scores: dict[int, float]
    tree: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": "alphabeta",
            "column": self.column,
            "score": round(self.score, 2),
            "depth": self.depth,
            "nodes_visited": self.nodes_visited,
            "recursive_calls": self.recursive_calls,
            "cutoffs": self.cutoffs,
            "max_depth_reached": self.max_depth_reached,
            "execution_time_ms": round(self.execution_time_ms, 3),
            "use_move_ordering": self.use_move_ordering,
            "candidate_scores": {str(c): round(s, 2) for c, s in self.candidate_scores.items()},
            "tree": self.tree,
        }


def order_candidate_columns(
    board: Board,
    valid_cols: list[int],
    current_player: int,
    use_ordering: bool,
) -> list[int]:
    """Order candidate columns to optimize alpha-beta cutoff frequency.

    Ordering Strategy:
    1. If `use_ordering` is False:
       Return columns in natural numerical order [0, 1, ..., 6] for baseline comparison.
    2. If `use_ordering` is True:
       - Immediate winning moves for current player placed first (priority 10,000).
       - Immediate blocking moves (opponent wins if they play here) placed second (priority 5,000).
       - Center-to-flank bias: columns closer to center (col 3) placed earlier.
    """
    if not use_ordering:
        return sorted(valid_cols)

    opponent = Rules.opponent(current_player)

    scored_cols: list[tuple[float, int]] = []
    for col in valid_cols:
        priority = 0.0

        # Center proximity bonus (col 3 gets +60, cols 2/4 get +40, cols 1/5 get +20, cols 0/6 get 0)
        center_dist = abs(col - 3)
        priority += (3 - center_dist) * 20.0

        # Check immediate win
        row = board.drop_disc(col, current_player)
        if row is not None:
            is_win, state = Rules.is_game_over_after_move(board, row, col)
            board.undo_last_move()
            if is_win and state is not None and state.winner == current_player:
                priority += 10_000.0

        # Check immediate block (opponent win)
        opp_row = board.drop_disc(col, opponent)
        if opp_row is not None:
            is_opp_win, opp_state = Rules.is_game_over_after_move(board, opp_row, col)
            board.undo_last_move()
            if is_opp_win and opp_state is not None and opp_state.winner == opponent:
                priority += 5_000.0

        scored_cols.append((priority, col))

    # Sort descending by priority. When priorities tie, center-to-flank order breaks tie
    scored_cols.sort(key=lambda item: (item[0], -_CENTER_FIRST_COLUMNS.index(item[1])), reverse=True)
    return [col for _, col in scored_cols]


def _alphabeta_recursive(
    board: Board,
    depth: int,
    alpha: float,
    beta: float,
    is_maximizing: bool,
    ai_player: int,
    weights: HeuristicWeights,
    use_move_ordering: bool,
    stats: AlphaBetaStats,
) -> float:
    """Recursive core of the Alpha-Beta Pruning algorithm.

    Maintains alpha and beta bounds and terminates search early when beta <= alpha.
    """
    stats.nodes_visited += 1
    current_ply = stats.initial_depth - depth
    if current_ply > stats.max_depth_reached:
        stats.max_depth_reached = current_ply

    opponent = Rules.opponent(ai_player)

    # 1. Terminal State Check
    win_state = Rules.check_win(board)
    if win_state is not None:
        if win_state.winner == ai_player:
            return TERMINAL_WIN_BASE + (depth * 1_000.0)
        else:
            return -TERMINAL_WIN_BASE - (depth * 1_000.0)

    valid_cols = board.get_valid_columns()
    if not valid_cols:
        return 0.0  # Draw

    # 2. Depth Limit Cut-off: Heuristic evaluation
    if depth == 0:
        return evaluate_board(board, player=ai_player, weights=weights)

    current_player = ai_player if is_maximizing else opponent
    ordered_cols = order_candidate_columns(board, valid_cols, current_player, use_move_ordering)

    stats.recursive_calls += 1

    if is_maximizing:
        max_eval = -float("inf")
        for col in ordered_cols:
            row = board.drop_disc(col, ai_player)
            if row is not None:
                # Fast immediate win check
                is_win, state = Rules.is_game_over_after_move(board, row, col)
                if is_win and state is not None and state.winner == ai_player:
                    eval_val = TERMINAL_WIN_BASE + (depth * 1_000.0)
                else:
                    eval_val = _alphabeta_recursive(
                        board,
                        depth=depth - 1,
                        alpha=alpha,
                        beta=beta,
                        is_maximizing=False,
                        ai_player=ai_player,
                        weights=weights,
                        use_move_ordering=use_move_ordering,
                        stats=stats,
                    )
                board.undo_last_move()

                if eval_val > max_eval:
                    max_eval = eval_val

                alpha = max(alpha, eval_val)
                # Beta Cutoff: Minimizer already has an alternative guaranteeing a score <= beta
                if beta <= alpha:
                    stats.cutoffs += 1
                    break
        return max_eval
    else:
        min_eval = float("inf")
        for col in ordered_cols:
            row = board.drop_disc(col, opponent)
            if row is not None:
                # Fast immediate loss check
                is_win, state = Rules.is_game_over_after_move(board, row, col)
                if is_win and state is not None and state.winner == opponent:
                    eval_val = -TERMINAL_WIN_BASE - (depth * 1_000.0)
                else:
                    eval_val = _alphabeta_recursive(
                        board,
                        depth=depth - 1,
                        alpha=alpha,
                        beta=beta,
                        is_maximizing=True,
                        ai_player=ai_player,
                        weights=weights,
                        use_move_ordering=use_move_ordering,
                        stats=stats,
                    )
                board.undo_last_move()

                if eval_val < min_eval:
                    min_eval = eval_val

                beta = min(beta, eval_val)
                # Alpha Cutoff: Maximizer already has an alternative guaranteeing a score >= alpha
                if beta <= alpha:
                    stats.cutoffs += 1
                    break
        return min_eval


def get_alphabeta_decision(
    board: Union[Board, list[list[int]]],
    depth: int = 3,
    player: int = PLAYER2,
    use_move_ordering: bool = True,
    weights: HeuristicWeights | None = None,
) -> AlphaBetaDecision:
    """Execute depth-bounded Alpha-Beta Pruning search and return structured statistics.

    Parameters:
    -----------
    board : Board or list[list[int]]
        The Connect-4 board state.
    depth : int
        Search depth limit (default 3, range 1 to 5).
    player : int
        The maximizing player (PLAYER1 or PLAYER2). Defaults to PLAYER2.
    use_move_ordering : bool
        If True, optimizes move ordering (wins first, blocks second, center-bias).
        If False, explores columns in raw ascending index order for comparison.
    weights : HeuristicWeights | None
        Heuristic weights configuration.

    Returns:
    --------
    AlphaBetaDecision : Dataclass with chosen move, evaluation score, nodes visited,
                        recursive calls, cutoffs, max depth, candidate scores, and timing.
    """
    start_time = time.perf_counter()
    b = _ensure_board(board)
    w = weights if weights is not None else DEFAULT_WEIGHTS
    safe_depth = max(1, min(depth, 5))

    stats = AlphaBetaStats(initial_depth=safe_depth)

    # Terminal check before search
    if Rules.check_win(b) is not None:
        elapsed = (time.perf_counter() - start_time) * 1000
        return AlphaBetaDecision(
            column=None,
            score=0.0,
            depth=safe_depth,
            nodes_visited=0,
            recursive_calls=0,
            cutoffs=0,
            max_depth_reached=0,
            execution_time_ms=elapsed,
            use_move_ordering=use_move_ordering,
            candidate_scores={},
            tree={"name": "Root", "status": "terminal_game_over"},
        )

    valid_cols = b.get_valid_columns()
    if not valid_cols:
        elapsed = (time.perf_counter() - start_time) * 1000
        return AlphaBetaDecision(
            column=None,
            score=0.0,
            depth=safe_depth,
            nodes_visited=0,
            recursive_calls=0,
            cutoffs=0,
            max_depth_reached=0,
            execution_time_ms=elapsed,
            use_move_ordering=use_move_ordering,
            candidate_scores={},
            tree={"name": "Root", "status": "board_full"},
        )

    # Order root columns
    ordered_cols = order_candidate_columns(b, valid_cols, player, use_move_ordering)
    candidate_scores: dict[int, float] = {}
    tree_branches: list[dict[str, Any]] = []

    best_score = -float("inf")
    best_col: int = ordered_cols[0]

    alpha = -float("inf")
    beta = float("inf")

    stats.nodes_visited += 1

    # Evaluate each root candidate branch
    for col in ordered_cols:
        row = b.drop_disc(col, player)
        if row is not None:
            is_win, state = Rules.is_game_over_after_move(b, row, col)
            if is_win and state is not None and state.winner == player:
                score = TERMINAL_WIN_BASE + (safe_depth * 1_000.0)
            else:
                score = _alphabeta_recursive(
                    b,
                    depth=safe_depth - 1,
                    alpha=alpha,
                    beta=beta,
                    is_maximizing=False,
                    ai_player=player,
                    weights=w,
                    use_move_ordering=use_move_ordering,
                    stats=stats,
                )
            b.undo_last_move()

            candidate_scores[col] = score
            tree_branches.append({
                "column": col + 1,
                "score": round(score, 2),
                "is_immediate_win": bool(is_win and state and state.winner == player),
            })

            # Update best move and alpha bound
            if score > best_score:
                best_score = score
                best_col = col

            alpha = max(alpha, score)

    elapsed = (time.perf_counter() - start_time) * 1000

    tree_data = {
        "depth": safe_depth,
        "chosen_column": best_col + 1,
        "use_move_ordering": use_move_ordering,
        "branches": tree_branches,
    }

    return AlphaBetaDecision(
        column=best_col,
        score=best_score,
        depth=safe_depth,
        nodes_visited=stats.nodes_visited,
        recursive_calls=stats.recursive_calls,
        cutoffs=stats.cutoffs,
        max_depth_reached=stats.max_depth_reached,
        execution_time_ms=elapsed,
        use_move_ordering=use_move_ordering,
        candidate_scores=candidate_scores,
        tree=tree_data,
    )


def choose_alphabeta_move(
    board: Union[Board, list[list[int]]],
    depth: int = 3,
    player: int = PLAYER2,
    use_move_ordering: bool = True,
    weights: HeuristicWeights | None = None,
) -> int | None:
    """Convenience wrapper returning solely the chosen column (0 to 6)."""
    decision = get_alphabeta_decision(
        board,
        depth=depth,
        player=player,
        use_move_ordering=use_move_ordering,
        weights=weights,
    )
    return decision.column
