#!/usr/bin/env python3
"""Emit nested JSON path frequencies from simulation_systems.json (audit-first)."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_DEFAULT = _REPO / "documents" / "game_data" / "simulation_systems.json"
_KEYWORDS = ("ChainPosition", "TileBased", "Simulation", "_Lanes")
_MAX_LINES = 200


def _walk(obj: object, prefix: str, stats: dict[str, list[int]]) -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            path = f"{prefix}.{key}" if prefix else key
            if any(kw in key for kw in _KEYWORDS):
                if isinstance(val, list):
                    stats[path].append(len(val))
            _walk(val, path, stats)
    elif isinstance(obj, list):
        if any(kw in prefix for kw in _KEYWORDS):
            stats[prefix].append(len(obj))
        for i, item in enumerate(obj):
            _walk(item, f"{prefix}[{i}]", stats)


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else _DEFAULT
    if not path.is_file():
        print(f"missing: {path}", file=sys.stderr)
        return 1
    rows = json.loads(path.read_text(encoding="utf-8"))
    stats: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        _walk(row, "", stats)
    print("path\toccurrences\tmax_list_len")
    lines = 0
    for path in sorted(stats.keys()):
        counts = stats[path]
        print(f"{path}\t{len(counts)}\t{max(counts) if counts else 0}")
        lines += 1
        if lines >= _MAX_LINES:
            print(f"# truncated at {_MAX_LINES} lines", file=sys.stderr)
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
