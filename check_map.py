"""Check a campus map against the Part C rules.

Usage: python3 check_map.py maps/my_campus.txt
"""
import sys

import agents
from campus import BUILDING_NAMES, CampusMap


def open_cells(campus):
    return [(r, c) for r in range(campus.height) for c in range(campus.width)
            if campus.passable((r, c))]


def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else "maps/my_campus.txt"
    rows = open(filename).read().splitlines()
    campus = CampusMap(filename)  # raises on bad symbols, ragged rows, duplicates
    checks = []
    text = "".join(rows)
    checks.append(("each of S L H D P W exactly once",
                   all(text.count(letter) == 1 for letter in BUILDING_NAMES)))
    checks.append(("only # . S L H D P W symbols",
                   set(text) <= set("#." + "".join(BUILDING_NAMES))))
    checks.append(("rectangular", len({len(row) for row in rows}) == 1))
    checks.append(("size %dx%d within 9..25" % (campus.height, campus.width),
                   9 <= campus.height <= 25 and 9 <= campus.width <= 25))
    border = (rows[0] + rows[-1] + "".join(row[0] + row[-1] for row in rows))
    checks.append(("surrounded by #", set(border) == {"#"}))

    cells = open_cells(campus)
    degree = {cell: len(campus.neighbors(cell)) for cell in cells}
    edges = sum(degree.values()) // 2
    # Count connected components with a flood fill.
    seen, components = set(), 0
    for cell in cells:
        if cell in seen:
            continue
        components += 1
        stack = [cell]
        seen.add(cell)
        while stack:
            for _, nxt in campus.neighbors(stack.pop()):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
    independent_cycles = edges - len(cells) + components
    result = agents.bfs(campus, campus.location("S"), campus.location("W"))
    dead_ends = sorted(cell for cell, d in degree.items() if d == 1)
    checks.append(("S->W route reachable (length %s)"
                   % (len(result.path) - 1 if result.path else None),
                   result.path is not None))
    checks.append(("at least one cycle (%d independent cycles)" % independent_cycles,
                   independent_cycles >= 1))
    checks.append(("at least one dead end (%s)" % ", ".join(map(str, dead_ends)),
                   len(dead_ends) >= 1))
    checks.append(("all open cells connected (%d component)" % components,
                   components == 1))
    for name, ok in checks:
        print(("PASS " if ok else "FAIL ") + name)
    sys.exit(0 if all(ok for _, ok in checks) else 1)


if __name__ == "__main__":
    main()
