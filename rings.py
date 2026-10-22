#!/usr/bin/env python3
"""Chinese rings (Baguenaudier) puzzle for the terminal.

Rings are numbered from the free end of the bar: ring 1 is on the left.
A state is an int where bit k-1 is set when ring k is on the bar.

Rules:
  - Ring 1 can always be moved on or off.
  - Ring k > 1 can be moved only when ring k-1 is on the bar
    and every ring below k-1 is off.

The goal is to take every ring off the bar, or with --on to put every
ring on the bar starting from all off.
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


def rank_of(state):
    # The shortest path between all-off and all-on walks the binary-reflected
    # Gray code, so a state's position on that path is its Gray code converted
    # back to binary. All-off is rank 0.
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
    """Return the ring to move next on the shortest path, or None if solved."""
    rank, goal_rank = rank_of(state), rank_of(goal)
    if rank == goal_rank:
        return None
    next_rank = rank - 1 if rank > goal_rank else rank + 1
    return (state ^ state_at(next_rank)).bit_length()


def blocked_reason(state, ring):
    if not (state >> (ring - 2)) & 1:
        return f"Ring {ring} is stuck: ring {ring - 1} must be on the bar."
    return f"Ring {ring} is stuck: every ring below {ring - 1} must be off."


class Game:
    def __init__(self, ring_count, goal_on=False):
        self.ring_count = ring_count
        self.goal_on = goal_on
        self.reset()

    @property
    def all_on(self):
        return (1 << self.ring_count) - 1

    @property
    def start(self):
        return 0 if self.goal_on else self.all_on

    @property
    def goal(self):
        return self.all_on if self.goal_on else 0

    @property
    def objective(self):
        return "Put every ring on the bar." if self.goal_on else "Take every ring off the bar."

    @property
    def best_total(self):
        return moves_left(self.start, self.goal)

    def reset(self):
        self.state = self.start
        self.history = []
        self.cursor = 1
        self.message = self.objective

    def move(self, ring):
        if not can_toggle(self.state, ring):
            self.message = blocked_reason(self.state, ring)
            return
        self.history.append(self.state)
        self.state = toggle(self.state, ring)
        direction = "on" if (self.state >> (ring - 1)) & 1 else "off"
        self.message = f"Moved ring {ring} {direction}."
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
        ring = hint(self.state, self.goal)
        if ring is None:
            self.message = "Already solved."
        else:
            self.message = f"Hint: move ring {ring}."


HELP_LINES = [
    "1-9 move that ring   ←/→ select   space move   h hint   u undo",
    "r restart   +/- rings   m switch goal (on/off)   q quit",
]

# One color per ring: red, orange, yellow, green, cyan, blue, purple, pink, tan.
RING_COLORS_256 = [196, 208, 226, 46, 51, 33, 129, 201, 180]
RING_COLORS_8 = [
    curses.COLOR_RED,
    curses.COLOR_YELLOW,
    curses.COLOR_GREEN,
    curses.COLOR_CYAN,
    curses.COLOR_BLUE,
    curses.COLOR_MAGENTA,
    curses.COLOR_WHITE,
]


def draw(screen, game, ring_colors):
    screen.erase()
    left = 2

    goal_word = "on" if game.goal_on else "off"
    title = f"Chinese Rings · {game.ring_count} rings · goal: all {goal_word}"
    stats = (
        f"moves: {len(game.history)}   "
        f"optimal from here: {moves_left(game.state, game.goal)}   "
        f"best total: {game.best_total}"
    )
    screen.addstr(1, left, title, curses.A_BOLD)
    screen.addstr(2, left, stats)

    screen.addstr(5, left, "◀═")
    for column, ring in enumerate(range(1, game.ring_count + 1)):
        x = left + 2 + column * COLUMN_WIDTH
        color = ring_colors[(ring - 1) % len(ring_colors)]
        is_on = (game.state >> (ring - 1)) & 1

        screen.addstr(4, x, f"{ring:^{COLUMN_WIDTH}}", color | curses.A_BOLD)
        if is_on:
            screen.addstr(5, x, "═")
            screen.addstr(5, x + 1, "(O)", color | curses.A_BOLD)
            screen.addstr(5, x + 4, "═")
        else:
            screen.addstr(5, x, "═════")
            screen.addstr(6, x + 1, "(O)", color)

        if ring == game.cursor:
            screen.addstr(7, x, f"{'^':^{COLUMN_WIDTH}}", curses.A_BOLD)

    screen.addstr(9, left, game.message)
    for offset, line in enumerate(HELP_LINES):
        screen.addstr(11 + offset, left, line, curses.A_DIM)
    screen.refresh()


def run(screen, ring_count, goal_on):
    curses.curs_set(0)
    ring_colors = [0]
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        palette = RING_COLORS_256 if curses.COLORS >= 256 else RING_COLORS_8
        for pair, color in enumerate(palette, start=1):
            curses.init_pair(pair, color, -1)
        ring_colors = [curses.color_pair(pair) for pair in range(1, len(palette) + 1)]

    game = Game(ring_count, goal_on)
    while True:
        try:
            draw(screen, game, ring_colors)
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
            game.cursor = min(game.cursor + 1, game.ring_count)
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
        elif key == ord("m"):
            game = Game(game.ring_count, not game.goal_on)
        elif key in (ord("+"), ord("=")) and game.ring_count < MAX_RINGS:
            game = Game(game.ring_count + 1, game.goal_on)
        elif key in (ord("-"), ord("_")) and game.ring_count > MIN_RINGS:
            game = Game(game.ring_count - 1, game.goal_on)


def main():
    parser = argparse.ArgumentParser(description="Play the Chinese rings puzzle.")
    parser.add_argument(
        "rings",
        nargs="?",
        type=int,
        default=5,
        help=f"number of rings ({MIN_RINGS}-{MAX_RINGS}, default 5)",
    )
    parser.add_argument(
        "--on",
        action="store_true",
        help="start with every ring off and put them all on",
    )
    args = parser.parse_args()
    if not MIN_RINGS <= args.rings <= MAX_RINGS:
        parser.error(f"rings must be between {MIN_RINGS} and {MAX_RINGS}")
    curses.wrapper(run, args.rings, args.on)


if __name__ == "__main__":
    main()
