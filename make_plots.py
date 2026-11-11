"""Make the report figures from saved CSVs (matplotlib only).

Usage: python3 make_plots.py [results_root]
Saves PNG files to <results_root>/figures/.
"""
import csv
from pathlib import Path
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

COLORS = ["#2a78d6", "#eb6834", "#1baf7a"]
DASHES = ["-", "--", ":"]
BLOCK = 20  # episodes per point on the learning curves
SEEDS = (0, 1, 2)


def read_csv(filename):
    with open(filename, newline="") as source:
        return list(csv.DictReader(source))


def block_means(folder, field):
    """Mean of `field` over seeds, then over consecutive BLOCK-episode windows."""
    runs = [read_csv(folder / ("training_seed%d.csv" % s)) for s in SEEDS]
    per_episode = [statistics.mean(float(run[i][field]) for run in runs)
                   for i in range(len(runs[0]))]
    xs, ys = [], []
    for start in range(0, len(per_episode), BLOCK):
        chunk = per_episode[start:start + BLOCK]
        xs.append(start + len(chunk))
        ys.append(statistics.mean(chunk))
    return xs, ys


def style(ax, title, ylabel):
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("Training episode")
    ax.set_ylabel(ylabel)
    ax.grid(True, color="#e3e3e3", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def learning_figure(root, series, suptitle, filename):
    fig, (left, right) = plt.subplots(1, 2, figsize=(10, 3.25))
    for i, (folder, label) in enumerate(series):
        xs, steps = block_means(root / folder, "steps")
        _, success = block_means(root / folder, "success")
        kwargs = dict(color=COLORS[i], linestyle=DASHES[i], linewidth=2, label=label)
        left.plot(xs, steps, **kwargs)
        right.plot(xs, [100 * v for v in success], **kwargs)
    left.set_yscale("log")
    left.set_yticks([15, 20, 30, 50, 100, 200])
    left.set_yticklabels(["15", "20", "30", "50", "100", "200"])
    style(left, "Steps per episode (log scale)", "Actions per episode")
    style(right, "Delivery success rate", "Success rate (%)")
    right.set_ylim(0, 102)
    left.legend(frameon=False)
    right.legend(frameon=False, loc="lower right")
    fig.suptitle(suptitle + " (mean of seeds 0-2, %d-episode blocks)" % BLOCK,
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(filename, dpi=200)
    plt.close(fig)
    print("Saved", filename)


def epsilon_bar_figure(root, filename):
    analysis = [r for r in read_csv(root / "training_analysis.csv")
                if r["folder"].startswith("custom") and r["seed"] == "mean"]
    labels = ["eps = " + r["epsilon"] for r in analysis]
    late = [float(r["late_mean_steps"]) for r in analysis]
    evaluation = [float(r["eval_mean_steps"]) for r in analysis]
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    width = 0.36
    positions = range(len(labels))
    bars1 = ax.bar([p - width / 2 - 0.01 for p in positions], late, width,
                   color=COLORS[0], label="Training, last 200 episodes (eps on)")
    bars2 = ax.bar([p + width / 2 + 0.01 for p in positions], evaluation, width,
                   color=COLORS[1], hatch="//", edgecolor="white",
                   label="Evaluation (eps = 0, frozen Q)")
    ax.axhline(20, color="#555555", linewidth=1, linestyle="--",
               label="Optimal route (20 actions)")
    for bar in list(bars1) + list(bars2):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.6,
                "%.1f" % bar.get_height(), ha="center", fontsize=9)
    ax.set_xticks(list(positions))
    ax.set_xticklabels(labels)
    ax.set_xlabel("Exploration rate during training")
    ax.set_ylabel("Mean actions per delivery")
    ax.set_title("my_campus S->W: training vs. evaluation route length\n"
                 "(mean of seeds 0-2)", fontsize=11)
    ax.set_ylim(0, max(late) * 1.18)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    fig.savefig(filename, dpi=200)
    plt.close(fig)
    print("Saved", filename)


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "results")
    figures = root / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    learning_figure(root, [("baseline_SW", "S->W (optimal 18)"),
                           ("baseline_LD", "L->D (optimal 22)"),
                           ("baseline_HP", "H->P (optimal 16)")],
                    "Part B: Q-learning on emu_campus, eps = 0.2",
                    figures / "partB_learning_curves.png")
    learning_figure(root, [("custom_e005", "eps = 0.05"),
                           ("custom_e020", "eps = 0.2"),
                           ("custom_e050", "eps = 0.5")],
                    "Part C: my_campus S->W by exploration rate",
                    figures / "partC_learning_curves.png")
    epsilon_bar_figure(root, figures / "partC_train_vs_eval_steps.png")


if __name__ == "__main__":
    main()
