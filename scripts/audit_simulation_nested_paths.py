#!/usr/bin/env python3
"""Emit nested JSON path frequencies from simulation_systems.json (audit-first)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_DEFAULT = _REPO / "documents" / "game_data" / "simulation_systems.json"
_KEYWORDS = ("ChainPosition", "TileBased", "Simulation", "_Lanes")
_MAX_LINES = 200
_PRIORITY_MAX_LINES = 250
_PRIORITY_KW = (
    "ChainPosition",
    "TileBased",
    "ConnectableSimulation",
    "SimulationFactory",
    "ISimulationSystem",
    "k__BackingField",
    "ExtractorPosition",
    "_Networks",
    "Interlock",
)


def _norm(path: str) -> str:
    return re.sub(r"\[\d+\]", "[]", path)


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
        for item in obj:
            _walk(item, f"{prefix}[]", stats)


def _walk_full(obj: object, prefix: str, stats: dict[str, list[int]]) -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(val, list):
                stats[path].append(len(val))
            _walk_full(val, path, stats)
    elif isinstance(obj, list):
        if prefix:
            stats[prefix].append(len(obj))
        for item in obj:
            _walk_full(item, f"{prefix}[]", stats)


def _emit_keyword_sample(rows: list[dict]) -> int:
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


def _priority_row(norm_path: str, meta: dict[str, int]) -> bool:
    return meta["max_len"] >= 4 or any(kw in norm_path for kw in _PRIORITY_KW)


def _emit_normalized_aggregate(rows: list[dict], *, priority_only: bool = False) -> int:
    stats: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        _walk_full(row.get("definition_snapshot") or {}, "definition_snapshot", stats)
        _walk_full(row.get("simulation_parameters") or {}, "simulation_parameters", stats)
    agg: dict[str, dict[str, int]] = {}
    for raw_path, lens in stats.items():
        norm_path = _norm(raw_path)
        bucket = agg.setdefault(norm_path, {"hits": 0, "max_len": 0})
        bucket["hits"] += len(lens)
        bucket["max_len"] = max(bucket["max_len"], max(lens) if lens else 0)

    print("norm_path\thits\tmax_list_len")
    ordered = sorted(agg.items(), key=lambda kv: (-kv[1]["max_len"], -kv[1]["hits"], kv[0]))
    lines = 0
    for norm_path, meta in ordered:
        if priority_only and not _priority_row(norm_path, meta):
            continue
        if not priority_only and not (
            meta["max_len"] >= 1
            or any(
                kw in norm_path
                for kw in (
                    "ChainPosition",
                    "TileBased",
                    "ConnectableSimulation",
                    "Simulation",
                    "_Lanes",
                    "k__BackingField",
                    "$type",
                    "instance_id",
                )
            )
        ):
            continue
        print(f"{norm_path}\t{meta['hits']}\t{meta['max_len']}")
        lines += 1
        if priority_only and lines >= _PRIORITY_MAX_LINES:
            print(f"# truncated at {_PRIORITY_MAX_LINES} priority lines", file=sys.stderr)
            break
    print(f"# total_norm_paths={len(agg)}", file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=str(_DEFAULT))
    parser.add_argument(
        "--normalized",
        action="store_true",
        help="Aggregate paths with [] indices; emit all priority families (no 200 cap).",
    )
    parser.add_argument(
        "--priority",
        action="store_true",
        help="With --normalized: emit review subset only (max 250 rows).",
    )
    args = parser.parse_args()
    path = Path(args.path)
    if not path.is_file():
        print(f"missing: {path}", file=sys.stderr)
        return 1
    rows = json.loads(path.read_text(encoding="utf-8"))
    if args.normalized:
        return _emit_normalized_aggregate(rows, priority_only=args.priority)
    return _emit_keyword_sample(rows)


if __name__ == "__main__":
    raise SystemExit(main())
