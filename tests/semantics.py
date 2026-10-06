#!/usr/bin/env python3
"""Finite boundary validation plus controlled schema and floor regressions."""
from __future__ import annotations

import copy
import itertools
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import certify
import checker
import oracle
from result_io import emit, output_path, peak_rss_kib


def rejected(function) -> bool:
    try:
        function()
    except (ValueError, TypeError, KeyError, IndexError):
        return True
    return False


def run() -> dict[str, object]:
    for key in certify.COUNTERS:
        certify.COUNTERS[key] = 0
    checker.STEPS = 0
    start = time.process_time()

    clauses = list(itertools.product([-1, 0, 1], repeat=2))
    formulas = 0
    for include in range(1 << len(clauses)):
        selected = [clause for j, clause in enumerate(clauses) if include >> j & 1]

        def satisfied(assignment):
            return all(
                any(sign and assignment[j] == (sign == 1) for j, sign in enumerate(clause))
                for clause in selected
            )

        assignment_results = [satisfied(assignment) for assignment in itertools.product([False, True], repeat=2)]
        sat = any(assignment_results)
        case = {
            "id": "cnf-boundary",
            "fail": [1, 0],
            "kill": [[1, 1, 0, 0], [0, 1, 0, 0]],
            "location": [0, 1, 1, 1],
            "locations": 2,
            "tie": [0, 1],
            "a": [0] * 4,
            "b": [0] * 4,
            "a_bounds": [[0, 4]],
            "b_bounds": [[0, 4]],
            "size": [0, 4],
            "force": [1],
            "forbid": [],
            "reference": [0],
            "empty": "bottom",
        }
        changes = []
        for z, x, y in itertools.product([False, True], repeat=3):
            # A generic CNF policy extension, deliberately outside the solver schema.
            if not (z or satisfied([x, y])):
                continue
            sample = [1] + ([0] if z else []) + ([2] if x else []) + ([3] if y else [])
            changes.append(set(certify.top(case, sample)) != {0})
        assert changes and any(changes) == sat
        formulas += 1

    # Direct finite validation of the three-exact-partition reduction map.
    three_partition_instances = 0
    three_partition_selections = 0
    well_formed_reduction_checks = 0
    well_formed_reduction_selections = 0

    def check_well_formed_reduction(q, triples, expected):
        nonlocal well_formed_reduction_checks, well_formed_reduction_selections
        if q == 0:
            mapped_q, mapped = 1, [(0, 0, 0)]
        elif len(triples) < q:
            mapped_q, mapped = 2, [(0, 0, 0), (0, 1, 1)]
        else:
            mapped_q, mapped = q, triples
        assert 1 <= mapped_q <= len(mapped)
        assert all(0 <= label < mapped_q for triple in mapped for label in triple)
        # Exact-one quotas and global size now obey the declared [0,n] bounds.
        feasible = False
        for choice in itertools.combinations(range(len(mapped)), mapped_q):
            well_formed_reduction_selections += 1
            if all(all(sum(mapped[i][d] == group for i in choice) == 1 for group in range(mapped_q)) for d in range(3)):
                feasible = True
                break
        assert feasible == expected
        well_formed_reduction_checks += 1

    def check_3dm(q, triples):
        nonlocal three_partition_instances, three_partition_selections
        triples = list(triples)
        matching = False
        for choice in itertools.combinations(range(len(triples)), q):
            three_partition_selections += 1
            picked = [triples[i] for i in choice]
            if all(len({triple[d] for triple in picked}) == q for d in range(3)):
                matching = True
                break
        quota = False
        for mask in range(1 << len(triples)):
            if mask.bit_count() != q:
                continue
            picked = [triples[i] for i in range(len(triples)) if mask >> i & 1]
            three_partition_selections += 1
            if all(
                all(sum(triple[d] == group for triple in picked) == 1 for group in range(q))
                for d in range(3)
            ):
                quota = True
                break
        assert matching == quota
        check_well_formed_reduction(q, triples, matching)
        three_partition_instances += 1

    universe2 = list(itertools.product(range(2), repeat=3))
    for include in range(1 << len(universe2)):
        check_3dm(2, [triple for i, triple in enumerate(universe2) if include >> i & 1])
    rng = random.Random(20260915)
    universe3 = list(itertools.product(range(3), repeat=3))
    for _ in range(64):
        check_3dm(3, [triple for triple in universe3 if rng.random() < 0.30])
    check_well_formed_reduction(0, [], True)

    regression = json.loads((Path(__file__).parent / "zero-floor-tie.json").read_text())
    certificate = certify.produce(regression)
    assert checker.check(regression, certificate) == oracle.solve(regression)[0] == "stable"

    # Six established contract-invalid inputs are exercised at both producer
    # and checker entry points.  These are six inputs and twelve rejection
    # events, not twelve distinct schema extensions.
    contract_invalid = []
    changed = copy.deepcopy(regression); changed["cnf"] = [[1]]; contract_invalid.append(changed)
    changed = copy.deepcopy(regression); changed["score"] = "MUSE"; contract_invalid.append(changed)
    changed = copy.deepcopy(regression); changed["fail"] = [0 for _ in changed["fail"]]; contract_invalid.append(changed)
    changed = copy.deepcopy(regression); changed["kill"][0][0] = 0.5; contract_invalid.append(changed)
    changed = copy.deepcopy(regression); changed["tie"] = [0] * changed["locations"]; contract_invalid.append(changed)
    changed = copy.deepcopy(regression); changed["location"][0] = [0, 1]; contract_invalid.append(changed)
    contract_rejections = 0
    for changed in contract_invalid:
        for function in (lambda x=changed: certify.produce(x), lambda x=changed: checker.check(x, certificate)):
            if not rejected(function):
                raise AssertionError("unsupported input accepted")
            contract_rejections += 1

    # Controlled regression for zero-length vectors: dict and string values
    # previously passed the checker through len()==0 and vacuous all().
    fixture13 = json.loads((ROOT / "data/cases/fixture-13.json").read_text())
    fixture13_certificate = json.loads((ROOT / "results/campaign/certificates/fixture-13.json").read_text())
    strict_inputs = []
    for field in ("location", "a", "b"):
        for replacement in ({}, ""):
            changed = copy.deepcopy(fixture13)
            changed[field] = replacement
            strict_inputs.append(changed)
    strict_entry_rejections = 0
    for changed in strict_inputs:
        for function in (
            lambda x=changed: certify.produce(x),
            lambda x=changed: checker.check(x, fixture13_certificate),
        ):
            if not rejected(function):
                raise AssertionError("non-list zero-length vector accepted")
            strict_entry_rejections += 1

    # JSON numeric equality must not let float or boolean branch labels stand in
    # for exact integer labels.
    fixture00 = json.loads((ROOT / "data/cases/fixture-00.json").read_text())
    fixture00_certificate = json.loads((ROOT / "results/campaign/certificates/fixture-00.json").read_text())
    branch_rejections = 0
    for replacement in (1.0, True):
        changed = copy.deepcopy(fixture00_certificate)
        changed["branches"][0]["branch"][2] = replacement
        if not rejected(lambda x=changed: checker.check(fixture00, x)):
            raise AssertionError("non-integer branch label accepted")
        branch_rejections += 1

    return {
        "cnf_formulas": formulas,
        "sat_assignments_enumerated": formulas * 4,
        "extended_samples_enumerated": formulas * 8,
        "three_partition_instances": three_partition_instances,
        "three_partition_selections_enumerated": three_partition_selections,
        "well_formed_three_partition_reduction_checks": well_formed_reduction_checks,
        "well_formed_reduction_selections_enumerated": well_formed_reduction_selections,
        "contract_invalid_inputs": len(contract_invalid),
        "contract_entry_rejections": contract_rejections,
        "strict_empty_vector_inputs": len(strict_inputs),
        "strict_empty_vector_entry_rejections": strict_entry_rejections,
        "branch_label_type_confusions": 2,
        "branch_label_type_rejections": branch_rejections,
        "schema_rejections": strict_entry_rejections,
        "floor_regression": "stable",
        "cpu_seconds": time.process_time() - start,
        "peak_rss_kib": peak_rss_kib(),
    }


if __name__ == "__main__":
    emit(output_path(ROOT / "results/semantics.json"), run())
