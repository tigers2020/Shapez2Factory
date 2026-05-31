"""Shim — relocated to ``shapez2_factory.domain.asteroid_lab.reconstruction.fill`` (PR-CLI-2f)."""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.reconstruction.fill import (
    ASTEROID_SHAPE_FIELD,
    EXTERNAL_POCKET_INTERIOR_CANDIDATE_MAX,
    EXTERNAL_POCKET_MAX_COMPONENT_SIZE,
    EXTERNAL_POCKET_MIN_ENCLAVE_COMPONENT_SIZE,
    SMALL_INTERIOR_EXTERIOR_FILL_BLOCKLIST,
    TOPOLOGY_FILL_PLACEHOLDER_KIND,
    _component_touches_walls,
    _is_narrow_external_channel,
    _wall_neighbor_count,
    connected_components,
    dense_gap_column_coords,
    diagonal_barrier_fill_coords,
    external_pocket_cells_to_fill,
    external_pocket_components,
    passes_bbox_interior,
    passes_two_axis_evidence_guard,
    seam_column_bridge_gap_fill_coords,
    seam_column_span_gap_fill_coords,
    synthetic_field_cell,
)

__all__ = [
    "ASTEROID_SHAPE_FIELD",
    "EXTERNAL_POCKET_INTERIOR_CANDIDATE_MAX",
    "EXTERNAL_POCKET_MAX_COMPONENT_SIZE",
    "EXTERNAL_POCKET_MIN_ENCLAVE_COMPONENT_SIZE",
    "SMALL_INTERIOR_EXTERIOR_FILL_BLOCKLIST",
    "TOPOLOGY_FILL_PLACEHOLDER_KIND",
    "_component_touches_walls",
    "_is_narrow_external_channel",
    "_wall_neighbor_count",
    "connected_components",
    "dense_gap_column_coords",
    "diagonal_barrier_fill_coords",
    "external_pocket_cells_to_fill",
    "external_pocket_components",
    "passes_bbox_interior",
    "passes_two_axis_evidence_guard",
    "seam_column_bridge_gap_fill_coords",
    "seam_column_span_gap_fill_coords",
    "synthetic_field_cell",
]
