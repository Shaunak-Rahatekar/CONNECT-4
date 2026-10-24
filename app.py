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
_ai_strategy: str = "greedy"       # active AI strategy: "greedy" | "minimax"
_ai_depth: int = 3                 # search depth limit for Minimax (1-4)
_ai_player: int = PLAYER2          # AI plays as Player 2 (Yellow)
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


def _compute_ai_decision() -> GreedyDecision | MinimaxDecision:
    """Compute authoritative AI move using currently configured strategy and depth."""
    if _ai_strategy == "minimax":
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
        "version": "1.0.0-milestone-4",
        "python_game_engine": "active",
        "two_player_mode": "complete",
        "supported_modes": ["hvh", "hva"],
        "supported_strategies": ["greedy", "minimax"],
        "active_ai_strategy": _ai_strategy,
        "ai_depth": _ai_depth,
        "greedy_ai": "active",
        "minimax_ai": "active",
    })


@app.route("/api/board")
def api_board() -> object:
    """Return the current board state as JSON."""
    return jsonify(_board_snapshot())


@app.route("/api/mode", methods=["POST"])
def api_mode() -> object:
    """Configure game mode ('hvh' or 'hva'), AI strategy, and search depth.

    Expected JSON body:
        {"mode": "hvh" | "hva", "ai_strategy": "greedy" | "minimax", "depth": <1-4>}
    Resets the board to ensure a clean match under the new mode.
    """
    global _game_mode, _ai_strategy, _ai_depth
    data = request.get_json(silent=True) or {}
    new_mode = data.get("mode")
    new_strategy = data.get("ai_strategy", _ai_strategy)
    new_depth = data.get("depth")

    if new_mode not in ("hvh", "hva"):
        return jsonify({"error": f"Invalid mode '{new_mode}'. Must be 'hvh' or 'hva'."}), 400

    _game_mode = new_mode
    if new_strategy in ("greedy", "minimax"):
        _ai_strategy = new_strategy

    if isinstance(new_depth, int) and 1 <= new_depth <= 4:
        _ai_depth = new_depth

    _reset_state(keep_mode=True)
    return jsonify({
        "success": True,
        "message": f"Game mode set to {_game_mode} ({_ai_strategy}, depth {_ai_depth}).",
        **_board_snapshot(),
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
