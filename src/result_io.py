#!/usr/bin/env python3
"""Canonical JSON result persistence and scientific-result comparison.

Runtime-only timing and peak-memory fields may vary across clean executions.
All other fields, including operation counters, are part of the recoverable
scientific output and must match exactly.
"""
from __future__ import annotations

import json
import argparse
from pathlib import Path
from typing import Any


def peak_rss_kib() -> int | None:
    """Return the existing Unix process metric, or null when unavailable.

    Windows has no standard-library resource module; do not substitute an
    invented RSS value or imply that a Unix memory limit was applied there.
    """
    try:
        import resource
    except ImportError:
        return None
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def output_path(default: Path) -> Path:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=default)
    return parser.parse_args().output


def _runtime_only(key: str) -> bool:
    return (
        "cpu_seconds" in key
        or key in {"wall_seconds", "user_seconds", "system_seconds", "elapsed_reported"}
        or key.endswith("_rss_kib")
        or key == "max_rss_kib"
    )


def scientific_view(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: scientific_view(item)
            for key, item in value.items()
            if not _runtime_only(str(key))
        }
    if isinstance(value, list):
        return [scientific_view(item) for item in value]
    return value


def assert_scientific_equal(expected: Any, actual: Any, label: str) -> None:
    left = scientific_view(expected)
    right = scientific_view(actual)
    if left != right:
        raise RuntimeError(f"scientific result mismatch: {label}")


def write_json(path: Path, result: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def emit(path: Path, result: Any) -> None:
    write_json(path, result)
    print(json.dumps(result, indent=2, sort_keys=True))
