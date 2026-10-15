"""
Tests for GameEngine.handle_click – focused on post-round-over click guard.

board_pos_to_cell maps pixel coords → (row, col):
  BOARD_TOP = 100, CELL_SIZE = 120
  cell (r, c) centre ≈ (c*120 + 60,  r*120 + 100 + 60)
We patch board_pos_to_cell so these tests have no pygame dependency.
"""

import copy
import pytest
from unittest.mock import patch
from game.game_engine import GameEngine


# ---------------------------------------------------------------------------
# Helper: make a valid pixel-pos for any (row, col)
# ---------------------------------------------------------------------------
CELL_SIZE = 120
BOARD_TOP = 100

def pixel_for(row, col):
    """Return a pixel coordinate that board_pos_to_cell maps to (row, col)."""
    return (col * CELL_SIZE + CELL_SIZE // 2,
            BOARD_TOP + row * CELL_SIZE + CELL_SIZE // 2)


def click(engine, row, col):
    """Click cell (row, col) on engine; bypasses pygame via direct patch."""
    with patch("game.game_engine.board_pos_to_cell", return_value=(row, col)):
        engine.handle_click(pixel_for(row, col))


# ---------------------------------------------------------------------------
# Core bug: clicking after the round ends must be a no-op
# ---------------------------------------------------------------------------

def test_click_after_win_does_not_change_board():
    """After X wins, clicking an empty cell must leave the board unchanged."""
    engine = GameEngine()
    # Force a won state directly – row 0 is all X
    engine.board[0] = ['X', 'X', 'X']
    engine.round_over = True
    engine.winner = 'X'

    board_before = copy.deepcopy(engine.board)
    player_before = engine.current_player

    click(engine, 1, 0)   # empty cell – should be ignored

    assert engine.board == board_before, "Board must not change after round ends"
    assert engine.current_player == player_before, "Current player must not change after round ends"


def test_click_after_draw_does_not_change_board():
    """After a draw, clicking an empty cell must leave the board unchanged."""
    engine = GameEngine()
    # Near-full board with one empty cell at (2, 2), no winner
    engine.board = [
        ['X', 'O', 'X'],
        ['O', 'O', 'X'],
        ['X', 'X', None],
    ]
    engine.round_over = True
    engine.winner = None

    board_before = copy.deepcopy(engine.board)
    player_before = engine.current_player

    click(engine, 2, 2)   # the only empty cell

    assert engine.board == board_before
    assert engine.current_player == player_before


def test_click_after_loss_does_not_change_board():
    """After O wins, clicking an empty cell must leave the board unchanged."""
    engine = GameEngine()
    engine.board[0] = ['O', 'O', 'O']
    engine.round_over = True
    engine.winner = 'O'

    board_before = copy.deepcopy(engine.board)
    player_before = engine.current_player

    click(engine, 1, 1)

    assert engine.board == board_before
    assert engine.current_player == player_before


# ---------------------------------------------------------------------------
# Regression: normal gameplay still works when round is active
# ---------------------------------------------------------------------------

def test_click_on_empty_cell_places_symbol_during_active_round():
    """During a live round, clicking an empty cell must place X."""
    engine = GameEngine()
    assert engine.round_over is False

    with patch("game.game_engine.board_pos_to_cell", return_value=(0, 0)), \
         patch("game.game_engine.choose_move", return_value=None):   # suppress AI so board stays predictable
        engine.handle_click(pixel_for(0, 0))

    assert engine.board[0][0] == 'X', "X should be placed on an empty cell during an active round"


def test_restart_with_r_clears_round_over():
    """Pressing R resets round_over to False, re-enabling clicks."""
    import pygame
    pygame.init()

    engine = GameEngine()
    engine.round_over = True
    engine.winner = 'X'

    engine.handle_keydown(pygame.K_r)

    assert engine.round_over is False
    assert engine.winner is None
    assert engine.board == [[None] * 3 for _ in range(3)]

    pygame.quit()
