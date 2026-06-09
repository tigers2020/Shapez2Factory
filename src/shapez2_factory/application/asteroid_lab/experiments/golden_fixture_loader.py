"""Load and summarize golden fixture copy strings (domain-only; no Django)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from shapez2_factory.domain.asteroid_lab.cell_classifier import classify_blueprint_entry
from shapez2_factory.domain.asteroid_lab.copy_decode import decode_copy_string
from shapez2_factory.domain.asteroid_lab.copy_json_coords import (
    entries_have_explicit_raw_x_zero,
    entry_island_raw_coord,
    iter_entry_dicts,
    raw_x_to_export_column,
)
from shapez2_factory.domain.asteroid_lab.normalization import normalize_decoded_blueprint
from shapez2_factory.domain.asteroid_lab.service_dtos import NormalizedBlueprintDTO

_EXTRACTOR_TILES = frozenset({"Layout_ShapeMiner", "Layout_FluidMiner", "Layout_ProMiner"})
_EXTENSION_TILES = frozenset(
    {"Layout_ShapeMinerExtension", "Layout_FluidMinerExtension"},
)
_BELT_PREFIX = "SpaceBelt"


@dataclass(frozen=True, slots=True)
class GoldenOracle:
    """Precomputed golden-map features for eval (oracle only; never solver input)."""

    extractor_anchors_direct: frozenset[tuple[int, int]]
    extractor_anchors_normalized: frozenset[tuple[int, int]]
    extension_cells: frozenset[tuple[int, int]]
    belt_edges: frozenset[tuple[tuple[int, int], tuple[int, int]]]
    layout_miner_count: int
    layout_extension_count: int
    belt_count: int
    entry_count: int
    bbox: tuple[int, int, int, int]


def load_shapez_copy_string(path: Path | str) -> str:
    text = Path(path).read_text(encoding="utf-8").strip()
    line = text.splitlines()[0].strip() if text else ""
    return line.removesuffix("$")


def normalize_blueprint_entries(bp_root: dict[str, Any]) -> NormalizedBlueprintDTO:
    from shapez2_factory.domain.asteroid_lab.service_dtos import RawDecodedBlueprintDTO

    return normalize_decoded_blueprint(RawDecodedBlueprintDTO(root=bp_root))


def summarize_blueprint(bp_root: dict[str, Any]) -> dict[str, Any]:
    """Return summary dict including per-tile-type counts and bbox list."""

    norm = normalize_blueprint_entries(bp_root)
    summary = dict(norm.decoded_json.get("_asteroid_lab_summary") or {})
    entries = iter_entry_dicts(norm.decoded_json)
    type_counts: dict[str, int] = {}
    layout_miner_count = 0
    layout_extension_count = 0
    belt_count = 0
    for row in entries:
        t = str(row.get("T") or "")
        type_counts[t] = type_counts.get(t, 0) + 1
        if t in _EXTRACTOR_TILES:
            layout_miner_count += 1
        if t in _EXTENSION_TILES:
            layout_extension_count += 1
        if t.startswith(_BELT_PREFIX) or "SpaceBelt" in t:
            belt_count += 1
    bbox = summary.get("bbox") or {}
    return {
        "entry_count": int(summary.get("entry_count") or len(entries)),
        "layout_miner_count": layout_miner_count,
        "layout_extension_count": layout_extension_count,
        "belt_count": belt_count,
        "bbox": [
            int(bbox.get("min_x", 0)),
            int(bbox.get("max_x", 0)),
            int(bbox.get("min_y", 0)),
            int(bbox.get("max_y", 0)),
        ],
        "type_counts": type_counts,
    }


def _extractor_anchor_export_xy(
    rows: list[dict[str, Any]],
    *,
    has_explicit_raw_x_zero: bool,
) -> tuple[int, int] | None:
    candidates: list[tuple[int, int]] = []
    for row in rows:
        t = str(row.get("T") or "")
        if t not in _EXTRACTOR_TILES:
            continue
        island = entry_island_raw_coord(row)
        candidates.append(
            (
                raw_x_to_export_column(
                    island.x,
                    has_explicit_raw_x_zero=has_explicit_raw_x_zero,
                ),
                island.y,
            )
        )
    if not candidates:
        return None
    return min(candidates)


def _normalize_coords(
    coords: frozenset[tuple[int, int]],
    *,
    anchor: tuple[int, int],
) -> frozenset[tuple[int, int]]:
    ax, ay = anchor
    return frozenset((x - ax, y - ay) for x, y in coords)


def _belt_adjacency_edges(
    belt_cells: frozenset[tuple[int, int]],
) -> frozenset[tuple[tuple[int, int], tuple[int, int]]]:
    edges: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    for x, y in belt_cells:
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) in belt_cells:
                a, b = (x, y), (nx, ny)
                norm: tuple[tuple[int, int], tuple[int, int]] = (a, b) if a <= b else (b, a)
                edges.add(norm)
    return frozenset(edges)


def build_golden_oracle(golden_bp: dict[str, Any]) -> GoldenOracle:
    entries = iter_entry_dicts(golden_bp)
    has_zero = entries_have_explicit_raw_x_zero(entries)
    summary = summarize_blueprint(golden_bp)

    extractors_direct: set[tuple[int, int]] = set()
    extensions: set[tuple[int, int]] = set()
    belt_cells: set[tuple[int, int]] = set()
    for row in entries:
        t = str(row.get("T") or "")
        island = entry_island_raw_coord(row)
        xy = (island.x, island.y)
        if t in _EXTRACTOR_TILES:
            extractors_direct.add(
                (
                    raw_x_to_export_column(island.x, has_explicit_raw_x_zero=has_zero),
                    island.y,
                )
            )
        elif t in _EXTENSION_TILES:
            extensions.add(xy)
        else:
            cell_kind, _ = classify_blueprint_entry(t)
            if cell_kind == "space_belt":
                belt_cells.add(xy)

    anchor = _extractor_anchor_export_xy(entries, has_explicit_raw_x_zero=has_zero)
    if anchor is None and extractors_direct:
        anchor = min(extractors_direct)
    elif anchor is None:
        anchor = (0, 0)

    extractors_normalized = _normalize_coords(frozenset(extractors_direct), anchor=anchor)
    belt_edges = _belt_adjacency_edges(frozenset(belt_cells))
    bbox_list = summary["bbox"]
    return GoldenOracle(
        extractor_anchors_direct=frozenset(extractors_direct),
        extractor_anchors_normalized=extractors_normalized,
        extension_cells=frozenset(extensions),
        belt_edges=belt_edges,
        layout_miner_count=int(summary["layout_miner_count"]),
        layout_extension_count=int(summary["layout_extension_count"]),
        belt_count=int(summary["belt_count"]),
        entry_count=int(summary["entry_count"]),
        bbox=(bbox_list[0], bbox_list[1], bbox_list[2], bbox_list[3]),
    )


def load_golden_fixture_summary(path: Path | str) -> dict[str, Any]:
    payload: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload


def write_decoded_snapshots(
    *,
    empty_copy: str,
    golden_copy: str,
    out_dir: Path | str,
) -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    empty_path = out / "decoded_empty.json"
    golden_path = out / "decoded_golden.json"
    empty_root = decode_copy_string(empty_copy).root
    golden_root = decode_copy_string(golden_copy).root
    empty_path.write_text(
        json.dumps(empty_root, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    golden_path.write_text(
        json.dumps(golden_root, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return empty_path, golden_path


__all__ = [
    "GoldenOracle",
    "build_golden_oracle",
    "load_golden_fixture_summary",
    "load_shapez_copy_string",
    "normalize_blueprint_entries",
    "summarize_blueprint",
    "write_decoded_snapshots",
]
