"""
app.py — Flask entry point for the Connect-4 DAA web application.

Routes
------
GET  /                → homepage (game board)
GET  /api/status      → JSON health-check and engine status
GET  /api/board       → JSON snapshot of the current board state
POST /api/mode        → configure game mode (hvh / hva) and AI strategy
POST /api/reset       → reset the active game session
POST /api/move        → apply a player move (column sent as JSON)
POST /api/ai-move     → calculate and execute an authoritative AI move

Authoritative Model
-------------------
All game logic, turn progression, and AI decisions are computed server-side in
Python. The browser interface renders snapshots received from the API and never
directly dictates game outcomes.
"""

from __future__ import annotations
from typing import Any

from flask import Flask, jsonify, render_template, request, session

from game.board import Board, ROWS, COLS, PLAYER1, PLAYER2
from game.rules import Rules
from algorithms.greedy import get_greedy_decision, GreedyDecision
from algorithms.minimax import get_minimax_decision, MinimaxDecision
from algorithms.alphabeta import get_alphabeta_decision, AlphaBetaDecision
from algorithms.comparison import compare_algorithms
from benchmarks import (
    list_positions,
    get_position,
    run_position_benchmark,
    run_depth_scaling_benchmark,
)

app: Flask = Flask(__name__)
# Secret key enables Flask session cookies.
app.secret_key = "connect4-daa-dev-key-change-in-production"

# ---------------------------------------------------------------------------
# Module-level game state
# ---------------------------------------------------------------------------
_board: Board = Board()
_game_over: bool = False
_winner: int | None = None
_winning_cells: list[tuple[int, int]] = []
_is_draw: bool = False
_game_mode: str = "hvh"            # "hvh" (local 2-player) or "hva" (human vs AI)
_ai_strategy: str = "alphabeta"    # active AI strategy: "greedy" | "minimax" | "alphabeta"
_ai_depth: int = 3                 # search depth limit (1-5)
_use_move_ordering: bool = True       # enable move ordering optimization for Alpha-Beta
_use_transposition_table: bool = True  # enable memoization via transposition table
_ai_player: int = PLAYER2             # AI plays as Player 2 (Yellow)
_last_ai_decision: dict[str, Any] | None = None


def _reset_state(keep_mode: bool = True) -> None:
    """Reset all module-level game variables to their initial state."""
    global _board, _game_over, _winner, _winning_cells, _is_draw, _last_ai_decision
    _board = Board()
    _game_over = False
    _winner = None
    _winning_cells = []
    _is_draw = False
    _last_ai_decision = None


def _compute_ai_decision() -> GreedyDecision | MinimaxDecision | AlphaBetaDecision:
    """Compute authoritative AI move using currently configured strategy and depth."""
    if _ai_strategy == "alphabeta":
        return get_alphabeta_decision(
            _board,
            depth=_ai_depth,
            player=_ai_player,
            use_move_ordering=_use_move_ordering,
            use_transposition_table=_use_transposition_table,
        )
    elif _ai_strategy == "minimax":
        return get_minimax_decision(_board, depth=_ai_depth, player=_ai_player)
    return get_greedy_decision(_board, player=_ai_player)


def _board_snapshot() -> dict[str, Any]:
    """Return an authoritative JSON-serialisable dictionary of the game state."""
    win_status = "win" if _winner else ("draw" if _is_draw else "in_progress")
    valid_cols = [] if _game_over else _board.get_valid_columns()
    return {
        "grid": _board.to_list(),
        "current_player": _board.current_player,
        "move_count": _board.move_count,
        "valid_columns": valid_cols,
        "game_over": _game_over,
        "winner": _winner,
        "winning_cells": _winning_cells,
        "is_draw": _is_draw,
        "status": win_status,
        "move_history": _board.get_move_history(),
        "game_mode": _game_mode,
        "ai_strategy": _ai_strategy,
        "ai_depth": _ai_depth,
        "use_move_ordering": _use_move_ordering,
        "use_transposition_table": _use_transposition_table,
        "ai_player": _ai_player,
        "ai_decision": _last_ai_decision,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index() -> str:
    """Serve the Connect-4 homepage."""
    return render_template("index.html")


@app.route("/api/status")
def api_status() -> object:
    """Health-check endpoint — confirms application and AI modules are active."""
    return jsonify({
        "status": "ok",
        "application": "Connect-4 DAA",
        "version": "1.0.0-milestone-6",
        "python_game_engine": "active",
        "two_player_mode": "complete",
        "supported_modes": ["hvh", "hva"],
        "supported_strategies": ["greedy", "minimax", "alphabeta"],
        "active_ai_strategy": _ai_strategy,
        "ai_depth": _ai_depth,
        "use_move_ordering": _use_move_ordering,
        "use_transposition_table": _use_transposition_table,
        "greedy_ai": "active",
        "minimax_ai": "active",
        "alphabeta_ai": "active",
        "transposition_table": "active",
    })


@app.route("/api/board")
def api_board() -> object:
    """Return the current board state as JSON."""
    return jsonify(_board_snapshot())


@app.route("/api/mode", methods=["POST"])
def api_mode() -> object:
    """Configure game mode ('hvh' or 'hva'), AI strategy, search depth, move ordering, and caching.

    Expected JSON body:
        {"mode": "hvh" | "hva", "ai_strategy": "greedy" | "minimax" | "alphabeta", "depth": <1-5>, "use_move_ordering": <bool>, "use_transposition_table": <bool>}
    Resets the board to ensure a clean match under the new mode.
    """
    global _game_mode, _ai_strategy, _ai_depth, _use_move_ordering, _use_transposition_table
    data = request.get_json(silent=True) or {}
    new_mode = data.get("mode")
    new_strategy = data.get("ai_strategy", _ai_strategy)
    new_depth = data.get("depth")
    new_ordering = data.get("use_move_ordering")
    new_tt = data.get("use_transposition_table")

    if new_mode not in ("hvh", "hva"):
        return jsonify({"error": f"Invalid mode '{new_mode}'. Must be 'hvh' or 'hva'."}), 400

    _game_mode = new_mode
    if new_strategy in ("greedy", "minimax", "alphabeta"):
        _ai_strategy = new_strategy

    if isinstance(new_depth, int) and 1 <= new_depth <= 5:
        _ai_depth = new_depth

    if isinstance(new_ordering, bool):
        _use_move_ordering = new_ordering

    if isinstance(new_tt, bool):
        _use_transposition_table = new_tt

    _reset_state(keep_mode=True)
    return jsonify({
        "success": True,
        "message": f"Game mode set to {_game_mode} ({_ai_strategy}, depth {_ai_depth}).",
        **_board_snapshot(),
    })


@app.route("/api/compare", methods=["POST"])
def api_compare() -> object:
    """Run an empirical comparison of Minimax, Alpha-Beta (natural), and Alpha-Beta (ordered).

    Expected optional JSON body: {"depth": <int 1-5>, "repeats": <int 1-10>}
    """
    data = request.get_json(silent=True) or {}
    depth = data.get("depth", _ai_depth)
    repeats = data.get("repeats", 1)
    try:
        depth = int(depth)
    except (ValueError, TypeError):
        depth = _ai_depth
    try:
        repeats = int(repeats)
    except (ValueError, TypeError):
        repeats = 1

    report = compare_algorithms(_board, depth=depth, player=_ai_player, repeats=repeats)
    return jsonify({"success": True, **report})


@app.route("/api/benchmark/positions")
def api_benchmark_positions() -> object:
    """Return available saved benchmark positions."""
    return jsonify({"success": True, "ok": True, "positions": list_positions()})


@app.route("/api/benchmark/run", methods=["POST"])
def api_benchmark_run() -> object:
    """Execute reproducible performance benchmark across algorithms.

    Expected JSON body:
        {"position_id": "opening_center" | "tactical_block" | ..., "depth": <1-4>, "repeats": <1-5>}
    Guarantees the live game board state is never modified.
    """
    data = request.get_json(silent=True) or {}
    pos_id = data.get("position_id", "opening_center")
    depth = data.get("depth", 3)
    repeats = data.get("repeats", 3)
    try:
        depth = int(depth)
    except (ValueError, TypeError):
        depth = 3
    depth = max(1, min(depth, 4))

    try:
        repeats = int(repeats)
    except (ValueError, TypeError):
        repeats = 3
    repeats = max(1, min(repeats, 5))

    if pos_id == "live":
        from benchmarks.positions import BenchmarkPosition
        live_clone = _board.copy()
        live_pos = BenchmarkPosition(
            id="live",
            name="Current Live Board State",
            description=f"Authoritative live board snapshot with {_board.move_count} moves played",
            phase="Live Match",
            player_to_move=_board.current_player,
            builder=lambda: live_clone.copy(),
        )
        report = run_position_benchmark(live_pos, depth=depth, repeats=repeats)
    else:
        report = run_position_benchmark(pos_id, depth=depth, repeats=repeats)

    KEY_MAP = {
        "minimax": "minimax",
        "alphabeta_no_ordering": "alphabeta_natural",
        "alphabeta_with_ordering": "alphabeta_ordered",
        "alphabeta_with_tt": "alphabeta_tt",
    }
    raw_results = report.get("results", {})
    results_list = [
        {"algorithm_key": KEY_MAP.get(k, k), "original_key": k, **v}
        for k, v in raw_results.items()
    ]
    return jsonify({
        **report,
        "success": True,
        "ok": True,
        "results": results_list,
        "raw_results": raw_results,
    })


@app.route("/api/benchmark/scaling", methods=["POST"])
def api_benchmark_scaling() -> object:
    """Execute depth-scaling benchmark generating multi-series chart datasets.

    Expected JSON body:
        {"position_id": "opening_center", "max_depth": <1-4>, "repeats": <1-3>}
    """
    data = request.get_json(silent=True) or {}
    pos_id = data.get("position_id", "opening_center")
    max_depth = data.get("max_depth", 4)
    repeats = data.get("repeats", 2)
    try:
        max_depth = int(max_depth)
    except (ValueError, TypeError):
        max_depth = 4
    max_depth = max(1, min(max_depth, 4))

    try:
        repeats = int(repeats)
    except (ValueError, TypeError):
        repeats = 2
    repeats = max(1, min(repeats, 3))

    if pos_id == "live":
        from benchmarks.positions import BenchmarkPosition
        live_clone = _board.copy()
        live_pos = BenchmarkPosition(
            id="live",
            name="Current Live Board State",
            description=f"Authoritative live board snapshot with {_board.move_count} moves played",
            phase="Live Match",
            player_to_move=_board.current_player,
            builder=lambda: live_clone.copy(),
        )
        scaling_report = run_depth_scaling_benchmark(position_id=live_pos, max_depth=max_depth, repeats=repeats)
    else:
        scaling_report = run_depth_scaling_benchmark(position_id=pos_id, max_depth=max_depth, repeats=repeats)

    return jsonify({
        "success": True,
        "ok": True,
        "scaling": scaling_report,
        **scaling_report,
    })



@app.route("/api/reset", methods=["POST"])
def api_reset() -> object:
    """Reset the game to its initial state."""
    global _game_mode
    data = request.get_json(silent=True) or {}
    if "mode" in data and data["mode"] in ("hvh", "hva"):
        _game_mode = data["mode"]

    _reset_state(keep_mode=True)
    return jsonify({"success": True, "message": "Game reset.", **_board_snapshot()})


@app.route("/api/move", methods=["POST"])
def api_move() -> object:
    """Apply an authoritative player move.

    Expected JSON body:
        {"col": <int 0-6>, "auto_ai": <bool optional>}

    If auto_ai is True and mode is 'hva', immediately computes and applies the
    AI response move within the same call.
    """
    global _game_over, _winner, _winning_cells, _is_draw, _last_ai_decision

    if _game_over:
        return jsonify({
            "error": "The game has ended. Click 'New Game' to play again.",
            **_board_snapshot(),
        }), 400

    data = request.get_json(silent=True) or {}
    col = data.get("col")
    auto_ai = bool(data.get("auto_ai", False))

    if col is None or not isinstance(col, int) or col < 0 or col >= COLS:
        return jsonify({
            "error": f"Invalid column '{col}'. Column must be an integer between 1 and {COLS}.",
            **_board_snapshot(),
        }), 400

    if not _board.is_valid_column(col):
        return jsonify({
            "error": f"Column {col + 1} is completely full! Choose another column.",
            **_board_snapshot(),
        }), 400

    player = _board.current_player
    row = Rules.apply_move(_board, col)

    if row is None:
        return jsonify({
            "error": "Move could not be applied by the game engine.",
            **_board_snapshot(),
        }), 400

    # Check for win or draw after this move
    over, state = Rules.is_game_over_after_move(_board, row, col)
    if over and state is not None:
        _game_over = True
        _winner = state.winner
        _winning_cells = list(state.winning_cells)
        _is_draw = state.is_draw

    response_data: dict[str, Any] = {
        "success": True,
        "placed_row": row,
        "placed_col": col,
        "player": player,
        **_board_snapshot(),
    }

    # If auto_ai is requested, game continues, and it is AI's turn
    if auto_ai and not _game_over and _game_mode == "hva" and _board.current_player == _ai_player:
        ai_decision = _compute_ai_decision()
        if ai_decision.column is not None:
            ai_row = Rules.apply_move(_board, ai_decision.column)
            _last_ai_decision = ai_decision.to_dict()
            ai_over, ai_state = Rules.is_game_over_after_move(_board, ai_row, ai_decision.column)
            if ai_over and ai_state is not None:
                _game_over = True
                _winner = ai_state.winner
                _winning_cells = list(ai_state.winning_cells)
                _is_draw = ai_state.is_draw
            response_data["ai_move"] = {
                "placed_row": ai_row,
                "placed_col": ai_decision.column,
                "player": _ai_player,
            }
            response_data.update(_board_snapshot())

    return jsonify(response_data)


@app.route("/api/ai-move", methods=["POST"])
def api_ai_move() -> object:
    """Execute an authoritative AI move using the configured strategy."""
    global _game_over, _winner, _winning_cells, _is_draw, _last_ai_decision

    if _game_over:
        return jsonify({
            "error": "The game has already ended. Click 'New Game' to play again.",
            **_board_snapshot(),
        }), 400

    if _board.current_player != _ai_player:
        return jsonify({
            "error": f"It is not the AI's turn (Current player: {_board.current_player}).",
            **_board_snapshot(),
        }), 400

    decision = _compute_ai_decision()
    if decision.column is None:
        return jsonify({
            "error": "No legal moves available for AI.",
            **_board_snapshot(),
        }), 400

    ai_col = decision.column
    ai_row = Rules.apply_move(_board, ai_col)
    _last_ai_decision = decision.to_dict()

    if ai_row is None:
        return jsonify({
            "error": "AI move could not be applied.",
            **_board_snapshot(),
        }), 400

    over, state = Rules.is_game_over_after_move(_board, ai_row, ai_col)
    if over and state is not None:
        _game_over = True
        _winner = state.winner
        _winning_cells = list(state.winning_cells)
        _is_draw = state.is_draw

    return jsonify({
        "success": True,
        "placed_row": ai_row,
        "placed_col": ai_col,
        "player": _ai_player,
        "ai_decision": _last_ai_decision,
        **_board_snapshot(),
    })


# ---------------------------------------------------------------------------
# Development entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
