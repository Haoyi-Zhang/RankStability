#!/usr/bin/env python3
"""Measure one fresh sequential pass over all documented public entry points.

The result is command-level scientific accounting only.  It is not a machine
fingerprint and does not reconstruct unmetered exploratory work.
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "results/release-reproduction-accounting.json"
OUT_CSV = ROOT / "results/release-reproduction-accounting.csv"


def parse_time(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    values: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if ": " in stripped:
            key, value = stripped.rsplit(": ", 1)
            values[key.strip()] = value.strip()
    required = ["User time (seconds)", "System time (seconds)", "Maximum resident set size (kbytes)", "Exit status"]
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


def load_commands() -> list[tuple[str, list[str]]]:
    data = json.loads((ROOT / "public_commands.json").read_text())
    commands = [(item["name"], item["argv"]) for item in data]
    if len(commands) != len({name for name, _ in commands}):
        raise RuntimeError("duplicate public command name")
    return commands


def run() -> dict[str, object]:
    if not Path("/usr/bin/time").is_file():
        raise SystemExit("release accounting requires /usr/bin/time")
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    records: list[dict[str, object]] = []
    commands = load_commands()
    with tempfile.TemporaryDirectory(prefix="mutation-release-time-") as td:
        folder = Path(td)
        for index, (name, relative) in enumerate(commands, start=1):
            time_path = folder / f"{index:02d}-{name}.time"
            command = [sys.executable, *relative]
            wrapped = ["/usr/bin/time", "-v", "-o", str(time_path), *command]
            start = time.perf_counter()
            process = subprocess.run(wrapped, cwd=ROOT, env=env, text=True, capture_output=True, timeout=3000, check=False)
            wall = time.perf_counter() - start
            timing = parse_time(time_path)
            try:
                parsed = json.loads(process.stdout)
            except json.JSONDecodeError:
                parsed = None
            record = {
                "ordinal": index,
                "name": name,
                "command": " ".join(["python", *relative]),
                "returncode": process.returncode,
                "wall_seconds": wall,
                **timing,
                "stdout_bytes": len(process.stdout.encode()),
                "stderr_bytes": len(process.stderr.encode()),
                "stdout_json": parsed,
            }
            records.append(record)
            if process.returncode != 0 or timing["time_exit_status"] != 0:
                raise RuntimeError(f"{name} failed with {process.returncode}:\n{process.stderr[-4000:]}")
    total_user = sum(float(record["user_seconds"]) for record in records)
    total_system = sum(float(record["system_seconds"]) for record in records)
    result = {
        "scope": "one fresh sequential pass over all documented scientific entry points",
        "not_scope": "whole research-lifetime accounting or a toolchain/environment fingerprint",
        "measurement_tool": "GNU /usr/bin/time -v; each scientific command executes through src/limited.py",
        "commands": records,
        "summary": {
            "commands": len(records),
            "successful_commands": sum(record["returncode"] == 0 for record in records),
            "user_seconds_sum": total_user,
            "system_seconds_sum": total_system,
            "cpu_seconds_sum": total_user + total_system,
            "wall_seconds_sum": sum(float(record["wall_seconds"]) for record in records),
            "largest_command_max_rss_kib": max(int(record["max_rss_kib"]) for record in records),
            "workers": 1,
        },
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    with OUT_CSV.open("w", newline="") as handle:
        fields = ["ordinal", "name", "command", "returncode", "user_seconds", "system_seconds", "wall_seconds", "max_rss_kib", "stdout_bytes", "stderr_bytes"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record[field] for field in fields})
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
