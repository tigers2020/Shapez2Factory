"""Shared importer utilities."""

from __future__ import annotations

import re

from django_apps.game_data.models import (
    GameDataReference,
    ImportBatch,
    SourceObject,
    UnknownProperty,
)
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
        value: object,
        *,
        reason_code: str = "",
        classification: str = "",
    ) -> None:
        preview, digest = hash_preview(value)
        _, created = UnknownProperty.objects.update_or_create(
            import_batch=self.batch,
            owner_model=owner_model,
            owner_key=owner_key,
            json_path=json_path,
            defaults={
                "key": key,
                "value_type": type(value).__name__,
                "value_preview": preview,
                "value_hash": digest,
                "reason_code": reason_code,
                "classification": classification,
            },
        )
        if created:
            self.summary["unknown_fields"] = int(self.summary["unknown_fields"]) + 1

    def record_source_row(
        self,
        filename: str,
        index: int,
        row: dict[str, object],
        *,
        source_path: str = "",
        system_id: str = "",
        clr_type: str = "",
    ) -> SourceObject:
        """Upsert row-level provenance; UK remains (batch, file, row_index)."""
        stable = str(row.get("stable_id", ""))
        dump_type = str(row.get("source_type_name", ""))
        obj, _ = SourceObject.objects.update_or_create(
            import_batch=self.batch,
            source_file=filename,
            source_row_index=index,
            defaults={
                "source_stable_id": stable,
                "dump_source_type": dump_type or clr_type,
                "source_path": source_path,
                "system_id": system_id or stable,
                "clr_type": clr_type or dump_type,
            },
        )
        return obj

    def record_unresolved_reference(
        self,
        from_source: SourceObject,
        ref_kind: str,
        ref_value: str,
        *,
        to_source: SourceObject | None = None,
    ) -> GameDataReference:
        ref, _ = GameDataReference.objects.update_or_create(
            import_batch=self.batch,
            from_source=from_source,
            ref_kind=ref_kind,
            ref_value=ref_value[:512],
            defaults={
                "to_source": to_source,
                "resolved": False,
            },
        )
        return ref


def dig(obj: dict[str, object], *keys: str, default: object = None) -> object:
    cur: object = obj
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key, default)
    return cur


def parse_toolbar_child_index(tree_path: str) -> int:
    """Last ``Children[n]`` segment in a flattened toolbar ``display_name_key`` path."""
    match = _CHILD_INDEX_RE.search(tree_path)
    return int(match.group(1)) if match else 0
