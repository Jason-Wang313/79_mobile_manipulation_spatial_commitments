# Submission Readiness Decision

Decision: KILL_ARCHIVE

ICLR main-conference readiness: NO.

Reason: v4 adds implemented local mobile-manipulation geometry evidence, but the evidence does not support the central claim. The commitment planner ties receding-horizon TAMP on the decisive combined long-horizon split and does not reduce future regret. Ablations are indistinguishable from the full method.

Additional blockers:

- No real robot validation.
- No recognized high-fidelity simulator benchmark.
- No learned mobile-manipulation policy or learned commitment model.
- The local oracle/search baseline is also weak under high stress, which indicates the benchmark/mechanism is not mature enough for main-track claims.

Honest terminal action: archive/kill for ICLR main. Do not submit this paper to ICLR main in its current form.

Revival condition: rebuild on real or high-fidelity mobile-manipulation tasks and show decisive gains over strong task-and-motion planning baselines with nontrivial ablations.
