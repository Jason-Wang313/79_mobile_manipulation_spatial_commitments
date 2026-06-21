# 79 Mobile Manipulation Spatial Commitments

Submission-hardening version: v5 expanded

Terminal decision: KILL_ARCHIVE for ICLR main conference.

Paper 79 was rebuilt into a CPU-only, RAM-light hostile-review archive for mobile-manipulation spatial commitments. The v5 runner evaluates whether explicit future spatial-commitment reasoning beats strong sequence-search and backtracking baselines when early base-pose choices create later aisle traps, drawer swing deadlocks, clutter occlusion, relocation pressure, and adversarial dead ends.

The evidence is negative. On the decisive `combined_long_horizon` split, `spatial_commitment_tree_search_v5`, `receding_horizon_tamp`, and `robust_backtracking_tamp` all reach `0.000 +/- 0.000` success. On the aggregate hard regime, v5 reaches `0.396 +/- 0.005` success, tying `robust_backtracking_tamp` and `exact_sequence_oracle`. Maximum-stress success is `0.000`, fixed-risk combined-long-horizon success is `0.000` at all evaluated budgets, and ablations do not establish mechanism necessity.

## Evidence Artifacts

- `results/rollouts.csv`: 7,392 main rollout rows.
- `results/scene_summary.csv`: 672 scene/support diagnostic rows.
- `results/raw_seed_metrics.csv`: 616 seed-level main metric rows.
- `results/metrics.csv`: 770 aggregate metric rows.
- `results/pairwise_stats.csv`: 252 pairwise statistic rows.
- `results/aggregate_seed_metrics.csv`: 88 hard-regime seed rows.
- `results/aggregate_metrics.csv`: 110 hard-regime metric rows.
- `results/aggregate_pairwise_stats.csv`: 36 hard-regime pairwise rows.
- `results/ablation_rollouts.csv`: 1,600 ablation rollout rows.
- `results/stress_sweep_raw.csv`: 4,096 stress rollout rows.
- `results/fixed_risk_raw.csv`: 3,072 fixed-risk rollout rows.
- `results/negative_cases.csv`: 12 curated negative cases.

## Reproduce Evidence

```powershell
python src\run_experiment.py
```

## Rebuild Manuscript

```powershell
python scripts\generate_manuscript.py
cd paper
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

## Validate

```powershell
python scripts\validate_submission_artifacts.py
```

Canonical final PDF: `C:/Users/wangz/Downloads/79.pdf`

Validated PDF pages: 68

Validated PDF SHA256: `858EF0AD1A929071167AF5781397AFFA2F727DE59D3C70FFDCE454CB5B244ED8`

No visible Desktop PDF is produced.
