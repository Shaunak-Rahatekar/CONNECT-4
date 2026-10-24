# Real-Time Python-Powered Connect-4
## AI Game & Algorithm Analysis Platform

A browser-based Connect-4 game with Python AI opponents and an interactive
algorithm performance dashboard. Built for the **Design and Analysis of
Algorithms (DAA)** course.

---

## Current Status

**Milestone 6 — Memoization and Transposition Table** ✅

- 💾 **Transposition Table Search Optimization:** Dedicated state memoization engine (`algorithms/transposition_table.py`) caching evaluated subtrees across game graph transpositions:
  - Canonical immutable tuple keying `((row_0), ..., (row_5), player)` with **zero collision risk** and optional 64-bit Zobrist hashing.
  - Three-tier Alpha-Beta bound semantics: `EXACT` (full subgame value), `LOWER_BOUND` (beta-cutoff), and `UPPER_BOUND` (all moves failed low).
  - Depth requirement verification: only reuses stored bounds when $d_{\text{stored}} \ge d_{\text{current}}$, while leveraging shallower entries for **Hash Move Ordering**.
  - Depth-aware terminal score normalization and reconstitution across search depths.
  - Bounded memory management with configurable `max_entries` and shallow-depth eviction.
- ⚡ **Alpha-Beta Pruning Integration:** Seamless caching toggle with real-time tracking of cache hits, misses, hit rate %, active entries, and estimated memory.
- ⚖️ **4-Way Benchmark Comparison Modal:** Interactive benchmarking evaluating identical live board positions across:
  1. Minimax (No Pruning)
  2. Alpha-Beta (Natural Order, No Cache)
  3. Alpha-Beta (Move Ordering, No Cache)
  4. Alpha-Beta + Transposition Table (Move Ordering & Caching)
- 🎮 **Game Modes & Strategy Selector:** Full support for Local 2-Player, Greedy AI, Minimax AI, and Alpha-Beta AI with Move Ordering and Transposition Table toggles.
- 🧪 **Complete Test Suite:** 158 automated pytest tests passing across game engine, procedural API, Greedy AI, Minimax AI, Alpha-Beta AI, Transposition Table, and Flask REST endpoints.

---

## Features (Across Milestones)

- ♟ **Local 2-Player Mode** (Pass & Play) ✅ *(Milestone 2)*
- 🤖 **Greedy AI Opponent** ✅ *(Milestone 3)*
- 🌲 **Recursive Minimax AI Opponent** ✅ *(Milestone 4)*
- ✂️ **Alpha-Beta Pruning Optimization** ✅ *(Milestone 5)*
- 💾 **Memoized Minimax & Transposition Table** ✅ *(Milestone 6)*
- 📈 **Algorithm Performance Comparison Dashboard** *(Milestone 7 — Next)*
- 🧪 **Complete pytest suite (158 tests passing)** ✅

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
│   ├── minimax.py          Recursive Minimax AI search & decision tree generator
│   ├── alphabeta.py        Alpha-Beta Pruning search & move ordering
│   ├── transposition_table.py  Transposition Table, bound types, Zobrist hashing
│   └── comparison.py       Automated 4-way algorithm benchmark runner
├── benchmarks/             Performance runner (added in Prompt 7)
├── tests/                  Automated pytest test suite (158 tests)
│   ├── test_board.py       40 unit tests for Board
│   ├── test_rules.py       24 unit tests for Rules
│   ├── test_engine.py      23 unit tests for procedural engine functions
│   ├── test_greedy.py      14 unit tests for Greedy AI & heuristic scoring
│   ├── test_minimax.py     12 unit tests for Minimax AI search & statistics
│   ├── test_alphabeta.py   13 unit tests for Alpha-Beta pruning & equivalence
│   ├── test_transposition.py 13 unit tests for Transposition Table & bounds
│   └── test_app.py         19 integration tests for Flask REST endpoints
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
