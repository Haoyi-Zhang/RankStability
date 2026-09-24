# Complete-paper literature calibration

## Scope and audit rule

This ledger closes the requested **12 same-venue + 5 influential + 5 adjacent-venue** calibration for the retained internal research question. “Complete-paper calibration” means that an accessible publisher version, accepted manuscript, author manuscript, or stable full-paper deposit was traversed at section level: problem framing, definitions or mechanism, proof/evaluation design, principal results, limitations or conclusion, and reference context. It does **not** mean that every sentence was memorized, that paywalled publisher bytes are redistributed, or that citation alone proves novelty. All papers remain external; only this comparison ledger and bibliographic metadata are distributed.

The calibration outcome is deliberately negative in one important respect: the survey found a defensible restricted composition of known ideas, but no evidence that the current generated workload establishes journal-level practical superiority. The closest prior principles are necessary top-k reasoning, flow/cut duality, safe-selection style universal guarantees, mutation reduction, and certifying algorithms. The retained novelty is therefore scoped to the exact two-crossing-partition contract, its threshold/circulation reduction, globally minimum refuter packet, separately implemented checker, and the sharp NP-complete boundary at a third partition.

## Same venue: IEEE Transactions on Software Engineering (12)

### 1. An Analysis and Survey of the Development of Mutation Testing (`jia11survey`)
- **Venue/year:** IEEE Transactions on Software Engineering 37(5):649–678 (2011).
- **Full-text route:** https://doi.org/10.1109/TSE.2010.62 (published article / author technical-report route).
- **Question/principle:** Organizes mutation-testing development, operators, cost, applications, and open problems.
- **Method/proof style:** Systematic historical/taxonomic synthesis rather than a new certificate algorithm.
- **Evidence/artifact pattern:** Broad literature corpus and taxonomy; no single benchmark claim is treated as universal.
- **Narrative lesson:** Defines terms before organizing techniques by problem and historical development.
- **Exact relationship:** Supplies the field boundary. It does not ask whether one top-k location set is invariant over every quota-feasible mutant subset.

### 2. A Survey on Software Fault Localization (`wong16survey`)
- **Venue/year:** IEEE Transactions on Software Engineering 42(8):707–740 (2016).
- **Full-text route:** https://doi.org/10.1109/TSE.2016.2521368 (publisher full outline / full-paper route).
- **Question/principle:** Catalogs traditional and advanced fault-localization families, subjects, and metrics.
- **Method/proof style:** Survey synthesis with explicit evaluation dimensions.
- **Evidence/artifact pattern:** Cross-family literature, benchmark and metric comparison.
- **Narrative lesson:** Separates technique families, subjects, and evaluation measures before open issues.
- **Exact relationship:** Constrains our claims: ranking stability under a fixed matrix is not localization accuracy, developer usefulness, or a new suspiciousness family.

### 3. Using Mutation Analysis for Assessing and Comparing Testing Coverage Criteria (`andrews06coverage`)
- **Venue/year:** IEEE Transactions on Software Engineering 32(8):608–624 (2006).
- **Full-text route:** https://doi.org/10.1109/TSE.2006.83 (published article / institutional full-text route).
- **Question/principle:** Tests whether mutants support trustworthy empirical comparisons of coverage criteria.
- **Method/proof style:** Industrial subject, known faults, many mutants, statistical comparison.
- **Evidence/artifact pattern:** Real and seeded faults, coverage criteria, cost/effectiveness analysis.
- **Narrative lesson:** Motivation and validity question precede protocol and comparative results.
- **Exact relationship:** Motivates caution about what mutation evidence represents. It provides no universal guarantee over quota-constrained samples.

### 4. A Theoretical and Empirical Study of Diversity-Aware Mutation Adequacy Criterion (`shin18diversity`)
- **Venue/year:** IEEE Transactions on Software Engineering 44(10):914–931 (2018).
- **Full-text route:** https://doi.org/10.1109/TSE.2017.2732347 (published article / author replication route).
- **Question/principle:** Defines a diversity-aware adequacy objective based on distinguishing mutants.
- **Method/proof style:** Formal criterion plus empirical comparison on test suites.
- **Evidence/artifact pattern:** Replication package and empirical fault-detection/test-size outcomes.
- **Narrative lesson:** Formal definition first, then empirical questions and trade-offs.
- **Exact relationship:** Its selected object is a test suite and its objective is adequacy/diversity. Our selected object is a mutant subset and our predicate is invariance of a fixed location set.

### 5. Detecting Trivial Mutant Equivalences via Compiler Optimisations (`kintis18tce`)
- **Venue/year:** IEEE Transactions on Software Engineering 44(4):308–333 (2018).
- **Full-text route:** https://doi.org/10.1109/TSE.2017.2684805 (author full text).
- **Question/principle:** Reduces mutation cost by detecting trivial equivalent or duplicated mutants through compilation.
- **Method/proof style:** Static/compiler-based technique with empirical evaluation.
- **Evidence/artifact pattern:** Multiple programs, optimization levels, equivalent/duplicate reduction outcomes.
- **Narrative lesson:** Technique and mechanism are followed by controlled empirical assessment and limitations.
- **Exact relationship:** Column equality or compiler equivalence alone does not preserve crossing group identities, forced membership, or quota feasibility in our model.

### 6. Predictive Mutation Testing (`zhang19predictive`)
- **Venue/year:** IEEE Transactions on Software Engineering 45(9):898–918 (2019).
- **Full-text route:** https://doi.org/10.1109/TSE.2018.2809496 (UCL accepted manuscript).
- **Question/principle:** Predicts killed/survived outcomes without executing every mutant.
- **Method/proof style:** Supervised classification in cross-version and cross-project settings.
- **Evidence/artifact pattern:** 163 projects, AUC/error and efficiency trade-offs.
- **Narrative lesson:** Clearly separates prediction setting, features, scenarios, and empirical results.
- **Exact relationship:** It addresses acquisition cost by estimating missing outcomes. Our certificate assumes the entire declared matrix is fixed and exact; uncertain columns would require a different contract.

### 7. Sentinel: A Hyper-Heuristic for the Generation of Mutant Reduction Strategies (`guizzo22sentinel`)
- **Venue/year:** IEEE Transactions on Software Engineering 48(3):803–818 (2022).
- **Full-text route:** https://doi.org/10.1109/TSE.2020.3002496 (arXiv full text / published metadata).
- **Question/principle:** Automates project-specific mutant-reduction strategies under cost/effectiveness objectives.
- **Method/proof style:** Multi-objective evolutionary hyper-heuristic with empirical baselines.
- **Evidence/artifact pattern:** 40 releases of 10 systems and thousands of experiments.
- **Narrative lesson:** Research questions and objective trade-offs drive the evaluation narrative.
- **Exact relationship:** Sentinel optimizes reduction quality empirically. It does not certify that every policy-feasible sample preserves a supplied localization report.

### 8. Cerebro: Static Subsuming Mutant Selection (`garg23cerebro`)
- **Venue/year:** IEEE Transactions on Software Engineering 49(1):24–43 (2023).
- **Full-text route:** https://doi.org/10.1109/TSE.2022.3140510 (open publisher postprint).
- **Question/principle:** Selects likely subsuming mutants from surrounding code context.
- **Method/proof style:** Machine learning with cross-project evaluation in C and Java.
- **Evidence/artifact pattern:** 58 programs, subsumption/equivalence/execution-cost measures.
- **Narrative lesson:** Mechanism, learning setup, baselines and threats are explicitly separated.
- **Exact relationship:** Subsuming-mutant selection pursues testing strength and cost. Our identity-sensitive quota predicate may be broken by merging behaviorally identical mutants.

### 9. An Empirical Study of Fault Localization Families and Their Combinations (`zou21families`)
- **Venue/year:** IEEE Transactions on Software Engineering 47(2):332–347 (2021).
- **Full-text route:** https://doi.org/10.1109/TSE.2019.2892102 (author full text and tool route).
- **Question/principle:** Compares multiple localization families and their combinations on real faults.
- **Method/proof style:** Large comparative empirical study including execution cost.
- **Evidence/artifact pattern:** Real-world faults and a released combination/evaluation implementation.
- **Narrative lesson:** Family taxonomy motivates combined evaluation and measured outcomes.
- **Exact relationship:** Provides the appropriate effectiveness context. Our work fixes one score and offers no evidence of superior fault-location accuracy.

### 10. Historical Spectrum Based Fault Localization (`wen21historical`)
- **Venue/year:** IEEE Transactions on Software Engineering 47(11):2348–2368 (2021).
- **Full-text route:** https://doi.org/10.1109/TSE.2019.2948158 (institutional accepted-manuscript route).
- **Question/principle:** Uses version history to augment spectra and break suspiciousness ties.
- **Method/proof style:** History-derived model plus Defects4J evaluation.
- **Evidence/artifact pattern:** Top-k, MAP, MRR, and comparisons with several families.
- **Narrative lesson:** Motivating limitations lead to a new information source and benchmark evaluation.
- **Exact relationship:** Changes the evidence and ranking method to improve effectiveness. We hold both fixed and certify robustness only over a declared sample family.

### 11. Overcoming the Equivalent Mutant Problem: A Systematic Literature Review and a Comparative Experiment of Second Order Mutation (`madeyski14equivalent`)
- **Venue/year:** IEEE Transactions on Software Engineering 40(1):23–42 (2014).
- **Full-text route:** https://doi.org/10.1109/TSE.2013.44 (author full-text route).
- **Question/principle:** Synthesizes and compares approaches to the equivalent-mutant problem.
- **Method/proof style:** Systematic review plus controlled comparative experiment.
- **Evidence/artifact pattern:** Classified literature and second-order mutation evidence.
- **Narrative lesson:** Review protocol is made explicit before the comparative experiment.
- **Exact relationship:** Supports the warning that mutant equivalence is a separate semantic/cost issue. Our checker neither detects equivalence nor treats survival as proof of equivalence.

### 12. The ManyBugs and IntroClass Benchmarks for Automated Repair of C Programs (`legoues15manybugs`)
- **Venue/year:** IEEE Transactions on Software Engineering 41(12):1236–1256 (2015).
- **Full-text route:** https://doi.org/10.1109/TSE.2015.2454513 (published article / benchmark route).
- **Question/principle:** Builds curated C benchmarks with reproducible faults and tests.
- **Method/proof style:** Benchmark construction, characterization, and repair-tool case studies.
- **Evidence/artifact pattern:** Real faults in C projects plus reproducibility infrastructure.
- **Narrative lesson:** Benchmark definition and curation evidence precede downstream experiments.
- **Exact relationship:** Shows what a real-defect evaluation would require. Our owned generated C schemas provide pipeline assurance but are not a substitute for such a benchmark.

## Influential foundations and closest application lineage (5)

### 1. Hints on Test Data Selection: Help for the Practicing Programmer (`demillo78`)
- **Venue/year:** Computer 11(4):34–41 (1978).
- **Full-text route:** https://doi.org/10.1109/C-M.1978.218136 (publisher record / full-paper route).
- **Question/principle:** Introduces the competent-programmer and coupling intuitions behind mutation testing.
- **Method/proof style:** Conceptual argument with examples.
- **Evidence/artifact pattern:** Foundational rather than benchmark-scale evidence.
- **Narrative lesson:** Problem intuition and testing implications dominate the narrative.
- **Exact relationship:** Historical foundation only; it neither defines mutant-sampling quotas nor a checkable ranking-stability proposition.

### 2. Empirical Evaluation of the Tarantula Automatic Fault-Localization Technique (`jones05tarantula`)
- **Venue/year:** ASE 2005:273–282 (2005).
- **Full-text route:** https://doi.org/10.1145/1101908.1101949 (ACM full-text route).
- **Question/principle:** Ranks statements from passing/failing coverage spectra and evaluates debugging guidance.
- **Method/proof style:** Spectrum formula plus empirical study.
- **Evidence/artifact pattern:** Standard program suites and inspection-effort measures.
- **Narrative lesson:** Technique is motivated by visualization and evaluated through ranked inspection.
- **Exact relationship:** Defines a landmark ranking context. Our squared-Ochiai mutant score and maximum aggregation are fixed inputs, not a proposed successor to Tarantula.

### 3. On the Accuracy of Spectrum-Based Fault Localization (`abreu07ochiai`)
- **Venue/year:** TAICPART-MUTATION 2007:89–98 (2007).
- **Full-text route:** https://doi.org/10.1109/TAIC.PART.2007.13 (publisher/author full-text route).
- **Question/principle:** Compares similarity coefficients, including Ochiai, for fault localization.
- **Method/proof style:** Empirical formula comparison.
- **Evidence/artifact pattern:** Benchmark faults and ranking accuracy.
- **Narrative lesson:** A focused formula question leads directly to comparative results.
- **Exact relationship:** Supplies the score family we freeze. It does not address sample-family quantification or certificate checking.

### 4. Metallaxis-FL: Mutation-Based Fault Localization (`metallaxis`)
- **Venue/year:** Software Testing, Verification and Reliability 25(5–7):605–628 (2015).
- **Full-text route:** https://doi.org/10.1002/stvr.1509 (publisher full text).
- **Question/principle:** Links mutant behavior to faulty program locations for localization.
- **Method/proof style:** Mutation-based suspiciousness with empirical and controlled evaluation.
- **Evidence/artifact pattern:** Program subjects, cost-reduction settings and localization outcomes.
- **Narrative lesson:** Method, experiments and practical implications are clearly separated.
- **Exact relationship:** The closest application lineage. We preserve its kind of mutant evidence but study a post-hoc universal robustness question, not a new localization score.

### 5. Ask the Mutants: Mutating Faulty Programs for Fault Localization (`moon14muse`)
- **Venue/year:** ICST 2014:153–162 (2014).
- **Full-text route:** https://doi.org/10.1109/ICST.2014.28 (publisher/author full-text route).
- **Question/principle:** Uses behavioral changes from mutating faulty programs to localize faults.
- **Method/proof style:** Mutation-based method with comparative evaluation.
- **Evidence/artifact pattern:** Benchmark programs and ranking outcomes.
- **Narrative lesson:** Assumption, technique, evaluation and comparison form a concise conference narrative.
- **Exact relationship:** Demonstrates that mutation-localization semantics differ across methods. Our certificate is tied to the supplied binary kill matrix and does not generalize to repair-oriented observations.

## Adjacent venues and methodological controls (5)

### 1. Evaluating and Improving Fault Localization (`pearson17`)
- **Venue/year:** ICSE 2017:609–620 (2017).
- **Full-text route:** https://doi.org/10.1109/ICSE.2017.62 (author full text).
- **Question/principle:** Reassesses localization techniques and improves evaluation realism.
- **Method/proof style:** Large comparative evaluation with explicit fault spaces and metrics.
- **Evidence/artifact pattern:** Real faults, multiple families, released infrastructure.
- **Narrative lesson:** Starts from evaluation weaknesses, then reports corrected comparisons.
- **Exact relationship:** Directly motivates our narrow nonclaims: finite ranking invariance cannot be interpreted as real-fault effectiveness.

### 2. Transforming Programs and Tests in Tandem for Fault Localization (`li17tandem`)
- **Venue/year:** Proceedings of the ACM on Programming Languages 1(OOPSLA), Article 92 (2017).
- **Full-text route:** https://doi.org/10.1145/3133916 (ACM full text).
- **Question/principle:** Transforms programs and tests together to expose better localization signals.
- **Method/proof style:** Semantics-aware transformations and empirical evaluation.
- **Evidence/artifact pattern:** Benchmark defects and localization improvements.
- **Narrative lesson:** Formal transformation intuition is connected to an empirical pipeline.
- **Exact relationship:** Changes program/test evidence to improve ranking. Our problem is post-observation and leaves programs, tests and scores unchanged.

### 3. Are Mutation Scores Correlated with Real Fault Detection? (`papadakis18correlation`)
- **Venue/year:** ICSE 2018:537–548 (2018).
- **Full-text route:** https://doi.org/10.1145/3180155.3180183 (author full text).
- **Question/principle:** Separates mutation score, test-suite size and real-fault detection relationships.
- **Method/proof style:** Large-scale empirical correlation/causal-control analysis.
- **Evidence/artifact pattern:** Real faults, mutants and test suites at scale.
- **Narrative lesson:** Claims are qualified by confounding and validity analysis.
- **Exact relationship:** Supports our refusal to infer fault-detection quality from an exact matrix certificate.

### 4. Evaluating the Impact of Experimental Assumptions in Automated Fault Localization (`soremekun23assumptions`)
- **Venue/year:** ICSE 2023:159–171 (2023).
- **Full-text route:** https://doi.org/10.1109/ICSE48619.2023.00025 (author full text).
- **Question/principle:** Measures how patch/root-cause and evaluation assumptions change localization conclusions.
- **Method/proof style:** Controlled re-evaluation under multiple assumptions.
- **Evidence/artifact pattern:** Real faults and sensitivity of reported effectiveness.
- **Narrative lesson:** Assumptions are made first-class experimental factors.
- **Exact relationship:** Motivates explicit tie, floor, reference-set and corpus assumptions and prevents us from presenting one operationalization as universal debugging utility.

### 5. Certifying Algorithms (`mcconnell11certifying`)
- **Venue/year:** Computer Science Review 5(2):119–161 (2011).
- **Full-text route:** https://doi.org/10.1016/j.cosrev.2010.09.009 (publisher/author full-text route).
- **Question/principle:** Surveys algorithms that return easily checked witnesses of correctness.
- **Method/proof style:** Theory and design principles with examples across algorithmic problems.
- **Evidence/artifact pattern:** Proof objects and independent checker patterns rather than a software-debugging corpus.
- **Narrative lesson:** Separates producer complexity from simple verification obligations.
- **Exact relationship:** Provides the certificate design lens. Our contribution is a problem-specific branch/cut packet and checker, not a new general certification framework.


## Recent closest-work metadata supplement (7 peer-reviewed papers)

These seven papers are not counted again in the fixed 12+5+5 calibration matrix. They were added after the inherited calibration to close the recency gap in the mutation-based fault-localization comparison. Publisher or DBLP metadata and stable identifiers were freshly cross-checked on 2026-09-16; the distributed provenance ledger records every bibliography entry separately.

| Key | Year/venue | Main objective | Exact delta from this work |
|---|---|---|---|
| `li20hmer` | 2020, JSS | Reduce mutant and mutant--test execution cost while retaining localization accuracy | Optimizes acquisition cost empirically; does not quantify every quota-feasible sample or return a minimum ranking-changing sample. |
| `kim21simfl` | 2021, ISSRE | Reuse ahead-of-time mutation evidence through statistical inference | Predicts fault location from historical mutation outcomes; our contract assumes a fixed exact current matrix and certifies a supplied set. |
| `jang22hotfuz` | 2022, STVR | Use higher-order mutants to reduce MBFL cost | Changes the mutant representation and cost/accuracy trade-off; our method does not generate or combine mutants. |
| `du22bias` | 2022, ISSRE | Improve MBFL performance by addressing mutant bias | Changes the scoring/effectiveness mechanism; our score and aggregation are frozen. |
| `kim23relationship` | 2023, IST | Extend SIMFL with learned test--mutant relationships and redundancy analysis | Learns from historical or predicted evidence; no universal subset-invariance certificate is supplied. |
| `liu24delta4ms` | 2024, STVR | Correct mutant bias using signal-based reasoning and higher-order mutants | Proposes a different suspiciousness model and evaluates accuracy; our theorem is conditional on one supplied score table. |
| `wang25formulae` | 2025, STVR | Systematically transform and compare MBFL formulae and introduce weighted treatment of mutants | Broadens and evaluates formula choices; our question starts only after a formula, matrix, tie order, floor, and policy are fixed. |

The supplement strengthens the negative novelty test: recent MBFL work mainly changes evidence acquisition, mutant construction, weighting, or the suspiciousness model. None of these records, as calibrated here, supplies the retained three-way outcome---nonvacuous invariance certificate, globally minimum admissible refuter with a checked lower bound, or policy-infeasibility certificate---for two crossing quota partitions.

## Cross-paper conclusions

1. **The score is not the contribution.** Mutation-based and spectrum-based localization already contain extensive score, aggregation, selection, and effectiveness research. The present paper must continue to frame squared Ochiai and maximum-by-location as fixed semantics.
2. **Reduction is not preservation.** Equivalence, subsumption, prediction, diversity, and hyper-heuristic reduction optimize different objectives. None alone proves preservation of identity-sensitive crossing quotas and a top-k set.
3. **Universal guarantees require a declared world family.** Safe selection and certifying-algorithm work support the form of the question and the producer/checker split, but not this particular network encoding or its software interpretation.
4. **Real-fault usefulness remains open.** Same-venue and adjacent empirical work uses public real-fault benchmarks, multiple systems, developer studies, or large comparative designs. The current ten-template corpus is assurance evidence, not an external-validity substitute.
5. **The sharpest defensible theoretical delta is the boundary.** Two crossing partition systems admit the flow certificate used here; with three exact-one partition systems, policy feasibility already captures perfect three-dimensional matching and is NP-complete. This is a policy-feasibility boundary, not evidence that practical instances are hard.

## Integration decisions

- The paper bibliography contains exactly 61 relevance-screened scholarly items, but the 22 papers above are the explicit calibration sample.
- Main-text related work compares objectives and certified propositions rather than listing papers chronologically.
- Detailed corpus, family, sensitivity, and resource tables are kept in the separate appendix so the 12-page main paper can retain a normal bibliography without changing publisher fonts, margins, or spacing.
- No paper PDF is copied into the repository. URLs are provenance only; downstream users must follow the source license and access terms.
