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


# ---------------------------------------------------------------------------
# Bug 2: winning move on the final empty cell must be a win, not a draw
# ---------------------------------------------------------------------------

def test_winning_move_on_last_cell_is_a_win_not_a_draw():
    """X completes a row on the 9th (last) cell – must be declared a win."""
    engine = GameEngine()
    # Board: 8 cells filled, (0,2) is the only empty cell.
    # Placing X there completes row 0 → X wins.
    engine.board = [
        ['X', 'X', None],   # (0,2) will complete the row
        ['O', 'O', 'X'],
        ['O', 'X', 'O'],
    ]
    engine.check_round_end()   # board not yet full – no result expected yet

    # Now place the winning final move directly and call check_round_end
    engine.board[0][2] = 'X'
    engine.check_round_end()

    assert engine.round_over is True
    assert engine.winner == 'X', (
        "A win on the last cell must set winner='X', not trigger a draw"
    )


def test_full_board_with_no_winner_is_a_draw():
    """A completely filled board with no three-in-a-row is correctly a draw."""
    engine = GameEngine()
    # Classic drawn configuration – no winner in any direction
    engine.board = [
        ['X', 'O', 'X'],
        ['O', 'X', 'O'],
        ['O', 'X', 'O'],
    ]
    engine.check_round_end()

    assert engine.round_over is True
    assert engine.winner is None, (
        "A full board with no winner must set winner=None (draw)"
    )


# ---------------------------------------------------------------------------
# Bug 4: clicking an occupied cell must not overwrite its symbol or advance turn
# ---------------------------------------------------------------------------

def test_clicking_cell_with_O_does_not_overwrite():
    """Clicking a cell that contains O must leave it as O and keep X's turn."""
    engine = GameEngine()
    engine.board[1][1] = 'O'   # plant an O in the centre
    player_before = engine.current_player   # 'X'

    click(engine, 1, 1)   # X tries to overwrite O

    assert engine.board[1][1] == 'O', "O must not be overwritten by X"
    assert engine.current_player == player_before, "Turn must not advance after a blocked click"


def test_clicking_cell_with_X_does_not_overwrite():
    """Clicking a cell that contains X must leave it as X and keep X's turn."""
    engine = GameEngine()
    engine.board[0][0] = 'X'   # plant an X in the corner
    player_before = engine.current_player   # 'X'

    click(engine, 0, 0)   # X tries to click its own cell

    assert engine.board[0][0] == 'X', "X must not be overwritten"
    assert engine.current_player == player_before, "Turn must not advance after a blocked click"
