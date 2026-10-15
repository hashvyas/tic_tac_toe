"""
renderer: all pygame drawing lives here, kept separate from game logic.

Layout (400 × 540)
------------------
  y=  0 – 120   header strip
        y= 16     row 1 – turn label        (22pt, left-aligned)
        y= 52     row 2 – score | first:X   (16pt, left / right)
        y=115     thin separator line
  y=120 – 480   board  (360 × 360, 3 × 120-px cells)
  y=480 – 540   footer strip
                  result + key hints        (16pt, centred)
"""

import pygame

WIDTH, HEIGHT = 400, 540
BOARD_SIZE = 360
CELL_SIZE = BOARD_SIZE // 3
BOARD_TOP = 120
WINDOW_SIZE = (WIDTH, HEIGHT)

COLOR_BG     = (245, 245, 245)
COLOR_LINE   = (60,  60,  60)
COLOR_SEP    = (180, 180, 180)   # header separator
COLOR_X      = (200, 60,  60)
COLOR_O      = (60,  100, 200)
COLOR_TEXT   = (30,  30,  30)
COLOR_HINT   = (110, 110, 110)   # muted, for key hints
COLOR_RESULT = (180, 40,  40)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_small_fonts: dict = {}   # cache by size so we don't recreate every frame


def _small(size: int = 16) -> pygame.font.Font:
    if size not in _small_fonts:
        _small_fonts[size] = pygame.font.SysFont("consolas", size)
    return _small_fonts[size]


# ---------------------------------------------------------------------------
# Public drawing functions
# ---------------------------------------------------------------------------

def board_pos_to_cell(pos):
    x, y = pos
    y -= BOARD_TOP
    if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
        return None
    col = x // CELL_SIZE
    row = y // CELL_SIZE
    return int(row), int(col)


def draw_board(surface, board):
    surface.fill(COLOR_BG)

    # Thin separator between header and board
    pygame.draw.line(surface, COLOR_SEP, (0, BOARD_TOP - 5), (WIDTH, BOARD_TOP - 5), 1)

    # Grid lines
    for i in range(1, 3):
        pygame.draw.line(surface, COLOR_LINE,
                         (i * CELL_SIZE, BOARD_TOP),
                         (i * CELL_SIZE, BOARD_TOP + BOARD_SIZE), 3)
        pygame.draw.line(surface, COLOR_LINE,
                         (0, BOARD_TOP + i * CELL_SIZE),
                         (BOARD_SIZE, BOARD_TOP + i * CELL_SIZE), 3)

    # Symbols
    for r in range(3):
        for c in range(3):
            symbol = board[r][c]
            if symbol is None:
                continue
            center = (c * CELL_SIZE + CELL_SIZE // 2,
                      BOARD_TOP + r * CELL_SIZE + CELL_SIZE // 2)
            if symbol == 'X':
                offset = CELL_SIZE // 3
                pygame.draw.line(surface, COLOR_X,
                                 (center[0]-offset, center[1]-offset),
                                 (center[0]+offset, center[1]+offset), 6)
                pygame.draw.line(surface, COLOR_X,
                                 (center[0]+offset, center[1]-offset),
                                 (center[0]-offset, center[1]+offset), 6)
            else:
                pygame.draw.circle(surface, COLOR_O, center, CELL_SIZE // 3, 6)


def draw_text(surface, font, text, pos, color=COLOR_TEXT):
    surface.blit(font.render(text, True, color), pos)


def draw_header(surface, font, turn_label, score, first_player):
    """
    Render two clean rows in the 120px header strip.

    Row 1 (y=16): turn label in the main font.
    Row 2 (y=52): score left, first-player hint right, both in small muted font.
    """
    # Row 1 – turn label
    surface.blit(font.render(turn_label, True, COLOR_TEXT), (12, 16))

    sf = _small()

    # Row 2 left – scoreboard
    score_text = f"X: {score['X']}   Draw: {score['draw']}   O: {score['O']}"
    surface.blit(sf.render(score_text, True, COLOR_HINT), (12, 52))

    # Row 2 right – first-player toggle hint
    fp_text = f"First: {first_player}  [F]"
    fp_surf = sf.render(fp_text, True, COLOR_HINT)
    surface.blit(fp_surf, (WIDTH - fp_surf.get_width() - 12, 52))


def draw_banner(surface, font, result_text):
    """
    Render the round result and key hints in the 60px footer strip.

    Two lines vertically centred in the strip:
      • result text  – main font, red
      • key hints    – small font, muted
    """
    board_bottom = BOARD_TOP + BOARD_SIZE   # y = 480
    footer_mid = (board_bottom + HEIGHT) // 2   # y = 510

    # Result line
    r_surf = font.render(result_text, True, COLOR_RESULT)
    r_rect = r_surf.get_rect(centerx=WIDTH // 2, centery=footer_mid - 13)
    surface.blit(r_surf, r_rect)

    # Key-hint line
    h_surf = _small().render("R: new round    M: reset match", True, COLOR_HINT)
    h_rect = h_surf.get_rect(centerx=WIDTH // 2, centery=footer_mid + 13)
    surface.blit(h_surf, h_rect)


# ---------------------------------------------------------------------------
# Backward-compatible wrappers (kept so existing tests/callers don't break)
# ---------------------------------------------------------------------------

def draw_scoreboard(surface, font, score):
    sf = _small()
    text = f"X: {score['X']}   Draw: {score['draw']}   O: {score['O']}"
    surf = sf.render(text, True, COLOR_HINT)
    surface.blit(surf, (12, 52))


def draw_controls(surface, font, first_player):
    sf = _small()
    text = f"First: {first_player}  [F]"
    surf = sf.render(text, True, COLOR_HINT)
    surface.blit(surf, (WIDTH - surf.get_width() - 12, 52))
