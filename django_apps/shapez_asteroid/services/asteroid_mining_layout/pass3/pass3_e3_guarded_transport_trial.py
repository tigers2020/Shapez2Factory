"""Trial transport maps for P3-E3 guarded validation (no committed layout mutation)."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    P3E3_REJECT_CONNECTIVITY,
    P3E3_REJECT_FIXED_STUB_REMOVAL,
    P3E3_REJECT_GEOMETRY,
    P3E3_REJECT_HARD_PROTECTED_CORRIDOR,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


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


def _p3e3_validate_candidate_transport_map(
    *,
    cells_base: dict[Coord, dict[str, Any]],
    want_role: str,
    candidate_transport_cells: frozenset[Coord],
    fixed_output_stubs: frozenset[Coord],
    hard_protected_corridors: frozenset[Coord],
) -> tuple[bool, str | None]:
    """Assertion gate only: no rerouting; uses :func:`validate_final_mining_layout`."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        validate_final_mining_layout,
    )

    if not fixed_output_stubs.issubset(candidate_transport_cells):
        return False, P3E3_REJECT_FIXED_STUB_REMOVAL
    if hard_protected_corridors and not hard_protected_corridors.issubset(
        candidate_transport_cells
    ):
        return False, P3E3_REJECT_HARD_PROTECTED_CORRIDOR

    trial_cells = _p3e3_apply_candidate_transport_to_cells(
        cells_base, want_role=want_role, candidate_transport=candidate_transport_cells
    )
    trial_map = _p3e3_cells_to_mining_map_rows(trial_cells)
    report = validate_final_mining_layout(trial_map)
    if report.geometry_valid and report.connectivity_valid:
        return True, None
    if not report.geometry_valid:
        return False, P3E3_REJECT_GEOMETRY
    return False, P3E3_REJECT_CONNECTIVITY


def _p3e3_validate_post_commit_transport_map(
    *,
    cells_base: dict[Coord, dict[str, Any]],
    want_role: str,
    candidate_transport_cells: frozenset[Coord],
    fixed_output_stubs: frozenset[Coord],
    hard_protected_corridors: frozenset[Coord],
) -> tuple[bool, str | None]:
    """Post-swap check: same gate as pre-commit (``validate_final_mining_layout``)."""

    return _p3e3_validate_candidate_transport_map(
        cells_base=cells_base,
        want_role=want_role,
        candidate_transport_cells=candidate_transport_cells,
        fixed_output_stubs=fixed_output_stubs,
        hard_protected_corridors=hard_protected_corridors,
    )


def _p3e3_validate_guarded_swap_mining_map(
    *,
    mining_map: list[dict[str, Any]],
    transport_cells: dict[Coord, str],
    want_role: str,
    candidate_transport_cells: frozenset[Coord],
    fixed_output_stubs: frozenset[Coord],
    hard_protected_corridors: frozenset[Coord],
) -> tuple[bool, str | None]:
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

    if not fixed_output_stubs.issubset(candidate_transport_cells):
        return False, P3E3_REJECT_FIXED_STUB_REMOVAL
    if hard_protected_corridors and not hard_protected_corridors.issubset(
        candidate_transport_cells
    ):
        return False, P3E3_REJECT_HARD_PROTECTED_CORRIDOR

    trial_map = mining_map_after_transport_reconstruction(
        mining_map,
        transport_cells,
        target_role=want_role,
    )
    report = validate_final_mining_layout(trial_map)
    if report.geometry_valid and report.connectivity_valid:
        return True, None
    if not report.geometry_valid:
        return False, P3E3_REJECT_GEOMETRY
    return False, P3E3_REJECT_CONNECTIVITY
