# Real-Time Python-Powered Connect-4
## AI Game & Algorithm Analysis Platform

A browser-based Connect-4 game with Python AI opponents and an interactive
algorithm performance dashboard. Built for the **Design and Analysis of
Algorithms (DAA)** course.

---

## Current Status

**Milestone 4 — Recursive Minimax AI Opponent** ✅

- 🌲 **Recursive Minimax AI Engine:** Full recursive game-tree search (`algorithms/minimax.py`) considering future counter-moves from both players:
  - Alternating maximizing (AI) and minimizing (opponent) turns.
  - Depth-aware terminal scoring ($+1,000,000 + d \times 1000$ for wins, $-1,000,000 - d \times 1000$ for losses), favoring faster victories and delaying unavoidable defeats.
  - Zero-allocation in-place backtracking (`drop_disc` + `undo_last_move`), ensuring $O(d)$ recursion call-stack memory without copying boards.
  - Heuristic non-terminal leaf evaluation across 69 four-cell windows (`algorithms/evaluation.py`).
  - Configurable search-depth limits: Easy (Depth 1), Casual (Depth 2), Medium (Depth 3), Hard (Depth 4).
- 📊 **Real-Time Decision Tree & Metrics Visualizer:** AI Decision Panel displays chosen column, depth-aware evaluation score, measured compute time (ms), nodes visited, recursive calls, max depth reached, candidate scores, and collapsible root decision branches tree.
- 🎮 **Game Modes & Strategy Selector:** Seamless toggling between Local 2-Player (Pass & Play), Greedy AI (Prompt 3), and Minimax AI (Prompt 4) with authoritative server-side execution.
- 🧪 **Complete Test Suite:** 128 automated pytest tests passing across game engine, procedural API, Greedy AI, Minimax AI, and Flask REST endpoints.

---

## Features (Across Milestones)

- ♟ **Local 2-Player Mode** (Pass & Play) ✅ *(Milestone 2)*
- 🤖 **Greedy AI Opponent** ✅ *(Milestone 3)*
- 🌲 **Recursive Minimax AI Opponent** ✅ *(Milestone 4)*
- ✂️ **Alpha-Beta Pruning** *(Milestone 5 — Next)*
- 💾 **Memoized Minimax & Transposition Table** *(Milestone 6)*
- 📈 **Algorithm Performance Comparison Dashboard** *(Milestone 7)*
- 🧪 **Complete pytest suite (128 tests passing)** ✅

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
│   ├── greedy.py           Greedy AI priority decision maker
│   └── minimax.py          Recursive Minimax AI search & decision tree generator
├── benchmarks/             Performance runner (added in Prompt 7)
├── tests/                  Automated pytest test suite (128 tests)
│   ├── test_board.py       40 unit tests for Board
│   ├── test_rules.py       24 unit tests for Rules
│   ├── test_engine.py      23 unit tests for procedural engine functions
│   ├── test_greedy.py      14 unit tests for Greedy AI & heuristic scoring
│   ├── test_minimax.py     12 unit tests for Minimax AI search & statistics
│   └── test_app.py         15 integration tests for Flask REST endpoints
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
