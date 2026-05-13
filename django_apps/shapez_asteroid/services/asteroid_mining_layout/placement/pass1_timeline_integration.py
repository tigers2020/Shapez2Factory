"""Pass1/Pass2 placement wiring for ``build_solver_timeline`` (no API surface).

Mutates layout through ``run_pass1_outer_placement_mvp`` / ``run_pass2_internal_placement_mvp``
and bundle commits only. Does not import ``solver_service`` (avoids import cycles with
``pass12_bundle_commit``).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django.conf import settings

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import (
    rotation_r_for_output_direction,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.existing_layout.pass12_existing_layout_hints import (  # noqa: E501
    pass12_existing_layout_barrier_meta,
    pass12_transport_related_block_extra_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.extension_topology import (  # noqa: E501
    rotation_r_for_extension_facing_parent,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass1_outer_placement import (  # noqa: E501
    run_pass1_outer_placement_mvp,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass2_internal_placement import (  # noqa: E501
    run_pass2_internal_placement_mvp,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass2_spine import (
    spine_seed_voids_adjacent_extensions,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_bundle_commit import (  # noqa: E501
    Pass2RouteProbePack,
    Pass12LayoutScratch,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_merged_layout_seed import (  # noqa: E501
    seed_pass12_scratch_from_merged_existing,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_route_probe import (  # noqa: E501
    finalize_pass2_route_probe_stats,
    new_pass2_route_probe_stats_sink,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    layout_kind,
    mineable_and_asteroid_coords,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_mutation_transaction import (  # noqa: E501
    copy_mining_map_rows,
    diff_mining_maps,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_events import (  # noqa: E501
    SolverMutationEventKind,
    new_replay_transaction_id,
    replay_transaction_payload,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import (
    merge_with_transport_and_final_mining_map,
)


def _clone_scratch(scratch: Pass12LayoutScratch) -> Pass12LayoutScratch:
    """Copy scratch state for a Pass1-only merged-map snapshot before Pass2 runs."""

    return Pass12LayoutScratch(
        transport_cells=set(scratch.transport_cells),
        blocked_cells=set(scratch.blocked_cells),
        extractor_cells=set(scratch.extractor_cells),
        extension_facings=dict(scratch.extension_facings),
        extractor_output_dirs=dict(scratch.extractor_output_dirs),
        transport_kind=scratch.transport_kind,
        next_placement_seq=scratch.next_placement_seq,
        placement_records=dict(scratch.placement_records),
        preserved_mining_row_overrides=dict(scratch.preserved_mining_row_overrides),
    )


_BUILDING_LAYOUT_KINDS = frozenset(
    {"miner", "fluid_miner", "extractor", "extension", "fluid_extension"}
)


def _transport_cell_coords_from_map_rows(rows: list[dict[str, Any]]) -> frozenset[Coord]:
    """Belt/pipe coords (last row wins per cell, ``x==0`` excluded)."""

    cells = cells_dict_from_mining_map(rows)
    return frozenset(c for c, r in cells.items() if r.get("role") in ("belt", "pipe"))


def is_mixed_surface_mining_map(mining_map: list[dict[str, Any]]) -> bool:
    """True when both surfaces appear; one global dominant miner/transport kind would be wrong."""

    fluids = shapes = 0
    for row in mining_map:
        if row.get("surface") == "fluid":
            fluids += 1
        elif row.get("surface") == "shape":
            shapes += 1
    return fluids > 0 and shapes > 0


def dominant_surface_from_map(mining_map: list[dict[str, Any]]) -> str:
    """Prefer fluid when fluid dominates; invalid on mixed maps (guard skips Pass12 first)."""

    fluids = 0
    shapes = 0
    for row in mining_map:
        if row.get("surface") == "fluid":
            fluids += 1
        elif row.get("surface") == "shape":
            shapes += 1
    return "fluid" if fluids > shapes else "shape"


def scratch_from_working_map(
    working_map: list[dict[str, Any]],
    *,
    mineable_coords: frozenset[Coord],
) -> tuple[Pass12LayoutScratch, frozenset[Coord], frozenset[Coord]]:
    """Belts/pipes from ``with_transport``; bodies only where not a reconstructed mineable slot.

    Blueprint miners on cells that ``final_mining_map`` exposes as ``asteroid_field`` were
    stripped for reconstruction and must not stay in ``blocked_cells`` for Pass1-A.
    """

    transport: set[Coord] = set()
    blocked: set[Coord] = set()
    for row in working_map:
        x, y = row.get("x"), row.get("y")
        if not isinstance(x, int) or not isinstance(y, int) or x == 0:
            continue
        role = row.get("role")
        lk = layout_kind(row)
        c = (x, y)
        if role in ("belt", "pipe"):
            transport.add(c)
        elif role == "occupied" and lk in _BUILDING_LAYOUT_KINDS:
            if c not in mineable_coords:
                blocked.add(c)
    scratch = Pass12LayoutScratch(transport_cells=transport, blocked_cells=blocked)
    return scratch, frozenset(transport), frozenset(blocked)


def _merge_pass1_into_rows(
    working_map: list[dict[str, Any]],
    final_mining_map: list[dict[str, Any]],
    scratch: Pass12LayoutScratch,
    transport_init: frozenset[Coord],
    blocked_init: frozenset[Coord],
    mineable: frozenset[Coord],
    surface: str,
) -> list[dict[str, Any]]:
    """Rebuild cells: ``with_transport`` plus reconstructed mineable shell, then P1 overlays."""

    _ = transport_init  # Baseline transport coords (symmetry with callers); full scratch stamp.
    cells = {k: dict(v) for k, v in cells_dict_from_mining_map(working_map).items()}
    final_cells = cells_dict_from_mining_map(final_mining_map)
    for c in mineable:
        if c in final_cells:
            cells[c] = dict(final_cells[c])
    new_bodies = scratch.blocked_cells - set(blocked_init)
    # Stamp every scratch transport cell after the mineable shell overlay. Using only
    # ``scratch.transport_cells - transport_init`` drops baseline stub belts/pipes that the
    # shell overwrote with ``inferred`` (Pass12 preserve stub-route recovery may omit the stub
    # from ``new_transport_coords`` when it was already same-kind on the merged probe map).
    if surface == "fluid":
        miner_layout = "fluid_miner"
        miner_t = "Layout_FluidMiner"
        transport_role = "pipe"
        ext_layout = "fluid_extension"
        ext_t = "Layout_FluidMinerExtension"
    else:
        miner_layout = "miner"
        miner_t = "Layout_ShapeMiner"
        transport_role = "belt"
        ext_layout = "extension"
        ext_t = "Layout_ShapeMinerExtension"
    miner_row: dict[str, Any] = {
        "role": "occupied",
        "surface": surface,
        "layout_kind": miner_layout,
        "t": miner_t,
    }
    pid_by_cell: dict[Coord, str] = {}
    for rec in scratch.placement_records.values():
        pid_by_cell[rec.extractor_cell] = rec.placement_id
        pid_by_cell[rec.stub_cell] = rec.placement_id
        for ec in rec.extension_cells:
            pid_by_cell[ec] = rec.placement_id
    for x, y in new_bodies:
        c = (x, y)
        if c in scratch.preserved_mining_row_overrides:
            ov_row = dict(scratch.preserved_mining_row_overrides[c])
            if c in scratch.extension_facings:
                edx, edy = scratch.extension_facings[c]
                ov_row["r"] = rotation_r_for_extension_facing_parent((edx, edy))
            cells[c] = ov_row
            continue
        if c in scratch.extractor_cells:
            row = dict(miner_row)
            row.update({"x": x, "y": y})
            out_dir = scratch.extractor_output_dirs.get(c)
            if out_dir is not None:
                row["r"] = rotation_r_for_output_direction(out_dir[0], out_dir[1])
            if c in pid_by_cell:
                row["placement_id"] = pid_by_cell[c]
            cells[c] = row
        elif c in scratch.extension_facings:
            edx, edy = scratch.extension_facings[c]
            r = rotation_r_for_extension_facing_parent((edx, edy))
            ext_row: dict[str, Any] = {
                "x": x,
                "y": y,
                "role": "occupied",
                "surface": surface,
                "layout_kind": ext_layout,
                "t": ext_t,
                "r": r,
            }
            if c in pid_by_cell:
                ext_row["placement_id"] = pid_by_cell[c]
            cells[c] = ext_row
        else:
            row = dict(miner_row)
            row.update({"x": x, "y": y})
            cells[c] = row
    for x, y in sorted(scratch.transport_cells, key=lambda p: (p[1], p[0])):
        if (x, y) in scratch.blocked_cells:
            continue
        tr: dict[str, Any] = {
            "x": x,
            "y": y,
            "role": transport_role,
            "surface": surface,
        }
        if (x, y) in pid_by_cell:
            tr["placement_id"] = pid_by_cell[(x, y)]
        cells[(x, y)] = tr
    ordered = sorted(cells.keys(), key=lambda p: (p[1], p[0]))
    return [dict(cells[k]) for k in ordered]


def integrate_pass12_placement_into_working_map(
    *,
    working_map: list[dict[str, Any]],
    final_mining_map: list[dict[str, Any]],
    is_external: Callable[[Coord], bool],
    existing_layout_analysis: dict[str, Any] | None = None,
    replay_events: list[dict[str, Any]] | None = None,
    pass2_spine_priority_enabled: bool = False,
    suppress_pass1_pass2_loops: bool = False,
    suppress_pass1_loop: bool | None = None,
    suppress_pass2_loop: bool | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Run Pass1 outer then Pass2 internal placement; merge each stage into row lists.

    Returns ``(mining_map_after_pass1, mining_map_after_pass2, stats)``.

    When ``existing_layout_analysis`` is set (STEP 0.5), ``solver_hints`` trunk/cleanup
    coordinates that intersect ``mineable`` become Pass2 ``hard_barrier_cells`` so inner fill
    does not occupy those cells; summary stats record hint/barrier counts.

    ``pass2_spine_priority_enabled``가 True면 Pass1 직후 계산한 spine 시드를 Pass2
    ``mineable_inner_first_order``의 soft 우선순위로 흘려 인접 셀을 그룹 선두로 끌어온다
    (정본: 07_step3_pass2_placement.md §8.5). 기본값은 False (기존 동작 동일).

    ``suppress_pass1_pass2_loops``: True면 시드 이후 Pass1/Pass2 배치 루프를 모두 건너뛴다
    (기존 연결 레이아웃 preserve-first 동작과 호환). 더 세밀한 분기는 ``suppress_pass1_loop`` /
    ``suppress_pass2_loop``로 패스를 따로 끈다(설정되지 않으면 ``suppress_pass1_pass2_loops``
    값을 그대로 사용). ``pass12_skipped``(혼합 면)와 달리 STEP4는 계속 실행된다.
    """

    sp1 = suppress_pass1_loop if suppress_pass1_loop is not None else suppress_pass1_pass2_loops
    sp2 = suppress_pass2_loop if suppress_pass2_loop is not None else suppress_pass1_pass2_loops

    mineable, asteroid = mineable_and_asteroid_coords(final_mining_map)
    _, ela_empty_meta = pass12_existing_layout_barrier_meta(
        existing_layout_analysis, mineable=mineable
    )
    empty_stats: dict[str, Any] = {
        "pass1_outer_placements": 0,
        "pass1_new_extractor_cells": 0,
        "pass1_new_extension_cells": 0,
        "pass1_preserved_transport_cells": 0,
        "pass1_new_transport_cells": 0,
        "pass1_total_transport_cells_after": 0,
        "pass2_internal_placements": 0,
        "pass2_new_extractor_cells": 0,
        "pass2_new_extension_cells": 0,
        "pass2_new_transport_cells": 0,
        "pass2_spine_seed_count": 0,
        "pass2_spine_priority_applied": False,
        "pass12_skipped": False,
        "pass12_skip_reason": None,
        "pass12_mixed_surface_skipped": False,
        "placement_records": {},
        "placement_candidate_blocked_count": 0,
        "pass12_preserved_equipment_groups": 0,
        "pass12_preserved_routed_placement_records": 0,
        "pass12_preserved_missing_stub_drop_details": [],
        "pass12_merged_seed_miner_count": 0,
        "pass12_preserve_drop_reason_counts": {},
        "pass12_preserved_recovery_traces": [],
        "pass12_preserved_recovery_success_count": 0,
        "pass12_placement_loops_suppressed": False,
        "pass12_pass1_loop_suppressed": False,
        "pass12_pass2_loop_suppressed": False,
        "pass12_preserved_bundle_extension_count_histogram": {},
        "pass12_preserved_extension_per_extractor_avg": 0.0,
        "pass12_preserved_orphan_extension_count": 0,
        "pass12_preserved_missing_stub_route_recovery_attempted_count": 0,
        "pass12_preserved_missing_stub_route_recovery_success_count": 0,
        "pass12_preserved_missing_stub_route_recovery_rejected_by_nearest_hops_count": 0,
        "pass12_preserved_missing_stub_route_recovery_rejected_by_no_stub_space_count": 0,
        "pass12_preserved_missing_stub_route_recovery_rejected_by_no_same_kind_route_count": 0,
        "pass12_preserved_missing_stub_route_recovery_rejected_by_route_len_count": 0,
        "pass12_preserved_missing_stub_route_recovery_rejected_by_new_transport_cells_count": 0,
        (
            "pass12_preserved_missing_stub_route_recovery_rejected_by_extension_carve_"
            "disabled_count"
        ): 0,
        "pass12_preserved_rotation_recovery_count": 0,
        "pass12_preserved_missing_stub_route_recovery_queue_rounds": 0,
        "pass12_preserved_recovered_stub_samples": [],
        "pass12_preserved_unrecovered_stub_drop_samples": [],
        "pass12_stub_route_recovery_enabled": False,
        "pass12_stub_route_recovery_disabled_by_flag": True,
        "pass12_stub_route_recovery_eligible_count": 0,
        "pass12_stub_route_recovery_queue_rounds": 0,
        "pass12_stub_route_recovery_attempted_count": 0,
        **new_pass2_route_probe_stats_sink(),
        **ela_empty_meta,
    }
    if not mineable:
        unchanged = [dict(r) for r in working_map]
        return unchanged, unchanged, empty_stats

    if is_mixed_surface_mining_map(final_mining_map):
        unchanged = [dict(r) for r in working_map]
        skip_stats: dict[str, Any] = {
            **empty_stats,
            "pass12_skipped": True,
            "pass12_skip_reason": "mixed_surface",
            # Backward-compatible flag name (same meaning as pass12_skipped here).
            "pass12_mixed_surface_skipped": True,
            "placement_records": {},
            "placement_candidate_blocked_count": 0,
            "pass12_preserved_equipment_groups": 0,
            "pass12_preserved_routed_placement_records": 0,
            "pass12_preserved_missing_stub_drop_details": [],
            "pass12_merged_seed_miner_count": 0,
            "pass12_preserve_drop_reason_counts": {},
            "pass12_preserved_recovery_traces": [],
            "pass12_preserved_recovery_success_count": 0,
            "pass12_preserved_missing_stub_route_recovery_attempted_count": 0,
            "pass12_preserved_missing_stub_route_recovery_success_count": 0,
            "pass12_preserved_missing_stub_route_recovery_rejected_by_nearest_hops_count": 0,
            "pass12_preserved_missing_stub_route_recovery_rejected_by_no_stub_space_count": 0,
            "pass12_preserved_missing_stub_route_recovery_rejected_by_no_same_kind_route_count": 0,
            "pass12_preserved_missing_stub_route_recovery_rejected_by_route_len_count": 0,
            "pass12_preserved_missing_stub_route_recovery_rejected_by_new_transport_cells_count": 0,
            (
                "pass12_preserved_missing_stub_route_recovery_rejected_by_extension_carve_"
                "disabled_count"
            ): 0,
            "pass12_preserved_rotation_recovery_count": 0,
            "pass12_preserved_missing_stub_route_recovery_queue_rounds": 0,
            "pass12_preserved_recovered_stub_samples": [],
            "pass12_preserved_unrecovered_stub_drop_samples": [],
            "pass12_placement_loops_suppressed": False,
        }
        return unchanged, unchanged, skip_stats

    pass2_barriers, ela_meta = pass12_existing_layout_barrier_meta(
        existing_layout_analysis, mineable=mineable
    )
    pass2_hard_barriers: frozenset[Coord] | None = pass2_barriers if pass2_barriers else None

    scratch, transport_init, blocked_init = scratch_from_working_map(
        working_map, mineable_coords=mineable
    )
    surface = dominant_surface_from_map(final_mining_map)
    scratch.transport_kind = "fluid_pipe" if surface == "fluid" else "shape_belt"
    merged_for_seed = merge_with_transport_and_final_mining_map(working_map, final_mining_map)
    existing_transport_baseline = _transport_cell_coords_from_map_rows(merged_for_seed)
    ela_sk = ela_meta.get("existing_layout_source_kind")
    preserve_seed_stats = seed_pass12_scratch_from_merged_existing(
        merged_for_seed,
        mineable=mineable,
        scratch=scratch,
        existing_layout_source_kind=ela_sk if isinstance(ela_sk, str) else None,
    )
    extractors_after_seed = len(scratch.extractor_cells)
    extensions_after_seed = len(scratch.extension_facings)
    extra_transport_blocks = pass12_transport_related_block_extra_cells(existing_layout_analysis)
    placement_transport_blocked_counter: list[int] = [0]

    pass12_txn_id: str | None = None
    map_before_pass12: list[dict[str, Any]] | None = None
    if replay_events is not None:
        pass12_txn_id = new_replay_transaction_id()
        map_before_pass12 = copy_mining_map_rows(working_map)
        replay_events.append(
            {
                "kind": SolverMutationEventKind.TRANSACTION_BEGIN.value,
                "phase": "pass12",
                "payload": replay_transaction_payload(transaction_id=pass12_txn_id),
            }
        )
    try:
        priority_seeds_arg: frozenset[Coord] | None = None
        spine_seeds: frozenset[Coord] = frozenset()
        if sp1:
            placed = 0
        else:
            placed = run_pass1_outer_placement_mvp(
                mineable_cells=mineable,
                asteroid_cells=asteroid,
                scratch=scratch,
                is_external=is_external,
                existing_layout_analysis=existing_layout_analysis,
                replay_events=replay_events,
                extra_transport_block_cells=extra_transport_blocks,
                placement_transport_blocked_counter=placement_transport_blocked_counter,
            )
        scratch_after_pass1 = _clone_scratch(scratch)
        merged_rows_pass1_for_probe = _merge_pass1_into_rows(
            working_map,
            final_mining_map,
            scratch_after_pass1,
            transport_init,
            blocked_init,
            mineable,
            surface,
        )
        cells_for_pass2_probe = {
            k: dict(v) for k, v in cells_dict_from_mining_map(merged_rows_pass1_for_probe).items()
        }
        pass2_probe_stats = new_pass2_route_probe_stats_sink()
        pass2_route_probe_pack = Pass2RouteProbePack(
            mineable=mineable,
            asteroid=asteroid,
            cells=cells_for_pass2_probe,
            existing_layout_analysis=existing_layout_analysis,
            stats_sink=pass2_probe_stats,
        )
        ex_before_p2 = len(scratch.extractor_cells)
        ext_before_p2 = len(scratch.extension_facings)
        tr_before_p2 = len(scratch.transport_cells)
        if sp2:
            placed_p2 = 0
        else:
            # Pass2 spine seeds: extension-인접 void cells (Pass2 진입 직전 관측). 동작 변경 없음;
            # 후속 단계에서 우선순위/힌트로 활용 가능. 정본: 07_step3_pass2_placement.md §8.
            ext_role = "fluid_extension" if surface == "fluid" else "extension"
            buildings_for_spine: dict[Coord, str] = {
                cell: ext_role for cell in scratch.extension_facings
            }
            spine_seeds = frozenset(
                spine_seed_voids_adjacent_extensions(
                    buildings_for_spine,
                    set(asteroid),
                )
            )
            priority_seeds_arg = (
                spine_seeds if pass2_spine_priority_enabled and spine_seeds else None
            )
            pass2_preserve_trunk_baseline: frozenset[Coord] | None = None
            if isinstance(ela_sk, str) and ela_sk == "existing_fluid_layout":
                pass2_preserve_trunk_baseline = frozenset(scratch.transport_cells)
            placed_p2 = run_pass2_internal_placement_mvp(
                mineable_cells=mineable,
                asteroid_cells=asteroid,
                scratch=scratch,
                is_external=is_external,
                hard_barrier_cells=pass2_hard_barriers,
                replay_events=replay_events,
                priority_seeds=priority_seeds_arg,
                extra_transport_block_cells=extra_transport_blocks,
                placement_transport_blocked_counter=placement_transport_blocked_counter,
                adjacent_preserve_trunk_baseline_cells=pass2_preserve_trunk_baseline,
                pass2_route_probe_pack=pass2_route_probe_pack,
            )
        finalize_pass2_route_probe_stats(pass2_probe_stats)
        merged_pass1 = _merge_pass1_into_rows(
            working_map,
            final_mining_map,
            scratch_after_pass1,
            transport_init,
            blocked_init,
            mineable,
            surface,
        )
        merged_pass2 = _merge_pass1_into_rows(
            working_map, final_mining_map, scratch, transport_init, blocked_init, mineable, surface
        )
        if getattr(settings, "SHAPEZ_MINING_ASSERT_SCRATCH_TRANSPORT_SUBSET", False):
            from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.spatial_authority import (  # noqa: E501
                assert_scratch_transport_subset_of_map,
            )

            assert_scratch_transport_subset_of_map(
                scratch, merged_pass2, context="post_pass2_merge"
            )
        pass1_new_transport_cells = tr_before_p2 - len(transport_init)
        final_transport_cells = _transport_cell_coords_from_map_rows(merged_pass2)
        ex_base_n = len(existing_transport_baseline)
        tr_init_n = len(transport_init)
        reuse_vs_baseline = len(existing_transport_baseline & final_transport_cells) / max(
            1, ex_base_n
        )
        reuse_vs_working = len(frozenset(transport_init) & final_transport_cells) / max(
            1, tr_init_n
        )
        stats: dict[str, Any] = {
            "pass1_outer_placements": placed,
            "pass1_new_extractor_cells": ex_before_p2 - extractors_after_seed,
            "pass1_new_extension_cells": ext_before_p2 - extensions_after_seed,
            "pass1_preserved_transport_cells": tr_init_n,
            "pass12_working_map_transport_cells_initial": tr_init_n,
            "pass12_merged_seed_transport_cells_baseline": ex_base_n,
            "pass1_new_transport_cells": pass1_new_transport_cells,
            "pass1_total_transport_cells_after": tr_before_p2,
            "pass2_internal_placements": placed_p2,
            "pass2_new_extractor_cells": len(scratch.extractor_cells) - ex_before_p2,
            "pass2_new_extension_cells": len(scratch.extension_facings) - ext_before_p2,
            "pass2_new_transport_cells": len(scratch.transport_cells) - tr_before_p2,
            "pass2_spine_seed_count": len(spine_seeds),
            "pass2_spine_priority_applied": bool(priority_seeds_arg),
            "pass12_skipped": False,
            "pass12_skip_reason": None,
            "pass12_mixed_surface_skipped": False,
            "placement_records": dict(scratch.placement_records),
            "placement_candidate_blocked_count": int(placement_transport_blocked_counter[0]),
            "pass12_placement_loops_suppressed": bool(sp1 and sp2),
            "pass12_pass1_loop_suppressed": bool(sp1),
            "pass12_pass2_loop_suppressed": bool(sp2),
            "existing_transport_cell_count_baseline": ex_base_n,
            "existing_transport_reuse_ratio_after_pass12": round(reuse_vs_baseline, 6),
            "existing_transport_reuse_ratio_vs_working_initial_after_pass12": round(
                reuse_vs_working, 6
            ),
            **pass2_probe_stats,
            **preserve_seed_stats,
            **ela_meta,
        }
        if replay_events is not None and pass12_txn_id is not None:
            assert map_before_pass12 is not None
            diff_pl = diff_mining_maps(map_before_pass12, merged_pass2)
            diff_pl.update(replay_transaction_payload(transaction_id=pass12_txn_id))
            replay_events.append(
                {
                    "kind": SolverMutationEventKind.MAP_DIFF_COMMITTED.value,
                    "phase": "pass12",
                    "payload": diff_pl,
                }
            )
            stats["_replay_pass12_transaction_id"] = pass12_txn_id
        return merged_pass1, merged_pass2, stats
    except BaseException:
        if replay_events is not None and pass12_txn_id is not None:
            replay_events.append(
                {
                    "kind": SolverMutationEventKind.ROLLBACK.value,
                    "phase": "pass12",
                    "payload": replay_transaction_payload(transaction_id=pass12_txn_id),
                }
            )
        raise


def integrate_pass1_outer_into_working_map(
    *,
    working_map: list[dict[str, Any]],
    final_mining_map: list[dict[str, Any]],
    is_external: Callable[[Coord], bool],
    existing_layout_analysis: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Deprecated compatibility name: runs full Pass12 and returns the **post-Pass2** merged map.

    Despite ``pass1_outer`` in the name, this is not Pass1-only; callers should prefer
    ``integrate_pass12_placement_into_working_map`` for explicit Pass1/Pass2 frames.
    """

    _, merged_pass2, stats = integrate_pass12_placement_into_working_map(
        working_map=working_map,
        final_mining_map=final_mining_map,
        is_external=is_external,
        existing_layout_analysis=existing_layout_analysis,
    )
    return merged_pass2, stats
