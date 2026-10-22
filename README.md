# The Brain

Mag-Nif's The Brain puzzle in your terminal. Python 3 standard library only, no install needed.

Play it without downloading anything:

```bash
python3 <(curl -s https://raw.githubusercontent.com/katiesharp/the-brain/main/brain.py)
```

Add options at the end of that command, or run a local copy:

```bash
python3 brain.py              # 8 flaps, pull them all out (170 moves)
python3 brain.py --reverse    # start with every flap out, push them all in (or press ↓ in game)
python3 brain.py 5            # fewer flaps (1-9)
```

## Rules

Mag-Nif's The Brain (1970s) is a round stack of transparent rotating discs with 8 flaps around the edge. The game shows it from above, with flap 1 at 12 o'clock and the rest clockwise. Every flap starts pushed in, and the goal is to pull them all out. Pressing a flap's number slides it in or out.

- Flap 1 can always be pulled out or pushed in.
- Any other flap can move only when the flap numbered just before it is out and every lower-numbered flap is in.

Each flap has its own color.

## Keys

| Key | Action |
|---|---|
| 1–9 | move that flap |
| ← / → | select a flap |
| space / enter | move the selected flap |
| h | hint (next move on the shortest path) |
| u | undo |
| r | restart |
| + / - | more / fewer flaps |
| ↑ | new game: start with every flap in, pull them all out |
| ↓ | new game: start with every flap out, push them all in |
| q | quit |
