"""Pure boundary observability seam (no Django, no settings, no file I/O).

The decode / cleanup / reconstruction pipelines build their boundary payloads in pure core and
hand them to an injected :class:`BoundaryTraceSink`. The default sink is a no-op, so core never
writes JSONL or reads settings. The Django side supplies a sink adapter that forwards to the
settings/file-I/O ``emit_boundary_jsonl`` writer when ``ASTEROID_LAB_BOUNDARY_JSONL`` is enabled.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from shapez2_factory.domain.asteroid_lab.decoded_cell import DecodedCellDTO


class BoundaryTraceSink(Protocol):
    """Receives one boundary record built by a pure pipeline stage."""

    def emit(
        self,
        *,
        run_id: str,
        stage: str,
        boundary: str,
        data: dict[str, object],
    ) -> None: ...


class NullBoundaryTraceSink:
    """No-op sink used by default so core stays side-effect free."""

    def emit(
        self,
        *,
        run_id: str,
        stage: str,
        boundary: str,
        data: dict[str, object],
    ) -> None:
        return None


NO_OP_BOUNDARY_SINK: BoundaryTraceSink = NullBoundaryTraceSink()


def summarize_cell_kind_transitions(
    before: Sequence[DecodedCellDTO],
    after: Sequence[DecodedCellDTO],
    *,
    max_items: int = 8000,
) -> list[dict[str, object]]:
    """Pair cells by ``(x, y, layer)`` and list ``cell_kind`` changes (for boundary payloads).

    Each item includes explicit ``raw_x`` / ``raw_y`` names.
    """

    before_map: dict[tuple[int, int, int | None], str] = {}
    for c in before:
        before_map[(c.x, c.y, c.layer)] = str(c.cell_kind)

    out: list[dict[str, object]] = []
    for c in after:
        key = (c.x, c.y, c.layer)
        prev = before_map.get(key)
        cur = str(c.cell_kind)
        if prev != cur:
            item: dict[str, object] = {
                "raw_x": key[0],
                "raw_y": key[1],
                "layer": key[2],
                "cell_kind_before": prev,
                "cell_kind_after": cur,
            }
            out.append(item)
        if len(out) >= max_items:
            break
    return out


__all__ = [
    "NO_OP_BOUNDARY_SINK",
    "BoundaryTraceSink",
    "NullBoundaryTraceSink",
    "summarize_cell_kind_transitions",
]
