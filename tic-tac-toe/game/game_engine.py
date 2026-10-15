"""
GameEngine: owns the board, turn state, and round-end logic.

You (the player) always play X and click to move. The computer always
plays O and moves automatically right after you, using a simple
random-move AI (see game/ai.py) - this is given infrastructure, not
something you need to build.

Starter version: no scoreboard yet, no first-player choice, and only
one combined reset control. Win/draw detection has known bugs (see
game/rules.py and check_round_end below) that Task 1 asks you to fix,
and move validation has a known gap (see handle_click) that Task 3
asks you to fix.
"""

from game.rules import check_winner, is_board_full
from game.renderer import board_pos_to_cell
from game.ai import choose_move

HUMAN_SYMBOL = 'X'
COMPUTER_SYMBOL = 'O'


class GameEngine:
    def __init__(self):
        self.score = {'X': 0, 'O': 0, 'draw': 0}
        self._reset_round()

    def _reset_round(self):
        """Reset only the per-round state; score is preserved."""
        self.board = [[None] * 3 for _ in range(3)]
        self.current_player = 'X'
        self.round_over = False
        self.winner = None   # 'X', 'O', or None (meaning draw, only valid when round_over)

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
        renderer.draw_text(surface, font, turn_label, (10, 20))
        renderer.draw_scoreboard(surface, font, self.score)

        if self.round_over:
            text = f"{self.winner} wins!" if self.winner else "Draw!"
            renderer.draw_banner(surface, font, f"{text} Press R for a new round.")

