"""P3-F: branch detector + replacement probe + commit alias trace tests.

Covers ``p3f_*`` contract keys, priority-order list, ``parallel_duplicate_branch``
inactive reason, kind-priority best selection, reject reason mapping, and end-to-end
forwarding into ``pass3_summary`` via ``build_solver_timeline``.
"""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    P3E3_REJECT_CONNECTIVITY,
    P3E3_REJECT_HARD_PROTECTED_CORRIDOR,
    P3E3_REJECT_NO_REPLACEMENT_ROUTE,
    P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE,
    P3F_COMMIT_REASON_NORMAL_GAIN,
    P3F_KIND_LONG_PERIMETER_DETOUR,
    P3F_KIND_LOW_REUSE,
    P3F_KIND_MINEABLE_HEAVY,
    P3F_KIND_NONE,
    P3F_KIND_PARALLEL_DUPLICATE,
    P3F_KIND_PRIORITY_ORDER,
    P3F_REJECTED_NO_REPLACEMENT_ROUTE,
    P3F_REJECTED_REASON_UNMAPPED,
    P3F_REPLACEMENT_SEARCH_MODE_LEX_PER_STUB,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_e3_guarded_dto import (
    P3E3GuardedCommitCandidate,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_f_branch_candidate import (  # noqa: E501
    P3F_PARALLEL_INACTIVE_GREEDY_PATHS_UNAVAILABLE,
    P3F_REJECT_REASON_TABLE,
    p3f_build_trace,
    p3f_disabled_trace,
    p3f_map_rejected_reason,
    p3f_pass3_summary_placeholder,
)


def _candidate(
    *,
    candidate: frozenset[tuple[int, int]] = frozenset(),
    removed: frozenset[tuple[int, int]] = frozenset(),
    added: frozenset[tuple[int, int]] = frozenset(),
    baseline_route_length: int | None = 10,
    candidate_route_length: int | None = 9,
    precheck_passed: bool = True,
    rejected_reason: str | None = None,
    attempted: bool = True,
    hard_protected: frozenset[tuple[int, int]] = frozenset(),
) -> P3E3GuardedCommitCandidate:
    return P3E3GuardedCommitCandidate(
        attempted=attempted,
        candidate_transport_cells=candidate,
        removed_transport_cells=removed,
        added_transport_cells=added,
        preserved_stub_cells=frozenset(),
        touched_hard_protected_cells=frozenset(),
        touched_soft_protected_cells=frozenset(),
        replacement_route_cells=frozenset(),
        baseline_route_length=baseline_route_length,
        candidate_route_length=candidate_route_length,
        route_length_ratio=None,
        precheck_passed=precheck_passed,
        rejected_reason=rejected_reason,
        hard_protected_corridors=hard_protected,
    )


def test_p3f_map_rejected_reason_known_constants_route_to_namespace() -> None:
    mapped, raw = p3f_map_rejected_reason(P3E3_REJECT_NO_REPLACEMENT_ROUTE)
    assert mapped == P3F_REJECTED_NO_REPLACEMENT_ROUTE
    assert raw is None
    mapped2, raw2 = p3f_map_rejected_reason(P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE)
    assert mapped2 == P3F_REJECTED_NO_REPLACEMENT_ROUTE
    assert raw2 is None
    mapped3, raw3 = p3f_map_rejected_reason(P3E3_REJECT_CONNECTIVITY)
    assert mapped3 == P3E3_REJECT_CONNECTIVITY
    assert raw3 is None
    assert P3E3_REJECT_HARD_PROTECTED_CORRIDOR in P3F_REJECT_REASON_TABLE


def test_p3f_map_rejected_reason_unknown_falls_back_and_preserves_raw() -> None:
    mapped, raw = p3f_map_rejected_reason("totally_made_up")
    assert mapped == P3F_REJECTED_REASON_UNMAPPED
    assert raw == "totally_made_up"


def test_p3f_map_rejected_reason_none_returns_none_pair() -> None:
    assert p3f_map_rejected_reason(None) == (None, None)


def test_p3f_disabled_trace_has_all_contract_keys() -> None:
    d = p3f_disabled_trace()
    expected = {
        "p3f_candidate_kind_count",
        "p3f_best_candidate_kind",
        "p3f_candidate_kinds",
        "p3f_candidate_internal_cells",
        "p3f_candidate_mineable_freed",
        "p3f_candidate_reuse_ratio",
        "p3f_candidate_score_tuple",
        "p3f_replacement_connected",
        "p3f_fixed_output_stub_preserved",
        "p3f_hard_protected_preserved",
        "p3f_internal_transport_delta",
        "p3f_route_cell_delta",
        "p3f_route_cell_delta_within_budget",
        "p3f_replacement_search_mode",
        "p3f_replacement_expanded_nodes",
        "p3f_replacement_search_ms",
        "p3f_parallel_duplicate_inactive_reason",
        "p3f_committed",
        "p3f_transport_cells_added",
        "p3f_transport_cells_removed",
        "p3f_internal_transport_saved",
        "p3f_commit_reason",
        "p3f_rejected_reason",
        "p3f_rejected_reason_raw",
    }
    assert expected.issubset(d.keys())
    assert d["p3f_best_candidate_kind"] == P3F_KIND_NONE
    assert d["p3f_candidate_score_tuple"] == [0, 0.0, 0, 0]
    assert (
        d["p3f_parallel_duplicate_inactive_reason"]
        == P3F_PARALLEL_INACTIVE_GREEDY_PATHS_UNAVAILABLE
    )


def test_p3f_pass3_summary_placeholder_uses_supplied_rejected_reason() -> None:
    ph = p3f_pass3_summary_placeholder(rejected_reason="pass3_not_eligible")
    assert ph["p3f_rejected_reason"] == "pass3_not_eligible"
    assert ph["p3f_candidate_kinds"] is None
    assert ph["p3f_committed"] is None


def test_p3f_build_trace_commit_emits_normal_gain_and_kind_priority() -> None:
    candidate = frozenset({(1, 1), (2, 1)})
    removed = frozenset({(3, 1), (4, 1), (5, 1)})
    asteroid = frozenset({(3, 1), (4, 1), (5, 1), (1, 1)})
    mineable = frozenset({(3, 1), (4, 1)})
    trunk = frozenset({(1, 1), (2, 1)})
    dto = _candidate(
        candidate=candidate,
        removed=removed,
        added=frozenset({(1, 1), (2, 1)}),
        baseline_route_length=12,
        candidate_route_length=8,
    )
    trace = p3f_build_trace(
        dto=dto,
        baseline_internal_transport_count=3,
        candidate_internal_transport_count=1,
        fixed_output_stubs=frozenset(),
        hard_protected_corridors=frozenset(),
        trunk_cells=trunk,
        mineable=mineable,
        asteroid=asteroid,
        sum_lex_len=10,
        sum_gr_len=12,
        greedy_paths=None,
        committed=True,
        rejected_reason_raw=None,
        internal_transport_saved=2,
        search_ms=4,
        expanded_nodes=42,
    )
    assert trace["p3f_committed"] is True
    assert trace["p3f_commit_reason"] == P3F_COMMIT_REASON_NORMAL_GAIN
    assert trace["p3f_rejected_reason"] is None
    assert trace["p3f_rejected_reason_raw"] is None
    assert trace["p3f_replacement_connected"] is True
    assert trace["p3f_internal_transport_delta"] == -2
    assert trace["p3f_route_cell_delta"] == 8 - 12
    assert trace["p3f_replacement_search_mode"] == P3F_REPLACEMENT_SEARCH_MODE_LEX_PER_STUB
    assert trace["p3f_replacement_search_ms"] == 4
    assert trace["p3f_replacement_expanded_nodes"] == 42
    kinds = trace["p3f_candidate_kinds"]
    assert P3F_KIND_MINEABLE_HEAVY in kinds
    assert P3F_KIND_LOW_REUSE in kinds
    assert trace["p3f_best_candidate_kind"] == P3F_KIND_MINEABLE_HEAVY
    assert trace["p3f_candidate_kind_count"] == len(kinds)
    expected_subseq = [k for k in P3F_KIND_PRIORITY_ORDER if k in set(kinds)]
    assert kinds == expected_subseq
    assert kinds.index(P3F_KIND_MINEABLE_HEAVY) < kinds.index(P3F_KIND_LOW_REUSE)


def test_p3f_build_trace_long_detour_label_emitted_from_shadow_lengths() -> None:
    dto = _candidate(
        candidate=frozenset({(1, 1)}),
        removed=frozenset(),
        added=frozenset(),
        baseline_route_length=8,
        candidate_route_length=7,
    )
    trace = p3f_build_trace(
        dto=dto,
        baseline_internal_transport_count=0,
        candidate_internal_transport_count=0,
        fixed_output_stubs=frozenset(),
        hard_protected_corridors=frozenset(),
        trunk_cells=frozenset(),
        mineable=frozenset(),
        asteroid=frozenset(),
        sum_lex_len=10,
        sum_gr_len=20,
        greedy_paths=None,
        committed=True,
        rejected_reason_raw=None,
        internal_transport_saved=0,
        search_ms=0,
        expanded_nodes=None,
    )
    assert P3F_KIND_LONG_PERIMETER_DETOUR in trace["p3f_candidate_kinds"]


def test_p3f_build_trace_parallel_duplicate_active_when_paths_supplied() -> None:
    # Two stubs reach trunk cells one apart (Manhattan 1) with no shared cells:
    # ratio 0/5 = 0 ≤ 0.25 → parallel_duplicate fires.
    pa = [(10, 10), (10, 9), (10, 8), (10, 7), (10, 6)]
    pb = [(20, 10), (20, 9), (20, 8), (20, 7), (11, 6)]
    trunk = frozenset({(10, 6), (11, 6)})
    dto = _candidate(
        candidate=frozenset({(10, 6), (11, 6)}),
        removed=frozenset(),
        added=frozenset(),
    )
    trace = p3f_build_trace(
        dto=dto,
        baseline_internal_transport_count=0,
        candidate_internal_transport_count=0,
        fixed_output_stubs=frozenset(),
        hard_protected_corridors=frozenset(),
        trunk_cells=trunk,
        mineable=frozenset(),
        asteroid=frozenset(),
        sum_lex_len=None,
        sum_gr_len=None,
        greedy_paths=[pa, pb],
        committed=False,
        rejected_reason_raw=None,
        internal_transport_saved=0,
        search_ms=0,
        expanded_nodes=None,
    )
    assert P3F_KIND_PARALLEL_DUPLICATE in trace["p3f_candidate_kinds"]
    assert trace["p3f_parallel_duplicate_inactive_reason"] is None


def test_p3f_build_trace_parallel_duplicate_inactive_when_paths_missing() -> None:
    dto = _candidate(
        candidate=frozenset({(1, 1)}),
        removed=frozenset(),
        added=frozenset(),
    )
    trace = p3f_build_trace(
        dto=dto,
        baseline_internal_transport_count=0,
        candidate_internal_transport_count=0,
        fixed_output_stubs=frozenset(),
        hard_protected_corridors=frozenset(),
        trunk_cells=frozenset(),
        mineable=frozenset(),
        asteroid=frozenset(),
        sum_lex_len=None,
        sum_gr_len=None,
        greedy_paths=None,
        committed=False,
        rejected_reason_raw=None,
        internal_transport_saved=0,
        search_ms=0,
        expanded_nodes=None,
    )
    assert P3F_KIND_PARALLEL_DUPLICATE not in trace["p3f_candidate_kinds"]
    assert (
        trace["p3f_parallel_duplicate_inactive_reason"]
        == P3F_PARALLEL_INACTIVE_GREEDY_PATHS_UNAVAILABLE
    )


def test_p3f_build_trace_reject_maps_no_replacement_route() -> None:
    dto = _candidate(
        candidate=frozenset(),
        removed=frozenset(),
        added=frozenset(),
        precheck_passed=False,
        rejected_reason=P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE,
        baseline_route_length=None,
        candidate_route_length=None,
    )
    trace = p3f_build_trace(
        dto=dto,
        baseline_internal_transport_count=0,
        candidate_internal_transport_count=0,
        fixed_output_stubs=frozenset(),
        hard_protected_corridors=frozenset(),
        trunk_cells=frozenset(),
        mineable=frozenset(),
        asteroid=frozenset(),
        sum_lex_len=None,
        sum_gr_len=None,
        greedy_paths=None,
        committed=False,
        rejected_reason_raw=P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE,
        internal_transport_saved=0,
        search_ms=0,
        expanded_nodes=None,
    )
    assert trace["p3f_committed"] is False
    assert trace["p3f_commit_reason"] is None
    assert trace["p3f_rejected_reason"] == P3F_REJECTED_NO_REPLACEMENT_ROUTE
    assert trace["p3f_rejected_reason_raw"] is None
    assert trace["p3f_replacement_connected"] is False
    assert trace["p3f_route_cell_delta"] is None
    assert trace["p3f_route_cell_delta_within_budget"] is None


def test_p3f_build_trace_unmapped_reject_preserves_raw_in_namespace_field() -> None:
    dto = _candidate(
        candidate=frozenset(),
        removed=frozenset(),
        added=frozenset(),
        precheck_passed=False,
        rejected_reason="exotic_internal_state",
    )
    trace = p3f_build_trace(
        dto=dto,
        baseline_internal_transport_count=0,
        candidate_internal_transport_count=0,
        fixed_output_stubs=frozenset(),
        hard_protected_corridors=frozenset(),
        trunk_cells=frozenset(),
        mineable=frozenset(),
        asteroid=frozenset(),
        sum_lex_len=None,
        sum_gr_len=None,
        greedy_paths=None,
        committed=False,
        rejected_reason_raw="exotic_internal_state",
        internal_transport_saved=0,
        search_ms=0,
        expanded_nodes=None,
    )
    assert trace["p3f_rejected_reason"] == P3F_REJECTED_REASON_UNMAPPED
    assert trace["p3f_rejected_reason_raw"] == "exotic_internal_state"


def test_p3f_build_trace_internal_delta_uses_single_definition() -> None:
    """`internal_delta` = candidate_internal - baseline_internal, no fallback."""

    dto = _candidate(
        candidate=frozenset({(1, 1)}),
        removed=frozenset({(2, 1)}),
        added=frozenset({(1, 1)}),
    )
    trace = p3f_build_trace(
        dto=dto,
        baseline_internal_transport_count=7,
        candidate_internal_transport_count=2,
        fixed_output_stubs=frozenset(),
        hard_protected_corridors=frozenset(),
        trunk_cells=frozenset(),
        mineable=frozenset(),
        asteroid=frozenset(),
        sum_lex_len=None,
        sum_gr_len=None,
        greedy_paths=None,
        committed=True,
        rejected_reason_raw=None,
        internal_transport_saved=5,
        search_ms=0,
        expanded_nodes=None,
    )
    assert trace["p3f_internal_transport_delta"] == -5
    assert trace["p3f_candidate_score_tuple"][0] == -5


def test_p3f_build_trace_fixed_stub_preservation_signal() -> None:
    stubs = frozenset({(1, 1), (2, 2)})
    candidate = frozenset({(1, 1), (2, 2), (3, 3)})
    dto = _candidate(candidate=candidate)
    trace_ok = p3f_build_trace(
        dto=dto,
        baseline_internal_transport_count=0,
        candidate_internal_transport_count=0,
        fixed_output_stubs=stubs,
        hard_protected_corridors=frozenset(),
        trunk_cells=frozenset(),
        mineable=frozenset(),
        asteroid=frozenset(),
        sum_lex_len=None,
        sum_gr_len=None,
        greedy_paths=None,
        committed=True,
        rejected_reason_raw=None,
        internal_transport_saved=0,
        search_ms=0,
        expanded_nodes=None,
    )
    assert trace_ok["p3f_fixed_output_stub_preserved"] is True

    dto_missing = _candidate(candidate=frozenset({(3, 3)}))
    trace_missing = p3f_build_trace(
        dto=dto_missing,
        baseline_internal_transport_count=0,
        candidate_internal_transport_count=0,
        fixed_output_stubs=stubs,
        hard_protected_corridors=frozenset(),
        trunk_cells=frozenset(),
        mineable=frozenset(),
        asteroid=frozenset(),
        sum_lex_len=None,
        sum_gr_len=None,
        greedy_paths=None,
        committed=False,
        rejected_reason_raw=None,
        internal_transport_saved=0,
        search_ms=0,
        expanded_nodes=None,
    )
    assert trace_missing["p3f_fixed_output_stub_preserved"] is False


def test_solver_timeline_pass3_summary_carries_p3f_keys() -> None:
    """End-to-end: ``p3f_*`` keys forwarded into ``pass3_summary`` via prefix loop."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
        build_solver_timeline,
    )
    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    decoded = _decoded_miners_with_belt_escape()
    out = build_solver_timeline(decoded)
    ss = out["solver_summary"]
    expected_keys = {
        "p3f_candidate_kind_count",
        "p3f_best_candidate_kind",
        "p3f_candidate_kinds",
        "p3f_candidate_internal_cells",
        "p3f_candidate_mineable_freed",
        "p3f_candidate_reuse_ratio",
        "p3f_candidate_score_tuple",
        "p3f_replacement_connected",
        "p3f_fixed_output_stub_preserved",
        "p3f_hard_protected_preserved",
        "p3f_internal_transport_delta",
        "p3f_route_cell_delta",
        "p3f_route_cell_delta_within_budget",
        "p3f_replacement_search_mode",
        "p3f_replacement_expanded_nodes",
        "p3f_replacement_search_ms",
        "p3f_parallel_duplicate_inactive_reason",
        "p3f_committed",
        "p3f_transport_cells_added",
        "p3f_transport_cells_removed",
        "p3f_internal_transport_saved",
        "p3f_commit_reason",
        "p3f_rejected_reason",
        "p3f_rejected_reason_raw",
    }
    assert expected_keys.issubset(ss.keys())
