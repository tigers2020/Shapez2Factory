"""Bounded STEP4 recovery for Pass2 provisional placements after a routing failure.

At most one recovery *session* per failed Pass2 job: deterministically evaluates a capped set
of local variants (legal output rotation, ``cheap_reuse_cells`` ablations, margin-focused goal
subset). Picks the best successful path by
``(new_internal_transport_cells, route_cost, path_len, path_lex)``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import shape_miner_output_cell
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    blocked_cells as _blocked_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    want_role as _want_role,
)

from ..validation.final_validation import transport_cells_reaching_external
from .step4_goal_trunk_seed import build_step4_goal_set
from .step4_routing_permission import step4_step_cost

_MAX_RECOVERY_VARIANT_EVALS = 16

_MISSING = object()


def _rotation_probe_order(current_r: int) -> tuple[int, ...]:
    order: list[int] = []
    for cand in (current_r % 4, *range(4)):
        if cand not in order:
            order.append(cand)
    return tuple(order)


def _touch_coords_for_recovery(ext_cell: Coord, rec: PlacementCommitRecord) -> frozenset[Coord]:
    out: set[Coord] = {ext_cell, rec.stub_cell, *rec.extension_cells}
    for r in range(4):
        sc = shape_miner_output_cell(ext_cell, r)
        if sc is not None:
            out.add(sc)
    return frozenset(out)


def _snapshot_cells(cells: dict[Coord, dict[str, Any]], keys: frozenset[Coord]) -> dict[Coord, Any]:
    snap: dict[Coord, Any] = {}
    for k in keys:
        if k in cells:
            snap[k] = dict(cells[k])
        else:
            snap[k] = _MISSING
    return snap


def _restore_cells(cells: dict[Coord, dict[str, Any]], snap: dict[Coord, Any]) -> None:
    for k, v in snap.items():
        if v is _MISSING:
            cells.pop(k, None)
        else:
            cells[k] = dict(v)


def _copy_snap(snap: dict[Coord, Any]) -> dict[Coord, Any]:
    out: dict[Coord, Any] = {}
    for k, v in snap.items():
        out[k] = _MISSING if v is _MISSING else dict(v)
    return out


def _route_path_cost(
    path: tuple[Coord, ...],
    *,
    want_role: str,
    cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    cheap_reuse_cells: frozenset[Coord] | None,
) -> float:
    if len(path) < 2:
        return 0.0
    total = 0.0
    for _u, v in zip(path[:-1], path[1:], strict=True):
        step = step4_step_cost(
            v,
            want_role=want_role,
            cells=cells,
            mineable=mineable,
            asteroid=asteroid,
            is_external=is_external,
            cheap_reuse_cells=cheap_reuse_cells,
        )
        total += float(step) if step is not None else 0.0
    return total


def _new_internal_transport_count(
    path: tuple[Coord, ...],
    *,
    cells_before: dict[Coord, dict[str, Any]],
    want_role: str,
) -> int:
    n = 0
    for p in path[1:]:
        row = cells_before.get(p)
        if row is None or row.get("role") != want_role:
            n += 1
    return n


def _path_lex_key(path: tuple[Coord, ...]) -> tuple[tuple[int, int, int, int], ...]:
    return tuple((p[1], p[0], p[0], p[1]) for p in path)


def _same_kind_transport_cells(cells: dict[Coord, dict[str, Any]], want_role: str) -> set[Coord]:
    out: set[Coord] = set()
    for c, row in cells.items():
        if row.get("role") == want_role:
            out.add(c)
    return out


@dataclass(frozen=True)
class Pass2RouteRecoveryOutcome:
    path: tuple[Coord, ...]
    recovery_search_mode: str
    recovery_variant_eval_count: int
    new_rotation_r: int | None
    new_stub_cell: Coord
    recovery_last_error: str | None


def try_step4_failed_pass2_route_recovery(
    *,
    ext_cell: Coord,
    stub_cell: Coord,
    tk: str,
    rec: PlacementCommitRecord,
    cells: dict[Coord, dict[str, Any]],
    final_cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    committed_trunk_by_kind: dict[str, set[Coord]],
    margin_cells: set[Coord],
    trunk_seed_by_kind: dict[str, set[Coord]],
    cheap_reuse_cells: frozenset[Coord],
    hard_extras: frozenset[Coord],
    raw_goal_primary: set[Coord],
    dijkstra_fn: Any,
) -> tuple[Pass2RouteRecoveryOutcome | None, int]:
    """Return ``(outcome, variant_eval_count)``.

    ``cells`` are restored to baseline when ``outcome`` is ``None``.
    """

    if rec.placement_pass != "pass2" or rec.state != PlacementCommitState.PROVISIONAL_PLACED:
        return None, 0

    want_role = _want_role(tk)
    touch = _touch_coords_for_recovery(ext_cell, rec)
    baseline_snap = _snapshot_cells(cells, touch)
    eval_count = 0
    last_error: str | None = None

    ex_row0 = cells.get(ext_cell)
    if ex_row0 is None or not isinstance(ex_row0.get("r"), int):
        return None, 0
    current_r = int(ex_row0["r"])

    successes: list[
        tuple[
            tuple[int, float, int, tuple[tuple[int, int, int, int], ...]],
            tuple[Coord, ...],
            str,
            int | None,
            Coord,
            dict[Coord, Any],
        ]
    ] = []

    def _eval_once(
        *,
        mode: str,
        start_stub: Coord,
        goal_cells: frozenset[Coord],
        cheap: frozenset[Coord] | None,
        new_r: int | None,
        cells_snap: dict[Coord, Any],
    ) -> None:
        nonlocal eval_count, last_error
        if eval_count >= _MAX_RECOVERY_VARIANT_EVALS:
            return
        eval_count += 1
        _restore_cells(cells, cells_snap)
        blocked_set = set(_blocked_cells(cells)) | set(hard_extras)
        blocked_set.discard(start_stub)
        blocked = frozenset(blocked_set)
        transport_now = _same_kind_transport_cells(cells, want_role)
        trunk_cells = frozenset(
            transport_cells_reaching_external(transport_now, set(blocked), is_external)
        )
        search_stats: dict[str, Any] = {"search_mode": f"pass2_recovery:{mode}"}
        path_raw = dijkstra_fn(
            start_stub,
            want_role=want_role,
            cells=cells,
            blocked=blocked,
            mineable=mineable,
            asteroid=asteroid,
            is_external=is_external,
            trunk=trunk_cells,
            goal_cells=goal_cells,
            cheap_reuse_cells=cheap,
            search_stats=search_stats,
        )
        path: tuple[Coord, ...] | None = path_raw
        if path is None:
            last_error = str(search_stats.get("stop_reason") or "no_route")
            return
        cells_before = dict(cells)
        internal = _new_internal_transport_count(
            path, cells_before=cells_before, want_role=want_role
        )
        cost = _route_path_cost(
            path,
            want_role=want_role,
            cells=cells_before,
            mineable=mineable,
            asteroid=asteroid,
            is_external=is_external,
            cheap_reuse_cells=cheap,
        )
        plex = _path_lex_key(path)
        key = (internal, cost, len(path), plex)
        successes.append((key, path, mode, new_r, start_stub, _copy_snap(cells_snap)))

    # --- Variant A: output rotations (legal alternate ``r`` with matching stub tile).
    for cand_r in _rotation_probe_order(current_r):
        if cand_r == current_r:
            continue
        alt_stub = shape_miner_output_cell(ext_cell, cand_r)
        if alt_stub is None:
            continue
        st = cells.get(alt_stub)
        if st is None or st.get("role") != want_role:
            continue
        _restore_cells(cells, baseline_snap)
        old_stub = shape_miner_output_cell(ext_cell, current_r)
        ex_row = cells.get(ext_cell)
        if ex_row is None:
            continue
        ex_row = dict(ex_row)
        ex_row["r"] = cand_r
        cells[ext_cell] = ex_row
        if old_stub is not None and old_stub != alt_stub:
            if old_stub in mineable and old_stub in final_cells:
                cells[old_stub] = dict(final_cells[old_stub])
            elif old_stub in cells:
                del cells[old_stub]
        rot_snap = _snapshot_cells(cells, touch)
        blocked_set = set(_blocked_cells(cells)) | set(hard_extras)
        blocked_set.discard(alt_stub)
        blocked = frozenset(blocked_set)
        transport_now = _same_kind_transport_cells(cells, want_role)
        trunk_cells = frozenset(
            transport_cells_reaching_external(transport_now, set(blocked), is_external)
        )
        goal_cells_rot = frozenset(
            build_step4_goal_set(
                tk,
                committed_trunk_by_kind=committed_trunk_by_kind,
                exterior_margin_cells=margin_cells,
                trunk_seed_candidates_by_kind=trunk_seed_by_kind,
            )
            | set(trunk_cells)
        )
        _eval_once(
            mode="output_rotation",
            start_stub=alt_stub,
            goal_cells=goal_cells_rot,
            cheap=cheap_reuse_cells,
            new_r=cand_r,
            cells_snap=rot_snap,
        )

    # --- Variant B/C/D: same stub, STEP4 goal / reuse ablations (bounded).
    _restore_cells(cells, baseline_snap)
    base_snap = _snapshot_cells(cells, touch)

    blocked_set0 = set(_blocked_cells(cells)) | set(hard_extras)
    blocked_set0.discard(stub_cell)
    blocked0 = frozenset(blocked_set0)
    transport0 = _same_kind_transport_cells(cells, want_role)
    trunk0 = frozenset(transport_cells_reaching_external(transport0, set(blocked0), is_external))
    goal_union = frozenset(raw_goal_primary | set(trunk0))
    margin_only = frozenset(set(trunk0) | (margin_cells & goal_union))

    for mode, goal_cells, cheap in (
        ("cheap_reuse_off", goal_union, frozenset()),
        ("cheap_reuse_trunk_only", goal_union, frozenset(trunk0)),
        ("goal_margin_trunk_subset", margin_only, cheap_reuse_cells),
    ):
        _eval_once(
            mode=mode,
            start_stub=stub_cell,
            goal_cells=goal_cells,
            cheap=cheap,
            new_r=None,
            cells_snap=_copy_snap(base_snap),
        )

    if not successes:
        _restore_cells(cells, baseline_snap)
        return None, eval_count

    successes.sort(key=lambda row: row[0])
    _, win_path, win_mode, win_r, win_stub, win_snap = successes[0]
    _restore_cells(cells, win_snap)
    return (
        Pass2RouteRecoveryOutcome(
            path=win_path,
            recovery_search_mode=win_mode,
            recovery_variant_eval_count=eval_count,
            new_rotation_r=win_r,
            new_stub_cell=win_stub,
            recovery_last_error=last_error,
        ),
        eval_count,
    )


def apply_pass2_recovery_path_paint(
    *,
    path: tuple[Coord, ...],
    want_role: str,
    surface: str,
    cells: dict[Coord, dict[str, Any]],
    trunk_edge_hits: dict[str, int],
) -> None:
    """Paint non-stub transport cells (same rules as ``step4_merge_routing`` trunk edge hits)."""

    stub_cell = path[0]
    for p in path:
        if p == stub_cell:
            continue
        row = cells.get(p)
        if row is not None and row.get("role") == want_role:
            key = f"{p[0]},{p[1]}"
            trunk_edge_hits[key] = trunk_edge_hits.get(key, 0) + 1
            continue
        cells[p] = {"x": p[0], "y": p[1], "role": want_role, "surface": surface}
