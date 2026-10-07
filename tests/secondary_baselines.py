#!/usr/bin/env python3
"""Frozen owned-secondary baseline comparison; no compiler or external inputs.

Plan, finite shards, and reconciliation write only explicitly new output paths.
The producer, independent checker, and both original baselines are unchanged.
"""
from __future__ import annotations
import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path
import sys
import time
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import baselines
import certify
import checker
from result_io import scientific_view

CHANGES = ("relax_b", "zero_floor", "k2", "k3")
PROTOCOL = dict(primary_order="sorted data/cases/*.json filenames", changes=list(CHANGES),
                seed="271828 + zero-based sorted primary index; same for all transformations",
                accepted_limit=64, attempts_limit=4096, secondary_queries=981,
                shard_wall_limit_seconds=120, selection="all frozen owned secondary rows")

def require(ok, message):
    if not ok:
        raise ValueError(message)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)

def save_new(path, value):
    path = Path(path).resolve()
    require(not any(path.is_relative_to((ROOT / name).resolve()) for name in
                    ("src", "tests", "data", "external", "results", "literature", "proofs", ".github")),
            "scientific inputs and retained results protected")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")

def transform(case, change):
    require(change in CHANGES, "unknown transformation")
    altered = copy.deepcopy(case)
    if change == "relax_b":
        altered["b_bounds"] = [[0, len(case["location"]) ] for _ in case["b_bounds"]]
    elif change == "zero_floor":
        altered["empty"] = "zero"  # The supplied reference intentionally stays fixed.
    else:
        k = int(change[1:])
        require(case["locations"] >= k, "unavailable top-k transformation")
        altered["reference"] = list(range(k))
        altered["reference"] = certify.top(altered, list(range(len(case["location"]))))
        independent = checker.ranked(altered, list(range(len(case["location"]))), checker.prepare(altered))
        require(set(altered["reference"]) == independent, "independent reference mismatch")
    altered["id"] += "-" + change
    checker.prepare(altered)
    return altered

def table(path, keys):
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    result = {}
    for row in rows:
        key = tuple(row[k] for k in keys)
        require(key not in result, "duplicate table row: " + str(key))
        result[key] = row
    return result

def make_plan():
    paths = sorted((ROOT / "data/cases").glob("*.json"))
    require(len(paths) == 260, "exactly 260 frozen primary inputs required")
    retained = ROOT / "results/current/owned"
    proofs = ROOT / "results/campaign"  # The retained certificate archive, not missing current copies.
    primary = table(retained / "primary.csv", ["id"])
    secondary = table(retained / "secondary.csv", ["id", "change"])
    historical = table(ROOT / "results/campaign/secondary.csv", ["id", "change"])
    require(secondary == historical and len(secondary) == 981, "frozen secondary table mismatch")
    bindings = {}
    def bound(path):
        bindings[path.relative_to(ROOT).as_posix()] = digest(path)
        return read_json(path)
    for name in ("certify", "checker", "baselines", "result_io"):
        path = ROOT / "src" / (name + ".py")
        bindings[path.relative_to(ROOT).as_posix()] = digest(path)
    for path in (retained / "primary.csv", retained / "secondary.csv", ROOT / "results/campaign/secondary.csv"):
        bindings[path.relative_to(ROOT).as_posix()] = digest(path)
    rows, primary_order = [], []
    for index, path in enumerate(paths):
        case = bound(path)
        certify.validate(case)
        metadata = bound(ROOT / "data/metadata" / path.name)
        category = metadata["category"]
        require(category in {"program", "ambiguity", "fixture"}, "non-owned input")
        primary_order.append(dict(index=index, id=case["id"], filename=path.name))
        certificate = bound(proofs / "certificates" / path.name)
        status = checker.check(case, certificate)
        old = primary[(case["id"],)]
        require((status, str(certificate.get("size", ""))) == (old["status"], old["minimum"]), "primary binding")
        for change in CHANGES:
            if change.startswith("k") and case["locations"] < int(change[1:]):
                continue
            altered = transform(case, change)
            certificate = bound(proofs / "secondary_certificates" / (altered["id"] + ".json"))
            status = checker.check(altered, certificate)
            old = secondary[(case["id"], change)]
            require((status, str(certificate.get("size", ""))) == (old["status"], old["minimum"]), "secondary binding")
            rows.append(dict(query_index=len(rows), primary_index=index, primary_id=case["id"],
                             change=change, category=category, family=metadata.get("family", category),
                             seed=271828 + index, case=altered, status=status,
                             minimum=certificate.get("size")))
    require(len(rows) == 981 and len(primary) == 260, "complete frozen cohort required")
    require(set(secondary) == {(r["primary_id"], r["change"]) for r in rows}, "exact secondary key domain")
    return dict(protocol=PROTOCOL, certificate_archive="results/campaign", primary_order=primary_order,
                bindings=bindings, rows=rows)

def validate_plan(plan):
    require(plan["protocol"] == PROTOCOL, "protocol changed")
    require(len(plan["rows"]) == 981 and len(plan["primary_order"]) == 260, "incomplete plan")
    for name, expected in plan["bindings"].items():
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT.resolve()) and digest(path) == expected, "binding mismatch: " + name)
    seen = set()
    for index, row in enumerate(plan["rows"]):
        key = (row["primary_id"], row["change"])
        require(key not in seen, "duplicate query")
        seen.add(key)
        require(row["query_index"] == index and row["seed"] == 271828 + row["primary_index"], "index/seed mismatch")
        original = read_json(ROOT / "data/cases" / plan["primary_order"][row["primary_index"]]["filename"])
        require(row["case"] == transform(original, row["change"]), "transformed case mismatch")
    require(plan == make_plan(), "plan must exactly reconstruct the frozen complete domain and bindings")

def run_shard(plan, plan_sha, start, stop):
    begin = time.monotonic()
    require(type(start) is int and type(stop) is int and 0 <= start < stop <= 981, "shard bounds")
    validate_plan(plan)
    output = []
    for row in plan["rows"][start:stop]:
        require(time.monotonic() - begin < 120, "120-second shard deadline")
        case = row["case"]
        checker.STEPS = 0
        for key in certify.COUNTERS:
            certify.COUNTERS[key] = 0
        certificate = certify.produce(case)
        status = checker.check(case, certificate)
        require((status, certificate.get("size")) == (row["status"], row["minimum"]), "fresh exact answer mismatch")
        interval = baselines.marginal(case)
        sampled = baselines.random_samples(case, row["seed"])
        require(interval["result"] != "stable" or status == "stable", "unsound marginal decision")
        require(interval["result"] != "infeasible_policy" or status == "infeasible_policy", "policy mismatch")
        require(sampled["accepted"] <= 64 and sampled["attempts"] <= 4096, "random budget changed")
        require(sampled["observed_minimum"] is None or (status == "counterexample" and sampled["observed_minimum"] >= row["minimum"]), "random answer mismatch")
        output.append(dict(**{k: v for k, v in row.items() if k != "case"},
                           certificate=certificate, interval=interval, random=sampled,
                           producer_counters=dict(certify.COUNTERS), checker_steps=checker.STEPS))
    elapsed = time.monotonic() - begin
    require(elapsed <= 120, "shard exceeded deadline")
    return dict(plan_sha256=plan_sha, start=start, stop=stop, rows=output,
                wall_seconds=elapsed, scope="frozen owned inputs; no C or external execution")

def reconcile(plan, plan_sha, shards):
    validate_plan(plan)
    rows = []
    for shard in sorted(shards, key=lambda s: s["start"]):
        require(shard["plan_sha256"] == plan_sha and shard["start"] == len(rows), "foreign/duplicate/missing shard")
        require(len(shard["rows"]) == shard["stop"] - shard["start"] and shard["wall_seconds"] <= 120, "incomplete/unbounded shard")
        rows.extend(shard["rows"])
    require(len(rows) == 981, "all 981 outcomes required")
    totals, grouped = Counter(), {}
    for expected, actual in zip(plan["rows"], rows):
        require({k: actual[k] for k in expected if k != "case"} == {k: v for k, v in expected.items() if k != "case"}, "changed row identity")
        require(checker.check(expected["case"], actual["certificate"]) == expected["status"], "invalid exact certificate")
        interval, sampled = actual["interval"], actual["random"]
        require(interval["result"] in {"stable", "unknown", "infeasible_policy"}, "unknown marginal status")
        require(interval["result"] != "stable" or expected["status"] == "stable", "unsound marginal decision")
        require((interval["result"] == "infeasible_policy") == (expected["status"] == "infeasible_policy"), "policy decision mismatch")
        require(type(sampled["accepted"]) is int and type(sampled["attempts"]) is int
                and 0 <= sampled["accepted"] <= 64 and sampled["accepted"] <= sampled["attempts"] <= 4096,
                "invalid random counters")
        require(sampled["accepted"] == 64 or sampled["attempts"] == 4096, "random stopped before fixed budget")
        require(sampled["result"] == ("unknown" if sampled["observed_minimum"] is None else "observed_counterexample"), "random status mismatch")
        require(sampled["observed_minimum"] is None or (type(sampled["observed_minimum"]) is int
                and expected["status"] == "counterexample" and sampled["observed_minimum"] >= expected["minimum"]), "random minimum mismatch")
        measures = {"queries": 1, expected["status"]: 1,
                    "interval_stable": int(actual["interval"]["result"] == "stable"),
                    "interval_infeasible": int(actual["interval"]["result"] == "infeasible_policy"),
                    "stable_beyond_interval": int(expected["status"] == "stable" and actual["interval"]["result"] == "unknown"),
                    "random_hits": int(actual["random"]["observed_minimum"] is not None),
                    "random_misses": int(expected["status"] == "counterexample" and actual["random"]["observed_minimum"] is None),
                    "random_minimum_larger": int(actual["random"]["observed_minimum"] is not None and actual["random"]["observed_minimum"] > expected["minimum"])}
        totals.update(measures)
        for key in (expected["change"], expected["category"] + ":" + expected["change"]):
            grouped.setdefault(key, Counter()).update(measures)
    return dict(protocol=PROTOCOL, plan_sha256=plan_sha, complete=True, totals=dict(totals),
                groups={k: dict(v) for k, v in sorted(grouped.items())}, rows=rows,
                scope="secondary robustness comparison; not accuracy or execution savings")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("plan"); p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("shard"); p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--start", type=int, required=True); p.add_argument("--stop", type=int, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("aggregate"); p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--shards", type=Path, nargs="+", required=True); p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("check"); p.add_argument("--evidence", type=Path, required=True)
    a = parser.parse_args()
    if a.action == "check":
        plan_path = a.evidence / "plan.json"
        result = reconcile(read_json(plan_path), digest(plan_path),
                           [read_json(p) for p in sorted(a.evidence.glob("shard-*.json"))])
        require(scientific_view(result) == scientific_view(read_json(a.evidence / "all-outcomes.json")), "stored aggregate mismatch")
        print(json.dumps(dict(complete=True, totals=result["totals"], checked_queries=981), sort_keys=True))
        return
    if a.action == "plan":
        result = make_plan()
    elif a.action == "shard":
        result = run_shard(read_json(a.plan), digest(a.plan), a.start, a.stop)
    else:
        result = reconcile(read_json(a.plan), digest(a.plan), [read_json(p) for p in a.shards])
    save_new(a.output, result)
    print(json.dumps(dict(action=a.action, output=str(a.output), queries=len(result["rows"]),
                          totals=result.get("totals")), sort_keys=True))

if __name__ == "__main__":
    main()
