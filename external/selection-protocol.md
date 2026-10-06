# Frozen external-matrix challenge protocol

The challenge set is a deterministic, result-blind slice of the public Diversity-aware Mutation Testing Defects4J matrices at commit `f8d8376e0efe345161f26ff6483a404c8548fe1c`. It is used only to test whether the certificate implementation generalizes beyond owned generators; it is not a line-level fault-localization effectiveness benchmark.

1. Projects are Chart, Closure, Lang, Math, and Time.
2. The bug for each project is the smallest-mutant matrix among entries with at least one trigger and at least twelve mutants, breaking ties by bug id: Chart-24, Closure-28, Lang-54, Math-32, Time-10.
3. Select mutant columns 1--12 in file order. Each selected mutant is treated as its own location because the public CSV does not provide a sound source-location map.
4. Select the first eight `dev` rows with `bug=0` in file order. Add every official Defects4J trigger test that appears as a `dev` row with `bug=1`, capped at two.
5. Freeze three policy profiles before solving: `balanced` (operator counts within one of a six-mutant seed, stratum counts 1--3, size 5--8), `exact` (exact seed operator counts, exactly two per stratum, size 6), and `relaxed` (unbounded operator groups, stratum counts 0--4, size 4--9). Strata are three equal groups obtained by sorting the twelve columns by total kill count and then mutant identity; the six-mutant seed takes the first two columns in each stratum.
6. The supplied claim is the full-universe top-three set, with mutant order as the deterministic tie order and bottom empty floor.
7. Enumerate all 4096 subsets independently, run the producer and checker, exact marginal intervals, and the frozen random baseline. Keep every result.

No certification outcome or suspiciousness value is used to select the corpus or tune policy profiles; passing/failing labels and predeclared kill-density strata are used as specified above. The snapshots preserve only the selected rows/columns and therefore do not redistribute the full upstream matrices.
