#!/usr/bin/env bash
# Reproduce every result of the project into results_rerun/ (never results/).
# Usage: bash run_all.sh            (takes a few minutes)
set -euo pipefail
cd "$(dirname "$0")"

OUT="results_rerun"
PY="${PYTHON:-python3}"
if [ -d "$OUT" ]; then
    echo "Removing previous $OUT/ (the submitted results/ folder is never touched)"
    rm -rf "$OUT"
fi
mkdir -p "$OUT"

echo "== Unit tests =="
"$PY" -m unittest discover -v

echo "== Custom map rule check =="
"$PY" check_map.py maps/my_campus.txt

echo "== Part A: BFS vs A* =="
"$PY" search_comparison.py "$OUT/search_comparison.csv"

echo "== Part B: baseline Q-learning (emu_campus, seeds 0 1 2, defaults) =="
for task in "S W" "L D" "H P"; do
    set -- $task
    dir="$OUT/baseline_$1$2"
    "$PY" run_project.py train --map maps/emu_campus.txt --start "$1" --goal "$2" --output "$dir"
    "$PY" summarize_results.py "$dir" | tee "$dir/summary_output.txt"
done

echo "== Part C: epsilon experiment (my_campus S->W, seeds 0 1 2) =="
for setting in "0.05 e005" "0.2 e020" "0.5 e050"; do
    set -- $setting
    dir="$OUT/custom_$2"
    "$PY" run_project.py train --map maps/my_campus.txt --epsilon "$1" --output "$dir"
    "$PY" summarize_results.py "$dir" | tee "$dir/summary_output.txt"
done

echo "== Analysis and figures =="
"$PY" analyze_results.py "$OUT"
"$PY" make_plots.py "$OUT"

echo "== Comparing every rerun CSV with the submitted results/ =="
status=0
while IFS= read -r file; do
    rel="${file#"$OUT"/}"
    if ! cmp -s "$file" "results/$rel"; then
        echo "DIFFERS: $rel"
        status=1
    fi
done < <(find "$OUT" -name "*.csv" | sort)
if [ "$status" -eq 0 ]; then
    echo "All rerun CSV files are identical to results/."
fi
exit "$status"
