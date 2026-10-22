# Chinese Rings

The Chinese rings puzzle (Baguenaudier) in your terminal. Python 3 standard library only, no install needed.

```bash
python3 rings.py      # 5 rings
python3 rings.py 9    # the classic nine rings (341 moves)
```

Run it without cloning:

```bash
gh api repos/katiesharp/chinese-rings/contents/rings.py --jq .content | base64 -d > /tmp/rings.py && python3 /tmp/rings.py
```

## Rules

Take every ring off the bar. Rings are numbered from the free end (ring 1 is on the right).

- Ring 1 can always be moved on or off.
- Any other ring can move only when the ring just to its right is on the bar and every ring further right is off.

Press a ring's number to move it. Rings you can move right now are shown in green.

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
| q | quit |
