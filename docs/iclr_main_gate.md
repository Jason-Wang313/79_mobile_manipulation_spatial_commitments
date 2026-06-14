# ICLR Main Gate

Paper: 79 mobile_manipulation_spatial_commitments

Submission-hardening version: v4

Gate verdict: KILL_ARCHIVE

Fatal evidence:

- `combined_long_horizon`: `commitment_cost_planner` success 0.100 +/- 0.074.
- `combined_long_horizon`: `receding_horizon_tamp` success 0.100 +/- 0.074.
- `combined_long_horizon`: `reachability_margin_sampler` success 0.071 +/- 0.056.
- Paired commitment-minus-TAMP success difference: 0.00000.
- Paired commitment-minus-TAMP future-regret difference: 0.00000.
- Full commitment and no-future ablations are identical.
- Stress level 1.0 collapses all evaluated planners to 0.000 success.

The only honest main-conference-safe decision is to archive rather than overclaim.
