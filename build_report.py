"""Build report.pdf from the saved CSVs and figures.

Usage: python3 build_report.py      (needs: pip install reportlab)
All table numbers are read from results/, so the report always matches the data.
"""
import csv
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Image, Paragraph, Preformatted, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROOT = Path(__file__).parent
RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"
AUTHOR = "Andres Iniguez (ID 02704032)"


def read_csv(filename):
    with open(filename, newline="") as source:
        return list(csv.DictReader(source))


styles = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=styles["BodyText"], fontName="Times-Roman",
                      fontSize=9.4, leading=11.1, spaceAfter=3)
H1 = ParagraphStyle("h1", parent=BODY, fontName="Times-Bold", fontSize=11.5,
                    leading=13.5, spaceBefore=5, spaceAfter=2.5)
TITLE = ParagraphStyle("title", parent=BODY, fontName="Times-Bold", fontSize=14,
                       leading=17, alignment=TA_CENTER, spaceAfter=1)
SUB = ParagraphStyle("sub", parent=BODY, alignment=TA_CENTER, spaceAfter=6)
CAP = ParagraphStyle("cap", parent=BODY, fontSize=8.6, leading=10.2,
                     fontName="Times-Italic", spaceAfter=5)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8.4, leading=9.8, spaceAfter=0)
MONO = ParagraphStyle("mono", fontName="Courier", fontSize=7.6, leading=8.4)


def p(text, style=BODY):
    return Paragraph(text, style)


def table(rows, widths, caption):
    data = [[p(str(c), CELL) for c in row] for row in rows]
    t = Table(data, colWidths=widths, hAlign="CENTER")
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return [p(caption, CAP), t, Spacer(1, 5)]


def figure(name, width, caption):
    path = FIGURES / name
    img = Image(str(path))
    img.drawHeight = width * img.imageHeight / img.imageWidth
    img.drawWidth = width
    return [img, p(caption, CAP)]


def fmt(value, digits=1):
    number = float(value)
    return str(int(number)) if number == int(number) else ("%." + str(digits) + "f") % number


def main():
    search = read_csv(RESULTS / "search_comparison.csv")
    analysis = read_csv(RESULTS / "training_analysis.csv")
    means = {r["folder"]: r for r in analysis if r["seed"] == "mean"}
    seeds = {}
    for r in analysis:
        if r["seed"] != "mean":
            seeds.setdefault(r["folder"], []).append(r)

    story = [p("COSC 461/561 Project 1: Eagle Delivery", TITLE),
             p(AUTHOR + " &nbsp;&middot;&nbsp; A* search and Q-learning for a "
               "simulated EMU delivery robot", SUB)]

    # ---------------- Part A ----------------
    story.append(p("Part A: Planning a delivery with A*", H1))
    story.append(p(
        "<b>(a) Problem formulation.</b> <i>State:</i> the robot's cell (row, column) on a "
        "walkable square (<font face='Courier'>.</font> or a building letter). "
        "<i>Initial state:</i> the start entrance's cell, e.g. S = (1, 1). "
        "<i>Actions:</i> UP, DOWN, LEFT, RIGHT. "
        "<i>Transition model:</i> deterministic; an action moves one cell if the target is "
        "walkable and otherwise leaves the robot in place (search only generates the moves "
        "that change position, via <font face='Courier'>campus.neighbors</font>). "
        "<i>Goal test:</i> the state equals the destination entrance's cell; passing other "
        "entrances does nothing. <i>Path cost:</i> the number of actions, each costing 1. "
        "<b>BFS is optimal here</b> because it removes states in order of depth, and with "
        "unit step costs depth equals path cost. A state's first discovery is therefore by "
        "a shortest route, and the goal is first removed at the minimum number of actions."))
    story.append(p(
        "<b>(b) Admissibility of Manhattan distance.</b> One action changes either the row or "
        "the column by exactly 1 (no diagonals), so it reduces |r<sub>s</sub>&minus;r<sub>g</sub>| + "
        "|c<sub>s</sub>&minus;c<sub>g</sub>| by at most 1. Reaching the goal therefore takes at "
        "least h(s) actions. Walls only remove moves and never create shortcuts, so the true "
        "cost h*(s) &ge; h(s), and h(goal) = 0. h is also <i>consistent</i>: for any move "
        "s&rarr;s&prime;, h(s) &le; 1 + h(s&prime;). So the first time A* removes a state "
        "from the queue as a non-stale entry, it already has that state's optimal cost."))
    story.append(p(
        "<b>(c) Implementation.</b> A <font face='Courier'>heapq</font> queue holds "
        "(f, insertion number, g, state), so equal-f ties break in insertion order. "
        "<font face='Courier'>best_g</font> and <font face='Courier'>parents</font> are "
        "dictionaries. A successor is pushed again only when a strictly cheaper g is found. "
        "Popped entries whose g differs from <font face='Courier'>best_g</font> are skipped "
        "as stale. The goal test happens on removal. A node counts as expanded when its "
        "successors are generated, the same convention as the supplied BFS."))
    rows = [["Map", "Delivery task", "BFS route length", "A* route length",
             "BFS expanded", "A* expanded", "A* saving"]]
    for r in search:
        saving = 1 - int(r["astar_expanded"]) / int(r["bfs_expanded"])
        rows.append([r["map"].replace("maps/", ""), r["delivery_task"].replace("->", " &rarr; "),
                     r["bfs_route_length"], r["astar_route_length"], r["bfs_expanded"],
                     r["astar_expanded"], "%d%%" % round(100 * saving)])
    story += table(rows, [1.15 * inch, 0.85 * inch, 0.95 * inch, 0.9 * inch, 0.8 * inch,
                          0.75 * inch, 0.7 * inch],
                   "Table 1. BFS vs. A* (results/search_comparison.csv). The first six rows are "
                   "the required tasks; the last row is the custom map from Part C.")
    story.append(p(
        "<b>Discussion.</b> Both algorithms return routes of <b>equal length in every row</b>, "
        "as expected: BFS is optimal for unit costs and A* is optimal with an admissible, "
        "consistent heuristic. A* expanded fewer nodes in all seven rows, but the saving "
        "ranges from 67&ndash;70% (campus S&rarr;W, my_campus S&rarr;W) down to "
        "<b>only 8%</b> (detour L&rarr;D, 65 vs. 60). A* is not guaranteed to "
        "expand fewer nodes. It helps least when walls force the route far from the "
        "straight line, so the true cost is much larger than h. L sits at (5, 1) and D at "
        "(5, 15) in the same row, so h = 14, but L is walled in on its right side and the route takes 22 "
        "actions. Every cell whose g + h is below 22 must be expanded, and that covers most "
        "of the map. In the same way, the detour's closure at (3, 6) lengthens S&rarr;W from 18 "
        "to 26, and A*'s expansions rise from 22 to 51 while BFS barely changes (67 to 70). "
        "When h is uninformative, A* behaves like uniform-cost search, which is BFS order "
        "here, and it also pays heap overhead on each expansion."))

    # ---------------- Part B ----------------
    story.append(p("Part B: Learning a delivery policy with Q-learning", H1))
    story.append(p(
        "<b>Implementation and settings.</b> <font face='Courier'>epsilon_greedy</font> draws "
        "<font face='Courier'>rng.random()</font>. If the draw is below &epsilon; it picks uniformly among "
        "all four actions. Otherwise it picks uniformly among the actions tied at the maximum "
        "Q, with unseen pairs worth 0.0. "
        "<font face='Courier'>q_learning_update</font> sets Q(s,a) &larr; Q(s,a) + "
        "&alpha;[y &minus; Q(s,a)], where y = r on the terminal step and r + &gamma; max<sub>a&prime;</sub> "
        "Q(s&prime;,a&prime;) otherwise, and changes only that one entry. All baseline runs use the "
        "starter defaults: emu_campus, 2,000 training episodes, seeds 0/1/2, 100 evaluation "
        "episodes, 200 max actions, &alpha; = 0.3, &gamma; = 0.95, constant &epsilon; = 0.2, "
        "slip = 0. Evaluation uses &epsilon; = 0 with a frozen Q-table."))
    opt = {"baseline_SW": ("S &rarr; W", 18), "baseline_LD": ("L &rarr; D", 22),
           "baseline_HP": ("H &rarr; P", 16)}
    rows = [["Task (optimal)", "Eval. success", "Eval. steps / return", "Train success",
             "Trunc. eps.", "Last failure (seeds 0, 1, 2)", "Steps, eps. 1&ndash;100",
             "Steps / return, last 200", "Total train steps"]]
    for folder, (label, best) in opt.items():
        m = means[folder]
        rows.append(["%s (%d)" % (label, best), "%d%%" % round(100 * float(m["eval_success_rate"])),
                     "%s / %s" % (fmt(m["eval_mean_steps"]), fmt(m["eval_mean_return"])),
                     "%.1f%%" % (100 * float(m["train_success_rate"])),
                     fmt(m["truncated_episodes"]),
                     ", ".join(r["last_failure_episode"] for r in seeds[folder]),
                     fmt(m["first100_mean_steps"]),
                     "%s / %s" % (fmt(m["late_mean_steps"]), fmt(m["late_mean_return"])),
                     "{:,}".format(round(float(m["total_training_steps"])))])
    story += table(rows, [0.8 * inch, 0.58 * inch, 0.75 * inch, 0.58 * inch, 0.63 * inch,
                          0.8 * inch, 0.7 * inch, 0.82 * inch, 0.72 * inch],
                   "Table 2. Baseline results, means over seeds 0&ndash;2 (training_seed*.csv, "
                   "evaluation_seed*.csv; computed by analyze_results.py into "
                   "results/training_analysis.csv). Truncated = hit the 200-action limit.")
    story += figure("partB_learning_curves.png", 6.4 * inch,
                    "Figure 1. Training steps per episode (left, log scale) and delivery success "
                    "rate (right) for the three campus tasks, averaged over seeds in 20-episode "
                    "blocks.")
    story.append(p(
        "<b>Observations.</b> (1) <b>All nine runs reach 100% evaluation success on the "
        "shortest route</b>: 18 actions with return 22 for S&rarr;W, 22 with return 18 for L&rarr;D, and "
        "16 with return 24 for H&rarr;P, exactly the BFS/A* lengths. The sample SD across seeds is 0 for "
        "both success rate and return. (2) <b>Learning is fast.</b> Every truncated training "
        "episode happens early: the last failure is by episode 41 for S&rarr;W and 17 for L&rarr;D, "
        "and by episode 39 for H&rarr;P except one late truncation at episode 149 (seed 0). "
        "No run fails after episode 200, and training success is above 99%. Figure 1 shows "
        "the steps per episode falling from about 170 to a plateau within roughly 150 "
        "episodes. H&rarr;P learns fastest (57.6 mean steps in episodes 1&ndash;100 vs. 94&ndash;98) "
        "because its optimal route is the shortest (16 actions). (3) <b>Training "
        "stays above optimal while evaluation does not.</b> Over the last 200 episodes, "
        "training averages 22.5, 27.8 and 20.0 actions, 4&ndash;6 above optimal. With constant "
        "&epsilon; = 0.2, about one action in five is random. A random move often bumps a wall or "
        "steps backwards, and each one costs at least 1&ndash;2 extra actions. The longest task, L&rarr;D, "
        "makes the most random moves and pays the most. Evaluation sets &epsilon; = 0, so the "
        "greedy policy follows the learned optimal route every time. The gap between training "
        "and evaluation is the cost of exploration, not a learning failure."))

    # ---------------- Part C ----------------
    story.append(p("Part C: Custom map and exploration experiment", H1))
    story.append(p(
        "<b>(i) Question and prediction (stated before running the experiment).</b> "
        "<i>How does the exploration rate &epsilon; affect learning speed, training "
        "performance and the final greedy route on my_campus S&rarr;W?</i> I predicted that "
        "(1) training episodes would grow longer as &epsilon; rises, because more actions are "
        "random; (2) &epsilon; = 0.05 might settle on the longer 28-action inner route "
        "because it explores so little, while &epsilon; = 0.5 would find the 20-action "
        "route; and (3) &epsilon; = 0.5 would learn the greedy policy fastest, since it "
        "visits more state-action pairs early."))
    map_text = (ROOT / "maps" / "my_campus.txt").read_text().rstrip("\n")
    map_cell = [Preformatted(map_text, MONO),
                p("my_campus.txt (15 &times; 19). S (1,1), W (1,17), L (5,1), H (5,13), "
                  "D (7,17), P (9,1).", CAP)]
    bar = figure("partC_train_vs_eval_steps.png", 3.75 * inch,
                 "Figure 2. Late-training vs. evaluation steps by &epsilon;.")
    side = Table([[map_cell, bar]], colWidths=[2.35 * inch, 4.0 * inch])
    side.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                              ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    a_row = next(r for r in search if r["map"].endswith("my_campus.txt"))
    story.append(p(
        "<b>(ii) The custom map.</b> The map passes every rule (check_map.py). Each letter "
        "appears once, it is 15&times;19, rectangular and walled, and every open cell is "
        "reachable. It has 12 independent cycles. The relevant <b>loop</b> runs around the wall "
        "block in row 2, columns 9&ndash;15, and gives two S&rarr;W route choices. The "
        "<b>top corridor</b> takes 20 actions: row 1 is blocked at (1, 7), so the route dips "
        "through (3, 6)&ndash;(3, 8) and climbs back to row 1 at (2, 8). The <b>inner "
        "route</b> takes 28 actions: it stays on row 3 to (3, 9), drops to (5, 9)&ndash;(5, 11), "
        "returns to row 3 and follows it to column 15, then goes via (5, 15)&ndash;(5, 17) and "
        "up the east column to W. "
        "<b>Dead-end branches</b> end at (11, 16), (13, 3), (13, 5) and (13, 11), and the H and P "
        "entrances are cul-de-sacs. The whole southern half (L, P, D and the lower loops) is "
        "a detour trap for an S&rarr;W robot. BFS and A* both find the 20-action route; "
        "BFS expands %s nodes and A* %s (Table 1)." % (a_row["bfs_expanded"], a_row["astar_expanded"])))
    story.append(side)
    story.append(p(
        "<b>(iii) Method.</b> <i>Changed:</i> only &epsilon;, set to 0.05, 0.2 and 0.5 (constant during "
        "training). <i>Held fixed:</i> the map, S&rarr;W, seeds 0/1/2, 2,000 training episodes, "
        "&alpha; = 0.3, &gamma; = 0.95, 200 max actions, slip = 0 and 100 evaluation episodes. Each "
        "seed and setting starts from a fresh, empty Q-table. Training runs the supplied "
        "loop: choose an &epsilon;-greedy action, step, apply the Q-learning update, and repeat "
        "until delivery or 200 actions. Evaluation then uses &epsilon; = 0 with the Q-table frozen. "
        "This gives 9 runs, saved in results/custom_e005, custom_e020 and custom_e050."))
    rows = [["&epsilon;", "Eval. success", "Eval. steps / return", "Train success",
             "Trunc. eps.", "Trunc. after ep. 200", "Last failure (seeds 0, 1, 2)",
             "Steps, eps. 1&ndash;100", "Steps / return, last 200", "Total train steps"]]
    for folder, eps in (("custom_e005", "0.05"), ("custom_e020", "0.2"), ("custom_e050", "0.5")):
        m = means[folder]
        rows.append([eps, "%d%%" % round(100 * float(m["eval_success_rate"])),
                     "%s / %s" % (fmt(m["eval_mean_steps"]), fmt(m["eval_mean_return"])),
                     "%.1f%%" % (100 * float(m["train_success_rate"])),
                     fmt(m["truncated_episodes"]),
                     ", ".join(r["truncated_after_200"] for r in seeds[folder]),
                     ", ".join(r["last_failure_episode"] for r in seeds[folder]),
                     fmt(m["first100_mean_steps"]),
                     "%s / %s" % (fmt(m["late_mean_steps"]), fmt(m["late_mean_return"])),
                     "{:,}".format(round(float(m["total_training_steps"])))])
    story += table(rows, [0.38 * inch, 0.55 * inch, 0.72 * inch, 0.55 * inch, 0.6 * inch,
                          0.7 * inch, 0.82 * inch, 0.66 * inch, 0.82 * inch, 0.68 * inch],
                   "Table 3. &epsilon; experiment on my_campus S&rarr;W, means over seeds 0&ndash;2 "
                   "unless listed per seed (optimal route = 20 actions, return 20).")
    story += figure("partC_learning_curves.png", 6.4 * inch,
                    "Figure 3. my_campus S&rarr;W training steps per episode (left, log scale) and "
                    "success rate (right) by &epsilon;, averaged over seeds in 20-episode blocks.")
    e5, e20, e50 = means["custom_e005"], means["custom_e020"], means["custom_e050"]
    story.append(p(
        "<b>(iv) Findings.</b> <b>Final performance did not depend on &epsilon;.</b> All nine runs "
        "deliver 100%% of evaluation episodes in 20 actions (return 20), using the top corridor. "
        "<b>Training cost depends strongly on &epsilon;.</b> Over the last 200 episodes, training "
        "averages %s, %s and %s actions for &epsilon; = 0.05, 0.2 and 0.5, with returns of %s, %s and %s. "
        "&epsilon; = 0.5 needs about 75%% more total training actions (%s vs. %s), and its "
        "best late episode is still 23&ndash;24 actions. <b>Early learning is almost identical.</b> "
        "Mean steps over episodes 1&ndash;100 are %s, %s and %s, and every setting has about "
        "50&ndash;60 truncated episodes, nearly all before episode ~150 (Figure 3). "
        "The difference is in late failures: &epsilon; = 0.5 still truncates 1&ndash;3 episodes "
        "per seed after episode 200, with the last at episodes 1,157&ndash;1,652. The smaller "
        "&epsilon; values have at most one late truncation per run."
        % (fmt(e5["late_mean_steps"]), fmt(e20["late_mean_steps"]), fmt(e50["late_mean_steps"]),
           fmt(e5["late_mean_return"]), fmt(e20["late_mean_return"]),
           fmt(e50["late_mean_return"]),
           "{:,}".format(round(float(e50["total_training_steps"]))),
           "{:,}".format(round(float(e5["total_training_steps"]))),
           fmt(e5["first100_mean_steps"]), fmt(e20["first100_mean_steps"]),
           fmt(e50["first100_mean_steps"]))))
    story.append(p(
        "<b>(v) Discussion.</b> Prediction (1) held. Predictions (2) and (3) did not: "
        "&epsilon; = 0.05 never settled on the 28-action route, and &epsilon; = 0.5 did not learn "
        "faster. The reason is that <b>Q starts at 0 and every step costs &minus;1</b>, so any "
        "action already tried has a negative value, while untried actions still look like "
        "0. The greedy choice therefore prefers untried actions. This acts like "
        "<i>optimistic initialization</i>: early on, even a nearly greedy agent explores "
        "systematically, and &epsilon; adds little. That explains the near-identical first "
        "100 episodes and truncation counts. Q-learning is also <i>off-policy</i>. Its target uses "
        "max<sub>a&prime;</sub> Q, so random actions do not bias the learned values toward a worse "
        "route, and all settings converge to the same optimal greedy policy. In this "
        "deterministic map, &epsilon; mainly sets the <i>price</i> of exploration during "
        "training, not the quality of the final route. The surprise was that a large "
        "&epsilon; can still cause failed episodes late in training: when half the "
        "actions are random, a long random excursion into the southern loops sometimes uses "
        "up the 200-action limit even with a correct Q-table. With slip or a non-stationary map, I "
        "would expect larger &epsilon; to matter more, which would be a natural follow-up."))

    doc = SimpleDocTemplate(str(ROOT / "report.pdf"), pagesize=letter,
                            leftMargin=0.7 * inch, rightMargin=0.7 * inch,
                            topMargin=0.55 * inch, bottomMargin=0.55 * inch,
                            title="Eagle Delivery - Project 1 Report", author="Andres Iniguez")
    doc.build(story)
    print("Saved", ROOT / "report.pdf")


if __name__ == "__main__":
    main()
