"""Trial transport maps for P3-E3 guarded validation (no committed layout mutation)."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import shape_miner_output_cell
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    P3E3_REJECT_CONNECTIVITY,
    P3E3_REJECT_DISCONNECTED_STUB,
    P3E3_REJECT_EXTERNAL_UNREACHABLE_TRANSPORT,
    P3E3_REJECT_FIXED_STUB_REMOVAL,
    P3E3_REJECT_GEOMETRY,
    P3E3_REJECT_HARD_PROTECTED_CORRIDOR,
    P3E3_REJECT_ORPHAN_TRANSPORT,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.route_probe import (
    probe_stub_to_external,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    EXTRACTORS_FLUID,
    EXTRACTORS_SHAPE,
    blocked_cells,
    layout_kind,
    transport_kind_for_extractor,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation_contracts import (  # noqa: E501
    FinalValidationReport,
)


def _p3e3_apply_candidate_transport_to_cells(
    cells: dict[Coord, dict[str, Any]],
    *,
    want_role: str,
    candidate_transport: frozenset[Coord],
) -> dict[Coord, dict[str, Any]]:
    """Replace same-kind transport cells with ``candidate_transport`` (for validation only)."""

    out: dict[Coord, dict[str, Any]] = {k: dict(v) for k, v in cells.items()}
    belt_template: dict[str, Any] | None = None
    for _c, row in out.items():
        if row.get("role") == want_role:
            belt_template = dict(row)
            break
    if belt_template is None:
        belt_template = {"role": want_role}
    for c in list(out.keys()):
        if out[c].get("role") == want_role and c not in candidate_transport:
            del out[c]
    for c in candidate_transport:
        if c not in out:
            nr = dict(belt_template)
            nr["x"], nr["y"] = c[0], c[1]
            nr["role"] = want_role
            out[c] = nr
        elif out[c].get("role") != want_role:
            nr = dict(out[c])
            nr["role"] = want_role
            nr["x"], nr["y"] = c[0], c[1]
            out[c] = nr
    return out


def _p3e3_cells_to_mining_map_rows(cells: dict[Coord, dict[str, Any]]) -> list[dict[str, Any]]:
    """candidate transport 셀 집합을 validation용 mining_map rows로 합성한다 (§11 P3-E3)."""
    ordered = sorted(cells.keys(), key=lambda p: (p[1], p[0]))
    return [dict(cells[k]) for k in ordered]


def _p3e3_first_disconnected_stub_cell(
    cells: dict[Coord, dict[str, Any]],
    *,
    transport_cells: frozenset[Coord],
    blocked: frozenset[Coord],
    is_external: Any,
) -> list[int] | None:
    """First extractor stub that cannot reach external (same predicate as §15 validation)."""

    fc_transport = transport_cells
    fc_blocked = blocked
    for c, row in sorted(cells.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        lk = layout_kind(row)
        if lk not in EXTRACTORS_SHAPE | EXTRACTORS_FLUID:
            continue
        tk = transport_kind_for_extractor(row)
        if tk is None:
            continue
        raw_r = row.get("r")
        if isinstance(raw_r, int):
            stub_cell = shape_miner_output_cell(c, raw_r)
            if stub_cell is None:
                continue
            st = cells.get(stub_cell)
            ok_kind = st is not None and (
                (tk == "shape_belt" and st.get("role") == "belt")
                or (tk == "fluid_pipe" and st.get("role") == "pipe")
            )
            if not ok_kind:
                continue
            if not probe_stub_to_external(
                stub_cell=stub_cell,
                transport_cells=fc_transport,
                blocked_cells=fc_blocked,
                is_external=is_external,
            ):
                return [stub_cell[0], stub_cell[1]]
    return None


def _p3e3_connectivity_failure_reason_and_diag(
    *,
    trial_map: list[dict[str, Any]],
    report: FinalValidationReport,
    transport_kind: str,
) -> tuple[str, dict[str, Any]]:
    """Structured connectivity reject + NDJSON-friendly diagnostics."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        cells_dict_from_mining_map,
        external_predicate_for_mining_map,
        transport_cells_reaching_external,
    )

    if report.disconnected_stub_count > 0:
        sub = P3E3_REJECT_DISCONNECTED_STUB
    elif report.orphan_transport_count > 0:
        sub = P3E3_REJECT_ORPHAN_TRANSPORT
    else:
        sub = P3E3_REJECT_EXTERNAL_UNREACHABLE_TRANSPORT

    cells = cells_dict_from_mining_map(trial_map)
    is_ext = external_predicate_for_mining_map(trial_map)
    tc_set = {c for c, row in cells.items() if row.get("role") in ("belt", "pipe")}
    blocked = frozenset(blocked_cells(cells))
    connected_exit = transport_cells_reaching_external(tc_set, set(blocked), is_ext)
    orphans = tc_set - connected_exit
    first_orphan_cells = [[c[0], c[1]] for c in sorted(orphans, key=lambda p: (p[1], p[0]))[:8]]
    first_stub = _p3e3_first_disconnected_stub_cell(
        cells,
        transport_cells=frozenset(tc_set),
        blocked=blocked,
        is_external=is_ext,
    )

    diag: dict[str, Any] = {
        "disconnected_stub_count": int(report.disconnected_stub_count),
        "orphan_transport_count": int(report.orphan_transport_count),
        "external_reachable_transport_count": len(connected_exit),
        "total_transport_count": len(tc_set),
        "failed_transport_kind": transport_kind,
        "first_orphan_cells": first_orphan_cells,
        "first_disconnected_stub": first_stub,
        "p3e3_connectivity_reject_parent": P3E3_REJECT_CONNECTIVITY,
        "p3e3_connectivity_reject_subreason": sub,
    }
    return sub, diag


def _p3e3_validate_candidate_transport_map(
    *,
    cells_base: dict[Coord, dict[str, Any]],
    want_role: str,
    candidate_transport_cells: frozenset[Coord],
    fixed_output_stubs: frozenset[Coord],
    hard_protected_corridors: frozenset[Coord],
    transport_kind: str,
) -> tuple[bool, str | None, dict[str, Any]]:
    """Assertion gate only: no rerouting; uses :func:`validate_final_mining_layout`."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        validate_final_mining_layout,
    )

    empty: dict[str, Any] = {}
    if not fixed_output_stubs.issubset(candidate_transport_cells):
        return False, P3E3_REJECT_FIXED_STUB_REMOVAL, empty
    if hard_protected_corridors and not hard_protected_corridors.issubset(
        candidate_transport_cells
    ):
        return False, P3E3_REJECT_HARD_PROTECTED_CORRIDOR, empty

    trial_cells = _p3e3_apply_candidate_transport_to_cells(
        cells_base, want_role=want_role, candidate_transport=candidate_transport_cells
    )
    trial_map = _p3e3_cells_to_mining_map_rows(trial_cells)
    report = validate_final_mining_layout(trial_map)
    if report.geometry_valid and report.connectivity_valid:
        return True, None, empty
    if not report.geometry_valid:
        return False, P3E3_REJECT_GEOMETRY, empty
    sub, diag = _p3e3_connectivity_failure_reason_and_diag(
        trial_map=trial_map, report=report, transport_kind=transport_kind
    )
    return False, sub, diag


def _p3e3_validate_post_commit_transport_map(
    *,
    cells_base: dict[Coord, dict[str, Any]],
    want_role: str,
    candidate_transport_cells: frozenset[Coord],
    fixed_output_stubs: frozenset[Coord],
    hard_protected_corridors: frozenset[Coord],
    transport_kind: str,
) -> tuple[bool, str | None, dict[str, Any]]:
    """Post-swap check: same gate as pre-commit (``validate_final_mining_layout``)."""

    return _p3e3_validate_candidate_transport_map(
        cells_base=cells_base,
        want_role=want_role,
        candidate_transport_cells=candidate_transport_cells,
        fixed_output_stubs=fixed_output_stubs,
        hard_protected_corridors=hard_protected_corridors,
        transport_kind=transport_kind,
    )


def _p3e3_validate_guarded_swap_mining_map(
    *,
    mining_map: list[dict[str, Any]],
    transport_cells: dict[Coord, str],
    want_role: str,
    candidate_transport_cells: frozenset[Coord],
    fixed_output_stubs: frozenset[Coord],
    hard_protected_corridors: frozenset[Coord],
    transport_kind: str,
) -> tuple[bool, str | None, dict[str, Any]]:
    """Post-swap gate on the **same** rows as :func:`mining_map_after_transport_reconstruction`.

    Greedy Pass3 may mutate the live ``cells`` dict while the committed layout is derived from the
    original ``mining_map`` list; validating only ``cells`` can false-accept swaps that break
    connectivity on the reconstructed map.
    """

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core import (  # noqa: E501
        mining_map_after_transport_reconstruction,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        validate_final_mining_layout,
    )

    empty: dict[str, Any] = {}
    if not fixed_output_stubs.issubset(candidate_transport_cells):
        return False, P3E3_REJECT_FIXED_STUB_REMOVAL, empty
    if hard_protected_corridors and not hard_protected_corridors.issubset(
        candidate_transport_cells
    ):
        return False, P3E3_REJECT_HARD_PROTECTED_CORRIDOR, empty

    trial_map = mining_map_after_transport_reconstruction(
        mining_map,
        transport_cells,
        target_role=want_role,
    )
    report = validate_final_mining_layout(trial_map)
    if report.geometry_valid and report.connectivity_valid:
        return True, None, empty
    if not report.geometry_valid:
        return False, P3E3_REJECT_GEOMETRY, empty
    sub, diag = _p3e3_connectivity_failure_reason_and_diag(
        trial_map=trial_map, report=report, transport_kind=transport_kind
    )
    return False, sub, diag
