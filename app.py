"""
app.py — Flask entry point for the Connect-4 DAA web application.

Routes
------
GET  /                → homepage (game board)
GET  /api/status      → JSON health-check for the application
GET  /api/board       → JSON snapshot of the current board state
POST /api/reset       → reset the active game session
POST /api/move        → apply a human move (column sent as JSON)

The game engine (game.board, game.rules) is imported directly; no
database or external service is required.

Session-per-user state
-----------------------
For this initial milestone a single in-memory Board instance is used.
Multi-user session isolation will be added if a later requirement demands
it; the current goal is a working, playable application for one session.
"""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request, session

from game.board import Board, PLAYER1, PLAYER2
from game.rules import Rules

app: Flask = Flask(__name__)
# Secret key enables Flask session cookies (in-browser state per tab).
app.secret_key = "connect4-daa-dev-key-change-in-production"

# ---------------------------------------------------------------------------
# Module-level game state (single active game for development purposes)
# ---------------------------------------------------------------------------
_board: Board = Board()
_game_over: bool = False
_winner: int | None = None
_winning_cells: list[tuple[int, int]] = []
_is_draw: bool = False
_move_history: list[dict] = []   # [{player, col, row, move_number}, …]


def _reset_state() -> None:
    """Reset all module-level game variables to their initial state."""
    global _board, _game_over, _winner, _winning_cells, _is_draw, _move_history
    _board = Board()
    _game_over = False
    _winner = None
    _winning_cells = []
    _is_draw = False
    _move_history = []


def _board_snapshot() -> dict:
    """Return a JSON-serialisable dictionary of the current game state."""
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
    """Health-check endpoint — confirms the server is running."""
    return jsonify({
        "status": "ok",
        "application": "Connect-4 DAA",
        "version": "1.0.0-milestone-2",
        "python_game_engine": "active",
        "two_player_mode": "complete",
    })


@app.route("/api/board")
def api_board() -> object:
    """Return the current board state as JSON."""
    return jsonify(_board_snapshot())


@app.route("/api/reset", methods=["POST"])
def api_reset() -> object:
    """Reset the game to its initial state."""
    _reset_state()
    return jsonify({"success": True, "message": "Game reset.", **_board_snapshot()})


@app.route("/api/move", methods=["POST"])
def api_move() -> object:
    """Apply an authoritative human player move.

    Expected JSON body: {"col": <int 0-6>}

    Returns the updated board state plus move metadata.
    Error cases return HTTP 400 with an authoritative error message.
    """
    global _game_over, _winner, _winning_cells, _is_draw

    if _game_over:
        return jsonify({
            "error": "The game has ended. Click 'New Game' to play again.",
            **_board_snapshot(),
        }), 400

    data = request.get_json(silent=True) or {}
    col = data.get("col")

    if col is None or not isinstance(col, int) or col < 0 or col >= 7:
        return jsonify({
            "error": f"Invalid column: '{col}'. Column must be an integer between 1 and 7.",
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

    # Record history entry
    _move_history.append({
        "move_number": _board.move_count,
        "player": player,
        "col": col,
        "row": row,
    })

    # Check for win or draw after this move
    over, state = Rules.is_game_over_after_move(_board, row, col)
    if over and state is not None:
        _game_over = True
        _winner = state.winner
        _winning_cells = list(state.winning_cells)
        _is_draw = state.is_draw

    return jsonify({
        "success": True,
        "placed_row": row,
        "placed_col": col,
        "player": player,
        **_board_snapshot(),
    })


# ---------------------------------------------------------------------------
# Development entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
