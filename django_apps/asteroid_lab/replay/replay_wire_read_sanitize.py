"""Read-path replay wire sanitizer (candidate compat) and committed-cell audit."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import cast

from django_apps.asteroid_lab.replay.overlay_wire_contract import (
    CANDIDATE_OUTPUT_OVERLAY_KINDS,
)
from django_apps.asteroid_lab.replay.replay_cell_semantics import (
    normalize_project_transport_kind,
)
from django_apps.asteroid_lab.replay.replay_map_cell_wire import (
    wire_field_kind,
    wire_field_transport,
)
from django_apps.asteroid_lab.typing_boundary import JsonObject

_BANNED_CANDIDATE_OCCUPANCY = frozenset(
    {
        "space_belt",
        "space_pipe",
        "shape_belt",
        "fluid_pipe",
        "shape",
        "fluid",
        "belt",
        "pipe",
    }
)

# Legacy occupancy tokens on committed transport rows — not canonical space_belt/space_pipe.
_BANNED_LEGACY_COMMITTED_TRANSPORT = frozenset(
    {
        "shape_belt",
        "fluid_pipe",
        "shape",
        "fluid",
        "belt",
        "pipe",
    }
)

_COMMITTED_TRANSPORT_KINDS = frozenset({"space_belt", "space_pipe"})


class ReplayWireAuditError(ValueError):
    """Committed wire row violates replay transport contract."""


def is_candidate_output_hint_kind(kind: str) -> bool:
    return kind in CANDIDATE_OUTPUT_OVERLAY_KINDS


def audit_replay_wire_cell(row: Mapping[str, object]) -> None:
    kind = wire_field_kind(row)
    transport = wire_field_transport(row).strip().lower()
    if is_candidate_output_hint_kind(kind):
        if transport in _BANNED_CANDIDATE_OCCUPANCY:
            raise ReplayWireAuditError(
                f"candidate overlay kind={kind!r} must not claim transport={transport!r}"
            )
        return
    if kind in _COMMITTED_TRANSPORT_KINDS and transport in _BANNED_LEGACY_COMMITTED_TRANSPORT:
        raise ReplayWireAuditError(
            f"committed transport kind={kind!r} has invalid transport={transport!r}"
        )


def sanitize_replay_wire_cell_for_read(row: Mapping[str, object]) -> JsonObject:
    """Normalize legacy candidate occupancy transport for display merge input only."""

    out = cast(JsonObject, copy.deepcopy(dict(row)))
    kind = wire_field_kind(out)
    if not is_candidate_output_hint_kind(kind):
        return out
    transport = wire_field_transport(out).strip().lower()
    if transport not in _BANNED_CANDIDATE_OCCUPANCY:
        audit_replay_wire_cell(out)
        return out
    normalized = normalize_project_transport_kind(transport)
    if normalized == "none":
        audit_replay_wire_cell(out)
        return out
    out["transport"] = "none"
    out["transport_kind"] = "none"
    existing = str(out.get("output_transport_kind") or "").strip()
    if not existing or normalize_project_transport_kind(existing) == "none":
        out["output_transport_kind"] = normalized
    return out


__all__ = [
    "ReplayWireAuditError",
    "audit_replay_wire_cell",
    "is_candidate_output_hint_kind",
    "sanitize_replay_wire_cell_for_read",
]
