# Hostile Reviewer Response

Paper: 79 Mobile Manipulation Spatial Commitments

## Strongest Technical Threats

- Classical task-and-motion planning already reasons over base poses, reachability, manipulation constraints, and future action feasibility.
- Optimal base placement and mobile-manipulator planning literatures directly attack the same problem.
- Receding-horizon TAMP is a strong baseline because it replans after each manipulation.
- A local geometric simulator is not enough to claim a robotics systems advance without hardware or recognized benchmark validation.

## v4 Response

The hostile reviewer would still reject this as an ICLR main submission, now with direct evidence. The v4 rebuild implemented a mobile-manipulation geometry benchmark, but the proposed commitment-cost planner did not beat receding-horizon TAMP:

- Commitment planner: 0.100 combined long-horizon success.
- Receding-horizon TAMP: 0.100 combined long-horizon success.
- Paired success difference: 0.00000.
- Future-regret difference: 0.00000.
- Full and no-future ablations are identical.

## Honest Action

The paper remains `KILL_ARCHIVE`. The repository should be retained as a negative diagnostic, not reframed as an ICLR-main algorithm paper.

## 2026-06-15 Continuation Response

The continuation audit strengthens the hostile-reviewer conclusion rather than weakening it. The proposed method still has no decisive empirical separation from receding-horizon TAMP:

- `commitment_cost_planner`: 0.100 +/- 0.074 combined long-horizon success.
- `receding_horizon_tamp`: 0.100 +/- 0.074 combined long-horizon success.
- Paired success difference: 0.00000 +/- 0.00000.
- Paired future-regret difference: 0.00000 +/- 0.00000.
- Full, no-future, no-corridor, no-swing, no-reposition, and one-step ablations all reach 0.100 success and 0.900 future regret.
- At maximum stress, every evaluated planner reaches 0.000 success and 1.000 future regret.

The only honest response is to archive the paper as a reproducible failed mechanism test.
