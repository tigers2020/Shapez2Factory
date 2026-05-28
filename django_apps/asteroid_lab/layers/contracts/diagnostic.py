"""Non-resumable diagnostic snapshots (observability only)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DiagnosticLayerSnapshot:
    """Output-only layer snapshot; not a valid stack restart input."""

    layer_slug: str
    layer_index: int
    payload: dict[str, object]
