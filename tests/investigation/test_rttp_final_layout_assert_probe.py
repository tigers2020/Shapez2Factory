"""Unit tests for read-only final_layout assert probe (E-track)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from harness.investigation.rttp_final_layout_assert_probe import (
    FinalLayoutAssertCode,
    diagnose_final_layout,
)
from harness.investigation.rttp_t1b_step_forensics import extract_t1b_forensics

# Narrow-corridor greenfield mineable block (see rttp_narrow_corridor_fixture).
_PROBE_ANCHOR: Coord = (6, 6)


def _minimal_pattern_e() -> BundlePattern:
    return BundlePattern(
        pattern_id="probe_test_e_len0",
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
    reachable: bool = True,
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
        reachable=reachable,
        catalog_placement_ref=None,
    )


def test_diagnose_fl03_occupied_overlap(
    greenfield_optimization_input,
) -> None:
    inp = greenfield_optimization_input
    a = _bundle_candidate(
        "a", _PROBE_ANCHOR, occupied=frozenset({_PROBE_ANCHOR}), output_stub=(8, 6)
    )
    b = _bundle_candidate(
        "b", _PROBE_ANCHOR, occupied=frozenset({_PROBE_ANCHOR}), output_stub=(8, 6)
    )
    code, detail = diagnose_final_layout(
        (a.candidate_id, b.candidate_id),
        frozenset(),
        {a.candidate_id: a, b.candidate_id: b},
        inp,
    )
    assert code is FinalLayoutAssertCode.FL_03
    assert detail["candidate_id"] == "b"
    assert detail["overlap_coords"]


def test_diagnose_fl07_reserved_vs_occupied(
    greenfield_optimization_input,
) -> None:
    inp = greenfield_optimization_input
    ext = _bundle_candidate(
        "ext", _PROBE_ANCHOR, occupied=frozenset({_PROBE_ANCHOR}), output_stub=(8, 6)
    )
    code, detail = diagnose_final_layout(
        (ext.candidate_id,),
        frozenset({_PROBE_ANCHOR, (8, 6)}),
        {ext.candidate_id: ext},
        inp,
    )
    assert code is FinalLayoutAssertCode.FL_07
    assert detail["reserved_vs_occupied"]


def test_diagnose_fl06_stub_not_in_reserved_when_reserved_nonempty(
    greenfield_optimization_input,
) -> None:
    inp = greenfield_optimization_input
    ext = _bundle_candidate(
        "ext", _PROBE_ANCHOR, occupied=frozenset({_PROBE_ANCHOR}), output_stub=(8, 6)
    )
    code, detail = diagnose_final_layout(
        (ext.candidate_id,),
        frozenset({_PROBE_ANCHOR}),
        {ext.candidate_id: ext},
        inp,
    )
    assert code is FinalLayoutAssertCode.FL_06
    assert detail["output_stub"] == (8, 6)
    assert detail["reserved_route_cells_nonempty"] is True


def test_diagnose_fl09_unreachable(greenfield_optimization_input) -> None:
    inp = greenfield_optimization_input
    bad = _bundle_candidate(
        "bad",
        _PROBE_ANCHOR,
        occupied=frozenset({_PROBE_ANCHOR}),
        output_stub=(8, 6),
        reachable=False,
    )
    code, detail = diagnose_final_layout(
        (bad.candidate_id,),
        frozenset(),
        {bad.candidate_id: bad},
        inp,
    )
    assert code is FinalLayoutAssertCode.FL_09
    assert detail["candidate_id"] == "bad"


def test_diagnose_ok_matches_validate_final_layout(
    greenfield_optimization_input,
) -> None:
    from django_apps.asteroid_lab.optimization.validation.final_validation import (
        validate_final_layout,
    )

    inp = greenfield_optimization_input
    ok = _bundle_candidate(
        "ok", _PROBE_ANCHOR, occupied=frozenset({_PROBE_ANCHOR}), output_stub=(8, 6)
    )
    committed = (ok.candidate_id,)
    reserved = frozenset()
    by_id = {ok.candidate_id: ok}
    code, _ = diagnose_final_layout(committed, reserved, by_id, inp)
    assert code is FinalLayoutAssertCode.FL_OK
    assert validate_final_layout(committed, reserved, by_id, inp) is True


def test_extract_t1b_forensics_from_algorithm_steps() -> None:
    steps = [
        {
            "step_id": "rttp.commit",
            "passed": False,
            "metrics": {
                "validation_passed": False,
                "committed_ids": ["c1", "c2"],
                "conflict_count": 0,
            },
        },
        {
            "step_id": "rttp.catalog_placement_validation",
            "passed": True,
            "metrics": {
                "matched_count": 2,
                "mismatch_candidate_count": 0,
                "catalog_error_issue_codes": [],
            },
        },
    ]
    forensics = extract_t1b_forensics(steps)
    assert forensics["commit_passed"] is False
    assert forensics["validation_passed"] is False
    assert forensics["committed_count"] == 2
    assert forensics["catalog_passed"] is True
    assert forensics["catalog_mismatch_count"] == 0
    assert forensics["pipeline_composition_anomaly"] is False


def test_extract_t1b_forensics_committed_ids_tuple_and_anomaly() -> None:
    steps = [
        {
            "step_id": "rttp.commit",
            "passed": True,
            "metrics": {
                "validation_passed": False,
                "committed_ids": ("c1",),
                "conflict_count": 0,
            },
        },
    ]
    forensics = extract_t1b_forensics(steps)
    assert forensics["committed_count"] == 1
    assert forensics["pipeline_composition_anomaly"] is True
