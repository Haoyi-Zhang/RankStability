#!/usr/bin/env python3
"""Owned, bounded C mutation-schema benchmark.

The confirmatory corpus contains ten templates and twenty variants per template.
Variant 19 of each template is reserved for protocol development and is never
used as a confirmatory case; variants 0--18 and 20 form the frozen 200-case
corpus.  No real-project or naturally occurring fault claim is made.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import random
import resource
import subprocess
import tempfile
import time
from pathlib import Path

import certify

FAMILIES = [
    "affine", "clamp", "tariff", "median", "interval", "predicate",
    "accumulator", "remainder", "bucket", "polynomial",
]
OPERATORS = ["increment", "decrement", "negation", "zero"]
DEVELOPMENT_VARIANT = 19
CONFIRMATORY_VARIANTS = tuple(range(19)) + (20,)


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def expressions(family: int, p: list[int]) -> list[str]:
    p0, p1, p2 = p
    return [
        [f"x+({p0})", f"y-({p1})", "2*a+b", f"c>{p2}?c-({p2}):c+({p2})", "3*d+a", "e-b"],
        [f"x+({p0})", f"a<({p1})?({p1}):a", f"b>({p1+4})?({p1+4}):b", f"y+({p2})", "d<0?-d:d", "c+e"],
        [f"x>({p0})", f"y>({p1})", "x+5", "a?2*c:c", f"b?d+({p2}):d", "e<0?0:e"],
        [f"x+({p0})", f"y+({p1})", f"({p2})", "a<b?a:b", "a>b?a:b", "c<d?d:(c>e?e:c)"],
        [f"x-({p0})", f"y-({p1})", "a<b?a:b", "a>b?a:b", "d-c", f"(e>{p2+4}?1:0)+e"],
        [f"x>({p0})", f"y<({p1})", f"x+y==({p2})", "2*a+3*b", "d-4*c", "e>0?e:0"],
        [f"x+({p0})", "a+y", f"b+({p1})", "c>0?c:-c", f"d*({p2+4})", "e+(x>y?x:y)"],
        ["x+8", "y+8", "a*3+b", "c%7", f"(d+({p0+8}))%5", f"e*2+({p2})"],
        [f"x+({p0})", f"y+({p1})", "a>0?1:0", "b>0?2:0", "c+d", f"e==0?({p2}):(e==1?a:(e==2?b:a+b))"],
        [f"x+({p0})", f"y+({p1})", "a*a", "b*b", "c-d", f"e>({p2})?e-a:e+b"],
    ][family]


def specification(family: int, variant: int) -> tuple[list[int], list[list[int]], int]:
    if not 0 <= family < len(FAMILIES):
        raise ValueError("unknown template family")
    if not 0 <= variant <= 20:
        raise ValueError("variant outside frozen range 0--20")
    rng = random.Random(91273 + family * 1000 + variant)
    p = [rng.randrange(-2, 3) for _ in range(3)]
    operators: list[list[int]] = []
    for loc in range(6):
        rest = [x for x in range(4) if x != loc % 4]
        rng.shuffle(rest)
        choices = sorted([loc % 4] + rest[: 1 + ((variant + loc) % 2)])
        for op in choices:
            operators.append([loc, op])
    return p, operators, 1 if variant % 2 == 0 else -1


def source(family: int, variant: int, seed_location: int) -> str:
    p, operators, delta = specification(family, variant)
    names = ["a", "b", "c", "d", "e", "r"]
    body: list[str] = []
    for loc, (name, expr) in enumerate(zip(names, expressions(family, p))):
        body.append(f"  int64_t {name}=({expr}); /* logical location {loc} */")
        body.append(f"  if (fault=={loc}) {name}+=({delta});")
        for j, (mloc, op) in enumerate(operators):
            if mloc != loc:
                continue
            replace = [f"{name}+1", f"{name}-1", f"-{name}", "0"][op]
            body.append(f"  if (mutant=={j}) {name}=({replace}); /* {OPERATORS[op]} */")
    body.append("  return r;")
    code = "/* Generated bounded arithmetic subject; MIT license, see repository LICENSE. */\n#include <stdint.h>\n#include <inttypes.h>\n#include <stdio.h>\n"
    code += "static int64_t subject(int64_t x,int64_t y,int fault,int mutant) {\n" + "\n".join(body) + "\n}\n"
    code += "int main(void) {\n  for (int x=-3;x<=3;x++) for(int y=-3;y<=3;y++) {\n"
    code += f'    printf("%d,%d,%" PRId64 ",%" PRId64,x,y,subject(x,y,-1,-1),subject(x,y,{seed_location},-1));\n'
    code += f'    for (int m=0;m<{len(operators)};m++) printf(",%" PRId64,subject(x,y,{seed_location},m));\n'
    code += "    putchar('\\n');\n  }\n  return 0;\n}\n"
    return code


def run_one(family: int, variant: int, outdir: Path | str, ident: str | None = None,
            protocol_role: str = "confirmatory") -> dict[str, object]:
    if ident is None:
        ident = f"program-{family * 20 + variant:03d}"
    if not ident or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for ch in ident):
        raise ValueError("unsafe subject identifier")
    outdir = Path(outdir)
    srcdir, rawdir, cases = outdir / "programs", outdir / "observations", outdir / "cases"
    for directory in (srcdir, rawdir, cases):
        directory.mkdir(parents=True, exist_ok=True)

    p, operators, delta = specification(family, variant)
    attempts: list[dict[str, int]] = []
    wall_start = time.monotonic()
    start = time.process_time()
    child_start = resource.getrusage(resource.RUSAGE_CHILDREN)
    with tempfile.TemporaryDirectory(prefix="mutation-c-") as td:
        exe = Path(td) / "subject"
        for offset in range(6):
            if time.monotonic() - wall_start >= 45:
                raise TimeoutError("45-second subject budget exhausted")
            fault = (variant + offset) % 6
            path = srcdir / f"{ident}.c"
            path.write_text(source(family, variant, fault))
            remaining = 45 - (time.monotonic() - wall_start)
            compile_result = subprocess.run(
                ["cc", "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror", str(path), "-o", str(exe)],
                capture_output=True, text=True, timeout=max(0.001, min(40, remaining)), check=False,
            )
            if compile_result.returncode:
                raise RuntimeError(compile_result.stderr)
            remaining = 45 - (time.monotonic() - wall_start)
            output = subprocess.run(
                [str(exe)], capture_output=True, text=True,
                timeout=max(0.001, min(5, remaining)), check=True,
            ).stdout
            rows = [[int(v) for v in row.split(",")] for row in output.splitlines()]
            ensure(len(rows) == 49, "subject did not emit 49 rows")
            ensure(all(len(row) == 4 + len(operators) for row in rows), "subject output width mismatch")
            fail = [int(row[2] != row[3]) for row in rows]
            attempts.append({"fault_location": fault, "failing_tests": sum(fail)})
            if sum(fail):
                break
        else:
            raise RuntimeError("no detected seed among six deterministic candidates")

    n = len(operators)
    seed_sample = [
        next(j for j, (loc_j, op) in enumerate(operators) if loc_j == loc and op == loc % 4)
        for loc in range(6)
    ]
    chosen = Counter(operators[j][1] for j in seed_sample)
    a_bounds = [[max(0, chosen[op] - 1), chosen[op] + 1] for op in range(4)]
    case = {
        "id": ident,
        "fail": fail,
        "kill": [[int(x != row[3]) for x in row[4:]] for row in rows],
        "location": [loc for loc, _ in operators],
        "locations": 6,
        "tie": list(range(6)),
        "a": [op for _, op in operators],
        "b": [loc for loc, _ in operators],
        "a_bounds": a_bounds,
        "b_bounds": [[1, 2] for _ in range(6)],
        "size": [6, min(n, sum(q[1] for q in a_bounds))],
        "force": [],
        "forbid": [],
        "reference": [0],
        "empty": "bottom",
    }
    case["reference"] = certify.top(case, list(range(n)))
    ensure(certify.admissible(case, seed_sample), "policy seed sample is not admissible")
    rawdir.joinpath(f"{ident}.csv").write_text(
        "x,y,reference,buggy," + ",".join(f"mutant_{i}" for i in range(n)) + "\n" + output
    )
    cases.joinpath(f"{ident}.json").write_text(json.dumps(case, sort_keys=True, indent=2) + "\n")
    child_end = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
        "id": ident,
        "category": "program" if protocol_role == "confirmatory" else "development",
        "protocol_role": protocol_role,
        "family": FAMILIES[family],
        "family_index": family,
        "variant": variant,
        "parameters": p,
        "fault_location": fault,
        "fault_delta": delta,
        "mutants": operators,
        "screening": attempts,
        "tests": 49,
        "failing_tests": sum(fail),
        "policy_seed_sample": seed_sample,
        "cpu_seconds": time.process_time() - start + child_end.ru_utime - child_start.ru_utime + child_end.ru_stime - child_start.ru_stime,
        "peak_child_rss_kib": child_end.ru_maxrss,
    }


def confirmatory_design(index: int) -> tuple[int, int, str]:
    if not 0 <= index < 200:
        raise ValueError("confirmatory index outside 0--199")
    family, slot = divmod(index, 20)
    variant = slot if slot < DEVELOPMENT_VARIANT else 20
    return family, variant, f"program-{index:03d}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int, default=200)
    args = parser.parse_args()
    if not 0 <= args.start < 200 or not 1 <= args.count <= 200 - args.start:
        parser.error("invalid bounded chunk")
    for index in range(args.start, args.start + args.count):
        family, variant, ident = confirmatory_design(index)
        target = args.out / "metadata" / f"{ident}.json"
        if target.exists():
            raise RuntimeError("output exists; use an empty reproduction directory")
        meta = run_one(family, variant, args.out, ident=ident, protocol_role="confirmatory")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(meta, sort_keys=True, indent=2) + "\n")
        print(meta["id"], "variant=", variant, "cpu=", round(float(meta["cpu_seconds"]), 4), flush=True)


if __name__ == "__main__":
    main()
