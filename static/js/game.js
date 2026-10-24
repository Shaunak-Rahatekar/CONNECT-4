/**
 * game.js — Connect-4 frontend game controller.
 *
 * Responsibilities
 * ----------------
 * - Render the board state received from the Flask API.
 * - Handle column-drop button clicks and send POST /api/move.
 * - Animate disc placement.
 * - Display status, move history, winning cells, and scores.
 * - Handle game reset (POST /api/reset).
 * - Hover preview for the current player's colour.
 *
 * Communication model
 * -------------------
 * All game state is authoritative on the server (Python).
 * The client requests state changes via fetch() and re-renders from the
 * response.  No local game-logic is duplicated here.
 */

"use strict";

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
const State = {
  scores: { 1: 0, 2: 0, draw: 0 },
  lastPlacedCell: null,   // {row, col} — used to attach drop animation class
};

// ---------------------------------------------------------------------------
// DOM references (resolved once at DOMContentLoaded)
// ---------------------------------------------------------------------------
let DOM = {};

function initDOM() {
  DOM = {
    board:       document.getElementById("board"),
    statusBar:   document.getElementById("status-bar"),
    statusText:  document.getElementById("status-text"),
    colButtons:  Array.from(document.querySelectorAll(".col-btn")),
    moveHistory: document.getElementById("move-history"),
    aiInfo:      document.getElementById("ai-info"),
    scoreP1:     document.getElementById("score-p1"),
    scoreP2:     document.getElementById("score-p2"),
    scoreDraw:   document.getElementById("score-draw"),
    btnReset:    document.getElementById("btn-reset"),
    depthSlider: document.getElementById("ai-depth"),
    depthLabel:  document.getElementById("depth-label"),
  };
}

// ---------------------------------------------------------------------------
// Board rendering
// ---------------------------------------------------------------------------

/**
 * Render the full board grid from the server snapshot.
 * @param {number[][]} grid  6×7 nested array (0=empty, 1=P1, 2=P2)
 * @param {Array}      winningCells  list of [row, col] pairs (may be empty)
 */
function renderBoard(grid, winningCells = []) {
  const winSet = new Set(winningCells.map(([r, c]) => `${r}-${c}`));
  const cells = DOM.board.querySelectorAll(".cell");

  cells.forEach(cell => {
    const r = parseInt(cell.dataset.row, 10);
    const c = parseInt(cell.dataset.col, 10);
    const val = grid[r][c];

    // Reset classes
    cell.classList.remove("p1", "p2", "winning", "dropped", "hover-preview");

    if (val === 1) cell.classList.add("p1");
    if (val === 2) cell.classList.add("p2");

    if (winSet.has(`${r}-${c}`)) cell.classList.add("winning");

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
}

/**
 * Update the status bar text and colour class.
 * @param {object} snap  Full board snapshot from the API
 */
function renderStatus(snap) {
  const bar  = DOM.statusBar;
  const text = DOM.statusText;

  bar.classList.remove("p1-turn", "p2-turn", "p1-win", "p2-win", "draw");

  if (snap.game_over) {
    if (snap.is_draw) {
      text.textContent = "It's a draw!";
      bar.classList.add("draw");
    } else {
      const name = snap.winner === 1 ? "Player 1 (Red)" : "Player 2 (Yellow)";
      text.textContent = `${name} wins! 🎉`;
      bar.classList.add(snap.winner === 1 ? "p1-win" : "p2-win");
    }
  } else {
    const name = snap.current_player === 1 ? "Player 1 (Red)" : "Player 2 (Yellow)";
    text.textContent = `${name}'s turn`;
    bar.classList.add(snap.current_player === 1 ? "p1-turn" : "p2-turn");
  }
}

/**
 * Enable or disable column buttons based on validity and game state.
 * @param {number[]} validCols  columns that can accept a disc
 * @param {boolean}  gameOver
 */
function renderColumnButtons(validCols, gameOver) {
  const validSet = new Set(validCols);
  DOM.colButtons.forEach(btn => {
    const col = parseInt(btn.dataset.col, 10);
    btn.disabled = gameOver || !validSet.has(col);
  });
}

/**
 * Append a single move to the move-history list.
 * @param {object} entry  {move_number, player, col, row}
 */
function appendMoveHistory(entry) {
  const li = document.createElement("li");
  const playerClass = entry.player === 1 ? "p1-tag" : "p2-tag";
  const playerName  = entry.player === 1 ? "P1" : "P2";
  li.innerHTML = `<span class="${playerClass}">${playerName}</span> → Col ${entry.col + 1} (row ${entry.row + 1})`;
  DOM.moveHistory.prepend(li);  // newest at top (list is reversed)
}

/**
 * Rebuild the full move history list from scratch (used on reset / board fetch).
 * @param {Array} history
 */
function rebuildMoveHistory(history) {
  DOM.moveHistory.innerHTML = "";
  [...history].reverse().forEach(appendMoveHistory);
}

/**
 * Update score counters after a game-over.
 * @param {object} snap
 */
function updateScores(snap) {
  if (!snap.game_over) return;
  if (snap.is_draw) {
    State.scores.draw += 1;
  } else {
    State.scores[snap.winner] += 1;
  }
  DOM.scoreP1.textContent   = State.scores[1];
  DOM.scoreP2.textContent   = State.scores[2];
  DOM.scoreDraw.textContent = State.scores.draw;
}

// ---------------------------------------------------------------------------
// Full re-render from a snapshot
// ---------------------------------------------------------------------------

/**
 * Redraw every UI element from a full server snapshot object.
 * @param {object} snap
 */
function applySnapshot(snap) {
  renderBoard(snap.grid, snap.winning_cells);
  renderStatus(snap);
  renderColumnButtons(snap.valid_columns, snap.game_over);
  rebuildMoveHistory(snap.move_history);
}

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  return res.json();
}

async function loadBoard() {
  const snap = await fetchJSON("/api/board");
  State.lastPlacedCell = null;
  applySnapshot(snap);
}

async function sendMove(col) {
  disableAllColumns();
  const snap = await fetchJSON("/api/move", {
    method: "POST",
    body: JSON.stringify({ col }),
  });

  if (snap.error) {
    console.warn("Move error:", snap.error);
    enableValidColumns(snap.valid_columns || []);
    return;
  }

  State.lastPlacedCell = { row: snap.placed_row, col: snap.placed_col };
  applySnapshot(snap);
  updateScores(snap);
}

async function sendReset() {
  const snap = await fetchJSON("/api/reset", { method: "POST" });
  State.lastPlacedCell = null;
  applySnapshot(snap);
}

// ---------------------------------------------------------------------------
// Hover preview
// ---------------------------------------------------------------------------

function attachHoverPreview() {
  DOM.colButtons.forEach(btn => {
    btn.addEventListener("mouseenter", () => {
      if (btn.disabled) return;
      const col = parseInt(btn.dataset.col, 10);
      highlightColumn(col, true);
    });
    btn.addEventListener("mouseleave", () => {
      const col = parseInt(btn.dataset.col, 10);
      highlightColumn(col, false);
    });
  });
}

function highlightColumn(col, on) {
  DOM.board.querySelectorAll(`.cell[data-col="${col}"]`).forEach(cell => {
    if (cell.classList.contains("p1") || cell.classList.contains("p2")) return;
    cell.classList.toggle("hover-preview", on);
  });
}

// ---------------------------------------------------------------------------
// Utility
// ---------------------------------------------------------------------------

function disableAllColumns() {
  DOM.colButtons.forEach(b => { b.disabled = true; });
}

function enableValidColumns(validCols) {
  const vs = new Set(validCols);
  DOM.colButtons.forEach(b => {
    b.disabled = !vs.has(parseInt(b.dataset.col, 10));
  });
}

// ---------------------------------------------------------------------------
// Depth slider
// ---------------------------------------------------------------------------

function initDepthSlider() {
  DOM.depthSlider.addEventListener("input", () => {
    DOM.depthLabel.textContent = DOM.depthSlider.value;
  });
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", async () => {
  initDOM();
  initDepthSlider();
  attachHoverPreview();

  // Wire up column drop buttons
  DOM.colButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const col = parseInt(btn.dataset.col, 10);
      sendMove(col);
    });
  });

  // Wire up reset button
  DOM.btnReset.addEventListener("click", sendReset);

  // Load initial board state from the server
  await loadBoard();
});
