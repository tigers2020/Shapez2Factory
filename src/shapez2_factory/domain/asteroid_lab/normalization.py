"""Attach lab-local summary metadata to decoded blueprint JSON (pure, no I/O)."""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.copy_json_coords import entry_island_raw_coord
from shapez2_factory.domain.asteroid_lab.service_dtos import (
    NormalizedBlueprintDTO,
    RawDecodedBlueprintDTO,
)

_SUMMARY_SCHEMA_VERSION = 1


def normalize_decoded_blueprint(raw: RawDecodedBlueprintDTO) -> NormalizedBlueprintDTO:
    """Return a shallow-copied root dict with ``_asteroid_lab_summary`` injected."""

    summary = _build_summary(raw.root)
    merged: dict[str, object] = dict(raw.root)
    merged["_asteroid_lab_summary"] = summary
    return NormalizedBlueprintDTO(decoded_json=merged)


def _build_summary(root: dict[str, object]) -> dict[str, object]:
    bp = root["BP"]
    entries: list[object] = bp["Entries"]
    v_raw = root.get("V")
    binary_version = _coerce_int_version(v_raw)

    xs: list[int] = []
    ys: list[int] = []
    cells: set[tuple[int, int]] = set()
    miner_count = 0
    extension_count = 0
    belt_count = 0
    pipe_count = 0

    for item in entries:
        if not isinstance(item, dict):
            continue
        island = entry_island_raw_coord(item)
        x, y = island.x, island.y
        xs.append(x)
        ys.append(y)
        cells.add((x, y))

        t = item.get("T")
        if not isinstance(t, str):
            continue
        if t.startswith("Layout_") and "Miner" in t:
            miner_count += 1
        if "MinerExtension" in t:
            extension_count += 1
        if "SpaceBelt" in t or t.startswith("SpaceBelt"):
            belt_count += 1
        if "SpacePipe" in t or t.startswith("SpacePipe"):
            pipe_count += 1

    if xs and ys:
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width = max_x - min_x + 1
        height = max_y - min_y + 1
    else:
        min_x = max_x = min_y = max_y = width = height = 0

    return {
        "schema_version": _SUMMARY_SCHEMA_VERSION,
        "binary_version": binary_version,
        "blueprint_type": str(bp["$type"]),
        "entry_count": len(entries),
        "cell_count": len(cells),
        "bbox": {
            "min_x": min_x,
            "max_x": max_x,
            "min_y": min_y,
            "max_y": max_y,
            "width": width,
            "height": height,
        },
        "miner_count": miner_count,
        "extension_count": extension_count,
        "belt_count": belt_count,
        "pipe_count": pipe_count,
        "inferred_source_kind": "copy_code_v4",
    }


def _coerce_int_version(v_raw: object) -> int:
    if isinstance(v_raw, int):
        return v_raw
    if v_raw is None:
        return 0
    try:
        return int(v_raw)
    except (TypeError, ValueError):
        return 0


def _as_int(val: object) -> int:
    if val is None:
        return 0
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, int):
        return val
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


__all__ = ["normalize_decoded_blueprint"]
