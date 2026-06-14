"""Sole authority for building L3 ``WeightedTransportRouteDomain`` snapshots at probe and commit."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.weighted_transport_route_domain import (  # noqa: E501
    WeightedTransportRouteDomain,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import BBox, Coord, bbox_from_coords


class RouteDomainSnapshotBuilder:
    """Build L3 weighted route probe domains from walkable/field/blocker inputs."""

    @staticmethod
    def build_snapshot(
        *,
        search_bbox: BBox,
        base_walkable: frozenset[Coord],
        field_cells: frozenset[Coord],
        blockers: frozenset[Coord],
    ) -> WeightedTransportRouteDomain:
        """Candidate-gen and commit-time re-probe share this surface construction."""

        return WeightedTransportRouteDomain(
            search_bbox=search_bbox,
            blocked_cells=blockers,
            walkable_cells=base_walkable,
            field_cost_cells=field_cells,
        )

    @staticmethod
    def build_immediate_probe_surface(
        *,
        placeable_cells: frozenset[Coord],
    ) -> WeightedTransportRouteDomain:
        """Geometry-only immediate probe before full search bbox is known."""

        return WeightedTransportRouteDomain(
            search_bbox=bbox_from_coords(frozenset()),
            blocked_cells=frozenset(),
            walkable_cells=placeable_cells,
            field_cost_cells=frozenset(),
        )


__all__ = ["RouteDomainSnapshotBuilder"]
