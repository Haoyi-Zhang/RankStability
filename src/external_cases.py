#!/usr/bin/env python3
"""Build the frozen result-blind external Defects4J matrix challenge cases.

The snapshots are immutable slices of a public MIT-licensed matrix corpus.  The
CSV files lack a trustworthy source-location map, so each selected mutant is a
separate location.  This is a mutant-level specialization of the general model,
not a line-level fault-localization effectiveness experiment.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import certify

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS = ROOT / "external" / "snapshots"
CASES = ROOT / "external" / "cases"
PROFILES = ("balanced", "exact", "relaxed")
EXPECTED_PROJECTS = ("Chart", "Closure", "Lang", "Math", "Time")
UPSTREAM_COMMIT = "f8d8376e0efe345161f26ff6483a404c8548fe1c"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _read_snapshot(meta_path: Path) -> tuple[dict[str, object], list[str], list[int], list[list[int]], list[str]]:
    meta = json.loads(meta_path.read_text())
    csv_path = meta_path.with_suffix(".csv")
    rows = list(csv.reader(csv_path.open(newline="")))
    require(len(rows) >= 4, f"too few rows in {csv_path.name}")
    require(rows[0][:3] == ["test_type", "test_name", "bug"], f"bad header in {csv_path.name}")
    require(rows[1][:3] == ["operator", "-", "-"], f"missing operator row in {csv_path.name}")
    operators = rows[1][3:]
    require(len(operators) == 12 and all(operators), f"operator width in {csv_path.name}")
    names: list[str] = []
    fail: list[int] = []
    kill: list[list[int]] = []
    for row in rows[2:]:
        require(len(row) == 15, f"row width in {csv_path.name}")
        require(row[0] == "dev", f"non-dev row in {csv_path.name}")
        bug = int(row[2])
        bits = [int(x) for x in row[3:]]
        require(bug in (0, 1) and all(x in (0, 1) for x in bits), f"nonbinary data in {csv_path.name}")
        names.append(row[1])
        fail.append(bug)
        kill.append(bits)
    require(len(fail) in (9, 10), f"unexpected selected test count in {csv_path.name}")
    require(sum(1 for x in fail if not x) == 8 and 1 <= sum(fail) <= 2, f"pass/fail slice in {csv_path.name}")
    require(meta["upstream_commit"] == UPSTREAM_COMMIT, f"mutable upstream reference in {meta_path.name}")
    require(meta["selected_mutant_columns"] == list(range(1, 13)), f"column protocol drift in {meta_path.name}")
    require(meta["operators"] == operators, f"operator metadata mismatch in {meta_path.name}")
    selected_fail = [name for name, flag in zip(names, fail) if flag]
    require(meta["selected_failing_tests"] == selected_fail, f"trigger metadata mismatch in {meta_path.name}")
    official = set(meta["official_triggers"])
    normalized = {name.split("__", 2)[-1] for name in selected_fail}
    require(normalized <= official, f"selected failure not in official trigger list for {meta_path.name}")
    return meta, operators, fail, kill, names


def _labels(operators: list[str]) -> tuple[list[int], list[str], list[int]]:
    order: list[str] = []
    for op in operators:
        if op not in order:
            order.append(op)
    labels = [order.index(op) for op in operators]
    populations = [labels.count(i) for i in range(len(order))]
    return labels, order, populations


def build_case(meta: dict[str, object], operators: list[str], fail: list[int], kill: list[list[int]], profile: str) -> dict[str, object]:
    require(profile in PROFILES, "unknown external policy profile")
    n = len(operators)
    a, op_order, populations = _labels(operators)
    # The second partition uses kill-density strata, not a result-dependent
    # stability label. Sort the twelve columns by total kills (then identity)
    # and split them into three equal, predeclared strata.
    kill_counts = [sum(row[j] for row in kill) for j in range(n)]
    ordered = sorted(range(n), key=lambda j: (kill_counts[j], j))
    b = [0] * n
    for rank, mutant in enumerate(ordered):
        b[mutant] = rank // 4
    seed = sorted(ordered[0:2] + ordered[4:6] + ordered[8:10])
    chosen = Counter(a[j] for j in seed)
    if profile == "balanced":
        a_bounds = [[max(0, chosen[g] - 1), min(populations[g], chosen[g] + 1)] for g in range(len(populations))]
        b_bounds = [[1, 3] for _ in range(3)]
        size = [5, 8]
    elif profile == "exact":
        a_bounds = [[chosen[g], chosen[g]] for g in range(len(populations))]
        b_bounds = [[2, 2] for _ in range(3)]
        size = [6, 6]
    else:
        a_bounds = [[0, populations[g]] for g in range(len(populations))]
        b_bounds = [[0, 4] for _ in range(3)]
        size = [4, 9]
    ident = f"{meta['id']}-{profile}"
    case: dict[str, object] = {
        "id": ident,
        "fail": fail,
        "kill": kill,
        "location": list(range(n)),
        "locations": n,
        "tie": list(range(n)),
        "a": a,
        "b": b,
        "a_bounds": a_bounds,
        "b_bounds": b_bounds,
        "size": size,
        "force": [],
        "forbid": [],
        "reference": [0, 1, 2],
        "empty": "bottom",
    }
    case["reference"] = certify.top(case, list(range(n)))
    certify.validate(case)
    require(certify.admissible(case, seed), f"seed policy infeasible for {ident}")
    case_meta = {
        "id": ident,
        "category": "external_matrix",
        "project": meta["project"],
        "bug_id": meta["bug_id"],
        "profile": profile,
        "source_snapshot": f"snapshots/{meta['id']}.csv",
        "upstream_commit": meta["upstream_commit"],
        "upstream_path": meta["path"],
        "upstream_blob": meta["blob"],
        "operator_order": op_order,
        "policy_seed_sample": seed,
        "second_partition_semantics": "three equal strata after sorting selected mutants by total kill count and identity",
        "kill_counts": kill_counts,
        "location_semantics": "one location per selected mutant because source locations are absent from the public CSV",
    }
    case["external_metadata"] = case_meta  # removed before producer input; retained by builder API only
    return case


def build_all(write: bool = True) -> list[tuple[dict[str, object], dict[str, object]]]:
    paths = sorted(SNAPSHOTS.glob("*.json"))
    require(len(paths) == 5, "expected five frozen external snapshots")
    built: list[tuple[dict[str, object], dict[str, object]]] = []
    projects: list[str] = []
    if write:
        CASES.mkdir(parents=True, exist_ok=True)
        for old in CASES.glob("*.json"):
            old.unlink()
    for path in paths:
        meta, operators, fail, kill, _ = _read_snapshot(path)
        projects.append(str(meta["project"]))
        for profile in PROFILES:
            enriched = build_case(meta, operators, fail, kill, profile)
            case_meta = enriched.pop("external_metadata")
            case = enriched
            if write:
                (CASES / f"{case['id']}.json").write_text(json.dumps(case, indent=2, sort_keys=True) + "\n")
                (CASES / f"{case['id']}.meta.json").write_text(json.dumps(case_meta, indent=2, sort_keys=True) + "\n")
            built.append((case, case_meta))
    require(tuple(projects) == EXPECTED_PROJECTS, f"project order or membership drift: {projects}")
    require(len(built) == 15, "expected fifteen external cases")
    return built


if __name__ == "__main__":
    records = build_all(write=True)
    print(json.dumps({"cases": len(records), "projects": list(EXPECTED_PROJECTS), "profiles": list(PROFILES)}, indent=2))
