"""
GameEngine: owns the board, turn state, and round-end logic.

You (the player) always play X and click to move. The computer always
plays O and moves automatically right after you, using a simple
random-move AI (see game/ai.py) - this is given infrastructure, not
something you need to build.

Controls
--------
  R  – restart current round (preserves scoreboard)
  M  – reset entire match   (clears scoreboard)
  F  – toggle which player moves first (takes effect on next round)
"""

from game.rules import check_winner, is_board_full
from game.renderer import board_pos_to_cell
from game.ai import choose_move

HUMAN_SYMBOL = 'X'
COMPUTER_SYMBOL = 'O'


class GameEngine:
    def __init__(self):
        self.score = {'X': 0, 'O': 0, 'draw': 0}
        self.first_player = HUMAN_SYMBOL   # 'X' or 'O'; preserved across rounds
        self._reset_round()

    def _reset_round(self):
        """Reset only the per-round state; score and first_player are preserved."""
        self.board = [[None] * 3 for _ in range(3)]
        self.current_player = self.first_player
        self.round_over = False
        self.winner = None   # 'X', 'O', or None (meaning draw, only valid when round_over)
        # If O starts, the computer makes the opening move immediately.
        self._maybe_take_computer_turn()

    def handle_click(self, pos):
        if self.round_over:
            return   # round finished – ignore all clicks until R is pressed
        if self.current_player != HUMAN_SYMBOL:
            return   # not your turn - the computer is about to move (or already has)
        cell = board_pos_to_cell(pos)
        if cell is None:
            return
        row, col = cell
        if self.board[row][col] is not None:
            return   # cell already occupied – ignore the click
        self.board[row][col] = self.current_player
        self.check_round_end()
        self.current_player = 'O' if self.current_player == 'X' else 'X'
        self._maybe_take_computer_turn()

    def _maybe_take_computer_turn(self):
        if self.round_over or self.current_player != COMPUTER_SYMBOL:
            return
        move = choose_move(self.board)
        if move is None:
            return
        row, col = move
        self.board[row][col] = self.current_player
        self.check_round_end()
        self.current_player = 'O' if self.current_player == 'X' else 'X'

    def handle_keydown(self, key):
        import pygame
        if key == pygame.K_r:
            self._reset_round()                 # new round – keep score
        elif key == pygame.K_m:
            self.__init__()                     # full match reset (clears score and board)
        elif key == pygame.K_f:
            # Toggle which player moves first and restart the round immediately
            # so the new setting takes effect without requiring another R press.
            # If O is now first, _reset_round() will call _maybe_take_computer_turn()
            # and fire exactly one opening move.
            self.first_player = (COMPUTER_SYMBOL
                                 if self.first_player == HUMAN_SYMBOL
                                 else HUMAN_SYMBOL)
            self._reset_round()

    def check_round_end(self):
        if self.round_over:
            return   # already settled – do not update scores again
        winner = check_winner(self.board)
        if winner:
            self.round_over = True
            self.winner = winner
            self.score[winner] += 1
            return
        if is_board_full(self.board):
            self.round_over = True
            self.winner = None   # draw
            self.score['draw'] += 1

    def draw(self, surface, font):
        from game import renderer
        renderer.draw_board(surface, self.board)
        turn_label = "Your turn (X)" if self.current_player == HUMAN_SYMBOL else "Computer's turn (O)"
        renderer.draw_header(surface, font, turn_label, self.score, self.first_player)

        if self.round_over:
            text = f"{self.winner} wins!" if self.winner else "Draw!"
            renderer.draw_banner(surface, font, text)

