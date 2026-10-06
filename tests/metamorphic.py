#!/usr/bin/env python3
"""Metamorphic invariance checks for representation-preserving transformations.

The transformations preserve the mathematical instance while changing row,
mutant, location, or group identifiers.  This suite supplements, rather than
replaces, the exhaustive oracle tests.
"""
from __future__ import annotations

import copy
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
import certify  # noqa: E402
import checker  # noqa: E402
import oracle  # noqa: E402
from stress import make_case  # noqa: E402
from result_io import output_path, peak_rss_kib, write_json

SEED = 20260921
CASES = 512


def row_permutation(c: dict, rng: random.Random) -> dict:
    d = copy.deepcopy(c)
    order = list(range(len(d["fail"])))
    rng.shuffle(order)
    d["fail"] = [d["fail"][i] for i in order]
    d["kill"] = [d["kill"][i] for i in order]
    return d


def add_zero_passing_row(c: dict) -> dict:
    d = copy.deepcopy(c)
    d["fail"].append(0)
    d["kill"].append([0] * len(d["location"]))
    return d


def mutant_permutation(c: dict, rng: random.Random) -> dict:
    d = copy.deepcopy(c)
    n = len(d["location"])
    order = list(range(n))
    rng.shuffle(order)
    old_to_new = {old: new for new, old in enumerate(order)}
    for key in ("location", "a", "b"):
        d[key] = [d[key][old] for old in order]
    d["kill"] = [[row[old] for old in order] for row in d["kill"]]
    d["force"] = sorted(old_to_new[x] for x in d["force"])
    d["forbid"] = sorted(old_to_new[x] for x in d["forbid"])
    return d


def location_relabel(c: dict, rng: random.Random) -> dict:
    d = copy.deepcopy(c)
    labels = list(range(d["locations"]))
    shuffled = labels[:]
    rng.shuffle(shuffled)
    mapping = dict(zip(labels, shuffled))
    d["location"] = [mapping[x] for x in d["location"]]
    d["tie"] = [mapping[x] for x in d["tie"]]
    d["reference"] = [mapping[x] for x in d["reference"]]
    return d


def group_relabel(c: dict, rng: random.Random) -> dict:
    d = copy.deepcopy(c)
    for side in ("a", "b"):
        groups = list(range(len(d[side + "_bounds"])))
        shuffled = groups[:]
        rng.shuffle(shuffled)
        mapping = dict(zip(groups, shuffled))
        new_bounds = [None] * len(groups)
        for old, new in mapping.items():
            new_bounds[new] = d[side + "_bounds"][old]
        d[side] = [mapping[x] for x in d[side]]
        d[side + "_bounds"] = new_bounds
    return d


def outcome(c: dict) -> tuple[str, int | None]:
    expected, minimum, _ = oracle.solve(c)
    cert = certify.produce(c)
    observed = checker.check(c, cert)
    if observed != expected:
        raise AssertionError((c["id"], observed, expected))
    if observed == "counterexample" and cert["size"] != minimum:
        raise AssertionError((c["id"], cert["size"], minimum))
    return expected, minimum


def run(output: Path | None = None) -> dict:
    begin = time.process_time()
    rng = random.Random(SEED)
    transformations = {
        "test_row_permutation": row_permutation,
        "zero_passing_row": lambda c, _rng: add_zero_passing_row(c),
        "mutant_permutation": mutant_permutation,
        "location_relabel": location_relabel,
        "partition_group_relabel": group_relabel,
    }
    checks = 0
    status_counts: dict[str, int] = {}
    for i in range(CASES):
        case = make_case(rng, 10000 + i)
        case["id"] = f"metamorphic-{i:04d}"
        baseline = outcome(case)
        status_counts[baseline[0]] = status_counts.get(baseline[0], 0) + 1
        for name, transform in transformations.items():
            changed = transform(case, rng)
            changed["id"] = case["id"] + "-" + name
            certify.validate(changed)
            if outcome(changed) != baseline:
                raise AssertionError((case["id"], name, baseline, outcome(changed)))
            checks += 1
    result = {
        "cases": CASES,
        "transformations_per_case": len(transformations),
        "metamorphic_checks": checks,
        "transformations": sorted(transformations),
        "status_counts": dict(sorted(status_counts.items())),
        "seed": SEED,
        "cpu_seconds": time.process_time() - begin,
        "peak_rss_kib": peak_rss_kib(),
        "scope": "representation-preserving metamorphic relations; not an independent proof of the algorithm",
    }
    write_json(ROOT / "results/metamorphic.json" if output is None else output, result)
    return result


if __name__ == "__main__":
    print(json.dumps(run(output_path(ROOT / "results/metamorphic.json")), indent=2, sort_keys=True))
