"""§14 protected corridor lifecycle: DTO labels, probe discard trace, atomic soft replace, STEP9."""

from __future__ import annotations

from unittest.mock import patch

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation import constants as fc
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridor_contracts import (  # noqa: E501
    ProtectedCorridors,
    corridor_lifecycle_state_for_cell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridors import (
    protected_corridors_read_for_reclaim,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.protected_corridor_replace import (  # noqa: E501
    try_atomic_replace_soft_corridor,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4Route,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_routing_state import (
    _routing_state_from_committed_routes,
    compute_hard_promotion_audit,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as fv_mod,
)
from tests.unit.shapez_asteroid.test_reclaim_shadow import (
    _base_final_mining_map,
    _external_east,
    _minimal_routed_shape_map,
)


def test_rejected_by_aliases_match_document_strings() -> None:
    assert fc.REJECTED_BY_HARD_PROTECTED_CORRIDOR == "rejected_by_hard_protected_corridor"
    assert fc.REJECTED_BY_NO_REPLACEMENT_ROUTE == "rejected_by_no_replacement_route"


def test_corridor_lifecycle_state_for_cell_tiers() -> None:
    pc = ProtectedCorridors(
        hard=frozenset({(1, 1)}),
        soft=frozenset({(2, 2)}),
        candidate=frozenset({(9, 9)}),
        source="test",
        probe_candidate_cells=frozenset({(8, 8)}),
        probe_discarded_cells=frozenset({(7, 7)}),
    )
    assert corridor_lifecycle_state_for_cell(pc, (1, 1)) == fc.CORRIDOR_LIFECYCLE_HARD
    assert corridor_lifecycle_state_for_cell(pc, (2, 2)) == fc.CORRIDOR_LIFECYCLE_SOFT
    assert corridor_lifecycle_state_for_cell(pc, (7, 7)) == fc.CORRIDOR_LIFECYCLE_DISCARDED
    assert corridor_lifecycle_state_for_cell(pc, (8, 8)) == fc.CORRIDOR_LIFECYCLE_CANDIDATE
    assert corridor_lifecycle_state_for_cell(pc, (9, 9)) == fc.CORRIDOR_LIFECYCLE_CANDIDATE
    assert corridor_lifecycle_state_for_cell(pc, (0, 0)) is None


def test_protected_corridors_read_ignores_pass3_trace_probe_fields_at_runtime() -> None:
    """§14: reclaim must not reconstruct probe lifecycle from pass3_trace (telemetry only)."""

    pc = protected_corridors_read_for_reclaim(
        pass3_trace={
            "protected_corridors": {"hard": [], "soft": []},
            "corridor_probe_discarded_cells": [[3, 4]],
            "corridor_probe_candidate_cells": [[5, 5]],
        },
        solver_routing_state={
            "hard_protected_corridors": [],
            "soft_protected_corridors": [],
            "protected_corridors": {"hard": [], "soft": []},
        },
        existing_layout_solver_hints=None,
    )
    assert pc.probe_discarded_cells == frozenset()
    assert pc.probe_candidate_cells == frozenset()
    assert corridor_lifecycle_state_for_cell(pc, (3, 4)) is None


def test_step4_committed_routing_state_marks_soft_hard_pools_and_empty_probe_candidates() -> None:
    r = Step4Route(
        extractor_cell=(10, 1),
        stub_cell=(11, 1),
        transport_kind="shape_belt",
        path=((11, 1), (12, 1), (13, 1)),
        merged_to_existing=False,
        reached_external=True,
        placement_id="p1",
    )
    st = _routing_state_from_committed_routes((r,), cells=None, is_external=None)
    assert st is not None
    assert st["corridor_probe_candidates_at_commit"] == []
    assert st["corridor_lifecycle_soft_pool"] == fc.CORRIDOR_LIFECYCLE_SOFT
    assert st["corridor_lifecycle_hard_pool"] == fc.CORRIDOR_LIFECYCLE_HARD
    assert isinstance(st.get("soft_protected_corridors"), list)
    assert len(st["soft_protected_corridors"]) >= 1


def test_soft_replace_exhausted_trace_when_probe_returns_no_path() -> None:
    """§14.3: exhaustive replacement failure records ``replacement_search_exhausted`` + budgets."""

    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
        "placement_stub_route_probe_path",
        return_value=None,
    ):
        out, tr = try_atomic_replace_soft_corridor(
            m,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 10},
            solver_routing_state={
                "hard_protected_corridors": [],
                "soft_protected_corridors": [[14, 2]],
            },
            old_soft_corridor_cells=[(14, 2)],
            is_external=_external_east,
        )
    assert out is None
    assert tr.get("replacement_search_exhausted") is True
    keys = list(fc.CORRIDOR_REPLACEMENT_BUDGET_KEYS_SOFT_REPLACE)
    assert tr.get("replacement_budget_keys") == keys
    assert tr.get("replacement_frontier_last_size") == 0


def test_final_validation_module_docstring_forbids_new_hard_corridors() -> None:
    """Contract: STEP9 stays an assertion gate (see module docstring)."""

    doc = fv_mod.__doc__ or ""
    low = doc.lower()
    assert "does not promote" in low
    assert "hard_protected_corridors" in low


def test_compute_hard_promotion_audit_flags_missing_promotion_trace() -> None:
    rs = {"hard_protected_corridors": [[2, 2]], "hard_protected_promotions": []}
    aud = compute_hard_promotion_audit(rs)
    assert aud["hard_promotion_without_proof_count"] == 1


def test_compute_hard_promotion_audit_ok_when_promotions_cover_hard() -> None:
    rs = {
        "hard_protected_corridors": [[2, 2]],
        "hard_protected_promotions": [
            {"cell": [2, 2], "reason": fc.HARD_PROMOTION_REASON_OUTPUT_STUB},
        ],
    }
    assert compute_hard_promotion_audit(rs)["hard_promotion_without_proof_count"] == 0


def test_hard_terminal_promoted_when_replacement_search_exhausted_reason_on_route() -> None:
    r = Step4Route(
        extractor_cell=(1, 1),
        stub_cell=(1, 2),
        transport_kind="shape_belt",
        path=((1, 3), (1, 4)),
        merged_to_existing=False,
        reached_external=True,
        placement_id="p1",
        trunk_terminal_hard_reason=fc.HARD_PROMOTION_REASON_REPLACEMENT_SEARCH_EXHAUSTED,
    )
    st = _routing_state_from_committed_routes((r,), cells=None, is_external=None)
    assert st is not None
    hard = {tuple(int(a) for a in c) for c in st.get("hard_protected_corridors") or []}
    assert hard == {(1, 2), (1, 4)}
    byr = st.get("protected_corridor_hard_by_reason") or {}
    assert fc.HARD_PROMOTION_REASON_OUTPUT_STUB in byr
    assert fc.HARD_PROMOTION_REASON_REPLACEMENT_SEARCH_EXHAUSTED in byr


def test_soft_active_is_intersection_of_soft_pool_and_on_map_transport() -> None:
    """§14 reclaim scan: ``soft_active`` ⊆ ``soft`` (cells still carrying transport on map)."""

    soft = frozenset({(1, 1), (2, 2)})
    transport_on_map = frozenset({(2, 2), (5, 5)})
    soft_active = frozenset(c for c in soft if c in transport_on_map)
    assert (1, 1) not in soft_active
    assert (2, 2) in soft_active
