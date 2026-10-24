"""
positions.py — Canonical benchmark board positions for Connect-4 AI evaluation.

Provides fixed, reproducible test positions representing distinct game phases:
1. Opening Phase: Center-dominated early development.
2. Tactical Threat Phase: Immediate horizontal/vertical block required.
3. Midgame Phase: Clustered tactical struggle with high branching.
4. Symmetric Transposition Phase: Symmetrical dual-flank development.

All positions return a fresh, independent `Board` instance ready for benchmarking.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

from game.board import Board, PLAYER1, PLAYER2


@dataclass(frozen=True)
class BenchmarkPosition:
    """Descriptor for a reproducible benchmark scenario."""
    id: str
    name: str
    description: str
    phase: str
    player_to_move: int
    builder: Callable[[], Board]

    def create_board(self) -> Board:
        """Create a fresh, isolated board instance for this position."""
        return self.builder()


def _build_opening_center() -> Board:
    """Human (P1) plays center column (3)."""
    b = Board()
    b.drop_disc(3, PLAYER1)
    return b


def _build_tactical_block_required() -> Board:
    """Human (P1) has 3-in-a-row horizontally (cols 1, 2, 3), threatening win."""
    b = Board()
    b.drop_disc(1, PLAYER1)
    b.drop_disc(1, PLAYER2)
    b.drop_disc(2, PLAYER1)
    b.drop_disc(2, PLAYER2)
    b.drop_disc(3, PLAYER1)
    return b


def _build_midgame_complex() -> Board:
    """Complex 8-move midgame with contested center."""
    b = Board()
    moves = [
        (3, PLAYER1), (3, PLAYER2),
        (2, PLAYER1), (4, PLAYER2),
        (4, PLAYER1), (2, PLAYER2),
        (3, PLAYER1), (3, PLAYER2),
    ]
    for col, p in moves:
        b.drop_disc(col, p)
    return b


def _build_symmetric_transposition() -> Board:
    """Symmetrical dual-flank position with high transposition potential."""
    b = Board()
    moves = [
        (1, PLAYER1), (5, PLAYER2),
        (2, PLAYER1), (4, PLAYER2),
        (5, PLAYER1), (1, PLAYER2),
    ]
    for col, p in moves:
        b.drop_disc(col, p)
    return b


# Registry of canonical benchmark test positions
BENCHMARK_POSITIONS: dict[str, BenchmarkPosition] = {
    "opening_center": BenchmarkPosition(
        id="opening_center",
        name="Opening (Center Move)",
        description="Single opening move in Column 4. Tests root expansion and center-bias pruning.",
        phase="Opening",
        player_to_move=PLAYER2,
        builder=_build_opening_center,
    ),
    "tactical_block": BenchmarkPosition(
        id="tactical_block",
        name="Tactical Block (Threat Response)",
        description="Opponent threatens 4-in-a-row. Tests tactical priority and forced cutoffs.",
        phase="Tactical",
        player_to_move=PLAYER2,
        builder=_build_tactical_block_required,
    ),
    "midgame_complex": BenchmarkPosition(
        id="midgame_complex",
        name="Midgame Center Battle",
        description="8 discs played in central columns. Tests deep tree evaluation and branching.",
        phase="Midgame",
        player_to_move=PLAYER1,
        builder=_build_midgame_complex,
    ),
    "symmetric_transposition": BenchmarkPosition(
        id="symmetric_transposition",
        name="Symmetric Dual-Flank",
        description="Symmetrical moves across flanks. Tests transposition table cache reuse.",
        phase="Midgame Transpositions",
        player_to_move=PLAYER2,
        builder=_build_symmetric_transposition,
    ),
}


def get_position(position_id: str) -> BenchmarkPosition:
    """Retrieve benchmark position by key, defaulting to opening_center."""
    return BENCHMARK_POSITIONS.get(position_id, BENCHMARK_POSITIONS["opening_center"])


def list_positions() -> list[dict[str, str]]:
    """List summary metadata for all benchmark positions."""
    return [
        {
            "id": pos.id,
            "name": pos.name,
            "description": pos.description,
            "phase": pos.phase,
            "player_to_move": pos.player_to_move,
        }
        for pos in BENCHMARK_POSITIONS.values()
    ]
