"""Pattern bundle highlight wire shapes (replay metrics projection only)."""

from __future__ import annotations

from typing import NotRequired, TypedDict

type OutlineLoopWire = list[list[int]]
type OutlineLoopsWire = list[OutlineLoopWire]


class PatternBundleHighlightEntryWire(TypedDict):
    bundle_key: str
    color_index: int
    outline_loops: OutlineLoopsWire
    gene_key: NotRequired[str]


class PatternBundleHighlightsWire(TypedDict):
    version: int
    bundles: list[PatternBundleHighlightEntryWire]


__all__ = [
    "OutlineLoopWire",
    "OutlineLoopsWire",
    "PatternBundleHighlightEntryWire",
    "PatternBundleHighlightsWire",
]
