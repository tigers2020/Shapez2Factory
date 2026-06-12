"""Golden JSON comparator for deterministic regression (Phase 2 harness)."""

from __future__ import annotations

import json
from pathlib import Path

GOLDEN_DIR = Path(__file__).resolve().parents[2] / "tests" / "golden"


def golden_path(name: str, *, kind: str) -> Path:
    """Resolve ``<name>_input.json`` or ``<name>_expected.json`` under tests/golden/."""
    suffix = "_input.json" if kind == "input" else "_expected.json"
    return GOLDEN_DIR / f"{name}{suffix}"


def load_golden_json(path: Path) -> object:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _diff_paths(
    actual: object,
    expected: object,
    prefix: str = "$",
) -> list[str]:
    if type(actual) is not type(expected):
        return [f"{prefix}: type {type(actual).__name__} != {type(expected).__name__}"]
    if isinstance(actual, dict):
        out: list[str] = []
        keys = sorted(set(actual) | set(expected))
        for key in keys:
            sub = f"{prefix}.{key}"
            if key not in actual:
                out.append(f"{sub}: missing in actual")
            elif key not in expected:
                out.append(f"{sub}: extra in actual")
            else:
                out.extend(_diff_paths(actual[key], expected[key], sub))
        return out
    if isinstance(actual, list):
        if len(actual) != len(expected):
            return [f"{prefix}: len {len(actual)} != {len(expected)}"]
        out = []
        for idx, (a_item, e_item) in enumerate(zip(actual, expected, strict=True)):
            out.extend(_diff_paths(a_item, e_item, f"{prefix}[{idx}]"))
        return out
    if actual != expected:
        return [f"{prefix}: {actual!r} != {expected!r}"]
    return []


def compare_json(actual: object, expected: object) -> tuple[bool, list[str]]:
    diffs = _diff_paths(actual, expected)
    return (not diffs, diffs)


def assert_golden_match(actual: object, expected_path: Path) -> None:
    expected = load_golden_json(expected_path)
    ok, diffs = compare_json(actual, expected)
    if not ok:
        msg = "golden mismatch:\n" + "\n".join(diffs[:20])
        if len(diffs) > 20:
            msg += f"\n... and {len(diffs) - 20} more"
        raise AssertionError(msg)


__all__ = [
    "GOLDEN_DIR",
    "assert_golden_match",
    "compare_json",
    "golden_path",
    "load_golden_json",
]
