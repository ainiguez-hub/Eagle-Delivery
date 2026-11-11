# EagleDelivery

**COSC 461/561 Project 1, Eagle Delivery** by Andres Iniguez

A simulated delivery robot for Eastern Michigan University carries a package from one
building entrance to another on a grid map of campus. The project has three parts:

* **Part A:** plans the route with **A\*** (Manhattan heuristic) and compares it with the supplied BFS baseline.
* **Part B:** learns a navigation policy from experience with tabular **Q-learning** and ε-greedy exploration.
* **Part C:** designs a custom campus map (`maps/my_campus.txt`) and runs a controlled experiment on the exploration rate ε.

All algorithms are implemented from scratch in [`agents.py`](agents.py) with no search
or RL libraries. matplotlib is used only for plots, and reportlab only to build the PDF.
The full write-up is in [`report.pdf`](report.pdf).

## Requirements

* Python 3.9 or newer, standard library only, for the algorithms, tests, training and search.
* `matplotlib` for `make_plots.py`.
* `reportlab` for `build_report.py`. This is optional and only needed to rebuild the PDF.

```bash
python3 -m pip install matplotlib reportlab
```

## Repository structure

```
agents.py               BFS (supplied) + the four completed TODOs: manhattan, astar,
                        epsilon_greedy, q_learning_update
campus.py               Map loading, movement, rewards, resets (supplied, unchanged)
run_project.py          show / search / random / train commands (supplied, unchanged)
summarize_results.py    Evaluation summary + learning_curve.csv (supplied, unchanged)
search_comparison.py    Runs BFS and A* on all tasks -> results/search_comparison.csv
check_map.py            Verifies a map against the Part C rules
analyze_results.py      Per-seed training/evaluation statistics -> results/training_analysis.csv
make_plots.py           Figures -> results/figures/*.png
build_report.py         Builds report.pdf from the CSVs and figures
run_all.sh              Reproduces everything into results_rerun/ and diffs it against results/
maps/                   emu_campus.txt, emu_detour.txt (supplied), my_campus.txt (custom)
tests/                  Public unit tests (supplied, unchanged)
examples/               API demo (supplied)
results/
  search_comparison.csv         Part A table (6 required rows + my_campus)
  training_analysis.csv         Derived statistics for every Part B/C run
  baseline_SW|LD|HP/            Part B: training_seed{0,1,2}.csv, evaluation_seed{0,1,2}.csv,
                                summary.csv, learning_curve.csv, summary_output.txt
  custom_e005|e020|e050/        Part C: same files for eps = 0.05, 0.2, 0.5
  figures/                      partB_learning_curves.png, partC_learning_curves.png,
                                partC_train_vs_eval_steps.png
report.pdf              3-page report
```

## Run commands

Run these from the repository root.

```bash
# Tests: 14 total (6 environment + 8 student)
python3 -m unittest discover -v

# Search (Part A)
python3 run_project.py show
python3 run_project.py search --algorithm bfs   --start S --goal W     # length 18, expanded 67
python3 run_project.py search --algorithm astar --start S --goal W     # length 18, expanded 22
python3 run_project.py search --algorithm astar --map maps/emu_detour.txt --start L --goal D
python3 run_project.py search --algorithm astar --map maps/my_campus.txt
python3 search_comparison.py results_rerun/search_comparison.csv
python3 check_map.py maps/my_campus.txt

# Training + summary (Part B example). The runner refuses folders that already hold CSVs,
# so use a new output folder each time.
python3 run_project.py train --map maps/emu_campus.txt --start S --goal W --output results_rerun/my_run
python3 summarize_results.py results_rerun/my_run

# Analysis, plots and report (default: read results/)
python3 analyze_results.py
python3 make_plots.py
python3 build_report.py

# Reproduce everything (writes only to results_rerun/; never touches results/)
bash run_all.sh
```

## Experiment settings

**Part B baseline:** `maps/emu_campus.txt`, tasks S→W, L→D and H→P.

| Setting | Value |
|---|---|
| Training episodes | 2,000 per seed |
| Seeds | 0, 1, 2 (a fresh Q-table for each) |
| Evaluation episodes | 100 per seed (ε = 0, Q frozen) |
| Max actions per episode | 200 |
| α / γ / ε | 0.3 / 0.95 / 0.2 (constant) |
| Slip | 0.0 |

```bash
python3 run_project.py train --map maps/emu_campus.txt --start S --goal W --output results/baseline_SW
python3 run_project.py train --map maps/emu_campus.txt --start L --goal D --output results/baseline_LD
python3 run_project.py train --map maps/emu_campus.txt --start H --goal P --output results/baseline_HP
```

**Part C experiment:** `maps/my_campus.txt`, task S→W. Only ε changes, over **0.05, 0.2 and 0.5**.
Every other setting matches the baseline table above, including seeds 0, 1 and 2.

```bash
python3 run_project.py train --map maps/my_campus.txt --epsilon 0.05 --output results/custom_e005
python3 run_project.py train --map maps/my_campus.txt --epsilon 0.2  --output results/custom_e020
python3 run_project.py train --map maps/my_campus.txt --epsilon 0.5  --output results/custom_e050
```

Each folder was then summarized with `python3 summarize_results.py <folder> | tee <folder>/summary_output.txt`.

## Results summary

| Map | Task | BFS length | A* length | BFS expanded | A* expanded |
|---|---|---|---|---|---|
| emu_campus | S→W | 18 | 18 | 67 | 22 |
| emu_campus | L→D | 22 | 22 | 79 | 62 |
| emu_campus | H→P | 16 | 16 | 41 | 16 |
| emu_detour | S→W | 26 | 26 | 70 | 51 |
| emu_detour | L→D | 22 | 22 | 65 | 60 |
| emu_detour | H→P | 16 | 16 | 41 | 16 |
| my_campus | S→W | 20 | 20 | 83 | 25 |

* **Part A:** A* always finds an optimal route, the same length as BFS. It expands fewer nodes, but the saving
  is small (8% on detour L→D) when walls force the route far from the straight-line direction.
* **Part B:** all 9 baseline runs reach **100% evaluation success on the optimal route**: S→W in 18 actions
  (return 22), L→D in 22 (return 18) and H→P in 16 (return 24). Truncated training episodes stop by
  about episode 40, with one at episode 149. Late training stays 4–6 actions above optimal because ε = 0.2 is constant.
* **Part C:** all three ε values give the same optimal 20-action evaluation route. ε mainly changes the cost of
  training: the last 200 episodes average 21.0, 25.3 and 40.8 actions, and total training actions are about
  53k, 61k and 93k. Zero-initialized Q-values with −1 step costs act like optimistic initialization, so even
  ε = 0.05 explores enough.
