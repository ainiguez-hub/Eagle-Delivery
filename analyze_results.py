"""Compute training/evaluation statistics for every results folder.

Usage: python3 analyze_results.py [results_root]
Writes <results_root>/training_analysis.csv (one row per folder and seed,
plus a 'mean' row per folder).
"""
import csv
from pathlib import Path
import statistics
import sys

FOLDERS = ["baseline_SW", "baseline_LD", "baseline_HP",
           "custom_e005", "custom_e020", "custom_e050"]
LATE = 200  # "late" training window: the last 200 episodes


def read_csv(filename):
    with open(filename, newline="") as source:
        return list(csv.DictReader(source))


def seed_stats(training, evaluation):
    steps = [int(r["steps"]) for r in training]
    returns = [float(r["return"]) for r in training]
    success = [int(r["success"]) for r in training]
    failures = [int(r["episode"]) for r in training if not int(r["success"])]
    late = training[-LATE:]
    return {
        "train_success_rate": statistics.mean(success),
        "truncated_episodes": len(failures),
        "last_failure_episode": max(failures) if failures else 0,
        "truncated_after_200": sum(1 for e in failures if e > 200),
        "total_training_steps": sum(steps),
        "first100_mean_steps": statistics.mean(steps[:100]),
        "late_mean_steps": statistics.mean(int(r["steps"]) for r in late),
        "late_mean_return": statistics.mean(float(r["return"]) for r in late),
        "late_min_steps": min(int(r["steps"]) for r in late),
        "eval_success_rate": statistics.mean(int(r["success"]) for r in evaluation),
        "eval_mean_steps": statistics.mean(int(r["steps"]) for r in evaluation),
        "eval_mean_return": statistics.mean(float(r["return"]) for r in evaluation),
    }


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "results")
    rows = []
    for folder in FOLDERS:
        path = root / folder
        summary = read_csv(path / "summary.csv")
        per_seed = []
        for entry in summary:
            seed = entry["seed"]
            stats = seed_stats(read_csv(path / ("training_seed" + seed + ".csv")),
                               read_csv(path / ("evaluation_seed" + seed + ".csv")))
            row = {"folder": folder, "map": entry["map"],
                   "task": entry["start"] + "->" + entry["goal"],
                   "epsilon": entry["epsilon"], "seed": seed}
            row.update(stats)
            per_seed.append(row)
        mean_row = dict(per_seed[0], seed="mean")
        for key in per_seed[0]:
            if key not in ("folder", "map", "task", "epsilon", "seed"):
                mean_row[key] = round(statistics.mean(r[key] for r in per_seed), 3)
        rows.extend(per_seed + [mean_row])
    for row in rows:
        for key, value in row.items():
            if isinstance(value, float):
                row[key] = round(value, 3)
    output = root / "training_analysis.csv"
    with open(output, "w", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("Saved", output)


if __name__ == "__main__":
    main()
