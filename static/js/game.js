/**
 * game.js — Connect-4 frontend game controller.
 *
 * Responsibilities
 * ----------------
 * - Render authoritative board state received from Flask API endpoints.
 * - Interactive board: click columns or board cells to drop discs.
 * - Dynamic ghost preview: displays where the disc will land in the player's color.
 * - Clear invalid-move feedback with user-facing alert banner and shake animation.
 * - Visual turn indicators: active player card, pulsating disc, and move badges.
 * - Celebratory game-over modal on win or draw with restart shortcut.
 * - Mode selection: toggle between Local 2-Player (hvh) and Human vs Greedy AI (hva).
 * - Real-time AI Decision Panel: displays chosen move, heuristic evaluation,
 *   decision reasoning, execution time, and candidate move scores.
 * - Accessible ARIA attributes and keyboard navigation (Enter/Space on cells).
 *
 * Communication model
 * -------------------
 * All game state, rules validation, and AI calculations are strictly authoritative
 * on the server (Python). The client renders snapshots and manages user interactions.
 */

"use strict";

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
const State = {
  scores: { 1: 0, 2: 0, draw: 0 },
  lastPlacedCell: null,     // {row, col}
  currentSnapshot: null,    // cache authoritative server state
  hoveredCol: null,         // currently hovered column index
  alertTimeout: null,       // timer handle for auto-dismissing feedback banner
  isProcessing: false,      // flag preventing double-clicks or moves during AI turn
};

// ---------------------------------------------------------------------------
// DOM References
// ---------------------------------------------------------------------------
let DOM = {};

function initDOM() {
  DOM = {
    board:              document.getElementById("board"),
    statusBar:          document.getElementById("status-bar"),
    statusDisc:         document.getElementById("status-disc"),
    statusText:         document.getElementById("status-text"),
    moveBadge:          document.getElementById("move-badge"),
    colButtons:         Array.from(document.querySelectorAll(".col-btn")),
    moveHistory:        document.getElementById("move-history"),
    historyCount:       document.getElementById("history-count"),
    alertBanner:        document.getElementById("alert-banner"),
    gameOverModal:      document.getElementById("game-over-modal"),
    modalBadge:         document.getElementById("modal-badge"),
    modalTitle:         document.getElementById("modal-title"),
    modalSubtitle:      document.getElementById("modal-subtitle"),
    modalMoveCount:     document.getElementById("modal-move-count"),
    modalBtnReset:      document.getElementById("modal-btn-reset"),
    cardP1:             document.getElementById("card-p1"),
    cardP2:             document.getElementById("card-p2"),
    labelP1:            document.getElementById("label-p1"),
    labelP2:            document.getElementById("label-p2"),
    subP1:              document.getElementById("sub-p1"),
    subP2:              document.getElementById("sub-p2"),
    scoreP1:            document.getElementById("score-p1"),
    scoreP2:            document.getElementById("score-p2"),
    scoreDraw:          document.getElementById("score-draw"),
    scoreNameP1:        document.getElementById("score-name-p1"),
    scoreNameP2:        document.getElementById("score-name-p2"),
    btnReset:           document.getElementById("btn-reset"),
    modeRadios:         Array.from(document.querySelectorAll('input[name="mode"]')),
    aiStrategySelect:   document.getElementById("ai-strategy"),
    aiEmptyState:       document.getElementById("ai-empty-state"),
    aiDataContainer:    document.getElementById("ai-data-container"),
    aiChosenCol:        document.getElementById("ai-chosen-col"),
    aiEvalScore:        document.getElementById("ai-eval-score"),
    aiComputeTime:      document.getElementById("ai-compute-time"),
    aiDecisionReason:   document.getElementById("ai-decision-reason"),
    aiCandidatesGrid:   document.getElementById("ai-candidates-grid"),
    aiActiveBadge:      document.getElementById("ai-active-badge"),
  };
}

// ---------------------------------------------------------------------------
// Feedback & Alerts
// ---------------------------------------------------------------------------

/**
 * Display an authoritative feedback alert banner and shake the board.
 * @param {string} message  Error message text
 */
function showAlert(message) {
  if (!DOM.alertBanner) return;

  DOM.alertBanner.textContent = `⚠️ ${message}`;
  DOM.alertBanner.classList.remove("hidden");

  // Shake effect on board
  if (DOM.board) {
    DOM.board.classList.remove("shake");
    void DOM.board.offsetWidth; // Trigger reflow
    DOM.board.classList.add("shake");
  }

  if (State.alertTimeout) clearTimeout(State.alertTimeout);
  State.alertTimeout = setTimeout(() => {
    hideAlert();
  }, 3200);
}

function hideAlert() {
  if (DOM.alertBanner) {
    DOM.alertBanner.classList.add("hidden");
    DOM.alertBanner.textContent = "";
  }
}

// ---------------------------------------------------------------------------
// Board & Disc Rendering
// ---------------------------------------------------------------------------

/**
 * Render the 6x7 grid from the server snapshot.
 * @param {number[][]} grid  6×7 nested array
 * @param {Array}      winningCells  list of [row, col] pairs
 */
function renderBoard(grid, winningCells = []) {
  const winSet = new Set(winningCells.map(([r, c]) => `${r}-${c}`));
  const cells = DOM.board.querySelectorAll(".cell");

  cells.forEach(cell => {
    const r = parseInt(cell.dataset.row, 10);
    const c = parseInt(cell.dataset.col, 10);
    const val = grid[r][c];

    // Clear transient classes
    cell.classList.remove("p1", "p2", "winning", "dropped");

    if (val === 1) {
      cell.classList.add("p1");
      cell.setAttribute("aria-label", `Row ${r + 1}, Column ${c + 1}: Player 1 (Red)`);
    } else if (val === 2) {
      cell.classList.add("p2");
      cell.setAttribute("aria-label", `Row ${r + 1}, Column ${c + 1}: Player 2 (Yellow)`);
    } else {
      cell.setAttribute("aria-label", `Row ${r + 1}, Column ${c + 1}: empty`);
    }

    if (winSet.has(`${r}-${c}`)) {
      cell.classList.add("winning");
      cell.setAttribute("aria-label", `${cell.getAttribute("aria-label")} (Winning disc)`);
    }

    // Drop animation for the last placed disc
    if (
      State.lastPlacedCell &&
      State.lastPlacedCell.row === r &&
      State.lastPlacedCell.col === c &&
      val !== 0
    ) {
      cell.classList.add("dropped");
    }
  });

  // Re-apply hover preview if a column is hovered
  if (State.hoveredCol !== null && State.currentSnapshot && !State.currentSnapshot.game_over && !State.isProcessing) {
    applyHoverPreview(State.hoveredCol);
  }
}

/**
 * Update the status bar, active player cards, and move counter badge.
 * @param {object} snap  Authoritative board snapshot
 */
function renderStatus(snap) {
  const bar  = DOM.statusBar;
  const disc = DOM.statusDisc;
  const text = DOM.statusText;
  const badge = DOM.moveBadge;

  bar.classList.remove("p1-turn", "p2-turn", "p1-win", "p2-win", "draw");
  disc.classList.remove("p1", "p2", "thinking-pulse");

  const isHvA = snap.game_mode === "hva";

  // Dynamic names
  const p1Name = isHvA ? "Human (Red)" : "Player 1 (Red)";
  const p2Name = isHvA ? "Greedy AI (Yellow)" : "Player 2 (Yellow)";

  // Update Roster Card labels
  if (DOM.labelP1 && DOM.labelP2) {
    DOM.labelP1.textContent = isHvA ? "Human" : "Player 1";
    DOM.subP1.textContent = "Red Discs";
    DOM.labelP2.textContent = isHvA ? "Greedy AI" : "Player 2";
    DOM.subP2.textContent = isHvA ? "Yellow Discs (Python)" : "Yellow Discs";
  }

  // Update Score Board names
  if (DOM.scoreNameP1 && DOM.scoreNameP2) {
    DOM.scoreNameP1.textContent = p1Name;
    DOM.scoreNameP2.textContent = p2Name;
  }

  // Roster card active states
  if (DOM.cardP1 && DOM.cardP2) {
    DOM.cardP1.classList.toggle("active-card", !snap.game_over && snap.current_player === 1);
    DOM.cardP2.classList.toggle("active-card", !snap.game_over && snap.current_player === 2);
  }

  if (snap.game_over) {
    if (snap.is_draw) {
      text.textContent = "Match Ended in a Draw!";
      bar.classList.add("draw");
      disc.style.display = "none";
    } else {
      const winnerName = snap.winner === 1 ? p1Name : p2Name;
      text.textContent = `${winnerName} Wins! 🎉`;
      bar.classList.add(snap.winner === 1 ? "p1-win" : "p2-win");
      disc.style.display = "inline-block";
      disc.classList.add(snap.winner === 1 ? "p1" : "p2");
    }
    badge.textContent = `${snap.move_count} moves played`;
  } else {
    if (isHvA && snap.current_player === 2 && State.isProcessing) {
      text.textContent = "Greedy AI is thinking...";
      bar.classList.add("p2-turn");
      disc.style.display = "inline-block";
      disc.classList.add("p2", "thinking-pulse");
      badge.textContent = `Move ${snap.move_count + 1}`;
    } else {
      const currentName = snap.current_player === 1 ? `${p1Name}'s turn` : `${p2Name}'s turn`;
      text.textContent = currentName;
      bar.classList.add(snap.current_player === 1 ? "p1-turn" : "p2-turn");
      disc.style.display = "inline-block";
      disc.classList.add(snap.current_player === 1 ? "p1" : "p2");
      badge.textContent = `Move ${snap.move_count + 1}`;
    }
  }
}

/**
 * Update the AI Decision Info Panel.
 * @param {object} snap
 */
function renderAIDecision(snap) {
  if (!DOM.aiInfo) return;

  const decision = snap.ai_decision;
  const isHvA = snap.game_mode === "hva";

  if (!isHvA || !decision) {
    if (DOM.aiEmptyState) DOM.aiEmptyState.classList.remove("hidden");
    if (DOM.aiDataContainer) DOM.aiDataContainer.classList.add("hidden");
    if (DOM.aiActiveBadge) {
      DOM.aiActiveBadge.textContent = isHvA ? "Greedy AI" : "2-Player";
    }
    return;
  }

  if (DOM.aiEmptyState) DOM.aiEmptyState.classList.add("hidden");
  if (DOM.aiDataContainer) DOM.aiDataContainer.classList.remove("hidden");
  if (DOM.aiActiveBadge) DOM.aiActiveBadge.textContent = "Greedy Decision";

  DOM.aiChosenCol.textContent = `Column ${decision.column + 1}`;
  DOM.aiEvalScore.textContent = decision.score > 0 ? `+${decision.score}` : `${decision.score}`;
  DOM.aiComputeTime.textContent = `${decision.execution_time_ms} ms`;
  DOM.aiDecisionReason.textContent = decision.reason;

  // Render candidate score pills
  if (DOM.aiCandidatesGrid && decision.candidate_scores) {
    DOM.aiCandidatesGrid.innerHTML = "";
    Object.keys(decision.candidate_scores).sort((a, b) => parseInt(a, 10) - parseInt(b, 10)).forEach(colStr => {
      const col = parseInt(colStr, 10);
      const score = decision.candidate_scores[colStr];
      const pill = document.createElement("span");
      pill.className = "candidate-pill";
      if (col === decision.column) pill.classList.add("chosen");
      if (score > 0) pill.classList.add("positive");
      if (score < 0) pill.classList.add("negative");

      const mark = col === decision.column ? "★ " : "";
      pill.textContent = `${mark}Col ${col + 1}: ${score > 0 ? "+" + score : score}`;
      DOM.aiCandidatesGrid.appendChild(pill);
    });
  }
}

/**
 * Update game-over celebration overlay modal.
 * @param {object} snap
 */
function renderGameOverModal(snap) {
  if (!DOM.gameOverModal) return;

  if (!snap.game_over) {
    DOM.gameOverModal.classList.add("hidden");
    return;
  }

  DOM.modalBadge.classList.remove("p1", "p2", "draw");

  const isHvA = snap.game_mode === "hva";
  const p1Name = isHvA ? "Human (Red)" : "Player 1 (Red)";
  const p2Name = isHvA ? "Greedy AI (Yellow)" : "Player 2 (Yellow)";

  if (snap.is_draw) {
    DOM.modalBadge.classList.add("draw");
    DOM.modalBadge.textContent = "½";
    DOM.modalTitle.textContent = "It's a Draw!";
    DOM.modalSubtitle.textContent = "Board is completely filled with no 4-in-a-row.";
  } else {
    DOM.modalBadge.textContent = "";
    DOM.modalBadge.classList.add(snap.winner === 1 ? "p1" : "p2");
    const name = snap.winner === 1 ? p1Name : p2Name;
    DOM.modalTitle.textContent = `${name} Wins!`;
    DOM.modalSubtitle.textContent = "Successfully connected 4 discs in a line.";
  }

  DOM.modalMoveCount.textContent = `Completed in ${snap.move_count} moves`;
  DOM.gameOverModal.classList.remove("hidden");
}

/**
 * Enable or disable column drop buttons.
 * @param {number[]} validCols
 * @param {boolean}  gameOver
 */
function renderColumnButtons(validCols, gameOver) {
  const validSet = new Set(validCols);
  DOM.colButtons.forEach(btn => {
    const col = parseInt(btn.dataset.col, 10);
    btn.disabled = gameOver || State.isProcessing || !validSet.has(col);
  });
}

/**
 * Render the full move history list.
 * @param {Array} history
 * @param {string} mode
 */
function rebuildMoveHistory(history, mode = "hvh") {
  DOM.moveHistory.innerHTML = "";
  if (!history || history.length === 0) {
    const emptyLi = document.createElement("li");
    emptyLi.className = "history-empty";
    emptyLi.textContent = "No moves played yet. Click any column to begin!";
    DOM.moveHistory.appendChild(emptyLi);
    if (DOM.historyCount) DOM.historyCount.textContent = "0 moves";
    return;
  }

  if (DOM.historyCount) {
    DOM.historyCount.textContent = `${history.length} move${history.length === 1 ? "" : "s"}`;
  }

  const isHvA = mode === "hva";
  [...history].reverse().forEach(entry => {
    const li = document.createElement("li");
    const playerClass = entry.player === 1 ? "p1-tag" : "p2-tag";
    const playerName  = entry.player === 1
      ? (isHvA ? "Human" : "P1")
      : (isHvA ? "Greedy AI" : "P2");
    li.innerHTML = `
      <span class="${playerClass}">#${entry.move_number} ${playerName}</span>
      <span class="move-coord">Col ${entry.col + 1}, Row ${entry.row + 1}</span>
    `;
    DOM.moveHistory.appendChild(li);
  });
}

/**
 * Update the match scoreboard counters.
 * @param {object} snap
 */
function updateScores(snap) {
  if (!snap.game_over) return;
  if (snap.is_draw) {
    State.scores.draw += 1;
  } else if (snap.winner === 1 || snap.winner === 2) {
    State.scores[snap.winner] += 1;
  }
  DOM.scoreP1.textContent   = State.scores[1];
  DOM.scoreP2.textContent   = State.scores[2];
  DOM.scoreDraw.textContent = State.scores.draw;
}

/**
 * Redraw the entire UI from an authoritative server snapshot.
 * @param {object} snap
 */
function applySnapshot(snap) {
  State.currentSnapshot = snap;

  // Sync mode radio selection
  if (DOM.modeRadios) {
    DOM.modeRadios.forEach(r => {
      r.checked = (r.value === snap.game_mode);
    });
  }

  renderBoard(snap.grid, snap.winning_cells || []);
  renderStatus(snap);
  renderAIDecision(snap);
  renderColumnButtons(snap.valid_columns || [], snap.game_over);
  renderGameOverModal(snap);
  rebuildMoveHistory(snap.move_history || [], snap.game_mode);
}

// ---------------------------------------------------------------------------
// API Communication
// ---------------------------------------------------------------------------

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  return { ok: res.ok, status: res.status, data };
}

async function loadBoard() {
  const result = await fetchJSON("/api/board");
  if (result.ok) {
    State.lastPlacedCell = null;
    applySnapshot(result.data);
  } else {
    showAlert("Could not connect to Python game engine.");
  }
}

async function sendMove(col) {
  if (State.isProcessing) return;

  // Check client-side against authoritative snapshot
  if (State.currentSnapshot) {
    if (State.currentSnapshot.game_over) {
      showAlert("The game has already ended! Click 'New Game' or 'Play Again' to start a new match.");
      return;
    }
    const validSet = new Set(State.currentSnapshot.valid_columns || []);
    if (!validSet.has(col)) {
      showAlert(`Column ${col + 1} is already full! Please select an open column.`);
      return;
    }
  }

  State.isProcessing = true;
  disableAllColumns();
  hideAlert();

  const result = await fetchJSON("/api/move", {
    method: "POST",
    body: JSON.stringify({ col }),
  });

  if (!result.ok) {
    const errorMsg = (result.data && result.data.error) || "Move rejected by server.";
    showAlert(errorMsg);
    State.isProcessing = false;
    if (result.data && result.data.grid) {
      applySnapshot(result.data);
    } else if (State.currentSnapshot) {
      enableValidColumns(State.currentSnapshot.valid_columns || []);
    }
    return;
  }

  const snap = result.data;
  State.lastPlacedCell = { row: snap.placed_row, col: snap.placed_col };
  applySnapshot(snap);
  updateScores(snap);

  // If playing against AI and game continues, trigger AI turn
  if (!snap.game_over && snap.game_mode === "hva" && snap.current_player === snap.ai_player) {
    renderStatus(snap); // Updates to "Greedy AI is thinking..."
    // Natural tactical pause (300ms) for smooth visual disc drop
    setTimeout(async () => {
      await triggerAIMove();
    }, 300);
  } else {
    State.isProcessing = false;
    enableValidColumns(snap.valid_columns || []);
  }
}

async function triggerAIMove() {
  const result = await fetchJSON("/api/ai-move", { method: "POST" });
  State.isProcessing = false;

  if (!result.ok) {
    const errorMsg = (result.data && result.data.error) || "AI move failed.";
    showAlert(errorMsg);
    if (result.data && result.data.grid) applySnapshot(result.data);
    return;
  }

  const snap = result.data;
  State.lastPlacedCell = { row: snap.placed_row, col: snap.placed_col };
  applySnapshot(snap);
  updateScores(snap);
}

async function sendReset() {
  State.isProcessing = false;
  hideAlert();
  if (DOM.gameOverModal) DOM.gameOverModal.classList.add("hidden");

  const activeMode = DOM.modeRadios.find(r => r.checked)?.value || "hvh";
  const result = await fetchJSON("/api/reset", {
    method: "POST",
    body: JSON.stringify({ mode: activeMode }),
  });

  if (result.ok) {
    State.lastPlacedCell = null;
    clearHoverPreview();
    applySnapshot(result.data);
  } else {
    showAlert("Failed to reset game.");
  }
}

async function switchMode(newMode) {
  State.isProcessing = false;
  hideAlert();
  const result = await fetchJSON("/api/mode", {
    method: "POST",
    body: JSON.stringify({ mode: newMode, ai_strategy: "greedy" }),
  });

  if (result.ok) {
    State.lastPlacedCell = null;
    clearHoverPreview();
    applySnapshot(result.data);
  } else {
    showAlert("Failed to switch game mode.");
  }
}

// ---------------------------------------------------------------------------
// Interactive Column & Cell Hover Preview
// ---------------------------------------------------------------------------

function clearHoverPreview() {
  DOM.board.querySelectorAll(".cell").forEach(cell => {
    cell.classList.remove("col-hover", "preview-p1", "preview-p2");
  });
}

function applyHoverPreview(col) {
  clearHoverPreview();
  if (State.isProcessing) return;
  if (!State.currentSnapshot || State.currentSnapshot.game_over) return;

  const validSet = new Set(State.currentSnapshot.valid_columns || []);
  if (!validSet.has(col)) return;

  const grid = State.currentSnapshot.grid;
  const player = State.currentSnapshot.current_player;

  // Find lowest open row in this column
  let lowestOpenRow = -1;
  for (let r = 5; r >= 0; r--) {
    if (grid[r][col] === 0) {
      lowestOpenRow = r;
      break;
    }
  }

  DOM.board.querySelectorAll(`.cell[data-col="${col}"]`).forEach(cell => {
    const r = parseInt(cell.dataset.row, 10);
    cell.classList.add("col-hover");
    if (r === lowestOpenRow) {
      cell.classList.add(player === 1 ? "preview-p1" : "preview-p2");
    }
  });
}

function attachBoardInteractions() {
  // Top column drop buttons
  DOM.colButtons.forEach(btn => {
    const col = parseInt(btn.dataset.col, 10);

    btn.addEventListener("mouseenter", () => {
      State.hoveredCol = col;
      applyHoverPreview(col);
    });

    btn.addEventListener("mouseleave", () => {
      State.hoveredCol = null;
      clearHoverPreview();
    });

    btn.addEventListener("click", () => {
      sendMove(col);
    });
  });

  // Hover & Click directly on board cells
  DOM.board.addEventListener("mouseover", e => {
    const cell = e.target.closest(".cell");
    if (!cell) return;
    const col = parseInt(cell.dataset.col, 10);
    if (!isNaN(col)) {
      State.hoveredCol = col;
      applyHoverPreview(col);
    }
  });

  DOM.board.addEventListener("mouseleave", () => {
    State.hoveredCol = null;
    clearHoverPreview();
  });

  DOM.board.addEventListener("click", e => {
    const cell = e.target.closest(".cell");
    if (!cell) return;
    const col = parseInt(cell.dataset.col, 10);
    if (!isNaN(col)) {
      sendMove(col);
    }
  });

  // Keyboard navigation on cells (Enter or Space)
  DOM.board.addEventListener("keydown", e => {
    if (e.key === "Enter" || e.key === " ") {
      const cell = e.target.closest(".cell");
      if (cell) {
        e.preventDefault();
        const col = parseInt(cell.dataset.col, 10);
        if (!isNaN(col)) sendMove(col);
      }
    }
  });

  // Game Mode Radio Switchers
  DOM.modeRadios.forEach(radio => {
    radio.addEventListener("change", () => {
      if (radio.checked) {
        switchMode(radio.value);
      }
    });
  });
}

// ---------------------------------------------------------------------------
// Column Button Helpers
// ---------------------------------------------------------------------------

function disableAllColumns() {
  DOM.colButtons.forEach(b => { b.disabled = true; });
}

function enableValidColumns(validCols) {
  if (State.isProcessing) return;
  const vs = new Set(validCols);
  DOM.colButtons.forEach(b => {
    b.disabled = !vs.has(parseInt(b.dataset.col, 10));
  });
}

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", async () => {
  initDOM();
  attachBoardInteractions();

  // Reset buttons (panel + modal)
  if (DOM.btnReset) DOM.btnReset.addEventListener("click", sendReset);
  if (DOM.modalBtnReset) DOM.modalBtnReset.addEventListener("click", sendReset);

  // Load initial board state from authoritative Python engine
  await loadBoard();
});
