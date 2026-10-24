"""
game package — Connect-4 game engine.

Exposes Board, Rules, GameState, and functional engine utilities:
    from game import (
        Board,
        Rules,
        GameState,
        create_board,
        get_valid_moves,
        make_move,
        check_winner,
        is_draw,
        get_game_status,
        ROWS,
        COLS,
        EMPTY,
        PLAYER1,
        PLAYER2,
    )
"""

from game.board import Board, ROWS, COLS, EMPTY, PLAYER1, PLAYER2
from game.rules import Rules, GameState
from game.engine import (
    create_board,
    get_valid_moves,
    make_move,
    check_winner,
    is_draw,
    get_game_status,
)

__all__ = [
    "Board",
    "Rules",
    "GameState",
    "create_board",
    "get_valid_moves",
    "make_move",
    "check_winner",
    "is_draw",
    "get_game_status",
    "ROWS",
    "COLS",
    "EMPTY",
    "PLAYER1",
    "PLAYER2",
]
