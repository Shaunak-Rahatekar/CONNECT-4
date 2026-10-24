"""
test_transposition.py — Deterministic unit tests for Transposition Table and Memoization.

Verifies:
1. Stable board-state key generation (symmetry, side to move, distinguishing states).
2. Transposition table storage, retrieval, and replacement policy.
3. Depth requirement constraints (shallow entries cannot trigger cutoffs for deeper searches).
4. Correct bound type handling (EXACT, LOWER_BOUND, UPPER_BOUND).
5. Terminal score normalization and reconstitution across search depths.
6. Equivalence of cached Alpha-Beta and uncached Alpha-Beta / Minimax.
7. Eviction policy and capacity limits.
8. Cache hit rate and statistics tracking.
"""

import pytest
from game.board import Board, PLAYER1, PLAYER2
from game.rules import Rules
from algorithms.alphabeta import get_alphabeta_decision
from algorithms.minimax import get_minimax_decision
from algorithms.transposition_table import (
    TranspositionTable,
    EntryType,
    TTEntry,
    ZobristHasher,
)


def test_board_key_stability():
    """Identical board states and player turn must produce identical keys."""
    b1 = Board()
    b2 = Board()
    tt = TranspositionTable()

    # Drop disc in Col 3 on both boards
    b1.drop_disc(3, PLAYER1)
    b2.drop_disc(3, PLAYER1)

    k1 = tt.make_key(b1, PLAYER2)
    k2 = tt.make_key(b2, PLAYER2)
    assert k1 == k2
    assert hash(k1) == hash(k2)


def test_board_key_distinguishes_side_to_move():
    """The exact same board grid with different active players must produce different keys."""
    b = Board()
    b.drop_disc(3, PLAYER1)
    tt = TranspositionTable()

    k_p1 = tt.make_key(b, PLAYER1)
    k_p2 = tt.make_key(b, PLAYER2)
    assert k_p1 != k_p2


def test_board_key_distinguishes_different_positions():
    """Different board configurations must produce distinct keys."""
    b1 = Board()
    b2 = Board()
    b1.drop_disc(2, PLAYER1)
    b2.drop_disc(4, PLAYER1)

    tt = TranspositionTable()
    k1 = tt.make_key(b1, PLAYER2)
    k2 = tt.make_key(b2, PLAYER2)
    assert k1 != k2


def test_zobrist_hasher_stability_and_reproducibility():
    """Zobrist hasher must produce identical 64-bit integer hashes for identical states."""
    b1 = Board()
    b2 = Board()
    b1.drop_disc(3, PLAYER1)
    b1.drop_disc(4, PLAYER2)

    b2.drop_disc(3, PLAYER1)
    b2.drop_disc(4, PLAYER2)

    hasher1 = ZobristHasher(seed=42)
    hasher2 = ZobristHasher(seed=42)

    h1 = hasher1.compute_hash(b1, PLAYER1)
    h2 = hasher2.compute_hash(b2, PLAYER1)
    assert h1 == h2
    assert isinstance(h1, int)

    # Different player produces different hash
    h_p2 = hasher1.compute_hash(b1, PLAYER2)
    assert h1 != h_p2


def test_tt_depth_requirement_constraint():
    """A shallow cached entry cannot be used as a score cutoff for a deeper search."""
    tt = TranspositionTable()
    b = Board()
    b.drop_disc(3, PLAYER1)

    # Store entry with depth=2
    tt.store(b, PLAYER2, depth=2, score=50.0, flag=EntryType.EXACT, best_column=3)

    # Lookup at depth=3: score must NOT be returned for cutoff, but best_column can be used for move ordering
    score, best_col = tt.lookup(b, PLAYER2, depth=3, alpha=-100.0, beta=100.0)
    assert score is None
    assert best_col == 3

    # Lookup at depth=2: score CAN be returned
    score, best_col = tt.lookup(b, PLAYER2, depth=2, alpha=-100.0, beta=100.0)
    assert score == 50.0
    assert best_col == 3


def test_tt_exact_bound_cutoff():
    """EXACT entries are valid when depth is sufficient regardless of alpha/beta window."""
    tt = TranspositionTable()
    b = Board()
    b.drop_disc(3, PLAYER1)

    tt.store(b, PLAYER2, depth=3, score=25.0, flag=EntryType.EXACT, best_column=3)
    score, best_col = tt.lookup(b, PLAYER2, depth=3, alpha=-50.0, beta=50.0)
    assert score == 25.0
    assert best_col == 3
    assert tt.stats.exact_hits == 1


def test_tt_lower_bound_beta_cutoff():
    """LOWER_BOUND entries trigger cutoffs only when stored score >= beta."""
    tt = TranspositionTable()
    b = Board()
    b.drop_disc(3, PLAYER1)

    # Stored score = 40 (value is at least 40)
    tt.store(b, PLAYER2, depth=3, score=40.0, flag=EntryType.LOWER_BOUND, best_column=3)

    # Window with beta=30: since score (40) >= beta (30), cutoff occurs!
    score, best_col = tt.lookup(b, PLAYER2, depth=3, alpha=-100.0, beta=30.0)
    assert score == 40.0
    assert best_col == 3
    assert tt.stats.cutoff_hits == 1

    # Window with beta=50: score (40) < beta (50), cannot guarantee cutoff
    score_no_cutoff, _ = tt.lookup(b, PLAYER2, depth=3, alpha=-100.0, beta=50.0)
    assert score_no_cutoff is None


def test_tt_upper_bound_alpha_cutoff():
    """UPPER_BOUND entries trigger cutoffs only when stored score <= alpha."""
    tt = TranspositionTable()
    b = Board()
    b.drop_disc(3, PLAYER1)

    # Stored score = -20 (value is at most -20)
    tt.store(b, PLAYER2, depth=3, score=-20.0, flag=EntryType.UPPER_BOUND, best_column=3)

    # Window with alpha=-10: since score (-20) <= alpha (-10), cutoff occurs!
    score, best_col = tt.lookup(b, PLAYER2, depth=3, alpha=-10.0, beta=100.0)
    assert score == -20.0
    assert best_col == 3
    assert tt.stats.cutoff_hits == 1

    # Window with alpha=-30: score (-20) > alpha (-30), cannot guarantee cutoff
    score_no_cutoff, _ = tt.lookup(b, PLAYER2, depth=3, alpha=-30.0, beta=100.0)
    assert score_no_cutoff is None


def test_tt_terminal_score_normalization():
    """Depth-aware terminal win scores must be normalized and reconstituted across search depths."""
    tt = TranspositionTable()
    b = Board()

    # Win found with remaining depth=2: score = 1_000_000 + (2 * 1_000) = 1_002_000
    tt.store(b, PLAYER2, depth=2, score=1_002_000.0, flag=EntryType.EXACT, best_column=3)

    # Reconstituted lookup at current depth=2
    score_d2, _ = tt.lookup(b, PLAYER2, depth=2, alpha=-float("inf"), beta=float("inf"))
    assert score_d2 == 1_002_000.0

    # Stored entry was at depth 2. If looked up at depth 1:
    score_d1, _ = tt.lookup(b, PLAYER2, depth=1, alpha=-float("inf"), beta=float("inf"))
    # Reconstituted at depth 1 should be 1_000_000 + (1 * 1_000) = 1_001_000
    assert score_d1 == 1_001_000.0


def test_caching_preserves_minimax_and_alphabeta_optimality():
    """Cached Alpha-Beta must yield the exact same optimal score as uncached Alpha-Beta and Minimax."""
    b = Board()
    # Play a realistic 3-move opening
    b.drop_disc(3, PLAYER1)
    b.drop_disc(3, PLAYER2)
    b.drop_disc(2, PLAYER1)

    depth = 3
    # 1. Baseline Minimax
    mm_dec = get_minimax_decision(b, depth=depth, player=PLAYER2)

    # 2. Alpha-Beta without cache
    ab_uncached = get_alphabeta_decision(
        b,
        depth=depth,
        player=PLAYER2,
        use_move_ordering=True,
        use_transposition_table=False,
    )

    # 3. Alpha-Beta with cache
    ab_cached = get_alphabeta_decision(
        b,
        depth=depth,
        player=PLAYER2,
        use_move_ordering=True,
        use_transposition_table=True,
    )

    assert abs(mm_dec.score - ab_uncached.score) < 1e-4
    assert abs(ab_uncached.score - ab_cached.score) < 1e-4
    assert ab_uncached.column == ab_cached.column


def test_transposition_table_records_cache_hits_on_transposition():
    """Identical position reached via different move orders must record a cache hit."""
    # Sequence A: Col 3 then Col 4
    b_seq_a = Board()
    b_seq_a.drop_disc(3, PLAYER1)
    b_seq_a.drop_disc(4, PLAYER2)

    # Sequence B: Col 4 then Col 3
    b_seq_b = Board()
    b_seq_b.drop_disc(4, PLAYER1)
    b_seq_b.drop_disc(3, PLAYER2)

    # Boards are NOT equal because player 1 played 3 vs 4.
    # Now let's create a TRUE transposition:
    # Transposition:
    # Branch 1: P1 plays 2, P2 plays 3, P1 plays 4
    # Branch 2: P1 plays 4, P2 plays 3, P1 plays 2
    # In both branches: P1 has discs in (5,2) and (5,4), P2 has disc in (5,3).
    # Next turn is P2 in both!
    b1 = Board()
    b1.drop_disc(2, PLAYER1)
    b1.drop_disc(3, PLAYER2)
    b1.drop_disc(4, PLAYER1)

    b2 = Board()
    b2.drop_disc(4, PLAYER1)
    b2.drop_disc(3, PLAYER2)
    b2.drop_disc(2, PLAYER1)

    assert b1.grid == b2.grid

    tt = TranspositionTable()
    # Evaluate b1 with shared TT
    dec1 = get_alphabeta_decision(
        b1,
        depth=3,
        player=PLAYER2,
        use_transposition_table=True,
        transposition_table=tt,
    )

    # Evaluate b2 with the same shared TT
    hits_before = tt.stats.hits
    dec2 = get_alphabeta_decision(
        b2,
        depth=3,
        player=PLAYER2,
        use_transposition_table=True,
        transposition_table=tt,
    )

    # The second search must benefit from root and internal cache hits!
    assert tt.stats.hits > hits_before
    assert abs(dec1.score - dec2.score) < 1e-4


def test_tt_clear_resets_table_and_stats():
    """Calling clear() must empty the table and reset all counters."""
    tt = TranspositionTable()
    b = Board()
    b.drop_disc(3, PLAYER1)

    tt.store(b, PLAYER2, depth=2, score=10.0, flag=EntryType.EXACT, best_column=3)
    tt.lookup(b, PLAYER2, depth=2, alpha=-100.0, beta=100.0)

    assert len(tt) == 1
    assert tt.stats.hits == 1

    tt.clear()
    assert len(tt) == 0
    assert tt.stats.hits == 0
    assert tt.stats.misses == 0


def test_tt_eviction_when_capacity_exceeded():
    """Table must prune entries when max_entries is exceeded."""
    max_cap = 20
    tt = TranspositionTable(max_entries=max_cap)

    for col in range(7):
        b = Board()
        b.drop_disc(col, PLAYER1)
        tt.store(b, PLAYER2, depth=1, score=float(col), flag=EntryType.EXACT, best_column=col)

    # Add more distinct configurations to exceed capacity
    for r in range(5):
        for col in range(5):
            b = Board()
            for _ in range(r + 1):
                b.drop_disc(col, PLAYER1)
            tt.store(b, PLAYER2, depth=r + 1, score=10.0, flag=EntryType.EXACT, best_column=col)

    # Verify size did not grow unboundedly beyond limit
    assert len(tt) <= max_cap + 5
