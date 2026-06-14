# Paper 79 Rebuild Plan: Mobile Manipulation Spatial Commitments

## Goal

Rebuild Paper 79 into an honest ICLR-main gate study of the claim:

> Mobile manipulation planners should reason about spatial commitments: base motions and base placements that make future manipulation harder even when the current action is feasible.

The rebuild must implement a concrete mobile-manipulation geometry benchmark rather than another probability-table scaffold. The terminal decision must be evidence-driven. If the proposed commitment mechanism does not beat strong task-and-motion planning baselines, the paper stays `KILL_ARCHIVE`.

## Benchmark

Implement a local 2D mobile-manipulation simulator with:

- A circular mobile base.
- A planar arm reach annulus and manipulation cone.
- Rooms, doorways, counters, drawers, and narrow aisles represented as polygons/segments.
- Object goals that require base placement, reachability, collision-free arm approach, and enough clearance for drawer/door swing.
- Multi-step task sequences where an early base pose can block a later pose, trap the robot in an aisle, occlude a grasp approach, or require costly repositioning.

The benchmark should expose the difference between immediate feasibility and future spatial regret.

## Splits

Evaluate five splits over seven seeds:

- `open_room_easy`: base placement is mostly unconstrained; commitment reasoning should not matter much.
- `narrow_kitchen_aisle`: current feasible poses can trap the base or block later reach in a narrow aisle.
- `drawer_door_conflict`: a base pose that reaches one handle blocks a later drawer/door swing.
- `cluttered_reach_occlusion`: clutter and counters create approach-cone commitments.
- `combined_long_horizon`: future task order, aisle width, and object placements combine into commitment-heavy episodes.

## Methods

Implement all methods against the same geometry:

- `greedy_current_reach`: choose the nearest pose that reaches the current object.
- `navigation_then_manipulation`: plan base path first, then check manipulation feasibility.
- `reachability_margin_sampler`: choose poses with high immediate reach and clearance margins.
- `receding_horizon_tamp`: replan after every object with a short horizon and explicit collision checks.
- `commitment_cost_planner`: proposed method that scores base poses by immediate feasibility plus future reach-set loss, corridor blocking, swing-clearance loss, and reposition cost.
- `commitment_planner_no_future`: ablation that keeps immediate commitment features but removes future task loss.
- `oracle_sequence_planner`: upper bound that knows the full future task sequence and searches over base-pose sequences.

## Metrics

Primary metrics:

- Episode success: all manipulation subtasks completed.
- Per-object manipulation success.
- Future-regret rate: an earlier base pose makes a later subtask infeasible.
- Reposition count and reposition distance.
- Base collision rate.
- Arm approach collision rate.
- Drawer/door swing-block rate.
- Path length and execution cost.
- Paired success difference versus `receding_horizon_tamp`.
- Paired success difference versus `reachability_margin_sampler`.

Secondary diagnostics:

- Commitment-cost calibration.
- Failure labels: aisle trap, swing block, reach loss, approach occlusion, navigation collision, oracle-only solvable.
- Negative cases where commitment scoring is over-conservative.

## Ablations

Run ablations on `combined_long_horizon` and `drawer_door_conflict`:

- Remove future reach-set loss.
- Remove corridor-blocking term.
- Remove swing-clearance term.
- Remove reposition-cost term.
- Use one-step horizon only.
- Replace commitment score with random feasible pose among top immediate-reach candidates.

## Stress Sweeps

Stress the mechanism by varying:

- Aisle width.
- Future-task ambiguity.
- Clutter density.
- Drawer/door swing radius.
- Number of subtasks per episode.

## Submission Gate

The paper may reach only `STRONG_REVISE`, not full ICLR-ready, without robot or recognized high-fidelity benchmark validation. It must be `KILL_ARCHIVE` if:

- The commitment planner does not beat `receding_horizon_tamp` on combined long-horizon success.
- Gains vanish when compared to reachability-margin or oracle-informed search.
- Success comes from over-conservative repositioning rather than useful spatial commitment prediction.
- Ablations do not show that future commitment terms are necessary.
- Stress sweeps show brittle behavior under realistic aisle/clutter/swing changes.

## Deliverables

- Replace `src/run_experiment.py` with the mobile-manipulation geometry benchmark and runner.
- Save raw rollouts, per-seed metrics, pairwise statistics, ablations, stress sweeps, training/scene summaries, and negative cases under `results/`.
- Save figures under `figures/`.
- Rewrite README, audit docs, readiness decision, hostile reviewer response, and ICLR gate.
- Rewrite `paper/main.tex` as an evidence report with a terminal decision.
- Compile `paper/main.pdf` and copy only `C:/Users/wangz/Downloads/79.pdf`.
- Commit and push to the public GitHub repo.
- Update root pool reports after Paper 79 reaches a terminal state.
