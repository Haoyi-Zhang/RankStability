#!/usr/bin/env python3
"""Reconcile every paper-facing aggregate from retained scientific inputs."""
from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: object) -> None:
    if not condition:
        raise RuntimeError(str(message))


def run() -> dict[str, object]:
    result = ROOT / "results" / "campaign"
    primary = list(csv.DictReader((result / "primary.csv").open()))
    secondary = list(csv.DictReader((result / "secondary.csv").open()))
    summary = json.loads((result / "summary.json").read_text())
    stress = json.loads((ROOT / "results/stress.json").read_text())
    reference_audit = json.loads((ROOT / "results/reference-audit.json").read_text())
    protocol = json.loads((ROOT / "results/protocol-audit.json").read_text())
    generated = json.loads((ROOT / "results/generated-oracle-audit.json").read_text())
    external = json.loads((ROOT / "results/external-matrices.json").read_text())
    metamorphic = json.loads((ROOT / "results/metamorphic.json").read_text())
    cases = [json.loads(path.read_text()) for path in sorted((ROOT / "data/cases").glob("*.json"))]

    statuses = Counter(row["status"] for row in primary)
    require(len(primary) == len(cases) == 260 and len(secondary) == 981, "campaign dimensions")
    require(statuses == {"stable": 96, "counterexample": 162, "infeasible_policy": 2}, statuses)
    programs = [row for row in primary if row["category"] == "program"]
    require(len(programs) == 200, "program count")
    families = Counter((row["family"], row["status"]) for row in programs)
    expected_stable = {
        "affine": 3, "clamp": 8, "tariff": 0, "median": 9, "interval": 4,
        "predicate": 7, "accumulator": 5, "remainder": 5, "bucket": 3,
        "polynomial": 1,
    }
    for family, count in expected_stable.items():
        require(families[(family, "stable")] == count, (family, families))
        require(families[(family, "counterexample")] == 20 - count, (family, families))

    interval = sum(row["interval_result"] == "stable" for row in primary)
    random_hits = sum(row["random_result"] == "observed_counterexample" for row in primary)
    require(interval == summary["interval_stable"] == 95, interval)
    require(random_hits == summary["random_counterexamples"] == 161, random_hits)
    require(all(row["interval_result"] == "stable" for row in programs if row["status"] == "stable"), "interval coverage")
    require(all(row["random_result"] == "observed_counterexample" and row["minimum"] == "6" for row in programs if row["status"] == "counterexample"), "random refuter coverage")
    larger = sum(int(row["random_minimum"]) > int(row["minimum"]) for row in programs if row["status"] == "counterexample")
    require(larger == 11, larger)

    sizes = [int(row["certificate_bytes"]) for row in primary]
    require((min(sizes), statistics.median(sizes), max(sizes)) == (73, 844, 1552), "certificate sizes")
    entries = sum(len(case["fail"]) * len(case["location"]) for case in cases)
    require(entries == summary["matrix_entries"] == 153288, entries)
    require(max(len(case["location"]) for case in cases) == 40, "max mutants")
    require(max(len(case["fail"]) for case in cases) == 49, "max tests")
    require(max(case["locations"] for case in cases) == 6, "max locations")

    counts = Counter((row["change"], row["status"]) for row in secondary)
    expected_secondary = {
        "relax_b": (50, 208, 2), "zero_floor": (99, 159, 2),
        "k2": (65, 193, 2), "k3": (3, 198, 0),
    }
    for change, values in expected_secondary.items():
        actual = tuple(counts[(change, outcome)] for outcome in ["stable", "counterexample", "infeasible_policy"])
        require(actual == values, (change, actual, values))
    lookup = {row["id"]: row for row in primary}
    changes = [row["id"] for row in secondary if row["change"] == "relax_b" and lookup[row["id"]]["status"] == "stable" and row["status"] == "counterexample"]
    require(len(changes) == 46 and sum(lookup[item]["category"] == "program" for item in changes) == 45, changes)
    attempts = Counter(len(json.loads((ROOT / "data/metadata" / f"{row['id']}.json").read_text())["screening"]) for row in programs)
    require(attempts == {1: 196, 2: 3, 3: 1}, attempts)

    require(sum(summary["corruption_rejections"].values()) == 1436, "campaign corruptions")
    require(stress["cases"] == 2048 and stress["oracle_subset_visits"] == 383907, "stress dimensions")
    require(stress["status_counts"] == {"counterexample": 738, "infeasible_policy": 468, "stable": 842}, stress["status_counts"])
    require(stress["certificate_mutations_rejected"] == 25463, "stress corruptions")

    require(protocol["confirmatory_programs"] == 200 and protocol["development_subjects_recompiled"] == 10, protocol)
    require(19 not in protocol["confirmatory_variants_per_family"] and 20 in protocol["confirmatory_variants_per_family"], protocol)
    require(generated["cases"] == 200 and generated["subsets_enumerated"] == 6553600, generated)
    require(generated["status_counts"] == {"counterexample": 155, "stable": 45}, generated["status_counts"])
    require(generated["minimum_counts"] == {"6": 155}, generated["minimum_counts"])

    require(external["cases"] == 15 and external["all_subsets_enumerated"] == 61440, external)
    require(external["status_counts"] == {"counterexample": 15}, external["status_counts"])
    require(external["certificate_mutations_rejected"] == 90, external)
    require(external["interval_stable"] == 0 and external["random_counterexamples"] == 15, external)
    require(metamorphic["cases"] == 512 and metamorphic["metamorphic_checks"] == 2560, metamorphic)
    require(metamorphic["transformations_per_case"] == 5, metamorphic)

    require(reference_audit["references"] == 61, reference_audit)
    require(reference_audit["unique_identifiers"] == 61 and reference_audit["unique_normalized_titles"] == 61, reference_audit)
    require(reference_audit["doi_identifiers"] == 61 and reference_audit["isbn_identifiers"] == 0, reference_audit)
    require(reference_audit["calibration_counts"] == {"adjacent": 5, "influential": 5, "same-venue": 12}, reference_audit)
    require(reference_audit["placeholder_scan"] == "passed", reference_audit)
    require(reference_audit["live_resolution_rows"] == 61 and reference_audit["manuscript_cited_keys"] == 61, reference_audit)
    require(reference_audit["corrected_metadata_entries"] == ["zhang10random", "zhang13together"], reference_audit)

    for row in primary:
        if row["category"] != "fixture":
            continue
        meta = json.loads((ROOT / "data/metadata" / f"{row['id']}.json").read_text())
        require(row["status"] == meta["expected_status"], (row, meta))
        expected_minimum = "" if meta["expected_minimum"] is None else str(meta["expected_minimum"])
        require(row["minimum"] == expected_minimum, (row, meta))

    reconciled = {
        "primary_counts": dict(statuses),
        "secondary_queries": len(secondary),
        "exact_interval_stable": interval,
        "random_counterexamples": random_hits,
        "program_random_minimum_larger": larger,
        "relaxation_stable_to_refuter": len(changes),
        "matrix_entries": entries,
        "certificate_bytes_min_median_max": [min(sizes), statistics.median(sizes), max(sizes)],
        "rare_fixture_sample_space": math.comb(40, 20),
        "stress_cases": stress["cases"],
        "stress_oracle_subset_visits": stress["oracle_subset_visits"],
        "stress_certificate_mutations_rejected": stress["certificate_mutations_rejected"],
        "confirmatory_generated_cases": generated["cases"],
        "confirmatory_generated_subsets": generated["subsets_enumerated"],
        "external_cases": external["cases"],
        "external_subsets": external["all_subsets_enumerated"],
        "external_status_counts": external["status_counts"],
        "metamorphic_cases": metamorphic["cases"],
        "metamorphic_checks": metamorphic["metamorphic_checks"],
        "references": reference_audit["references"],
        "unique_reference_identifiers": reference_audit["unique_identifiers"],
        "unique_reference_titles": reference_audit["unique_normalized_titles"],
        "table_reconciliation": "passed",
    }
    (ROOT / "results/table-check.json").write_text(json.dumps(reconciled, indent=2, sort_keys=True) + "\n")
    return reconciled


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
