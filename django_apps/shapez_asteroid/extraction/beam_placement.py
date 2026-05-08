"""Beam placement of extractor+extension clusters (STEP2 MVP)."""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from django_apps.shapez_asteroid.extraction.canonical import canonicalize_cluster
from django_apps.shapez_asteroid.extraction.constants import (
    BEAM_DEFAULT_MAX_CLUSTERS_CAP,
    BEAM_ENUM_MAX_EXTENSION_DEPTH,
    BEAM_HARD_CAP,
    BEAM_MAX_CORE_CANDIDATES_PER_STATE,
    BEAM_TIME_BUDGET_SEC,
    CLUSTER_TILE_ESTIMATE,
    DEFAULT_BEAM_WIDTH,
    EXTENSION_MAX_PER_CLUSTER,
    ITEMS_PER_MIN_PER_SHAPE_SLOT,
    SHAPE_SLOTS_PER_CORE,
    SHAPE_SLOTS_PER_EXTENSION,
)
from django_apps.shapez_asteroid.extraction.reachability import cheap_transport_escape_exists
from django_apps.shapez_asteroid.extraction.shape_miner_rotation import (
    shape_miner_extension_positions,
    shape_miner_output_cell,
)
from django_apps.shapez_asteroid.extraction.shapez_grid import cores_shapez_adjacent, neighbors4
from django_apps.shapez_asteroid.services.asteroid_reconstruction import AsteroidReconstruction

Coord = tuple[int, int]


@dataclass(frozen=True, slots=True)
class ExtractorCluster:
    core: Coord
    extensions: tuple[Coord, ...]
    cells: frozenset[Coord]
    rotation: int

    @property
    def slots(self) -> int:
        return SHAPE_SLOTS_PER_CORE + SHAPE_SLOTS_PER_EXTENSION * len(self.extensions)

    def canonical_signature(self) -> frozenset[Coord]:
        return canonicalize_cluster(cells=self.cells, anchor=self.core)


def throughput_items_per_min_from_slots(slots: int) -> float:
    return float(ITEMS_PER_MIN_PER_SHAPE_SLOT * slots)


def enumerate_rotated_chain_clusters(
    core: Coord,
    forbidden: frozenset[Coord],
    mineable: frozenset[Coord],
) -> Iterator[ExtractorCluster]:
    """Yield (core, rotation, straight extension chain) clusters with valid void output."""

    if core not in mineable:
        return
    max_ext = min(EXTENSION_MAX_PER_CLUSTER, BEAM_ENUM_MAX_EXTENSION_DEPTH)

    for r in range(4):
        out_cell = shape_miner_output_cell(core, r)
        if out_cell is None or out_cell in forbidden:
            continue
        for ext_count in range(0, max_ext + 1):
            exts = shape_miner_extension_positions(core, r, ext_count)
            if exts is None:
                continue
            if any(p not in mineable or p in forbidden for p in exts):
                continue
            cells = frozenset({core, *exts})
            if out_cell in cells:
                continue
            if cells & forbidden:
                continue
            yield ExtractorCluster(core=core, extensions=exts, cells=cells, rotation=r)


def cluster_span_penalty(cells: frozenset[Coord]) -> float:
    if not cells:
        return 0.0
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    span = max(xs) - min(xs) + max(ys) - min(ys)
    return float(span) * 0.08


def _default_max_clusters(mineable_count: int) -> int:
    """At most one cluster per CLUSTER_TILE_ESTIMATE mineable cells, capped by BEAM_HARD_CAP."""

    return min(
        max(1, math.ceil(mineable_count / CLUSTER_TILE_ESTIMATE)),
        BEAM_DEFAULT_MAX_CLUSTERS_CAP,
        BEAM_HARD_CAP,
    )


def _placement_sort_key(placements: tuple[ExtractorCluster, ...]) -> tuple[int, float, float]:
    """Lexicographic beam objective: coverage, throughput, then less scatter (via -scatter term)."""

    used: set[Coord] = set()
    for c in placements:
        used |= set(c.cells)
    coverage = len(used)
    throughput = sum(throughput_items_per_min_from_slots(c.slots) for c in placements)
    scatter = sum(cluster_span_penalty(c.cells) for c in placements)
    return (coverage, throughput, -scatter)


def _state_can_beat_best(
    *,
    placements: tuple[ExtractorCluster, ...],
    free_count: int,
    best_key: tuple[int, float, float],
) -> bool:
    """남은 자유 셀 상한으로 현재 best를 넘을 수 있는지 빠르게 본다."""

    current_key = _placement_sort_key(placements)
    if best_key[0] < 0:
        return True
    max_extra_throughput = throughput_items_per_min_from_slots(
        free_count * (SHAPE_SLOTS_PER_CORE + SHAPE_SLOTS_PER_EXTENSION)
    )
    upper_key = (
        current_key[0] + free_count,
        current_key[1] + max_extra_throughput,
        current_key[2],
    )
    return upper_key > best_key


def _fragmentation_ratio(free_cells: frozenset[Coord]) -> float:
    """4이웃이 없는 자유 셀 비율을 fragmentation 프록시로 쓴다."""

    if not free_cells:
        return 0.0
    isolated = 0
    for cell in free_cells:
        if not any(nb in free_cells for nb in neighbors4(cell[0], cell[1])):
            isolated += 1
    return isolated / float(len(free_cells))


def beam_place_clusters(
    *,
    rec: AsteroidReconstruction,
    beam_width: int = DEFAULT_BEAM_WIDTH,
    max_clusters: int | None = None,
    transport_kind: str = "belt",
    on_round: Callable[[int, int], None] | None = None,
    time_budget_sec: float = BEAM_TIME_BUDGET_SEC,
) -> tuple[ExtractorCluster, ...]:
    mineable = frozenset(rec.mineable_placement_cells)
    if not mineable:
        return tuple()

    max_rounds = (
        min(max(1, max_clusters), BEAM_HARD_CAP)
        if max_clusters is not None
        else _default_max_clusters(len(mineable))
    )

    routed_empty: frozenset[Coord] = frozenset()

    empty_placements: tuple[ExtractorCluster, ...] = tuple()
    State = tuple[tuple[int, float, float], tuple[ExtractorCluster, ...], frozenset[Coord]]
    frontier: list[State] = [(_placement_sort_key(empty_placements), empty_placements, frozenset())]
    global_best_key: tuple[int, float, float] = (-1, -1.0, -1.0)
    global_best_solution: tuple[ExtractorCluster, ...] = tuple()
    deadline = time.monotonic() + max(0.25, float(time_budget_sec))

    for _round_i in range(max_rounds):
        if time.monotonic() >= deadline:
            break
        next_states: list[State] = []
        for _old_key, placements, used_cells in frontier:
            if time.monotonic() >= deadline:
                break
            free_cells = frozenset(c for c in mineable if c not in used_cells)
            if not _state_can_beat_best(
                placements=placements,
                free_count=len(free_cells),
                best_key=global_best_key,
            ):
                continue
            frag_ratio = _fragmentation_ratio(free_cells)
            free_sorted = sorted(
                free_cells,
                key=lambda c: (
                    sum(1 for nb in neighbors4(c[0], c[1]) if nb in free_cells),
                    -frag_ratio,
                    -c[1],
                    -c[0],
                ),
                reverse=True,
            )
            for core in free_sorted[:BEAM_MAX_CORE_CANDIDATES_PER_STATE]:
                if time.monotonic() >= deadline:
                    break
                forbidden = used_cells
                for cluster in enumerate_rotated_chain_clusters(core, forbidden, mineable):
                    if time.monotonic() >= deadline:
                        break
                    if cluster.cells & used_cells:
                        continue
                    if any(cores_shapez_adjacent(p.core, cluster.core) for p in placements):
                        continue
                    if not cheap_transport_escape_exists(
                        rec=rec,
                        extractor_core=cluster.core,
                        rotation=cluster.rotation,
                        cluster_cells=cluster.cells,
                        routed_transport_cells=routed_empty,
                        additional_blocked_cells=forbidden,
                        transport_kind=transport_kind,
                    ):
                        continue
                    new_used = used_cells | cluster.cells
                    new_placements = placements + (cluster,)
                    sk = _placement_sort_key(new_placements)
                    if sk > global_best_key:
                        global_best_key = sk
                        global_best_solution = new_placements
                    next_states.append((sk, new_placements, new_used))

        if not next_states:
            break
        next_states.sort(key=lambda t: (t[0], len(t[1])), reverse=True)
        refined: list[State] = []
        seen_plc: set[tuple[ExtractorCluster, ...]] = set()
        for sk, plc, ud in next_states:
            if plc in seen_plc:
                continue
            seen_plc.add(plc)
            refined.append((sk, plc, ud))
        frontier = refined[:beam_width]
        if on_round is not None:
            on_round(_round_i, max_rounds)

    return global_best_solution
