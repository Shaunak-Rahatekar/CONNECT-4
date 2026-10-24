"""
netlify/functions/app.py — Netlify Serverless Function Handler for Connect-4 Flask App.

Adapts AWS Lambda / Netlify Functions proxy events to WSGI environ format,
invoking the authoritative Flask application.
"""

from __future__ import annotations

import base64
import io
import os
import sys
from typing import Any
from urllib.parse import urlencode

# Ensure root directory is in sys.path so 'app', 'game', 'algorithms' can be imported
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app as flask_app  # noqa: E402


def build_wsgi_environ(event: dict[str, Any]) -> dict[str, Any]:
    """Convert a Netlify / AWS Lambda event dictionary into a standard PEP-3333 WSGI environ."""
    method = (event.get("httpMethod") or "GET").upper()
    path = event.get("path") or "/"
    
    # Netlify redirect might pass the function path in some raw environments, sanitize to root if needed
    if path.startswith("/.netlify/functions/app"):
        path = path[len("/.netlify/functions/app"):] or "/"

    query_params = event.get("queryStringParameters") or {}
    query_string = urlencode(query_params)
    raw_headers = event.get("headers") or {}
    norm_headers = {k.lower(): v for k, v in raw_headers.items() if v is not None}
    
    host_val = norm_headers.get("host", "localhost")
    host_name = host_val.split(":")[0]
    proto = norm_headers.get("x-forwarded-proto", "https")
    default_port = "443" if proto == "https" else "80"
    server_port = host_val.split(":")[1] if ":" in host_val else default_port

    body = event.get("body")
    is_base64 = event.get("isBase64Encoded", False)

    if body is not None:
        if is_base64:
            body_bytes = base64.b64decode(body)
        else:
            body_bytes = body.encode("utf-8") if isinstance(body, str) else body
    else:
        body_bytes = b""

    environ: dict[str, Any] = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "SCRIPT_NAME": "",
        "QUERY_STRING": query_string,
        "SERVER_NAME": host_name,
        "SERVER_PORT": server_port,
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": proto,
        "wsgi.input": io.BytesIO(body_bytes),
        "wsgi.errors": sys.stderr,
        "wsgi.multithread": False,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
        "CONTENT_LENGTH": str(len(body_bytes)),
    }

    # Map headers to WSGI format
    for raw_key, raw_val in raw_headers.items():
        if raw_val is None:
            continue
        header_key = raw_key.upper().replace("-", "_")
        if header_key == "CONTENT_TYPE":
            environ["CONTENT_TYPE"] = raw_val
        elif header_key == "CONTENT_LENGTH":
            environ["CONTENT_LENGTH"] = raw_val
        else:
            environ[f"HTTP_{header_key}"] = raw_val

    return environ


def handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Netlify Function entry point handling incoming HTTP requests."""
    environ = build_wsgi_environ(event)
    response_data: dict[str, Any] = {
        "status_code": 200,
        "headers": [],
        "body_chunks": [],
    }

    def start_response(status: str, response_headers: list[tuple[str, str]], exc_info: Any = None) -> None:
        response_data["status_code"] = int(status.split()[0])
        response_data["headers"] = response_headers

    app_iter = flask_app(environ, start_response)
    try:
        for chunk in app_iter:
            if isinstance(chunk, bytes):
                response_data["body_chunks"].append(chunk)
            elif isinstance(chunk, str):
                response_data["body_chunks"].append(chunk.encode("utf-8"))
    finally:
        if hasattr(app_iter, "close"):
            app_iter.close()

    raw_body = b"".join(response_data["body_chunks"])

    # Build response header dictionaries
    single_headers: dict[str, str] = {}
    multi_headers: dict[str, list[str]] = {}
    content_type = ""

    for k, v in response_data["headers"]:
        if k.lower() == "content-type":
            content_type = v.lower()
        single_headers[k] = v
        multi_headers.setdefault(k, []).append(v)

    is_text = any(t in content_type for t in ["text/", "json", "javascript", "xml", "svg", "css"])
    is_b64 = False

    if is_text or not content_type:
        try:
            body_out = raw_body.decode("utf-8")
        except UnicodeDecodeError:
            body_out = base64.b64encode(raw_body).decode("ascii")
            is_b64 = True
    else:
        body_out = base64.b64encode(raw_body).decode("ascii")
        is_b64 = True

    return {
        "statusCode": response_data["status_code"],
        "headers": single_headers,
        "multiValueHeaders": multi_headers,
        "body": body_out,
        "isBase64Encoded": is_b64,
    }
