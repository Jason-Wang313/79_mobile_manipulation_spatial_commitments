# Paper 79 Terminal Audit 2026-06-21

## Decision

Terminal decision: KILL_ARCHIVE.

ICLR main ready: no.

## Frozen Protocol

- CPU only and RAM-light.
- Seeds: 0 through 7.
- Main splits: `open_room_easy`, `narrow_aisle_commitment`, `drawer_swing_deadlock`, `clutter_occlusion_reach`, `relocation_sequence`, `combined_long_horizon`, `adversarial_dead_end`.
- Main methods: greedy reach, navigation-then-manipulation, reachability margin sampling, receding-horizon TAMP, v4 commitment cost, depth-2 rollout MPC, beam sequence search, topological graph search, robust backtracking TAMP, `spatial_commitment_tree_search_v5`, and exact sequence oracle.

## Final Counts

- Main rollouts: 7,392.
- Scene/support diagnostics: 672.
- Seed-level main metrics: 616.
- Main aggregate metrics: 770.
- Pairwise statistics: 252.
- Hard-regime seed metrics: 88.
- Hard-regime metrics: 110.
- Hard-regime pairwise statistics: 36.
- Ablation rollouts: 1,600.
- Stress rollouts: 4,096.
- Fixed-risk rollouts: 3,072.
- Negative cases: 12.

## Main Evidence

On `combined_long_horizon`, `spatial_commitment_tree_search_v5`, `receding_horizon_tamp`, `robust_backtracking_tamp`, and the exact oracle all reach `0.000 +/- 0.000` success. The proposed method therefore has no decisive success separation on the decisive split.

On the hard-regime aggregate, `spatial_commitment_tree_search_v5` reaches `0.396 +/- 0.005` success. This ties `robust_backtracking_tamp` and the exact oracle. The paired hard-regime success difference versus robust backtracking is `0.00000 +/- 0.00000`.

At maximum stress level `1.40`, v5 success is `0.000`. Fixed-risk combined-long-horizon success is `0.000` at budgets `0.00`, `0.05`, `0.10`, and `0.20`. The strongest practical ablation matches the full method on the decisive ablation split.

## Validation

`python scripts/validate_submission_artifacts.py` passed.

`C:/Users/wangz/Downloads/79.pdf` has 68 pages.

PDF SHA256: `858EF0AD1A929071167AF5781397AFFA2F727DE59D3C70FFDCE454CB5B244ED8`.

`C:/Users/wangz/Desktop/79.pdf` is absent.

Visual QA rendered all 68 pages and inspected representative title, citation, figure, appendix-table, fixed-risk, and reference pages. No clipping, unreadable glyphs, missing references, or citation-box defects were found.
