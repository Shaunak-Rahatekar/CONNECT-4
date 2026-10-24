# Real-Time Python-Powered Connect-4
## AI Game & Algorithm Analysis Platform

A browser-based Connect-4 game with Python AI opponents and an interactive
algorithm performance dashboard. Built for the **Design and Analysis of
Algorithms (DAA)** course.

---

## Current Status

**Milestone 3 — Greedy AI Opponent** ✅

- 🤖 **Fast Tactical Greedy AI:** Implemented depth-1 priority-driven AI that evaluates all immediate candidate moves:
  1. Immediate win detection.
  2. Immediate opponent win blocking.
  3. Static heuristic scoring across all 69 four-cell winning windows.
  4. Center column bias and deterministic tie-breaking (`[3, 2, 4, 1, 5, 0, 6]`).
- 📊 **Real-Time AI Decision Panel:** Visualizes chosen column, heuristic score, tactical reasoning, measured execution time in milliseconds, and candidate move breakdown pills.
- 🎮 **Game Mode Selector:** Seamless toggle between Local 2-Player (Pass & Play) and Play vs Greedy AI with authoritative server validation.
- 🧪 **Complete Test Suite:** 113 automated pytest tests passing across game engine, AI logic, and Flask REST endpoints.

---

## Features (Across Milestones)

- ♟ **Local 2-Player Mode** (Pass & Play) ✅ *(Milestone 2)*
- 🤖 **Greedy AI Opponent** ✅ *(Milestone 3)*
- 🌲 **Minimax Search** *(Milestone 4 — Next)*
- ✂️ **Alpha-Beta Pruning** *(Milestone 5)*
- 💾 **Memoized Minimax & Transposition Table** *(Milestone 6)*
- 📈 **Algorithm Performance Comparison Dashboard** *(Milestone 7)*
- 🧪 **Complete pytest suite (113 tests passing)** ✅

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
├── app.py                  Flask entry point, mode selection, REST endpoints
├── game/                   Authoritative Python game engine
│   ├── __init__.py         Package exports
│   ├── board.py            Grid state, gravity, history, undo
│   ├── rules.py            Win detection across 4 axes, draw detection, GameState
│   └── engine.py           Procedural engine API (create_board, make_move, etc.)
├── algorithms/             AI strategies
│   ├── __init__.py         Package exports
│   ├── evaluation.py       Static heuristic window evaluation and weights
│   └── greedy.py           Greedy AI priority decision maker
├── benchmarks/             Performance runner (added in Prompt 7)
├── tests/                  Automated pytest test suite (113 tests)
│   ├── test_board.py       40 unit tests for Board
│   ├── test_rules.py       24 unit tests for Rules
│   ├── test_engine.py      23 unit tests for procedural engine functions
│   ├── test_greedy.py      14 unit tests for Greedy AI & heuristic scoring
│   └── test_app.py         12 integration tests for Flask REST endpoints
├── templates/              Jinja2 HTML templates (base.html, index.html)
├── static/                 CSS stylesheet and JavaScript client controller
└── docs/                   Technical documentation and DAA analysis
```

---

## Documentation

Full technical documentation, DAA concept mapping, complexity analysis,
and development logs:

📄 [`docs/PROJECT_DOCUMENTATION.md`](docs/PROJECT_DOCUMENTATION.md)

---

## Tech Stack

Python 3.13 · Flask 3.1 · HTML5 · Vanilla CSS3 · Vanilla JavaScript · pytest · pytest-cov
