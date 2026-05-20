"""Placement equipment materialization tests (CONFIRMED extractor + extensions)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.commit_best_candidates import (
    ConfirmedGenePlacement,
    IncrementalCommitResult,
)
from django_apps.asteroid_lab.optimization.coord_transform import steps_from_canonical_e
from django_apps.asteroid_lab.optimization.enums import (
    Direction,
    MaterializationFailureReason,
    PlacementCommitState,
    ReservationState,
    RouteGoalKind,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.gene_projection import _translate, project_gene_placement
from django_apps.asteroid_lab.optimization.gene_template import (
    extension_attachments_parent_first,
)
from django_apps.asteroid_lab.optimization.gene_template_loader import (
    gene_template_from_generated_sample,
)
from django_apps.asteroid_lab.optimization.input_contracts import RouteGoal, RouteReservation
from django_apps.asteroid_lab.optimization.placement_network_materializer import (
    _direction_child_to_parent_server,
    materialize_confirmed_placements,
    merge_materialized_layout,
    preview_equipment_for_candidate,
)
from django_apps.asteroid_lab.optimization.route_network_materializer import (
    materialize_route_network,
)
from django_apps.asteroid_lab.optimization.route_probe import RouteProbeResult
from django_apps.asteroid_lab.services.sample_gene_exhaustive_generator import (
    generate_exhaustive_sample_genes,
)
from django_apps.asteroid_lab.snapshots.equipment_bundles import ports_compatible


def _goal(*, coord: tuple[int, int], kind: TransportKind) -> RouteGoal:
    return RouteGoal(
        coord=coord,
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=kind,
        priority=10,
        existing_trunk=False,
    )


def _candidate_from_gene(
    *,
    gene_template,
    anchor: tuple[int, int] = (0, 0),
    rotation: Direction = Direction.E,
) -> GeneCandidate:
    projected = project_gene_placement(anchor=anchor, rotation=rotation, gene=gene_template)
    fot = projected.fixed_output_transport
    goal = _goal(coord=(6, 0), kind=TransportKind.SHAPE_BELT)
    path = (fot, (fot[0] + 1, fot[1]), (fot[0] + 2, fot[1]), goal.coord)
    probe = RouteProbeResult(
        reachable=True,
        path=path,
        cost=len(path),
        expanded_nodes=len(path),
        reached_goal=goal,
        goal_priority=goal.priority,
        failure_reason=None,
    )
    return GeneCandidate(
        candidate_id=f"test:{anchor[0]},{anchor[1]}:e:shape_belt",
        gene_id=gene_template.gene_id,
        topology_signature="sig",
        extractor=projected.extractor,
        extensions=projected.extensions,
        occupied_cells=projected.occupied_cells,
        route_probe_start=projected.route_probe_start,
        fixed_output_transport=fot,
        output_dir=rotation,
        transport_kind=TransportKind.SHAPE_BELT,
        base_throughput=gene_template.throughput_factor,
        base_score=float(gene_template.throughput_factor),
        route_probe_result=probe,
    )


def _reservation(candidate: GeneCandidate) -> RouteReservation:
    path = candidate.route_probe_result.path
    fot = candidate.fixed_output_transport
    if fot in path:
        path = path[path.index(fot) :]
    goal = candidate.route_probe_result.reached_goal
    assert goal is not None
    return RouteReservation(
        reservation_id=f"{candidate.candidate_id}:route:0",
        candidate_id=candidate.candidate_id,
        transport_kind=candidate.transport_kind,
        path=path,
        reserved_cells=frozenset(path),
        cost=len(path),
        reached_goal=goal,
        goal_priority=goal.priority,
        reservation_state=ReservationState.CONFIRMED,
        domain_cell_transitions=(),
    )


def test_placement_materializer_emits_extractor_solo() -> None:
    genes, _ = generate_exhaustive_sample_genes(max_extensions=0, transport_kinds=("belt",))
    tpl = gene_template_from_generated_sample(genes[0])
    cand = _candidate_from_gene(gene_template=tpl)
    commit = IncrementalCommitResult(
        confirmed=(
            ConfirmedGenePlacement(
                candidate_id=cand.candidate_id,
                reservation=_reservation(cand),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        ),
        skipped_candidate_ids=(),
        goal_assigned_platforms={},
    )
    equipment = materialize_confirmed_placements(
        commit, {cand.candidate_id: cand}, gene_templates_by_id={tpl.gene_id: tpl}
    )
    assert isinstance(equipment, tuple)
    assert len(equipment) == 1
    assert equipment[0].cell_kind == "shape_miner"
    assert equipment[0].tile_type == "Layout_ShapeMiner"
    assert equipment[0].coord == cand.extractor


def test_placement_materializer_emits_extractor_and_extension() -> None:
    genes, _ = generate_exhaustive_sample_genes(max_extensions=1, transport_kinds=("belt",))
    with_ext = next(g for g in genes if g.extension_count == 1)
    tpl = gene_template_from_generated_sample(with_ext)
    cand = _candidate_from_gene(gene_template=tpl)
    commit = IncrementalCommitResult(
        confirmed=(
            ConfirmedGenePlacement(
                candidate_id=cand.candidate_id,
                reservation=_reservation(cand),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        ),
        skipped_candidate_ids=(),
        goal_assigned_platforms={},
    )
    equipment = materialize_confirmed_placements(
        commit, {cand.candidate_id: cand}, gene_templates_by_id={tpl.gene_id: tpl}
    )
    assert isinstance(equipment, tuple)
    kinds = {c.cell_kind for c in equipment}
    assert "shape_miner" in kinds
    assert "shape_miner_extension" in kinds
    assert len(equipment) == 1 + len(cand.extensions)


def test_merge_materialized_layout_includes_equipment_and_transport() -> None:
    genes, _ = generate_exhaustive_sample_genes(max_extensions=0, transport_kinds=("belt",))
    tpl = gene_template_from_generated_sample(genes[0])
    cand = _candidate_from_gene(gene_template=tpl)
    commit = IncrementalCommitResult(
        confirmed=(
            ConfirmedGenePlacement(
                candidate_id=cand.candidate_id,
                reservation=_reservation(cand),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        ),
        skipped_candidate_ids=(),
        goal_assigned_platforms={},
    )
    route = materialize_route_network(commit, {cand.candidate_id: cand})
    equipment = materialize_confirmed_placements(
        commit, {cand.candidate_id: cand}, gene_templates_by_id={tpl.gene_id: tpl}
    )
    merged = merge_materialized_layout(route, equipment)
    assert merged.failure_reason is None
    assert merged.layout is not None
    assert merged.layout.cells
    assert merged.layout.equipment_cells
    assert merged.layout.equipment_cells[0].cell_kind == "shape_miner"


def test_merge_rejects_equipment_on_transport_coord() -> None:
    genes, _ = generate_exhaustive_sample_genes(max_extensions=0, transport_kinds=("belt",))
    tpl = gene_template_from_generated_sample(genes[0])
    cand = _candidate_from_gene(gene_template=tpl)
    commit = IncrementalCommitResult(
        confirmed=(
            ConfirmedGenePlacement(
                candidate_id=cand.candidate_id,
                reservation=_reservation(cand),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        ),
        skipped_candidate_ids=(),
        goal_assigned_platforms={},
    )
    route = materialize_route_network(commit, {cand.candidate_id: cand})
    assert route.layout is not None
    equipment = materialize_confirmed_placements(
        commit, {cand.candidate_id: cand}, gene_templates_by_id={tpl.gene_id: tpl}
    )
    assert isinstance(equipment, tuple)
    overlap_coord = route.layout.cells[0].coord
    forced_overlap = tuple(equipment) + (
        type(equipment[0])(
            coord=overlap_coord,
            tile_type="Layout_ShapeMiner",
            cell_kind="shape_miner",
            rotation=0,
        ),
    )
    merged = merge_materialized_layout(route, forced_overlap)
    assert merged.layout is None
    assert merged.failure_reason is MaterializationFailureReason.EQUIPMENT_TRANSPORT_COORD_OVERLAP


def test_merge_success_keeps_disjoint_transport_and_equipment_coords() -> None:
    genes, _ = generate_exhaustive_sample_genes(max_extensions=1, transport_kinds=("belt",))
    with_ext = next(g for g in genes if g.extension_count == 1)
    tpl = gene_template_from_generated_sample(with_ext)
    cand = _candidate_from_gene(gene_template=tpl)
    commit = IncrementalCommitResult(
        confirmed=(
            ConfirmedGenePlacement(
                candidate_id=cand.candidate_id,
                reservation=_reservation(cand),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        ),
        skipped_candidate_ids=(),
        goal_assigned_platforms={},
    )
    route = materialize_route_network(commit, {cand.candidate_id: cand})
    equipment = materialize_confirmed_placements(
        commit, {cand.candidate_id: cand}, gene_templates_by_id={tpl.gene_id: tpl}
    )
    merged = merge_materialized_layout(route, equipment)
    assert merged.layout is not None
    transport_coords = {c.coord for c in merged.layout.cells}
    equipment_coords = {c.coord for c in merged.layout.equipment_cells}
    assert not transport_coords & equipment_coords
    assert len(merged.layout.cells) + len(merged.layout.equipment_cells) > 0


def test_extension_attachments_parent_first_orders_multi_extension_chain() -> None:
    genes, _ = generate_exhaustive_sample_genes(max_extensions=3, transport_kinds=("belt",))
    chain = next(
        g
        for g in genes
        if g.extension_count >= 2
        and any(
            n.kind == "extension" and n.parent_id not in (None, "E0")
            for n in g.nodes
        )
    )
    tpl = gene_template_from_generated_sample(chain)
    ordered = extension_attachments_parent_first(tpl.extension_attachments)
    child_to_parent = {e.child_offset: e.parent_offset for e in ordered}
    seen: set[tuple[int, int]] = set()
    for edge in ordered:
        if edge.parent_offset != (0, 0) and edge.parent_offset in child_to_parent:
            assert edge.parent_offset in seen
        seen.add(edge.child_offset)


def test_multi_extension_chain_preview_equipment() -> None:
    genes, _ = generate_exhaustive_sample_genes(max_extensions=3, transport_kinds=("belt",))
    chain = next(
        g
        for g in genes
        if g.extension_count >= 2
        and any(
            n.kind == "extension" and n.parent_id not in (None, "E0")
            for n in g.nodes
        )
    )
    tpl = gene_template_from_generated_sample(chain)
    cand = _candidate_from_gene(gene_template=tpl, anchor=(5, 10), rotation=Direction.N)
    equipment = preview_equipment_for_candidate(cand, gene=tpl)
    assert len(equipment) == 1 + len(cand.extensions)


@pytest.mark.parametrize(
    "rotation",
    (Direction.E, Direction.S, Direction.W, Direction.N),
)
def test_extension_rotation_ports_valid_for_cardinal_placements(
    rotation: Direction,
) -> None:
    genes, _ = generate_exhaustive_sample_genes(max_extensions=1, transport_kinds=("belt",))
    with_ext = next(g for g in genes if g.extension_count == 1)
    tpl = gene_template_from_generated_sample(with_ext)
    cand = _candidate_from_gene(gene_template=tpl, anchor=(12, 7), rotation=rotation)
    equipment = preview_equipment_for_candidate(cand, gene=tpl)
    by_coord = {c.coord: c for c in equipment}
    steps = steps_from_canonical_e(rotation)
    extractor = cand.extractor
    for edge in tpl.extension_attachments:
        parent = _translate(extractor, edge.parent_offset, steps)
        child = _translate(extractor, edge.child_offset, steps)
        if child not in cand.extensions:
            continue
        parent_cell = by_coord[parent]
        child_cell = by_coord[child]
        direction = _direction_child_to_parent_server(child, parent)
        assert direction is not None
        assert ports_compatible(
            child_cell.cell_kind,
            child_cell.rotation,
            parent_cell.cell_kind,
            parent_cell.rotation,
            direction,
        )
