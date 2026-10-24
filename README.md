# Real-Time Python-Powered Connect-4
## AI Game & Algorithm Analysis Platform

A browser-based Connect-4 game with Python AI opponents and an interactive
algorithm performance dashboard. Built for the **Design and Analysis of
Algorithms (DAA)** course.

---

## Current Status

**Milestone 7 — AI Performance Dashboard & DAA Learning Center** ✅

- 📊 **Empirical Performance Dashboard:** Dedicated analytics dashboard powered by the authoritative Python search engines:
  - Multi-run statistical aggregation with median execution time reporting (`time.perf_counter()`).
  - Strict game state isolation: benchmarks evaluate independent detached board clones without mutating live gameplay.
  - Reproducible benchmark positions representing diverse game phases (Opening, Tactical Threat, Complex Midgame, Symmetric Transpositions).
- 📈 **Interactive Chart.js Visualizations:**
  1. *⏱️ Latency vs. Search Depth:* Millisecond execution time across depths 1–4.
  2. *🌳 Nodes Visited vs. Search Depth:* Demonstrates the reduction from $O(b^d)$ to $O(b^{d/2})$.
  3. *✂️ Alpha-Beta Branch Cutoffs:* Pruned dominated branches where $\beta \le \alpha$.
  4. *💾 Transposition Table Memory:* Estimated allocated memory in KB per CPython object footprint.
- 🧠 **DAA Interactive Learning Center:** Collapsible reference cards matching the academic syllabus (Divide & Conquer, Dynamic Programming, Backtracking, and Greedy Heuristics) with mathematical recurrences and complexity trade-offs.
- 🧪 **Complete Test Suite:** **173 automated pytest tests** passing across all modules and REST endpoints.

---

## Features (Across Milestones)

- ♟ **Local 2-Player Mode** (Pass & Play) ✅ *(Milestone 2)*
- 🤖 **Greedy AI Opponent** ✅ *(Milestone 3)*
- 🌲 **Recursive Minimax AI Opponent** ✅ *(Milestone 4)*
- ✂️ **Alpha-Beta Pruning Optimization** ✅ *(Milestone 5)*
- 💾 **Memoized Minimax & Transposition Table** ✅ *(Milestone 6)*
- 📊 **AI Performance Dashboard & DAA Analytics** ✅ *(Milestone 7)*
- 🧪 **Complete pytest suite (173 tests passing)** ✅

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
├── benchmarks/             Automated benchmark engine
│   ├── __init__.py         Package exports
│   ├── positions.py        Canonical benchmark board positions
│   └── runner.py           Multi-run benchmark runner & Chart.js dataset generator
├── tests/                  Automated pytest test suite (173 tests)
│   ├── test_board.py       40 unit tests for Board
│   ├── test_rules.py       24 unit tests for Rules
│   ├── test_engine.py      23 unit tests for procedural engine functions
│   ├── test_greedy.py      14 unit tests for Greedy AI & heuristic scoring
│   ├── test_minimax.py     12 unit tests for Minimax AI search & statistics
│   ├── test_alphabeta.py   13 unit tests for Alpha-Beta pruning & equivalence
│   ├── test_transposition.py 13 unit tests for Transposition Table & bounds
│   ├── test_benchmark.py   5 unit tests for benchmark runner and chart scaling
│   ├── test_app.py         23 integration tests for Flask REST endpoints
│   └── test_audit.py       5 regression and invariant audit tests
├── templates/
│   ├── base.html           Base layout template with navigation
│   └── index.html          Game arena, AI decision panel, dashboard, DAA center
├── static/
│   ├── css/style.css       Theme tokens, responsive board, charts & accordion styles
│   └── js/
│       ├── game.js         Live game controller & AI panel updates
│       └── dashboard.js    Performance dashboard & Chart.js interactive manager
└── docs/
    ├── PROJECT_DOCUMENTATION.md  Exhaustive DAA analysis and development log
    └── TEST_REPORT.md            Comprehensive testing report (173 tests, audits & benchmarks)
```

---

## Documentation

Full technical documentation, DAA concept mapping, complexity analysis,
test reports, and development logs:

📄 [`docs/PROJECT_DOCUMENTATION.md`](docs/PROJECT_DOCUMENTATION.md) — Exhaustive DAA Analysis and Architecture  
🧪 [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md) — Comprehensive Test & Evaluation Report (173 Tests, Invariants & Benchmarks)

---

## Tech Stack

Python 3.13 · Flask 3.1 · HTML5 · Vanilla CSS3 · Vanilla JavaScript · pytest · pytest-cov
