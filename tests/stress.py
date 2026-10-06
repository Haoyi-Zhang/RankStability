#!/usr/bin/env python3
"""Deterministic oracle stress and certificate-adversary suite.

This suite is independent of the campaign generator.  For each small random
instance it compares the producer and checker with exhaustive enumeration, then
applies certificate mutations that must be rejected.  The finite run is not a
mechanized proof of the general theorems.
"""
from __future__ import annotations

import copy
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from result_io import emit, output_path, peak_rss_kib
import certify  # noqa: E402
import checker  # noqa: E402
import oracle  # noqa: E402

SEED = 20260916
CASES = 2048


def make_case(rng: random.Random, i: int) -> dict:
    n = rng.randint(0, 10)
    tests = rng.randint(1, 6)
    locations = rng.randint(1, 6)
    fail = [rng.randrange(2) for _ in range(tests)]
    if not any(fail):
        fail[rng.randrange(tests)] = 1

    a_groups = rng.randint(1, min(4, max(1, n + 1)))
    b_groups = rng.randint(1, min(4, max(1, n + 1)))
    a = [rng.randrange(a_groups) for _ in range(n)]
    b = [rng.randrange(b_groups) for _ in range(n)]

    def bounds(groups: int) -> list[list[int]]:
        result = []
        for _ in range(groups):
            lo = rng.randint(0, n)
            hi = rng.randint(lo, n)
            result.append([lo, hi])
        return result

    size_lo = rng.randint(0, n)
    size_hi = rng.randint(size_lo, n)
    order = list(range(n))
    rng.shuffle(order)
    force_count = rng.randint(0, min(2, n))
    force = sorted(order[:force_count])
    remaining = order[force_count:]
    forbid_count = rng.randint(0, min(2, len(remaining)))
    forbid = sorted(remaining[:forbid_count])

    tie = list(range(locations))
    rng.shuffle(tie)
    k = rng.randint(1, min(4, locations))
    reference = rng.sample(range(locations), k)

    case = {
        "id": f"stress-{i:04d}",
        "fail": fail,
        "kill": [[rng.randrange(2) for _ in range(n)] for _ in range(tests)],
        "location": [rng.randrange(locations) for _ in range(n)],
        "locations": locations,
        "tie": tie,
        "a": a,
        "b": b,
        "a_bounds": bounds(a_groups),
        "b_bounds": bounds(b_groups),
        "size": [size_lo, size_hi],
        "force": force,
        "forbid": forbid,
        "reference": reference,
        "empty": rng.choice(["bottom", "zero"]),
    }

    # Deterministic mixture of broad, tight, contradictory, and fixed policies.
    mode = i % 8
    if mode == 0:
        case["a_bounds"] = [[0, n] for _ in range(a_groups)]
        case["b_bounds"] = [[0, n] for _ in range(b_groups)]
        case["size"] = [0, n]
        case["force"] = []
        case["forbid"] = []
    elif mode == 1:
        target = rng.randint(0, n)
        case["a_bounds"] = [[0, n] for _ in range(a_groups)]
        case["b_bounds"] = [[0, n] for _ in range(b_groups)]
        case["size"] = [target, target]
        case["force"] = []
        case["forbid"] = []
    elif mode == 2:
        # Guaranteed policy contradiction, including the n=0 boundary.
        case["a_bounds"][0] = [min(1, n), min(1, n)]
        if n == 0:
            case["a_bounds"][0] = [0, 0]
            case["size"] = [0, 0]
            case["force"] = []
            case["forbid"] = []
            case["b_bounds"][0] = [0, 0]
            # Reference can still disagree with the unique empty-sample ranking.
        else:
            members = [j for j, g in enumerate(a) if g == 0]
            case["forbid"] = sorted(set(case["forbid"]) | set(members))
            case["force"] = [j for j in case["force"] if j not in case["forbid"]]
    elif mode == 3:
        # Fully fixed membership gives exactly one admissible subset.
        fixed = set(rng.sample(range(n), rng.randint(0, n)))
        case["force"] = sorted(fixed)
        case["forbid"] = sorted(set(range(n)) - fixed)
        case["size"] = [len(fixed), len(fixed)]
        case["a_bounds"] = [[sum(a[j] == g for j in fixed)] * 2 for g in range(a_groups)]
        case["b_bounds"] = [[sum(b[j] == g for j in fixed)] * 2 for g in range(b_groups)]
    elif mode == 4:
        # A positive quota whose entire group is forbidden is infeasible.
        if n:
            group = rng.randrange(a_groups)
            members = [j for j, g in enumerate(a) if g == group]
            case["a_bounds"] = [[0, n] for _ in range(a_groups)]
            case["b_bounds"] = [[0, n] for _ in range(b_groups)]
            case["a_bounds"][group] = [1, n]
            case["forbid"] = sorted(set(case["forbid"]) | set(members))
            case["force"] = [j for j in case["force"] if j not in case["forbid"]]
    elif mode == 5:
        # Force and cardinality determine one feasible sample.
        chosen = sorted(rng.sample(range(n), rng.randint(0, n)))
        case["force"] = chosen
        case["forbid"] = sorted(set(range(n)) - set(chosen))
        case["size"] = [len(chosen), len(chosen)]
        case["a_bounds"] = [[sum(a[j] == g for j in chosen)] * 2 for g in range(a_groups)]
        case["b_bounds"] = [[sum(b[j] == g for j in chosen)] * 2 for g in range(b_groups)]
    elif mode == 6:
        # All locations in the reference: no outsider branches are expected.
        case["reference"] = list(range(locations))
        case["a_bounds"] = [[0, n] for _ in range(a_groups)]
        case["b_bounds"] = [[0, n] for _ in range(b_groups)]
        case["size"] = [0, n]
        case["force"] = []
        case["forbid"] = []
    elif mode == 7:
        # Exact crossed counts induced by a witness are guaranteed feasible.
        chosen = sorted(rng.sample(range(n), rng.randint(0, n)))
        case["size"] = [len(chosen), len(chosen)]
        case["force"] = []
        case["forbid"] = []
        case["a_bounds"] = [[sum(a[j] == g for j in chosen)] * 2 for g in range(a_groups)]
        case["b_bounds"] = [[sum(b[j] == g for j in chosen)] * 2 for g in range(b_groups)]

    return case


def expect_reject(case: dict, mutated: dict) -> None:
    try:
        checker.check(case, mutated)
    except (ValueError, KeyError, TypeError, IndexError):
        return
    raise AssertionError("mutated certificate accepted: " + json.dumps(mutated, sort_keys=True))


def mutate_proof(case: dict, cert: dict, proof_path: list) -> int:
    """Apply guaranteed-invalid proof changes; return the number tested."""
    count = 0

    def get_parent(obj, path):
        for key in path[:-1]:
            obj = obj[key]
        return obj, path[-1]

    parent, key = get_parent(cert, proof_path)
    proof = parent[key]

    bad = copy.deepcopy(cert)
    p_parent, p_key = get_parent(bad, proof_path)
    p_parent[p_key]["kind"] = "not-a-proof"
    expect_reject(case, bad)
    count += 1

    bad = copy.deepcopy(cert)
    p_parent, p_key = get_parent(bad, proof_path)
    p_parent[p_key]["unchecked_annotation"] = 1
    expect_reject(case, bad)
    count += 1

    if proof.get("kind") == "interval":
        bad = copy.deepcopy(cert)
        p_parent, p_key = get_parent(bad, proof_path)
        p_parent[p_key]["edge"] = -1
        expect_reject(case, bad)
        count += 1
    elif proof.get("kind") == "cut":
        vertices = proof.get("vertices", [])
        if vertices:
            bad = copy.deepcopy(cert)
            p_parent, p_key = get_parent(bad, proof_path)
            p_parent[p_key]["vertices"] = vertices + [vertices[0]]
            expect_reject(case, bad)
            count += 1
        # Reconstructed network has ordinary vertices 0..nv-1, then ss=nv,
        # tt=nv+1.  Removing ss or adding tt violates the terminal condition.
        nv = 2 + len(case["a_bounds"]) + len(case["b_bounds"])
        bad = copy.deepcopy(cert)
        p_parent, p_key = get_parent(bad, proof_path)
        p_parent[p_key]["vertices"] = [v for v in vertices if v != nv]
        expect_reject(case, bad)
        count += 1

        bad = copy.deepcopy(cert)
        p_parent, p_key = get_parent(bad, proof_path)
        p_parent[p_key]["vertices"] = list(dict.fromkeys(vertices + [nv + 1]))
        expect_reject(case, bad)
        count += 1
    else:
        raise AssertionError("producer emitted unknown proof kind")
    return count


def adversarial_checks(case: dict, cert: dict) -> int:
    count = 0

    bad = copy.deepcopy(cert)
    bad["case_id"] = case["id"] + "-wrong"
    expect_reject(case, bad)
    count += 1

    bad = copy.deepcopy(cert)
    bad["status"] = "unknown-status"
    expect_reject(case, bad)
    count += 1

    bad = copy.deepcopy(cert)
    bad["unchecked_annotation"] = "must not be silently accepted"
    expect_reject(case, bad)
    count += 1

    bad = copy.deepcopy(cert)
    del bad["status"]
    expect_reject(case, bad)
    count += 1

    status = cert["status"]
    n = len(case["location"])
    if status == "infeasible_policy":
        bad = copy.deepcopy(cert)
        del bad["proof"]
        expect_reject(case, bad)
        count += 1
        count += mutate_proof(case, cert, ["proof"])
        return count

    # Flip the status without supplying the obligations for the other outcome.
    bad = copy.deepcopy(cert)
    bad["status"] = "counterexample" if status == "stable" else "stable"
    expect_reject(case, bad)
    count += 1

    sample_field = "base_sample" if status == "stable" else "sample"
    sample = cert[sample_field]

    bad = copy.deepcopy(cert)
    del bad[sample_field]
    expect_reject(case, bad)
    count += 1

    bad = copy.deepcopy(cert)
    if sample:
        bad[sample_field] = sample + [sample[0]]
    else:
        bad[sample_field] = [n]  # always outside 0..n-1, including n=0
    expect_reject(case, bad)
    count += 1

    bad = copy.deepcopy(cert)
    bad[sample_field] = list(sample) + [n]
    expect_reject(case, bad)
    count += 1

    if status == "counterexample":
        bad = copy.deepcopy(cert)
        bad["size"] = cert["size"] + 1
        expect_reject(case, bad)
        count += 1

        bad = copy.deepcopy(cert)
        del bad["size"]
        expect_reject(case, bad)
        count += 1

    records = cert["branches"]
    if records:
        bad = copy.deepcopy(cert)
        bad["branches"] = bad["branches"][:-1]
        expect_reject(case, bad)
        count += 1

        bad = copy.deepcopy(cert)
        bad["branches"][0]["branch"] = [999, 999, 999]
        expect_reject(case, bad)
        count += 1

        bad = copy.deepcopy(cert)
        bad["branches"][0]["unchecked_annotation"] = 1
        expect_reject(case, bad)
        count += 1

        count += mutate_proof(case, cert, ["branches", 0, "proof"])

        if len(records) >= 2:
            bad = copy.deepcopy(cert)
            bad["branches"][0], bad["branches"][1] = bad["branches"][1], bad["branches"][0]
            expect_reject(case, bad)
            count += 1
    else:
        bad = copy.deepcopy(cert)
        bad["branches"] = [{"branch": [0, 0, -1], "proof": {"kind": "not-a-proof"}}]
        expect_reject(case, bad)
        count += 1

    return count


def run() -> dict:
    start = time.process_time()
    rng = random.Random(SEED)
    statuses = Counter()
    proof_kinds = Counter()
    subset_visits = 0
    mutation_rejections = 0
    maximum_branches = 0
    empty_universes = 0

    # Global counters are process-wide. Reset them to make the report self-contained.
    for key in certify.COUNTERS:
        certify.COUNTERS[key] = 0
    checker.STEPS = 0

    for i in range(CASES):
        case = make_case(rng, i)
        if not case["location"]:
            empty_universes += 1
        subset_visits += 1 << len(case["location"])

        expected, minimum, witness = oracle.solve(case)
        cert = certify.produce(case)
        observed = checker.check(case, cert)
        assert observed == expected, (case, cert, expected, witness)
        if observed == "counterexample":
            assert cert["size"] == minimum
            assert certify.admissible(case, cert["sample"])
            assert set(certify.top(case, cert["sample"])) != set(case["reference"])
        elif observed == "stable":
            assert certify.admissible(case, cert["base_sample"])
        statuses[observed] += 1
        maximum_branches = max(maximum_branches, len(cert.get("branches", [])))
        if cert.get("proof"):
            proof_kinds[cert["proof"]["kind"]] += 1
        for record in cert.get("branches", []):
            proof_kinds[record["proof"]["kind"]] += 1

        mutation_rejections += adversarial_checks(case, cert)

    return {
        "cases": CASES,
        "seed": SEED,
        "oracle_subset_visits": subset_visits,
        "empty_mutant_universes": empty_universes,
        "status_counts": dict(sorted(statuses.items())),
        "proof_kind_counts": dict(sorted(proof_kinds.items())),
        "maximum_branches": maximum_branches,
        "certificate_mutations_rejected": mutation_rejections,
        "producer": dict(certify.COUNTERS),
        "checker_steps": checker.STEPS,
        "cpu_seconds": time.process_time() - start,
        "peak_rss_kib": peak_rss_kib(),
        "workers": 1,
    }


if __name__ == "__main__":
    emit(output_path(Path(__file__).resolve().parents[1]/"results"/"stress.json"),run())
