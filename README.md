# Chinese Rings

The Chinese rings puzzle (Baguenaudier) in your terminal. Python 3 standard library only, no install needed.

```bash
python3 rings.py      # 5 rings
python3 rings.py 9    # the classic nine rings (341 moves)
python3 rings.py --on # reverse: start with rings off, put them all on
```

Run it without cloning:

```bash
python3 <(gh api -H "Accept: application/vnd.github.raw" repos/katiesharp/chinese-rings/contents/rings.py)
```

## Rules

Take every ring off the bar, or with `--on` (or `m` in game) put every ring on starting from all off. Rings are numbered from the free end (ring 1 is on the left).

- Ring 1 can always be moved on or off.
- Any other ring can move only when the ring just to its left is on the bar and every ring further left is off.

Press a ring's number to move it. Each ring has its own color.

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
| m | switch goal between all off and all on |
| q | quit |
