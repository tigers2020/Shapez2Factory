"""Map L3 rim greedy result into Layer 04 routing source views."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    Layer04SourceView,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    IntegratedRimGreedyResult,
)


def build_layer04_sources(rim: IntegratedRimGreedyResult) -> tuple[Layer04SourceView, ...]:
    """Convert committed L3 placements to L4 inputs.

    Assumption (v1): ``source_load_m = throughput_factor`` (M-bundle units).
    EVTC/minute conversion, if needed later, stays in this adapter only.
    """
    views: list[Layer04SourceView] = []
    for placement in rim.committed_placements:
        views.append(
            Layer04SourceView(
                placement_id=placement.placement_id,
                m_output_stub=placement.m_output_stub,
                source_load_m=placement.throughput_factor,
                throughput_factor=placement.throughput_factor,
                equipment_cells=placement.miner_cells | placement.extension_cells,
                route_probe_path=placement.route_probe_path,
            )
        )
    return tuple(sorted(views, key=lambda v: v.placement_id))


__all__ = ["build_layer04_sources"]
