"""
tests/test_netlify.py — Unit and integration tests for Netlify Serverless Function adapter.
"""

from __future__ import annotations

import json
from netlify.functions.app import handler, build_wsgi_environ


def test_build_wsgi_environ_defaults():
    event = {"httpMethod": "GET", "path": "/"}
    environ = build_wsgi_environ(event)
    assert environ["REQUEST_METHOD"] == "GET"
    assert environ["PATH_INFO"] == "/"
    assert environ["SERVER_NAME"] == "localhost"
    assert environ["CONTENT_LENGTH"] == "0"


def test_build_wsgi_environ_with_headers_and_body():
    event = {
        "httpMethod": "POST",
        "path": "/api/move",
        "headers": {
            "Content-Type": "application/json",
            "X-Forwarded-Proto": "https",
            "Host": "connect4.netlify.app",
        },
        "body": json.dumps({"col": 3}),
    }
    environ = build_wsgi_environ(event)
    assert environ["REQUEST_METHOD"] == "POST"
    assert environ["PATH_INFO"] == "/api/move"
    assert environ["CONTENT_TYPE"] == "application/json"
    assert environ["HTTP_X_FORWARDED_PROTO"] == "https"
    assert environ["SERVER_NAME"] == "connect4.netlify.app"
    assert int(environ["CONTENT_LENGTH"]) > 0


def test_netlify_handler_homepage():
    event = {"httpMethod": "GET", "path": "/"}
    res = handler(event)
    assert res["statusCode"] == 200
    assert "Connect-4" in res["body"]
    assert res["isBase64Encoded"] is False


def test_netlify_handler_api_status():
    event = {"httpMethod": "GET", "path": "/api/status"}
    res = handler(event)
    assert res["statusCode"] == 200
    data = json.loads(res["body"])
    assert data["status"] == "ok"
    assert data["application"] == "Connect-4 DAA"


def test_netlify_handler_api_board():
    event = {"httpMethod": "GET", "path": "/api/board"}
    res = handler(event)
    assert res["statusCode"] == 200
    data = json.loads(res["body"])
    assert "grid" in data
    assert len(data["grid"]) == 6
    assert len(data["grid"][0]) == 7


def test_netlify_handler_api_move_and_reset():
    # Make a move
    move_event = {
        "httpMethod": "POST",
        "path": "/api/move",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"col": 3}),
    }
    res = handler(move_event)
    assert res["statusCode"] == 200
    data = json.loads(res["body"])
    assert data["grid"][5][3] == 1  # Bottom row index 5 of column 3

    # Reset
    reset_event = {
        "httpMethod": "POST",
        "path": "/api/reset",
    }
    res_reset = handler(reset_event)
    assert res_reset["statusCode"] == 200
    data_reset = json.loads(res_reset["body"])
    assert data_reset["grid"][5][3] == 0  # Cleared
