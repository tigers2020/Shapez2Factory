"""Layer 03 candidate generation (Task B2) — geometry + immediate route probe.

Covers spec rules R2 (equipment ⊆ matching-resource field), R3 (output stub ⊆
external void), R5 (only route-feasible candidates enter the normal pool), and D1
(deterministic candidate enumeration order in the canonical solver frame).

Geometry expectations are computed from the actual golden 5×5 fixture, not assumed.
"""

from __future__ import annotations

from shapez2_factory.adapters.asteroid_lab.gene_catalog_snapshot import (
    GeneCatalogEntry,
    GeneCatalogSnapshot,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    CandidateRejectReason,
    RouteProbeStatus,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.candidate_gen import (  # noqa: E501
    generate_candidates,
    output_dir_rank,
    rotate_offset_east_to,
)
from shapez2_factory.domain.asteroid_lab.genetic_sample.enums import Direction
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)

_ROUTE_FAILURE_REASONS = frozenset(
    {
        CandidateRejectReason.EXTERIOR_ENTRY_NOT_REACHABLE,
        CandidateRejectReason.EXTERIOR_CONNECTOR_UNREACHABLE,
        CandidateRejectReason.ROUTE_PROBE_FAILED,
    }
)


def _m0e_entry() -> GeneCatalogEntry:
    return GeneCatalogEntry(
        gene_id="m0e",
        resource_kind="both",
        canonical_output_dir="E",
        occupied_offsets=((0, 0),),
        extractor_offset=(0, 0),
        extension_offsets=(),
        output_stub_offset=(1, 0),
        route_probe_start_offset=(2, 0),
        throughput_factor=4,
        topology_signature_base="m0e_base",
    )


def _m3e_entry() -> GeneCatalogEntry:
    return GeneCatalogEntry(
        gene_id="m3e",
        resource_kind="shape",
        canonical_output_dir="E",
        occupied_offsets=((0, 0), (-1, 0), (-2, 0), (-3, 0)),
        extractor_offset=(0, 0),
        extension_offsets=((-1, 0), (-2, 0), (-3, 0)),
        output_stub_offset=(1, 0),
        route_probe_start_offset=(2, 0),
        throughput_factor=16,
        topology_signature_base="m3e_base",
    )


def _catalog() -> GeneCatalogSnapshot:
    return GeneCatalogSnapshot(
        schema_version="gene_catalog_v1",
        generated_at="",
        provenance_hash="",
        source_batch_id="",
        deterministic_sort_key="by_gene_id_then_throughput_desc",
        entries=(_m3e_entry(), _m0e_entry()),
    )


# ---------------------------------------------------------------------------
# rotation helper (canonical E -> target cardinal)
# ---------------------------------------------------------------------------


def test_rotate_output_offset_maps_to_target_direction() -> None:
    # canonical output stub (1, 0) points east; it must rotate to each cardinal delta.
    assert rotate_offset_east_to((1, 0), "east") == (1, 0)
    assert rotate_offset_east_to((1, 0), "north") == (0, -1)
    assert rotate_offset_east_to((1, 0), "west") == (-1, 0)
    assert rotate_offset_east_to((1, 0), "south") == (0, 1)


def test_rotate_route_start_offset() -> None:
    assert rotate_offset_east_to((2, 0), "east") == (2, 0)
    assert rotate_offset_east_to((2, 0), "north") == (0, -2)
    assert rotate_offset_east_to((2, 0), "west") == (-2, 0)
    assert rotate_offset_east_to((2, 0), "south") == (0, 2)


def test_rotate_inward_extension_offset() -> None:
    # canonical extension (-1, 0) extends west (inward when output is east); it must
    # always rotate to point opposite the output direction.
    assert rotate_offset_east_to((-1, 0), "east") == (-1, 0)
    assert rotate_offset_east_to((-1, 0), "north") == (0, 1)
    assert rotate_offset_east_to((-1, 0), "west") == (1, 0)
    assert rotate_offset_east_to((-1, 0), "south") == (0, -1)


def test_output_dir_rank_is_nesw() -> None:
    assert output_dir_rank(Direction.N) == 0
    assert output_dir_rank(Direction.E) == 1
    assert output_dir_rank(Direction.S) == 2
    assert output_dir_rank(Direction.W) == 3


# ---------------------------------------------------------------------------
# generate_candidates
# ---------------------------------------------------------------------------


def test_normal_pool_equipment_in_matching_field_r2() -> None:
    complete_map = golden_5x5_complete_map()
    result = generate_candidates(
        complete_map=complete_map,
        exterior_plan=minimal_l2_plan_for_golden(),
        gene_catalog=_catalog(),
    )
    assert result.normal_candidates, "expected at least one route-feasible candidate"
    for probed in result.normal_candidates:
        cand = probed.candidate
        assert cand.mining_occupied_cells <= complete_map.field_cells


def test_normal_pool_output_stub_in_external_void_r3() -> None:
    complete_map = golden_5x5_complete_map()
    result = generate_candidates(
        complete_map=complete_map,
        exterior_plan=minimal_l2_plan_for_golden(),
        gene_catalog=_catalog(),
    )
    for probed in result.normal_candidates:
        cand = probed.candidate
        assert cand.transport_stub_cells <= complete_map.external_void_cells


def test_only_route_feasible_candidates_enter_normal_pool_r5() -> None:
    complete_map = golden_5x5_complete_map()
    result = generate_candidates(
        complete_map=complete_map,
        exterior_plan=minimal_l2_plan_for_golden(),
        gene_catalog=_catalog(),
    )
    for probed in result.normal_candidates:
        assert probed.route_probe_status == RouteProbeStatus.SUCCEEDED
        assert probed.route_probe_result is not None
        assert probed.route_probe_result.reached_goal

    assert result.diagnostic_rejected_candidates, "expected infeasible diagnostics"
    for probed in result.diagnostic_rejected_candidates:
        assert probed.route_probe_status != RouteProbeStatus.SUCCEEDED
        assert probed.route_probe_result is None

    # At least one diagnostic is geometry-valid yet route-infeasible (R5 in action).
    assert any(
        probed.reject_reason in _ROUTE_FAILURE_REASONS
        for probed in result.diagnostic_rejected_candidates
    )


def test_candidate_enumeration_order_equals_d1_sort_key() -> None:
    complete_map = golden_5x5_complete_map()
    result = generate_candidates(
        complete_map=complete_map,
        exterior_plan=minimal_l2_plan_for_golden(),
        gene_catalog=_catalog(),
    )

    def d1_key(probed: object) -> tuple[int, int, int, int, str]:
        cand = probed.candidate  # type: ignore[attr-defined]
        return (
            cand.anchor_coord[0],
            cand.anchor_coord[1],
            output_dir_rank(cand.output_dir),
            -cand.throughput_factor,
            cand.gene_key,
        )

    actual = list(result.normal_candidates)
    assert actual == sorted(actual, key=d1_key)


def test_golden_normal_pool_is_the_single_aligned_anchor() -> None:
    # The golden fixture's only route goal is the void cell (8, 4); the only anchor whose
    # canonical-E footprint lands route_probe_start on (8, 4) is field cell (6, 4).
    complete_map = golden_5x5_complete_map()
    result = generate_candidates(
        complete_map=complete_map,
        exterior_plan=minimal_l2_plan_for_golden(),
        gene_catalog=_catalog(),
    )
    assert len(result.normal_candidates) == 2
    for probed in result.normal_candidates:
        assert probed.candidate.anchor_coord == (6, 4)
        assert probed.candidate.output_dir == Direction.E
        assert probed.candidate.route_probe_start_coord == (8, 4)
    # higher throughput gene (m3e) enumerates before m0e at the same anchor/direction.
    assert [p.candidate.gene_key for p in result.normal_candidates] == ["m3e", "m0e"]


def test_metrics_counts_match_pools() -> None:
    complete_map = golden_5x5_complete_map()
    result = generate_candidates(
        complete_map=complete_map,
        exterior_plan=minimal_l2_plan_for_golden(),
        gene_catalog=_catalog(),
    )
    metrics = result.metrics
    assert metrics.normal_candidate_count == len(result.normal_candidates)
    assert metrics.diagnostic_rejected_count == len(result.diagnostic_rejected_candidates)
    assert metrics.route_probe_succeeded_count == len(result.normal_candidates)
    assert result.observability.normal_candidate_count == metrics.normal_candidate_count
