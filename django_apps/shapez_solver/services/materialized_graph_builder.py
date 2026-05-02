from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_core.services.shape_render_scene import build_shape_render_scene
from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.domain.recipe import (
    OperationRecipe,
    RecipeRef,
    SolvedRecipe,
    SourceRecipe,
)
from django_apps.shapez_solver.dto.solver_graph import (
    SolverGraph,
    SolverGraphEdge,
    SolverGraphNode,
    SolverOperationNode,
    SolverShapeNode,
)
from django_apps.shapez_solver.services.operation_engine import OperationEngine
from django_apps.shapez_solver.services.planner_support import (
    is_empty_shape,
    paint_shape,
    single_quadrant_shapes,
    split_halves,
    uniform_non_empty_color,
)


@dataclass(slots=True)
class _ShapeCloneRecord:
    id: str
    output_key: str
    role: str
    shape_code: str
    label: str
    preview_scene: dict[str, object]
    produced_state: str
    batch_index: int
    batch_total: int


@dataclass(slots=True)
class _MaterializedState:
    recipe_by_id: dict[str, SourceRecipe | OperationRecipe]
    nodes: list[SolverGraphNode]
    edges: list[SolverGraphEdge]
    shape_records: dict[str, _ShapeCloneRecord]
    available_inventory: dict[str, list[str]]
    shape_clone_counts: dict[str, int]
    shape_batch_totals: dict[str, int]
    operation_run_counts: dict[str, int]
    operation_run_totals: dict[str, int]


@dataclass(frozen=True, slots=True)
class _HalfInventoryEntry:
    id: str
    shape: Shape


@dataclass(frozen=True, slots=True)
class _StructuredBatchStrategy:
    kind_usage: dict[str, str]


@dataclass(frozen=True, slots=True)
class MaterializedGraphBuilder:
    def build(
        self,
        solved: SolvedRecipe,
        *,
        target_count: int,
        base_demands: tuple[object, ...],
    ) -> SolverGraph | None:
        if not base_demands:
            return None
        if _supports_batch_materialization(solved.ref.shape):
            optimized = _build_half_batch_graph(
                solved.ref.shape,
                target_count=target_count,
                base_demands=base_demands,
            )
            if optimized is not None:
                return optimized
            return _build_single_layer_batch_graph(
                solved.ref.shape,
                target_count=target_count,
                base_demands=base_demands,
            )

        recipe_by_id = {recipe.id: recipe for recipe in solved.recipes}
        final_key = _ref_key(solved.ref)
        if isinstance(recipe_by_id.get(solved.ref.recipe_id), SourceRecipe):
            return _build_source_only_graph(
                solved.ref,
                target_count=target_count,
            )

        demand_counts = _compute_output_demands(solved, target_count=target_count)
        state = _build_state(
            solved,
            recipe_by_id=recipe_by_id,
            demand_counts=demand_counts,
            target_count=target_count,
            base_demands=base_demands,
            final_key=final_key,
        )

        for _ in range(target_count):
            target_clone_id = _allocate_output(
                state,
                solved.ref,
                for_target=True,
                final_key=final_key,
            )
            if target_clone_id is None:
                raise ValueError("Could not materialize target output from solver recipe.")

        _finalize_shape_nodes(state)
        _finalize_operation_nodes(state)
        return SolverGraph(nodes=tuple(state.nodes), edges=tuple(state.edges))


def _build_source_only_graph(ref: RecipeRef, *, target_count: int) -> SolverGraph:
    nodes: list[SolverGraphNode] = []
    for index in range(1, target_count + 1):
        nodes.append(
            SolverShapeNode(
                id=f"{ref.recipe_id}:shape:{ref.output_index}:materialized:{index}",
                role="target",
                shape_code=ref.shape.canonical_code,
                label=_target_label(target_count),
                preview_scene=_serialize_shape_preview(ref.shape),
                quantity=1,
                produced_state="target",
                batch_index=index,
                batch_total=target_count,
            )
        )
    return SolverGraph(nodes=tuple(nodes), edges=())


def _supports_batch_materialization(target_shape: Shape) -> bool:
    return target_shape.is_single_layer() and not target_shape.has_unsupported_materials()


def _build_half_batch_graph(
    target_shape: Shape,
    *,
    target_count: int,
    base_demands: tuple[object, ...],
) -> SolverGraph | None:
    engine = OperationEngine()
    target_color = uniform_non_empty_color(target_shape)
    skeleton = paint_shape(target_shape, "u") if target_color is not None else target_shape
    left_target, right_target = split_halves(skeleton)
    strategy = _analyze_structured_batch_strategy(left_target, right_target)
    if strategy is None:
        return None

    nodes: list[SolverGraphNode] = []
    edges: list[SolverGraphEdge] = []
    shape_records: dict[str, _ShapeCloneRecord] = {}
    half_pool: dict[str, list[_HalfInventoryEntry]] = defaultdict(list)
    quarter_pool: dict[str, list[str]] = defaultdict(list)
    op_counters: dict[str, int] = defaultdict(int)
    shape_counters: dict[str, int] = defaultdict(int)

    for demand in base_demands:
        base_shape_code = getattr(demand, "base_shape_code", None)
        full_source_count = getattr(demand, "full_source_count", None)
        if not isinstance(base_shape_code, str) or not isinstance(full_source_count, int):
            continue
        source_shape = shape_from_pattern(parse_shape_code_list(base_shape_code)[0])
        source_kind = source_shape.non_empty_parts()[0].kind
        usage = strategy.kind_usage.get(source_kind)
        if usage is None:
            continue
        for source_index in range(1, full_source_count + 1):
            source_node_id = _next_shape_id(shape_counters, f"{base_shape_code}:source")
            shape_records[source_node_id] = _ShapeCloneRecord(
                id=source_node_id,
                output_key=base_shape_code,
                role="source",
                shape_code=source_shape.canonical_code,
                label="Source",
                preview_scene=_serialize_shape_preview(source_shape),
                produced_state="consumed",
                batch_index=source_index,
                batch_total=full_source_count,
            )
            cut_op_id = _append_operation_node(
                nodes,
                op_counters,
                operation_type=OperationType.CUTTER,
                label="Cutter",
                description="Cuts the shape into two halves.",
            )
            edges.append(
                SolverGraphEdge(
                    from_id=source_node_id,
                    to_id=cut_op_id,
                    kind="input",
                    slot="Input A",
                    label="Input A",
                )
            )
            left_half, right_half = engine.cut(source_shape)
            if usage == "half":
                for output_index, half_shape in enumerate((left_half, right_half)):
                    half_id = _append_shape_record(
                        shape_records,
                        shape_counters,
                        key=f"{base_shape_code}:half",
                        shape=half_shape,
                        role="intermediate",
                        label="Shape",
                        produced_state="unused",
                    )
                    half_pool[half_shape.canonical_code].append(
                        _HalfInventoryEntry(id=half_id, shape=half_shape)
                    )
                    edges.append(
                        SolverGraphEdge(
                            from_id=cut_op_id,
                            to_id=half_id,
                            kind="output",
                            slot=_output_label(output_index),
                            label=_output_label(output_index),
                        )
                    )
            else:
                _seed_quarter_inventory(
                    nodes,
                    edges,
                    shape_records,
                    shape_counters,
                    op_counters,
                    quarter_pool,
                    base_shape_code=base_shape_code,
                    cut_op_id=cut_op_id,
                    left_half=left_half,
                    right_half=right_half,
                    engine=engine,
                )

    for target_index in range(1, target_count + 1):
        left_acquired = _materialize_structured_half(
            left_target,
            half_pool=half_pool,
            quarter_pool=quarter_pool,
            shape_records=shape_records,
            shape_counters=shape_counters,
            nodes=nodes,
            edges=edges,
            op_counters=op_counters,
            engine=engine,
        )
        right_acquired = _materialize_structured_half(
            right_target,
            half_pool=half_pool,
            quarter_pool=quarter_pool,
            shape_records=shape_records,
            shape_counters=shape_counters,
            nodes=nodes,
            edges=edges,
            op_counters=op_counters,
            engine=engine,
        )
        current_shape_id: str
        current_shape: Shape
        if right_acquired is None:
            if left_acquired is None:
                return None
            current_shape_id, current_shape = left_acquired
        elif left_acquired is None:
            current_shape_id, current_shape = right_acquired
        else:
            left_id, left_shape = left_acquired
            right_id, right_shape = right_acquired
            swapper_id = _append_operation_node(
                nodes,
                op_counters,
                operation_type=OperationType.SWAPPER,
                label="Swapper",
                description="Swap left and right halves into a target layer.",
            )
            edges.extend(
                [
                    SolverGraphEdge(
                        from_id=left_id,
                        to_id=swapper_id,
                        kind="input",
                        slot="Input A",
                        label="Input A",
                    ),
                    SolverGraphEdge(
                        from_id=right_id,
                        to_id=swapper_id,
                        kind="input",
                        slot="Input B",
                        label="Input B",
                    ),
                ]
            )
            output_a, output_b = engine.swapper(left_shape, right_shape)
            current_shape_id = _append_shape_record(
                shape_records,
                shape_counters,
                key="materialized:swapper-output",
                shape=output_a,
                role="intermediate",
                label="Shape",
                produced_state="consumed",
            )
            current_shape = output_a
            edges.append(
                SolverGraphEdge(
                    from_id=swapper_id,
                    to_id=current_shape_id,
                    kind="output",
                    slot="Output A",
                    label="Output A",
                )
            )
            if output_b.non_empty_parts():
                unused_output_id = _append_shape_record(
                    shape_records,
                    shape_counters,
                    key="materialized:swapper-unused",
                    shape=output_b,
                    role="intermediate",
                    label="Shape",
                    produced_state="unused",
                )
                edges.append(
                    SolverGraphEdge(
                        from_id=swapper_id,
                        to_id=unused_output_id,
                        kind="output",
                        slot="Output B",
                        label="Output B",
                    )
                )

        if target_color is not None:
            painter_id = _append_operation_node(
                nodes,
                op_counters,
                operation_type=OperationType.PAINTER,
                label=f"Painter ({target_color})",
                description=f"Paint the shape {target_color}.",
            )
            edges.append(
                SolverGraphEdge(
                    from_id=current_shape_id,
                    to_id=painter_id,
                    kind="input",
                    slot="Input A",
                    label="Input A",
                )
            )
            painted_shape = engine.painter(current_shape, target_color)
            target_shape_id = _append_shape_record(
                shape_records,
                shape_counters,
                key="materialized:painted-target",
                shape=painted_shape,
                role="target",
                label=_target_label(target_count),
                produced_state="target",
                batch_index=target_index,
                batch_total=target_count,
            )
            edges.append(
                SolverGraphEdge(
                    from_id=painter_id,
                    to_id=target_shape_id,
                    kind="output",
                    slot="Output A",
                    label="Output A",
                )
            )
        else:
            target_record = shape_records[current_shape_id]
            target_record.role = "target"
            target_record.label = _target_label(target_count)
            target_record.produced_state = "target"
            target_record.batch_index = target_index
            target_record.batch_total = target_count

    for record in shape_records.values():
        nodes.append(
            SolverShapeNode(
                id=record.id,
                role=record.role,  # type: ignore[arg-type]
                shape_code=record.shape_code,
                label=record.label,
                preview_scene=record.preview_scene,
                quantity=1,
                produced_state=record.produced_state,  # type: ignore[arg-type]
                batch_index=record.batch_index,
                batch_total=record.batch_total,
            )
        )
    return SolverGraph(nodes=tuple(nodes), edges=tuple(edges))


def _analyze_structured_batch_strategy(
    left_target: Shape,
    right_target: Shape,
) -> _StructuredBatchStrategy | None:
    kind_usage: dict[str, str] = {}
    for half_target in (left_target, right_target):
        if is_empty_shape(half_target):
            continue
        if _is_direct_source_half(half_target):
            kind = half_target.non_empty_parts()[0].kind
            if kind_usage.get(kind) == "quarter":
                return None
            kind_usage[kind] = "half"
            continue
        for quadrant_shape in single_quadrant_shapes(half_target):
            kind = quadrant_shape.non_empty_parts()[0].kind
            if kind_usage.get(kind) == "half":
                return None
            kind_usage[kind] = "quarter"
    return _StructuredBatchStrategy(kind_usage=kind_usage)


def _seed_quarter_inventory(
    nodes: list[SolverGraphNode],
    edges: list[SolverGraphEdge],
    shape_records: dict[str, _ShapeCloneRecord],
    shape_counters: dict[str, int],
    op_counters: dict[str, int],
    quarter_pool: dict[str, list[str]],
    *,
    base_shape_code: str,
    cut_op_id: str,
    left_half: Shape,
    right_half: Shape,
    engine: OperationEngine,
) -> None:
    left_half_id = _append_shape_record(
        shape_records,
        shape_counters,
        key=f"{base_shape_code}:left-half",
        shape=left_half,
        role="intermediate",
        label="Shape",
        produced_state="consumed",
    )
    right_half_id = _append_shape_record(
        shape_records,
        shape_counters,
        key=f"{base_shape_code}:right-half",
        shape=right_half,
        role="intermediate",
        label="Shape",
        produced_state="consumed",
    )
    edges.extend(
        [
            SolverGraphEdge(
                from_id=cut_op_id,
                to_id=left_half_id,
                kind="output",
                slot="Output A",
                label="Output A",
            ),
            SolverGraphEdge(
                from_id=cut_op_id,
                to_id=right_half_id,
                kind="output",
                slot="Output B",
                label="Output B",
            ),
        ]
    )
    for half_id, half_shape, rotation_type in (
        (left_half_id, left_half, OperationType.ROTATE_CCW),
        (right_half_id, right_half, OperationType.ROTATE_CCW),
    ):
        _, rotated_half_id = _append_unary_operation_output(
            nodes,
            edges,
            shape_records,
            shape_counters,
            op_counters,
            source_id=half_id,
            source_shape=half_shape,
            result_shape=_rotate_shape(half_shape, rotation_type, engine),
            operation_type=rotation_type,
            key=f"{base_shape_code}:{rotation_type.value}:half",
            role="intermediate",
            label="Shape",
            produced_state="consumed",
        )
        rotated_half = shape_from_pattern(
            parse_shape_code_list(shape_records[rotated_half_id].shape_code)[0]
        )
        half_cut_op_id = _append_operation_node(
            nodes,
            op_counters,
            operation_type=OperationType.CUTTER,
            label="Cutter",
            description="Cuts the shape into two halves.",
        )
        edges.append(
            SolverGraphEdge(
                from_id=rotated_half_id,
                to_id=half_cut_op_id,
                kind="input",
                slot="Input A",
                label="Input A",
            )
        )
        quarter_a, quarter_b = engine.cut(rotated_half)
        for output_index, quarter_shape in enumerate((quarter_a, quarter_b)):
            if not quarter_shape.non_empty_parts():
                continue
            quarter_id = _append_shape_record(
                shape_records,
                shape_counters,
                key=f"{base_shape_code}:quarter",
                shape=quarter_shape,
                role="intermediate",
                label="Shape",
                produced_state="unused",
            )
            quarter_pool[base_shape_code].append(quarter_id)
            edges.append(
                SolverGraphEdge(
                    from_id=half_cut_op_id,
                    to_id=quarter_id,
                    kind="output",
                    slot=_output_label(output_index),
                    label=_output_label(output_index),
                )
            )


def _materialize_structured_half(
    target_shape: Shape,
    *,
    half_pool: dict[str, list[_HalfInventoryEntry]],
    quarter_pool: dict[str, list[str]],
    shape_records: dict[str, _ShapeCloneRecord],
    shape_counters: dict[str, int],
    nodes: list[SolverGraphNode],
    edges: list[SolverGraphEdge],
    op_counters: dict[str, int],
    engine: OperationEngine,
) -> tuple[str, Shape] | None:
    if is_empty_shape(target_shape):
        return None
    if _is_direct_source_half(target_shape):
        return _acquire_half(
            half_pool,
            target_shape=target_shape,
            shape_records=shape_records,
            shape_counters=shape_counters,
            nodes=nodes,
            edges=edges,
            op_counters=op_counters,
            engine=engine,
        )
    quadrant_targets = single_quadrant_shapes(target_shape)
    current_shape_id: str | None = None
    current_shape: Shape | None = None
    for quadrant_shape in quadrant_targets:
        acquired = _acquire_quadrant(
            quarter_pool,
            target_shape=quadrant_shape,
            shape_records=shape_records,
            shape_counters=shape_counters,
            nodes=nodes,
            edges=edges,
            op_counters=op_counters,
            engine=engine,
        )
        if acquired is None:
            return None
        quadrant_id, aligned_quadrant_shape = acquired
        if current_shape_id is None:
            current_shape_id = quadrant_id
            current_shape = aligned_quadrant_shape
            continue
        assert current_shape is not None
        merged_shape = engine.stacker(current_shape, aligned_quadrant_shape)
        stacker_id = _append_operation_node(
            nodes,
            op_counters,
            operation_type=OperationType.STACKER,
            label="Stacker",
            description="Merge disjoint quadrants within a target half.",
        )
        edges.extend(
            [
                SolverGraphEdge(
                    from_id=current_shape_id,
                    to_id=stacker_id,
                    kind="input",
                    slot="Input A",
                    label="Input A",
                ),
                SolverGraphEdge(
                    from_id=quadrant_id,
                    to_id=stacker_id,
                    kind="input",
                    slot="Input B",
                    label="Input B",
                ),
            ]
        )
        current_shape_id = _append_shape_record(
            shape_records,
            shape_counters,
            key="materialized:half-stacked",
            shape=merged_shape,
            role="intermediate",
            label="Shape",
            produced_state="consumed",
        )
        current_shape = merged_shape
        edges.append(
            SolverGraphEdge(
                from_id=stacker_id,
                to_id=current_shape_id,
                kind="output",
                slot="Output A",
                label="Output A",
            )
        )
    if current_shape_id is None or current_shape is None:
        return None
    return current_shape_id, current_shape


def _acquire_quadrant(
    quarter_pool: dict[str, list[str]],
    *,
    target_shape: Shape,
    shape_records: dict[str, _ShapeCloneRecord],
    shape_counters: dict[str, int],
    nodes: list[SolverGraphNode],
    edges: list[SolverGraphEdge],
    op_counters: dict[str, int],
    engine: OperationEngine,
) -> tuple[str, Shape] | None:
    source_code = _full_source_code_for_shape(target_shape)
    available = quarter_pool.get(source_code)
    if not available:
        return None
    quarter_id = available.pop(0)
    quarter_record = shape_records[quarter_id]
    quarter_shape = shape_from_pattern(parse_shape_code_list(quarter_record.shape_code)[0])
    quarter_record.produced_state = "consumed"
    return _align_quadrant_shape(
        nodes,
        edges,
        shape_records,
        shape_counters,
        op_counters,
        source_id=quarter_id,
        source_shape=quarter_shape,
        target_shape=target_shape,
        engine=engine,
    )


def _is_direct_source_half(shape: Shape) -> bool:
    parts = shape.non_empty_parts()
    return bool(parts) and len(parts) == 2 and len({part.kind for part in parts}) == 1


def _acquire_half(
    half_pool: dict[str, list[_HalfInventoryEntry]],
    *,
    target_shape: Shape,
    shape_records: dict[str, _ShapeCloneRecord],
    shape_counters: dict[str, int],
    nodes: list[SolverGraphNode],
    edges: list[SolverGraphEdge],
    op_counters: dict[str, int],
    engine: OperationEngine,
) -> tuple[str, Shape] | None:
    exact = half_pool.get(target_shape.canonical_code)
    if exact:
        acquired = exact.pop(0)
        shape_records[acquired.id].produced_state = "consumed"
        return acquired.id, acquired.shape

    rotated_target = engine.rotate_180(target_shape)
    rotated_pool = half_pool.get(rotated_target.canonical_code)
    if not rotated_pool:
        return None
    source_entry = rotated_pool.pop(0)
    shape_records[source_entry.id].produced_state = "consumed"
    _, rotated_id = _append_unary_operation_output(
        nodes,
        edges,
        shape_records,
        shape_counters,
        op_counters,
        source_id=source_entry.id,
        source_shape=source_entry.shape,
        result_shape=target_shape,
        operation_type=OperationType.ROTATE_180,
        key="materialized:rotate-half",
        role="intermediate",
        label="Shape",
        produced_state="consumed",
    )
    return rotated_id, target_shape


def _build_single_layer_batch_graph(
    target_shape: Shape,
    *,
    target_count: int,
    base_demands: tuple[object, ...],
) -> SolverGraph:
    engine = OperationEngine()
    nodes: list[SolverGraphNode] = []
    edges: list[SolverGraphEdge] = []
    shape_records: dict[str, _ShapeCloneRecord] = {}
    quarter_pool: dict[str, list[str]] = defaultdict(list)
    op_counters: dict[str, int] = defaultdict(int)
    shape_counters: dict[str, int] = defaultdict(int)
    target_color = uniform_non_empty_color(target_shape)
    skeleton = paint_shape(target_shape, "u") if target_color is not None else target_shape

    for demand in base_demands:
        base_shape_code = getattr(demand, "base_shape_code", None)
        full_source_count = getattr(demand, "full_source_count", None)
        if not isinstance(base_shape_code, str) or not isinstance(full_source_count, int):
            continue
        source_shape = shape_from_pattern(parse_shape_code_list(base_shape_code)[0])
        for source_index in range(1, full_source_count + 1):
            source_node_id = _next_shape_id(shape_counters, f"{base_shape_code}:source")
            shape_records[source_node_id] = _ShapeCloneRecord(
                id=source_node_id,
                output_key=base_shape_code,
                role="source",
                shape_code=source_shape.canonical_code,
                label="Source",
                preview_scene=_serialize_shape_preview(source_shape),
                produced_state="consumed",
                batch_index=source_index,
                batch_total=full_source_count,
            )

            full_cut_op_id = _append_operation_node(
                nodes,
                op_counters,
                operation_type=OperationType.CUTTER,
                label="Cutter",
                description="Cuts the shape into two halves.",
            )
            edges.append(
                SolverGraphEdge(
                    from_id=source_node_id,
                    to_id=full_cut_op_id,
                    kind="input",
                    slot="Input A",
                    label="Input A",
                )
            )
            left_half, right_half = engine.cut(source_shape)
            left_half_id = _append_shape_record(
                shape_records,
                shape_counters,
                key=f"{base_shape_code}:left-half",
                shape=left_half,
                role="intermediate",
                label="Shape",
                produced_state="consumed",
            )
            right_half_id = _append_shape_record(
                shape_records,
                shape_counters,
                key=f"{base_shape_code}:right-half",
                shape=right_half,
                role="intermediate",
                label="Shape",
                produced_state="consumed",
            )
            edges.extend(
                [
                    SolverGraphEdge(
                        from_id=full_cut_op_id,
                        to_id=left_half_id,
                        kind="output",
                        slot="Output A",
                        label="Output A",
                    ),
                    SolverGraphEdge(
                        from_id=full_cut_op_id,
                        to_id=right_half_id,
                        kind="output",
                        slot="Output B",
                        label="Output B",
                    ),
                ]
            )

            for half_id, half_shape, rotation_type in (
                (left_half_id, left_half, OperationType.ROTATE_CCW),
                (right_half_id, right_half, OperationType.ROTATE_CCW),
            ):
                _, rotated_half_id = _append_unary_operation_output(
                    nodes,
                    edges,
                    shape_records,
                    shape_counters,
                    op_counters,
                    source_id=half_id,
                    source_shape=half_shape,
                    result_shape=_rotate_shape(half_shape, rotation_type, engine),
                    operation_type=rotation_type,
                    key=f"{base_shape_code}:{rotation_type.value}:half",
                    role="intermediate",
                    label="Shape",
                    produced_state="consumed",
                )
                rotated_half = shape_from_pattern(
                    parse_shape_code_list(shape_records[rotated_half_id].shape_code)[0]
                )
                half_cut_op_id = _append_operation_node(
                    nodes,
                    op_counters,
                    operation_type=OperationType.CUTTER,
                    label="Cutter",
                    description="Cuts the shape into two halves.",
                )
                edges.append(
                    SolverGraphEdge(
                        from_id=rotated_half_id,
                        to_id=half_cut_op_id,
                        kind="input",
                        slot="Input A",
                        label="Input A",
                    )
                )
                quarter_a, quarter_b = engine.cut(rotated_half)
                for output_index, quarter_shape in enumerate((quarter_a, quarter_b)):
                    if not quarter_shape.non_empty_parts():
                        continue
                    quarter_id = _append_shape_record(
                        shape_records,
                        shape_counters,
                        key=f"{base_shape_code}:quarter",
                        shape=quarter_shape,
                        role="intermediate",
                        label="Shape",
                        produced_state="unused",
                    )
                    quarter_pool[base_shape_code].append(quarter_id)
                    edges.append(
                        SolverGraphEdge(
                            from_id=half_cut_op_id,
                            to_id=quarter_id,
                            kind="output",
                            slot=_output_label(output_index),
                            label=_output_label(output_index),
                        )
                    )

    quadrant_targets = single_quadrant_shapes(skeleton)
    for target_index in range(1, target_count + 1):
        current_shape_id: str | None = None
        current_shape: Shape | None = None
        for quadrant_shape in quadrant_targets:
            source_code = _full_source_code_for_shape(quadrant_shape)
            quarter_id = quarter_pool[source_code].pop(0)
            quarter_record = shape_records[quarter_id]
            quarter_shape = shape_from_pattern(parse_shape_code_list(quarter_record.shape_code)[0])
            quarter_record.produced_state = "consumed"
            aligned_quarter_id, aligned_quarter_shape = _align_quadrant_shape(
                nodes,
                edges,
                shape_records,
                shape_counters,
                op_counters,
                source_id=quarter_id,
                source_shape=quarter_shape,
                target_shape=quadrant_shape,
                engine=engine,
            )
            if current_shape_id is None:
                current_shape_id = aligned_quarter_id
                current_shape = aligned_quarter_shape
                continue
            assert current_shape is not None
            merged_shape = engine.stacker(current_shape, aligned_quarter_shape)
            stacker_id = _append_operation_node(
                nodes,
                op_counters,
                operation_type=OperationType.STACKER,
                label="Stacker",
                description="Merge disjoint quadrants into a buildable layer.",
            )
            edges.extend(
                [
                    SolverGraphEdge(
                        from_id=current_shape_id,
                        to_id=stacker_id,
                        kind="input",
                        slot="Input A",
                        label="Input A",
                    ),
                    SolverGraphEdge(
                        from_id=aligned_quarter_id,
                        to_id=stacker_id,
                        kind="input",
                        slot="Input B",
                        label="Input B",
                    ),
                ]
            )
            current_shape_id = _append_shape_record(
                shape_records,
                shape_counters,
                key="materialized:stacked",
                shape=merged_shape,
                role="intermediate",
                label="Shape",
                produced_state="consumed",
            )
            current_shape = merged_shape
            edges.append(
                SolverGraphEdge(
                    from_id=stacker_id,
                    to_id=current_shape_id,
                    kind="output",
                    slot="Output A",
                    label="Output A",
                )
            )

        if current_shape_id is None or current_shape is None:
            continue

        target_shape_id = current_shape_id
        if target_color is not None:
            painter_id = _append_operation_node(
                nodes,
                op_counters,
                operation_type=OperationType.PAINTER,
                label=f"Painter ({target_color})",
                description=f"Paint the shape {target_color}.",
            )
            edges.append(
                SolverGraphEdge(
                    from_id=current_shape_id,
                    to_id=painter_id,
                    kind="input",
                    slot="Input A",
                    label="Input A",
                )
            )
            painted_shape = engine.painter(current_shape, target_color)
            target_shape_id = _append_shape_record(
                shape_records,
                shape_counters,
                key="materialized:painted-target",
                shape=painted_shape,
                role="target",
                label=_target_label(target_count),
                produced_state="target",
                batch_index=target_index,
                batch_total=target_count,
            )
            edges.append(
                SolverGraphEdge(
                    from_id=painter_id,
                    to_id=target_shape_id,
                    kind="output",
                    slot="Output A",
                    label="Output A",
                )
            )
        else:
            target_record = shape_records[target_shape_id]
            target_record.role = "target"
            target_record.label = _target_label(target_count)
            target_record.produced_state = "target"
            target_record.batch_index = target_index
            target_record.batch_total = target_count

    for record in shape_records.values():
        nodes.append(
            SolverShapeNode(
                id=record.id,
                role=record.role,  # type: ignore[arg-type]
                shape_code=record.shape_code,
                label=record.label,
                preview_scene=record.preview_scene,
                quantity=1,
                produced_state=record.produced_state,  # type: ignore[arg-type]
                batch_index=record.batch_index,
                batch_total=record.batch_total,
            )
        )
    return SolverGraph(nodes=tuple(nodes), edges=tuple(edges))


def _build_state(
    solved: SolvedRecipe,
    *,
    recipe_by_id: dict[str, SourceRecipe | OperationRecipe],
    demand_counts: dict[str, int],
    target_count: int,
    base_demands: tuple[object, ...],
    final_key: str,
) -> _MaterializedState:
    nodes: list[SolverGraphNode] = []
    edges: list[SolverGraphEdge] = []
    shape_records: dict[str, _ShapeCloneRecord] = {}
    available_inventory = defaultdict(list)
    shape_clone_counts = defaultdict(int)
    shape_batch_totals = defaultdict(int)
    operation_run_counts: dict[str, int] = defaultdict(int)
    operation_run_totals: dict[str, int] = defaultdict(int)

    source_total_by_code = _base_quantity_map(base_demands)
    for recipe in solved.recipes:
        if not isinstance(recipe, SourceRecipe):
            continue
        output_key = f"{recipe.id}:0"
        if output_key == final_key:
            continue
        total = source_total_by_code.get(recipe.shape.canonical_code, 0)
        if total <= 0:
            continue
        shape_batch_totals[output_key] = total
        for batch_index in range(1, total + 1):
            clone_id = f"{output_key}:materialized:{batch_index}"
            shape_records[clone_id] = _ShapeCloneRecord(
                id=clone_id,
                output_key=output_key,
                role="source",
                shape_code=recipe.shape.canonical_code,
                label=recipe.label,
                preview_scene=_serialize_shape_preview(recipe.shape),
                produced_state="unused",
                batch_index=batch_index,
                batch_total=total,
            )
            available_inventory[output_key].append(clone_id)
            shape_clone_counts[output_key] = batch_index

    for recipe in solved.recipes:
        if not isinstance(recipe, OperationRecipe):
            continue
        if recipe.id == solved.ref.recipe_id:
            operation_run_totals[recipe.id] = demand_counts.get(_ref_key(solved.ref), 0)
        else:
            operation_run_totals[recipe.id] = max(
                demand_counts.get(f"{recipe.id}:{output_index}", 0)
                for output_index in range(len(recipe.outputs))
            )
        for output_index in range(len(recipe.outputs)):
            output_key = f"{recipe.id}:{output_index}"
            shape_batch_totals[output_key] = demand_counts.get(output_key, 0)

    if shape_batch_totals.get(final_key, 0) < target_count:
        shape_batch_totals[final_key] = target_count

    return _MaterializedState(
        recipe_by_id=recipe_by_id,
        nodes=nodes,
        edges=edges,
        shape_records=shape_records,
        available_inventory=available_inventory,
        shape_clone_counts=shape_clone_counts,
        shape_batch_totals=shape_batch_totals,
        operation_run_counts=operation_run_counts,
        operation_run_totals=operation_run_totals,
    )


def _append_operation_node(
    nodes: list[SolverGraphNode],
    op_counters: dict[str, int],
    *,
    operation_type: OperationType,
    label: str,
    description: str,
) -> str:
    op_key = operation_type.value
    op_counters[op_key] += 1
    catalog = OPERATION_CATALOG[operation_type]
    node_id = f"materialized:{op_key}:run:{op_counters[op_key]}"
    nodes.append(
        SolverOperationNode(
            id=node_id,
            operation_type=operation_type.value,
            label=label,
            icon=catalog.icon,
            input_count=catalog.input_count,
            output_count=catalog.output_count,
            description=description,
            run_index=op_counters[op_key],
        )
    )
    return node_id


def _append_shape_record(
    shape_records: dict[str, _ShapeCloneRecord],
    shape_counters: dict[str, int],
    *,
    key: str,
    shape: Shape,
    role: str,
    label: str,
    produced_state: str,
    batch_index: int | None = None,
    batch_total: int | None = None,
) -> str:
    shape_counters[key] += 1
    batch_value = batch_index if batch_index is not None else shape_counters[key]
    total_value = batch_total if batch_total is not None else shape_counters[key]
    node_id = f"{key}:item:{shape_counters[key]}"
    shape_records[node_id] = _ShapeCloneRecord(
        id=node_id,
        output_key=key,
        role=role,
        shape_code=shape.canonical_code,
        label=label,
        preview_scene=_serialize_shape_preview(shape),
        produced_state=produced_state,
        batch_index=batch_value,
        batch_total=total_value,
    )
    return node_id


def _next_shape_id(shape_counters: dict[str, int], key: str) -> str:
    shape_counters[key] += 1
    return f"{key}:item:{shape_counters[key]}"


def _align_quadrant_shape(
    nodes: list[SolverGraphNode],
    edges: list[SolverGraphEdge],
    shape_records: dict[str, _ShapeCloneRecord],
    shape_counters: dict[str, int],
    op_counters: dict[str, int],
    *,
    source_id: str,
    source_shape: Shape,
    target_shape: Shape,
    engine: OperationEngine,
) -> tuple[str, Shape]:
    if source_shape == target_shape:
        return source_id, source_shape

    for operation_type in (
        OperationType.ROTATE_CW,
        OperationType.ROTATE_CCW,
        OperationType.ROTATE_180,
    ):
        rotated_shape = _rotate_shape(source_shape, operation_type, engine)
        if rotated_shape != target_shape:
            continue
        _, output_id = _append_unary_operation_output(
            nodes,
            edges,
            shape_records,
            shape_counters,
            op_counters,
            source_id=source_id,
            source_shape=source_shape,
            result_shape=rotated_shape,
            operation_type=operation_type,
            key=f"materialized:{operation_type.value}:output",
            role="intermediate",
            label="Shape",
            produced_state="consumed",
        )
        return output_id, rotated_shape
    raise ValueError(
        f"Could not align {source_shape.canonical_code} to {target_shape.canonical_code}."
    )


def _append_unary_operation_output(
    nodes: list[SolverGraphNode],
    edges: list[SolverGraphEdge],
    shape_records: dict[str, _ShapeCloneRecord],
    shape_counters: dict[str, int],
    op_counters: dict[str, int],
    *,
    source_id: str,
    source_shape: Shape,
    result_shape: Shape,
    operation_type: OperationType,
    key: str,
    role: str,
    label: str,
    produced_state: str,
) -> tuple[str, str]:
    operation_id = _append_operation_node(
        nodes,
        op_counters,
        operation_type=operation_type,
        label=OPERATION_CATALOG[operation_type].label,
        description=OPERATION_CATALOG[operation_type].description,
    )
    edges.append(
        SolverGraphEdge(
            from_id=source_id,
            to_id=operation_id,
            kind="input",
            slot="Input A",
            label="Input A",
        )
    )
    output_id = _append_shape_record(
        shape_records,
        shape_counters,
        key=key,
        shape=result_shape,
        role=role,
        label=label,
        produced_state=produced_state,
    )
    edges.append(
        SolverGraphEdge(
            from_id=operation_id,
            to_id=output_id,
            kind="output",
            slot="Output A",
            label="Output A",
        )
    )
    return operation_id, output_id


def _rotate_shape(shape: Shape, operation_type: OperationType, engine: OperationEngine) -> Shape:
    if operation_type == OperationType.ROTATE_CW:
        return engine.rotate_cw(shape)
    if operation_type == OperationType.ROTATE_CCW:
        return engine.rotate_ccw(shape)
    if operation_type == OperationType.ROTATE_180:
        return engine.rotate_180(shape)
    raise ValueError(f"Unsupported rotation type: {operation_type}")


def _full_source_code_for_shape(shape: Shape) -> str:
    part = shape.non_empty_parts()[0]
    return f"{part.kind}u" * 4


def _compute_output_demands(solved: SolvedRecipe, *, target_count: int) -> dict[str, int]:
    demand_counts: dict[str, int] = defaultdict(int)
    demand_counts[_ref_key(solved.ref)] = target_count

    for recipe in reversed(solved.recipes):
        if not isinstance(recipe, OperationRecipe):
            continue
        run_count = max(
            demand_counts.get(f"{recipe.id}:{index}", 0) for index in range(len(recipe.outputs))
        )
        if run_count <= 0:
            continue
        for recipe_input in recipe.inputs:
            key = _ref_key(recipe_input)
            demand_counts[key] += run_count
    return dict(demand_counts)


def _allocate_output(
    state: _MaterializedState,
    ref: RecipeRef,
    *,
    for_target: bool,
    final_key: str,
) -> str | None:
    key = _ref_key(ref)
    available = state.available_inventory.get(key)
    if available:
        clone_id = available.pop(0)
        record = state.shape_records[clone_id]
        if for_target:
            record.role = "target"
            record.label = _target_label(state.shape_batch_totals.get(final_key, 1))
            record.produced_state = "target"
        else:
            record.produced_state = "consumed"
        return clone_id

    owner = state.recipe_by_id.get(ref.recipe_id)
    if owner is None:
        return None
    if isinstance(owner, SourceRecipe):
        return None

    _materialize_operation_run(
        state,
        owner,
        final_key=final_key,
    )
    available = state.available_inventory.get(key)
    if not available:
        return None
    return _allocate_output(state, ref, for_target=for_target, final_key=final_key)


def _materialize_operation_run(
    state: _MaterializedState,
    recipe: OperationRecipe,
    *,
    final_key: str,
) -> None:
    state.operation_run_counts[recipe.id] += 1
    run_index = state.operation_run_counts[recipe.id]
    run_total = max(state.operation_run_totals.get(recipe.id, 0), run_index)
    operation = OPERATION_CATALOG[recipe.operation_type]
    operation_id = f"{recipe.id}:run:{run_index}"

    for recipe_input in recipe.inputs:
        input_clone_id = _allocate_output(
            state,
            recipe_input,
            for_target=False,
            final_key=final_key,
        )
        if input_clone_id is None:
            raise ValueError(f"Could not allocate input {recipe_input} for {recipe.id}.")
        input_slot = _slot_label(len([edge for edge in state.edges if edge.to_id == operation_id]))
        state.edges.append(
            SolverGraphEdge(
                from_id=input_clone_id,
                to_id=operation_id,
                kind="input",
                slot=input_slot,
                label=input_slot,
            )
        )

    state.nodes.append(
        SolverOperationNode(
            id=operation_id,
            operation_type=recipe.operation_type.value,
            label=recipe.label,
            icon=operation.icon,
            input_count=operation.input_count,
            output_count=operation.output_count,
            description=recipe.description,
            run_index=run_index,
            run_total=run_total,
        )
    )

    for output_index, output_shape in enumerate(recipe.outputs):
        output_key = f"{recipe.id}:{output_index}"
        state.shape_clone_counts[output_key] += 1
        batch_index = state.shape_clone_counts[output_key]
        batch_total = max(state.shape_batch_totals.get(output_key, 0), batch_index)
        clone_id = f"{output_key}:materialized:{batch_index}"
        state.shape_records[clone_id] = _ShapeCloneRecord(
            id=clone_id,
            output_key=output_key,
            role="target" if output_key == final_key else "intermediate",
            shape_code=output_shape.canonical_code,
            label=(
                _target_label(state.shape_batch_totals.get(final_key, 1))
                if output_key == final_key
                else "Shape"
            ),
            preview_scene=_serialize_shape_preview(output_shape),
            produced_state="target" if output_key == final_key else "unused",
            batch_index=batch_index,
            batch_total=batch_total,
        )
        state.available_inventory[output_key].append(clone_id)
        state.edges.append(
            SolverGraphEdge(
                from_id=operation_id,
                to_id=clone_id,
                kind="output",
                slot=_output_label(output_index),
                label=_output_label(output_index),
            )
        )


def _finalize_shape_nodes(state: _MaterializedState) -> None:
    for record in state.shape_records.values():
        state.nodes.append(
            SolverShapeNode(
                id=record.id,
                role=record.role,  # type: ignore[arg-type]
                shape_code=record.shape_code,
                label=record.label,
                preview_scene=record.preview_scene,
                quantity=1,
                produced_state=record.produced_state,  # type: ignore[arg-type]
                batch_index=record.batch_index,
                batch_total=record.batch_total,
            )
        )


def _finalize_operation_nodes(state: _MaterializedState) -> None:
    return None


def _base_quantity_map(base_demands: tuple[object, ...]) -> dict[str, int]:
    out: dict[str, int] = {}
    for demand in base_demands:
        code = getattr(demand, "base_shape_code", None)
        count = getattr(demand, "full_source_count", None)
        if isinstance(code, str) and isinstance(count, int) and count >= 1:
            out[code] = count
    return out


def _serialize_shape_preview(shape: Shape) -> dict[str, object]:
    scene = build_shape_render_scene(shape)
    return {
        "normalized_code": scene.normalized_code,
        "cells": [
            {
                "layer_index": cell.layer_index,
                "quadrant_index": cell.quadrant_index,
                "position": cell.position.value,
                "shape_code": cell.shape_code,
                "color_code": cell.color_code,
                "shape_kind": cell.shape_kind,
                "color_kind": cell.color_kind,
                "mesh_key": cell.mesh_key,
                "material_key": cell.material_key,
                "transform_key": cell.transform_key,
            }
            for cell in scene.cells
        ],
    }


def _ref_key(ref: RecipeRef) -> str:
    return f"{ref.recipe_id}:{ref.output_index}"


def _slot_label(index: int) -> str:
    return f"Input {chr(ord('A') + index)}"


def _output_label(index: int) -> str:
    return f"Output {chr(ord('A') + index)}"


def _target_label(target_count: int) -> str:
    return f"Target x{target_count}" if target_count > 1 else "Target"
