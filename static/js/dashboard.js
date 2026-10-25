/**
 * static/js/dashboard.js
 * 
 * Interactive controller for the Connect-4 AI Performance Dashboard & DAA Analytics.
 * Fetches real empirical measurements from Flask Python endpoints (/api/benchmark/*)
 * and renders responsive visualizations via Chart.js.
 */

(function () {
  'use strict';

  // Chart instances repository to ensure proper canvas cleanup
  const Charts = {
    time: null,
    nodes: null,
    cutoffs: null,
    memory: null,
  };

  // Color tokens aligned with dark CSS design system
  const THEME_COLORS = {
    minimax: {
      border: 'rgba(239, 68, 68, 1)',      // red-500
      bg: 'rgba(239, 68, 68, 0.25)',
      point: '#f87171'
    },
    abNatural: {
      border: 'rgba(245, 158, 11, 1)',     // amber-500
      bg: 'rgba(245, 158, 11, 0.25)',
      point: '#fbbf24'
    },
    abOrdered: {
      border: 'rgba(56, 189, 248, 1)',     // sky-400
      bg: 'rgba(56, 189, 248, 0.25)',
      point: '#38bdf8'
    },
    abTT: {
      border: 'rgba(52, 211, 153, 1)',      // emerald-400
      bg: 'rgba(52, 211, 153, 0.25)',
      point: '#34d399'
    },
    grid: 'rgba(255, 255, 255, 0.08)',
    text: '#94a3b8'
  };

  // DOM Elements
  let DOM = {};

  function initDOM() {
    DOM = {
      positionSelect: document.getElementById('bench-position-select'),
      depthSelect: document.getElementById('bench-depth-select'),
      repeatsSelect: document.getElementById('bench-repeats-select'),
      btnRun: document.getElementById('btn-run-benchmark'),
      tableBody: document.getElementById('bench-table-body'),
      statusBadge: document.getElementById('bench-status-badge'),
      chartTimeCanvas: document.getElementById('chart-time'),
      chartNodesCanvas: document.getElementById('chart-nodes'),
      chartCutoffsCanvas: document.getElementById('chart-cutoffs'),
      chartMemoryCanvas: document.getElementById('chart-memory'),
    };
  }

  /**
   * Fetch available benchmark positions from server and update select element.
   */
  async function loadPositions() {
    try {
      const res = await fetch('/api/benchmark/positions');
      const data = await res.json();
      if ((data.ok || data.success) && Array.isArray(data.positions)) {
        const currentVal = DOM.positionSelect.value;
        let html = '';
        data.positions.forEach(p => {
          html += `<option value="${p.id}">${p.name} (${p.phase})</option>`;
        });
        html += `<option value="live">⚡ Current Live Board State</option>`;
        DOM.positionSelect.innerHTML = html;
        if (currentVal && DOM.positionSelect.querySelector(`option[value="${currentVal}"]`)) {
          DOM.positionSelect.value = currentVal;
        }
      }
    } catch (err) {
      console.warn('Could not load dynamic positions list, using default markup options:', err);
    }
  }

  /**
   * Set status badge UI state.
   */
  function setStatus(state, text) {
    if (!DOM.statusBadge) return;
    DOM.statusBadge.className = `badge bench-badge ${state}`;
    DOM.statusBadge.textContent = text;
  }

  /**
   * Run benchmark suite on Python backend.
   */
  async function runBenchmark() {
    const positionId = DOM.positionSelect ? DOM.positionSelect.value : 'opening_center';
    const depth = DOM.depthSelect ? parseInt(DOM.depthSelect.value, 10) : 3;
    const repeats = DOM.repeatsSelect ? parseInt(DOM.repeatsSelect.value, 10) : 3;

    setStatus('running', 'Computing...');
    if (DOM.btnRun) DOM.btnRun.disabled = true;

    if (DOM.tableBody) {
      DOM.tableBody.innerHTML = `
        <tr>
          <td colspan="10" class="bench-loading-cell">
            <span class="spinner-sm"></span> Benchmarking algorithms server-side (depth ${depth}, ${repeats} runs)...
          </td>
        </tr>
      `;
    }

    try {
      if (typeof Connect4Engine !== 'undefined') {
        // High-speed client-side execution (0ms latency, eliminates Netlify cold starts)
        const liveBoard = window.ClientSession ? window.ClientSession.board : null;
        const tableRes = Connect4Engine.runBenchmarkSuite(positionId, depth, repeats, liveBoard);

        // Generate depth scaling data across depths 1 to Math.max(depth, 3)
        const maxD = Math.max(depth, 3);
        const scalingDepths = [];
        const mmNodes = [], mmTimes = [];
        const abNoNodes = [], abNoTimes = [], abNoCutoffs = [];
        const abOrdNodes = [], abOrdTimes = [], abOrdCutoffs = [];
        const abTTNodes = [], abTTTimes = [], abTTCutoffs = [], abTTMem = [];

        for (let d = 1; d <= maxD; d++) {
          scalingDepths.push(d);
          const rep = Connect4Engine.runBenchmarkSuite(positionId, d, repeats, liveBoard);
          const rMM = rep.results[0];
          const rAbNo = rep.results[1];
          const rAbOrd = rep.results[2];
          const rAbTT = rep.results[3];

          mmNodes.push(rMM.nodes_visited);
          mmTimes.push(rMM.time_ms);

          abNoNodes.push(rAbNo.nodes_visited);
          abNoTimes.push(rAbNo.time_ms);
          abNoCutoffs.push(rAbNo.cutoffs);

          abOrdNodes.push(rAbOrd.nodes_visited);
          abOrdTimes.push(rAbOrd.time_ms);
          abOrdCutoffs.push(rAbOrd.cutoffs);

          abTTNodes.push(rAbTT.nodes_visited);
          abTTTimes.push(rAbTT.time_ms);
          abTTCutoffs.push(rAbTT.cutoffs);
          abTTMem.push(rAbTT.memory_kb);
        }

        const scalingData = {
          depths: scalingDepths,
          time_ms: {
            minimax: mmTimes,
            alphabeta_natural: abNoTimes,
            alphabeta_ordered: abOrdTimes,
            alphabeta_tt: abTTTimes,
          },
          nodes: {
            minimax: mmNodes,
            alphabeta_natural: abNoNodes,
            alphabeta_ordered: abOrdNodes,
            alphabeta_tt: abTTNodes,
          },
          cutoffs: {
            alphabeta_natural: abNoCutoffs,
            alphabeta_ordered: abOrdCutoffs,
            alphabeta_tt: abTTCutoffs,
          },
          memory_kb: {
            alphabeta_tt: abTTMem,
          },
        };

        renderTable(tableRes.results);
        renderCharts(scalingData);
        setStatus('ready', `Done (${repeats} runs aggregated)`);
        return;
      }

      // 1. Fetch benchmark table data
      const tablePromise = fetch('/api/benchmark/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position_id: positionId, depth: depth, repeats: repeats })
      }).then(r => r.json());

      // 2. Fetch depth scaling chart data
      const scalingPromise = fetch('/api/benchmark/scaling', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position_id: positionId, max_depth: Math.max(depth, 3), repeats: repeats })
      }).then(r => r.json());

      const [tableRes, scalingRes] = await Promise.all([tablePromise, scalingPromise]);

      if (!tableRes.ok) {
        throw new Error(tableRes.error || 'Benchmark table run failed');
      }
      if (!scalingRes.ok) {
        throw new Error(scalingRes.error || 'Depth scaling benchmark failed');
      }

      renderTable(tableRes.results);
      renderCharts(scalingRes.scaling);
      setStatus('ready', `Done (${repeats} runs aggregated)`);
    } catch (err) {
      console.error('Benchmark error:', err);
      setStatus('error', 'Error');
      if (DOM.tableBody) {
        DOM.tableBody.innerHTML = `
          <tr>
            <td colspan="10" class="bench-error-cell">
              ⚠️ Benchmark execution failed: ${err.message}
            </td>
          </tr>
        `;
      }
    } finally {
      if (DOM.btnRun) DOM.btnRun.disabled = false;
    }
  }

  /**
   * Render benchmark comparison table.
   */
  function renderTable(results) {
    if (!DOM.tableBody || !Array.isArray(results)) return;

    let html = '';
    results.forEach((row, idx) => {
      const isBaseline = row.algorithm_key === 'minimax';
      const colVal = row.column !== undefined && row.column !== null ? row.column : row.chosen_col;
      const colText = colVal !== undefined && colVal !== null ? `Col ${colVal + 1}` : '—';
      const cutoffsText = (row.cutoffs !== null && row.cutoffs !== undefined && !isBaseline)
        ? Number(row.cutoffs).toLocaleString()
        : (isBaseline ? '—' : '0');
      
      let cacheText = '—';
      const hitRate = row.hit_rate_pct !== undefined
        ? row.hit_rate_pct
        : (row.cache_hit_rate !== undefined ? row.cache_hit_rate * 100 : null);
      if (row.cache_hits !== null && row.cache_hits !== undefined && (row.cache_hits > 0 || row.cache_misses > 0)) {
        cacheText = `${row.cache_hits} (${hitRate !== null ? Number(hitRate).toFixed(1) : '0.0'}%)`;
      }

      const redVal = row.node_reduction_pct !== undefined ? row.node_reduction_pct : (row.work_reduction_pct !== undefined ? row.work_reduction_pct : null);
      let redClass = 'reduction-neutral';
      let redText = 'Baseline (0%)';
      if (!isBaseline && redVal !== null && redVal !== undefined) {
        const redNum = Number(redVal) || 0;
        if (redNum > 0) {
          redClass = 'reduction-positive';
          redText = `-${redNum.toFixed(1)}%`;
        } else if (redNum < 0) {
          redClass = 'reduction-negative';
          redText = `+${Math.abs(redNum).toFixed(1)}%`;
        } else {
          redText = '0.0%';
        }
      }

      const speedVal = row.speedup_ratio !== undefined ? row.speedup_ratio : row.speedup;
      let speedClass = 'speedup-neutral';
      let speedText = '1.0×';
      if (!isBaseline && speedVal !== null && speedVal !== undefined) {
        const speedNum = Number(speedVal) || 1;
        if (speedNum > 1.05) {
          speedClass = 'speedup-positive';
          speedText = `${speedNum.toFixed(2)}×`;
        } else if (speedNum < 0.95) {
          speedClass = 'speedup-negative';
          speedText = `${speedNum.toFixed(2)}×`;
        } else {
          speedText = `${speedNum.toFixed(2)}×`;
        }
      }

      const memText = row.memory_kb !== null && row.memory_kb !== undefined
        ? (Number(row.memory_kb) > 0 ? `~${Number(row.memory_kb).toFixed(1)} KB` : '0 KB')
        : '—';

      const scoreNum = (row.score !== undefined && row.score !== null) ? Number(row.score) : 0;
      const scoreText = Number.isFinite(scoreNum) ? scoreNum.toFixed(1) : '0.0';

      const execTime = row.execution_time_ms !== undefined ? row.execution_time_ms : (row.time_ms !== undefined ? row.time_ms : (row.compute_time_ms || 0));
      const timeNum = Number(execTime) || 0;
      const timeText = `${timeNum.toFixed(2)} ms`;

      const nodesNum = (row.nodes_visited !== undefined && row.nodes_visited !== null) ? Number(row.nodes_visited) : 0;
      const nodesText = nodesNum.toLocaleString();

      html += `
        <tr class="bench-row ${isBaseline ? 'bench-row-baseline' : ''}">
          <td class="bench-cfg-name">
            <span class="cfg-dot cfg-dot-${row.algorithm_key || 'minimax'}"></span>
            <strong>${row.name}</strong>
          </td>
          <td><span class="badge badge-move">${colText}</span></td>
          <td class="font-mono">${scoreText}</td>
          <td class="font-mono"><strong>${nodesText}</strong></td>
          <td class="font-mono">${cutoffsText}</td>
          <td class="font-mono">${cacheText}</td>
          <td class="font-mono">${timeText}</td>
          <td><span class="badge ${redClass}">${redText}</span></td>
          <td><span class="badge ${speedClass}">${speedText}</span></td>
          <td class="font-mono text-muted">${memText}</td>
        </tr>
      `;
    });

    DOM.tableBody.innerHTML = html;
  }

  /**
   * Helper to destroy chart safely.
   */
  function destroyChart(key) {
    if (Charts[key]) {
      Charts[key].destroy();
      Charts[key] = null;
    }
  }

  /**
   * Common Chart.js default options for dark theme.
   */
  function getBaseChartOptions(yAxisTitle) {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: '#cbd5e1',
            font: { family: 'inherit', size: 12 },
            boxWidth: 14,
            usePointStyle: true,
          }
        },
        tooltip: {
          backgroundColor: '#0f172a',
          titleColor: '#f8fafc',
          bodyColor: '#cbd5e1',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          padding: 10,
          boxPadding: 4,
          usePointStyle: true
        }
      },
      scales: {
        x: {
          grid: { color: THEME_COLORS.grid },
          ticks: { color: THEME_COLORS.text, font: { family: 'inherit' } },
          title: {
            display: true,
            text: 'Search Depth (plies)',
            color: THEME_COLORS.text,
            font: { weight: 'bold' }
          }
        },
        y: {
          grid: { color: THEME_COLORS.grid },
          ticks: { color: THEME_COLORS.text, font: { family: 'inherit' } },
          title: {
            display: true,
            text: yAxisTitle,
            color: THEME_COLORS.text,
            font: { weight: 'bold' }
          },
          beginAtZero: true
        }
      }
    };
  }

  /**
   * Render all 4 Chart.js charts.
   */
  function renderCharts(scaling) {
    if (!window.Chart) {
      console.error('Chart.js library not loaded');
      return;
    }

    const depths = scaling.depths.map(d => `Depth ${d}`);

    // ─────────────────────────────────────────────────────────────
    // Chart 1: Execution Time vs Search Depth
    // ─────────────────────────────────────────────────────────────
    if (DOM.chartTimeCanvas) {
      destroyChart('time');
      const ctx1 = DOM.chartTimeCanvas.getContext('2d');
      Charts.time = new Chart(ctx1, {
        type: 'line',
        data: {
          labels: depths,
          datasets: [
            {
              label: 'Minimax (Baseline)',
              data: scaling.time_ms.minimax,
              borderColor: THEME_COLORS.minimax.border,
              backgroundColor: THEME_COLORS.minimax.bg,
              pointBackgroundColor: THEME_COLORS.minimax.point,
              borderWidth: 2.5,
              tension: 0.2,
              fill: false
            },
            {
              label: 'Alpha-Beta (Natural)',
              data: scaling.time_ms.alphabeta_natural,
              borderColor: THEME_COLORS.abNatural.border,
              backgroundColor: THEME_COLORS.abNatural.bg,
              pointBackgroundColor: THEME_COLORS.abNatural.point,
              borderWidth: 2,
              tension: 0.2,
              fill: false
            },
            {
              label: 'Alpha-Beta (Ordered)',
              data: scaling.time_ms.alphabeta_ordered,
              borderColor: THEME_COLORS.abOrdered.border,
              backgroundColor: THEME_COLORS.abOrdered.bg,
              pointBackgroundColor: THEME_COLORS.abOrdered.point,
              borderWidth: 2,
              tension: 0.2,
              fill: false
            },
            {
              label: 'Alpha-Beta + TT',
              data: scaling.time_ms.alphabeta_tt,
              borderColor: THEME_COLORS.abTT.border,
              backgroundColor: THEME_COLORS.abTT.bg,
              pointBackgroundColor: THEME_COLORS.abTT.point,
              borderWidth: 2.5,
              tension: 0.2,
              fill: false
            }
          ]
        },
        options: getBaseChartOptions('Latency (milliseconds)')
      });
    }

    // ─────────────────────────────────────────────────────────────
    // Chart 2: Nodes Visited vs Search Depth (Logarithmic / Comparison)
    // ─────────────────────────────────────────────────────────────
    if (DOM.chartNodesCanvas) {
      destroyChart('nodes');
      const ctx2 = DOM.chartNodesCanvas.getContext('2d');
      const opts = getBaseChartOptions('Nodes Visited (count)');
      
      Charts.nodes = new Chart(ctx2, {
        type: 'bar',
        data: {
          labels: depths,
          datasets: [
            {
              label: 'Minimax',
              data: scaling.nodes.minimax,
              backgroundColor: 'rgba(239, 68, 68, 0.75)',
              borderColor: THEME_COLORS.minimax.border,
              borderWidth: 1,
              borderRadius: 4
            },
            {
              label: 'Alpha-Beta (Natural)',
              data: scaling.nodes.alphabeta_natural,
              backgroundColor: 'rgba(245, 158, 11, 0.75)',
              borderColor: THEME_COLORS.abNatural.border,
              borderWidth: 1,
              borderRadius: 4
            },
            {
              label: 'Alpha-Beta (Ordered)',
              data: scaling.nodes.alphabeta_ordered,
              backgroundColor: 'rgba(56, 189, 248, 0.75)',
              borderColor: THEME_COLORS.abOrdered.border,
              borderWidth: 1,
              borderRadius: 4
            },
            {
              label: 'Alpha-Beta + TT',
              data: scaling.nodes.alphabeta_tt,
              backgroundColor: 'rgba(52, 211, 153, 0.75)',
              borderColor: THEME_COLORS.abTT.border,
              borderWidth: 1,
              borderRadius: 4
            }
          ]
        },
        options: opts
      });
    }

    // ─────────────────────────────────────────────────────────────
    // Chart 3: Branch Cutoffs vs Search Depth
    // ─────────────────────────────────────────────────────────────
    if (DOM.chartCutoffsCanvas) {
      destroyChart('cutoffs');
      const ctx3 = DOM.chartCutoffsCanvas.getContext('2d');
      Charts.cutoffs = new Chart(ctx3, {
        type: 'line',
        data: {
          labels: depths,
          datasets: [
            {
              label: 'Alpha-Beta (Natural)',
              data: scaling.cutoffs.alphabeta_natural,
              borderColor: THEME_COLORS.abNatural.border,
              backgroundColor: THEME_COLORS.abNatural.bg,
              pointBackgroundColor: THEME_COLORS.abNatural.point,
              borderWidth: 2,
              tension: 0.2,
              fill: false
            },
            {
              label: 'Alpha-Beta (Ordered)',
              data: scaling.cutoffs.alphabeta_ordered,
              borderColor: THEME_COLORS.abOrdered.border,
              backgroundColor: THEME_COLORS.abOrdered.bg,
              pointBackgroundColor: THEME_COLORS.abOrdered.point,
              borderWidth: 2,
              tension: 0.2,
              fill: false
            },
            {
              label: 'Alpha-Beta + TT',
              data: scaling.cutoffs.alphabeta_tt,
              borderColor: THEME_COLORS.abTT.border,
              backgroundColor: THEME_COLORS.abTT.bg,
              pointBackgroundColor: THEME_COLORS.abTT.point,
              borderWidth: 2.5,
              tension: 0.2,
              fill: false
            }
          ]
        },
        options: getBaseChartOptions('Pruned Branch Cutoffs (count)')
      });
    }

    // ─────────────────────────────────────────────────────────────
    // Chart 4: Transposition Table Memory Consumption
    // ─────────────────────────────────────────────────────────────
    if (DOM.chartMemoryCanvas) {
      destroyChart('memory');
      const ctx4 = DOM.chartMemoryCanvas.getContext('2d');
      Charts.memory = new Chart(ctx4, {
        type: 'bar',
        data: {
          labels: depths,
          datasets: [
            {
              label: 'Transposition Table Footprint (Est. KB)',
              data: scaling.memory_kb.alphabeta_tt,
              backgroundColor: 'rgba(52, 211, 153, 0.65)',
              borderColor: THEME_COLORS.abTT.border,
              borderWidth: 1.5,
              borderRadius: 6
            }
          ]
        },
        options: getBaseChartOptions('Allocated Memory (KB, Estimated)')
      });
    }
  }

  // Initialization lifecycle
  document.addEventListener('DOMContentLoaded', async () => {
    initDOM();
    if (!DOM.positionSelect || !DOM.btnRun) return;

    // Load dynamic positions list
    await loadPositions();

    // Attach event listeners
    DOM.btnRun.addEventListener('click', runBenchmark);
    DOM.positionSelect.addEventListener('change', () => {
      // Auto-trigger when position is changed
      runBenchmark();
    });

    // Run benchmark immediately to provide initial empirical data
    runBenchmark();
  });

})();
