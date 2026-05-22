"""Deterministic stratified sampling for fast import stability tests."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import TypeVar

T = TypeVar("T")

# Structural anchors from toolbar contract tests (skip if absent in dump).
TOOLBAR_CANONICAL_ID_ANCHOR_PATHS: tuple[str, ...] = (
    "root",
    "root/Children[5]/Children[8]/Children[4]",
    "root/Children[6]/Children[7]",
    "root/Children[6]/Children[7]/Children[0]",
    "root/Children[0]/Children[1]",
)


def pick_stratified_by_key[T](items: Sequence[T], *, n: int, key: Callable[[T], str]) -> list[T]:
    """Return up to ``3 * n`` items: first ``n``, middle ``n``, last ``n`` by ``key`` order."""

    ordered = sorted(items, key=key)
    total = len(ordered)
    if total == 0:
        return []
    if total <= n * 3:
        return list(ordered)

    head = ordered[:n]
    mid_start = max(0, total // 2 - n // 2)
    middle = ordered[mid_start : mid_start + n]
    tail = ordered[-n:]
    return list(head) + list(middle) + list(tail)


def merge_unique_paths(
    stratified_paths: Iterable[str],
    anchor_paths: Iterable[str],
    *,
    available: set[str],
) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for path in (*stratified_paths, *anchor_paths):
        if path not in available or path in seen:
            continue
        seen.add(path)
        result.append(path)
    return result
