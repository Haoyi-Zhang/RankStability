#!/usr/bin/env python3
"""Independent all-subset audit of all 200 confirmatory generated programs."""
from __future__ import annotations

import csv
import json
import argparse
import sys
import time
from collections import Counter, defaultdict
from functools import cmp_to_key
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from result_io import peak_rss_kib, write_json


def require(condition: bool, message: object) -> None:
    if not condition:
        raise RuntimeError(str(message))


def solve_counts(case: dict[str, object]) -> dict[str, object]:
    n = len(case["location"])
    total_fail = sum(case["fail"])
    scores: list[tuple[int, int]] = []
    for j in range(n):
        failing_kills = sum(row[j] for row, flag in zip(case["kill"], case["fail"]) if flag)
        kills = sum(row[j] for row in case["kill"])
        scores.append((failing_kills * failing_kills, total_fail * kills) if kills else (0, 1))

    def compare(x: tuple[int, int], y: tuple[int, int]) -> int:
        delta = x[0] * y[1] - y[0] * x[1]
        return (delta > 0) - (delta < 0)

    tie = {loc: pos for pos, loc in enumerate(case["tie"])}
    reference = set(case["reference"])
    force_mask = sum(1 << j for j in case["force"])
    forbid_mask = sum(1 << j for j in case["forbid"])
    group_masks = []
    for side in ("a", "b"):
        for group, bounds in enumerate(case[f"{side}_bounds"]):
            mask = sum(1 << j for j, label in enumerate(case[side]) if label == group)
            group_masks.append((mask, bounds[0], bounds[1]))
    feasible = 0
    refuters = 0
    minimum = None
    distinct: set[tuple[int, ...]] = set()
    for mask in range(1 << n):
        size = mask.bit_count()
        if not case["size"][0] <= size <= case["size"][1]:
            continue
        if mask & force_mask != force_mask or mask & forbid_mask:
            continue
        if any(not low <= (mask & group_mask).bit_count() <= high for group_mask, low, high in group_masks):
            continue
        feasible += 1
        floor = (-1, 1) if case["empty"] == "bottom" else (0, 1)
        values = [floor] * case["locations"]
        remaining = mask
        while remaining:
            bit = remaining & -remaining
            j = bit.bit_length() - 1
            location = case["location"][j]
            if compare(scores[j], values[location]) > 0:
                values[location] = scores[j]
            remaining -= bit

        def order(a: int, b: int) -> int:
            delta = compare(values[b], values[a])
            return delta if delta else tie[a] - tie[b]

        top = tuple(sorted(sorted(range(case["locations"]), key=cmp_to_key(order))[: len(reference)]))
        distinct.add(top)
        if set(top) != reference:
            refuters += 1
            if minimum is None or size < minimum:
                minimum = size
    return {
        "status": "infeasible_policy" if not feasible else "stable" if not refuters else "counterexample",
        "minimum": minimum,
        "feasible_samples": feasible,
        "refuting_samples": refuters,
        "distinct_top_sets": len(distinct),
        "subsets": 1 << n,
    }


def run(output_dir: Path | None = None, campaign_csv: Path | None = None) -> dict[str, object]:
    begin = time.process_time()
    output_dir = ROOT / "results" if output_dir is None else output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    campaign_csv = ROOT / "results/campaign/primary.csv" if campaign_csv is None else campaign_csv
    campaign = {row["id"]: row for row in csv.DictReader(campaign_csv.open(encoding="utf-8"))}
    metadata = []
    rows = []
    family = defaultdict(Counter)
    for path in sorted((ROOT / "data/cases").glob("program-*.json")):
        case = json.loads(path.read_text())
        meta = json.loads((ROOT / "data/metadata" / path.name).read_text())
        result = solve_counts(case)
        retained = campaign[case["id"]]
        require(result["status"] == retained["status"], (case["id"], result, retained))
        retained_min = None if retained["minimum"] == "" else int(retained["minimum"])
        require(result["minimum"] == retained_min, (case["id"], result, retained_min))
        require(meta.get("protocol_role") == "confirmatory", (case["id"], meta))
        record = {
            "id": case["id"],
            "family": meta["family"],
            "variant": meta["variant"],
            **result,
            "refuter_fraction_numerator": result["refuting_samples"],
            "refuter_fraction_denominator": result["feasible_samples"],
        }
        rows.append(record)
        metadata.append(meta)
        family[meta["family"]][result["status"]] += 1
    require(len(rows) == 200, "expected all 200 generated programs")
    with (output_dir / "generated-oracle-audit.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result = {
        "cases": len(rows),
        "subsets_enumerated": sum(r["subsets"] for r in rows),
        "feasible_samples": sum(r["feasible_samples"] for r in rows),
        "refuting_samples": sum(r["refuting_samples"] for r in rows),
        "status_counts": dict(Counter(r["status"] for r in rows)),
        "minimum_counts": {str(k): v for k, v in sorted(Counter(r["minimum"] for r in rows if r["minimum"] is not None).items())},
        "family_status_counts": {name: dict(sorted(counts.items())) for name, counts in sorted(family.items())},
        "minimum_nonzero_refuter_fraction": min(
            (r["refuting_samples"] / r["feasible_samples"] for r in rows if r["refuting_samples"]),
            default=None,
        ),
        "maximum_refuter_fraction": max(
            (r["refuting_samples"] / r["feasible_samples"] for r in rows if r["feasible_samples"]),
            default=None,
        ),
        "cpu_seconds": time.process_time() - begin,
        "peak_rss_kib": peak_rss_kib(),
        "independence": "enumerates all masks and reimplements score, quota, tie, and top-set semantics without importing producer, checker, or oracle",
    }
    write_json(output_dir / "generated-oracle-audit.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    parser.add_argument("--campaign-csv", type=Path, default=ROOT / "results/campaign/primary.csv")
    args = parser.parse_args()
    print(json.dumps(run(args.output_dir, args.campaign_csv), indent=2, sort_keys=True))
