# Counterexample-Calibrated Mutation-Ranking Certificates

This standalone repository checks whether a supplied top-k **set** is invariant over every mutant subset admitted by two crossing partition-quota systems, a global cardinality interval, and forced/forbidden identities. Scores are fixed squared-Ochiai values derived from a binary kill matrix; locations use maximum aggregation, an explicit empty-location floor, and a deterministic total tie order.

The producer returns exactly one of:

1. a nonvacuous stability certificate;
2. a globally minimum-cardinality refuting sample plus lower-bound proofs for every smaller cardinality; or
3. a policy-infeasibility certificate.

`src/checker.py` imports neither the producer, an oracle, nor flow-search code. It reconstructs scores, ranking branches, lower-bound networks, and cut capacities from the case and certificate.

## Requirements

Full reconstruction requires Linux, Python 3.11 or later, and a C11 compiler available as `cc`. Scientific code uses only the Python standard library. The portable finite campaign also runs on Windows without a compiler. Runs are serial and require no GPU, remote solver, model API, credential, or private service. The Linux reconstruction is bounded by `src/limited.py`; the portable runner enforces wall-clock timeouts and reports unavailable RSS as null, without claiming a memory cap or CPU affinity.

Do not invoke Python with `-O` or `PYTHONOPTIMIZE`; the limiter rejects optimized execution.

## Complete validation

The authoritative public-command list is `public_commands.json`. Run the twelve commands individually:

```sh
python src/limited.py tests/pilot.py
python src/limited.py tests/exhaustive.py
python src/limited.py tests/semantics.py
python src/limited.py tests/stress.py
python src/limited.py tests/reference_audit.py
python src/limited.py tests/protocol_audit.py
python src/limited.py tests/generated_oracle_audit.py
python src/limited.py tests/external_matrices.py
python src/limited.py tests/metamorphic.py
python src/limited.py tests/verify_all.py data results/campaign
python src/limited.py tests/reproduce.py
python src/limited.py tests/check_tables.py
```

The retained historical Linux release pass reports:

- 12,288 exhaustive tiny cases and 98,304 subset visits;
- 256 seeded pilot cases;
- 2,048 independently generated stress cases, 383,907 subset visits, and 25,463 rejected invalid certificate variants;
- 512 finite CNF instances, 320 finite three-partition reduction instances, six malformed empty-vector inputs rejected at two entry points (12 events), and two noninteger branch-label rejections;
- 200 confirmatory generated programs with all 6,553,600 subsets independently enumerated;
- 15 result-blind public kill-matrix cases from five Defects4J projects with all 61,440 subsets enumerated;
- 512 cases under five representation-preserving transformations, for 2,560 metamorphic checks;
- all 1,241 legal campaign certificates rechecked; 1,436 invalid variants generated from the 260 primary certificates and rejected;
- 220 C schemas recompiled, 2,463 retained scientific files and all non-timing operation counts compared, with a changed network count detected;
- 61 live-resolved manuscript references and an exact 12+5+5 full-paper calibration.

`public_commands.json` declares each command's source, inputs, and canonical output. `python tests/release_accounting.py` deletes each prior output, reruns all twelve commands under GNU `time -v`, requires the recreated file to equal same-run stdout, and verifies that a non-timing count change is detected. The retained historical pass matched 12/12 outputs and succeeded with 34.52 CPU seconds, 30.388 summed wall seconds, and a largest per-command maximum RSS of 97,580 KiB. These values describe that release pass only. The bibliography audit uses `literature/manuscript-citations.json`, a frozen citation snapshot, so the standalone repository does not depend on a sibling `paper/` directory. Metadata resolution and offline consistency do not establish claim-to-source entailment.

## Portable owned-input replay

From the standalone artifact root, choose a new output directory outside retained `results/`:

```text
python -B tests/local_campaign.py --out /path/to/new/owned-evidence
```

The seven commands rerun pilot, tiny exhaustive, semantic, stress, and metamorphic checks, recompute the 260 owned primary and 981 secondary certificates, and independently enumerate all 6,553,600 confirmatory subsets against the same-run primary table. Raw stdout/stderr, exact command arguments, durations, canonical JSON, and the fresh certificate packet are saved under that output directory. Existing result files are preserved. The runner has a 420-second total wall budget and 90/120/180-second child limits; its reviewed children create no subprocesses. This replay reconstructs matrices from retained observations but does not execute C or use external matrices.

The October 6, 2026 Windows pass completed 7/7 commands in 17.469 seconds (17.453 summed command seconds) and reproduced the 45 stable / 155 refutable program outcomes and every secondary-table count. Stress perturbations of the owned primary packet rejected 4,279 variants. This collection differs from the historical 1,436 variants; the historical total of 26,989 remains labelled separately. The CNF suite now actually evaluates all four assignments for each of its 512 formulas. Another 321 checks validate well-formed three-partition reduction outputs, with 3,303 additional selection visits kept separate from the historical 7,513 direct matching/quota visits.

`.github/workflows/scientific-checks.yml` runs the finite campaign and owned C reconstruction on Linux, preserving raw outputs. Run 37414665654 completed the seven stages in 24.080337995 wall seconds; its outputs match the finite counts, 1,241 certificates, all 220 recompiled C schemas, and 2,463 scientific files. It uses the runner's existing `cc`, installs no research dependencies, and does not execute external projects or TeX. This run does not establish all-citation entailment or validation beyond these owned inputs.

## Development/confirmation separation

Variant 19 of each of the ten owned program templates is reserved as a development subject. The 200 confirmatory programs use variants 0–18 and 20; `tests/protocol_audit.py` recompiles all ten development subjects and rejects overlap. The confirmation set is still a controlled template corpus, not 200 independent projects.

The independent confirmation audit in `tests/generated_oracle_audit.py` imports no producer, checker, or original oracle. It enumerates every subset, reimplements scores, quotas, ties, and top-set semantics, and confirms 45 stable and 155 refutable programs; every refuter has minimum size six.

## Floor sensitivity

The `zero_floor` sensitivity changes only the empty-location convention and keeps the supplied reference fixed. Its outcomes are 98 stable, 160 refutable, and 2 infeasible. In particular, the empty-universe `fixture-14` keeps `reference=[1]` and remains a minimum-zero refuter under both floor conventions.

## Public-matrix challenge

`external/` freezes license-compatible slices from `donghwan-shin/Diversity-aware-Mutation-Testing` at commit `f8d8376e0efe345161f26ff6483a404c8548fe1c`. The cases cover Chart-24, Closure-28, Lang-54, Math-32, and Time-10. Selection follows `external/selection-protocol.md` and does not inspect certification outcomes.

Each project contributes twelve mutation columns and official failing-test labels. Because the source archive does not provide mutant-to-source-location mappings in the CSVs, every mutant is treated as a surrogate location. This is a mutant-level specialization of the model, not a line-localization evaluation. Three predeclared policy profiles produce fifteen cases. All fifteen are refutable; exact marginal intervals certify none and random search observes every refuter. The negative outcome is retained rather than filtered.

## References and calibration

`literature/references.bib`, `literature/reference-provenance.csv`, and `literature/reference-live-audit.csv` contain the 61 manuscript references. The audit enforces exact manuscript citation coverage, unique normalized titles and DOI identifiers, metadata/ledger consistency, no placeholders, a maximum citation cluster of seven, and exact 12 same-venue + 5 influential + 5 adjacent full-paper calibration counts. Two author lists were corrected during live resolution. Publisher services are not contacted during offline reproduction; the dated live-resolution record is frozen.

## Produce and check one certificate

```sh
python src/limited.py src/certify.py data/cases/fixture-00.json /tmp/certificate.json
python src/limited.py src/checker.py data/cases/fixture-00.json /tmp/certificate.json
```

The JSON input schema and all three certificate objects are documented in the separate paper appendix and in `proofs/model-and-proofs.md`.

## Layout

- `src/`: producer, independent checker, oracle, generators, baselines, and campaign code.
- `tests/`: exhaustive, stress, protocol, external-data, metamorphic, reference, packet, reconciliation, reproduction, and accounting checks.
- `data/`: owned C sources, observations, cases, and metadata.
- `external/`: frozen public matrix slices, selection protocol, license, and source metadata.
- `results/`: retained certificates and machine-readable scientific summaries.
- `proofs/`: self-contained model and proof record.
- `literature-calibration.{md,csv}`: 22 complete-paper calibration records.
- `claim_evidence_ledger.csv`: claim-to-evidence mapping and limits.

## Scope and limitations

The certificate concerns robustness to mutant selection under one declared policy. It does not prove that the reference ranking is accurate, that a reported location caused the fault, that a developer benefits, or that mutation executions are saved. The public challenge contains only five purposively selected versions and surrogate mutant locations. The checker is independently implemented but not mechanically verified. Targeted corruptions and finite enumeration are strong implementation evidence, not exhaustive hostile-input assurance or external peer review.
