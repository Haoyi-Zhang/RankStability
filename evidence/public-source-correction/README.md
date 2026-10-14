# Source-corrected public fixed-matrix replay

The immutable source is Diversity-aware Mutation Testing commit
`f8d8376e0efe345161f26ff6483a404c8548fe1c`. The five upstream Git blob IDs match
the retained provenance. Four slices match all selected rows. Historical Time-10
has six unsupported passing-test names, a differing failure row and differing
operator labels. `input/` restores the original selection rule and actual source
columns. Historical `external/` and `results/` are not overwritten.
The corrected slice remains third-party MIT-licensed material from the same
upstream corpus; attribution and license are retained in
`external/LICENSE-DIVERSITY-AWARE-MUTATION-TESTING.txt` and `licenses/NOTICE.md`.

`historical-source-audit.json` retains the initial row-level discrepancies.
The upstream `src/Matrix/InitMatrix.java` reads fixed-version mutation logs and
separate faulty-version trigger labels. No faulty-program mutant output relation
is inferred. No upstream code or binaries were executed.

`replay/` contains all fifteen current cases, complete direct populations,
certificates, same-information interval/random controls and environment/input
bindings. All fifteen cases remain refutable and randomly found, with 26,855
feasible and 23,781 refuting subsets. The historical population was
27,423/24,443; these are not interchangeable records or native program histories.

Regenerate with the documented `tests/public_source_replay.py` command at a new
evidence path. The supplied corrected input is a real-source slice, not a new
generated research corpus. Neither this repair nor a generated matrix is claimed
as a new scientific contribution.
