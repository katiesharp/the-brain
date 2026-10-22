# Chinese Rings

The Chinese rings puzzle (Baguenaudier) and Mag-Nif's The Brain in your terminal. Python 3 standard library only, no install needed.

```bash
python3 rings.py             # 5 rings
python3 rings.py 9           # the classic nine rings (341 moves)
python3 rings.py --reverse   # start with rings off, put them all on
python3 rings.py --brain     # The Brain: pull all 8 rods out (170 moves)
```

Run it without cloning (add `--brain` or any other option at the end):

```bash
python3 <(gh api -H "Accept: application/vnd.github.raw" repos/katiesharp/chinese-rings/contents/rings.py)
```

## Rules

Take every ring off the bar, or with `--reverse` (or `m` in game) put every ring on starting from all off. Rings are numbered from the free end (ring 1 is on the left).

- Ring 1 can always be moved on or off.
- Any other ring can move only when the ring just to its left is on the bar and every ring further left is off.

Press a ring's number to move it. Each ring has its own color.

## The Brain

Mag-Nif's The Brain (1970s) is a tower of 8 transparent rotating discs with 8 rods through it. Every rod starts pushed in, and the goal is to pull them all out. Under the discs it's the same puzzle as the Chinese rings, with "out" for "on" and "in" for "off":

- Rod 1 can always be pulled out or pushed in.
- Any other rod can move only when the rod just to its left is out and every rod further left is in.

`--brain --reverse` (or `m` in game) starts with every rod out and the goal of pushing them all in.

## Keys

| Key | Action |
|---|---|
| ← / → | select a ring |
| space / enter | move the selected ring |
| 1–9 | move that ring |
| h | hint (next move on the shortest path) |
| u | undo |
| r | restart |
| + / - | more / fewer rings |
| m | switch goal (rings: off ↔ on, Brain: out ↔ in) |
| q | quit |
