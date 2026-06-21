# Paper 79 Expanded v5 Submission-Hardening Plan

Date: 2026-06-21

Target: rebuild Paper 79 into a real CPU-only hostile-review archive/submission artifact. Do not optimize for pretty results. Optimize for evidence that can survive hostile review. If the mechanism fails, report the failure and keep `KILL_ARCHIVE`.

## Claim Under Test

Spatial commitment planning for mobile manipulation should outperform myopic reachability and receding-horizon task-and-motion planning when early base poses can create later aisle traps, drawer/door swing deadlocks, clutter approach occlusion, or relocation dead ends.

The reference method is `spatial_commitment_tree_search_v5`: a sequence-level base-pose planner with explicit commitment-state prediction, limited beam diversity, backtracking, and future-regret scoring.

## Frozen Experimental Scope

- CPU only.
- RAM-light implementation using deterministic geometry and bounded candidate lists.
- Seeds: 0-7.
- Main episodes per split/seed: 12.
- Demonstration-free local geometry benchmark; no learned checkpoint is claimed.
- Main splits:
  - `open_room_easy`
  - `narrow_aisle_commitment`
  - `drawer_swing_deadlock`
  - `clutter_occlusion_reach`
  - `relocation_sequence`
  - `combined_long_horizon`
  - `adversarial_dead_end`
- Hard aggregate splits:
  - `drawer_swing_deadlock`
  - `clutter_occlusion_reach`
  - `relocation_sequence`
  - `combined_long_horizon`
  - `adversarial_dead_end`

## Main Methods

1. `greedy_current_reach`
2. `navigation_then_manipulation`
3. `reachability_margin_sampler`
4. `receding_horizon_tamp`
5. `commitment_cost_planner_v4`
6. `rollout_mpc_depth2`
7. `beam_search_sequence_planner`
8. `topological_base_graph_search`
9. `robust_backtracking_tamp`
10. `spatial_commitment_tree_search_v5`
11. `exact_sequence_oracle`

The reference must beat strong non-oracle baselines, not merely weak greedy baselines. The oracle is an upper bound and is not counted as a method to beat.

## Planned Row Counts

- Main rollouts: 7 splits * 8 seeds * 12 episodes * 11 methods = 7,392.
- Scene/support diagnostics: 7 splits * 8 seeds * 12 episodes = 672.
- Raw seed metrics: 7 splits * 8 seeds * 11 methods = 616.
- Main aggregate metrics: 7 splits * 11 methods * 10 metrics = 770.
- Pairwise stats: 7 splits * 6 comparisons * 6 metrics = 252.
- Aggregate hard-regime seed metrics: 8 seeds * 11 methods = 88.
- Aggregate hard-regime metrics: 11 methods * 10 metrics = 110.
- Aggregate hard-regime pairwise stats: 6 comparisons * 6 metrics = 36.
- Ablation rollouts: 2 splits * 8 seeds * 10 episodes * 10 ablations = 1,600.
- Ablation seed metrics: 2 splits * 8 seeds * 10 ablations = 160.
- Ablation metrics: 2 splits * 10 ablations = 20.
- Stress raw rows: 8 stress levels * 8 seeds * 8 episodes * 8 methods = 4,096.
- Stress aggregate rows: 8 stress levels * 8 methods = 64.
- Fixed-risk raw rows: 2 splits * 4 budgets * 8 seeds * 8 episodes * 6 methods = 3,072.
- Fixed-risk seed metrics: 2 splits * 4 budgets * 8 seeds * 6 methods = 384.
- Fixed-risk metrics: 2 splits * 4 budgets * 6 methods * 3 metrics = 144.
- Fixed-risk pairwise rows: 2 splits * 4 budgets * 5 comparisons = 40.
- Curated negative cases: 12.

## Ablations

- `spatial_commitment_v5_full`
- `no_future_loss`
- `no_commitment_state`
- `no_backtracking`
- `no_beam_diversity`
- `one_step_only`
- `no_swing_cost`
- `no_aisle_cost`
- `no_occlusion_cost`
- `oracle_handoff`

The mechanism gate fails if any practical ablation matches or beats the full method on hard splits.

## Stress And Fixed-Risk Tests

Stress levels: 0.00, 0.20, 0.40, 0.60, 0.80, 1.00, 1.20, 1.40.

Fixed-risk budgets bound future-regret rate: 0.00, 0.05, 0.10, 0.20.

The method must not just increase success by accepting future-regret failures. It must retain success under fixed future-regret budgets and avoid collapse at maximum stress.

## Decision Gates

Assign `STRONG_REVISE` only if all of the following hold:

- `spatial_commitment_tree_search_v5` improves hard-aggregate success over `receding_horizon_tamp`, `beam_search_sequence_planner`, `topological_base_graph_search`, and `robust_backtracking_tamp` by at least 0.05.
- Paired lower confidence bounds against the strongest non-oracle baselines are positive for success and negative for future regret.
- It reduces future regret on `combined_long_horizon` and `adversarial_dead_end`.
- It does not lose maximum-stress success to a non-oracle baseline.
- It clears at least one nonzero fixed-risk budget without being matched by a simpler baseline.
- Ablations show necessity of future loss, commitment-state prediction, and backtracking.

If any of these fail, report `KILL_ARCHIVE` or, at most, `STRONG_REVISE` only if the evidence is genuinely promising but externally incomplete. No result may be hidden after the full protocol starts.

## Manuscript And Artifact Rules

- Generate the manuscript only from frozen CSV artifacts.
- Minimum target length: 25 pages, using real theory, tables, appendices, and evidence rather than filler.
- Bright citation boxes are required with `hyperref` border settings.
- Final numbered PDF must be `C:/Users/wangz/Downloads/79.pdf`.
- Do not create or copy `79.pdf` to the visible Desktop.
- Public GitHub repository must be updated after validation.
