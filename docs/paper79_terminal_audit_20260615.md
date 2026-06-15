# Paper 79 Terminal Audit - 2026-06-15

## Scope

Paper 79, `mobile_manipulation_spatial_commitments`, was re-audited under the sequential ICLR-main-target continuation gate. The goal was not to make the paper look ready, but to determine whether the real evidence could honestly support an ICLR-main submission.

## Execution Plan

The continuation plan was written first in `docs/paper79_iclr_submission_execution_plan_20260615.md`. The audit then checked code validity, evidence files, main baselines, paired statistics, ablations, stress behavior, PDF build hygiene, artifact placement, and public GitHub readiness.

## Verification

- Code compilation: `python -m py_compile src/run_experiment.py` passed.
- Main rows: 2,450 rollout rows and 245 seed-level metric rows.
- Secondary rows: 280 metric rows, 60 pairwise-stat rows, 14 ablation-metric rows, 980 ablation-rollout rows, 30 stress-sweep rows, 1,260 stress-rollout rows, 12 negative-case rows, and 350 scene-summary rows.
- Seeds: 0 through 6.
- Methods: `commitment_cost_planner`, `commitment_planner_no_future`, `greedy_current_reach`, `navigation_then_manipulation`, `oracle_sequence_planner`, `reachability_margin_sampler`, and `receding_horizon_tamp`.

## Central Evidence

On `combined_long_horizon`, `commitment_cost_planner` reaches 0.100 +/- 0.074 success and 0.900 future regret. `receding_horizon_tamp` reaches the same 0.100 +/- 0.074 success and 0.900 future regret. The paired success difference is 0.00000 +/- 0.00000 and the paired future-regret difference is 0.00000 +/- 0.00000.

The ablation gate also fails. The full method, no-future reach loss, no-corridor term, no-swing term, no-reposition term, and one-step-only variant all reach 0.100 success and 0.900 future regret on `combined_long_horizon`.

The stress gate fails. At stress level 1.0, every evaluated planner reaches 0.000 success and 1.000 future regret.

## Artifact Verification

- Downloads PDF: `C:/Users/wangz/Downloads/79.pdf`
- SHA256: `F6FF3F2AB2733EB8079DB6E80F1682619EB8EA212289ECD861342FBCB0C509E0`
- Desktop PDF: absent at `C:/Users/wangz/Desktop/79.pdf`
- GitHub: `https://github.com/Jason-Wang313/79_mobile_manipulation_spatial_commitments`

## Decision

Final decision: KILL_ARCHIVE.

The paper is useful as a reproducible negative diagnostic for spatial-commitment planning, but it is not ICLR-main-ready. The proposed method does not beat the strongest implemented non-oracle baseline, the ablations do not support the mechanism, and the hardest stress condition collapses all planners.
