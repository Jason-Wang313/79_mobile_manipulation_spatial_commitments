# Claims

- Tested mechanism claim: explicit spatial-commitment costs should improve mobile-manipulation task success by avoiding base poses that create future reach, swing, aisle, or approach failures.
- Evidence claim: v4 implements a local mobile-manipulation geometry benchmark with seven seeds, five splits, receding-horizon TAMP, reachability-margin baselines, commitment-cost planning, ablations, stress sweeps, and negative cases.
- Empirical result: the mechanism fails the local gate; `commitment_cost_planner` ties `receding_horizon_tamp` at 0.100 combined success and does not reduce future regret.
- Scope claim: the repository is useful as a negative diagnostic of a spatial-commitment idea, not as an ICLR-main submission.
- Unsupported claim explicitly avoided: no claim of improved mobile-manipulation planning performance.
