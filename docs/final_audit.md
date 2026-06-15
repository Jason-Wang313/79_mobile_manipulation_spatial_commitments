# Final Audit

1. Chosen thesis: mobile-manipulation planners should account for spatial commitments created by base motion and base placement.
2. ICLR-main decision: KILL_ARCHIVE.
3. Submission-hardening version: v4.
4. Evidence added: local geometric mobile-manipulation benchmark with base reach, arm approach, drawer/door swing, aisle trap, clutter occlusion, receding-horizon TAMP, commitment-cost planning, ablations, and stress sweeps.
5. Main evidence rows: 2,450 main rollouts, 245 seed-level metric rows, 980 ablation rollouts, 1,260 stress-sweep rollouts.
6. Decisive result: on `combined_long_horizon`, `commitment_cost_planner` success is 0.100 +/- 0.074, `receding_horizon_tamp` is 0.100 +/- 0.074, and `reachability_margin_sampler` is 0.071 +/- 0.056.
7. Paired result: commitment-minus-TAMP success difference is 0.00000; future-regret difference is 0.00000.
8. Ablation result: full commitment, no-future, no-corridor, no-swing, no-reposition, and one-step variants all have 0.100 success and 0.900 future regret.
9. Stress result: at stress level 1.0, all evaluated planners have 0.000 success and 1.000 future regret.
10. Reproducibility: `python src/run_experiment.py` regenerates CSVs and figures.
11. Exact Downloads PDF path: `C:/Users/wangz/Downloads/79.pdf`
12. GitHub URL: https://github.com/Jason-Wang313/79_mobile_manipulation_spatial_commitments
13. Confirmation: no visible Desktop copy was requested or made.

## 2026-06-15 Continuation Audit

1. Plan-first requirement: satisfied by `docs/paper79_iclr_submission_execution_plan_20260615.md` before the continuation audit was closed.
2. Code gate: `python -m py_compile src/run_experiment.py` passed.
3. CSV integrity gate: audited 2,450 `rollouts.csv` rows, 245 `raw_seed_metrics.csv` rows, 280 `metrics.csv` rows, 60 `pairwise_stats.csv` rows, 14 `ablation_metrics.csv` rows, 980 `ablation_rollouts.csv` rows, 30 `stress_sweep.csv` rows, 1,260 `stress_sweep_raw.csv` rows, 12 `negative_cases.csv` rows, and 350 `scene_summary.csv` rows.
4. Seed gate: seeds 0 through 6 are present.
5. Main baseline gate: the evaluated methods are `commitment_cost_planner`, `commitment_planner_no_future`, `greedy_current_reach`, `navigation_then_manipulation`, `oracle_sequence_planner`, `reachability_margin_sampler`, and `receding_horizon_tamp`.
6. Decisive split: on `combined_long_horizon`, `commitment_cost_planner` reaches 0.100 +/- 0.074 success, 0.900 future regret, and 2.329 repositions; `receding_horizon_tamp` reaches 0.100 +/- 0.074 success, 0.900 future regret, and 2.357 repositions.
7. Paired statistics: commitment-minus-TAMP success difference is 0.00000 +/- 0.00000 and future-regret difference is 0.00000 +/- 0.00000. The small reposition/path differences are not a submission-grade win.
8. Ablation gate: full commitment, no-future reach loss, no-corridor term, no-swing term, no-reposition term, and one-step-only all reach 0.100 success and 0.900 future regret.
9. Stress gate: at stress level 1.0, `commitment_cost_planner`, `commitment_planner_no_future`, `oracle_sequence_planner`, `reachability_margin_sampler`, and `receding_horizon_tamp` all reach 0.000 success and 1.000 future regret.
10. PDF gate: `paper/main.pdf` rebuilt cleanly after BibTeX-author and float-placement cleanup, then copied to `C:/Users/wangz/Downloads/79.pdf`.
11. Artifact gate: `C:/Users/wangz/Downloads/79.pdf` SHA256 is `F6FF3F2AB2733EB8079DB6E80F1682619EB8EA212289ECD861342FBCB0C509E0`; `C:/Users/wangz/Desktop/79.pdf` is absent.
12. Final decision: KILL_ARCHIVE. The paper is reproducible as a negative diagnostic, but not submission-ready for ICLR main.
