# Tic-Tac-Toe

A single-player Tic-Tac-Toe game built with Python and pygame.  
You play as **X**; the computer plays as **O**.

---

## Requirements

- Python 3.10+
- pygame (`pip install pygame`)

---

## Running the game

```bash
python main.py
```

---

## How to play

| Action | Control |
|---|---|
| Place your symbol | Click any empty cell |
| New round (keep score) | Press **R** |
| Reset entire match (clear score) | Press **M** |
| Toggle who moves first | Press **F** |

### First-player selection

- Default: **X** moves first (you click first).
- Press **F** to switch to **O** first. The computer immediately places one O automatically — no click needed.
- Press **F** again to switch back to **X** first.
- The preference takes effect right away and is preserved across rounds until you reset the match.

---

## Project structure

```
tic-tac-toe/
├── main.py               # Entry point – pygame event loop
├── requirements.txt
├── game/
│   ├── __init__.py
│   ├── game_engine.py    # Board state, turn logic, round/match control
│   ├── rules.py          # Win and draw detection
│   ├── ai.py             # Random-move computer opponent
│   └── renderer.py       # All pygame drawing (board, header, footer)
└── tests/
    ├── test_rules.py       # 17 tests – win/draw detection
    └── test_game_engine.py # 28 tests – engine behaviour
```

---

## UI layout

```
┌─────────────────────────────────────┐  ← 400 × 540 window
│  Your turn (X)           [22pt]     │  y=16  turn label
│  X: 0   Draw: 0   O: 0  First:X[F] │  y=52  score + first-player hint (muted)
├─────────────────────────────────────┤  y=115 separator
│                                     │
│         3 × 3 board                 │  y=120–480  (360 × 360, cells 120×120)
│                                     │
├─────────────────────────────────────┤  y=480
│         X wins!                     │  footer – result (only when round over)
│   R: new round    M: reset match    │  footer – key hints (muted)
└─────────────────────────────────────┘  y=540
```

---

## Bugs fixed

### Bug 1 – Diagonal wins not detected (`game/rules.py`)

`check_winner()` checked rows and columns but skipped both diagonals.  
**Fix:** appended the two diagonal lines to the `lines` list before the winner loop.

### Bug 2 – Win on the last cell reported as a draw (`game/game_engine.py`)

`check_round_end()` called `is_board_full()` before `check_winner()`.  
When the final move completed a winning row, the board-full check fired first and set `winner = None` (draw).  
**Fix:** check for a winner first; only fall through to the draw check if no winner exists.

### Bug 3 – Clicks accepted after the round ended (`game/game_engine.py`)

`handle_click()` had no guard for `self.round_over`.  
After a win or draw, clicking an empty cell could still place a symbol.  
**Fix:** added `if self.round_over: return` as the first check in `handle_click()`.

### Bug 4 – Clicking an occupied cell overwrote its symbol (`game/game_engine.py`)

`handle_click()` wrote `self.current_player` to the board without checking whether the cell was already occupied.  
**Fix:** added `if self.board[row][col] is not None: return` before the write.

### Bug 5 – Computer did not make opening move when switching first player with F (`game/game_engine.py`)

Pressing `F` toggled `first_player` to `O`, but only mutated the state and did not trigger a new round or the opening AI move. The computer only moved after the human clicked.  
**Fix:** updated the `F` key handler to call `self._reset_round()`, which immediately sets up the round and triggers `self._maybe_take_computer_turn()`.

---

## Features implemented

### Scoreboard (Task 2)

- Tracks **X wins**, **O wins**, and **draws** across rounds within a match.
- Score is displayed in the header at all times.
- `check_round_end()` increments the correct counter exactly once per round (guarded by the `round_over` flag to prevent double-counting).
- Pressing **R** resets the board but **preserves** the score.
- Pressing **M** resets the board **and** zeroes the score.

### First-player choice + separate restart controls (Task 4)

- **F** – toggle which player moves first (`'X'` or `'O'`).  
  Immediately restarts the current round with the new setting.  
  When O is selected, the computer places its opening move automatically — no human click required.
- **R** – restart the current round; score is preserved.
- **M** – reset the entire match; board and score are both zeroed.
- `first_player` lives on the engine and survives round resets (`_reset_round()`).  
  A full match reset (`__init__()`) restores the default (`'X'`).

### UI Decluttering & Layout Redesign

- **Window dimensions increased:** expanded from `400×500` to `400×540` and moved `BOARD_TOP` from `100` to `120` to give the header and footer room to breathe.
- **Header hierarchy:**
  - Row 1: prominent turn status (`Your turn (X)` / `Computer's turn (O)`) in 22pt font.
  - Row 2: scoreboard and first-player toggle hint in a smaller, muted 16pt font.
  - Added a clean visual divider separating the header strip from the game grid.
- **Footer layout:** round result banners and control keys are cleanly separated into two vertically aligned lines, avoiding text collisions and horizontal clamping issues.

---

## Architecture notes

| Concern | Where it lives |
|---|---|
| Board state, turns, round/match lifecycle | `GameEngine` in `game_engine.py` |
| Win / draw detection | `check_winner()`, `is_board_full()` in `rules.py` |
| Computer move selection | `choose_move()` in `ai.py` (random empty cell) |
| All pygame rendering | `renderer.py` — no game logic here |
| Event loop | `main.py` — thin; only dispatches events to the engine |

**Key engine methods:**

| Method | Purpose |
|---|---|
| `_reset_round()` | Clears board/turn/winner; fires computer's opening move if O starts |
| `check_round_end()` | Checks winner then full-board draw; increments score once |
| `handle_click(pos)` | Places X on a valid empty cell, then triggers the computer's reply |
| `handle_keydown(key)` | Dispatches R / M / F key actions |
| `_maybe_take_computer_turn()` | Fires one AI move when it is O's turn; no-op otherwise |

---

## Tests

```
tests/test_rules.py       – 17 tests
tests/test_game_engine.py – 28 tests
                            ──────
                            45 total  (all passing)
```

Run with:

```bash
python -m pytest tests/ -v
```

### What is covered

**`test_rules.py`**
- Row wins (all three rows, both symbols)
- Column wins (all three columns, both symbols)
- Diagonal wins – top-left→bottom-right and top-right→bottom-left (both symbols)
- No-winner states: empty board, mid-game, full-board draw
- `is_board_full()` true and false cases

**`test_game_engine.py`**
- Post-round clicks ignored (win, draw, loss)
- Normal gameplay: empty cell accepts a symbol
- Win on the last cell is a win, not a draw
- Occupied cell is not overwritten; turn does not advance
- R resets board/turn/winner while preserving score
- M resets board and zeroes score
- Scoreboard: X win, O win, draw each increment only the right counter
- Score accumulates correctly across multiple rounds
- Double-call of `check_round_end()` does not double-count
- F toggles `first_player` and restarts the round immediately
- F → O: exactly one automatic computer move, then X's turn
- F → X: board remains empty, human moves first
- O starts via R: computer fires one opening move
- Regression suite: all four bugs verified fixed
