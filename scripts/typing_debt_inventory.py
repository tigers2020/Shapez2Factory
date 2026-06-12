#!/usr/bin/env python3
"""Scan Python typing debt for the typing-zero loop."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".worktrees",
    "graphify-out",
}

_ANY: str = chr(65) + "ny"

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("any_token", re.compile(rf"\b{_ANY}\b")),
    ("dict_str_any", re.compile(rf"dict\[str,\s*{_ANY}\]")),
    ("list_any", re.compile(rf"list\[{_ANY}\]")),
    ("mapping_str_any", re.compile(rf"Mapping\[str,\s*{_ANY}\]")),
    ("sequence_any", re.compile(rf"Sequence\[{_ANY}\]")),
    ("dict_str_object", re.compile(r"dict\[str,\s*object\]")),
    ("cast_call", re.compile(r"\bcast\s*\(")),
]


@dataclass(frozen=True, slots=True)
class FileDebt:
    path: str
    any_token: int
    dict_str_any: int
    list_any: int
    mapping_str_any: int
    sequence_any: int
    dict_str_object: int
    cast_call: int
    bucket: str
    boundary_kind: str
    risk: str

    @property
    def total_any_surface(self) -> int:
        return (
            self.any_token
            + self.dict_str_any
            + self.list_any
            + self.mapping_str_any
            + self.sequence_any
        )


def _bucket(path: str) -> str:
    if path.startswith("tests/"):
        return "tests"
    if path.startswith("scripts/") or path.startswith("harness/"):
        return "scripts_harness"
    if path.startswith("config/"):
        return "config"
    if path.startswith("django_apps/asteroid_lab/replay/"):
        return "replay"
    if path.startswith("django_apps/asteroid_lab/services/"):
        return "asteroid_lab_services"
    if path.startswith("django_apps/asteroid_lab/snapshots/"):
        return "snapshots"
    if path.startswith("django_apps/asteroid_lab/adapters/"):
        return "adapters"
    if path.startswith("django_apps/asteroid_lab/genetic_sample/"):
        return "genetic_sample"
    if path.startswith("django_apps/web/"):
        return "web"
    if path.startswith("django_apps/shapez_solver/"):
        return "shapez_solver"
    if path.startswith("django_apps/game_data/"):
        return "game_data"
    if path.startswith("django_apps/shapez_core/"):
        return "shapez_core"
    if path.startswith("src/"):
        return "src"
    if path.startswith("django_apps/asteroid_lab/"):
        return "asteroid_lab_other"
    return "other"


def _boundary_kind(path: str) -> str:
    if "wire" in path or "serialization" in path or "deserialize" in path:
        return "wire"
    if path.startswith("django_apps/web/"):
        return "web_ui"
    if "importer" in path or path.startswith("django_apps/game_data/"):
        return "game_data_import"
    if path.startswith("tests/"):
        return "test_fixture"
    if path.endswith("typing_boundary.py"):
        return "governance_alias"
    return "service_dto"


def _risk(path: str, counts: dict[str, int]) -> str:
    if path.startswith("tests/") or path.startswith("scripts/"):
        return "low"
    if counts["any_token"] >= 20 or counts["dict_str_any"] >= 15:
        return "high"
    if counts["any_token"] >= 5:
        return "medium"
    return "low"


def scan(root: Path) -> list[FileDebt]:
    rows: list[FileDebt] = []
    root = root.resolve()
    for path in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = path.resolve().relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        counts = {name: len(pattern.findall(text)) for name, pattern in PATTERNS}
        if sum(counts.values()) == 0:
            continue
        rows.append(
            FileDebt(
                path=rel,
                any_token=counts["any_token"],
                dict_str_any=counts["dict_str_any"],
                list_any=counts["list_any"],
                mapping_str_any=counts["mapping_str_any"],
                sequence_any=counts["sequence_any"],
                dict_str_object=counts["dict_str_object"],
                cast_call=counts["cast_call"],
                bucket=_bucket(rel),
                boundary_kind=_boundary_kind(rel),
                risk=_risk(rel, counts),
            )
        )
    return rows


def summarize(rows: list[FileDebt]) -> dict[str, object]:
    by_bucket: dict[str, dict[str, int]] = defaultdict(
        lambda: {"files": 0, "any_token": 0, "dict_str_object": 0}
    )
    for row in rows:
        bucket = by_bucket[row.bucket]
        bucket["files"] += 1
        bucket["any_token"] += row.any_token
        bucket["dict_str_object"] += row.dict_str_object
    return {
        "files_with_debt": len(rows),
        "any_token_total": sum(r.any_token for r in rows),
        "dict_str_any_total": sum(r.dict_str_any for r in rows),
        "dict_str_object_total": sum(r.dict_str_object for r in rows),
        "by_bucket": dict(sorted(by_bucket.items(), key=lambda kv: -kv[1]["any_token"])),
        "top_files": [
            {
                "path": r.path,
                "any_token": r.any_token,
                "dict_str_object": r.dict_str_object,
                "bucket": r.bucket,
                "boundary_kind": r.boundary_kind,
                "risk": r.risk,
            }
            for r in sorted(rows, key=lambda r: (-r.any_token, r.path))[:40]
        ],
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    rows = scan(root)
    payload = summarize(rows)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
