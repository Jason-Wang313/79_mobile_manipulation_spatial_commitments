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

## v4 Continuation Audit - 2026-06-15

- Added `docs/paper79_iclr_submission_execution_plan_20260615.md` before closing the continuation pass.
- Rechecked code compilation, CSV integrity, seeds 0 through 6, main baselines, pairwise statistics, ablations, stress sweeps, PDF logs, Downloads-only placement, Desktop exclusion, and public GitHub status.
- Cleaned BibTeX placeholder entries by adding explicit authors and changed fragile `[h]` floats to `[tbp]` before rebuilding the PDF.
- Verified `C:/Users/wangz/Downloads/79.pdf` SHA256 `F6FF3F2AB2733EB8079DB6E80F1682619EB8EA212289ECD861342FBCB0C509E0`.
- Terminal decision remains: KILL_ARCHIVE.
