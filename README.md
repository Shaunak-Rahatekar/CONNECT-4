# Real-Time Python-Powered Connect-4
## AI Game & Algorithm Analysis Platform

A browser-based Connect-4 game with Python AI opponents and an interactive
algorithm performance dashboard. Built for the **Design and Analysis of
Algorithms (DAA)** course.

---

## Current Status

**Milestone 2 — Playable Connect-4 Game Engine** ✅

- 🎮 **Authoritative Python Game Engine:** Full 6×7 Connect-4 rule enforcement (gravity, turn alternation, boundary and full-column validation, win detection across horizontal, vertical, and both diagonal axes, and true draw detection).
- 🧩 **Procedural Engine API:** Canonical, reusable functions (`create_board()`, `get_valid_moves()`, `make_move()`, `check_winner()`, `is_draw()`, `get_game_status()`) supporting both `Board` instances and 2D arrays.
- 🎨 **Responsive Interactive Web UI:** Pass-and-play local 2-player mode with interactive board cell clicking, real-time ghost disc hover preview in player colors, invalid-move feedback with alert banner and board-shake animation, glowing active turn indicators, celebration victory modal, and live move history.
- 🧪 **Comprehensive Test Coverage:** 95 automated pytest tests covering all game engine methods, edge cases, deterministic boards, and Flask API endpoints.

---

## Features (Across Milestones)

- ♟ **Local 2-Player Mode** (Pass & Play) ✅ *(Milestone 2)*
- 🤖 **Greedy, Minimax, Alpha-Beta, and Memoized AI strategies** *(Milestones 3–6)*
- 🔢 **Configurable search depth (1–7)** *(Milestones 4–5)*
- 📊 **Real-time AI decision information panel** *(Milestone 3+)*
- 📈 **Algorithm performance comparison dashboard** *(Milestone 7)*
- 🧪 **Complete pytest suite (95 tests passing)** ✅

---

## Setup

```powershell
# Clone
git clone https://github.com/Shaunak-Rahatekar/CONNECT-4.git
cd CONNECT-4

# Virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1      # Windows PowerShell

# Dependencies
pip install -r requirements.txt
```

## Run Application

```powershell
python app.py
# then open http://127.0.0.1:5000 in your browser
```

## Run Test Suite

```powershell
pytest tests/ -v
```

---

## Project Structure

```
CONNECT-4/
├── app.py              Flask entry point and authoritative API routes
├── game/               Game engine (Flask-independent)
│   ├── __init__.py     Public API exports
│   ├── board.py        Board state, gravity, history, undo
│   ├── rules.py        Win detection across 4 axes, draw detection, GameState
│   └── engine.py       Procedural engine API (create_board, make_move, etc.)
├── algorithms/         AI modules (added in Prompts 3-6)
├── benchmarks/         Performance runner (added in Prompt 7)
├── tests/              pytest test suite
│   ├── test_board.py   40 unit tests for Board
│   ├── test_rules.py   24 unit tests for Rules
│   ├── test_engine.py  23 unit tests for reusable engine functions
│   └── test_app.py     8 integration tests for Flask API endpoints
├── templates/          Jinja2 HTML templates (base.html, index.html)
├── static/             CSS stylesheet and JavaScript client controller
└── docs/               Technical documentation and DAA analysis
```

---

## Documentation

Full technical documentation, DAA concept mapping, complexity analysis,
and development logs:

📄 [`docs/PROJECT_DOCUMENTATION.md`](docs/PROJECT_DOCUMENTATION.md)

---

## Tech Stack

Python 3.13 · Flask 3.1 · HTML5 · Vanilla CSS3 · Vanilla JavaScript · pytest · pytest-cov
