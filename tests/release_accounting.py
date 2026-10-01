#!/usr/bin/env python3
"""Run the documented public entry points sequentially and bind each command's
source, declared inputs, stdout, and canonical result file from the same run.

The accounting is command-level scientific evidence, not a toolchain
fingerprint or whole-research lifetime reconstruction.
"""
from __future__ import annotations

import copy
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from result_io import assert_scientific_equal, write_json

OUT_JSON = ROOT / "results/release-reproduction-accounting.json"
OUT_CSV = ROOT / "results/release-reproduction-accounting.csv"
RESOURCE_JSON = ROOT / "results/resource-accounting.json"


def parse_time(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    values: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if ": " in stripped:
            key, value = stripped.rsplit(": ", 1)
            values[key.strip()] = value.strip()
    required = [
        "User time (seconds)",
        "System time (seconds)",
        "Maximum resident set size (kbytes)",
        "Exit status",
    ]
    missing = [field for field in required if field not in values]
    if missing:
        raise RuntimeError(f"unparsed resource fields {missing}")
    return {
        "user_seconds": float(values["User time (seconds)"]),
        "system_seconds": float(values["System time (seconds)"]),
        "max_rss_kib": int(values["Maximum resident set size (kbytes)"]),
        "time_exit_status": int(values["Exit status"]),
        "elapsed_reported": values.get("Elapsed (wall clock) time (h:mm:ss or m:ss)", ""),
    }


def load_commands() -> list[dict[str, object]]:
    data = json.loads((ROOT / "public_commands.json").read_text())
    if len(data) != len({item["name"] for item in data}):
        raise RuntimeError("duplicate public command name")
    if len(data) != len({item["output"] for item in data}):
        raise RuntimeError("duplicate public command output")
    required = {"name", "source", "argv", "inputs", "output", "purpose"}
    for item in data:
        if set(item) != required:
            raise RuntimeError(f"public command fields: {item.get('name')}")
        if not isinstance(item["argv"], list) or not item["argv"] or not all(isinstance(value, str) and value for value in item["argv"]):
            raise RuntimeError(f"invalid argv declaration: {item.get('name')}")
        if item["argv"][0] != "src/limited.py" or item["source"] not in item["argv"]:
            raise RuntimeError(f"source/argv binding: {item.get('name')}")
        if not isinstance(item["inputs"], list) or not item["inputs"]:
            raise RuntimeError(f"invalid input declaration: {item.get('name')}")
        source = (ROOT / str(item["source"])).resolve()
        if not source.is_file():
            raise RuntimeError(f"missing command source: {item['source']}")
        for declared in item["inputs"]:
            path = (ROOT / str(declared)).resolve()
            if not path.exists():
                raise RuntimeError(f"missing declared input for {item['name']}: {declared}")
        output = (ROOT / str(item["output"])).resolve()
        if ROOT.resolve() not in output.parents:
            raise RuntimeError(f"output escapes artifact root: {item['output']}")
    return data


def run() -> dict[str, object]:
    if not Path("/usr/bin/time").is_file():
        raise SystemExit("release accounting requires /usr/bin/time")
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    records: list[dict[str, object]] = []
    saved_outputs: dict[str, dict[str, object]] = {}
    commands = load_commands()

    with tempfile.TemporaryDirectory(prefix="mutation-release-time-") as temporary_directory:
        folder = Path(temporary_directory)
        for index, item in enumerate(commands, start=1):
            name = str(item["name"])
            relative = [str(value) for value in item["argv"]]
            output_path = ROOT / str(item["output"])
            if output_path.exists():
                output_path.unlink()
            time_path = folder / f"{index:02d}-{name}.time"
            command = [sys.executable, *relative]
            wrapped = ["/usr/bin/time", "-v", "-o", str(time_path), *command]
            start = time.perf_counter()
            process = subprocess.run(
                wrapped,
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                timeout=3000,
                check=False,
            )
            wall = time.perf_counter() - start
            timing = parse_time(time_path)
            try:
                stdout_json = json.loads(process.stdout)
            except json.JSONDecodeError as error:
                raise RuntimeError(f"{name} did not emit one JSON result: {error}") from error
            if process.returncode != 0 or timing["time_exit_status"] != 0:
                raise RuntimeError(f"{name} failed with {process.returncode}:\n{process.stderr[-4000:]}")
            if not output_path.is_file():
                raise RuntimeError(f"{name} did not create declared output {item['output']}")
            saved_json = json.loads(output_path.read_text())
            if stdout_json != saved_json:
                raise RuntimeError(f"{name} stdout differs from its same-run canonical output")
            saved_outputs[name] = saved_json
            record = {
                "ordinal": index,
                "name": name,
                "source": item["source"],
                "inputs": item["inputs"],
                "output": item["output"],
                "purpose": item["purpose"],
                "command": " ".join(["python", *relative]),
                "returncode": process.returncode,
                "wall_seconds": wall,
                **timing,
                "stdout_bytes": len(process.stdout.encode()),
                "stderr_bytes": len(process.stderr.encode()),
                "stdout_json": stdout_json,
                "same_run_output_match": True,
            }
            records.append(record)

    clean = saved_outputs["clean_reproduction"]
    tampered = copy.deepcopy(clean)
    tampered["replay_producer"]["networks"] += 1
    try:
        assert_scientific_equal(clean, tampered, "release non-timing tamper probe")
    except RuntimeError:
        tamper_detection = True
    else:
        raise RuntimeError("non-timing result tamper was not detected")

    total_user = sum(float(record["user_seconds"]) for record in records)
    total_system = sum(float(record["system_seconds"]) for record in records)
    summary = {
        "commands": len(records),
        "successful_commands": sum(record["returncode"] == 0 for record in records),
        "user_seconds_sum": total_user,
        "system_seconds_sum": total_system,
        "cpu_seconds_sum": total_user + total_system,
        "wall_seconds_sum": sum(float(record["wall_seconds"]) for record in records),
        "largest_command_max_rss_kib": max(int(record["max_rss_kib"]) for record in records),
        "workers": 1,
        "same_run_outputs_verified": sum(bool(record["same_run_output_match"]) for record in records),
        "non_timing_tamper_detection": tamper_detection,
    }
    result = {
        "scope": "one fresh sequential pass over all documented scientific entry points",
        "not_scope": "whole research-lifetime accounting or a toolchain/environment fingerprint",
        "measurement_tool": "GNU /usr/bin/time -v; each scientific command executes through src/limited.py",
        "binding": "public_commands.json declares each entry source, consumed inputs, and canonical output; every command must recreate that output and match stdout in the same pass",
        "commands": records,
        "summary": summary,
    }
    write_json(OUT_JSON, result)

    with OUT_CSV.open("w", newline="") as handle:
        fields = [
            "ordinal",
            "name",
            "source",
            "output",
            "command",
            "returncode",
            "user_seconds",
            "system_seconds",
            "wall_seconds",
            "max_rss_kib",
            "stdout_bytes",
            "stderr_bytes",
            "same_run_output_match",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record[field] for field in fields})

    resource_result = {
        "scope": "final release-pass accounting and retained scientific operation counts; not whole research-lifetime accounting",
        "measurement_tool": result["measurement_tool"],
        "fresh_release_pass": summary,
        "operation_counts": {
            "campaign_certificates_rechecked": saved_outputs["verify_all"]["accepted_certificates"],
            "confirmatory_generated_subsets": saved_outputs["generated_oracle_audit"]["subsets_enumerated"],
            "external_subsets": saved_outputs["external_matrices"]["all_subsets_enumerated"],
            "metamorphic_checks": saved_outputs["metamorphic"]["metamorphic_checks"],
            "scientific_files_compared": clean["scientific_files_compared"],
            "stress_subsets": saved_outputs["stress"]["oracle_subset_visits"],
            "tiny_exhaustive_subsets": saved_outputs["exhaustive"]["oracle_subsets"],
            "campaign_networks": clean["replay_producer"]["networks"],
            "campaign_augmentations": clean["replay_producer"]["augmentations"],
            "campaign_edge_scans": clean["replay_producer"]["edge_scans"],
            "campaign_search_states": clean["replay_producer"]["search_states"],
            "campaign_checker_steps": clean["replay_checker_steps"],
        },
        "limits": {
            "address_space_limit_bytes": 2684354560,
            "per_case_wall_limit_seconds": 45,
            "whole_command_cpu_limit_seconds": 2700,
            "workers": 1,
        },
        "limitations": [
            "Early exploration, web transfers, typesetting, and packaging were not completely metered.",
            "Per-command RSS is a process peak, not simultaneous whole-system memory.",
            "Operation counters use different units and are not summed into a synthetic optimization-state total.",
            "Timing is machine-specific and is not a performance comparison.",
        ],
    }
    write_json(RESOURCE_JSON, resource_result)
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
