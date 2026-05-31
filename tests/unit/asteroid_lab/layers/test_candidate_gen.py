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
    BundleCellRole,
    CandidateRejectReason,
    RouteProbeStatus,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.candidate_gen import (  # noqa: E501
    edge_rotation_k,
    free_void_output_sides,
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
# §T footprint transform contract (Amendment 6)
# ---------------------------------------------------------------------------


def test_edge_rotation_k_is_east_zero_clockwise() -> None:
    # Canonical base orientation is East (k=0); each clockwise quarter-turn adds 1.
    # This is the geometric transform rank, NOT the NESW D1 ordering rank.
    assert edge_rotation_k("east") == 0
    assert edge_rotation_k("south") == 1
    assert edge_rotation_k("west") == 2
    assert edge_rotation_k("north") == 3


def test_placement_rotation_is_transformed_r_not_nesw_rank_t4() -> None:
    # T4: every placement's stored ``rotation`` is the transformed building R =
    # rotate_r(base_R=0, k) = edge_rotation_k(edge), NOT output_dir_rank (NESW).
    # The golden fixture's normal pool is East-facing, so R must be 0 (not 1).
    complete_map = golden_5x5_complete_map()
    result = generate_candidates(
        complete_map=complete_map,
        exterior_plan=minimal_l2_plan_for_golden(),
        gene_catalog=_catalog(),
    )
    assert result.normal_candidates
    for probed in result.normal_candidates:
        cand = probed.candidate
        assert cand.output_dir == Direction.E
        assert cand.rotation == 0, "East candidate R must be 0, not output_dir_rank(E)=1"
        for placement in cand.placements:
            assert placement.rotation == 0


def test_rotation_transforms_coordinates_not_r_only_t2() -> None:
    # T2: a non-identity rotation MUST move equipment coordinates; it is invalid to
    # keep coordinates fixed and only mutate R. Proven by the canonical extension at
    # (-3, 0): for south/west/north its rotated offset differs from the original.
    canonical = (-3, 0)
    for edge in ("south", "west", "north"):
        rotated = rotate_offset_east_to(canonical, edge)
        assert rotated != canonical, f"{edge}: coordinates must rotate, not stay R-only"
    # Locked T5 vectors (canonical-East extensions left of the miner).
    assert rotate_offset_east_to((-3, 0), "south") == (0, -3)
    assert rotate_offset_east_to((-3, 0), "west") == (3, 0)
    assert rotate_offset_east_to((-3, 0), "north") == (0, 3)


def test_free_void_output_sides_excludes_extension_and_non_void() -> None:
    # B2.1c-2 / T7 helper: the route-eligible output sides of an extractor are the
    # cardinal sides whose stub cell is (a) not occupied by an extension cell and
    # (b) in external void. A synthetic extractor at (5, 5) with one extension to its
    # west blocks the West face; only East and North stubs are placed in void.
    extractor = (5, 5)
    equipment = frozenset({(5, 5), (4, 5)})  # extension west of the extractor
    external_void = frozenset({(6, 5), (5, 4)})  # East stub (6,5) + North stub (5,4)
    sides = free_void_output_sides(extractor, equipment, external_void)
    assert set(sides) == {"east", "north"}
    assert "west" not in sides  # blocked by the extension cell (4, 5)
    assert "south" not in sides  # stub (5, 6) is not in external void


def test_independent_output_face_diverges_miner_and_extension_r_t7() -> None:
    # B2.1c-2 / T7: the extractor output side is INDEPENDENT of the bundle orientation.
    # A candidate is anchor × gene × bundle_orientation × output_side. Here the East-line
    # m3e variant (extensions {(6,5),(5,5),(4,5),(3,5)}, orientation k=0 so extension R=0)
    # is emitted with a SOUTH output face at anchor (6, 5). The miner R follows the output
    # side (edge_rotation_k("south")=1) while the extension R keeps the bundle orientation
    # (R=0): they DIVERGE, which the prior "output tied to orientation" wiring could not
    # express. The south stub (6, 6) is field, so R3 rejects it as a diagnostic.
    complete_map = golden_5x5_complete_map()
    result = generate_candidates(
        complete_map=complete_map,
        exterior_plan=minimal_l2_plan_for_golden(),
        gene_catalog=_catalog(),
    )
    diverged = next(
        probed
        for probed in result.diagnostic_rejected_candidates
        if probed.candidate.anchor_coord == (6, 5)
        and probed.candidate.gene_key == "m3e"
        and probed.candidate.output_dir == Direction.S
        and probed.candidate.mining_occupied_cells == frozenset({(6, 5), (5, 5), (4, 5), (3, 5)})
    )
    cand = diverged.candidate
    assert diverged.reject_reason == CandidateRejectReason.TRANSPORT_STUB_NOT_IN_VOID
    # miner R follows the independent output side (south -> 1)
    assert cand.rotation == 1
    miner = next(pl for pl in cand.placements if pl.cell_role == BundleCellRole.MINER)
    assert miner.rotation == 1
    # extensions keep the bundle orientation (east line -> R 0)
    extensions = [pl for pl in cand.placements if pl.cell_role == BundleCellRole.EXTENSION]
    assert len(extensions) == 3
    assert all(pl.rotation == 0 for pl in extensions)
    # T7 divergence: per-placement R differs between miner and extensions.
    assert miner.rotation != extensions[0].rotation


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


def test_golden_normal_pool_stage_funnel() -> None:
    # STAGE-AWARE contract test (B2.1c-3): the final pool of 2 is not a magic number —
    # it is the tail of the B2.1c-0 audit funnel. Each assertion below pins a stage so a
    # future regression localizes the broken stage rather than just "count changed":
    #
    #   canonical (2 genes)
    #     -> D4 expanded (8) -> extension-only deduped (5)   [dedupe_duplicate_count > 0]
    #     -> boundary survivors (equipment in field)
    #     -> independent output faces (void-facing, unblocked)
    #     -> route survivors to goal (8,4)                   [route_probe_succeeded == 2]
    #
    # The golden fixture's only route goal is the void cell (8, 4); the only extractor
    # whose +2 output cell lands in void is field cell (6, 4) facing East, so exactly the
    # m3e East-line and m0e single-cell bundles survive, m3e first by throughput.
    complete_map = golden_5x5_complete_map()
    result = generate_candidates(
        complete_map=complete_map,
        exterior_plan=minimal_l2_plan_for_golden(),
        gene_catalog=_catalog(),
    )
    metrics = result.metrics

    # final route-survivor pool (contract).
    assert len(result.normal_candidates) == 2
    assert metrics.normal_candidate_count == 2
    assert metrics.route_probe_succeeded_count == 2
    for probed in result.normal_candidates:
        assert probed.candidate.anchor_coord == (6, 4)
        assert probed.candidate.output_dir == Direction.E
        assert probed.candidate.route_probe_start_coord == (8, 4)
    # higher throughput gene (m3e) enumerates before m0e at the same anchor/direction.
    assert [p.candidate.gene_key for p in result.normal_candidates] == ["m3e", "m0e"]

    # funnel evidence: D4 collapsed duplicate extension layouts (m0e's empty-extension
    # variants), and the boundary/route funnel produced diagnostics.
    assert metrics.dedupe_duplicate_count > 0
    assert metrics.diagnostic_rejected_count > 0
    assert metrics.route_probe_attempt_count >= metrics.route_probe_succeeded_count


def test_generate_candidates_is_deterministic() -> None:
    # D1/D4: identical inputs yield an identical normal-pool candidate_id sequence
    # (stable sort over a deterministic enumeration order; no set/dict-order leakage).
    complete_map = golden_5x5_complete_map()
    plan = minimal_l2_plan_for_golden()
    first = generate_candidates(
        complete_map=complete_map, exterior_plan=plan, gene_catalog=_catalog()
    )
    second = generate_candidates(
        complete_map=complete_map, exterior_plan=plan, gene_catalog=_catalog()
    )
    assert [p.candidate.candidate_id for p in first.normal_candidates] == [
        p.candidate.candidate_id for p in second.normal_candidates
    ]
    assert [p.candidate.candidate_id for p in first.diagnostic_rejected_candidates] == [
        p.candidate.candidate_id for p in second.diagnostic_rejected_candidates
    ]


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
