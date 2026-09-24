#!/usr/bin/env python3
"""Apply the artifact resource envelope, then execute a Python entry point."""
import os
import resource
import runpy
import sys

if sys.flags.optimize:
    raise SystemExit("optimized Python is unsupported because validation obligations must not be disabled")
if len(sys.argv) < 2:
    raise SystemExit("usage: limited.py SCRIPT [ARG ...]")
if hasattr(os, "sched_setaffinity"):
    visible = sorted(os.sched_getaffinity(0))
    if visible:
        os.sched_setaffinity(0, {visible[0]})
resource.setrlimit(resource.RLIMIT_AS, (2684354560, 2684354560))
resource.setrlimit(resource.RLIMIT_CPU, (2700, 2700))
script = sys.argv[1]
sys.argv = sys.argv[1:]
runpy.run_path(script, run_name="__main__")
