"""Regression: equipment occupied must not overlap reserved route cells."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput, TransportKind
from django_apps.asteroid_lab.optimization.validation.final_validation import (
    validate_final_layout,
)


def _minimal_pattern_e() -> BundlePattern:
    return BundlePattern(
        pattern_id="test_min_e_len0",
        extension_count=0,
        occupied_offsets=frozenset({(0, 0)}),
        extractor_offset=(0, 0),
        extension_offsets=(),
        output_dir="E",
        fixed_output_transport_offset=(1, 0),
        output_stub_offset=(2, 0),
        throughput_factor=4,
        topology_kind="test",
    )


def _bundle_candidate(
    candidate_id: str,
    anchor: Coord,
    *,
    occupied: frozenset[Coord],
    output_stub: Coord,
) -> BundleCandidate:
    pattern = _minimal_pattern_e()
    return BundleCandidate(
        candidate_id=candidate_id,
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=occupied,
        output_stub=output_stub,
        output_dir=pattern.output_dir,
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=pattern.throughput_factor,
        route_probe_cost=1,
        reachable=True,
        catalog_placement_ref=None,
    )


def test_validate_final_layout_rejects_equipment_on_reserved_route(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    inp = greenfield_optimization_input
    extractor = _bundle_candidate(
        "ext",
        (0, 0),
        occupied=frozenset({(0, 0)}),
        output_stub=(2, 0),
    )
    other = _bundle_candidate(
        "oth",
        (5, 5),
        occupied=frozenset({(5, 5)}),
        output_stub=(7, 5),
    )
    reserved = frozenset({(0, 0), (1, 0)})
    assert (
        validate_final_layout(
            (extractor.candidate_id, other.candidate_id),
            reserved,
            {
                extractor.candidate_id: extractor,
                other.candidate_id: other,
            },
            inp,
        )
        is False
    )
