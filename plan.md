# Plan

Paper 79 v5 expanded rebuild is complete and terminal.

The frozen plan was written before execution in `docs/paper79_expanded_submission_plan_20260621.md`. The pass rebuilt the paper around a falsifiable claim: explicit spatial-commitment tree search should beat myopic, receding-horizon, sequence-search, graph-search, and backtracking mobile-manipulation baselines when early base poses destroy future feasibility.

## 2026-06-21 v5 Plan and Result

Plan before execution: run CPU-only and RAM-light; use eight seeds; compare 11 methods across 7 splits; include hard-regime aggregates, pairwise uncertainty, ablations, stress sweeps, fixed-risk budgets, negative cases, generated figures/tables, bright boxed citations, 25+ pages, Downloads-only numbered PDF, and public GitHub update.

Result: the evidence fails the ICLR-main readiness gate. On `combined_long_horizon`, `spatial_commitment_tree_search_v5`, `receding_horizon_tamp`, `robust_backtracking_tamp`, and the oracle all have `0.000 +/- 0.000` success. On the aggregate hard regime, v5 has `0.396 +/- 0.005` success and ties `robust_backtracking_tamp` and `exact_sequence_oracle`. The paired hard-regime success difference versus robust backtracking is `0.00000 +/- 0.00000`; maximum-stress success is `0.000`; fixed-risk combined-long-horizon success is `0.000` for all budgets; and ablations do not prove the mechanism is necessary.

Terminal action: `KILL_ARCHIVE`.

Final artifacts: 7,392 main rollouts, 672 scene diagnostics, 616 seed main metrics, 1,600 ablation rollouts, 4,096 stress rollouts, 3,072 fixed-risk rollouts, 12 negative cases, a 68-page validated PDF, and SHA256 `858EF0AD1A929071167AF5781397AFFA2F727DE59D3C70FFDCE454CB5B244ED8`.
