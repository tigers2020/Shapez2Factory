"""Shared helpers for shape JSON parity tests."""

from __future__ import annotations


def count_layers_and_slots(defn: dict[str, object]) -> tuple[int, int]:
    layers = defn.get("Layers") or []
    slots = sum(len(layer.get("Parts") or []) for layer in layers)
    return len(layers), slots


def shape_row_key(row: dict[str, object]) -> tuple[int, str]:
    snap = row.get("definition_snapshot") or {}
    defn = snap.get("Definition") if isinstance(snap.get("Definition"), dict) else snap
    if not isinstance(defn, dict):
        defn = {}
    op_uid = int(defn.get("UniqueOperationId") or defn.get("Id", {}).get("Uid") or 0)
    shape_hash = str(defn.get("Hash", ""))
    return op_uid, shape_hash
