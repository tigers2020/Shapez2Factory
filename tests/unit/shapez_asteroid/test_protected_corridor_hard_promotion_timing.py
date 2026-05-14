"""§14 hard promotion timing: ELA / existing transport vs STEP4 ``routing_state`` authority.

- Pre-commit: ``_build_step4_ctx_state`` must not put ELA trunk seeds into ``ctx.hard_extras``;
  only optional ``hard_protected_cells`` feeds that set (:mod:`step4_merge_routing`).
- Post-commit: ``hard_protected_corridors`` only from
  ``step4_routing_state._routing_state_from_committed_routes`` with
  ``source == "step4_committed_routes"``; ELA hints only in
  ``ela_trunk_seed_candidate_corridors`` (see :mod:`step4_routing_state`).
- Reclaim reads STEP4 ``routing_state`` only; ``existing_layout_solver_hints`` is not authority
  (:mod:`reclaim_corridors`).
- ``pass12_hard_protected_corridor_cells`` on ELA wire is a Pass12 transport-block overlay hint,
  not the same pool as ``routing_state`` hard corridors.
"""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    P4_RECLAIM_CORRIDOR_SOURCE_EMPTY,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass1_timeline_integration import (  # noqa: E501
    integrate_pass12_placement_into_working_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridors import (
    protected_corridors_for_reclaim,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4Route,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_goal_trunk_seed import (  # noqa: E501
    trunk_seed_union_from_existing_layout,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_merge_routing import (
    _build_step4_ctx_state,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_routing_state import (
    _routing_state_from_committed_routes,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    external_predicate_for_mining_map,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline
from tests.unit.shapez_asteroid.test_step4_merge_routing import (
    _decoded_shape_miners_with_belt_escape,
)


def _first_belt_cell(rows: list[dict[str, Any]]) -> Coord:
    for row in rows:
        if row.get("role") != "belt":
            continue
        x, y = row.get("x"), row.get("y")
        if isinstance(x, int) and isinstance(y, int) and x != 0:
            return (x, y)
    raise AssertionError("expected at least one belt cell")


def test_existing_layout_transport_not_hard_protected_before_step4_commit() -> None:
    """ELA trunk_seed hints feed trunk seeds / cheap_reuse only; never ``hard_extras`` pre-STEP4."""

    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    pr = stats.get("placement_records")
    belt = _first_belt_cell(m2)
    ela: dict[str, Any] = {
        "solver_hints": {
            "trunk_seed_cell_union": [list(belt)],
            "cleanup_candidate_cell_union": [],
        }
    }
    ctx, _state = _build_step4_ctx_state(
        m2,
        final_mining_map=fm,
        is_external=is_ext,
        placement_records=pr,
        existing_layout_analysis=ela,
        hard_protected_cells=None,
        force_route_attempt_placement_ids=None,
    )
    assert ctx.hard_extras == frozenset()
    hint = trunk_seed_union_from_existing_layout(ela)
    assert belt in hint
    assert belt in ctx.cheap_reuse_cells
    assert belt in ctx.trunk_seed_by_kind["shape_belt"]

    pcs = protected_corridors_for_reclaim(
        pass3_trace={},
        solver_routing_state=None,
        existing_layout_solver_hints={"fake_would_be_ignored": [[99, 99]]},
    )
    assert pcs.hard == frozenset() and pcs.soft == frozenset()
    assert pcs.source == P4_RECLAIM_CORRIDOR_SOURCE_EMPTY


def test_step4_committed_route_can_become_hard_or_soft_protected_with_reason() -> None:
    """Commit proof equivalent: ``source`` tag + stub/path-end hard rule (no extra ELA hard)."""

    route = Step4Route(
        extractor_cell=(9, 9),
        stub_cell=(10, 1),
        transport_kind="shape_belt",
        path=((10, 2), (10, 3), (10, 4)),
        merged_to_existing=False,
        reached_external=True,
        placement_id="p1",
    )
    ela = {
        "solver_hints": {
            "trunk_seed_cell_union": [[10, 2], [10, 3]],
            "cleanup_candidate_cell_union": [],
        }
    }
    rs = _routing_state_from_committed_routes((route,), existing_layout_analysis=ela)
    assert rs is not None
    assert rs["source"] == "step4_committed_routes"
    hard = {tuple(int(a) for a in c) for c in rs.get("hard_protected_corridors") or []}
    assert hard == {(10, 1), (10, 4)}
    ela_seeds = {
        tuple(int(a) for a in c) for c in rs.get("ela_trunk_seed_candidate_corridors") or []
    }
    assert ela_seeds == {(10, 2), (10, 3)}
    assert ela_seeds.isdisjoint(hard)
