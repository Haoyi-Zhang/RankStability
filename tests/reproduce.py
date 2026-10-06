#!/usr/bin/env python3
"""Regenerate owned programs, observations, matrices, and certificates in a
clean transient directory and compare all scientific content exactly.

Only timing and peak-memory fields are excluded from cross-run equality.
Operation counters remain scientific output and must match.
"""
from __future__ import annotations

import copy
import csv
import json
import resource
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import campaign
import controls
import programs
from result_io import assert_scientific_equal, emit, output_path


def run() -> dict[str, object]:
    begin = time.process_time()
    previous_children = resource.getrusage(resource.RUSAGE_CHILDREN)
    compared = 0
    with tempfile.TemporaryDirectory(prefix="mutation-clean-") as temporary_directory:
        temporary = Path(temporary_directory)
        data = temporary / "data"
        for index in range(200):
            family, variant, ident = programs.confirmatory_design(index)
            metadata = programs.run_one(
                family,
                variant,
                data,
                ident=ident,
                protocol_role="confirmatory",
            )
            campaign.write(data / "metadata" / (metadata["id"] + ".json"), metadata)
        controls.build(data)
        replay_summary = campaign.run(data, temporary / "results")

        for section in ["programs", "observations", "cases", "metadata"]:
            expected = ROOT / "data" / section
            actual = data / section
            if {path.name for path in expected.iterdir()} != {path.name for path in actual.iterdir()}:
                raise RuntimeError(f"file-set mismatch: {section}")
            for path in expected.iterdir():
                replay = actual / path.name
                if path.suffix == ".json":
                    assert_scientific_equal(
                        json.loads(path.read_text()),
                        json.loads(replay.read_text()),
                        f"{section}/{path.name}",
                    )
                elif path.read_bytes() != replay.read_bytes():
                    raise RuntimeError(f"byte mismatch: {section}/{path.name}")
                compared += 1

        for section in ["certificates", "secondary_certificates", "details"]:
            expected = ROOT / "results/campaign" / section
            actual = temporary / "results" / section
            if {path.name for path in expected.iterdir()} != {path.name for path in actual.iterdir()}:
                raise RuntimeError(f"file-set mismatch: results/campaign/{section}")
            for path in expected.iterdir():
                assert_scientific_equal(
                    json.loads(path.read_text()),
                    json.loads((actual / path.name).read_text()),
                    f"results/campaign/{section}/{path.name}",
                )
                compared += 1

        for name in ["primary.csv", "secondary.csv"]:
            expected_rows = list(csv.DictReader((ROOT / "results/campaign" / name).open()))
            replay_rows = list(csv.DictReader((temporary / "results" / name).open()))
            assert_scientific_equal(expected_rows, replay_rows, f"results/campaign/{name}")
            compared += 1

        retained_summary = json.loads((ROOT / "results/campaign/summary.json").read_text())
        assert_scientific_equal(retained_summary, replay_summary, "results/campaign/summary.json")

        tampered = copy.deepcopy(replay_summary)
        tampered["producer"]["networks"] += 1
        try:
            assert_scientific_equal(replay_summary, tampered, "non-timing tamper probe")
        except RuntimeError:
            tamper_detected = True
        else:
            raise AssertionError("non-timing operation-count tamper was ignored")

    final_children = resource.getrusage(resource.RUSAGE_CHILDREN)
    result = {
        "scientific_files_compared": compared,
        "primary_cases": 260,
        "secondary_queries": 981,
        "program_schemas_recompiled": 220,
        "exact_observation_and_certificate_agreement": True,
        "non_timing_tamper_detection": tamper_detected,
        "cpu_seconds": (
            time.process_time()
            - begin
            + final_children.ru_utime
            - previous_children.ru_utime
            + final_children.ru_stime
            - previous_children.ru_stime
        ),
        "peak_rss_kib": max(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            final_children.ru_maxrss,
        ),
        "replay_producer": replay_summary["producer"],
        "replay_checker_steps": replay_summary["checker_steps"],
    }
    return result


if __name__ == "__main__":
    emit(output_path(ROOT / "results/clean-reproduction.json"), run())
