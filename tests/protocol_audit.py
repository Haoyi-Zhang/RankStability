#!/usr/bin/env python3
"""Audit protocol separation and the frozen external selection contract."""
from __future__ import annotations

import csv
import json
import resource
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import external_cases  # noqa: E402
import programs  # noqa: E402


def require(condition: bool, message: object) -> None:
    if not condition:
        raise RuntimeError(str(message))


def run() -> dict[str, object]:
    begin = time.process_time()
    by_family: dict[str, set[int]] = defaultdict(set)
    primary_ids: set[str] = set()
    for path in sorted((ROOT / "data/metadata").glob("program-*.json")):
        meta = json.loads(path.read_text())
        primary_ids.add(meta["id"])
        require(meta.get("protocol_role") == "confirmatory", meta)
        by_family[meta["family"]].add(meta["variant"])
    require(len(primary_ids) == 200, "expected 200 confirmatory program ids")
    expected = set(programs.CONFIRMATORY_VARIANTS)
    for family in programs.FAMILIES:
        require(by_family[family] == expected, (family, by_family[family], expected))
        require(programs.DEVELOPMENT_VARIANT not in by_family[family], family)

    development: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="mutation-development-audit-") as td:
        out = Path(td) / "data"
        for family_index, family in enumerate(programs.FAMILIES):
            ident = f"development-{family_index:02d}"
            meta = programs.run_one(
                family_index, programs.DEVELOPMENT_VARIANT, out,
                ident=ident, protocol_role="development",
            )
            require(meta["id"] not in primary_ids, meta)
            require(meta["protocol_role"] == "development", meta)
            development.append({
                "id": ident,
                "family": family,
                "variant": meta["variant"],
                "failing_tests": meta["failing_tests"],
            })

    external = external_cases.build_all(write=True)
    manifest = list(csv.DictReader((ROOT / "external/source-provenance.csv").open()))
    require(len(manifest) == 5, "five external source rows required")
    require({row["project"] for row in manifest} == set(external_cases.EXPECTED_PROJECTS), "external project drift")
    require(all(row["upstream_commit"] == external_cases.UPSTREAM_COMMIT for row in manifest), "external commit drift")
    require(all(row["license"] == "MIT" for row in manifest), "external license metadata")
    result = {
        "confirmatory_programs": len(primary_ids),
        "families": len(by_family),
        "confirmatory_variants_per_family": sorted(expected),
        "reserved_development_variant": programs.DEVELOPMENT_VARIANT,
        "development_subjects_recompiled": len(development),
        "development_subjects": development,
        "external_snapshots": len(manifest),
        "external_cases": len(external),
        "external_projects": list(external_cases.EXPECTED_PROJECTS),
        "external_profiles": list(external_cases.PROFILES),
        "external_commit": external_cases.UPSTREAM_COMMIT,
        "cpu_seconds": time.process_time() - begin,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (ROOT / "results/protocol-audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
