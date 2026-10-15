"""
Tests for game/rules.py – check_winner and is_board_full.
"""

import pytest
from game.rules import check_winner, is_board_full

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def board_from(rows):
    """Accept a list of 3 strings like ['XOX', 'OXO', 'XOX'] for readability."""
    mapping = {"X": "X", "O": "O", ".": None}
    return [[mapping[ch] for ch in row] for row in rows]


# ---------------------------------------------------------------------------
# Row wins (existing behaviour – must keep passing)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rows, expected", [
    (["XXX", "O.O", "..."], "X"),   # top row
    (["O.O", "XXX", "..."], "X"),   # middle row
    (["O.O", "...", "XXX"], "X"),   # bottom row
    (["OOO", "X.X", "..."], "O"),   # top row O
])
def test_row_wins(rows, expected):
    assert check_winner(board_from(rows)) == expected


# ---------------------------------------------------------------------------
# Column wins (existing behaviour – must keep passing)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rows, expected", [
    (["XO.", "XO.", "X.."], "X"),   # left column
    (["OX.", "OX.", ".X."], "X"),   # middle column
    (["O.X", "O.X", "..X"], "X"),   # right column
    (["OX.", "OX.", "OX."], "O"),   # left column O
])
def test_column_wins(rows, expected):
    assert check_winner(board_from(rows)) == expected


# ---------------------------------------------------------------------------
# Diagonal wins (new behaviour being fixed)
# ---------------------------------------------------------------------------

def test_diagonal_top_left_to_bottom_right_X():
    b = board_from(["X..", ".X.", "..X"])
    assert check_winner(b) == "X"

def test_diagonal_top_left_to_bottom_right_O():
    b = board_from(["O..", ".O.", "..O"])
    assert check_winner(b) == "O"

def test_diagonal_top_right_to_bottom_left_X():
    b = board_from(["..X", ".X.", "X.."])
    assert check_winner(b) == "X"

def test_diagonal_top_right_to_bottom_left_O():
    b = board_from(["..O", ".O.", "O.."])
    assert check_winner(b) == "O"


# ---------------------------------------------------------------------------
# No winner
# ---------------------------------------------------------------------------

def test_no_winner_empty_board():
    b = board_from(["...", "...", "..."])
    assert check_winner(b) is None

def test_no_winner_mid_game():
    b = board_from(["XO.", "OX.", "..."])
    assert check_winner(b) is None

def test_no_winner_full_draw():
    # Classic drawn board – no three-in-a-row in any direction
    b = board_from(["XOX", "OXO", "OXO"])
    assert check_winner(b) is None


# ---------------------------------------------------------------------------
# is_board_full (unchanged helper – sanity check)
# ---------------------------------------------------------------------------

def test_board_full():
    b = board_from(["XOX", "OXO", "OXO"])
    assert is_board_full(b) is True

def test_board_not_full():
    b = board_from(["XO.", "OXO", "OXO"])
    assert is_board_full(b) is False
