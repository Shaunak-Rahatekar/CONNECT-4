# Real-Time Python-Powered Connect-4
## AI Game & Algorithm Analysis Platform

A browser-based Connect-4 game with Python AI opponents and an interactive
algorithm performance dashboard. Built for the **Design and Analysis of
Algorithms (DAA)** course.

---

## Current Status

**Milestone 5 — Alpha-Beta Pruning Optimization** ✅

- ⚡ **Alpha-Beta Pruning Search Engine:** Complete optimized game-tree search (`algorithms/alphabeta.py`) that strictly preserves the Minimax theorem while cutting search work:
  - Propagates $(\alpha, \beta)$ window bounds across alternating MAX (AI) and MIN (opponent) nodes.
  - Early cutoff termination whenever $\beta \le \alpha$, safely skipping dominated subtrees.
  - Configurable move ordering (`order_candidate_columns`): evaluates immediate wins first, immediate blocks second, and center columns before flanks (`[3, 2, 4, 1, 5, 0, 6]`).
  - Strict Minimax evaluation equivalence: identical depth-aware terminal scoring ($+1,000,000 + d \times 1000$ for wins, $-1,000,000 - d \times 1000$ for losses) and static leaf heuristic.
  - Real-time search statistics: `nodes_visited`, `recursive_calls`, `cutoffs`, `max_depth_reached`, and execution time.
- ⚖️ **Algorithm Benchmark Comparison Modal:** Interactive comparison interface evaluating identical live board positions across:
  1. Minimax (No Pruning)
  2. Alpha-Beta (Natural Order)
  3. Alpha-Beta (Move Ordering)
  - Displays side-by-side chosen move, score, nodes visited, cutoffs, execution time, work reduction percentage (up to **$73.5\%$ reduction** / **$4.51\times$ speedup**), and DAA insights.
- 🎮 **Game Modes & Strategy Selector:** Seamless toggling between Local 2-Player, Greedy AI (Prompt 3), Minimax AI (Prompt 4), and Alpha-Beta AI (Prompt 5).
- 🧪 **Complete Test Suite:** 144 automated pytest tests passing across game engine, procedural API, Greedy AI, Minimax AI, Alpha-Beta AI, comparison engine, and Flask REST endpoints.

---

## Features (Across Milestones)

- ♟ **Local 2-Player Mode** (Pass & Play) ✅ *(Milestone 2)*
- 🤖 **Greedy AI Opponent** ✅ *(Milestone 3)*
- 🌲 **Recursive Minimax AI Opponent** ✅ *(Milestone 4)*
- ✂️ **Alpha-Beta Pruning & Comparison Engine** ✅ *(Milestone 5)*
- 💾 **Memoized Minimax & Transposition Table** *(Milestone 6 — Next)*
- 📈 **Algorithm Performance Comparison Dashboard** *(Milestone 7)*
- 🧪 **Complete pytest suite (144 tests passing)** ✅

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
│   └── comparison.py       Automated 3-way algorithm benchmark runner
├── benchmarks/             Performance runner (added in Prompt 7)
├── tests/                  Automated pytest test suite (144 tests)
│   ├── test_board.py       40 unit tests for Board
│   ├── test_rules.py       24 unit tests for Rules
│   ├── test_engine.py      23 unit tests for procedural engine functions
│   ├── test_greedy.py      14 unit tests for Greedy AI & heuristic scoring
│   ├── test_minimax.py     12 unit tests for Minimax AI search & statistics
│   ├── test_alphabeta.py   13 unit tests for Alpha-Beta pruning & equivalence
│   └── test_app.py         18 integration tests for Flask REST endpoints
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
