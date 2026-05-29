"""Frozen Run #286 strip probes (project 23, y=11, x in [-8,-2])."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.candidates import (
    LAYER_03_RIM_MINING_BUNDLES,
    BundleCandidate,
    BundleCellRole,
    BundlePlacement,
    Layer03Slug,
    RouteProbedBundleCandidate,
    RouteProbeResult,
    RouteProbeStatus,
)
from django_apps.asteroid_lab.layers.contracts.transport_kind import ResourceKind, TransportKind
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_FIXTURE_PATH = (
    Path(__file__).resolve().parents[4] / "fixtures" / "layer04" / "run286_strip_probes.json"
)


def _coord_list(raw: list[list[int]]) -> frozenset[Coord]:
    return frozenset((int(x), int(y)) for x, y in raw)


def _probe_from_row(row: dict[str, object]) -> RouteProbedBundleCandidate:
    anchor = tuple(row["anchor"])  # type: ignore[arg-type]
    mining = _coord_list(row["mining"])  # type: ignore[arg-type]
    transport = _coord_list(row["transport"])  # type: ignore[arg-type]
    start = tuple(row["route_probe_start"])  # type: ignore[arg-type]
    goal_raw = row.get("goal")
    goal = tuple(goal_raw) if goal_raw else None  # type: ignore[arg-type]
    output_dir = Direction(str(row["output_dir"]))
    transport_kind = TransportKind.SHAPE_BELT
    candidate = BundleCandidate(
        candidate_id=str(row["candidate_id"]),
        layer_slug=cast(Layer03Slug, LAYER_03_RIM_MINING_BUNDLES),
        gene_key=str(row["gene_key"]),
        pattern_id=str(row["gene_key"]).replace("miner_seed_", ""),
        intrinsic_priority_rank=1,
        anchor_coord=anchor,
        output_dir=output_dir,
        rotation=1,
        resource_kind=ResourceKind.SHAPE,
        transport_kind=transport_kind,
        equivalence_key=str(row["equivalence_key"]),
        mining_occupied_cells=mining,
        transport_stub_cells=transport,
        route_probe_start_coord=start,
        placements=(
            BundlePlacement(
                coord=anchor,
                layout_t="Layout_ShapeMiner",
                rotation=1,
                cell_role=BundleCellRole.MINER,
            ),
        ),
        throughput_factor=16,
        topology_signature="run286_strip",
    )
    path_coords: tuple[Coord, ...] = (start, goal) if goal is not None else (start,)
    return RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=RouteProbeStatus.SUCCEEDED,
        route_probe_result=RouteProbeResult(
            reached_goal=goal is not None,
            goal_coord=goal,
            path_coords=path_coords,
            steps_expanded=len(path_coords),
            transport_kind=transport_kind,
            route_cost=int(row["route_cost"]),
        ),
        route_goal_id="run286_strip",
        reject_reason=None,
    )


def load_run286_strip_probes() -> tuple[RouteProbedBundleCandidate, ...]:
    raw = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    rows = sorted(raw, key=lambda r: str(r["candidate_id"]))
    return tuple(_probe_from_row(row) for row in rows)


__all__ = ["load_run286_strip_probes"]
