# Chinese Rings

Mag-Nif's The Brain and the Chinese rings puzzle (Baguenaudier) in your terminal. Python 3 standard library only, no install needed.

```bash
python3 rings.py                # The Brain: pull all 8 flaps out (170 moves)
python3 rings.py --reverse      # The Brain backwards: push all 8 flaps in
python3 rings.py --rings        # Chinese rings, 5 rings
python3 rings.py --rings 9      # the classic nine rings (341 moves)
```

Run it without cloning (add `--rings` or any other option at the end):

```bash
python3 <(gh api -H "Accept: application/vnd.github.raw" repos/katiesharp/chinese-rings/contents/rings.py)
```

## Rules

With `--rings`, take every ring off the bar, or with `--rings --reverse` (or `m` in game) put every ring on starting from all off. Rings are numbered from the free end (ring 1 is on the left).

- Ring 1 can always be moved on or off.
- Any other ring can move only when the ring just to its left is on the bar and every ring further left is off.

Press a ring's number to move it. Each ring has its own color.

## The Brain

Mag-Nif's The Brain (1970s) is a round stack of 8 transparent rotating discs with 8 flaps around the edge. The game shows it from above, with flap 1 at 12 o'clock and the rest clockwise. Every flap starts pushed in, and the goal is to pull them all out; pressing a flap's number slides it in or out. Under the discs it's the same puzzle as the Chinese rings, with "out" for "on" and "in" for "off":

- Flap 1 can always be pulled out or pushed in.
- Any other flap can move only when the flap numbered just before it is out and every lower-numbered flap is in.

This is the default game. `--reverse` (or `m` in game) starts with every flap out and the goal of pushing them all in.

## Keys

| Key | Action |
|---|---|
| ← / → | select a ring or flap |
| space / enter | move the selected ring |
| 1–9 | move that ring |
| h | hint (next move on the shortest path) |
| u | undo |
| r | restart |
| + / - | more / fewer rings |
| m | switch goal (rings: off ↔ on, Brain: out ↔ in) |
| q | quit |
