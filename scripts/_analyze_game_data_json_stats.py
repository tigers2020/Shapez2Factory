"""Collect compact stats for game_data JSON documentation."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SOURCE = Path(__file__).resolve().parents[1] / "documents" / "game_data"
SAMPLE = 50


def walk_types(obj: Any, path: str, out: Counter[str], depth: int = 0) -> None:
    if depth > 12:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            child = f"{path}.{k}" if path else k
            if k == "$type" and isinstance(v, str):
                out[f"$type@{path or '<root>'}"] += 1
            if k == "$unity" and isinstance(v, str):
                out[f"$unity@{path or '<root>'}"] += 1
            walk_types(v, child, out, depth + 1)
    elif isinstance(obj, list):
        for item in obj[:3]:
            walk_types(item, path + "[]", out, depth + 1)


def row_keys(rows: list[dict[str, Any]]) -> dict[str, float]:
    total = min(SAMPLE, len(rows))
    counts: Counter[str] = Counter()
    for row in rows[:total]:
        counts.update(row.keys())
    return {k: counts[k] / total for k in sorted(counts)}


def main() -> None:
    report: dict[str, Any] = {}
    for path in sorted(SOURCE.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        entry: dict[str, Any] = {
            "bytes": path.stat().st_size,
            "root": type(data).__name__,
        }
        if isinstance(data, list):
            entry["count"] = len(data)
            dict_rows = [r for r in data if isinstance(r, dict)]
            entry["key_rates"] = row_keys(dict_rows)
            stypes = Counter(str(r.get("source_type_name", "")) for r in dict_rows)
            entry["source_type_name_top20"] = stypes.most_common(20)
            types_in_snap = Counter()
            for row in dict_rows[:SAMPLE]:
                snap = row.get("definition_snapshot") or row.get("manager_snapshot")
                if isinstance(snap, dict) and "$type" in snap:
                    types_in_snap[str(snap["$type"])] += 1
            if types_in_snap:
                entry["snapshot_$type_top30"] = types_in_snap.most_common(30)
            path_types = Counter()
            for row in dict_rows[:SAMPLE]:
                walk_types(row, "", path_types)
            entry["nested_$type_paths_top25"] = [
                (k, v) for k, v in path_types.most_common(25) if k.startswith("$type")
            ]
        elif isinstance(data, dict):
            entry["top_level_keys"] = sorted(data.keys())
        report[path.name] = entry

    out = Path(__file__).resolve().parents[1] / "docs" / "domain" / "_game_data_json_stats.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
