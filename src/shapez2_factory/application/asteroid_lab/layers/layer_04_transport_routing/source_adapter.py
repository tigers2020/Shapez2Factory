"""Map L3 rim greedy result into Layer 04 routing source views."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    Layer04SourceView,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    IntegratedRimGreedyResult,
)

# Canon: 12 fully boosted miners (throughput_factor=16) saturate one exterior connector
# (12 lane M-units). Lane fraction is throughput_factor/16; round up to >=1 M-unit.
_MAX_THROUGHPUT_FACTOR = 16


def throughput_factor_to_source_load_m(throughput_factor: int) -> int:
    """Map L3 ``throughput_factor`` to L4 connector lane M-units."""
    return max(1, (throughput_factor + _MAX_THROUGHPUT_FACTOR - 1) // _MAX_THROUGHPUT_FACTOR)


def build_layer04_sources(rim: IntegratedRimGreedyResult) -> tuple[Layer04SourceView, ...]:
    """Convert committed L3 placements to L4 inputs.

    ``source_load_m`` is lane M-bundle demand for connector/group capacity only.
    ``throughput_factor`` is preserved for throughput scoring elsewhere.
    """
    views: list[Layer04SourceView] = []
    for placement in rim.committed_placements:
        views.append(
            Layer04SourceView(
                placement_id=placement.placement_id,
                m_output_stub=placement.m_output_stub,
                source_load_m=throughput_factor_to_source_load_m(placement.throughput_factor),
                throughput_factor=placement.throughput_factor,
                equipment_cells=placement.miner_cells | placement.extension_cells,
                route_probe_path=placement.route_probe_path,
            )
        )
    return tuple(sorted(views, key=lambda v: v.placement_id))


__all__ = ["build_layer04_sources", "throughput_factor_to_source_load_m"]
