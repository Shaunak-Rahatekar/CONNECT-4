"""
transposition_table.py — Memoization and Transposition Table for Connect-4 AI.

Design and Analysis of Algorithms (DAA Unit III & IV):
------------------------------------------------------
In game tree search, the game space is technically a Directed Acyclic Graph (DAG),
not a tree. Different sequences of moves can lead to the exact same board configuration;
such identical states reached via different move orders are called "transpositions".
For example:
    Player 1 plays Column 3, Player 2 plays Column 4
        vs.
    Player 1 plays Column 4, Player 2 plays Column 3
result in the identical board state with Player 1 to move.

Without memoization, tree search re-evaluates the subtree rooted at this state multiple
times, leading to redundant work. A Transposition Table (TT) caches previous search results
indexed by a stable representation of the board state and the active player.

Key Implementation Considerations:
----------------------------------
1. Stable Board Key:
   - Canonical tuple representation: ((row_0), (row_1), ..., (row_5), current_player)
   - Completely collision-free (0.0 collision probability).
   - Fast to compute, hashable, and immutable.
   - An optional 64-bit Zobrist hashing scheme is also provided and documented for reference.

2. Bound Types in Alpha-Beta Pruning:
   - EXACT: The true minimax value was found within the search window (alpha < score < beta).
   - LOWER_BOUND: A beta-cutoff occurred (score >= beta). The true minimax value is at least `score`.
   - UPPER_BOUND: All moves failed low (score <= alpha). The true minimax value is at most `score`.

3. Depth Requirement:
   - A cached entry is valid for cutoff reuse ONLY if its `stored_depth >= current_search_depth`.
   - If `stored_depth < current_search_depth`, the entry cannot provide a score cutoff, BUT its
     `best_column` can still be used for Move Ordering (Hash Move), speeding up cutoffs!

4. Depth-Aware Terminal Score Normalization:
   - Terminal win/loss scores incorporate remaining search depth:
         Win:  +TERMINAL_WIN_BASE + (depth * 1,000)
         Loss: -TERMINAL_WIN_BASE - (depth * 1,000)
   - To make cached terminal scores invariant across different root depths, scores are normalized
     to "distance from current node" when stored, and reconstituted when retrieved.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import random
import sys
from typing import Any, Union

from game.board import Board, ROWS, COLS, PLAYER1, PLAYER2
from algorithms.minimax import TERMINAL_WIN_BASE


class EntryType(str, Enum):
    """Classification of stored evaluation bounds from Alpha-Beta search."""
    EXACT = "EXACT"              # Value is exact (alpha < value < beta)
    LOWER_BOUND = "LOWER_BOUND"  # Beta-cutoff occurred: true value >= stored score
    UPPER_BOUND = "UPPER_BOUND"  # All moves failed low: true value <= stored score


# Threshold defining terminal scores (beyond standard heuristic range)
TERMINAL_THRESHOLD: float = 900_000.0


@dataclass
class TTEntry:
    """A single cached entry in the transposition table."""
    key: tuple[tuple[int, ...], ...] | int
    depth: int
    score: float
    flag: EntryType
    best_column: int | None
    age: int = 0


@dataclass
class TranspositionTableStats:
    """Real-time performance counters for the transposition table."""
    hits: int = 0
    misses: int = 0
    stores: int = 0
    overwrites: int = 0
    exact_hits: int = 0
    cutoff_hits: int = 0

    @property
    def total_lookups(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate_pct(self) -> float:
        if self.total_lookups == 0:
            return 0.0
        return round((self.hits / self.total_lookups) * 100.0, 2)

    def reset(self) -> None:
        self.hits = 0
        self.misses = 0
        self.stores = 0
        self.overwrites = 0
        self.exact_hits = 0
        self.cutoff_hits = 0


class ZobristHasher:
    """64-bit Zobrist Hashing implementation for Connect-4.

    Theory & Design:
    ----------------
    Zobrist hashing assigns a pseudorandom 64-bit integer to each possible piece
    at each (row, col) cell, plus a random constant for the player turn.
    The hash of a board is the XOR sum of these random values.

    Properties:
    - O(1) incremental update when discs are dropped/undone via XOR.
    - Collision Probability: 1 / 2^64 ≈ 5.42 × 10^-20 for random states.
    - Reproducibility: Initialized with a deterministic Mersenne Twister seed (42).
    """

    def __init__(self, seed: int = 42) -> None:
        rng = random.Random(seed)
        # Table of shape [ROWS][COLS][3] (0=empty, 1=player1, 2=player2)
        self.table: list[list[list[int]]] = [
            [[rng.getrandbits(64) for _ in range(3)] for _ in range(COLS)]
            for _ in range(ROWS)
        ]
        self.turn_p2: int = rng.getrandbits(64)

    def compute_hash(self, board: Board, current_player: int) -> int:
        """Compute full 64-bit Zobrist hash for a board state."""
        h = 0
        grid = board.grid
        for r in range(ROWS):
            for c in range(COLS):
                piece = grid[r][c]
                if piece != 0:
                    h ^= self.table[r][c][piece]
        if current_player == PLAYER2:
            h ^= self.turn_p2
        return h


class TranspositionTable:
    """High-performance transposition table with configurable replacement policy."""

    def __init__(
        self,
        max_entries: int = 100_000,
        use_zobrist: bool = False,
    ) -> None:
        """Initialize transposition table.

        Parameters:
        -----------
        max_entries : int
            Maximum number of entries to hold before pruning/replacing (default 100,000).
        use_zobrist : bool
            If True, uses 64-bit Zobrist integer hashes as dictionary keys.
            If False (default), uses canonical immutable tuple states with zero collision risk.
        """
        self.max_entries: int = max(10, max_entries)
        self.use_zobrist: bool = use_zobrist
        self.zobrist: ZobristHasher | None = ZobristHasher() if use_zobrist else None
        self._table: dict[Any, TTEntry] = {}
        self.stats: TranspositionTableStats = TranspositionTableStats()
        self._generation: int = 0

    def make_key(self, board: Board, current_player: int) -> Any:
        """Create a stable hash key incorporating the grid and current player."""
        if self.use_zobrist and self.zobrist is not None:
            return self.zobrist.compute_hash(board, current_player)
        return (board.to_tuple(), current_player)

    def normalize_score_to_tt(self, score: float, depth: int) -> float:
        """Normalize depth-dependent terminal scores for storage in the TT.

        In Minimax/Alpha-Beta, win score is: TERMINAL_WIN_BASE + (depth * 1000).
        Here `depth` is the remaining depth to search. A win found with depth `d`
        means the winning state is (initial_depth - d) moves from the root, or
        specifically 1 or more plies from the CURRENT node.
        By storing the distance from the current node:
            moves_away = - (score - TERMINAL_WIN_BASE) / 1000 + depth  (for win)
        To keep it simple and mathematically sound:
        - If score > TERMINAL_THRESHOLD:
          The score stored is `score - (depth * 1000)`.
          Then when reconstituted at current remaining depth `d'`:
          reconstituted = `stored + (d' * 1000)`.
        - If score < -TERMINAL_THRESHOLD:
          The score stored is `score + (depth * 1000)`.
          Then when reconstituted at current remaining depth `d'`:
          reconstituted = `stored - (d' * 1000)`.
        - If within heuristic range: stored unchanged.
        """
        if score > TERMINAL_THRESHOLD:
            return score - (depth * 1_000.0)
        elif score < -TERMINAL_THRESHOLD:
            return score + (depth * 1_000.0)
        return score

    def normalize_score_from_tt(self, stored_score: float, current_depth: int) -> float:
        """Reconstitute depth-dependent terminal score for the current search depth."""
        if stored_score > (TERMINAL_THRESHOLD - 50_000.0):
            return stored_score + (current_depth * 1_000.0)
        elif stored_score < (-TERMINAL_THRESHOLD + 50_000.0):
            return stored_score - (current_depth * 1_000.0)
        return stored_score

    def lookup(
        self,
        board: Board,
        current_player: int,
        depth: int,
        alpha: float,
        beta: float,
    ) -> tuple[float | None, int | None]:
        """Look up board state in transposition table.

        Parameters:
        -----------
        board : Board
            Current board configuration.
        current_player : int
            Active player whose turn is being evaluated.
        depth : int
            Current remaining search depth.
        alpha : float
            Current alpha bound.
        beta : float
            Current beta bound.

        Returns:
        --------
        (usable_score, best_column)
        - `usable_score`: Non-None if the entry satisfies depth and bound constraints for an early cutoff.
        - `best_column`: Best move stored in TT (useful for Move Ordering even when depth is insufficient).
        """
        key = self.make_key(board, current_player)
        entry = self._table.get(key)

        if entry is None:
            self.stats.misses += 1
            return None, None

        best_col = entry.best_column

        # Depth Condition: entry must have been searched to at least the current depth
        if entry.depth < depth:
            # Cannot use score for cutoff, but can still use best_column for move ordering!
            self.stats.misses += 1
            return None, best_col

        reconstituted_score = self.normalize_score_from_tt(entry.score, depth)

        if entry.flag == EntryType.EXACT:
            self.stats.hits += 1
            self.stats.exact_hits += 1
            return reconstituted_score, best_col

        elif entry.flag == EntryType.LOWER_BOUND:
            # Stored score is a lower bound (value >= reconstituted_score)
            if reconstituted_score >= beta:
                self.stats.hits += 1
                self.stats.cutoff_hits += 1
                return reconstituted_score, best_col

        elif entry.flag == EntryType.UPPER_BOUND:
            # Stored score is an upper bound (value <= reconstituted_score)
            if reconstituted_score <= alpha:
                self.stats.hits += 1
                self.stats.cutoff_hits += 1
                return reconstituted_score, best_col

        self.stats.misses += 1
        return None, best_col

    def store(
        self,
        board: Board,
        current_player: int,
        depth: int,
        score: float,
        flag: EntryType,
        best_column: int | None,
    ) -> None:
        """Store or update search evaluation in the transposition table.

        Replacement Policy:
        - Depth-preferred: Always replace an existing entry if the new entry was searched to
          greater or equal depth.
        - If depth is shallower, keep the deeper entry, but update its best_column if empty.
        - If cache limit is reached, evicts shallowest entries or evicts 15% of oldest entries.
        """
        key = self.make_key(board, current_player)
        normalized_score = self.normalize_score_to_tt(score, depth)

        existing = self._table.get(key)
        if existing is not None:
            # Depth-preferred replacement
            if depth >= existing.depth:
                existing.depth = depth
                existing.score = normalized_score
                existing.flag = flag
                if best_column is not None:
                    existing.best_column = best_column
                existing.age = self._generation
                self.stats.overwrites += 1
            else:
                # Keep existing deeper score, but record best_column if missing
                if existing.best_column is None and best_column is not None:
                    existing.best_column = best_column
            return

        # Handle size capacity eviction
        if len(self._table) >= self.max_entries:
            self._evict_entries()

        self._table[key] = TTEntry(
            key=key,
            depth=depth,
            score=normalized_score,
            flag=flag,
            best_column=best_column,
            age=self._generation,
        )
        self.stats.stores += 1

    def _evict_entries(self) -> None:
        """Evict approximately 15% of the table prioritizing shallow search depths."""
        target_evict = max(1, len(self._table) // 7)
        # Sort items by depth ascending (shallowest first)
        sorted_keys = sorted(self._table.keys(), key=lambda k: self._table[k].depth)
        for k in sorted_keys[:target_evict]:
            del self._table[k]

    def clear(self) -> None:
        """Completely clear transposition table entries and reset statistics."""
        self._table.clear()
        self.stats.reset()
        self._generation = 0

    def advance_generation(self) -> None:
        """Advance search generation counter."""
        self._generation += 1

    def __len__(self) -> int:
        return len(self._table)

    def size(self) -> int:
        return len(self._table)

    def get_memory_estimate(self) -> dict[str, Any]:
        """Calculate exact dictionary structure size and estimated total memory consumption.

        Memory Accounting Details:
        - `dict_overhead_bytes`: Exact measurement via `sys.getsizeof(self._table)`.
        - `entry_count`: Total number of active entries.
        - `entry_estimated_bytes`: Each TTEntry instance + tuple key + entry overhead in CPython
          averages ~200 bytes.
        - Returns clearly delineated exact vs estimated memory figures.
        """
        dict_overhead = sys.getsizeof(self._table)
        count = len(self._table)
        # In Python 64-bit: TTEntry instance (~56 bytes) + key tuple (~112 bytes) + dict node (~24 bytes) ≈ 192 bytes
        per_entry_estimate = 192
        total_estimated_bytes = dict_overhead + (count * per_entry_estimate)

        return {
            "entry_count": count,
            "max_entries": self.max_entries,
            "dict_overhead_bytes": dict_overhead,
            "per_entry_estimated_bytes": per_entry_estimate,
            "total_estimated_bytes": total_estimated_bytes,
            "total_estimated_kb": round(total_estimated_bytes / 1024.0, 2),
            "total_estimated_mb": round(total_estimated_bytes / (1024.0 * 1024.0), 3),
            "is_estimate": True,
            "key_type": "zobrist_int64" if self.use_zobrist else "canonical_tuple",
        }


# Global transposition table instance for session re-use
_GLOBAL_TT = TranspositionTable(max_entries=100_000)


def get_global_transposition_table() -> TranspositionTable:
    """Retrieve the shared transposition table instance."""
    return _GLOBAL_TT
