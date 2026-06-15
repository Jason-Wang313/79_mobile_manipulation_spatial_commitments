# Plan

Paper 79 v4 rebuild is complete and terminal.

The paper was rebuilt around the falsifiable claim that mobile-manipulation planners should reason about spatial commitments that harm future manipulation. The implemented benchmark shows the commitment planner does not outperform receding-horizon TAMP and its ablations are indistinguishable. Terminal action: `KILL_ARCHIVE`.

## 2026-06-15 Continuation Plan and Result

Plan before execution: verify the negative claim rather than polish around it; re-run the ICLR-main evidence gate on code compilation, CSV schema/seed coverage, main baselines, pairwise uncertainty, ablations, stress sweep, PDF build cleanliness, artifact placement, and GitHub readiness.

Result: the evidence still fails the ICLR-main readiness gate. On `combined_long_horizon`, `commitment_cost_planner` and `receding_horizon_tamp` both reach 0.100 +/- 0.074 success with 0.900 future regret. Their paired success and future-regret differences are exactly 0.00000. The full method, no-future, no-corridor, no-swing, no-reposition, and one-step ablations all reach 0.100 success and 0.900 future regret. At stress level 1.0, all evaluated planners have 0.000 success and 1.000 future regret. Terminal action remains `KILL_ARCHIVE`.
