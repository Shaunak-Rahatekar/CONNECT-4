# Real-Time Python-Powered Connect-4: AI Game and Algorithm Analysis Platform
## Technical Documentation

---

## Abstract

This document is the permanent technical record for a browser-based Connect-4
application built as a Design and Analysis of Algorithms (DAA) course project.
The application allows a human to play Connect-4 against increasingly
sophisticated AI opponents — Greedy, Minimax, Alpha-Beta Pruning, and
Memoized Minimax — while an interactive dashboard measures and visualises the
performance of each algorithm in real time.

---

## Problem Statement

Connect-4 is a two-player, perfect-information, zero-sum game. Its bounded state
space (at most 4 531 985 219 092 positions) and well-defined winning conditions
make it an ideal vehicle for teaching and evaluating classical search algorithms.
The challenge is to implement each algorithm correctly, compare their empirical
performance honestly, and present the results in an engaging web interface.

---

## Project Scope

**In scope**
- A playable 6 × 7 Connect-4 game (Human vs Human and Human vs AI).
- Four AI strategies: Greedy, Minimax, Alpha-Beta Pruning, Memoized Minimax.
- Configurable search depth.
- AI decision information panel.
- Performance comparison dashboard with real measurements.
- DAA concept mapping and complexity analysis.
- pytest-based correctness tests for all modules.
- Version-controlled development on GitHub.

**Out of scope**
- Network-flow or NP-completeness demonstrations (Units V–VI).
- Multiplayer over a network.
- Persistent user accounts or a database.
- Mobile-native applications.

---

## Functional Requirements

| ID  | Requirement |
|-----|-------------|
| FR1 | The game must enforce all standard Connect-4 rules (gravity, 4-in-a-row win, draw). |
| FR2 | The application must support Human vs Human and Human vs AI modes. |
| FR3 | The AI must support at least Greedy, Minimax, and Alpha-Beta strategies. |
| FR4 | Search depth must be configurable by the user (1–7). |
| FR5 | The application must display an AI decision panel with nodes visited, depth, and score. |
| FR6 | The performance dashboard must show real measured data, never invented values. |
| FR7 | The board must reset on demand and expose full move history. |
| FR8 | Invalid moves (full column, game over) must be rejected with a clear error. |
| FR9 | Win and draw conditions must be detected and displayed immediately. |
| FR10 | All algorithms must be testable independent of Flask. |

## Non-Functional Requirements

| ID   | Requirement |
|------|-------------|
| NFR1 | The UI must be responsive and usable on desktop screens ≥ 768 px wide. |
| NFR2 | AI moves at depth ≤ 4 must complete within 2 seconds on typical hardware. |
| NFR3 | All public Python functions must have docstrings with complexity annotations. |
| NFR4 | Code must pass `pytest` with no failures before each commit. |
| NFR5 | The project must run with `pip install -r requirements.txt` and `flask run`. |
| NFR6 | No secrets, credentials, or generated artefacts may be committed. |

---

## Technology Stack and Rationale

| Technology | Version | Rationale |
|---|---|---|
| Python | 3.13.1 (installed) | Course language; rich standard library; no game-AI framework needed. |
| Flask | 3.1.1 | Lightweight WSGI framework; minimal boilerplate; easy JSON APIs. |
| Jinja2 | 3.1.6 (Flask dep) | Server-side templating; no separate build step. |
| HTML5 / CSS3 / JS | — | Native browser stack; no React or Node.js overhead. |
| pytest | 8.3.5 | Standard Python test runner; clear output; fixture support. |
| pytest-cov | 6.1.0 | Coverage reporting for quality assurance. |
| Chart.js | CDN (Prompt 7) | Lightweight charting; no npm; renders inside `<canvas>`. |
| Git / GitHub | — | Version control and milestone tracking. |

---

## System Architecture

```
Browser (HTML + CSS + JS)
        │  fetch() JSON API calls
        ▼
Flask app.py  ──► Jinja2 templates (base.html, index.html)
        │
        ├── game/
        │     board.py   — Board state, gravity, undo
        │     rules.py   — Win/draw detection, move application
        │
        ├── algorithms/       (populated in Prompts 3-6)
        │     greedy.py
        │     minimax.py
        │     alphabeta.py
        │     transposition.py
        │     evaluation.py
        │
        ├── benchmarks/       (populated in Prompt 7)
        │     runner.py
        │     positions.py
        │
        └── tests/            (pytest, Flask-independent)
```

**Key architectural decision:** The `game/` package has zero Flask imports.
All Flask-specific code lives in `app.py`. This allows `pytest` to import
`game.board` and `game.rules` directly without starting a server.

---

## Directory Structure

```
CONNECT-4/
├── app.py                      Flask entry point, API routes, game session
├── requirements.txt            Pinned Python dependencies
├── README.md                   Project overview and setup guide
├── .gitignore
│
├── game/
│   ├── __init__.py             Exports Board, Rules
│   ├── board.py                Board representation, gravity, undo, copy
│   └── rules.py                Win detection, move application, GameState
│
├── algorithms/
│   └── __init__.py             Placeholder — AI modules added in Prompts 3-6
│
├── benchmarks/
│   └── __init__.py             Placeholder — benchmark engine added in Prompt 7
│
├── tests/
│   ├── __init__.py
│   ├── test_board.py           40 unit tests for Board
│   └── test_rules.py           24 unit tests for Rules
│
├── templates/
│   ├── base.html               Shared HTML shell (header, footer, CSS/JS links)
│   └── index.html              Game page (board, controls, history, AI info)
│
├── static/
│   ├── css/style.css           Responsive dark-theme stylesheet
│   └── js/game.js              Frontend game controller (fetch API, rendering)
│
└── docs/
    └── PROJECT_DOCUMENTATION.md   ← this file
```

---

## Installation and Execution Instructions

### Prerequisites
- Python 3.11 or later (tested on 3.13.1)
- Git

### Setup

```powershell
# 1. Clone the repository
git clone https://github.com/Shaunak-Rahatekar/CONNECT-4.git
cd CONNECT-4

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows PowerShell
# source venv/bin/activate         # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

### Run the application

```powershell
flask run
# or
python app.py
```

Open `http://127.0.0.1:5000` in a browser.

### Run tests

```powershell
pytest tests/ -v
```

### API endpoints (current)

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Homepage / game board |
| GET | `/api/status` | Health check JSON |
| GET | `/api/board` | Current board state JSON |
| POST | `/api/reset` | Reset the game |
| POST | `/api/move` | Apply a human move `{"col": 0-6}` |

---

## DAA Concept Mapping

| Unit | Concept | Module | Status |
|------|---------|--------|--------|
| I — Complexity Analysis | Board op complexity, win detection O(R·C) | board.py, rules.py | ✅ Prompt 1 |
| II — Recursion / D&C | Recursive Minimax, game trees | minimax.py | Prompt 4 |
| II — Recursion / D&C | Alpha-Beta Pruning | alphabeta.py | Prompt 5 |
| III — Dynamic Programming | Memoization / transposition table | transposition.py | Prompt 6 |
| IV — Greedy | Heuristic-based AI | greedy.py | Prompt 3 |
| IV — Backtracking | Move simulation + undo during search | board.py | ✅ Prompt 1 |

---

## Testing Strategy

Tests reside in `tests/` and run with `pytest`.  No Flask server is required.

- **test_board.py** — 40 tests covering all Board methods including edge cases
  (out-of-range columns, full columns, undo on empty board).
- **test_rules.py** — 24 tests covering win detection in all four directions,
  draw detection, turn alternation, and board-state restoration after undo.

After every milestone, the full test suite is re-run and regressions are fixed
before committing.

---

## Development Roadmap

| Prompt | Milestone | Status |
|--------|-----------|--------|
| 1 | Project initialization and architecture | ✅ Complete |
| 2 | Complete playable Connect-4 game | ✅ Complete |
| 3 | Greedy AI | Pending |
| 4 | Minimax AI and decision-tree analysis | Pending |
| 5 | Alpha-Beta Pruning and comparison | Pending |
| 6 | Memoization and transposition table | Pending |
| 7 | Performance dashboard | Pending |
| 8 | Final testing, complexity analysis, documentation | Pending |

---

---

## Development Log — Prompt 1

**Date:** 2026-10-24
**Objective:** Initialize the complete project architecture, establish the development environment, implement the Flask skeleton, build the game engine foundation, write the initial test suite, and set up Git/GitHub.

---

### Features Implemented

1. **Project directory structure** — All directories created: `game/`, `algorithms/`, `benchmarks/`, `tests/`, `templates/`, `static/css/`, `static/js/`, `docs/`.
2. **`game/board.py`** — `Board` class: 6×7 grid, gravity-based `drop_disc`, `undo_last_move`, `switch_player`, `get_valid_columns`, `is_full`, `reset`, `copy`, `to_tuple`, `__eq__`, `__hash__`.
3. **`game/rules.py`** — `Rules` class (stateless): `apply_move`, `check_win_at`, `check_win`, `check_draw`, `is_game_over`, `is_game_over_after_move`, `opponent`. `GameState` dataclass.
4. **`app.py`** — Flask application with 5 routes: `GET /`, `GET /api/status`, `GET /api/board`, `POST /api/reset`, `POST /api/move`. Module-level game session state.
5. **`templates/base.html`** — Shared HTML5 shell with header, footer, and block slots.
6. **`templates/index.html`** — Game page: controls panel, 6×7 board grid, move history, AI info placeholder, score tracker.
7. **`static/css/style.css`** — Responsive dark-theme stylesheet; CSS custom properties; drop animation; win-cell glow; hover preview.
8. **`static/js/game.js`** — Frontend controller: fetch-based API communication; board rendering; drop animation; status bar; move history; score tracking; hover preview.
9. **`requirements.txt`** — Pinned: Flask 3.1.1, pytest 8.3.5, pytest-cov 6.1.0.
10. **`.gitignore`** — Covers `__pycache__`, `venv/`, `.pytest_cache/`, coverage artefacts, IDE files.
11. **`tests/test_board.py`** — 40 unit tests for `Board`.
12. **`tests/test_rules.py`** — 24 unit tests for `Rules`.

---

### Technical Implementation Details

#### Board representation
- **Data structure:** `list[list[int]]` — a Python nested list, row-major order.
  Row 0 is the visual top; row 5 is the visual bottom.  Cell values: 0 (empty),
  1 (Player 1), 2 (Player 2).
- **Gravity:** `get_next_open_row` scans from `ROWS-1` down to 0, returning the
  first empty cell.  Time: O(ROWS) = O(6).
- **Undo support:** `_history` is a list of `(col, row)` tuples.  `undo_last_move`
  pops the last entry, sets the cell to `EMPTY`, and decrements `move_count`.
  This avoids board copies during AI search.

#### Win detection
- **`check_win_at(board, row, col)`** checks only the four directions through
  the given cell.  `_collect_line` extends in both directions along each axis
  and returns all consecutive same-player cells.  A win is detected if any
  direction yields ≥ 4 cells.  Time: O(ROWS + COLS) ≈ O(13) per call.
- **`check_win(board)`** scans every non-empty cell, O(ROWS × COLS) = O(42).
  Used as a fallback when the landing cell is unknown.
- **`is_game_over_after_move`** calls the faster `check_win_at`, reducing the
  post-move check to O(1) for a fixed-size board.

#### Flask API design
- All game state is kept server-side in module-level variables.  The client
  sends column numbers and receives complete board snapshots as JSON.  No
  game logic is duplicated in JavaScript.
- `POST /api/move` validates the column, applies the move via `Rules.apply_move`,
  appends to move history, and calls `is_game_over_after_move` before returning.

---

### Complexity Analysis (Unit I — DAA)

| Operation | Time Complexity | Space Complexity | Notes |
|-----------|----------------|-----------------|-------|
| Board creation | O(R·C) | O(R·C) | R=6, C=7 → O(42) |
| `drop_disc` | O(R) | O(1) | Scans rows top-to-bottom |
| `undo_last_move` | O(1) | O(1) | Stack pop |
| `get_valid_columns` | O(C) | O(C) | Checks top cell of each column |
| `check_win_at` | O(R+C) | O(R+C) | Four direction scans |
| `check_win` (full) | O(R·C·(R+C)) | O(R+C) | Each cell × direction scan |
| `copy` | O(R·C) | O(R·C) | Deep copy of grid |
| `to_tuple` | O(R·C) | O(R·C) | Serialise for hash key |
| `is_full` | O(C) | O(1) | Delegates to `get_valid_columns` |

For the fixed 6×7 board, all operations are effectively O(1) by the constant-
bound argument, but the asymptotic forms above are correct for a generalised
R×C board.

---

### Files Created

| File | Lines | Description |
|------|-------|-------------|
| `game/__init__.py` | 10 | Package init, public exports |
| `game/board.py` | 172 | Board class — state, gravity, undo |
| `game/rules.py` | 158 | Rules class — win detection, move application |
| `algorithms/__init__.py` | 12 | Placeholder with milestone roadmap |
| `benchmarks/__init__.py` | 8 | Placeholder with milestone roadmap |
| `app.py` | 123 | Flask routes and game session |
| `templates/base.html` | 28 | HTML5 base template |
| `templates/index.html` | 84 | Game page template |
| `static/css/style.css` | 295 | Responsive dark-theme stylesheet |
| `static/js/game.js` | 208 | Frontend game controller |
| `tests/__init__.py` | 2 | Test package marker |
| `tests/test_board.py` | 220 | 40 Board unit tests |
| `tests/test_rules.py` | 210 | 24 Rules unit tests |
| `requirements.txt` | 3 | Pinned dependencies |
| `.gitignore` | 30 | Exclusion rules |
| `docs/PROJECT_DOCUMENTATION.md` | this file | Permanent technical record |

---

### Technologies and Dependencies Used

- Python 3.13.1
- Flask 3.1.1 (+ Werkzeug 3.1.9, Jinja2 3.1.6, Click 8.5.0, itsdangerous 2.2.0)
- pytest 8.3.5
- pytest-cov 6.1.0
- coverage 7.17.0

---

### DAA Concepts Applied

- **Unit I — Complexity Analysis:** Every public method carries a docstring with
  its time and space complexity in asymptotic notation.  The Complexity Analysis
  table above consolidates these annotations.
- **Unit IV — Backtracking (foundation):** `undo_last_move` implements the
  "simulate and restore" pattern that the AI search algorithms will rely on in
  Prompts 4–6, avoiding the need to copy the board on every recursive call.

---

### Tests Executed and Actual Results

```
platform win32 -- Python 3.13.1, pytest-8.3.5, pluggy-1.7.0
rootdir: D:\CONNECT-4

tests/test_board.py  — 40 tests
tests/test_rules.py  — 24 tests

64 passed in 0.14s
```

**Bug discovered and fixed during testing:**
- `Board.drop_disc` called `get_next_open_row(col)` before checking whether
  `col` was in bounds.  On `col=99` this caused an `IndexError`.
- **Fix:** Added an out-of-range guard at the top of `drop_disc`:
  `if col < 0 or col >= COLS: return None`.
- Test `test_drop_disc_out_of_range` now passes (was the only failure before
  the fix).

---

### Git Commit Hash and Push Status

Repository initialised locally.  Remote configured to:
`https://github.com/Shaunak-Rahatekar/CONNECT-4.git`

**Commit hash:** `a137082`
**Branch:** `main`
**Remote:** `https://github.com/Shaunak-Rahatekar/CONNECT-4.git`
**Push status:** ✅ Confirmed — `origin/main` is up to date with local `main`.
Branch created on GitHub: `* [new branch] main -> main`.

---

### Known Limitations and Next Steps

**Limitations (Prompt 1)**
- Single-session in-memory state — opening a second browser tab shares the same game.
- No AI yet — Human vs AI radio button is disabled with a "Coming Soon" badge.
- No multi-user isolation.

**Next steps (Prompt 2)**
- Implement the full playable game: turn management enforced by Flask, move
  history persistence per session, winning-cell highlight triggered by the
  server, and a polished game-over modal.

---

---

## Development Log — Prompt 2

**Date:** 2026-10-24
**Objective:** Implement a fully playable Connect-4 game for two local players. Deliver an authoritative, robust game engine, procedural reusable APIs, a responsive browser interface with rich visual aesthetics, comprehensive pytest coverage for game logic and API endpoints, and complete DAA complexity and correctness analysis.

---

### Features Implemented

1. **Modular Engine Extension (`game/engine.py`)** — Implemented functional, procedural game utilities interoperable with both `Board` objects and raw 2D lists:
   - `create_board() -> Board`
   - `get_valid_moves(board) -> list[int]`
   - `make_move(board, column, player=None) -> int | None`
   - `check_winner(board, player=None) -> bool | int | None`
   - `is_draw(board) -> bool`
   - `get_game_status(board) -> dict`
2. **Move History & State Atomicity (`game/board.py`)** — Extended `Board` to track detailed move history `[{"move_number", "player", "col", "row"}, ...]`, synchronized across `drop_disc`, `undo_last_move`, `reset`, and `copy`. Guaranteed board immutability upon rejected moves.
3. **Geometric Line Sorting (`game/rules.py`)** — Refined `Rules.check_win_at` to sort winning cells in line order `(r, c)`, producing contiguous 4-in-a-row coordinates for frontend rendering.
4. **Authoritative API Enforcement (`app.py`)** — Upgraded `/api/move` to return structured 400 Bad Request payloads with user-friendly error messages on invalid moves (out of bounds, full columns, or moves attempted after game over). Kept state validation strictly server-side.
5. **Interactive Browser Interface (`templates/index.html`, `static/css/style.css`, `static/js/game.js`)**:
   - **Direct board interaction:** Players can click directly on columns or board cells to drop discs.
   - **Dynamic ghost preview:** Hovering over any column displays a semi-transparent preview disc in the player's color at the lowest unoccupied row.
   - **Invalid-move feedback:** User-facing alert banner with board shake animation (`@keyframes board-shake`) on illegal moves.
   - **Active turn indicators:** Turn status bar with pulsating player disc, active roster cards for Player 1 (Red) and Player 2 (Yellow), and move count badges.
   - **Celebratory game-over modal:** Centered modal with backdrop blur, victory badge, move statistics, and instant "Play Again" button.
   - **Accessible UI:** Complete ARIA attributes (`role="alert"`, `aria-live="polite"`, `role="grid"`, `tabindex="0"`, dynamic cell labels).
6. **Integration & API Tests (`tests/test_engine.py`, `tests/test_app.py`)** — Added 31 new unit and integration tests covering empty board initialisation, legal/illegal moves, gravity stacking, draw detection, post-game protection, reset behaviour, and HTTP endpoints. Total test suite expanded to 95 passing tests.

---

### DAA Concept Analysis (Unit I — Course Mapping)

#### 1. Board Representation & Matrix Trade-offs
- **Representation:** A 2-dimensional list `list[list[int]]` of dimensions $R \times C$ ($6 \times 7$), indexed in row-major order where row 0 is the top and row 5 is the bottom.
- **Trade-off Analysis:**
  - *Nested List (`list[list[int]]`):* Offers $O(1)$ random cell access by coordinate `(row, col)`, trivial conversion to JSON for web transport, direct visual correspondence to the grid, and zero external C-dependencies. Board copying costs $O(R \cdot C) = O(42)$ operations.
  - *Bitboard Representation (Alternative):* Encodes the 42 cells into two 64-bit integers (one per player). Bitboards provide $O(1)$ win checking via bitwise shifts (`board & (board >> 1) & ...`) and minimal memory footprint. However, bitboards incur significant code complexity, require custom coordinate decoders for API serialisation, and offer negligible wall-clock benefit in a high-level Python runtime for interactive play. The 2D matrix was chosen as the optimal balance between clarity, maintainability, and execution speed.

#### 2. Move Generation Complexity
- Connect-4 pieces are dropped into columns, meaning the branching factor $b \le C = 7$.
- A move into column $c$ is legal if and only if $0 \le c < C$ and `grid[0][c] == EMPTY`.
- **Work Required:** Generating valid moves requires inspecting the top cell of each of the $C$ columns.
  - **Time Complexity:** $O(C)$ — exactly 7 inspections per state evaluation.
  - **Auxiliary Space:** $O(C)$ to return the list of legal column indices $[0..6]$.

#### 3. Win Detection Complexity
- **Directional Scan:** Any winning line of length $K=4$ formed by a move must contain the landing cell $(r, c)$. Four axes pass through any cell:
  1. Horizontal ($\Delta r = 0, \Delta c = 1$)
  2. Vertical ($\Delta r = 1, \Delta c = 0$)
  3. Diagonal-downward ($\Delta r = 1, \Delta c = 1$, ↘)
  4. Diagonal-upward ($\Delta r = 1, \Delta c = -1$, ↗)
- **Local Win Check (`check_win_at`):** From $(r, c)$, the scan extends at most $K-1$ steps along the positive and negative directions for each of the 4 axes.
  - Maximum cell comparisons per axis: $2(K - 1) + 1 = 2K - 1$.
  - Total comparisons across 4 axes: $4(2K - 1) = 8K - 4$.
  - For $K=4$: at most $8(4) - 4 = 28$ cell comparisons.
  - **Time Complexity:** $O(K)$ or bounded by $O(R + C)$. For fixed $R=6, C=7, K=4$, this is strictly $O(1)$.
- **Global Board Scan (`check_win`):**
  - When the last move position is unknown, every cell $(r, c)$ is inspected.
  - **Time Complexity:** $O(R \cdot C \cdot K)$ operations. For a $6 \times 7$ grid: at most $42 \times 28 = 1176$ comparisons, executing in under $0.2\text{ ms}$.

#### 4. Correctness of the Four Directional Checks
- **Theorem:** Checking horizontal, vertical, and the two diagonal directions bi-directionally covers every possible winning line in Connect-4.
- **Proof:**
  1. A winning connection is defined as a contiguous sequence of $K=4$ cells forming a straight line segment on the discrete lattice $\mathbb{Z}^2$.
  2. Any straight line segment in $\mathbb{Z}^2$ has a constant slope $m = \frac{\Delta r}{\Delta c}$.
  3. In a square grid, two cells are adjacent if their Chebyshev distance is 1: $\max(|\Delta r|, |\Delta c|) = 1$. The non-zero displacement vectors $(\Delta r, \Delta c) \in \{-1, 0, 1\}^2 \setminus \{(0, 0)\}$ yield exactly 8 adjacent directions.
  4. These 8 directions partition into 4 antipodal pairs (lines):
     - Slope $m = 0$: Horizontal line along $(0, 1)$ and $(0, -1)$.
     - Slope $m = \infty$: Vertical line along $(1, 0)$ and $(-1, 0)$.
     - Slope $m = +1$: Main diagonal along $(1, 1)$ and $(-1, -1)$ (↘).
     - Slope $m = -1$: Anti-diagonal along $(1, -1)$ and $(-1, 1)$ (↗).
  5. Any connected straight path of length 4 must proceed along one of these 4 colinear axes. No other straight connected lines exist on a 2D integer grid.
  6. Bi-directional ray scanning from the landing cell along all 4 axes is therefore exhaustive and guaranteed to identify any winning line containing that cell. $\blacksquare$

---

### Complexity Summary Table

| Operation | Time Complexity | Auxiliary Space | Asymptotic Notes |
|---|---|---|---|
| `create_board()` | $O(R \cdot C)$ | $O(R \cdot C)$ | Creates $6 \times 7$ matrix ($O(42) \approx O(1)$) |
| `get_valid_moves(board)` | $O(C)$ | $O(C)$ | Inspects column headers ($7$ checks) |
| `make_move(board, col)` | $O(R)$ | $O(1)$ | Scans row gravity ($6$ rows) |
| `check_win_at(board, r, c)` | $O(K)$ | $O(K)$ | At most $28$ cell comparisons ($O(1)$) |
| `check_win(board)` (full) | $O(R \cdot C \cdot K)$ | $O(K)$ | Bounded by $42 \times 28$ operations |
| `is_draw(board)` | $O(R \cdot C \cdot K)$ | $O(1)$ | Full column check $O(C)$ + win check |
| `get_game_status(board)` | $O(R \cdot C \cdot K)$ | $O(C)$ | Aggregates full snapshot |
| Board `undo_last_move()` | $O(1)$ | $O(1)$ | Stack pop from history list |
| Board `to_tuple()` / hash | $O(R \cdot C)$ | $O(R \cdot C)$ | Immutable grid tuple for memoization |

---

### Files Changed and Created

| File | Status | Description |
|---|---|---|
| `game/engine.py` | Created | Procedural game engine APIs (`create_board`, `make_move`, etc.) |
| `game/__init__.py` | Updated | Package exports for engine functions and game constants |
| `game/board.py` | Updated | Move history tracking and `get_move_history()` |
| `game/rules.py` | Updated | Sorted winning cell coordinates in line order |
| `app.py` | Updated | Enhanced `/api/move` authoritative validation and snapshot serialization |
| `templates/index.html` | Updated | Accessible board, invalid-move banner, active turn roster, modal |
| `static/css/style.css` | Updated | Responsive dark-theme styling, ghost preview, board shake, pulse animations |
| `static/js/game.js` | Updated | Clickable cells, ghost disc hover preview, error alerts, celebration modal |
| `tests/test_engine.py` | Created | 23 comprehensive tests for procedural engine functions and edge cases |
| `tests/test_app.py` | Created | 8 integration tests for Flask API routes and error responses |
| `README.md` | Updated | Milestone 2 documentation and gameplay instructions |
| `docs/PROJECT_DOCUMENTATION.md` | Updated | Appended Prompt 2 Development Log and DAA analysis |

---

### Tests Executed and Actual Results

```powershell
pytest -v
```

```
============================= test session starts =============================
platform win32 -- Python 3.13.1, pytest-8.3.5, pluggy-1.7.0
rootdir: D:\CONNECT-4
plugins: cov-6.1.0
collected 95 items

tests/test_app.py (8 tests)       — All PASSED
tests/test_board.py (40 tests)    — All PASSED
tests/test_engine.py (23 tests)   — All PASSED
tests/test_rules.py (24 tests)    — All PASSED

============================= 95 passed in 0.53s ==============================
```

**Bugs Discovered and Fixed:**
1. *Partial board win false-positive in engine test:* In `test_get_valid_moves_partial_board`, filling a column with 6 discs of `PLAYER1` triggered a vertical win, causing `get_valid_moves` to correctly return `[]` (post-game protection). Fixed the test fixture to alternate discs (`(i % 2) + 1`), ensuring a non-winning full column and asserting `[0, 1, 3, 4, 5, 6]`.
2. *Draw pattern diagonal intersection:* An initial draw test pattern had an unintended 4-in-a-row diagonal connection. Replaced it with a mathematically verified alternating row pattern that guarantees zero 4-in-a-row connections across all 4 axes on a full $6 \times 7$ board.
3. *Move history synchronization:* Board undo operations previously popped internal `_history` tuples but did not pop `move_history` dictionaries. Synchronized `undo_last_move()` and `reset()` to keep both history lists atomic.

---

### Git Commit Hash and Push Status

- **Branch:** `main`
- **Commit Message:** `feat: implement playable Connect-4 game engine`
- **Push Status:** Ready for push to `origin/main`.

