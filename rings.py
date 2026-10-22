#!/usr/bin/env python3
"""Chinese rings (Baguenaudier) puzzle for the terminal.

Rings are numbered from the free end of the bar: ring 1 is on the right.
A state is an int where bit k-1 is set when ring k is on the bar.

Rules:
  - Ring 1 can always be moved on or off.
  - Ring k > 1 can be moved only when ring k-1 is on the bar
    and every ring below k-1 is off.

The goal is to take every ring off the bar.
"""

import argparse
import curses

MIN_RINGS = 1
MAX_RINGS = 9  # so number keys 1-9 can reach every ring
COLUMN_WIDTH = 5


def can_toggle(state, ring):
    if ring == 1:
        return True
    neighbor_on = (state >> (ring - 2)) & 1
    rings_below_neighbor = state & ((1 << (ring - 2)) - 1)
    return bool(neighbor_on) and rings_below_neighbor == 0


def toggle(state, ring):
    return state ^ (1 << (ring - 1))


def moves_left(state):
    # The solved path walks the binary-reflected Gray code down to 0, so a
    # state's distance from solved is its Gray code converted back to binary.
    rank = 0
    while state:
        rank ^= state
        state >>= 1
    return rank


def hint(state):
    """Return the ring to move next on the shortest path, or None if solved."""
    rank = moves_left(state)
    if rank == 0:
        return None
    next_state = (rank - 1) ^ ((rank - 1) >> 1)
    return (state ^ next_state).bit_length()


def blocked_reason(state, ring):
    if not (state >> (ring - 2)) & 1:
        return f"Ring {ring} is stuck: ring {ring - 1} must be on the bar."
    return f"Ring {ring} is stuck: every ring below {ring - 1} must be off."


class Game:
    def __init__(self, ring_count):
        self.ring_count = ring_count
        self.reset()

    def reset(self):
        self.state = (1 << self.ring_count) - 1
        self.history = []
        self.cursor = 1
        self.hinted_ring = None
        self.message = "Take every ring off the bar."

    @property
    def best_total(self):
        return moves_left((1 << self.ring_count) - 1)

    def move(self, ring):
        self.hinted_ring = None
        if not can_toggle(self.state, ring):
            self.message = blocked_reason(self.state, ring)
            return
        self.history.append(self.state)
        self.state = toggle(self.state, ring)
        direction = "on" if (self.state >> (ring - 1)) & 1 else "off"
        self.message = f"Moved ring {ring} {direction}."
        if self.state == 0:
            moves = len(self.history)
            if moves == self.best_total:
                self.message = f"Solved in {moves} moves. That's optimal!"
            else:
                self.message = f"Solved in {moves} moves (best is {self.best_total})."

    def undo(self):
        self.hinted_ring = None
        if not self.history:
            self.message = "Nothing to undo."
            return
        self.state = self.history.pop()
        self.message = "Undid last move."

    def show_hint(self):
        self.hinted_ring = hint(self.state)
        if self.hinted_ring is None:
            self.message = "Already solved."
        else:
            self.message = f"Hint: move ring {self.hinted_ring}."


HELP = "1-9 move that ring   ←/→ select   space move   h hint   u undo   r restart   +/- rings   q quit"


def draw(screen, game, colors):
    screen.erase()
    rings = range(game.ring_count, 0, -1)
    left = 2

    title = f"Chinese Rings · {game.ring_count} rings"
    stats = (
        f"moves: {len(game.history)}   "
        f"optimal from here: {moves_left(game.state)}   "
        f"best total: {game.best_total}"
    )
    screen.addstr(1, left, title, curses.A_BOLD)
    screen.addstr(2, left, stats)

    for column, ring in enumerate(rings):
        x = left + column * COLUMN_WIDTH
        is_on = (game.state >> (ring - 1)) & 1

        if ring == game.hinted_ring:
            label_attr = colors["hint"] | curses.A_BOLD
        elif can_toggle(game.state, ring):
            label_attr = colors["legal"] | curses.A_BOLD
        else:
            label_attr = curses.A_DIM
        screen.addstr(4, x, f"{ring:^{COLUMN_WIDTH}}", label_attr)

        bar = "═(O)═" if is_on else "═════"
        screen.addstr(5, x, bar, colors["ring"] if is_on else 0)
        screen.addstr(6, x, "     " if is_on else " (O) ", curses.A_DIM)

        if ring == game.cursor:
            screen.addstr(7, x, f"{'^':^{COLUMN_WIDTH}}", curses.A_BOLD)

    bar_end = left + game.ring_count * COLUMN_WIDTH
    screen.addstr(5, bar_end, "═▶")

    screen.addstr(9, left, game.message)
    screen.addstr(11, left, "green = can move now", colors["legal"])
    screen.addstr(12, left, HELP, curses.A_DIM)
    screen.refresh()


def run(screen, ring_count):
    curses.curs_set(0)
    colors = {"legal": 0, "hint": 0, "ring": 0}
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_YELLOW, -1)
        curses.init_pair(3, curses.COLOR_CYAN, -1)
        colors = {
            "legal": curses.color_pair(1),
            "hint": curses.color_pair(2),
            "ring": curses.color_pair(3),
        }

    game = Game(ring_count)
    while True:
        try:
            draw(screen, game, colors)
        except curses.error:
            screen.erase()
            screen.addstr(0, 0, "Window too small. Resize or press q.")
            screen.refresh()

        key = screen.getch()
        if key in (ord("q"), ord("Q")):
            return
        elif key in (curses.KEY_LEFT, ord("a")):
            game.cursor = min(game.cursor + 1, game.ring_count)
        elif key in (curses.KEY_RIGHT, ord("d")):
            game.cursor = max(game.cursor - 1, 1)
        elif key in (ord(" "), ord("\n"), curses.KEY_ENTER):
            game.move(game.cursor)
        elif ord("1") <= key <= ord("9") and key - ord("0") <= game.ring_count:
            game.cursor = key - ord("0")
            game.move(game.cursor)
        elif key == ord("h"):
            game.show_hint()
        elif key == ord("u"):
            game.undo()
        elif key == ord("r"):
            game.reset()
        elif key in (ord("+"), ord("=")) and game.ring_count < MAX_RINGS:
            game = Game(game.ring_count + 1)
        elif key in (ord("-"), ord("_")) and game.ring_count > MIN_RINGS:
            game = Game(game.ring_count - 1)


def main():
    parser = argparse.ArgumentParser(description="Play the Chinese rings puzzle.")
    parser.add_argument(
        "rings",
        nargs="?",
        type=int,
        default=5,
        help=f"number of rings ({MIN_RINGS}-{MAX_RINGS}, default 5)",
    )
    args = parser.parse_args()
    if not MIN_RINGS <= args.rings <= MAX_RINGS:
        parser.error(f"rings must be between {MIN_RINGS} and {MAX_RINGS}")
    curses.wrapper(run, args.rings)


if __name__ == "__main__":
    main()
