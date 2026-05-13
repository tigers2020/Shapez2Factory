"""STEP4 merge routing internal DTOs (read-only context vs mutable runtime).

Public output remains :class:`Step4RoutingResult` in ``step4_contracts``; these types shrink
parameter bundles inside ``run_step4_merge_aware_routing`` and helpers.

Full routing-failure trace serialization lives in ``step4_route_failure_detail`` as
:class:`Step4RoutingFailure` (single ``to_step4_route_failure_detail_dict`` exit).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
    apply_placement_commit_state_transition,
    replace_provisional_placement_stub_cell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4Route,
)


def _default_p2c_metrics() -> dict[str, Any]:
    return {
        "route_revalidation_passed": True,
        "broken_routed_route_count": 0,
        "cascade_corrective_attempts": 0,
        "cascade_reroute_count": 0,
        "cascade_rollback_count": 0,
        "cascade_rolled_back_placement_ids": tuple(),
        "cascade_route_replay_detail": [],
    }


@dataclass(frozen=True, slots=True)
class Step4StubRouteJob:
    """One extractor output stub routing unit (placement optional)."""

    extractor_cell: Coord
    stub_cell: Coord
    transport_kind: str
    placement_id: str | None


@dataclass(frozen=True, slots=True)
class Step4GoalSet:
    """§08 raw goals + merge-aware Dijkstra union (fluid primary subset optional)."""

    raw_goal_cells: frozenset[Coord]
    merged_union_cells: frozenset[Coord]
    goal_ordering_mode: str
    merge_applied: bool
    priority_head: tuple[tuple[int, int], ...]
    fluid_primary_goal_cells: frozenset[Coord] | None

    @staticmethod
    def from_merge_round(
        *,
        raw_goal: set[Coord],
        merged_union_cells: frozenset[Coord],
        goal_order_meta: Mapping[str, Any],
        fluid_primary_goal_cells: frozenset[Coord] | None = None,
    ) -> Step4GoalSet:
        head_raw = goal_order_meta.get("priority_head") or ()
        norm_head: list[tuple[int, int]] = []
        for p in head_raw:
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                norm_head.append((int(p[0]), int(p[1])))
        return Step4GoalSet(
            raw_goal_cells=frozenset(raw_goal),
            merged_union_cells=merged_union_cells,
            goal_ordering_mode=str(goal_order_meta.get("mode") or "none"),
            merge_applied=bool(goal_order_meta.get("applied")),
            priority_head=tuple(norm_head),
            fluid_primary_goal_cells=fluid_primary_goal_cells,
        )


@dataclass(frozen=True, slots=True)
class Step4RouteAttemptResult:
    """One Dijkstra outcome + telemetry snapshot (immutable read-through mapping)."""

    path: tuple[Coord, ...] | None
    search_stats: Mapping[str, Any]

    @staticmethod
    def capture(path: tuple[Coord, ...] | None, stats: dict[str, Any]) -> Step4RouteAttemptResult:
        return Step4RouteAttemptResult(path, MappingProxyType(dict(stats)))


@dataclass(frozen=True, slots=True)
class Step4FailureClassification:
    """Structured STEP4 failure classification (parallel to nested trace dict)."""

    category: str
    confidence: str
    evidence: Mapping[str, Any]

    def to_classification_dict(self) -> dict[str, Any]:
        from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
            step4_failure_category as _s4fc,
        )

        return _s4fc.build_step4_failure_classification_dict(
            category=self.category,
            confidence=self.confidence,
            evidence=dict(self.evidence),
        )


@dataclass(frozen=True, slots=True)
class Step4RouteJob(Step4StubRouteJob):
    """Stub job plus stable sequencing and placement FSM snapshot at route attempt."""

    job_seq: int
    placement_commit_state_at_route_attempt: str | None = None

    def as_stub_job(self) -> Step4StubRouteJob:
        return Step4StubRouteJob(
            extractor_cell=self.extractor_cell,
            stub_cell=self.stub_cell,
            transport_kind=self.transport_kind,
            placement_id=self.placement_id,
        )


@dataclass(frozen=True, slots=True)
class Step4SearchSnapshot:
    """Per-attempt frozen view for failure detail / diagnostics."""

    want_role: str
    blocked: frozenset[Coord]
    trunk_cells: frozenset[Coord]
    goal_cells: frozenset[Coord]
    transport_now: frozenset[Coord]
    search_stats: dict[str, Any]
    goal_set: Step4GoalSet | None = None
    attempt: Step4RouteAttemptResult | None = None


@dataclass(frozen=True, slots=True)
class Step4RoutingContext:
    """STEP4 inputs that are not the live working cell map."""

    mineable: frozenset[Coord]
    asteroid: frozenset[Coord]
    is_external: Callable[[Coord], bool]
    final_cells: dict[Coord, dict[str, Any]]
    hard_extras: frozenset[Coord]
    existing_layout_analysis: dict[str, Any] | None
    surface: str
    margin_cells: frozenset[Coord]
    cheap_reuse_cells: frozenset[Coord]
    trunk_seed_by_kind: Mapping[str, frozenset[Coord]]
    force_route_attempt_placement_ids: frozenset[str] | None


@dataclass(slots=True)
class Step4TrunkLoadRuntime:
    """Trunk edge / maximized-cache state; cleared after P2-C before final edge load."""

    trunk_edge_hits: dict[str, int] = field(default_factory=dict)
    trunk_edge_load_by_kind: dict[str, dict[str, int]] = field(default_factory=dict)
    trunk_edge_load_maximized_by_kind: dict[str, dict[str, int]] = field(default_factory=dict)
    maximized_extractor_cache: dict[Coord, bool] = field(default_factory=dict)

    def reset_edge_load_after_p2c(self) -> None:
        self.trunk_edge_load_by_kind.clear()
        self.trunk_edge_load_maximized_by_kind.clear()
        self.maximized_extractor_cache.clear()


@dataclass(slots=True)
class Step4MutableState:
    """STEP4 working set: live cells, placement records, routing outcomes, telemetry."""

    cells: dict[Coord, dict[str, Any]]
    work_records: dict[str, PlacementCommitRecord]
    baseline_cells: dict[Coord, dict[str, Any]]
    baseline_wr: dict[str, PlacementCommitRecord]
    jobs: list[tuple[Coord, Coord, str, str | None]]
    initial_trunk: frozenset[Coord]
    # Mutable per-kind trunk seed copy (APIs expect set cells).
    trunk_seed_by_kind_sets: dict[str, set[Coord]] = field(default_factory=dict)
    trunk: Step4TrunkLoadRuntime = field(default_factory=Step4TrunkLoadRuntime)
    committed_trunk_by_kind: dict[str, set[Coord]] = field(default_factory=dict)
    final_route_cells: set[Coord] = field(default_factory=set)
    route_visits_by_kind: dict[str, int] = field(default_factory=dict)
    unique_cells_by_kind: dict[str, set[Coord]] = field(default_factory=dict)
    routes_by_placement_id: dict[str, list[list[int]]] = field(default_factory=dict)
    goal_set_sizes: list[int] = field(default_factory=list)
    accumulated_route_cell_visits: int = 0
    routes_out: list[Step4Route] = field(default_factory=list)
    failures: list[dict[str, Any]] = field(default_factory=list)
    p2c_metrics: dict[str, Any] = field(default_factory=_default_p2c_metrics)
    rolled_back: list[str] = field(default_factory=list)
    quarantined: list[str] = field(default_factory=list)
    quarantined_placement_ids_peak: tuple[str, ...] = ()

    def transition_placement(
        self,
        placement_id: str,
        *,
        to: PlacementCommitState,
        route_id: str | None = None,
        rollback_reason: str | None = None,
        clear_route_id: bool = False,
        context: str = "",
    ) -> None:
        self.work_records[placement_id] = apply_placement_commit_state_transition(
            self.work_records[placement_id],
            to=to,
            route_id=route_id,
            rollback_reason=rollback_reason,
            clear_route_id=clear_route_id,
            context=context,
        )

    def mark_routed_confirmed(
        self,
        placement_id: str,
        *,
        route_id: str,
        context: str,
    ) -> None:
        self.transition_placement(
            placement_id,
            to=PlacementCommitState.ROUTED_CONFIRMED,
            route_id=route_id,
            context=context,
        )

    def mark_quarantined_unrouted(
        self,
        placement_id: str,
        *,
        rollback_reason: str | None,
        context: str,
    ) -> None:
        self.transition_placement(
            placement_id,
            to=PlacementCommitState.QUARANTINED_UNROUTED,
            rollback_reason=rollback_reason,
            context=context,
        )

    def replace_provisional_stub(self, placement_id: str, *, stub_cell: Coord) -> None:
        self.work_records[placement_id] = replace_provisional_placement_stub_cell(
            self.work_records[placement_id],
            stub_cell=stub_cell,
        )

    def note_route_path_committed(self, tk: str, path: tuple[Coord, ...]) -> None:
        self.committed_trunk_by_kind.setdefault(tk, set()).update(path)
        self.final_route_cells.update(path)
        self.accumulated_route_cell_visits += len(path)
        self.route_visits_by_kind[tk] = self.route_visits_by_kind.get(tk, 0) + len(path)
        self.unique_cells_by_kind.setdefault(tk, set()).update(path)

    def note_stub_in_trunk_merge(self, tk: str, stub_cell: Coord, placement_id: str) -> None:
        self.committed_trunk_by_kind.setdefault(tk, set()).add(stub_cell)
        self.final_route_cells.add(stub_cell)
        self.routes_by_placement_id[placement_id] = [list(stub_cell)]
        self.accumulated_route_cell_visits += 1
        self.route_visits_by_kind[tk] = self.route_visits_by_kind.get(tk, 0) + 1
        self.unique_cells_by_kind.setdefault(tk, set()).add(stub_cell)


__all__ = [
    "Step4FailureClassification",
    "Step4GoalSet",
    "Step4MutableState",
    "Step4RouteAttemptResult",
    "Step4RouteJob",
    "Step4RoutingContext",
    "Step4SearchSnapshot",
    "Step4StubRouteJob",
    "Step4TrunkLoadRuntime",
]
