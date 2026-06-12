"""Stable string keys for per-cell effective-view index (paint Slice 2+)."""

from __future__ import annotations


def cell_key(x: int, y: int, layer: int | None = None) -> str:
    if layer is not None and layer != 0:
        return f"{layer}:{x},{y}"
    return f"{x},{y}"


__all__ = ["cell_key"]
