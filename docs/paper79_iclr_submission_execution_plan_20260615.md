# Paper 79 ICLR-Main Submission-Readiness Execution Plan

Date: 2026-06-15
Paper: 79 - `mobile_manipulation_spatial_commitments`
Target venue posture: ICLR main only if spatial-commitment planning beats strong TAMP baselines
Current terminal label entering audit: `KILL_ARCHIVE`

## Goal

Audit Paper 79 as a real submission candidate rather than a polished negative diagnostic. The core question is whether explicit spatial-commitment costs improve long-horizon mobile manipulation beyond receding-horizon TAMP and reachability-margin planning.

## Decision Rule

Upgrade from `KILL_ARCHIVE` only if all of the following are true:

1. `commitment_cost_planner` decisively beats `receding_horizon_tamp` on `combined_long_horizon` success.
2. It reduces future regret, repositioning, or long-horizon trap failures rather than merely tying the baseline.
3. Ablations show future-reach, corridor, swing, and reposition terms are necessary.
4. Stress-sweep evidence remains favorable at the hardest clutter/aisle/trap settings.
5. The evidence is reproducible from checked-in code, raw CSVs, a clean PDF, and a public GitHub repository.

If any decisive gate fails, preserve `KILL_ARCHIVE` and document the exact failure mode.

## Evidence Gates

Run these checks before changing the decision:

1. Code integrity: compile `src/run_experiment.py`.
2. Result integrity: verify all required CSVs exist, are nonempty, finite, and schema-valid.
3. Scale check: confirm 2,450 main rollout rows, 245 seed metric rows, 980 ablation rollout rows, 1,260 stress-sweep raw rows, and the scene-summary artifact.
4. Baseline check: confirm `greedy_current_reach`, `navigation_then_manipulation`, `reachability_margin_sampler`, `receding_horizon_tamp`, `commitment_planner_no_future`, `commitment_cost_planner`, and `oracle_sequence_planner` are present.
5. Central comparison check: verify `combined_long_horizon` success, future regret, repositioning, and paired success/regret differences.
6. Ablation check: verify whether full commitment planning beats no-future, no-corridor, no-swing, no-reposition, and one-step variants.
7. Stress check: verify hardest stress behavior against TAMP and oracle.
8. Documentation consistency check: correct stale counts or wording if direct artifacts disagree.
9. Paper build: run LaTeX/BibTeX to produce a clean PDF and copy only `79.pdf` to Downloads.
10. Artifact hygiene: confirm no numbered PDF is copied to the visible Desktop.
11. GitHub hygiene: confirm the matching public GitHub repository exists and the local commit is pushed.
12. Root-report hygiene: update `GLOBAL_POOL_STATUS.md`, `BATCH_STATUS.md`, `SUBMISSION_STATUS.md`, `MASTER_REPORT.md`, and `MASTER_SUBMISSION_REPORT.md`.

## Expected Risk

The existing summary reports a decisive non-improvement: `commitment_cost_planner` and `receding_horizon_tamp` both achieve 0.100 +/- 0.074 success on `combined_long_horizon`, with paired success difference 0.000 and future-regret difference 0.000. Ablations also appear indistinguishable from the full method. Unless direct verification contradicts that result, Paper 79 remains a reproducible negative-result archive.

## Execution Order

1. Re-check repository cleanliness and result inventory.
2. Run code and CSV integrity gates.
3. Extract central, pairwise, ablation, and stress evidence.
4. Rebuild the paper PDF and repair recoverable build warnings.
5. Update child status and audit docs with exact verified evidence.
6. Update root reports through Paper 79.
7. Commit and push the Paper 79 repository.
8. Verify `Downloads/79.pdf`, no Desktop copy, public GitHub visibility, clean git state, and root report consistency.
