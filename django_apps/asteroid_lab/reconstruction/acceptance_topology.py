"""Shim: relocated to shapez2_factory.domain.asteroid_lab.reconstruction.acceptance_topology."""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.reconstruction.acceptance_topology import (
    AcceptanceTopology,
    acceptance_topology_from_complete_map,
    acceptance_topology_from_decoded_cells,
    acceptance_topology_from_reconstruction,
    constraint_violation_count,
    external_void_coords_from_reconstruction,
    infer_topology_coord_frame,
    mineable_coords_from_reconstruction,
    mineable_field_kind,
    topology_coord_for_cell,
)

__all__ = [
    "AcceptanceTopology",
    "acceptance_topology_from_complete_map",
    "acceptance_topology_from_decoded_cells",
    "acceptance_topology_from_reconstruction",
    "constraint_violation_count",
    "external_void_coords_from_reconstruction",
    "infer_topology_coord_frame",
    "mineable_coords_from_reconstruction",
    "mineable_field_kind",
    "topology_coord_for_cell",
]
