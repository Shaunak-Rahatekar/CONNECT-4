"""
game package — Connect-4 game engine.

Exposes Board and Rules as the public API so importers can write:
    from game import Board, Rules
"""

from game.board import Board
from game.rules import Rules

__all__ = ["Board", "Rules"]
