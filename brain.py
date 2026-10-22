#!/usr/bin/env python3
"""Mag-Nif's The Brain puzzle for the terminal.

The Brain is a round stack of rotating discs with flaps around its edge,
shown here from above. Flap 1 is at 12 o'clock and the rest follow clockwise.
A state is an int where bit k-1 is set when flap k is pulled out.

Rules:
  - Flap 1 can always be pulled out or pushed in.
  - Flap k > 1 can move only when flap k-1 is out and every flap below
    k-1 is in.

Every flap starts in and the goal is to pull them all out (170 moves for 8
flaps). With --reverse, every flap starts out and the goal is to push them
all in.
"""

import argparse
import curses
import math

MIN_FLAPS = 1
MAX_FLAPS = 9  # so number keys 1-9 can reach every flap
DEFAULT_FLAPS = 8


def can_toggle(state, flap):
    if flap == 1:
        return True
    neighbor_out = (state >> (flap - 2)) & 1
    flaps_below_neighbor = state & ((1 << (flap - 2)) - 1)
    return bool(neighbor_out) and flaps_below_neighbor == 0


def toggle(state, flap):
    return state ^ (1 << (flap - 1))


def rank_of(state):
    # The shortest path between all-in and all-out walks the binary-reflected
    # Gray code, so a state's position on that path is its Gray code converted
    # back to binary. All-in is rank 0.
    rank = 0
    while state:
        rank ^= state
        state >>= 1
    return rank


def state_at(rank):
    return rank ^ (rank >> 1)


def moves_left(state, goal):
    return abs(rank_of(state) - rank_of(goal))


def hint(state, goal):
    """Return the flap to move next on the shortest path, or None if solved."""
    rank, goal_rank = rank_of(state), rank_of(goal)
    if rank == goal_rank:
        return None
    next_rank = rank - 1 if rank > goal_rank else rank + 1
    return (state ^ state_at(next_rank)).bit_length()


def blocked_reason(state, flap):
    if not (state >> (flap - 2)) & 1:
        return f"Flap {flap} is stuck: flap {flap - 1} must be out."
    return f"Flap {flap} is stuck: every flap below {flap - 1} must be in."


class Game:
    def __init__(self, flap_count, goal_out=True):
        self.flap_count = flap_count
        self.goal_out = goal_out
        self.reset()

    @property
    def all_out(self):
        return (1 << self.flap_count) - 1

    @property
    def start(self):
        return 0 if self.goal_out else self.all_out

    @property
    def goal(self):
        return self.all_out if self.goal_out else 0

    @property
    def objective(self):
        return "Pull every flap out." if self.goal_out else "Push every flap in."

    @property
    def best_total(self):
        return moves_left(self.start, self.goal)

    def reset(self):
        self.state = self.start
        self.history = []
        self.cursor = 1
        self.message = self.objective

    def move(self, flap):
        if not can_toggle(self.state, flap):
            self.message = blocked_reason(self.state, flap)
            return
        self.history.append(self.state)
        self.state = toggle(self.state, flap)
        if (self.state >> (flap - 1)) & 1:
            self.message = f"Pulled flap {flap} out."
        else:
            self.message = f"Pushed flap {flap} in."
        if self.state == self.goal:
            moves = len(self.history)
            if moves == self.best_total:
                self.message = f"Solved in {moves} moves. That's optimal!"
            else:
                self.message = f"Solved in {moves} moves (best is {self.best_total})."

    def undo(self):
        if not self.history:
            self.message = "Nothing to undo."
            return
        self.state = self.history.pop()
        self.message = "Undid last move."

    def show_hint(self):
        flap = hint(self.state, self.goal)
        if flap is None:
            self.message = "Already solved."
        else:
            self.message = f"Hint: move flap {flap}."


HELP_LINES = [
    "1-9 move that flap   ←/→ select   space move   h hint   u undo",
    "↑ new game: pull all out   ↓ new game: push all in   r restart",
    "+/- flaps   q quit",
]

# One color per flap: red, orange, yellow, green, cyan, blue, purple, pink, tan.
FLAP_COLORS_256 = [196, 208, 226, 46, 51, 33, 129, 201, 180]
FLAP_COLORS_8 = [
    curses.COLOR_RED,
    curses.COLOR_YELLOW,
    curses.COLOR_GREEN,
    curses.COLOR_CYAN,
    curses.COLOR_BLUE,
    curses.COLOR_MAGENTA,
    curses.COLOR_WHITE,
]

# The dial, seen from above. Terminal cells are about twice as tall as they
# are wide, so x distances are doubled to keep the circle round.
DIAL_RADIUS = 5
DIAL_X_SCALE = 2.0
DIAL_LABEL_RADIUS = 3.0
FLAP_LENGTH = 1.2
FLAP_TRAVEL = 2.0
ANIMATION_FRAMES = 6
ANIMATION_FRAME_MS = 35


def draw(screen, game, flap_colors, flap_extents=None):
    screen.erase()
    left = 2

    goal_word = "out" if game.goal_out else "in"
    title = f"The Brain · {game.flap_count} flaps · goal: all {goal_word}"
    stats = (
        f"moves: {len(game.history)}   "
        f"optimal from here: {moves_left(game.state, game.goal)}   "
        f"best total: {game.best_total}"
    )
    screen.addstr(1, left, title, curses.A_BOLD)
    screen.addstr(2, left, stats)

    next_row = draw_dial(screen, game, flap_colors, left, flap_extents or {})

    screen.addstr(next_row + 1, left, game.message)
    for offset, line in enumerate(HELP_LINES):
        screen.addstr(next_row + 3 + offset, left, line, curses.A_DIM)
    screen.refresh()


def dial_cell(center_row, center_col, radius, angle):
    row = center_row + round(radius * math.sin(angle))
    col = center_col + round(radius * math.cos(angle) * DIAL_X_SCALE)
    return row, col


def draw_dial(screen, game, flap_colors, left, flap_extents):
    """Draw the dial and its flaps on rows 3-17; return the next free row.

    A flap's extent runs from 0 (pushed in, sitting across the rim) to 1
    (pulled out past the rim); flap_extents overrides it for flaps being
    animated.
    """
    center_row = 10
    center_col = left + round((DIAL_RADIUS + FLAP_TRAVEL + 1) * DIAL_X_SCALE)

    for degrees in range(0, 360, 2):
        row, col = dial_cell(center_row, center_col, DIAL_RADIUS, math.radians(degrees))
        screen.addstr(row, col, "·", curses.A_DIM)

    for flap in range(1, game.flap_count + 1):
        angle = math.radians(-90 + (flap - 1) * 360 / game.flap_count)
        color = flap_colors[(flap - 1) % len(flap_colors)] | curses.A_BOLD
        extent = flap_extents.get(flap, (game.state >> (flap - 1)) & 1)
        inner = DIAL_RADIUS - FLAP_LENGTH + FLAP_TRAVEL * extent

        # Sample along the flap finely so it has no gaps at any angle
        radius = inner
        while radius <= inner + FLAP_LENGTH:
            row, col = dial_cell(center_row, center_col, radius, angle)
            screen.addstr(row, col, "█", color)
            if abs(math.cos(angle)) < 0.3:
                # Up/down flaps are two cells wide to look as thick as the others
                screen.addstr(row, col + 1, "█", color)
            radius += 0.1

        row, col = dial_cell(center_row, center_col, DIAL_LABEL_RADIUS, angle)
        label_attr = color | curses.A_REVERSE if flap == game.cursor else color
        screen.addstr(row, col, str(flap), label_attr)

    return center_row + 8


def animate_flap(screen, game, flap_colors, flap):
    start = (game.state >> (flap - 1)) & 1
    for frame in range(1, ANIMATION_FRAMES):
        extent = start + (1 - 2 * start) * frame / ANIMATION_FRAMES
        try:
            draw(screen, game, flap_colors, {flap: extent})
        except curses.error:
            return
        curses.napms(ANIMATION_FRAME_MS)


def move(screen, game, flap_colors):
    if can_toggle(game.state, game.cursor):
        animate_flap(screen, game, flap_colors, game.cursor)
    game.move(game.cursor)


def run(screen, flap_count, goal_out):
    curses.curs_set(0)
    flap_colors = [0]
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        palette = FLAP_COLORS_256 if curses.COLORS >= 256 else FLAP_COLORS_8
        for pair, color in enumerate(palette, start=1):
            curses.init_pair(pair, color, -1)
        flap_colors = [curses.color_pair(pair) for pair in range(1, len(palette) + 1)]

    game = Game(flap_count, goal_out)
    while True:
        try:
            draw(screen, game, flap_colors)
        except curses.error:
            screen.erase()
            screen.addstr(0, 0, "Window too small. Resize or press q.")
            screen.refresh()

        key = screen.getch()
        if key in (ord("q"), ord("Q")):
            return
        elif key in (curses.KEY_LEFT, ord("a")):
            game.cursor = max(game.cursor - 1, 1)
        elif key in (curses.KEY_RIGHT, ord("d")):
            game.cursor = min(game.cursor + 1, game.flap_count)
        elif key in (ord(" "), ord("\n"), curses.KEY_ENTER):
            move(screen, game, flap_colors)
        elif ord("1") <= key <= ord("9") and key - ord("0") <= game.flap_count:
            game.cursor = key - ord("0")
            move(screen, game, flap_colors)
        elif key == ord("h"):
            game.show_hint()
        elif key == ord("u"):
            game.undo()
        elif key == ord("r"):
            game.reset()
        elif key in (curses.KEY_UP, ord("w")) and not game.goal_out:
            game = Game(game.flap_count, goal_out=True)
        elif key in (curses.KEY_DOWN, ord("s")) and game.goal_out:
            game = Game(game.flap_count, goal_out=False)
        elif key in (ord("+"), ord("=")) and game.flap_count < MAX_FLAPS:
            game = Game(game.flap_count + 1, game.goal_out)
        elif key in (ord("-"), ord("_")) and game.flap_count > MIN_FLAPS:
            game = Game(game.flap_count - 1, game.goal_out)


def main():
    parser = argparse.ArgumentParser(description="Play Mag-Nif's The Brain puzzle.")
    parser.add_argument(
        "flaps",
        nargs="?",
        type=int,
        default=DEFAULT_FLAPS,
        help=f"number of flaps ({MIN_FLAPS}-{MAX_FLAPS}, default {DEFAULT_FLAPS})",
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="start with every flap out and push them all in",
    )
    args = parser.parse_args()
    if not MIN_FLAPS <= args.flaps <= MAX_FLAPS:
        parser.error(f"flaps must be between {MIN_FLAPS} and {MAX_FLAPS}")
    curses.wrapper(run, args.flaps, not args.reverse)


if __name__ == "__main__":
    main()
