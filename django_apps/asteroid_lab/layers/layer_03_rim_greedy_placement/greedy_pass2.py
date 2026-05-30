"""Pass 2 — read-only validation and variant score (v0)."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import RouteProbeStatus
from django_apps.asteroid_lab.layers.contracts.rim_greedy import (
    RimGreedyObservationEvent,
    RimGreedyObservationPhase,
    RimGreedyPass2Report,
    RimGreedyPolicy,
)
from django_apps.asteroid_lab.layers.contracts.route_goal import RouteGoal
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.greedy_pass1 import (
    RimGreedyState,
    probe_seed_route,
)
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.greedy_seed import (
    GreedyMinerSeed,
)
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.seed_orient import (
    SeedLayout,
    layout_seed_at_anchor,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap

_ROUTE_LENGTH_PENALTY = 0.05


def _hard_fail(state: RimGreedyState, *, complete_map: ReconstructionCompleteMap) -> bool:
    field = complete_map.field_cells
    if len(state.occupied_equipment_cells) != sum(
        len(p.miner_cells) + len(p.extension_cells) for p in state.committed_placements
    ):
        return True
    for placement in state.committed_placements:
        if not placement.miner_cells <= field:
            return True
        if not placement.extension_cells <= field:
            return True
        if placement.m_output_stub in field:
            return True
        if placement.m_output_stub not in complete_map.external_void_cells:
            return True
    return False


def score_variant(
    state: RimGreedyState,
    *,
    complete_map: ReconstructionCompleteMap,
    route_goals: tuple[RouteGoal, ...],
    policy: RimGreedyPolicy,
    transport_kind: TransportKind,
    seeds_by_id: dict[str, GreedyMinerSeed],
) -> RimGreedyPass2Report:
    if _hard_fail(state, complete_map=complete_map):
        return RimGreedyPass2Report(
            variant_id=state.variant_id,
            score=None,
            hard_fail=True,
            miner_count=0,
            extension_count=0,
            total_route_length=0,
        )

    occupied_all = frozenset(state.occupied_equipment_cells)
    for placement in state.committed_placements:
        seed = seeds_by_id.get(placement.seed_id)
        if seed is None:
            return RimGreedyPass2Report(
                variant_id=state.variant_id,
                score=None,
                hard_fail=True,
                miner_count=0,
                extension_count=0,
                total_route_length=0,
            )
        layout = layout_seed_at_anchor(
            seed_id=placement.seed_id,
            anchor=placement.anchor,
            output_dir=placement.output_dir,
            complete_map=complete_map,
        )
        if not isinstance(layout, SeedLayout):
            return RimGreedyPass2Report(
                variant_id=state.variant_id,
                score=None,
                hard_fail=True,
                miner_count=0,
                extension_count=0,
                total_route_length=0,
            )
        others = occupied_all - layout.equipment_cells
        probed = probe_seed_route(
            layout,
            seed,
            route_goals=route_goals,
            complete_map=complete_map,
            search_bbox_margin=policy.dps_search_margin,
            occupied_equipment=others,
            transport_kind=transport_kind,
        )
        if probed.route_probe_status is not RouteProbeStatus.SUCCEEDED:
            return RimGreedyPass2Report(
                variant_id=state.variant_id,
                score=None,
                hard_fail=True,
                miner_count=0,
                extension_count=0,
                total_route_length=0,
            )

    miner_count = sum(len(p.miner_cells) for p in state.committed_placements)
    extension_count = sum(len(p.extension_cells) for p in state.committed_placements)
    route_len = sum(len(p.route_probe_path) for p in state.committed_placements)
    score = 2 * miner_count + extension_count - _ROUTE_LENGTH_PENALTY * route_len

    state.observability_events.append(
        RimGreedyObservationEvent(
            phase=RimGreedyObservationPhase.RIM_PASS2_VALIDATION,
            variant_id=state.variant_id,
            payload={"score": score, "hard_fail": False},
        )
    )
    return RimGreedyPass2Report(
        variant_id=state.variant_id,
        score=score,
        hard_fail=False,
        miner_count=miner_count,
        extension_count=extension_count,
        total_route_length=route_len,
    )


__all__ = ["score_variant"]
