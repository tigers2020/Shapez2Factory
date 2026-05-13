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


def test_protected_corridors_read_merges_probe_discarded_from_pass3_trace() -> None:
    pc = protected_corridors_read_for_reclaim(
        pass3_trace={
            "protected_corridors": {"hard": [], "soft": []},
            "corridor_probe_discarded_cells": [[3, 4]],
        },
        solver_routing_state=None,
        existing_layout_solver_hints=None,
    )
    assert (3, 4) in pc.probe_discarded_cells
    assert corridor_lifecycle_state_for_cell(pc, (3, 4)) == fc.CORRIDOR_LIFECYCLE_DISCARDED


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
