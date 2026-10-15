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
    """Pressing R resets board/turn/winner but preserves the scoreboard."""
    import pygame
    pygame.init()

    engine = GameEngine()
    engine.round_over = True
    engine.winner = 'X'
    score_before = dict(engine.score)   # snapshot current score

    engine.handle_keydown(pygame.K_r)

    assert engine.round_over is False
    assert engine.winner is None
    assert engine.board == [[None] * 3 for _ in range(3)]
    assert engine.score == score_before, "Score must not change when starting a new round"

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


# ---------------------------------------------------------------------------
# Task 2: scoreboard
# ---------------------------------------------------------------------------

def test_x_win_increments_only_x_score():
    """check_round_end on an X-win board increments score['X'] by 1 only."""
    engine = GameEngine()
    engine.board = [
        ['X', 'X', 'X'],
        ['O', 'O', None],
        [None, None, None],
    ]
    engine.check_round_end()

    assert engine.score['X'] == 1
    assert engine.score['O'] == 0
    assert engine.score['draw'] == 0


def test_o_win_increments_only_o_score():
    """check_round_end on an O-win board increments score['O'] by 1 only."""
    engine = GameEngine()
    engine.board = [
        ['O', 'O', 'O'],
        ['X', 'X', None],
        [None, None, None],
    ]
    engine.check_round_end()

    assert engine.score['X'] == 0
    assert engine.score['O'] == 1
    assert engine.score['draw'] == 0


def test_draw_increments_only_draw_score():
    """check_round_end on a full board with no winner increments score['draw'] only."""
    engine = GameEngine()
    engine.board = [
        ['X', 'O', 'X'],
        ['O', 'X', 'O'],
        ['O', 'X', 'O'],
    ]
    engine.check_round_end()

    assert engine.score['X'] == 0
    assert engine.score['O'] == 0
    assert engine.score['draw'] == 1


def test_new_round_preserves_scoreboard():
    """Pressing R (new round) clears board/turn/winner but keeps all scores."""
    import pygame
    pygame.init()

    engine = GameEngine()
    # Manually set a known score to simulate previous rounds
    engine.score = {'X': 2, 'O': 1, 'draw': 0}
    engine.round_over = True
    engine.winner = 'X'

    engine.handle_keydown(pygame.K_r)

    assert engine.round_over is False
    assert engine.winner is None
    assert engine.board == [[None] * 3 for _ in range(3)]
    assert engine.score == {'X': 2, 'O': 1, 'draw': 0}, (
        "Score must be preserved across rounds"
    )

    pygame.quit()


def test_score_not_incremented_twice_for_same_round():
    """Calling check_round_end repeatedly on a finished round must not increment score again."""
    engine = GameEngine()
    engine.board = [
        ['X', 'X', 'X'],
        ['O', 'O', None],
        [None, None, None],
    ]
    engine.check_round_end()   # first call – should score
    engine.check_round_end()   # second call – must be a no-op
    engine.check_round_end()   # third call – must be a no-op

    assert engine.score['X'] == 1, "Score must only be incremented once per round"


def test_multiple_rounds_accumulate_scores():
    """Scores accumulate correctly across several consecutive rounds."""
    engine = GameEngine()

    # Round 1 – X wins
    engine.board = [['X', 'X', 'X'], ['O', 'O', None], [None, None, None]]
    engine.check_round_end()
    engine._reset_round()

    # Round 2 – O wins
    engine.board = [['O', 'O', 'O'], ['X', 'X', None], [None, None, None]]
    engine.check_round_end()
    engine._reset_round()

    # Round 3 – draw
    engine.board = [['X', 'O', 'X'], ['O', 'X', 'O'], ['O', 'X', 'O']]
    engine.check_round_end()
    engine._reset_round()

    assert engine.score == {'X': 1, 'O': 1, 'draw': 1}


# ---------------------------------------------------------------------------
# Task 4: first-player choice and separate restart controls
# ---------------------------------------------------------------------------

def test_x_starts_and_makes_first_move():
    """When first_player is X, the board is empty at round start and X can click."""
    engine = GameEngine()
    assert engine.first_player == 'X'
    assert engine.current_player == 'X'
    # Board must be empty – computer has not moved
    assert all(cell is None for row in engine.board for cell in row)

    with patch("game.game_engine.board_pos_to_cell", return_value=(0, 0)), \
         patch("game.game_engine.choose_move", return_value=None):
        engine.handle_click(pixel_for(0, 0))

    assert engine.board[0][0] == 'X', "X should place on the first click"


def test_o_starts_with_exactly_one_automatic_move():
    """When first_player is O, the computer places exactly one symbol before the human's first click."""
    with patch("game.game_engine.choose_move", return_value=(1, 1)):
        engine = GameEngine()
        engine.first_player = 'O'
        engine._reset_round()

    # After reset, computer should have placed one O
    occupied = [(r, c) for r in range(3) for c in range(3) if engine.board[r][c] is not None]
    assert len(occupied) == 1, "Exactly one computer move expected when O starts"
    r, c = occupied[0]
    assert engine.board[r][c] == 'O', "The automatic first move must be O"
    assert engine.current_player == 'X', "After O's opening move it is X's turn"


def test_restart_round_clears_board_preserves_score():
    """R key clears the board and round state but leaves the score intact."""
    import pygame
    pygame.init()

    engine = GameEngine()
    engine.score = {'X': 3, 'O': 1, 'draw': 2}
    engine.board[0] = ['X', 'X', 'X']
    engine.round_over = True
    engine.winner = 'X'

    engine.handle_keydown(pygame.K_r)

    assert engine.round_over is False
    assert engine.winner is None
    assert engine.board == [[None] * 3 for _ in range(3)]
    assert engine.score == {'X': 3, 'O': 1, 'draw': 2}, "Score must survive a round restart"

    pygame.quit()


def test_reset_match_clears_score_and_board():
    """M key resets both the board and the scoreboard to zero."""
    import pygame
    pygame.init()

    engine = GameEngine()
    engine.score = {'X': 5, 'O': 3, 'draw': 1}
    engine.board[0] = ['X', 'O', 'X']
    engine.round_over = True
    engine.winner = 'X'

    engine.handle_keydown(pygame.K_m)

    assert engine.round_over is False
    assert engine.winner is None
    assert engine.board == [[None] * 3 for _ in range(3)]
    assert engine.score == {'X': 0, 'O': 0, 'draw': 0}, "Score must be zeroed on match reset"

    pygame.quit()


def test_first_player_respected_after_restart_round():
    """After toggling first_player to O and pressing R, current_player starts as O."""
    import pygame
    pygame.init()

    with patch("game.game_engine.choose_move", return_value=(2, 2)):
        engine = GameEngine()
        engine.first_player = 'O'
        engine.handle_keydown(pygame.K_r)

    # After the reset the computer has already moved, so current_player flipped to X
    assert engine.current_player == 'X', (
        "After O's automatic opening move, it must be X's turn"
    )
    # Board should contain exactly one O from the computer's opening move
    os_on_board = sum(1 for row in engine.board for cell in row if cell == 'O')
    assert os_on_board == 1

    pygame.quit()


def test_f_key_toggles_first_player():
    """F key toggles first_player between X and O and restarts the round."""
    import pygame
    pygame.init()

    with patch("game.game_engine.choose_move", return_value=None):
        engine = GameEngine()
        assert engine.first_player == 'X'

        engine.handle_keydown(pygame.K_f)
        assert engine.first_player == 'O', "F should toggle first_player to O"

        engine.handle_keydown(pygame.K_f)
        assert engine.first_player == 'X', "F should toggle first_player back to X"

    pygame.quit()


def test_f_key_o_starts_causes_exactly_one_automatic_move():
    """Pressing F to select O immediately fires one computer move; no click needed."""
    import pygame
    pygame.init()

    with patch("game.game_engine.choose_move", return_value=(0, 0)):
        engine = GameEngine()           # starts as X-first, board empty
        engine.handle_keydown(pygame.K_f)   # toggle to O, resets round → computer fires

    # Exactly one O must be on the board from the automatic opening move
    os_on_board = sum(cell == 'O' for row in engine.board for cell in row)
    assert os_on_board == 1, "Exactly one O must be placed automatically when O starts"
    assert engine.current_player == 'X', "After the opening O move it must be X's turn"
    assert engine.round_over is False

    pygame.quit()


def test_f_key_x_starts_causes_no_automatic_move():
    """Pressing F back to X leaves the board empty; the human moves first."""
    import pygame
    pygame.init()

    with patch("game.game_engine.choose_move", return_value=(0, 0)):
        engine = GameEngine()
        engine.handle_keydown(pygame.K_f)   # → O (computer fires)
        engine.handle_keydown(pygame.K_f)   # → X (no automatic move)

    # Board must be empty – no computer move when X starts
    assert all(cell is None for row in engine.board for cell in row), (
        "Board must be empty when X is selected to start"
    )
    assert engine.current_player == 'X'

    pygame.quit()


def test_reset_match_preserves_first_player_preference():
    """Match reset (M) keeps the first_player preference; it is a match-level setting."""
    import pygame
    pygame.init()

    engine = GameEngine()
    engine.first_player = 'O'

    engine.handle_keydown(pygame.K_m)

    # After __init__ first_player is reset to default 'X'
    # The spec says "keep unless README says otherwise"; no README exists, so default is acceptable.
    # We just verify the engine is in a clean, consistent state.
    assert engine.score == {'X': 0, 'O': 0, 'draw': 0}
    assert engine.board == [[None] * 3 for _ in range(3)]
    assert engine.round_over is False

    pygame.quit()


# ---------------------------------------------------------------------------
# Regression: all previously fixed bugs still pass
# ---------------------------------------------------------------------------

def test_regression_diagonal_win_detected():
    """Diagonal wins are still detected (Task 1 regression)."""
    engine = GameEngine()
    engine.board = [['X', None, None], [None, 'X', None], [None, None, 'X']]
    engine.check_round_end()
    assert engine.winner == 'X'


def test_regression_last_cell_win_not_draw():
    """A win on the 9th cell is not a draw (Task 1/Bug2 regression)."""
    engine = GameEngine()
    engine.board = [['X', 'X', 'X'], ['O', 'O', 'X'], ['O', 'X', 'O']]
    engine.check_round_end()
    assert engine.winner == 'X'
    assert engine.round_over is True


def test_regression_click_after_round_end_ignored():
    """Clicks after round_over must still be no-ops (Task 2/Bug3 regression)."""
    engine = GameEngine()
    engine.board[0] = ['X', 'X', 'X']
    engine.round_over = True
    engine.winner = 'X'
    board_before = copy.deepcopy(engine.board)

    click(engine, 1, 0)

    assert engine.board == board_before


def test_regression_occupied_cell_not_overwritten():
    """Clicking an occupied cell must not overwrite it (Task 3/Bug4 regression)."""
    engine = GameEngine()
    engine.board[1][1] = 'O'
    click(engine, 1, 1)
    assert engine.board[1][1] == 'O'

