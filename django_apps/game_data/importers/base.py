"""Shared importer utilities."""

from __future__ import annotations

import re
from typing import Any

from django_apps.game_data.models import ImportBatch, UnknownProperty
from django_apps.game_data.services.identifiers import hash_preview

_CHILD_INDEX_RE = re.compile(r"Children\[(\d+)\]$")


class ImportContext:
    def __init__(self, batch: ImportBatch) -> None:
        self.batch = batch
        self.summary: dict[str, int | list[str]] = {
            "imported": {},
            "skipped": {},
            "warnings": [],
            "unknown_fields": 0,
        }

    def bump(self, key: str, n: int = 1) -> None:
        imported = self.summary["imported"]
        assert isinstance(imported, dict)
        imported[key] = int(imported.get(key, 0)) + n

    def record_unknown(
        self,
        owner_model: str,
        owner_key: str,
        json_path: str,
        key: str,
        value: Any,
    ) -> None:
        preview, digest = hash_preview(value)
        UnknownProperty.objects.create(
            import_batch=self.batch,
            owner_model=owner_model,
            owner_key=owner_key,
            json_path=json_path,
            key=key,
            value_type=type(value).__name__,
            value_preview=preview,
            value_hash=digest,
        )
        self.summary["unknown_fields"] = int(self.summary["unknown_fields"]) + 1


def dig(obj: dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = obj
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key, default)
    return cur


def parse_toolbar_child_index(tree_path: str) -> int:
    """Last ``Children[n]`` segment in a flattened toolbar ``display_name_key`` path."""
    match = _CHILD_INDEX_RE.search(tree_path)
    return int(match.group(1)) if match else 0
