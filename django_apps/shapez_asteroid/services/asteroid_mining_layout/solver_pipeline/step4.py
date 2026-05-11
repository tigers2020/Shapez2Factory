"""STEP4 merge-aware routing pipeline stage extraction."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    ROUTING_STATE_KEYS_STEP4_HASH,
    SOLVER_FRAME_STEP4_ROUTING,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
    solver_mutation_transaction as solver_mut_txn,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_corridors import (  # noqa: E501
    protected_corridors_overlay_from_routing_state,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_events import (  # noqa: E501
    SolverMutationEventKind,
    corridor_added_replay_payload,
    new_replay_transaction_id,
    normalize_replay_transport_kind,
    replay_transaction_payload,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_state_hash import (
    solver_state_sha256_hex,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_timeline import (
    count_layout_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    debug_log_event,
    debug_trace_event,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4RoutingResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_merge_routing import (
    run_step4_merge_aware_routing,
    step4_routing_skipped_result,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    FinalValidationReport,
)


@dataclass(frozen=True)
class Step4StageResult:
    """STEP4 실행 결과와 downstream summary 입력."""

    step4_result: Step4RoutingResult
    map_after_routing: list[dict[str, Any]]
    post_step4_counts: dict[str, int]
    routing_state_summary: dict[str, Any] | None
    step_hash_step4: str
    step4_replay_transaction_id: str | None
    unfinalized_placement_count: int
    report_step4: FinalValidationReport


def _route_replaced_payload_geo(detail: list[Any]) -> dict[str, Any]:
    """Union cell diff across P2-C replacement rows for replay v5 ``route_replaced``."""

    rem: set[tuple[int, int]] = set()
    add: set[tuple[int, int]] = set()
    tk0: str | None = None
    rr0: str | None = None
    for row in detail:
        if not isinstance(row, dict):
            continue
        for pair in row.get("cells_removed") or []:
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                x, y = int(pair[0]), int(pair[1])
                if x != 0:
                    rem.add((x, y))
        for pair in row.get("cells_added") or []:
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                x, y = int(pair[0]), int(pair[1])
                if x != 0:
                    add.add((x, y))
        if tk0 is None:
            tkv = row.get("transport_kind")
            if isinstance(tkv, str):
                tk0 = normalize_replay_transport_kind(tkv)
        if rr0 is None:
            rrv = row.get("replacement_reason") or row.get("reason")
            if isinstance(rrv, str) and rrv:
                rr0 = rrv
    out: dict[str, Any] = {
        "cells_removed": [[a, b] for a, b in sorted(rem)],
        "cells_added": [[a, b] for a, b in sorted(add)],
        "cells_kept": None,
    }
    if tk0:
        out["transport_kind"] = tk0
    if rr0 is not None:
        out["replacement_reason"] = rr0
    return out


def _validate_final_mining_layout(mining_map: list[dict[str, Any]]) -> FinalValidationReport:
    """기존 ``solver_service`` validation patch 지점을 유지한다."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
        solver_service,
    )

    return solver_service.validate_final_mining_layout(mining_map)


def run_step4_stage(
    *,
    map_after_pass2: list[dict[str, Any]],
    final_map: list[dict[str, Any]],
    is_external: Callable[[Coord], bool],
    placement_records: dict[str, Any] | None,
    pass12_skipped: bool,
    pass12_replay_txn_id: str | None,
    replay_events: list[dict[str, Any]],
    debug_location: str,
    existing_layout_analysis: dict[str, Any] | None = None,
) -> Step4StageResult:
    """STEP4 route transaction을 실행하고 replay transaction 계약을 유지한다."""

    step4_replay_transaction_id: str | None = None
    if pass12_skipped:
        step4_result = step4_routing_skipped_result(map_after_pass2)
    else:
        step4_txn = solver_mut_txn.SolverMutationTransaction(map_after_pass2)
        step4_txn.begin()
        s4_txn_id = new_replay_transaction_id()
        step4_replay_transaction_id = s4_txn_id
        s4_map_before = solver_mut_txn.copy_mining_map_rows(step4_txn.working_map)
        replay_events.append(
            {
                "kind": SolverMutationEventKind.TRANSACTION_BEGIN.value,
                "phase": "step4",
                "payload": replay_transaction_payload(
                    transaction_id=s4_txn_id,
                    parent_txn_id=pass12_replay_txn_id,
                ),
            }
        )
        try:
            step4_result = run_step4_merge_aware_routing(
                step4_txn.working_map,
                final_mining_map=final_map,
                is_external=is_external,
                placement_records=placement_records,
                mutate_input_map=True,
                existing_layout_analysis=existing_layout_analysis,
            )
        except BaseException:
            replay_events.append(
                {
                    "kind": SolverMutationEventKind.ROLLBACK.value,
                    "phase": "step4",
                    "payload": replay_transaction_payload(
                        transaction_id=s4_txn_id,
                        parent_txn_id=pass12_replay_txn_id,
                    ),
                }
            )
            step4_txn.rollback()
            raise
        else:
            step4_txn.commit()
            diff_payload = solver_mut_txn.diff_mining_maps(
                s4_map_before,
                step4_result.map_after_routing,
            )
            diff_payload.update(
                replay_transaction_payload(
                    transaction_id=s4_txn_id,
                    parent_txn_id=pass12_replay_txn_id,
                )
            )
            replay_events.append(
                {
                    "kind": SolverMutationEventKind.MAP_DIFF_COMMITTED.value,
                    "phase": "step4",
                    "payload": diff_payload,
                }
            )
            cascade_reroute_count = int(
                step4_result.trunk_load.get("cascade_reroute_count", 0) or 0
            )
            if cascade_reroute_count:
                rr_payload: dict[str, Any] = {
                    "cascade_reroute_count": cascade_reroute_count,
                    **replay_transaction_payload(
                        transaction_id=s4_txn_id,
                        parent_txn_id=pass12_replay_txn_id,
                    ),
                }
                rr_detail = step4_result.trunk_load.get("cascade_route_replay_detail")
                if isinstance(rr_detail, list):
                    rr_payload["replacements"] = rr_detail
                    if rr_detail:
                        rr_payload.update(_route_replaced_payload_geo(rr_detail))
                replay_events.append(
                    {
                        "kind": SolverMutationEventKind.ROUTE_REPLACED.value,
                        "phase": "step4",
                        "payload": rr_payload,
                    }
                )
            rs_step4 = getattr(step4_result, "routing_state", None)
            pc_overlay = protected_corridors_overlay_from_routing_state(
                rs_step4 if isinstance(rs_step4, dict) else None
            )
            for tier in ("hard", "soft", "candidate"):
                cap = corridor_added_replay_payload(
                    transaction_id=s4_txn_id,
                    parent_txn_id=pass12_replay_txn_id,
                    tier=tier,
                    cells_raw=pc_overlay.get(tier),
                )
                if cap is not None:
                    replay_events.append(
                        {
                            "kind": SolverMutationEventKind.CORRIDOR_ADDED.value,
                            "phase": "step4",
                            "payload": cap,
                        }
                    )

    map_after_routing = step4_result.map_after_routing
    post_step4_counts = count_layout_cells(map_after_routing)
    routing_state = getattr(step4_result, "routing_state", None)
    routing_state_summary = dict(routing_state) if isinstance(routing_state, dict) else None
    step_hash_step4 = solver_state_sha256_hex(
        map_after_routing,
        routing_state=routing_state_summary,
        routing_state_keys=ROUTING_STATE_KEYS_STEP4_HASH,
    )
    debug_log_event(
        debug_location,
        "step4_completed",
        {
            "committed": step4_result.committed,
            "skipped": bool(pass12_skipped),
            "route_count": step4_result.trunk_load.get("step4_route_count", 0),
            "routing_failure_count": step4_result.trunk_load.get("step4_routing_failure_count", 0),
            "rolled_back_placement_ids": list(step4_result.rolled_back_placement_ids),
            "quarantined_placement_ids": list(step4_result.quarantined_placement_ids),
            "after_routing_counts": post_step4_counts,
            "step_hash_step4": step_hash_step4,
        },
    )
    debug_trace_event(
        debug_location,
        "phase_checkpoint",
        {"phase": "step4", "step_hash_step4": step_hash_step4},
        frame_id=SOLVER_FRAME_STEP4_ROUTING,
    )
    unfinalized_placement_count = int(
        step4_result.trunk_load.get("unfinalized_placement_count", 0) or 0
    )
    return Step4StageResult(
        step4_result=step4_result,
        map_after_routing=map_after_routing,
        post_step4_counts=post_step4_counts,
        routing_state_summary=routing_state_summary,
        step_hash_step4=step_hash_step4,
        step4_replay_transaction_id=step4_replay_transaction_id,
        unfinalized_placement_count=unfinalized_placement_count,
        report_step4=_validate_final_mining_layout(map_after_routing),
    )
