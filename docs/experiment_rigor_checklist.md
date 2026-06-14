# Experiment Rigor Checklist

## v4 Local Rigor

- [x] Seven random seeds.
- [x] Local geometric mobile-manipulation simulator.
- [x] Base collision and arm approach checks.
- [x] Drawer/door swing-block checks.
- [x] Aisle-trap and clutter-occlusion commitment states.
- [x] Greedy, navigation-only, reachability-margin, receding-horizon TAMP, no-future commitment, full commitment, and oracle/search baselines.
- [x] Paired comparisons against receding-horizon TAMP and reachability-margin baselines.
- [x] Ablations over future, corridor, swing, reposition, and one-step terms.
- [x] Stress sweep over aisle/clutter/swing difficulty.
- [x] Negative cases.
- [x] Paper-specific figures.

## Still Missing For ICLR Main

- [ ] Real-robot validation.
- [ ] Recognized high-fidelity mobile-manipulation benchmark.
- [ ] Learned policy or learned commitment model.
- [ ] External TAMP baselines.
- [ ] Full manual related-work synthesis.

Decision: fail ICLR main empirical-rigor gate because the implemented local evidence is negative.
