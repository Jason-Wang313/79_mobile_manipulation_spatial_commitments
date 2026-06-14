# Novelty Decision

Chosen thesis: explicit spatial-commitment costs should help mobile manipulators avoid base placements that damage future manipulation feasibility.

Implemented novelty test: a local geometry benchmark with narrow aisles, drawer/door swing conflicts, cluttered approach occlusion, long-horizon task sequences, and stress sweeps.

Decision: KILL_ARCHIVE.

Reason: the mechanism is not empirically distinct from receding-horizon TAMP or no-future variants. The novelty boundary collapses to ordinary replanning and reachability scoring under the local evidence.
