"""Run BFS and A* on every required delivery task and save a CSV table.

Usage: python3 search_comparison.py [output_csv]
"""
import csv
from pathlib import Path
import sys

import agents
from campus import CampusMap

TASKS = [
    ("maps/emu_campus.txt", "S", "W"),
    ("maps/emu_campus.txt", "L", "D"),
    ("maps/emu_campus.txt", "H", "P"),
    ("maps/emu_detour.txt", "S", "W"),
    ("maps/emu_detour.txt", "L", "D"),
    ("maps/emu_detour.txt", "H", "P"),
    ("maps/my_campus.txt", "S", "W"),
]


def length(result):
    return len(result.path) - 1 if result.path is not None else "NA"


def main():
    output = Path(sys.argv[1] if len(sys.argv) > 1 else "results/search_comparison.csv")
    output.parent.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).parent
    rows = []
    for map_name, first, last in TASKS:
        campus = CampusMap(root / map_name)
        start, goal = campus.location(first), campus.location(last)
        bfs_result = agents.bfs(campus, start, goal)
        astar_result = agents.astar(campus, start, goal)
        rows.append({"map": map_name, "delivery_task": first + "->" + last,
                     "bfs_route_length": length(bfs_result),
                     "astar_route_length": length(astar_result),
                     "bfs_expanded": bfs_result.expanded,
                     "astar_expanded": astar_result.expanded})
    with open(output, "w", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(row)
    print("Saved", output)


if __name__ == "__main__":
    main()
