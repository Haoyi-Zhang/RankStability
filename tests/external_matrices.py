#!/usr/bin/env python3
"""Exact external-matrix challenge: producer/checker/oracle plus all subsets."""
from __future__ import annotations

import copy
import csv
import json
import resource
import sys
import time
from collections import Counter
from functools import cmp_to_key
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import baselines  # noqa: E402
import certify  # noqa: E402
import checker  # noqa: E402
import external_cases  # noqa: E402
import oracle  # noqa: E402

OUT = ROOT / "results"
CERTS = ROOT / "external" / "certificates"


def require(condition: bool, message: object) -> None:
    if not condition:
        raise RuntimeError(str(message))


def exact_population(case: dict[str, object]) -> dict[str, object]:
    """Independent exhaustive semantics with no producer/checker ranking calls."""
    n = len(case["location"])
    total_fail = sum(case["fail"])
    ratios: list[tuple[int, int]] = []
    for j in range(n):
        failed_kills = sum(row[j] for row, failing in zip(case["kill"], case["fail"]) if failing)
        all_kills = sum(row[j] for row in case["kill"])
        ratios.append((failed_kills * failed_kills, total_fail * all_kills) if all_kills else (0, 1))

    def compare(x: tuple[int, int], y: tuple[int, int]) -> int:
        value = x[0] * y[1] - y[0] * x[1]
        return (value > 0) - (value < 0)

    tie = {loc: pos for pos, loc in enumerate(case["tie"])}
    reference = set(case["reference"])
    feasible = 0
    refuters = 0
    minimum = None
    distinct: set[tuple[int, ...]] = set()
    minimum_witness = None
    for mask in range(1 << n):
        selected = [j for j in range(n) if mask & (1 << j)]
        if not case["size"][0] <= len(selected) <= case["size"][1]:
            continue
        if any(not mask & (1 << j) for j in case["force"]):
            continue
        if any(mask & (1 << j) for j in case["forbid"]):
            continue
        admissible = True
        for side in ("a", "b"):
            for group, (low, high) in enumerate(case[f"{side}_bounds"]):
                count = sum(case[side][j] == group for j in selected)
                if not low <= count <= high:
                    admissible = False
                    break
            if not admissible:
                break
        if not admissible:
            continue
        feasible += 1
        floor = (-1, 1) if case["empty"] == "bottom" else (0, 1)
        values = [floor for _ in range(case["locations"])]
        for j in selected:
            location = case["location"][j]
            if compare(ratios[j], values[location]) > 0:
                values[location] = ratios[j]

        def order(a: int, b: int) -> int:
            score = compare(values[b], values[a])
            return score if score else tie[a] - tie[b]

        top = tuple(sorted(sorted(range(case["locations"]), key=cmp_to_key(order))[: len(reference)]))
        distinct.add(top)
        if set(top) != reference:
            refuters += 1
            if minimum is None or len(selected) < minimum:
                minimum = len(selected)
                minimum_witness = selected
    status = "infeasible_policy" if feasible == 0 else "stable" if refuters == 0 else "counterexample"
    return {
        "status": status,
        "minimum": minimum,
        "minimum_witness": minimum_witness,
        "feasible_samples": feasible,
        "refuting_samples": refuters,
        "refuter_fraction": [refuters, feasible] if feasible else None,
        "distinct_top_sets": len(distinct),
        "all_subsets": 1 << n,
    }


def reject_mutations(case: dict[str, object], cert: dict[str, object]) -> Counter:
    mutations: list[tuple[str, dict[str, object]]] = []
    changed = copy.deepcopy(cert)
    changed["case_id"] = "wrong-external-case"
    mutations.append(("case_binding", changed))
    changed = copy.deepcopy(cert)
    changed["unchecked_annotation"] = True
    mutations.append(("unknown_root_field", changed))
    branches = cert.get("branches", [])
    if branches:
        changed = copy.deepcopy(cert)
        changed["branches"] = changed["branches"][:-1]
        mutations.append(("branch_completeness", changed))
        changed = copy.deepcopy(cert)
        changed["branches"][0]["branch"] = [-1, -1, -1]
        mutations.append(("branch_identity", changed))
        changed = copy.deepcopy(cert)
        proof = changed["branches"][0]["proof"]
        proof.clear()
        proof.update({"kind": "cut", "vertices": []})
        mutations.append(("proof_validity", changed))
    else:
        changed = copy.deepcopy(cert)
        changed["branches"] = [{"branch": [0, 1, -1], "proof": {"kind": "cut", "vertices": []}}]
        mutations.append(("branch_completeness", changed))
    seq_key = "sample" if "sample" in cert else "base_sample" if "base_sample" in cert else None
    if seq_key and cert[seq_key]:
        changed = copy.deepcopy(cert)
        changed[seq_key] = list(changed[seq_key]) + [changed[seq_key][0]]
        mutations.append(("sample_uniqueness", changed))
    counts: Counter = Counter()
    for name, bad in mutations:
        try:
            checker.check(case, bad)
        except (ValueError, KeyError, TypeError, IndexError):
            counts[name] += 1
        else:
            raise RuntimeError(f"checker accepted external mutation {name} for {case['id']}")
    return counts


def run() -> dict[str, object]:
    begin = time.process_time()
    built = external_cases.build_all(write=True)
    CERTS.mkdir(parents=True, exist_ok=True)
    for old in CERTS.glob("*.json"):
        old.unlink()
    records: list[dict[str, object]] = []
    rejected: Counter = Counter()
    status_counts: Counter = Counter()
    profile_counts: Counter = Counter()
    total_subsets = 0
    total_feasible = 0
    total_refuters = 0
    for index, (case, meta) in enumerate(built):
        population = exact_population(case)
        oracle_status, oracle_minimum, _ = oracle.solve(case)
        require(population["status"] == oracle_status, (case["id"], population, oracle_status))
        require(population["minimum"] == oracle_minimum, (case["id"], population, oracle_minimum))
        cert = certify.produce(case)
        observed = checker.check(case, cert)
        require(observed == population["status"], (case["id"], observed, population))
        require(cert.get("size") == population["minimum"], (case["id"], cert, population))
        intervals = baselines.marginal(case)
        random = baselines.random_samples(case, 314159 + index)
        require(intervals["result"] != "stable" or observed == "stable", case["id"])
        require(random["result"] != "observed_counterexample" or observed == "counterexample", case["id"])
        rejected.update(reject_mutations(case, cert))
        (CERTS / f"{case['id']}.json").write_text(json.dumps(cert, indent=2, sort_keys=True) + "\n")
        record = {
            "id": case["id"],
            "project": meta["project"],
            "bug_id": meta["bug_id"],
            "profile": meta["profile"],
            "status": observed,
            "minimum": cert.get("size"),
            "tests": len(case["fail"]),
            "failing_tests": sum(case["fail"]),
            "mutants": len(case["location"]),
            "feasible_samples": population["feasible_samples"],
            "refuting_samples": population["refuting_samples"],
            "refuter_fraction_numerator": population["refuting_samples"],
            "refuter_fraction_denominator": population["feasible_samples"],
            "distinct_top_sets": population["distinct_top_sets"],
            "interval_result": intervals["result"],
            "random_result": random["result"],
            "random_accepted": random["accepted"],
            "random_attempts": random["attempts"],
            "random_minimum": random["observed_minimum"],
            "certificate_bytes": len(json.dumps(cert, sort_keys=True, separators=(",", ":")).encode()),
        }
        records.append(record)
        status_counts[observed] += 1
        profile_counts[(meta["profile"], observed)] += 1
        total_subsets += int(population["all_subsets"])
        total_feasible += int(population["feasible_samples"])
        total_refuters += int(population["refuting_samples"])

    csv_path = OUT / "external-matrices.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    result = {
        "protocol": "five projects x three predeclared profiles; twelve first-order mutant columns and all 4096 subsets per case",
        "cases": len(records),
        "projects": sorted({str(r["project"]) for r in records}),
        "profiles": sorted({str(r["profile"]) for r in records}),
        "status_counts": dict(sorted(status_counts.items())),
        "profile_status_counts": {f"{profile}:{status}": count for (profile, status), count in sorted(profile_counts.items())},
        "all_subsets_enumerated": total_subsets,
        "feasible_samples": total_feasible,
        "refuting_samples": total_refuters,
        "interval_stable": sum(r["interval_result"] == "stable" for r in records),
        "random_counterexamples": sum(r["random_result"] == "observed_counterexample" for r in records),
        "certificate_mutations_rejected": sum(rejected.values()),
        "rejection_categories": dict(sorted(rejected.items())),
        "cpu_seconds": time.process_time() - begin,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "records": records,
        "scope_limit": "mutant-level specialisation; no source-location map, prevalence estimate, or localization-accuracy claim",
    }
    (OUT / "external-matrices.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
