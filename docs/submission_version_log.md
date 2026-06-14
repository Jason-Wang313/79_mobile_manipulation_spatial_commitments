# Submission Version Log

## v1 - Generated Draft

- Original continuation-batch generated paper and toy single-seed experiment.

## v2 - Submission Hardening

- Added hostile reviewer attack log and response docs.
- Replaced the toy experiment with seven-seed synthetic metrics, stronger baselines, ablations, stress tests, and negative cases.
- Terminal decision: WORKSHOP_ONLY.

## v3 - ICLR Main Gate Archive

- Applied the stricter ICLR-main-conference standard.
- Determined that missing real-robot/high-fidelity evidence and template-generated experiments were not recoverable by paper polishing.
- Terminal decision: KILL_ARCHIVE.

## v4 - Mobile-Manipulation Geometry Rebuild

- Added `docs/paper79_rebuild_plan.md` before execution.
- Replaced the synthetic probability-table script with a mobile-manipulation spatial-commitment geometry benchmark.
- Added receding-horizon TAMP, reachability-margin, no-future commitment, full commitment, and oracle/search baselines.
- Generated 2,450 main rollout rows, 980 ablation rows, and 1,260 stress rows.
- Rewrote docs and manuscript around the negative result.
- Terminal decision: KILL_ARCHIVE.
