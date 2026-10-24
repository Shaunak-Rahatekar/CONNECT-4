/**
 * static/js/engine.js — High-Performance Client-Side Connect-4 Engine & AI Suite.
 *
 * Implements:
 * 1. Authoritative 6x7 Board with in-place drop/undo backtracking and 4-way win detection.
 * 2. Sliding-Window Heuristic Evaluator (all 69 four-windows + center dominance bonus).
 * 3. Greedy Heuristic AI (tactical win -> block -> heuristic -> center tie-breaking).
 * 4. Minimax Search with depth-aware terminal utility (+-1,000,000 +- d*1,000).
 * 5. Alpha-Beta Pruning with Cutoffs (beta <= alpha) and Tactical Move Ordering.
 * 6. Dynamic Programming Transposition Table with EXACT / LOWER_BOUND / UPPER_BOUND flags.
 * 7. Benchmark Suite with Curated Positions & Median Aggregation.
 *
 * Provides instantaneous (<1ms) client-side execution on static hosts like Netlify,
 * eliminating all serverless cold starts, latency spikes, and ephemeral state loss.
 */

"use strict";

(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.Connect4Engine = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {

  const ROWS = 6;
  const COLS = 7;
  const EMPTY = 0;
  const PLAYER1 = 1; // Red (Human)
  const PLAYER2 = 2; // Yellow (AI)

  // -------------------------------------------------------------------------
  // Pre-computed 69 Winning 4-Windows (for ultra-fast heuristic evaluation)
  // -------------------------------------------------------------------------
  const WINNING_WINDOWS = [];

  // Horizontal (24 windows)
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS - 3; c++) {
      WINNING_WINDOWS.push([[r, c], [r, c + 1], [r, c + 2], [r, c + 3]]);
    }
  }
  // Vertical (21 windows)
  for (let r = 0; r < ROWS - 3; r++) {
    for (let c = 0; c < COLS; c++) {
      WINNING_WINDOWS.push([[r, c], [r + 1, c], [r + 2, c], [r + 3, c]]);
    }
  }
  // Diagonal Up / (12 windows)
  for (let r = 3; r < ROWS; r++) {
    for (let c = 0; c < COLS - 3; c++) {
      WINNING_WINDOWS.push([[r, c], [r - 1, c + 1], [r - 2, c + 2], [r - 3, c + 3]]);
    }
  }
  // Diagonal Down \ (12 windows)
  for (let r = 0; r < ROWS - 3; r++) {
    for (let c = 0; c < COLS - 3; c++) {
      WINNING_WINDOWS.push([[r, c], [r + 1, c + 1], [r + 2, c + 2], [r + 3, c + 3]]);
    }
  }

  // Center column cells for dominance weighting
  const CENTER_COL = 3;

  // -------------------------------------------------------------------------
  // Board Model
  // -------------------------------------------------------------------------
  class Board {
    constructor() {
      this.grid = Array.from({ length: ROWS }, () => new Array(COLS).fill(EMPTY));
      this.moveCount = 0;
      this.currentPlayer = PLAYER1;
      this.moveHistory = [];
    }

    copy() {
      const b = new Board();
      for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS; c++) {
          b.grid[r][c] = this.grid[r][c];
        }
      }
      b.moveCount = this.moveCount;
      b.currentPlayer = this.currentPlayer;
      b.moveHistory = this.moveHistory.map(m => ({ ...m }));
      return b;
    }

    isValidColumn(col) {
      return col >= 0 && col < COLS && this.grid[0][col] === EMPTY;
    }

    getValidColumns() {
      const valid = [];
      for (let c = 0; c < COLS; c++) {
        if (this.grid[0][c] === EMPTY) valid.push(c);
      }
      return valid;
    }

    getNextOpenRow(col) {
      for (let r = ROWS - 1; r >= 0; r--) {
        if (this.grid[r][col] === EMPTY) return r;
      }
      return null;
    }

    dropDisc(col, player) {
      const r = this.getNextOpenRow(col);
      if (r === null) return null;
      this.grid[r][col] = player;
      this.moveCount++;
      this.moveHistory.push({
        move_number: this.moveCount,
        player: player,
        column: col + 1,
        row: r + 1,
        timestamp: new Date().toLocaleTimeString(),
      });
      this.currentPlayer = player === PLAYER1 ? PLAYER2 : PLAYER1;
      return r;
    }

    undoLastMove(col) {
      for (let r = 0; r < ROWS; r++) {
        if (this.grid[r][col] !== EMPTY) {
          const removedPlayer = this.grid[r][col];
          this.grid[r][col] = EMPTY;
          this.moveCount--;
          this.moveHistory.pop();
          this.currentPlayer = removedPlayer;
          return r;
        }
      }
      return null;
    }

    checkWin(player) {
      for (let i = 0; i < WINNING_WINDOWS.length; i++) {
        const [[r0, c0], [r1, c1], [r2, c2], [r3, c3]] = WINNING_WINDOWS[i];
        if (
          this.grid[r0][c0] === player &&
          this.grid[r1][c1] === player &&
          this.grid[r2][c2] === player &&
          this.grid[r3][c3] === player
        ) {
          return { win: true, cells: [[r0, c0], [r1, c1], [r2, c2], [r3, c3]] };
        }
      }
      return { win: false, cells: [] };
    }

    isFull() {
      for (let c = 0; c < COLS; c++) {
        if (this.grid[0][c] === EMPTY) return false;
      }
      return true;
    }

    toKey(player) {
      let key = "";
      for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS; c++) {
          key += this.grid[r][c];
        }
      }
      return `${key}:${player}`;
    }
  }

  // -------------------------------------------------------------------------
  // Heuristic Board Evaluator
  // -------------------------------------------------------------------------
  function evaluateBoard(board, player) {
    const opponent = player === PLAYER1 ? PLAYER2 : PLAYER1;
    let score = 0;

    // Center column dominance (+6 per piece)
    let centerPlayer = 0;
    let centerOpponent = 0;
    for (let r = 0; r < ROWS; r++) {
      if (board.grid[r][CENTER_COL] === player) centerPlayer++;
      else if (board.grid[r][CENTER_COL] === opponent) centerOpponent++;
    }
    score += (centerPlayer - centerOpponent) * 6;

    // Evaluate all 69 winning windows
    for (let i = 0; i < WINNING_WINDOWS.length; i++) {
      const [[r0, c0], [r1, c1], [r2, c2], [r3, c3]] = WINNING_WINDOWS[i];
      let pCount = 0;
      let oCount = 0;
      let eCount = 0;

      const cells = [
        board.grid[r0][c0],
        board.grid[r1][c1],
        board.grid[r2][c2],
        board.grid[r3][c3],
      ];

      for (let j = 0; j < 4; j++) {
        const val = cells[j];
        if (val === player) pCount++;
        else if (val === opponent) oCount++;
        else eCount++;
      }

      if (pCount === 4) score += 100000;
      else if (pCount === 3 && eCount === 1) score += 100;
      else if (pCount === 2 && eCount === 2) score += 5;

      if (oCount === 3 && eCount === 1) score -= 100;
      else if (oCount === 2 && eCount === 2) score -= 5;
    }

    return score;
  }

  // -------------------------------------------------------------------------
  // Greedy Heuristic AI
  // -------------------------------------------------------------------------
  function getGreedyDecision(board, player = PLAYER2) {
    const t0 = performance.now();
    const opponent = player === PLAYER1 ? PLAYER2 : PLAYER1;
    const validCols = board.getValidColumns();

    if (validCols.length === 0) {
      return { column: 3, score: 0, reason: "No legal moves available", compute_time_ms: 0, candidate_scores: {} };
    }

    const candidateScores = {};

    // 1. Immediate Winning Move
    for (const c of validCols) {
      board.dropDisc(c, player);
      const winCheck = board.checkWin(player);
      board.undoLastMove(c);
      if (winCheck.win) {
        candidateScores[c] = 100000;
        return {
          column: c,
          score: 100000,
          reason: `Immediate win: completes 4-in-a-row in column ${c + 1}`,
          compute_time_ms: +(performance.now() - t0).toFixed(2),
          candidate_scores: { [c]: 100000 },
        };
      }
    }

    // 2. Immediate Blocking Move
    for (const c of validCols) {
      board.dropDisc(c, opponent);
      const winCheck = board.checkWin(opponent);
      board.undoLastMove(c);
      if (winCheck.win) {
        candidateScores[c] = 50000;
        return {
          column: c,
          score: 50000,
          reason: `Immediate tactical block: prevents opponent win in column ${c + 1}`,
          compute_time_ms: +(performance.now() - t0).toFixed(2),
          candidate_scores: { [c]: 50000 },
        };
      }
    }

    // 3. Heuristic Evaluation with Center Tie-Breaking
    const centerPreference = [3, 2, 4, 1, 5, 0, 6];
    let bestScore = -Infinity;
    let bestCol = validCols[0];

    for (const c of validCols) {
      board.dropDisc(c, player);
      const s = evaluateBoard(board, player);
      board.undoLastMove(c);
      candidateScores[c] = s;

      if (s > bestScore) {
        bestScore = s;
        bestCol = c;
      } else if (s === bestScore) {
        if (centerPreference.indexOf(c) < centerPreference.indexOf(bestCol)) {
          bestCol = c;
        }
      }
    }

    return {
      column: bestCol,
      score: bestScore,
      reason: `Heuristic maximization (score: ${bestScore}) with center tie-breaking`,
      compute_time_ms: +(performance.now() - t0).toFixed(2),
      candidate_scores: candidateScores,
    };
  }

  // -------------------------------------------------------------------------
  // Minimax AI with Depth-Aware Scoring
  // -------------------------------------------------------------------------
  function getMinimaxDecision(board, depth = 3, player = PLAYER2) {
    const t0 = performance.now();
    const opponent = player === PLAYER1 ? PLAYER2 : PLAYER1;
    let nodesVisited = 0;
    let recursiveCalls = 0;
    let maxDepthReached = 0;

    const candidateScores = {};
    const branches = [];
    const validCols = board.getValidColumns();

    if (validCols.length === 0) {
      return { column: 3, score: 0, nodes_visited: 0, recursive_calls: 0, max_depth_reached: 0, compute_time_ms: 0, candidate_scores: {}, tree: { branches: [] } };
    }

    function minimax(b, d, isMax) {
      nodesVisited++;
      if (depth - d > maxDepthReached) maxDepthReached = depth - d;

      // Terminal checks
      const winCheckAI = b.checkWin(player);
      if (winCheckAI.win) return 1000000 + d * 1000;

      const winCheckOpp = b.checkWin(opponent);
      if (winCheckOpp.win) return -1000000 - d * 1000;

      if (b.isFull()) return 0;
      if (d === 0) return evaluateBoard(b, player);

      const openCols = b.getValidColumns();
      if (openCols.length === 0) return 0;

      if (isMax) {
        let maxEval = -Infinity;
        for (const c of openCols) {
          recursiveCalls++;
          b.dropDisc(c, player);
          const ev = minimax(b, d - 1, false);
          b.undoLastMove(c);
          maxEval = Math.max(maxEval, ev);
        }
        return maxEval;
      } else {
        let minEval = Infinity;
        for (const c of openCols) {
          recursiveCalls++;
          b.dropDisc(c, opponent);
          const ev = minimax(b, d - 1, true);
          b.undoLastMove(c);
          minEval = Math.min(minEval, ev);
        }
        return minEval;
      }
    }

    // Root-level candidate exploration
    let bestScore = -Infinity;
    let bestCol = validCols[0];
    const centerOrder = [3, 2, 4, 1, 5, 0, 6];

    for (const c of validCols) {
      recursiveCalls++;
      board.dropDisc(c, player);
      const score = minimax(board, depth - 1, false);
      board.undoLastMove(c);

      candidateScores[c] = score;
      branches.push({ column: c + 1, col: c, score: score, eval_score: score });

      if (score > bestScore) {
        bestScore = score;
        bestCol = c;
      } else if (score === bestScore) {
        if (centerOrder.indexOf(c) < centerOrder.indexOf(bestCol)) {
          bestCol = c;
        }
      }
    }

    return {
      column: bestCol,
      score: bestScore,
      nodes_visited: nodesVisited,
      recursive_calls: recursiveCalls,
      max_depth_reached: maxDepthReached,
      compute_time_ms: +(performance.now() - t0).toFixed(2),
      candidate_scores: candidateScores,
      tree: { branches: branches },
    };
  }

  // -------------------------------------------------------------------------
  // Alpha-Beta Pruning with Move Ordering & Transposition Table
  // -------------------------------------------------------------------------
  const EntryType = { EXACT: 1, LOWER_BOUND: 2, UPPER_BOUND: 3 };

  function orderMoves(b, validCols, player, opponent, tt) {
    const scoredMoves = [];
    const centerDistances = { 3: 60, 2: 40, 4: 40, 1: 20, 5: 20, 0: 0, 6: 0 };

    for (const c of validCols) {
      let priority = centerDistances[c] || 0;

      // Check immediate win (+10,000)
      b.dropDisc(c, player);
      if (b.checkWin(player).win) priority += 10000;
      b.undoLastMove(c);

      // Check immediate block (+5,000)
      b.dropDisc(c, opponent);
      if (b.checkWin(opponent).win) priority += 5000;
      b.undoLastMove(c);

      // Check TT hash move (+50,000)
      if (tt) {
        const key = b.toKey(player);
        const entry = tt.get(key);
        if (entry && entry.bestMove === c) priority += 50000;
      }

      scoredMoves.push({ col: c, priority: priority });
    }

    scoredMoves.sort((a, b) => b.priority - a.priority);
    return scoredMoves.map(m => m.col);
  }

  function getAlphaBetaDecision(board, depth = 3, player = PLAYER2, useMoveOrdering = true, useTT = true) {
    const t0 = performance.now();
    const opponent = player === PLAYER1 ? PLAYER2 : PLAYER1;
    let nodesVisited = 0;
    let recursiveCalls = 0;
    let cutoffs = 0;
    let maxDepthReached = 0;
    let cacheHits = 0;
    let cacheMisses = 0;

    const tt = useTT ? new Map() : null;
    const candidateScores = {};
    const branches = [];
    const validCols = board.getValidColumns();

    if (validCols.length === 0) {
      return { column: 3, score: 0, nodes_visited: 0, recursive_calls: 0, cutoffs: 0, max_depth_reached: 0, compute_time_ms: 0, candidate_scores: {}, tree: { branches: [] } };
    }

    function alphabeta(b, d, alpha, beta, isMax) {
      nodesVisited++;
      if (depth - d > maxDepthReached) maxDepthReached = depth - d;

      const currPlayer = isMax ? player : opponent;
      const key = useTT ? b.toKey(currPlayer) : null;

      // Transposition Table Lookup
      if (useTT) {
        const entry = tt.get(key);
        if (entry && entry.depth >= d) {
          cacheHits++;
          if (entry.flag === EntryType.EXACT) return entry.score;
          if (entry.flag === EntryType.LOWER_BOUND && entry.score >= beta) return entry.score;
          if (entry.flag === EntryType.UPPER_BOUND && entry.score <= alpha) return entry.score;
        } else {
          cacheMisses++;
        }
      }

      // Terminal checks
      const winCheckAI = b.checkWin(player);
      if (winCheckAI.win) return 1000000 + d * 1000;

      const winCheckOpp = b.checkWin(opponent);
      if (winCheckOpp.win) return -1000000 - d * 1000;

      if (b.isFull()) return 0;
      if (d === 0) return evaluateBoard(b, player);

      const openCols = b.getValidColumns();
      if (openCols.length === 0) return 0;

      const orderedCols = useMoveOrdering ? orderMoves(b, openCols, currPlayer, isMax ? opponent : player, tt) : openCols;

      let bestVal = isMax ? -Infinity : Infinity;
      let bestMove = orderedCols[0];
      const origAlpha = alpha;

      if (isMax) {
        for (const c of orderedCols) {
          recursiveCalls++;
          b.dropDisc(c, player);
          const ev = alphabeta(b, d - 1, alpha, beta, false);
          b.undoLastMove(c);

          if (ev > bestVal) {
            bestVal = ev;
            bestMove = c;
          }
          alpha = Math.max(alpha, ev);
          if (beta <= alpha) {
            cutoffs++;
            break; // Beta-cutoff
          }
        }
      } else {
        for (const c of orderedCols) {
          recursiveCalls++;
          b.dropDisc(c, opponent);
          const ev = alphabeta(b, d - 1, alpha, beta, true);
          b.undoLastMove(c);

          if (ev < bestVal) {
            bestVal = ev;
            bestMove = c;
          }
          beta = Math.min(beta, ev);
          if (beta <= alpha) {
            cutoffs++;
            break; // Alpha-cutoff
          }
        }
      }

      // Store in Transposition Table
      if (useTT && key) {
        let flag = EntryType.EXACT;
        if (bestVal <= origAlpha) flag = EntryType.UPPER_BOUND;
        else if (bestVal >= beta) flag = EntryType.LOWER_BOUND;

        tt.set(key, { depth: d, score: bestVal, flag: flag, bestMove: bestMove });
      }

      return bestVal;
    }

    // Root-level candidate exploration
    let bestScore = -Infinity;
    let bestCol = validCols[0];
    let alpha = -Infinity;
    const beta = Infinity;

    const orderedCols = useMoveOrdering ? orderMoves(board, validCols, player, opponent, tt) : validCols;

    for (const c of orderedCols) {
      recursiveCalls++;
      board.dropDisc(c, player);
      const score = alphabeta(board, depth - 1, alpha, beta, false);
      board.undoLastMove(c);

      candidateScores[c] = score;
      branches.push({ column: c + 1, col: c, score: score, eval_score: score });

      if (score > bestScore) {
        bestScore = score;
        bestCol = c;
      }
      alpha = Math.max(alpha, score);
    }

    const totalLookups = cacheHits + cacheMisses;
    const hitRate = totalLookups > 0 ? +((cacheHits / totalLookups) * 100).toFixed(1) : 0;
    const estMemoryKb = useTT ? +((tt.size * 0.16)).toFixed(1) : 0;

    return {
      column: bestCol,
      score: bestScore,
      nodes_visited: nodesVisited,
      recursive_calls: recursiveCalls,
      cutoffs: cutoffs,
      max_depth_reached: maxDepthReached,
      compute_time_ms: +(performance.now() - t0).toFixed(2),
      candidate_scores: candidateScores,
      cache_hits: cacheHits,
      cache_misses: cacheMisses,
      hit_rate_pct: hitRate,
      tt_memory_kb: estMemoryKb,
      tree: { branches: branches },
    };
  }

  // -------------------------------------------------------------------------
  // Benchmark Positions & Suite
  // -------------------------------------------------------------------------
  function createBenchmarkBoard(positionId, liveBoard = null) {
    const b = new Board();

    if (positionId === "live" && liveBoard) {
      return liveBoard.copy();
    } else if (positionId === "opening_center") {
      b.dropDisc(3, PLAYER1);
    } else if (positionId === "tactical_block") {
      // Player 1 has 3 in row 5 at cols 1, 2, 3
      b.dropDisc(1, PLAYER1);
      b.dropDisc(1, PLAYER2);
      b.dropDisc(2, PLAYER1);
      b.dropDisc(2, PLAYER2);
      b.dropDisc(3, PLAYER1);
    } else if (positionId === "midgame_complex") {
      const moves = [3, 3, 2, 4, 2, 4, 3, 2, 4, 3];
      moves.forEach((c, idx) => b.dropDisc(c, (idx % 2 === 0) ? PLAYER1 : PLAYER2));
    } else if (positionId === "symmetric_transposition") {
      const moves = [2, 4, 2, 4, 1, 5, 1, 5];
      moves.forEach((c, idx) => b.dropDisc(c, (idx % 2 === 0) ? PLAYER1 : PLAYER2));
    } else {
      b.dropDisc(3, PLAYER1);
    }

    return b;
  }

  function runBenchmarkSuite(positionId, depth = 3, repeats = 3, liveBoard = null) {
    const testBoard = createBenchmarkBoard(positionId, liveBoard);

    function runMedian(fn) {
      const times = [];
      let lastResult = null;
      for (let i = 0; i < repeats; i++) {
        const bClone = testBoard.copy();
        const t0 = performance.now();
        lastResult = fn(bClone);
        times.push(performance.now() - t0);
      }
      times.sort((a, b) => a - b);
      const medianTime = times[Math.floor(times.length / 2)];
      return { ...lastResult, compute_time_ms: +medianTime.toFixed(2) };
    }

    const resMinimax = runMedian(b => getMinimaxDecision(b, depth, PLAYER2));
    const resAbNatural = runMedian(b => getAlphaBetaDecision(b, depth, PLAYER2, false, false));
    const resAbOrdered = runMedian(b => getAlphaBetaDecision(b, depth, PLAYER2, true, false));
    const resAbTT = runMedian(b => getAlphaBetaDecision(b, depth, PLAYER2, true, true));

    const baselineNodes = resMinimax.nodes_visited || 1;
    const baselineTime = resMinimax.compute_time_ms || 0.1;

    function buildRow(name, r) {
      const workRed = Math.max(0, +(((baselineNodes - r.nodes_visited) / baselineNodes) * 100).toFixed(1));
      const speedup = +(baselineTime / Math.max(0.1, r.compute_time_ms)).toFixed(2);
      return {
        name: name,
        chosen_col: r.column,
        score: r.score,
        nodes_visited: r.nodes_visited,
        cutoffs: r.cutoffs || 0,
        cache_hits: r.cache_hits || 0,
        hit_rate_pct: r.hit_rate_pct || 0,
        time_ms: r.compute_time_ms,
        work_reduction_pct: workRed,
        speedup: speedup,
        memory_kb: r.tt_memory_kb || 0,
      };
    }

    return {
      success: true,
      position: positionId,
      depth: depth,
      repeats: repeats,
      results: [
        buildRow("Minimax (Baseline)", resMinimax),
        buildRow("Alpha-Beta (Natural)", resAbNatural),
        buildRow("Alpha-Beta (Move Ordered)", resAbOrdered),
        buildRow("Alpha-Beta + Transposition Table", resAbTT),
      ],
    };
  }

  // -------------------------------------------------------------------------
  // Authoritative Client Session Controller
  // -------------------------------------------------------------------------
  class SessionController {
    constructor() {
      this.board = new Board();
      this.gameMode = "hvh";
      this.aiStrategy = "alphabeta";
      this.aiDepth = 3;
      this.useMoveOrdering = true;
      this.useTT = true;
      this.aiPlayer = PLAYER2;
      this.lastAIDecision = null;
      this.gameOver = false;
      this.winner = null;
      this.winningCells = [];
      this.isDraw = false;
    }

    getSnapshot(placedRow = null, placedCol = null) {
      let winStatus = "in_progress";
      if (this.winner) winStatus = "win";
      else if (this.isDraw) winStatus = "draw";

      return {
        grid: this.board.grid.map(row => [...row]),
        current_player: this.board.currentPlayer,
        move_count: this.board.moveCount,
        valid_columns: this.gameOver ? [] : this.board.getValidColumns(),
        game_over: this.gameOver,
        winner: this.winner,
        winning_cells: this.winningCells,
        is_draw: this.isDraw,
        status: winStatus,
        move_history: this.board.moveHistory.map(m => ({ ...m })),
        game_mode: this.gameMode,
        ai_strategy: this.aiStrategy,
        ai_depth: this.aiDepth,
        use_move_ordering: this.useMoveOrdering,
        use_transposition_table: this.useTT,
        ai_player: this.aiPlayer,
        ai_decision: this.lastAIDecision,
        placed_row: placedRow,
        placed_col: placedCol,
      };
    }

    reset(mode = null) {
      this.board = new Board();
      this.gameOver = false;
      this.winner = null;
      this.winningCells = [];
      this.isDraw = false;
      this.lastAIDecision = null;
      if (mode) this.gameMode = mode;
      return this.getSnapshot();
    }

    configure(settings) {
      if (settings.mode !== undefined) this.gameMode = settings.mode;
      if (settings.ai_strategy !== undefined) this.aiStrategy = settings.ai_strategy;
      if (settings.depth !== undefined) this.aiDepth = settings.depth;
      if (settings.use_move_ordering !== undefined) this.useMoveOrdering = settings.use_move_ordering;
      if (settings.use_transposition_table !== undefined) this.useTT = settings.use_transposition_table;
      return this.getSnapshot();
    }

    makeMove(col) {
      if (this.gameOver) {
        return { ok: false, error: "The game has already ended." };
      }
      if (!this.board.isValidColumn(col)) {
        return { ok: false, error: `Column ${col + 1} is already full.` };
      }

      const player = this.board.currentPlayer;
      const r = this.board.dropDisc(col, player);

      const winCheck = this.board.checkWin(player);
      if (winCheck.win) {
        this.gameOver = true;
        this.winner = player;
        this.winningCells = winCheck.cells;
      } else if (this.board.isFull()) {
        this.gameOver = true;
        this.isDraw = true;
      }

      return { ok: true, data: this.getSnapshot(r, col) };
    }

    makeAIMove() {
      if (this.gameOver) {
        return { ok: false, error: "The game has already ended." };
      }

      let decision;
      if (this.aiStrategy === "alphabeta") {
        decision = getAlphaBetaDecision(this.board, this.aiDepth, this.aiPlayer, this.useMoveOrdering, this.useTT);
      } else if (this.aiStrategy === "minimax") {
        decision = getMinimaxDecision(this.board, this.aiDepth, this.aiPlayer);
      } else {
        decision = getGreedyDecision(this.board, this.aiPlayer);
      }

      this.lastAIDecision = decision;
      const col = decision.column;
      const r = this.board.dropDisc(col, this.aiPlayer);

      const winCheck = this.board.checkWin(this.aiPlayer);
      if (winCheck.win) {
        this.gameOver = true;
        this.winner = this.aiPlayer;
        this.winningCells = winCheck.cells;
      } else if (this.board.isFull()) {
        this.gameOver = true;
        this.isDraw = true;
      }

      return { ok: true, data: this.getSnapshot(r, col) };
    }
  }

  return {
    Board,
    SessionController,
    evaluateBoard,
    getGreedyDecision,
    getMinimaxDecision,
    getAlphaBetaDecision,
    runBenchmarkSuite,
  };
});
