#!/usr/bin/env python3
"""Bounded, serial, standard-library campaign over authored finite evidence.

Every child is a reviewed Python entry point with no subprocesses. Timeout
cleanup therefore owns the only process it terminates. Historical result files
are read where declared but never overwritten. This runner does not execute C,
read external matrices, access a network, install packages, or typeset papers.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from result_io import write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if sys.flags.optimize:
        parser.error("optimized execution disables test assertions")
    out = args.out.resolve()
    if out.exists():
        parser.error("output directory must be new; prior evidence is preserved")
    protected = [ROOT / name for name in ("src", "tests", "data", "external", "results", "literature", "proofs")]
    if any(out == p or p in out.parents for p in protected):
        parser.error("output must not overwrite repository scientific inputs")
    out.mkdir(parents=True)
    raw = out / "raw"
    raw.mkdir()
    env = os.environ.copy()
    env.update(PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0")
    commands = []
    for name in ("pilot", "exhaustive", "semantics", "stress", "metamorphic"):
        commands.append((name, [f"tests/{name}.py", "--output", str(out / (name + ".json"))], out / (name + ".json"), 90))
    commands.extend([
        ("owned_replay", ["tests/owned_replay.py", "--output-dir", str(out / "owned")], out / "owned/owned-replay.json", 120),
        ("generated_oracle_audit", ["tests/generated_oracle_audit.py", "--output-dir", str(out), "--campaign-csv", str(out / "owned/primary.csv")], out / "generated-oracle-audit.json", 180),
    ])
    start = time.monotonic()
    records = []
    for name, argv, target, limit in commands:
        command = [sys.executable, "-B", *argv]
        remaining = 420 - (time.monotonic() - start)
        timeout = min(limit, remaining)
        if timeout <= 0:
            raise TimeoutError("420-second whole-campaign wall budget exhausted")
        begin = time.monotonic()
        try:
            process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
        except subprocess.TimeoutExpired as error:
            for stream in ("stdout", "stderr"):
                value = getattr(error, stream) or b""
                (raw / (name + "." + stream + ".txt")).write_bytes(value.encode("utf-8") if isinstance(value, str) else value)
            write_json(out / "timeout.json", dict(name=name, command=command, timeout_seconds=timeout, owned_child_killed_and_waited=True))
            raise
        wall = time.monotonic() - begin
        (raw / (name + ".stdout.txt")).write_text(process.stdout, encoding="utf-8")
        (raw / (name + ".stderr.txt")).write_text(process.stderr, encoding="utf-8")
        record = dict(name=name, argv=command, wall_seconds=wall, timeout_seconds=timeout, returncode=process.returncode, canonical_output=str(target))
        records.append(record)
        write_json(out / "commands.json", records)
        if process.returncode:
            raise RuntimeError(f"{name} failed; raw output retained")
        result = json.loads(process.stdout)
        if result != json.loads(target.read_text(encoding="utf-8")):
            raise RuntimeError(f"{name}: stdout/canonical output mismatch")
        record["same_run_output_match"] = True
        print(f"{name}: PASS ({wall:.3f} s)", flush=True)
    write_json(out / "commands.json", records)
    summary = dict(
        commands=len(records), successful_commands=len(records),
        wall_seconds=time.monotonic() - start,
        command_wall_seconds_sum=sum(r["wall_seconds"] for r in records),
        python=sys.version, platform=platform.platform(), workers=1,
        limits=dict(per_command_wall_seconds=[r["timeout_seconds"] for r in records], whole_campaign_wall_seconds=420),
        scope="finite authored-input replay; not fresh C execution, external validation, mechanized proof, or hostile-input assurance",
        memory_limit_enforced=False,
        results={name: json.loads(target.read_text(encoding="utf-8")) for name, _, target, _ in commands},
    )
    write_json(out / "campaign.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "results"}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
