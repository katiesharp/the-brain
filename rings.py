#!/usr/bin/env python3
"""Chinese rings (Baguenaudier) puzzle for the terminal.

Rings are numbered from the free end of the bar: ring 1 is on the left.
A state is an int where bit k-1 is set when ring k is on the bar.

Rules:
  - Ring 1 can always be moved on or off.
  - Ring k > 1 can be moved only when ring k-1 is on the bar
    and every ring below k-1 is off.

The goal is to take every ring off the bar, or with --reverse to put every
ring on the bar starting from all off.

With --brain it plays Mag-Nif's The Brain instead, seen from above: a round
dial with 8 flaps around its edge, starting all in, with the goal of pulling
every flap out. It follows the same rule, with "out" in place of "on" and
"in" in place of "off".
"""

import argparse
import curses
import math

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


# A set bit means the piece is "on" (a ring on the bar, a Brain flap pulled out).
THEMES = {
    "rings": {
        "title": "Chinese Rings",
        "piece": "ring",
        "on": "on",
        "off": "off",
        "moved_on": "Moved ring {} on.",
        "moved_off": "Moved ring {} off.",
        "must_be_on": "on the bar",
        "goal_on_text": "Put every ring on the bar.",
        "goal_off_text": "Take every ring off the bar.",
        "default_count": 5,
        "default_goal_on": False,
    },
    "brain": {
        "title": "The Brain",
        "piece": "flap",
        "on": "out",
        "off": "in",
        "moved_on": "Pulled flap {} out.",
        "moved_off": "Pushed flap {} in.",
        "must_be_on": "out",
        "goal_on_text": "Pull every flap out.",
        "goal_off_text": "Push every flap in.",
        "default_count": 8,
        "default_goal_on": True,
    },
}


def blocked_reason(state, ring, theme):
    piece = theme["piece"]
    if not (state >> (ring - 2)) & 1:
        return f"{piece.capitalize()} {ring} is stuck: {piece} {ring - 1} must be {theme['must_be_on']}."
    return f"{piece.capitalize()} {ring} is stuck: every {piece} below {ring - 1} must be {theme['off']}."


class Game:
    def __init__(self, ring_count, goal_on=False, theme=THEMES["rings"]):
        self.ring_count = ring_count
        self.goal_on = goal_on
        self.theme = theme
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
        return self.theme["goal_on_text"] if self.goal_on else self.theme["goal_off_text"]

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
            self.message = blocked_reason(self.state, ring, self.theme)
            return
        self.history.append(self.state)
        self.state = toggle(self.state, ring)
        moved = "moved_on" if (self.state >> (ring - 1)) & 1 else "moved_off"
        self.message = self.theme[moved].format(ring)
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
            self.message = f"Hint: move {self.theme['piece']} {ring}."


def help_lines(theme):
    return [
        f"1-9 move that {theme['piece']}   ←/→ select   space move   h hint   u undo",
        f"r restart   +/- {theme['piece']}s   m switch goal ({theme['on']}/{theme['off']})   q quit",
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


def draw(screen, game, ring_colors, flap_extents=None):
    screen.erase()
    left = 2
    theme = game.theme

    goal_word = theme["on"] if game.goal_on else theme["off"]
    title = f"{theme['title']} · {game.ring_count} {theme['piece']}s · goal: all {goal_word}"
    stats = (
        f"moves: {len(game.history)}   "
        f"optimal from here: {moves_left(game.state, game.goal)}   "
        f"best total: {game.best_total}"
    )
    screen.addstr(1, left, title, curses.A_BOLD)
    screen.addstr(2, left, stats)

    if theme is THEMES["brain"]:
        next_row = draw_brain(screen, game, ring_colors, left, flap_extents or {})
    else:
        next_row = draw_rings(screen, game, ring_colors, left)

    screen.addstr(next_row + 1, left, game.message)
    for offset, line in enumerate(help_lines(theme)):
        screen.addstr(next_row + 3 + offset, left, line, curses.A_DIM)
    screen.refresh()


def draw_cursor(screen, game, row, column_x):
    x = column_x(game.cursor)
    screen.addstr(row, x, f"{'^':^{COLUMN_WIDTH}}", curses.A_BOLD)


def draw_rings(screen, game, ring_colors, left):
    """Draw the bar and rings on rows 4-7; return the next free row."""
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

    draw_cursor(screen, game, 7, lambda ring: left + 2 + (ring - 1) * COLUMN_WIDTH)
    return 8


# The Brain's dial, seen from above. Terminal cells are about twice as tall
# as they are wide, so x distances are doubled to keep the circle round.
DIAL_RADIUS = 5
DIAL_X_SCALE = 2.0
DIAL_LABEL_RADIUS = 3.0
FLAP_LENGTH = 1.2
FLAP_TRAVEL = 2.0
ANIMATION_FRAMES = 6
ANIMATION_FRAME_MS = 35


def dial_cell(center_row, center_col, radius, angle):
    row = center_row + round(radius * math.sin(angle))
    col = center_col + round(radius * math.cos(angle) * DIAL_X_SCALE)
    return row, col


def draw_brain(screen, game, ring_colors, left, flap_extents):
    """Draw the dial and its flaps on rows 3-17; return the next free row.

    Flap 1 is at 12 o'clock and the rest follow clockwise. A flap's
    extent runs from 0 (pushed in, sitting across the rim) to 1 (pulled out
    past the rim); flap_extents overrides it for flaps being animated.
    """
    center_row = 10
    center_col = left + round((DIAL_RADIUS + FLAP_TRAVEL + 1) * DIAL_X_SCALE)

    for degrees in range(0, 360, 2):
        row, col = dial_cell(center_row, center_col, DIAL_RADIUS, math.radians(degrees))
        screen.addstr(row, col, "·", curses.A_DIM)

    for flap in range(1, game.ring_count + 1):
        angle = math.radians(-90 + (flap - 1) * 360 / game.ring_count)
        color = ring_colors[(flap - 1) % len(ring_colors)] | curses.A_BOLD
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


def animate_flap(screen, game, ring_colors, flap):
    start = (game.state >> (flap - 1)) & 1
    for frame in range(1, ANIMATION_FRAMES):
        extent = start + (1 - 2 * start) * frame / ANIMATION_FRAMES
        try:
            draw(screen, game, ring_colors, {flap: extent})
        except curses.error:
            return
        curses.napms(ANIMATION_FRAME_MS)


def move(screen, game, ring_colors):
    if game.theme is THEMES["brain"] and can_toggle(game.state, game.cursor):
        animate_flap(screen, game, ring_colors, game.cursor)
    game.move(game.cursor)


def run(screen, ring_count, goal_on, theme):
    curses.curs_set(0)
    ring_colors = [0]
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        palette = RING_COLORS_256 if curses.COLORS >= 256 else RING_COLORS_8
        for pair, color in enumerate(palette, start=1):
            curses.init_pair(pair, color, -1)
        ring_colors = [curses.color_pair(pair) for pair in range(1, len(palette) + 1)]

    game = Game(ring_count, goal_on, theme)
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
            move(screen, game, ring_colors)
        elif ord("1") <= key <= ord("9") and key - ord("0") <= game.ring_count:
            game.cursor = key - ord("0")
            move(screen, game, ring_colors)
        elif key == ord("h"):
            game.show_hint()
        elif key == ord("u"):
            game.undo()
        elif key == ord("r"):
            game.reset()
        elif key == ord("m"):
            game = Game(game.ring_count, not game.goal_on, theme)
        elif key in (ord("+"), ord("=")) and game.ring_count < MAX_RINGS:
            game = Game(game.ring_count + 1, game.goal_on, theme)
        elif key in (ord("-"), ord("_")) and game.ring_count > MIN_RINGS:
            game = Game(game.ring_count - 1, game.goal_on, theme)


def main():
    parser = argparse.ArgumentParser(
        description="Play the Chinese rings puzzle, or Mag-Nif's The Brain with --brain."
    )
    parser.add_argument(
        "rings",
        nargs="?",
        type=int,
        help=f"number of rings or flaps ({MIN_RINGS}-{MAX_RINGS}, default 5 rings or 8 flaps)",
    )
    parser.add_argument(
        "--brain",
        action="store_true",
        help="play The Brain: pull all 8 flaps out of the dial",
    )
    parser.add_argument(
        "--reverse",
        "--on",
        action="store_true",
        help="play the other way: put every ring on, or push every Brain flap in",
    )
    args = parser.parse_args()
    theme = THEMES["brain"] if args.brain else THEMES["rings"]
    ring_count = theme["default_count"] if args.rings is None else args.rings
    if not MIN_RINGS <= ring_count <= MAX_RINGS:
        parser.error(f"count must be between {MIN_RINGS} and {MAX_RINGS}")
    goal_on = theme["default_goal_on"] != args.reverse
    curses.wrapper(run, ring_count, goal_on, theme)


if __name__ == "__main__":
    main()
