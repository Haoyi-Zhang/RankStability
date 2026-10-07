#!/usr/bin/env python3
"""Run all fixed secondary shards once, retaining raw output and bounded failures."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]

def run(out):
    if sys.flags.optimize:
        raise ValueError("optimized execution not admitted")
    out = out.resolve()
    if out.exists() or any(out.is_relative_to((ROOT / name).resolve()) for name in
                          ("src", "tests", "data", "external", "results", "literature", "proofs", ".github")):
        raise ValueError("new output directory outside retained results required")
    out.mkdir(parents=True)
    raw = out / "raw"; raw.mkdir()
    runner = ROOT / "tests/secondary_baselines.py"
    plan = out / "plan.json"
    commands = [["plan", "--output", str(plan)]]
    shards = []
    for start in range(0, 981, 100):
        path = out / ("shard-%03d.json" % start)
        shards.append(path)
        commands.append(["shard", "--plan", str(plan), "--start", str(start),
                         "--stop", str(min(981, start + 100)), "--output", str(path)])
    commands.append(["aggregate", "--plan", str(plan), "--shards", *map(str, shards),
                     "--output", str(out / "all-outcomes.json")])
    records = []
    begun = time.monotonic()
    for index, args in enumerate(commands):
        command = [sys.executable, "-B", str(runner), *args]
        remaining = 420 - (time.monotonic() - begun)
        if remaining <= 0:
            raise RuntimeError("420-second total budget exhausted; no retry")
        started = time.monotonic()
        try:
            completed = subprocess.run(command, cwd=ROOT, capture_output=True,
                                       timeout=min(120, remaining), check=False)
            stdout, stderr, code = completed.stdout, completed.stderr, completed.returncode
        except subprocess.TimeoutExpired as exc:
            stdout, stderr, code = exc.stdout or b"", exc.stderr or b"", "timeout"
        (raw / (str(index) + ".stdout.txt")).write_bytes(stdout)
        (raw / (str(index) + ".stderr.txt")).write_bytes(stderr)
        records.append(dict(command=command, exit_code=code, wall_seconds=time.monotonic() - started,
                            limit_seconds=min(120, remaining)))
        (out / "execution.json").write_text(json.dumps(dict(commands=records,
             complete=index == len(commands) - 1 and code == 0,
             wall_seconds=time.monotonic() - begun), indent=2) + "\n", encoding="utf-8")
        print("step", index + 1, "of", len(commands), "exit", code, flush=True)
        if code != 0:
            raise RuntimeError("bounded command failed; retained raw output; no retry")
    return json.loads((out / "all-outcomes.json").read_text(encoding="utf-8"))["totals"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    print(json.dumps(run(parser.parse_args().out), sort_keys=True))
