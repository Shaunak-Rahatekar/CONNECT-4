# Connect-4 AI & Algorithm Analysis Platform — User Manual & Interface Guide

Welcome to the **Connect-4 AI & Algorithm Analysis Platform**, a full-stack educational and experimental laboratory designed for coursework in **Design and Analysis of Algorithms (DAA)**.

This application pairs an interactive, high-performance Connect-4 game engine with real-time algorithm inspection, empirical performance benchmarking, and dynamic visualizations.

---

## Table of Contents

1. [Platform Overview](#platform-overview)
2. [Quick Start & Launching the App](#quick-start--launching-the-app)
3. [Game Rules & Mechanics](#game-rules--mechanics)
4. [Comprehensive Element-by-Element Interface Breakdown](#comprehensive-element-by-element-interface-breakdown)
   - [4.1 Site Header](#41-site-header)
   - [4.2 Left Panel: Game Controls & Configuration](#42-left-panel-game-controls--configuration)
   - [4.3 Center Panel: Interactive Game Board & Arena](#43-center-panel-interactive-game-board--arena)
   - [4.4 Right Panel: AI Decision Inspector & Move History](#44-right-panel-ai-decision-inspector--move-history)
   - [4.5 Bottom Panel 1: AI Performance & Benchmark Dashboard](#45-bottom-panel-1-ai-performance--benchmark-dashboard)
   - [4.6 Bottom Panel 2: DAA Interactive Learning Center](#46-bottom-panel-2-daa-interactive-learning-center)
   - [4.7 Modals & Overlays](#47-modals--overlays)
5. [Step-by-Step Workflows for Maximum Efficiency](#step-by-step-workflows-for-maximum-efficiency)
   - [Workflow A: Playing Against the AI](#workflow-a-playing-against-the-ai)
   - [Workflow B: Comparing Algorithms on Live Positions](#workflow-b-comparing-algorithms-on-live-positions)
   - [Workflow C: Running Empirical Benchmarks & Exporting Insights](#workflow-c-running-empirical-benchmarks--exporting-insights)
   - [Workflow D: Classroom & Viva Demonstrations](#workflow-d-classroom--viva-demonstrations)
6. [Keyboard Controls & Accessibility Features](#keyboard-controls--accessibility-features)
7. [Frequently Asked Questions (FAQ) & Troubleshooting](#frequently-asked-questions-faq--troubleshooting)

---

## 1. Platform Overview

The platform is designed to bridge the gap between abstract algorithmic theory and demonstrable, empirical behavior. Rather than treating artificial intelligence as a black box, every decision made by the computer is exposed in real time:

- **Game Engine:** Authoritative Python backend enforcing strict Connect-4 rules, drop gravity, and 4-direction victory detection.
- **AI Implementations:**
  1. **Greedy Heuristic (Unit IV):** Instant $O(1)$ tactical search prioritizing immediate 4-in-a-row wins, opponent blocks, and center column control.
  2. **Minimax (Unit II):** Exhaustive recursive game-tree search using depth-aware terminal scoring.
  3. **Alpha-Beta Pruning (Unit II & IV):** Branch-and-bound optimization cutting branches whenever $\beta \le \alpha$.
  4. **Move Ordering Heuristic:** Strategic candidate prioritization (winning moves $\rightarrow$ blocks $\rightarrow$ center-to-flank) driving search complexity toward $O(b^{d/2})$.
  5. **Transposition Table Memoization (Unit III):** Dynamic programming hash table storing exact minimax values, upper bounds, and lower bounds to eliminate redundant subtree evaluation.
- **Performance Analytics:** Live wall-clock latency (ms), node expansion counters, cutoff counts, cache hit ratios, and heap memory profiling.

---

## 2. Quick Start & Launching the App

### Prerequisites
- Python 3.10 or higher (Python 3.13 recommended)
- A modern web browser (Google Chrome, Mozilla Firefox, Microsoft Edge, or Safari)

### Starting the Server
Open your terminal in the project root directory and start the Flask server:

```powershell
# Using the Windows PowerShell runner:
.\run.ps1

# Or running Python directly:
python app.py
```

The application will start at:
```
http://127.0.0.1:5000/
```
Open this URL in your web browser.

---

## 3. Game Rules & Mechanics

Connect-4 is played on a vertical grid consisting of **6 rows** and **7 columns**:

1. **Turn-based:** Player 1 uses **Red** discs; Player 2 / AI uses **Yellow** discs. Player 1 always moves first.
2. **Gravity:** Discs fall to the lowest unoccupied cell in the chosen column.
3. **Winning Condition:** The first player to align **four consecutive discs** of their color horizontally, vertically, or diagonally wins immediately.
4. **Draw Condition:** If all 42 cells are filled without a four-in-a-row alignment, the game ends in a draw.

---

## 4. Comprehensive Element-by-Element Interface Breakdown

### 4.1 Site Header
- **Site Title (`.site-title`):** Displays the platform brand with decorative Red and Yellow disc icons.
- **Site Subtitle (`.site-subtitle`):** Identifies the application as an *AI Game & Algorithm Analysis Platform*.

---

### 4.2 Left Panel: Game Controls & Configuration
Located on the left side of the screen (`aside.panel-controls`). Controls the game state and AI parameters:

| Element | ID / Selector | Purpose & How to Use Efficiently |
| :--- | :--- | :--- |
| **Local 2-Player (Pass & Play)** | `#mode-hvh` | Radio option for two human players taking turns on the same screen. The AI panel goes into a standby prompt. |
| **Play vs AI** | `#mode-hva` | Radio option activating the Python AI engine. When selected, the computer automatically calculates and executes moves for Player 2 (Yellow). |
| **AI Mode Badge** | `#badge-ai-mode` | Visual badge highlighting that AI mode is active. |
| **Active Player Roster** | `#card-p1`, `#card-p2` | Two cards displaying the player names, disc colors, and current status. The player whose turn it is gains an active glowing border (`.active-card`). |
| **AI Strategy Selector** | `#ai-strategy` | Dropdown selector with 3 operational AI algorithms: <br>• **Alpha-Beta Pruning:** Recommended high-speed search.<br>• **Minimax AI:** Unpruned baseline to observe exponential tree expansion.<br>• **Greedy Heuristic:** Instant tactical evaluation without tree search. |
| **AI Search Depth Slider** | `#ai-depth` | Range slider (1 to 4) controlling how many moves ahead the AI calculates. Adjusting this slider immediately updates the depth badge (`#depth-label`). |
| **Depth Presets** | `.depth-tag` | Quick reference labels: `1: Easy`, `2: Casual`, `3: Medium`, `4: Hard`. |
| **Move Ordering Checkbox** | `#ai-move-ordering` | Toggles tactical move ordering for Alpha-Beta search. Keeping this checked produces the highest cutoff rates and fastest execution. |
| **Transposition Table Checkbox** | `#ai-transposition-table` | Toggles dynamic programming memoization. When checked, the search caches intermediate subproblems, displaying hit rates and memory usage. |
| **⟳ New Game Button** | `#btn-reset` | Instantly clears the server board, resets the UI grid, clears candidate score grids, and restarts the match at Move 1. |

---

### 4.3 Center Panel: Interactive Game Board & Arena
The main arena (`section.panel-board`) where the game is played:

| Element | ID / Selector | Purpose & How to Use Efficiently |
| :--- | :--- | :--- |
| **Alert / Feedback Banner** | `#alert-banner` | Displays error messages (e.g., "Column 3 is full! Please choose another column.") with an animated shake effect. Auto-dismisses after 3 seconds. |
| **Status Bar** | `#status-bar` | Dynamic bar displaying who has the active turn (`#status-text`), an animated disc badge (`#status-disc`), and the current move number badge (`#move-badge`). |
| **Drop Column Buttons** | `#col-buttons`, `.col-btn` | Seven arrow buttons (`▼`) positioned directly above columns 1 through 7. Clicking any button drops a disc into that column. |
| **Interactive Board Grid** | `#board`, `.cell` | 6-row by 7-column grid. You can click directly on any cell in a column to drop a disc. Supports full keyboard navigation (Tab to focus, Enter/Space to drop). |
| **Ghost / Hover Preview** | `.cell.ghost-p1`, `.cell.ghost-p2` | When hovering the mouse over any column, a translucent preview disc appears in the lowest available cell, showing exactly where your disc will settle. |
| **Drop Animation** | `.cell.dropped` | Smooth physical falling animation whenever a disc is placed. |
| **Winning Line Highlight** | `.cell.winning` | When a player connects four, the four winning discs illuminate with a pulsing golden glow and celebratory animation. |
| **Column Number Labels** | `.col-labels` | Clear text indicators (`Col 1` to `Col 7`) beneath each column to eliminate column miscounting. |

---

### 4.4 Right Panel: AI Decision Inspector & Move History
Located on the right side of the screen (`aside.panel-info`). Provides real-time algorithmic telemetry:

| Element | ID / Selector | Purpose & How to Use Efficiently |
| :--- | :--- | :--- |
| **Move History Log** | `#move-history` | A chronological, reverse-ordered list of every drop made during the session. Shows the move number, player name, disc icon, and selected column. |
| **History Counter** | `#history-count` | Badge showing the total number of moves played in the current match. |
| **AI Strategy Badge** | `#ai-active-badge` | Displays which algorithm made the last calculated move. |
| **Chosen Move** | `#ai-chosen-col` | Highlights the optimal column selected by the AI (e.g., `Col 4`). |
| **Evaluation Score** | `#ai-eval-score` | Shows the heuristic value of the position. For terminal wins or losses, automatically translates the score to depth-aware ply count (e.g., `+Win in 3 ply`). |
| **Compute Time** | `#ai-compute-time` | Wall-clock execution latency measured using Python's high-resolution `time.perf_counter()` in milliseconds. |
| **Nodes Visited** | `#ai-nodes-visited` | Total number of board states evaluated during the search. |
| **Recursive Calls** | `#ai-recursive-calls` | Total recursive function invocations dispatched by the algorithm. |
| **Branch Cutoffs (α/β)** | `#ai-cutoffs` | Number of subtrees pruned when $\beta \le \alpha$. Visible when Alpha-Beta Pruning is active. |
| **TT Cache Hits** | `#ai-cache-hits` | Number of times the search encountered a previously evaluated state in the Transposition Table, accompanied by the cache hit percentage. |
| **TT Memory (Est)** | `#ai-tt-memory` | Estimated heap memory consumption in kilobytes allocated by Python for the transposition hash table. |
| **Max Depth Reached** | `#ai-max-depth` | Deepest search tier reached during game-tree exploration. |
| **Tactical Priority / Reason** | `#ai-decision-reason` | High-level rationale explaining the move (e.g., *"Winning move detected: completes 4-in-a-row in column 4"* or *"Blocked opponent win in column 2"*). |
| **Candidate Move Scores Grid** | `#ai-candidates-grid` | An interactive grid displaying the evaluated score for every valid column. Highlights the chosen column in emerald green and full columns in gray. |
| **Decision Tree View** | `#ai-tree-box`, `#btn-toggle-tree` | An expandable visual breakdown of root decision branches showing column-by-column minimax values. |
| **⚡ Compare Search Algorithms Button** | `#btn-compare-algorithms` | Launches the on-demand comparison modal to benchmark the active board position across Minimax, Alpha-Beta (Natural), and Alpha-Beta (Ordered) simultaneously. |
| **Match Scoreboard** | `#score-p1`, `#score-p2`, `#score-draw` | Persistent session scoreboard tracking Player 1 wins, Player 2 / AI wins, and draws across game resets. |

---

### 4.5 Bottom Panel 1: AI Performance & Benchmark Dashboard
Located below the game board (`section.panel-dashboard`). This is the empirical laboratory:

| Element | ID / Selector | Purpose & How to Use Efficiently |
| :--- | :--- | :--- |
| **Test Position Selector** | `#bench-position-select` | Select from curated test scenarios: <br>1. **Opening (Center Move):** Standard opening board.<br>2. **Tactical Block:** Immediate defensive threat test.<br>3. **Midgame Center Battle:** Complex multi-piece contested board.<br>4. **Symmetric Dual-Flank:** Board with high transposition opportunities.<br>5. **⚡ Current Live Board State:** Uses the exact board state currently in your game! |
| **Max Depth Selector** | `#bench-depth-select` | Select the benchmark depth ceiling ($d = 1, 2, 3,$ or $4$). |
| **Repetitions Selector** | `#bench-repeats-select` | Choose 1, 2, 3, or 5 runs. The system takes the **median** run to eliminate background OS scheduling spikes. |
| **Status Badge** | `#bench-status-badge` | Displays benchmark state: `Ready` (emerald), `Running...` (amber with pulse), or `Complete` (blue). |
| **▶ Run Benchmark Suite** | `#btn-run-benchmark` | Dispatches the benchmark to the Flask backend. Executes safely in a detached clone without modifying your live game. |
| **Comparison Table** | `#bench-table` | Displays an authoritative side-by-side table comparing: <br>• Chosen Move & Score<br>• Nodes Visited & Work Reduction %<br>• Cutoffs Count<br>• Cache Hit Rate<br>• Execution Time & Speedup Factor<br>• Heap Memory Consumption |
| **Chart 1: Execution Time** | `#chart-time` | Responsive Chart.js line graph showing wall-clock latency (ms) plotted against search depths 1 through 4. |
| **Chart 2: Nodes Visited** | `#chart-nodes` | Chart illustrating the difference between exponential growth $O(b^d)$ and pruned expansion $O(b^{d/2})$. |
| **Chart 3: Branch Cutoffs** | `#chart-cutoffs` | Bar chart tracking total discarded subtrees across algorithms. |
| **Chart 4: Memory Footprint** | `#chart-memory` | Bar chart tracking memory allocation in KB for Transposition Table memoization. |

---

### 4.6 Bottom Panel 2: DAA Interactive Learning Center
Located at the bottom of the page (`section.panel-daa`). Features five collapsible educational accordions:

1. **Minimax Recurrence & Zero-Sum Search Formulation:** Mathematical formulation of $V(s) = \max_a \min_{a'} V(s'')$, depth-aware utility functions ($+1,000,000 + d \times 1,000$), and recursive stack frame analysis.
2. **Alpha-Beta Pruning Optimization & Cutoff Invariants:** Formal definitions of the $[\alpha, \beta]$ window, cutoff invariants when $\beta \le \alpha$, and equivalence proof showing Minimax and Alpha-Beta produce identical moves.
3. **Tactical Move Ordering Heuristic:** Detailed bonus point breakdown for transposition moves (+50,000), immediate wins (+10,000), blocks (+5,000), and center proximity (+60).
4. **Memoization, Bound Semantics & Transposition Tables:** Explanation of Connect-4 as a Directed Acyclic Graph (DAG), `EXACT`, `LOWER_BOUND`, and `UPPER_BOUND` entry types, and replacement policies.
5. **Theoretical Asymptotics vs. Measured Empirical Reality:** In-depth explanation of why constant-factor overhead, transposition density, and interpreter bytecode create subtle variations in real-world benchmarks.

---

### 4.7 Modals & Overlays

#### A. Game Over Celebration Modal (`#game-over-modal`)
- Automatically appears when a win or draw occurs.
- Displays the winner's colored disc icon, celebratory headline (`#modal-title`), winning alignment description (`#modal-subtitle`), and total moves played (`#modal-move-count`).
- Includes a **"⟳ Play Again"** button (`#modal-btn-reset`) to start a new match immediately.
- Pressing `Escape` or clicking outside dismisses the modal.

#### B. Search Algorithm Comparison Modal (`#comparison-modal`)
- Triggered by clicking the **"⚡ Compare Search Algorithms"** button in the AI Decision Panel.
- Executes an immediate three-way race on the **exact current board position**:
  1. Minimax (Unpruned)
  2. Alpha-Beta (Natural Column Order)
  3. Alpha-Beta (Tactical Move Ordering)
- Displays an instant comparison table showing score equivalence, nodes saved, and speedup percentage.

---

## 5. Step-by-Step Workflows for Maximum Efficiency

### Workflow A: Playing Against the AI
1. In the **Game Controls** panel, ensure **Play vs AI** (`#mode-hva`) is selected.
2. Choose your preferred AI Strategy from the dropdown:
   - For a casual, instant-response match: Select **Greedy Heuristic**.
   - For a balanced tactical challenge: Select **Alpha-Beta Pruning** at **Depth 3 (Medium)**.
   - For an expert-level opponent: Select **Alpha-Beta Pruning** at **Depth 4 (Hard)** with **Move Ordering** and **Transposition Table** enabled.
3. Drop your Red disc by clicking your preferred column button (`▼`) or hovering over the board.
4. Watch the AI calculate: the status bar will show *"AI is thinking..."* and the AI Decision Panel will display the move chosen, the evaluation score, and candidate column scores.

---

### Workflow B: Comparing Algorithms on Live Positions
To demonstrate that Alpha-Beta Pruning preserves Minimax decisions while exploring significantly fewer nodes:
1. Play 4–6 moves in **Play vs AI** mode until a contested board position develops.
2. In the **AI Decision Panel**, click **⚡ Compare Search Algorithms**.
3. Inspect the comparison modal:
   - Verify that **all three algorithms return the exact same chosen move and score**.
   - Observe that Alpha-Beta with Move Ordering evaluates **50% to 75% fewer nodes** than standard Minimax.
   - Close the modal with the close button (`×`) or the `Escape` key.

---

### Workflow C: Running Empirical Benchmarks & Exporting Insights
To generate empirical data for reports or lab records:
1. Scroll down to the **AI Performance & Benchmark Dashboard**.
2. Select a test scenario from the **Test Position** dropdown (e.g., `3. Midgame Center Battle` or `⚡ Current Live Board State`).
3. Select **Max Depth: 4** and **Repetitions: 3 Runs (Median)**.
4. Click **▶ Run Benchmark Suite**.
5. Once complete, analyze:
   - The **Summary Table** for work reduction percentages and speedup factors.
   - The **Chart Visualizations** for the exponential vs. sub-exponential curvature.

---

### Workflow D: Classroom & Viva Demonstrations
For faculty review, project evaluation, or college vivas:
1. **Show Modularity:** Point out the clean separation between the Game Engine (`game/engine.py`), AI algorithms (`algorithms/`), REST API (`app.py`), and interactive frontend (`static/`).
2. **Demonstrate Correctness:** Show the **Score Equivalence Invariant** via the comparison modal to prove pruning does not miss optimal moves.
3. **Demonstrate Cache Efficiency:** Run a benchmark on the `Symmetric Dual-Flank` position to show high Transposition Table hit rates ($>20\%$).
4. **Reference Complexity:** Open the **DAA Learning Center** accordions at the bottom to walk through the recurrence equations and asymptotic proofs.

---

## 6. Keyboard Controls & Accessibility Features

The platform includes comprehensive keyboard and screen-reader accessibility:

| Key / Action | Context | Result |
| :--- | :--- | :--- |
| `Tab` / `Shift+Tab` | Whole Page | Moves focus sequentially through interactive controls, buttons, and board cells. |
| `Enter` or `Space` | Focused Column Button (`.col-btn`) | Drops a disc into the focused column. |
| `Enter` or `Space` | Focused Board Cell (`.cell`) | Drops a disc into that cell's column. |
| `Escape` | Active Modal Overlay | Closes the Game Over or Comparison modal. |
| Screen Readers | Interactive Cells | Reads out row, column, occupancy status, and winning state (e.g., *"Row 6, Column 4: Player 1 (Red) (Winning disc)"*). |

---

## 7. Frequently Asked Questions (FAQ) & Troubleshooting

### Q1: Why is column click not responding?
- **Game Over:** If the game has already concluded, you must click **⟳ New Game** or **Play Again** before new moves can be made.
- **AI Turn:** When playing against the AI, user input is temporarily disabled while the AI calculates to prevent race conditions.
- **Column Full:** If a column already contains 6 discs, it cannot accept additional discs. The alert banner will notify you.

### Q2: Does running a benchmark disrupt my ongoing game?
**No.** The benchmark suite creates detached in-memory clones of the board state. Your live board, score, and move history remain completely isolated and intact.

### Q3: What do the scores `+Win in 3 ply` or `-Loss in 2 ply` mean?
The AI uses **depth-aware terminal scoring**:
- `+Win in 3 ply` means the AI has identified a forced victory within 3 turns ($+1,000,000 + 3 \times 1,000 = +1,003,000$).
- `-Loss in 2 ply` means the AI detects an unavoidable loss within 2 turns and is attempting to delay it.

### Q4: Why does Depth 4 take longer on Minimax than Alpha-Beta?
At depth 4, Minimax must evaluate all $7^4 = 2,401$ theoretical leaf paths. In contrast, Alpha-Beta with Move Ordering prunes dominated branches early, typically evaluating only $400\text{--}700$ nodes, yielding a $3\times\text{--}5\times$ speedup.

### Q5: How do I verify all automated tests?
Run `pytest` from your terminal:
```powershell
.\venv\Scripts\pytest -v
```
All **173 tests** across 10 test modules will run and validate game rules, heuristics, pruning cutoffs, and REST endpoints.
