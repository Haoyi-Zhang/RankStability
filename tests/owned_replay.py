#!/usr/bin/env python3
"""Recompute the owned campaign from retained inputs, without compiling C.

This is a current certificate/baseline replay, not a fresh execution of the
programs that originally supplied the observations. No external matrices are
read. The original Linux reconstruction remains a separate check.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import baselines
import certify
import checker
import oracle
from result_io import write_json
from verify_all import run as verify_packet
from stress import adversarial_checks


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def run(out: Path) -> dict:
    begin = time.process_time()
    paths = sorted((ROOT / "data/cases").glob("*.json"))
    require(len(paths) == 260, "expected exactly 260 owned primary cases")
    out.mkdir(parents=True, exist_ok=True)
    primary, secondary = [], []
    counts, mutations = Counter(), 0
    for index, path in enumerate(paths):
        case = json.loads(path.read_text(encoding="utf-8"))
        meta = json.loads((ROOT / "data/metadata" / path.name).read_text(encoding="utf-8"))
        category = meta["category"]
        require(category in {"program", "ambiguity", "fixture"}, "non-owned case")
        certificate = certify.produce(case)
        status = checker.check(case, certificate)
        if "expected_status" in meta:
            require(status == meta["expected_status"], case["id"])
            require(certificate.get("size") == meta.get("expected_minimum"), case["id"])
        if category == "fixture" and len(case["location"]) <= 8:
            expected, minimum, _ = oracle.solve(case)
            require((status, certificate.get("size")) == (expected, minimum), case["id"])
        interval = baselines.marginal(case)
        random = baselines.random_samples(case, 271828 + index)
        require(interval["result"] != "stable" or status == "stable", case["id"])
        require(random["observed_minimum"] is None or (
            status == "counterexample" and random["observed_minimum"] >= certificate["size"]
        ), case["id"])
        write_json(out / "certificates" / path.name, certificate)
        mutations += adversarial_checks(case, certificate)
        counts[category + ":" + status] += 1
        primary.append(dict(
            id=case["id"], category=category, family=meta.get("family", category),
            status=status, minimum=certificate.get("size"),
            interval_result=interval["result"], random_result=random["result"],
            random_minimum=random["observed_minimum"],
            certificate_bytes=len(json.dumps(certificate, sort_keys=True, separators=(",", ":")).encode()),
        ))
        for change in ("relax_b", "zero_floor", "k2", "k3"):
            if change.startswith("k") and case["locations"] < int(change[1:]):
                continue
            altered = copy.deepcopy(case)
            if change == "relax_b":
                altered["b_bounds"] = [[0, len(case["location"])]] * len(case["b_bounds"])
            elif change == "zero_floor":
                altered["empty"] = "zero"
            else:
                altered["reference"] = list(range(int(change[1:])))
                altered["reference"] = certify.top(altered, list(range(len(case["location"]))))
            altered["id"] += "-" + change
            answer = certify.produce(altered)
            checker.check(altered, answer)
            if change == "relax_b" and status == "counterexample":
                require(answer["status"] == "counterexample" and answer["size"] <= certificate["size"], case["id"])
            secondary.append(dict(id=case["id"], change=change, status=answer["status"], minimum=answer.get("size")))
            write_json(out / "secondary_certificates" / (altered["id"] + ".json"), answer)
    require(len(secondary) == 981, "expected exactly 981 owned secondary queries")
    for name, rows in (("primary", primary), ("secondary", secondary)):
        with (out / (name + ".csv")).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    summary = dict(primary_cases=len(primary), secondary_queries=len(secondary), status_counts=dict(sorted(counts.items())))
    write_json(out / "summary.json", summary)
    verification = verify_packet(ROOT / "data", out)
    programs = [r for r in primary if r["category"] == "program"]
    result = dict(
        **summary, accepted_certificates=verification["accepted_certificates"],
        matrices_reconstructed_from_retained_observations=verification["matrices_reconstructed"],
        certificate_mutations_rejected=mutations,
        exact_interval_stable=sum(r["interval_result"] == "stable" for r in primary),
        random_counterexamples=sum(r["random_result"] == "observed_counterexample" for r in primary),
        program_random_minimum_larger=sum(r["status"] == "counterexample" and r["random_minimum"] > r["minimum"] for r in programs),
        secondary_status_counts={change: dict(Counter(r["status"] for r in secondary if r["change"] == change)) for change in ("relax_b", "zero_floor", "k2", "k3")},
        cpu_seconds=time.process_time() - begin,
        scope="current algorithms on retained owned observations; no C execution and no external data",
    )
    write_json(out / "owned-replay.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    print(json.dumps(run(parser.parse_args().output_dir), indent=2, sort_keys=True))
