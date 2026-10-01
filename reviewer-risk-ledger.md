# Nine-perspective blind-review ledger

This is an internal adversarial review, not an external peer-review report. Scores use a 1–5 readiness scale and are accompanied by evidence and residual risk.

| Perspective | Initial concern | Repair/evidence | Residual risk | Readiness |
|---|---|---|---|---:|
| Mathematical correctness | Threshold branches might miss floor/tie cases; global minimum might be local to one branch. | Explicit floor guard; pivot/sentinel completeness theorem; common upper-bound cuts for every branch; 12,288 exhaustive cases, 2,048 stress cases, 512 CNF checks, 320 3-partition checks. | Handwritten rather than mechanized proof. | 4.4 |
| Algorithm/certificate design | Checker might merely replay producer logic or trust unchecked annotations. | Checker imports no producer/oracle/flow code, uses exact integer arithmetic, exact field whitelists, independently reconstructs cuts and samples; 26,989 targeted invalid certificates rejected across suites. | Conceptual common-mode risk remains because both implementations realize the same specification. | 4.5 |
| Software quality | Assertion-dependent tests, optimized Python, stale outputs, undocumented entry points, and JSON type confusion. | Limiter rejects `-O`; explicit list and exact-integer checks close empty-vector and branch-label gaps; 12 commands declare source/input/output bindings; all canonical outputs match same-run stdout; clean reproduction compares 2,463 files and non-timing counters. | No exhaustive hostile-input/fuzzing security guarantee or formally verified parser. | 4.4 |
| Experimental design | Ten templates and development leakage could make results overfit. | Variant 19 reserved for development; variants 0–18 and 20 confirmatory; protocol audit rejects overlap; all 6,553,600 confirmatory subsets independently enumerated. | Template families still share structure and do not represent a software population. | 4.1 |
| External validity | No public or real-project evidence. | Result-blind challenge on five Defects4J projects, immutable MIT-licensed matrix slices, 15 predeclared cases, all 61,440 subsets retained. | Mutant-level surrogate locations, only one version/project, synthetic quotas, no line-level effectiveness. | 3.6 |
| Baselines/statistics | Weak baselines or significance testing on dependent cases. | Exact attainable marginal intervals and bounded random search; finite-population exhaustive counts; no inappropriate cross-case NHST or population confidence intervals. | No alternative optimization/certification implementation from another group. | 4.2 |
| Novelty/related work | Method may be a routine combination of top-k crossing and flow; citation list could be padded. | Precise delta isolated; sharp 3-partition boundary; 12+5+5 full-paper calibration; bibliography pruned from 70 to 61 relevance-screened items; max citation cluster seven. | Magnitude of journal-level originality remains an external judgment. | 3.8 |
| Reproducibility/artifact | Narrative previously exceeded actual archive; retained summaries could be stale. | Each of 12 commands now recreates a declared canonical output and matches same-run stdout; clean reproduction is consumed by table reconciliation, matches operation counts, and detects non-timing tampering; external data and licenses remain included. | Public archive DOI and independent third-party reproduction remain external actions. | 4.7 |
| Writing/venue compliance | Overclaiming, 13-page overflow, stale reference metadata, opaque AI use. | Claims narrowed; public result reported as negative; 61 references live-resolved; two metadata corrections; exactly 12 pages without layout hacks; substantive AI-use disclosure retained. | Authors must still approve disclosures and recheck the live submission system. | 4.3 |

## Closed high-priority issues

1. **Evidence/archive mismatch:** removed unsupported claims and then added the missing external/protocol evidence before restoring them.
2. **Development leakage:** separated development variant 19 from the 200 confirmatory cases and regenerated all observations and certificates.
3. **Confirmation dependence on producer:** added an independent all-subset implementation over 6,553,600 subsets.
4. **No external data:** added a frozen, result-blind, five-project public challenge and retained its entirely negative outcomes.
5. **Reference reliability:** live-resolved every retained reference, corrected two author lists, removed a mismatched record and later pruned low-value citations, leaving 61 exact manuscript citations.
6. **Citation padding:** reduced the bibliography and bounded citation clusters instead of preserving a nominal count.
7. **Representation sensitivity:** added five metamorphic relations over 512 cases.
8. **Inappropriate statistics:** replaced implicit generalization with exact finite-population statements and explicit purposive-sample limits.
9. **Page target:** restored exactly 12 pages by pruning redundant content/references, not by shrinking fonts or margins.
10. **Floor sensitivity confound:** reran `zero_floor` with the supplied reference fixed; fixture-14 remains a size-zero refuter.
11. **Strict checker schema:** rejected float/Boolean branch labels and non-list zero-length `location`/`a`/`b` values.
12. **Stale result chain:** canonical same-run outputs, clean counter equality, and a non-timing tamper probe now guard the paper-facing summaries.

## Residual issues that cannot be honestly “fixed” inside this packet

- Natural-defect line-level accuracy and developer utility have not been measured.
- Five public versions do not estimate prevalence across Defects4J or industry.
- The proof is not mechanically verified.
- The public cases use surrogate mutant locations because the frozen matrix CSVs lack source maps.
- A public archival DOI, author approval, actual submission, and independent peer review require external action.

The manuscript treats these as boundaries, not as future-positive claims.
