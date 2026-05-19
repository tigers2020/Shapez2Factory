"""Phase K — route reservation → belt/pipe layout materialization (PR6)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.commit_best_candidates import IncrementalCommitResult
from django_apps.asteroid_lab.optimization.coord_transform import steps_from_canonical_e
from django_apps.asteroid_lab.optimization.coords import Coord, cardinal_unit_toward
from django_apps.asteroid_lab.optimization.enums import (
    Direction,
    MaterializationFailureReason,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.input_contracts import RouteReservation
from django_apps.asteroid_lab.optimization.materialization_dtos import (
    MaterializedLayoutCells,
    MaterializedTransportCell,
    RouteMaterializationResult,
)

_DIRECTION_ORDER: tuple[Direction, ...] = (Direction.N, Direction.E, Direction.S, Direction.W)


def _opposite(direction: Direction) -> Direction:
    if direction == Direction.N:
        return Direction.S
    if direction == Direction.S:
        return Direction.N
    if direction == Direction.E:
        return Direction.W
    return Direction.E


def _transport_prefix(kind: TransportKind) -> str:
    if kind == TransportKind.SHAPE_BELT:
        return "SpaceBelt_"
    if kind == TransportKind.FLUID_PIPE:
        return "SpacePipe_"
    msg = f"unsupported transport kind: {kind}"
    raise ValueError(msg)


def _dedupe_consecutive_path(path: tuple[Coord, ...]) -> tuple[Coord, ...]:
    if not path:
        return ()
    out: list[Coord] = [path[0]]
    for cell in path[1:]:
        if cell != out[-1]:
            out.append(cell)
    return tuple(out)


def full_path_for_reservation(
    candidate: GeneCandidate,
    reservation: RouteReservation,
) -> tuple[Coord, ...]:
    """OD-1: prepend ``fixed_output_transport`` before reservation probe path."""

    combined = (candidate.fixed_output_transport,) + reservation.path
    return _dedupe_consecutive_path(combined)


@dataclass
class _CellFlow:
    incoming: set[Direction] = field(default_factory=set)
    outgoing: set[Direction] = field(default_factory=set)


def _aggregate_flows(paths: tuple[tuple[Coord, ...], ...]) -> dict[Coord, _CellFlow]:
    flows: dict[Coord, _CellFlow] = defaultdict(_CellFlow)
    for path in paths:
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            step = cardinal_unit_toward(a, b)
            flows[a].outgoing.add(step)
            flows[b].incoming.add(_opposite(step))
    return dict(flows)


def _sorted_directions(directions: set[Direction]) -> tuple[Direction, ...]:
    return tuple(d for d in _DIRECTION_ORDER if d in directions)


def _is_triple_incoming(incoming: frozenset[Direction]) -> bool:
    """Triple merger: three arms without a single axis passing through."""

    if len(incoming) != 3:
        return False
    ordered = _sorted_directions(set(incoming))
    return ordered == (Direction.N, Direction.E, Direction.W) or ordered == (
        Direction.E,
        Direction.S,
        Direction.W,
    )


def _straight_tile(prefix: str, _incoming: Direction, _outgoing: Direction) -> str:
    return f"{prefix}Forward"


def _turn_tile(prefix: str, incoming: Direction, outgoing: Direction) -> str:
    pairs = (incoming, outgoing)
    left_turns = {
        (Direction.W, Direction.S),
        (Direction.S, Direction.E),
        (Direction.E, Direction.N),
        (Direction.N, Direction.W),
    }
    if pairs in left_turns:
        return f"{prefix}LeftTurn"
    return f"{prefix}RightTurn"


def _fwd_merger_tile(prefix: str, outgoing: Direction) -> str:
    if outgoing == Direction.W:
        return f"{prefix}LeftFwdMerger"
    return f"{prefix}RightFwdMerger"


def _fwd_splitter_tile(prefix: str, incoming: Direction) -> str:
    if incoming == Direction.W:
        return f"{prefix}LeftFwdSplitter"
    return f"{prefix}RightFwdSplitter"


def pick_tile_type(
    transport_kind: TransportKind,
    incoming: frozenset[Direction],
    outgoing: frozenset[Direction],
) -> str:
    """Deterministic belt/pipe sprite kind from aggregated flow at one cell."""

    prefix = _transport_prefix(transport_kind)
    ins = frozenset(incoming)
    outs = frozenset(outgoing)
    in_count = len(ins)
    out_count = len(outs)

    if in_count == 0 and out_count == 1:
        return f"{prefix}Forward"

    if in_count == 1 and out_count == 0:
        return f"{prefix}Forward"

    if in_count == 1 and out_count == 1:
        i_dir = next(iter(ins))
        o_dir = next(iter(outs))
        if _opposite(i_dir) == o_dir:
            return _straight_tile(prefix, i_dir, o_dir)
        return _turn_tile(prefix, i_dir, o_dir)

    if in_count >= 2 and out_count == 1:
        o_dir = next(iter(outs))
        if in_count == 3:
            if _is_triple_incoming(ins):
                return f"{prefix}TripleMerger"
            return f"{prefix}YMerger"
        return _fwd_merger_tile(prefix, o_dir)

    if in_count == 1 and out_count >= 2:
        i_dir = next(iter(ins))
        if out_count == 3:
            if _is_triple_incoming(frozenset(_opposite(d) for d in outs)):
                return f"{prefix}TripleSplitter"
            return f"{prefix}YSplitter"
        return _fwd_splitter_tile(prefix, i_dir)

    if in_count >= 2 and out_count >= 2:
        return f"{prefix}YMerger"

    return f"{prefix}Forward"


def _primary_outgoing(
    incoming: frozenset[Direction],
    outgoing: frozenset[Direction],
) -> Direction:
    """Primary output direction used to compute domain rotation."""
    if outgoing:
        if incoming:
            fwd = _opposite(_sorted_directions(set(incoming))[0])
            if fwd in outgoing:
                return fwd
        return _sorted_directions(set(outgoing))[0]
    if incoming:
        return _opposite(_sorted_directions(set(incoming))[0])
    return Direction.E


def pick_tile_rotation(
    incoming: frozenset[Direction],
    outgoing: frozenset[Direction],
) -> int:
    """Domain quarter-turn rotation for a materialized cell (0=E, 1=S, 2=W, 3=N)."""
    return steps_from_canonical_e(_primary_outgoing(incoming, outgoing))


def materialize_route_network(
    commit: IncrementalCommitResult,
    candidates_by_id: Mapping[str, GeneCandidate],
) -> RouteMaterializationResult:
    """Materialize confirmed route reservations into belt/pipe cells."""

    paths_by_kind: dict[TransportKind, list[tuple[Coord, ...]]] = defaultdict(list)
    coord_kinds: dict[Coord, set[TransportKind]] = defaultdict(set)

    for placement in commit.confirmed:
        candidate = candidates_by_id[placement.candidate_id]
        reservation = placement.reservation
        full_path = full_path_for_reservation(candidate, reservation)
        kind = reservation.transport_kind
        paths_by_kind[kind].append(full_path)
        for coord in full_path:
            coord_kinds[coord].add(kind)

    for kinds in coord_kinds.values():
        if len(kinds) > 1:
            return RouteMaterializationResult(
                layout=None,
                failure_reason=MaterializationFailureReason.TRANSPORT_KIND_OVERLAP,
            )

    cells: list[MaterializedTransportCell] = []
    for kind, paths in sorted(paths_by_kind.items(), key=lambda kv: kv[0].value):
        flows = _aggregate_flows(tuple(paths))
        for coord in sorted(flows.keys(), key=lambda c: (c[1], c[0])):
            flow = flows[coord]
            ins = frozenset(flow.incoming)
            outs = frozenset(flow.outgoing)
            tile_type = pick_tile_type(kind, ins, outs)
            rotation = pick_tile_rotation(ins, outs)
            cells.append(
                MaterializedTransportCell(
                    coord=coord,
                    tile_type=tile_type,
                    transport_kind=kind,
                    rotation=rotation,
                )
            )

    return RouteMaterializationResult(
        layout=MaterializedLayoutCells(cells=tuple(cells)),
        failure_reason=None,
    )
