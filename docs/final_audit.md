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
