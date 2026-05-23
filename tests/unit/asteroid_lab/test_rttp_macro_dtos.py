"""RTTP v1 MacroBundleT3 DTO smoke tests (PR-A)."""

from __future__ import annotations

import re
from dataclasses import replace

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.pattern_library import build_pattern_library
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.optimization.macros import (
    MacroBundleCandidate,
    MacroBundleT3,
    MacroRejectReason,
    SharedLiftStubPlan,
    SharedRingPortIntent,
    child_occupancy_overlaps,
    derive_macro_id,
    union_child_occupied_cells,
)

_MACRO_ID_HEX = re.compile(r"^[0-9a-f]{64}$")
_CANDIDATE_ID_SAFE = re.compile(r"^[0-9a-zA-Z_,:\-]+$")


def _bundle(
    candidate_id: str,
    anchor: Coord,
    *,
    occupied: frozenset[Coord] | None = None,
) -> BundleCandidate:
    pattern = build_pattern_library()[0]
    anchor_occupied = occupied or frozenset({anchor, (anchor[0] + 1, anchor[1])})
    output_stub = (anchor[0] + 2, anchor[1])
    return BundleCandidate(
        candidate_id=candidate_id,
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=anchor_occupied,
        output_stub=output_stub,
        output_dir="E",
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=pattern.throughput_factor,
        route_probe_cost=1,
        reachable=True,
    )


def _shared_lift() -> SharedLiftStubPlan:
    lift = frozenset({(10, 5), (10, 6)})
    return SharedLiftStubPlan(
        lift_column_coords=lift,
        trunk_entry_coord=(10, 7),
        reserved_route_cells=lift | frozenset({(10, 7)}),
    )


def _shared_ring() -> SharedRingPortIntent:
    return SharedRingPortIntent(
        primary_ring_port_coord=(4, 5),
        preferred_dir="E",
        secondary_port_coords=frozenset(),
    )


def _macro_bundle(
    child_a: BundleCandidate,
    child_b: BundleCandidate,
    child_c: BundleCandidate,
    combined: frozenset[Coord],
) -> MacroBundleT3:
    children = (child_a, child_b, child_c)
    shared_lift = _shared_lift()
    shared_ring = _shared_ring()
    macro_id = derive_macro_id(
        child_a_id=child_a.candidate_id,
        child_b_id=child_b.candidate_id,
        child_c_id=child_c.candidate_id,
        shared_lift_stub_plan=shared_lift,
        shared_ring_port_intent=shared_ring,
    )
    return MacroBundleT3(
        macro_id=macro_id,
        child_a_id=child_a.candidate_id,
        child_b_id=child_b.candidate_id,
        child_c_id=child_c.candidate_id,
        children=children,
        shared_lift_stub_plan=shared_lift,
        shared_ring_port_intent=shared_ring,
        combined_occupied_cells=combined,
        macro_throughput_factor=sum(c.throughput_factor for c in children),
        topology_signature=tuple(c.pattern.pattern_id for c in children),
    )


@pytest.mark.parametrize(
    ("dto_factory",),
    [
        (_shared_lift,),
        (_shared_ring,),
    ],
)
def test_supporting_dtos_frozen_and_hashable(dto_factory) -> None:
    first = dto_factory()
    second = replace(first)
    assert first == second
    assert hash(first) == hash(second)


def test_macro_bundle_t3_frozen_and_hashable() -> None:
    a = _bundle("5,5:lin_e_len0:shape_belt", (5, 5), occupied=frozenset({(5, 5)}))
    b = _bundle("6,5:lin_e_len0:shape_belt", (6, 5), occupied=frozenset({(6, 5)}))
    c = _bundle("7,5:lin_e_len0:shape_belt", (7, 5), occupied=frozenset({(7, 5)}))
    combined = union_child_occupied_cells((a, b, c))
    macro = _macro_bundle(a, b, c, combined)
    again = replace(macro)
    assert macro == again
    assert hash(macro) == hash(again)


def test_macro_bundle_candidate_frozen_and_hashable() -> None:
    a = _bundle("5,5:lin_e_len0:shape_belt", (5, 5), occupied=frozenset({(5, 5)}))
    b = _bundle("6,5:lin_e_len0:shape_belt", (6, 5), occupied=frozenset({(6, 5)}))
    c = _bundle("7,5:lin_e_len0:shape_belt", (7, 5), occupied=frozenset({(7, 5)}))
    combined = union_child_occupied_cells((a, b, c))
    macro = _macro_bundle(a, b, c, combined)
    row = MacroBundleCandidate(
        macro_id=macro.macro_id,
        macro=macro,
        route_probe_cost=3,
        reachable=True,
    )
    again = replace(row)
    assert row == again
    assert hash(row) == hash(again)


def test_macro_reject_reason_stable_strings() -> None:
    expected = {
        "CHILD_OCCUPANCY_OVERLAP": "child_occupancy_overlap",
        "RING_PORT_MISMATCH": "ring_port_mismatch",
        "SHARED_LIFT_UNREACHABLE": "shared_lift_unreachable",
        "CHILD_NOT_IN_NORMAL_POOL": "child_not_in_normal_pool",
        "TRANSPORT_KIND_MISMATCH": "transport_kind_mismatch",
        "PROTECTED_CORRIDOR_CONFLICT": "protected_corridor_conflict",
        "EXCEEDS_MAX_MACRO_CANDIDATES": "exceeds_max_macro_candidates",
    }
    for name, value in expected.items():
        reason = MacroRejectReason[name]
        assert reason.value == value
        assert str(reason) == value


def test_derive_macro_id_deterministic_across_child_id_order() -> None:
    shared_lift = _shared_lift()
    shared_ring = _shared_ring()
    ids = (
        "5,5:lin_e_len0:shape_belt",
        "6,5:lin_e_len0:shape_belt",
        "7,5:lin_e_len0:shape_belt",
    )
    permutations = (
        ids,
        (ids[1], ids[0], ids[2]),
        (ids[2], ids[1], ids[0]),
    )
    digests = [
        derive_macro_id(
            child_a_id=a,
            child_b_id=b,
            child_c_id=c,
            shared_lift_stub_plan=shared_lift,
            shared_ring_port_intent=shared_ring,
        )
        for a, b, c in permutations
    ]
    assert len(set(digests)) == 1


def test_derive_macro_id_charset_lowercase_hex() -> None:
    macro_id = derive_macro_id(
        child_a_id="5,5:lin_e_len0:shape_belt",
        child_b_id="6,5:lin_e_len0:shape_belt",
        child_c_id="7,5:lin_e_len0:shape_belt",
        shared_lift_stub_plan=_shared_lift(),
        shared_ring_port_intent=_shared_ring(),
    )
    assert _MACRO_ID_HEX.match(macro_id)
    assert not _CANDIDATE_ID_SAFE.match(macro_id) or _MACRO_ID_HEX.match(macro_id)


def test_combined_occupied_cells_explicit_union_field() -> None:
    a = _bundle("5,5:lin_e_len0:shape_belt", (5, 5), occupied=frozenset({(5, 5)}))
    b = _bundle("6,5:lin_e_len0:shape_belt", (6, 5), occupied=frozenset({(6, 5)}))
    c = _bundle("7,5:lin_e_len0:shape_belt", (7, 5), occupied=frozenset({(7, 5)}))
    union = union_child_occupied_cells((a, b, c))
    explicit_superset = union | frozenset({(99, 99)})
    macro = _macro_bundle(a, b, c, explicit_superset)
    assert macro.combined_occupied_cells == explicit_superset
    assert macro.combined_occupied_cells != union
    assert not child_occupancy_overlaps((a, b, c))


def test_child_occupancy_overlaps_detects_shared_cells() -> None:
    a = _bundle("5,5:lin_e_len0:shape_belt", (5, 5), occupied=frozenset({(5, 5), (5, 6)}))
    b = _bundle("6,5:lin_e_len0:shape_belt", (6, 5), occupied=frozenset({(5, 6), (6, 5)}))
    c = _bundle("7,5:lin_e_len0:shape_belt", (7, 5), occupied=frozenset({(7, 5)}))
    assert child_occupancy_overlaps((a, b, c))
