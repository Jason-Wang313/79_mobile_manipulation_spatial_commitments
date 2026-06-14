# 79 Mobile Manipulation Spatial Commitments

Submission-hardening version: v4

Terminal decision: KILL_ARCHIVE for ICLR main conference.

Paper 79 was rebuilt from a v3 synthetic archive into a local mobile-manipulation geometry benchmark. The runner simulates base-pose selection, reachability, approach clearance, drawer/door swing blocking, aisle traps, clutter occlusion, multi-step task sequences, receding-horizon TAMP, commitment-cost planning, ablations, and stress sweeps.

The evidence is negative. On the decisive `combined_long_horizon` split, `commitment_cost_planner` reaches `0.100 +/- 0.074` episode success, tying `receding_horizon_tamp` at `0.100 +/- 0.074` and only slightly above `reachability_margin_sampler` at `0.071 +/- 0.056`. The paired success difference versus TAMP is `0.00000`, and future-regret difference is also `0.00000`. Ablations are indistinguishable from the full method.

## Reproduce Evidence

```powershell
python src\run_experiment.py
```

This writes:

- `results/rollouts.csv` with 2,450 main rollout rows.
- `results/raw_seed_metrics.csv` with 245 seed-level metric rows.
- `results/metrics.csv` with aggregate metrics and confidence intervals.
- `results/pairwise_stats.csv` with paired comparisons.
- `results/ablation_rollouts.csv` and `results/ablation_metrics.csv`.
- `results/stress_sweep_raw.csv` and `results/stress_sweep.csv`.
- `results/negative_cases.csv`.
- Figures under `figures/`.

## Rebuild PDF

```powershell
cd paper
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Canonical local PDF: `C:/Users/wangz/Downloads/79.pdf`

No visible Desktop PDF is required or produced.
