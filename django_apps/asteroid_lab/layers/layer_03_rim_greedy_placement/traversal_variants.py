"""Deterministic traversal variants over Task 4 rim anchor order."""

from __future__ import annotations

from collections import deque

from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.rim_anchors import RimAnchor

VARIANT_IDS: tuple[str, ...] = ("CW_TL", "CCW_TL", "CW_MID", "EDGE_INTERLEAVE")
_EDGE_GROUP_ORDER: tuple[str, ...] = ("N", "E", "S", "W")


def build_variant_anchor_order(
    anchors: tuple[RimAnchor, ...],
    variant_id: str,
) -> tuple[RimAnchor, ...]:
    """Reorder anchors without recomputing geometry; unknown variant_id raises ValueError."""
    if variant_id not in VARIANT_IDS:
        msg = f"unknown variant_id: {variant_id!r}"
        raise ValueError(msg)
    if not anchors:
        return ()

    if variant_id == "CW_TL":
        return anchors
    if variant_id == "CCW_TL":
        return (anchors[0],) + tuple(reversed(anchors[1:]))
    if variant_id == "CW_MID":
        return _order_cw_mid(anchors)
    return _order_edge_interleave(anchors)


def _order_cw_mid(anchors: tuple[RimAnchor, ...]) -> tuple[RimAnchor, ...]:
    """Rotate CW order to start at longest same-primary edge run midpoint."""
    if len(anchors) <= 1:
        return anchors

    best_start = 0
    best_len = 1
    index = 0
    while index < len(anchors):
        primary = _primary_void_dir(anchors[index])
        run_end = index + 1
        while run_end < len(anchors) and _primary_void_dir(anchors[run_end]) == primary:
            run_end += 1
        run_len = run_end - index
        if run_len > best_len:
            best_len = run_len
            best_start = index
        index = run_end

    rotate_at = best_start + (best_len // 2)
    return anchors[rotate_at:] + anchors[:rotate_at]


def _order_edge_interleave(anchors: tuple[RimAnchor, ...]) -> tuple[RimAnchor, ...]:
    """Round-robin by primary void_dir groups N → E → S → W."""
    groups: dict[str, deque[RimAnchor]] = {edge: deque() for edge in _EDGE_GROUP_ORDER}
    for anchor in anchors:
        primary = _primary_void_dir(anchor)
        if primary in groups:
            groups[primary].append(anchor)

    ordered: list[RimAnchor] = []
    remaining = len(anchors)
    while remaining > 0:
        for edge in _EDGE_GROUP_ORDER:
            bucket = groups[edge]
            if bucket:
                ordered.append(bucket.popleft())
                remaining -= 1
    return tuple(ordered)


def _primary_void_dir(anchor: RimAnchor) -> str:
    if not anchor.void_dirs:
        msg = f"rim anchor {anchor.coord!r} has no void_dirs"
        raise ValueError(msg)
    return anchor.void_dirs[0]


__all__ = ["VARIANT_IDS", "build_variant_anchor_order"]
