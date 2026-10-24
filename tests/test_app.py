"""
test_app.py — Unit and integration tests for Flask API endpoints.

Covers:
- GET / (Homepage HTML)
- GET /api/status (Application health and engine status)
- GET /api/board (Initial board snapshot)
- POST /api/move (Valid moves, turn progression, error handling)
- POST /api/move edge cases (missing body, out of range col, full col, post-game)
- POST /api/reset (Game state reset)
"""

import pytest
from app import app, _reset_state
from game.board import ROWS, COLS, PLAYER1, PLAYER2


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            _reset_state()
        yield client
        with app.app_context():
            _reset_state()


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Connect-4" in response.data


def test_api_status(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["python_game_engine"] == "active"
    assert data["two_player_mode"] == "complete"


def test_api_board_initial(client):
    response = client.get("/api/board")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["grid"]) == ROWS
    assert len(data["valid_columns"]) == COLS
    assert data["current_player"] == PLAYER1
    assert data["game_over"] is False
    assert data["winner"] is None


def test_api_move_valid(client):
    response = client.post("/api/move", json={"col": 3})
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["placed_row"] == ROWS - 1
    assert data["placed_col"] == 3
    assert data["player"] == PLAYER1
    assert data["current_player"] == PLAYER2
    assert data["move_count"] == 1


def test_api_move_invalid_column(client):
    # Column out of bounds
    res_negative = client.post("/api/move", json={"col": -1})
    assert res_negative.status_code == 400
    assert "Invalid column" in res_negative.get_json()["error"]

    res_too_large = client.post("/api/move", json={"col": 10})
    assert res_too_large.status_code == 400

    # Missing column
    res_empty = client.post("/api/move", json={})
    assert res_empty.status_code == 400


def test_api_move_full_column(client):
    # Fill column 0
    for _ in range(ROWS):
        res = client.post("/api/move", json={"col": 0})
        assert res.status_code == 200

    # 7th move in column 0
    res_overflow = client.post("/api/move", json={"col": 0})
    assert res_overflow.status_code == 400
    assert "completely full" in res_overflow.get_json()["error"]


def test_api_move_post_game_rejected(client):
    # P1 connects 4 in a row horizontally
    # P1: (0, 1, 2, 3), P2: (0, 1, 2)
    # Move sequence: P1 col 0, P2 col 0, P1 col 1, P2 col 1, P1 col 2, P2 col 2, P1 col 3
    moves = [0, 0, 1, 1, 2, 2, 3]
    for col in moves:
        res = client.post("/api/move", json={"col": col})
        assert res.status_code == 200

    data = res.get_json()
    assert data["game_over"] is True
    assert data["winner"] == PLAYER1
    assert len(data["winning_cells"]) == 4

    # Subsequent move must be rejected with HTTP 400
    res_after = client.post("/api/move", json={"col": 4})
    assert res_after.status_code == 400
    assert "The game has ended" in res_after.get_json()["error"]


def test_api_reset(client):
    client.post("/api/move", json={"col": 2})
    client.post("/api/move", json={"col": 3})

    res = client.post("/api/reset")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["move_count"] == 0
    assert data["current_player"] == PLAYER1
    assert data["game_over"] is False
    assert len(data["move_history"]) == 0


def test_api_mode_switch(client):
    res = client.post("/api/mode", json={"mode": "hva", "ai_strategy": "greedy"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["game_mode"] == "hva"
    assert data["ai_strategy"] == "greedy"
    assert data["move_count"] == 0

    # Invalid mode
    res_invalid = client.post("/api/mode", json={"mode": "invalid_mode"})
    assert res_invalid.status_code == 400


def test_api_ai_move_success(client):
    # Set mode to hva
    client.post("/api/mode", json={"mode": "hva", "ai_strategy": "greedy"})

    # Human (P1) plays center column 3
    res_p1 = client.post("/api/move", json={"col": 3})
    assert res_p1.status_code == 200
    assert res_p1.get_json()["current_player"] == PLAYER2

    # Request AI move
    res_ai = client.post("/api/ai-move")
    assert res_ai.status_code == 200
    data_ai = res_ai.get_json()
    assert data_ai["success"] is True
    assert data_ai["player"] == PLAYER2
    assert data_ai["current_player"] == PLAYER1
    assert "ai_decision" in data_ai
    assert data_ai["ai_decision"]["strategy"] == "greedy"
    assert data_ai["ai_decision"]["column"] in range(COLS)


def test_api_ai_move_wrong_turn(client):
    # Fresh game: P1's turn
    res = client.post("/api/ai-move")
    assert res.status_code == 400
    assert "not the AI's turn" in res.get_json()["error"]


def test_api_move_auto_ai(client):
    # Set mode to hva
    client.post("/api/mode", json={"mode": "hva", "ai_strategy": "greedy"})

    # Post human move with auto_ai=True
    res = client.post("/api/move", json={"col": 3, "auto_ai": True})
    assert res.status_code == 200
    data = res.get_json()
    assert "ai_move" in data
    assert data["move_count"] == 2
    assert data["current_player"] == PLAYER1


def test_api_mode_switch_minimax_with_depth(client):
    res = client.post("/api/mode", json={"mode": "hva", "ai_strategy": "minimax", "depth": 4})
    assert res.status_code == 200
    data = res.get_json()
    assert data["game_mode"] == "hva"
    assert data["ai_strategy"] == "minimax"
    assert data["ai_depth"] == 4


def test_api_minimax_move_success(client):
    # Set mode to hva with minimax at depth 2
    client.post("/api/mode", json={"mode": "hva", "ai_strategy": "minimax", "depth": 2})

    # P1 plays col 3
    res_p1 = client.post("/api/move", json={"col": 3})
    assert res_p1.status_code == 200

    # Request AI move
    res_ai = client.post("/api/ai-move")
    assert res_ai.status_code == 200
    data = res_ai.get_json()
    assert data["success"] is True
    assert data["player"] == PLAYER2
    assert "ai_decision" in data
    decision = data["ai_decision"]
    assert decision["strategy"] == "minimax"
    assert decision["column"] in range(COLS)
    assert decision["depth"] == 2
    assert decision["nodes_visited"] > 0
    assert decision["recursive_calls"] > 0
    assert decision["max_depth_reached"] >= 1
    assert "tree" in decision
    assert len(decision["tree"]["branches"]) == COLS


def test_api_minimax_auto_ai(client):
    # Set mode to hva with minimax at depth 2
    client.post("/api/mode", json={"mode": "hva", "ai_strategy": "minimax", "depth": 2})

    # Human plays col 3 with auto_ai=True
    res = client.post("/api/move", json={"col": 3, "auto_ai": True})
    assert res.status_code == 200
    data = res.get_json()
    assert "ai_move" in data
    assert data["move_count"] == 2
    assert data["ai_decision"]["strategy"] == "minimax"


