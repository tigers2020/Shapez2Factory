"""Timeline frame TypedDicts and pass3-scan grid rollback snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


class SolverTimelinePass3Payload(TypedDict, total=False):
    """Optional ``pass3`` object on solver timeline frames."""

    committed: bool
    gain: int
    score_before: int
    score_after: int
    metrics: dict[str, Any]


class SolverTimelineFrame(TypedDict, total=False):
    """One element of ``result["solver_timeline"]`` from ``build_solver_timeline``."""

    id: str
    summary: dict[str, Any]
    mining_map: list[dict[str, Any]]
    pass3: SolverTimelinePass3Payload


@dataclass(frozen=True)
class MiningLayoutGridRollback:
    """Immutable snapshot for pass3-scan rollback (occupied/buildings/transport graph)."""

    occupied: frozenset[Coord]
    buildings: dict[Coord, str]
    transport_cells: dict[Coord, str]
    outlets_order: tuple[Coord, ...]
    extractor_facing: dict[Coord, Coord]
    extension_parents: dict[Coord, Coord]
    extension_facing: dict[Coord, Coord]

    @classmethod
    def capture(
        cls,
        *,
        occupied: set[Coord],
        buildings: dict[Coord, str],
        transport_cells: dict[Coord, str],
        outlets_order: list[Coord],
        extractor_facing: dict[Coord, Coord],
        extension_parents: dict[Coord, Coord],
        extension_facing: dict[Coord, Coord],
    ) -> MiningLayoutGridRollback:
        """Pass3-scan rollback snapshot을 현재 scratch 상태에서 캡처한다.

                transport reconstruction 후 재스캔 실패 시 원복 기준이다 (§11 Pass3 transport).

        상세: documents/Algorithm/mining_solver_cursor_sessions/09_step5_pass3_transport.md"""
        return cls(
            frozenset(occupied),
            dict(buildings),
            dict(transport_cells),
            tuple(outlets_order),
            dict(extractor_facing),
            dict(extension_parents),
            dict(extension_facing),
        )

    def restore_into(
        self,
        *,
        occupied: set[Coord],
        buildings: dict[Coord, str],
        outlets_order: list[Coord],
        extractor_facing: dict[Coord, Coord],
        extension_parents: dict[Coord, Coord],
        extension_facing: dict[Coord, Coord],
    ) -> dict[Coord, str]:
        """Mutate live collections to match this snapshot; returns new ``transport_cells`` dict."""

        occupied.clear()
        occupied.update(self.occupied)
        buildings.clear()
        buildings.update(self.buildings)
        outlets_order[:] = list(self.outlets_order)
        extractor_facing.clear()
        extractor_facing.update(self.extractor_facing)
        extension_parents.clear()
        extension_parents.update(self.extension_parents)
        extension_facing.clear()
        extension_facing.update(self.extension_facing)
        return dict(self.transport_cells)
