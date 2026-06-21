import csv
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PAPER = ROOT / "paper"
PAPER.mkdir(exist_ok=True)

METHOD_LABELS = {
    "greedy_current_reach": "greedy",
    "navigation_then_manipulation": "nav-then-manip",
    "reachability_margin_sampler": "reach-margin",
    "receding_horizon_tamp": "RH-TAMP",
    "commitment_cost_planner_v4": "commit-v4",
    "rollout_mpc_depth2": "MPC-d2",
    "beam_search_sequence_planner": "beam-search",
    "topological_base_graph_search": "topo-graph",
    "robust_backtracking_tamp": "backtracking",
    "spatial_commitment_tree_search_v5": "SCTS-v5",
    "exact_sequence_oracle": "oracle",
}


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def esc(text):
    return (
        str(text)
        .replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("$", "\\$")
        .replace("#", "\\#")
        .replace("_", "\\_")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("~", "\\textasciitilde{}")
        .replace("^", "\\textasciicircum{}")
    )


def metric(rows, split, method, name):
    vals = [r for r in rows if r.get("split") == split and r.get("method") == method and r.get("metric") == name]
    if not vals:
        return "0", "0"
    return vals[0]["mean"], vals[0]["ci95"]


def table_main(metrics, split, caption):
    lines = [
        "\\begin{table}[tbp]",
        "\\centering",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{3.0pt}",
        f"\\caption{{{caption}}}",
        "\\resizebox{\\linewidth}{!}{%",
        "\\begin{tabular}{lrrrrr}",
        "\\toprule",
        "Method & Success & Future regret & Commit. viol. & Repos. & Path \\\\",
        "\\midrule",
    ]
    for method, label in METHOD_LABELS.items():
        s, sci = metric(metrics, split, method, "success")
        r, _ = metric(metrics, split, method, "future_regret")
        c, _ = metric(metrics, split, method, "commitment_violation")
        rep, _ = metric(metrics, split, method, "reposition_count")
        path, _ = metric(metrics, split, method, "path_length")
        lines.append(f"{esc(label)} & {float(s):.3f}$\\pm${float(sci):.3f} & {float(r):.3f} & {float(c):.3f} & {float(rep):.3f} & {float(path):.3f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "}", "\\end{table}"]
    return "\n".join(lines)


def table_rows(rows, columns, caption, label=None, max_rows=None):
    use_rows = rows[:max_rows] if max_rows else rows
    align = "l" * len(columns)
    lines = [
        "\\begin{table}[tbp]",
        "\\centering",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{3.0pt}",
        f"\\caption{{{caption}}}",
    ]
    if label:
        lines.append(f"\\label{{{label}}}")
    lines += [
        "\\resizebox{\\linewidth}{!}{%",
        f"\\begin{{tabular}}{{{align}}}",
        "\\toprule",
        " & ".join(esc(c) for c in columns) + " \\\\",
        "\\midrule",
    ]
    for row in use_rows:
        lines.append(" & ".join(esc(row.get(c, "")) for c in columns) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "}", "\\end{table}"]
    return "\n".join(lines)


def chunk_tables(rows, columns, title, chunk=34):
    out = []
    for i in range(0, len(rows), chunk):
        part = rows[i : i + chunk]
        out.append(table_rows(part, columns, f"{title} continued ({i + 1}-{i + len(part)})"))
        out.append("\\clearpage")
    return "\n\n".join(out)


def bibliography():
    return r"""
@book{lavalle2006planning,
  title={Planning Algorithms},
  author={LaValle, Steven M.},
  publisher={Cambridge University Press},
  year={2006},
  url={https://lavalle.pl/planning/}
}
@article{kaelbling2011tamp,
  title={Hierarchical Task and Motion Planning in the Now},
  author={Kaelbling, Leslie Pack and Lozano-Perez, Tomas},
  journal={IEEE International Conference on Robotics and Automation},
  year={2011}
}
@article{garrett2021pddlstream,
  title={PDDLStream: Integrating Symbolic Planners and Blackbox Samplers via Optimistic Adaptive Planning},
  author={Garrett, Caelan Reed and Lozano-Perez, Tomas and Kaelbling, Leslie Pack},
  journal={International Conference on Automated Planning and Scheduling},
  year={2021}
}
@article{kavraki1996prm,
  title={Probabilistic Roadmaps for Path Planning in High-Dimensional Configuration Spaces},
  author={Kavraki, Lydia E. and Svestka, Petr and Latombe, Jean-Claude and Overmars, Mark H.},
  journal={IEEE Transactions on Robotics and Automation},
  year={1996}
}
@article{lavalle1998rrt,
  title={Rapidly-Exploring Random Trees: A New Tool for Path Planning},
  author={LaValle, Steven M.},
  journal={Technical Report},
  year={1998}
}
@inproceedings{ratliff2009chomp,
  title={CHOMP: Gradient Optimization Techniques for Efficient Motion Planning},
  author={Ratliff, Nathan and Zucker, Matt and Bagnell, J. Andrew and Srinivasa, Siddhartha},
  booktitle={IEEE International Conference on Robotics and Automation},
  year={2009}
}
@inproceedings{kalakrishnan2011stomp,
  title={STOMP: Stochastic Trajectory Optimization for Motion Planning},
  author={Kalakrishnan, Mrinal and Chitta, Sachin and Theodorou, Evangelos and Pastor, Peter and Schaal, Stefan},
  booktitle={IEEE International Conference on Robotics and Automation},
  year={2011}
}
@article{stilman2007navigation,
  title={Navigation Among Movable Obstacles: Real-Time Reasoning in Complex Environments},
  author={Stilman, Mike and Kuffner, James},
  journal={International Journal of Humanoid Robotics},
  year={2007}
}
"""


def main():
    metrics = read_csv(RESULTS / "metrics.csv")
    aggregate = read_csv(RESULTS / "aggregate_metrics.csv")
    pairwise = read_csv(RESULTS / "pairwise_stats.csv")
    aggregate_pairwise = read_csv(RESULTS / "aggregate_pairwise_stats.csv")
    ablation = read_csv(RESULTS / "ablation_metrics.csv")
    stress = read_csv(RESULTS / "stress_sweep.csv")
    fixed = read_csv(RESULTS / "fixed_risk_metrics.csv")
    negative = read_csv(RESULTS / "negative_cases.csv")
    scene = read_csv(RESULTS / "scene_summary.csv")
    raw_seed = read_csv(RESULTS / "raw_seed_metrics.csv")
    aggregate_seed = read_csv(RESULTS / "aggregate_seed_metrics.csv")
    ablation_seed = read_csv(RESULTS / "ablation_seed_metrics.csv")
    fixed_seed = read_csv(RESULTS / "fixed_risk_seed_metrics.csv")
    summary = (RESULTS / "summary.txt").read_text(encoding="utf-8")
    terminal = "KILL_ARCHIVE" if "Terminal recommendation: KILL_ARCHIVE" in summary else "STRONG_REVISE"
    terminal_tex = terminal.replace("_", "\\_")
    reason = next((line.replace("Reason: ", "") for line in summary.splitlines() if line.startswith("Reason: ")), "")

    v5, v5_ci = metric(metrics, "combined_long_horizon", "spatial_commitment_tree_search_v5", "success")
    tamp, tamp_ci = metric(metrics, "combined_long_horizon", "receding_horizon_tamp", "success")
    robust, robust_ci = metric(metrics, "combined_long_horizon", "robust_backtracking_tamp", "success")
    hard_v5, hard_v5_ci = metric(aggregate, "aggregate_hard_regime", "spatial_commitment_tree_search_v5", "success")

    paper = rf"""
\documentclass{{article}}
\usepackage{{iclr2026_conference,times}}
\input{{math_commands.tex}}
\usepackage{{booktabs}}
\usepackage{{graphicx}}
\usepackage{{amsmath,amssymb}}
\usepackage[colorlinks=false,pdfborder={{0 0 1.6}},citebordercolor={{0 1 0}},linkbordercolor={{1 0.55 0}},urlbordercolor={{0 0.45 1}}]{{hyperref}}
\usepackage{{url}}
\title{{Spatial Commitments for Mobile Manipulation Under Hostile Sequence-Search Baselines}}
\author{{Anonymous authors}}
\begin{{document}}
\maketitle

\begin{{abstract}}
Paper 79 asks whether a mobile manipulator should explicitly reason about base-pose commitments that make future manipulation impossible. The expanded v5 rebuild uses eight seeds, seven geometry splits, eleven planners, hard-regime aggregates, component ablations, stress sweeps, fixed-risk budgets, curated negative cases, and seed-level appendices. The terminal recommendation is \textbf{{{terminal_tex}}}. On the decisive combined long-horizon split, SCTS-v5 reaches ${float(v5):.3f}\pm{float(v5_ci):.3f}$ success, receding-horizon TAMP reaches ${float(tamp):.3f}\pm{float(tamp_ci):.3f}$, and robust backtracking reaches ${float(robust):.3f}\pm{float(robust_ci):.3f}$. The hard-regime aggregate success of SCTS-v5 is ${float(hard_v5):.3f}\pm{float(hard_v5_ci):.3f}$. We report the frozen outcome rather than polishing around it.
\end{{abstract}}

\section{{Decision and Protocol}}
This manuscript is generated only from frozen CSV artifacts. The terminal recommendation is \textbf{{{terminal_tex}}}. The summary reason is: \emph{{{esc(reason)}}}

The protocol is intentionally hostile. It compares a spatial-commitment tree-search reference against greedy reachability, navigation-then-manipulation, receding-horizon TAMP, the v4 commitment-cost planner, depth-2 rollout MPC, beam sequence search, topological graph search, robust backtracking TAMP, and an exact sequence-search oracle. The surrounding literature already includes classical motion planning, task-and-motion planning, sampling-based planning, trajectory optimization, and navigation among movable obstacles \citep{{lavalle2006planning,kaelbling2011tamp,garrett2021pddlstream,kavraki1996prm,lavalle1998rrt,ratliff2009chomp,kalakrishnan2011stomp,stilman2007navigation}}.

\section{{Theory Sketch}}
Let $x_t$ denote the mobile-base pose and $g_i$ the manipulation goal at step $i$. A spatial commitment is a state transition $c(x_t, g_i)$ that may leave the current manipulation feasible while shrinking the future feasible set $\mathcal{{F}}_{{i+1:T}}$. A myopic planner minimizes immediate navigation and reach cost, while a commitment-aware planner should minimize
\[
J(x_{{1:T}})=\sum_i d(x_i,x_{{i-1}})+\lambda R_i(x_i,g_i)+\beta\,\Delta |\mathcal{{F}}_{{i+1:T}}|,
\]
where $\Delta |\mathcal{{F}}_{{i+1:T}}|$ is the predicted loss of future feasible base-pose sets. The theory predicts a narrow win condition: commitment costs matter only when the future feasible-set loss is predictable and not already handled by generic sequence search or backtracking. This is why v5 uses hostile sequence-search baselines.

\section{{Main Results}}
{table_main(metrics, "combined_long_horizon", "Decisive combined long-horizon split")}

\begin{{figure}}[tbp]
\centering
\includegraphics[width=0.95\linewidth]{{../figures/spatial_commitment_success.png}}
\caption{{Combined long-horizon success across mobile-manipulation planners.}}
\end{{figure}}

\begin{{figure}}[tbp]
\centering
\includegraphics[width=0.95\linewidth]{{../figures/spatial_commitment_regret.png}}
\caption{{Future-regret rates caused by earlier spatial commitments.}}
\end{{figure}}

\section{{Aggregate Hard-Regime Evidence}}
{table_main(aggregate, "aggregate_hard_regime", "Aggregate hard-regime metrics")}

\section{{Pairwise Statistics}}
{table_rows(pairwise, ["split", "comparison_method", "metric", "paired_diff", "ci95", "reference_better_seeds"], "Pairwise v5-reference comparisons", max_rows=36)}

{table_rows(aggregate_pairwise, ["split", "comparison_method", "metric", "paired_diff", "ci95", "reference_better_seeds"], "Aggregate hard-regime pairwise comparisons", max_rows=36)}

\section{{Ablations}}
{table_rows(ablation, ["split", "ablation", "success", "ci95", "future_regret", "risk_proxy"], "Component ablations")}

\begin{{figure}}[tbp]
\centering
\includegraphics[width=0.95\linewidth]{{../figures/spatial_commitment_ablation.png}}
\caption{{Ablations on the spatial-commitment mechanism.}}
\end{{figure}}

\section{{Stress Sweep}}
{table_rows(stress, ["stress_level", "method", "success", "ci95", "future_regret", "risk_proxy"], "Commitment stress sweep", max_rows=40)}

\begin{{figure}}[tbp]
\centering
\includegraphics[width=0.95\linewidth]{{../figures/spatial_commitment_stress_sweep.png}}
\caption{{Planner success as aisle width, clutter, future ambiguity, and swing radius become more hostile.}}
\end{{figure}}

\section{{Fixed-Risk Budgets}}
{table_rows(fixed, ["split", "risk_budget", "method", "metric", "mean", "ci95"], "Fixed-risk metric rows", max_rows=48)}

\begin{{figure}}[tbp]
\centering
\includegraphics[width=0.95\linewidth]{{../figures/spatial_commitment_fixed_risk.png}}
\caption{{Combined long-horizon success under fixed future-regret risk budgets.}}
\end{{figure}}

\section{{Negative Cases}}
{table_rows(negative, ["split", "seed", "episode_id", "method", "failure_label", "task_success_rate", "future_regret", "risk_proxy", "lesson"], "Curated negative cases")}

\section{{Limitations}}
This is a local diagnostic benchmark. It lacks real robot validation, external mobile-manipulation benchmarks, perception, learned policies, and integration with a full TAMP stack. Even a local positive result would need external validation before ICLR-main submission.

\section{{Conclusion}}
The evidence should be judged by hostile-review survival, not by whether the plots are pretty. The frozen v5 protocol decides whether explicit spatial commitments add value beyond generic sequence search and backtracking; the terminal recommendation above follows from that evidence.

\clearpage
\appendix
\section{{Scene Diagnostics}}
{chunk_tables(scene, ["split", "seed", "episode_id", "objects", "zones", "obstacles", "aisle_width", "clutter_density", "future_ambiguity", "relocation_pressure"], "Scene/support diagnostics", chunk=34)}

\section{{Seed-Level Main Metrics}}
{chunk_tables(raw_seed, ["split", "method", "seed", "episodes", "success", "task_success_rate", "future_regret", "commitment_violation", "reposition_count", "path_length", "risk_proxy"], "Seed-level main metrics", chunk=34)}

\section{{Seed-Level Aggregate Metrics}}
{chunk_tables(aggregate_seed, ["split", "method", "seed", "episodes", "success", "task_success_rate", "future_regret", "commitment_violation", "reposition_count", "path_length", "risk_proxy"], "Seed-level aggregate hard-regime metrics", chunk=34)}

\section{{Seed-Level Ablation Metrics}}
{chunk_tables(ablation_seed, ["split", "ablation", "seed", "episodes", "success", "future_regret", "commitment_violation", "risk_proxy"], "Seed-level ablation metrics", chunk=34)}

\section{{Seed-Level Fixed-Risk Metrics}}
{chunk_tables(fixed_seed, ["split", "risk_budget", "method", "seed", "episodes", "success", "fixed_risk_success", "risk_proxy"], "Seed-level fixed-risk metrics", chunk=34)}

\bibliographystyle{{iclr2026_conference}}
\bibliography{{references}}
\end{{document}}
"""
    (PAPER / "main.tex").write_text(textwrap.dedent(paper).strip() + "\n", encoding="utf-8")
    (PAPER / "references.bib").write_text(bibliography().strip() + "\n", encoding="utf-8")
    print(f"wrote {PAPER / 'main.tex'}")


if __name__ == "__main__":
    main()
