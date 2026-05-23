"""RTTP v1 MacroBundleT3 compiler + probe gates — RTTP-G9, RTTP-G10 (PR-B)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.macros import (
    MacroCompileConfig,
    MacroRejectReason,
    compile_macros,
    probe_macro_shared_lift,
)
from django_apps.asteroid_lab.optimization.macros.macro_compiler import (
    _derive_shared_lift_stub_plan,
    _derive_shared_ring_port_intent,
)
from django_apps.asteroid_lab.optimization.macros.macro_dtos import SharedLiftStubPlan
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import (
    build_route_domain_from_skeleton,
)
from tests.support.macro_triple_greenfield_fixture import (
    build_macro_triple_greenfield_fixture,
    build_overlapping_macro_triple_candidates,
    build_unreachable_shared_trunk_skeleton,
)


def test_macro_compiler_emits_one_candidate_for_valid_triple() -> None:
    """RTTP-G9: valid triple → one MacroBundleCandidate in macro_normal."""

    fixture = build_macro_triple_greenfield_fixture()
    result = compile_macros(fixture.valid_triple, fixture.skeleton, fixture.inp)

    assert len(result.macro_normal) == 1
    macro_row = result.macro_normal[0]
    assert macro_row.reachable is True
    assert macro_row.macro_id == macro_row.macro.macro_id
    child_ids = {c.candidate_id for c in fixture.valid_triple}
    macro_child_ids = {
        macro_row.macro.child_a_id,
        macro_row.macro.child_b_id,
        macro_row.macro.child_c_id,
    }
    assert macro_child_ids == child_ids
    assert result.macro_rejected == ()


def test_macro_compiler_rejects_overlap() -> None:
    """RTTP-G9: overlapping child footprints → CHILD_OCCUPANCY_OVERLAP."""

    fixture = build_macro_triple_greenfield_fixture()
    overlapping = build_overlapping_macro_triple_candidates()
    result = compile_macros(overlapping, fixture.skeleton, fixture.inp)

    assert result.macro_normal == ()
    assert len(result.macro_rejected) == 1
    assert (
        result.macro_rejected[0].rejection_reason is MacroRejectReason.CHILD_OCCUPANCY_OVERLAP
    )


def test_macro_probe_rejects_unreachable_shared_trunk() -> None:
    """RTTP-G10: shared lift plan cannot reach trunk → SHARED_LIFT_UNREACHABLE."""

    fixture = build_macro_triple_greenfield_fixture()
    broken_skeleton = build_unreachable_shared_trunk_skeleton(fixture)
    domain = build_route_domain_from_skeleton(broken_skeleton, fixture.inp)

    shared_lift = SharedLiftStubPlan(
        lift_column_coords=frozenset({(99, 99), (99, 98)}),
        trunk_entry_coord=(99, 98),
        reserved_route_cells=frozenset({(99, 99), (99, 98)}),
    )
    probe = probe_macro_shared_lift(domain, shared_lift, max_expansions=500)
    assert probe.reachable is False

    result = compile_macros(fixture.valid_triple, broken_skeleton, fixture.inp)
    assert result.macro_normal == ()
    assert len(result.macro_rejected) == 1
    assert (
        result.macro_rejected[0].rejection_reason is MacroRejectReason.SHARED_LIFT_UNREACHABLE
    )


def test_macro_compiler_rejects_existing_shared_lift_when_probe_unreachable() -> None:
    """RTTP-G10: derived shared lift plan exists but probe fails → probe rejection branch."""

    fixture = build_macro_triple_greenfield_fixture()
    assert fixture.skeleton.lift_columns
    assert fixture.skeleton.ring_ports

    shared_lift = _derive_shared_lift_stub_plan(fixture.skeleton)
    shared_ring = _derive_shared_ring_port_intent(fixture.skeleton)
    assert shared_lift is not None
    assert shared_ring is not None

    domain = build_route_domain_from_skeleton(fixture.skeleton, fixture.inp)
    probe = probe_macro_shared_lift(domain, shared_lift, max_expansions=0)
    assert probe.reachable is False

    config = MacroCompileConfig(max_probe_expansions=0)
    result = compile_macros(
        fixture.valid_triple,
        fixture.skeleton,
        fixture.inp,
        config=config,
    )

    assert result.macro_normal == ()
    assert len(result.macro_rejected) == 1
    rejected = result.macro_rejected[0]
    assert rejected.rejection_reason is MacroRejectReason.SHARED_LIFT_UNREACHABLE
    assert rejected.route_probe_cost is not None


def test_macro_compiler_caps_enumeration_at_max_macro_candidates() -> None:
    fixture = build_macro_triple_greenfield_fixture()
    config = MacroCompileConfig(max_macro_candidates=0)
    result = compile_macros(fixture.valid_triple, fixture.skeleton, fixture.inp, config=config)

    assert result.macro_normal == ()
    assert len(result.macro_rejected) == 1
    assert (
        result.macro_rejected[0].rejection_reason
        is MacroRejectReason.EXCEEDS_MAX_MACRO_CANDIDATES
    )
