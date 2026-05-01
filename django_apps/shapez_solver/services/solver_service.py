from dataclasses import dataclass

from django_apps.shapez_core.domain.shape_pattern import NormalizedShapePattern
from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.dto.solver_graph import (
    ShapeNodeRole,
    SolverGraph,
    SolverGraphEdge,
    SolverOperationNode,
    SolverShapeNode,
)


@dataclass(frozen=True, slots=True)
class SolverRequest:
    target_pattern: NormalizedShapePattern
    max_depth: int = 12


@dataclass(frozen=True, slots=True)
class ShapeRef:
    shape_code: str
    label: str | None = None


@dataclass(frozen=True, slots=True)
class SolveStep:
    id: str
    index: int
    operation_type: OperationType
    title: str
    description: str
    inputs: tuple[ShapeRef, ...]
    outputs: tuple[ShapeRef, ...]


@dataclass(frozen=True, slots=True)
class SolverResult:
    found: bool
    target_shape: str
    steps: tuple[SolveStep, ...] = ()
    graph: SolverGraph | None = None
    warnings: tuple[str, ...] = ()


@dataclass(slots=True)
class _ShapeNodeDraft:
    id: str
    role: ShapeNodeRole
    shape_code: str
    label: str
    reused_count: int


class SolverService:
    def solve(self, request: SolverRequest) -> SolverResult:
        target_code = request.target_pattern.normalized_code
        base_shape = "CuCuCuCu"
        left_half = "CuCu----"
        right_half = "----CuCu"
        rotated_half = "--CuCu--"
        rotated_output = "--Cu--Cu"
        swapped_shape = "Cu----Cu"

        steps = (
            SolveStep(
                id="step-001",
                index=1,
                operation_type=OperationType.CUTTER,
                title="Cut a starter shape",
                description=("Cut a simple starter shape into two halves for recombination."),
                inputs=(ShapeRef(shape_code=base_shape, label="Input"),),
                outputs=(
                    ShapeRef(shape_code=left_half, label="Output A"),
                    ShapeRef(shape_code=right_half, label="Output B"),
                ),
            ),
            SolveStep(
                id="step-002",
                index=2,
                operation_type=OperationType.SWAPPER,
                title="Swap prepared halves",
                description=(
                    "Exchange halves between two lanes to demonstrate two-output operations."
                ),
                inputs=(
                    ShapeRef(shape_code=left_half, label="Input A"),
                    ShapeRef(shape_code=right_half, label="Input B"),
                ),
                outputs=(
                    ShapeRef(shape_code=rotated_half, label="Output A"),
                    ShapeRef(shape_code=swapped_shape, label="Output B"),
                ),
            ),
            SolveStep(
                id="step-003",
                index=3,
                operation_type=OperationType.ROTATE_CW,
                title="Rotate the prepared half",
                description="Rotate the selected intermediate shape clockwise.",
                inputs=(ShapeRef(shape_code=rotated_half, label="Input"),),
                outputs=(ShapeRef(shape_code=rotated_output, label="Output"),),
            ),
            SolveStep(
                id="step-004",
                index=4,
                operation_type=OperationType.STACKER,
                title="Stack into the target",
                description="Combine the intermediate with the target shape reference.",
                inputs=(
                    ShapeRef(shape_code=rotated_output, label="Input A"),
                    ShapeRef(shape_code=swapped_shape, label="Input B"),
                ),
                outputs=(ShapeRef(shape_code=target_code, label="Target"),),
            ),
        )

        return SolverResult(
            found=True,
            target_shape=target_code,
            warnings=("Prototype operation timeline: real search will replace this sequence.",),
            steps=steps,
            graph=_build_graph_from_steps(steps, target_shape=target_code),
        )


def _build_graph_from_steps(steps: tuple[SolveStep, ...], target_shape: str) -> SolverGraph:
    shape_reference_counts: dict[str, int] = {}
    for step in steps:
        for ref in (*step.inputs, *step.outputs):
            shape_reference_counts[ref.shape_code] = (
                shape_reference_counts.get(ref.shape_code, 0) + 1
            )

    shape_drafts: dict[str, _ShapeNodeDraft] = {}
    produced_shapes: set[str] = set()
    operation_nodes: list[SolverOperationNode] = []
    edges: list[SolverGraphEdge] = []

    def get_shape_node(ref: ShapeRef, fallback_role: ShapeNodeRole) -> _ShapeNodeDraft:
        role = "target" if ref.shape_code == target_shape else fallback_role
        label = ref.label or role.title()
        draft = shape_drafts.get(ref.shape_code)
        if draft is None:
            draft = _ShapeNodeDraft(
                id=f"shape-{len(shape_drafts) + 1:03d}",
                role=role,
                shape_code=ref.shape_code,
                label=label,
                reused_count=max(0, shape_reference_counts.get(ref.shape_code, 0) - 1),
            )
            shape_drafts[ref.shape_code] = draft
            return draft
        if draft.role != "target" and role == "target":
            draft.role = role
            draft.label = label
        return draft

    for step in steps:
        definition = OPERATION_CATALOG[step.operation_type]
        operation_node = SolverOperationNode(
            id=f"op-{step.index:03d}",
            operation_type=definition.type.value,
            label=definition.label,
            icon=definition.icon,
            input_count=definition.input_count,
            output_count=definition.output_count,
            description=definition.description,
        )
        operation_nodes.append(operation_node)

        for index, ref in enumerate(step.inputs):
            role: ShapeNodeRole = "intermediate" if ref.shape_code in produced_shapes else "source"
            shape_node = get_shape_node(ref, role)
            slot = _slot_name(index)
            edges.append(
                SolverGraphEdge(
                    from_id=shape_node.id,
                    to_id=operation_node.id,
                    kind="input",
                    slot=slot,
                    label=f"Input {slot}",
                )
            )

        for index, ref in enumerate(step.outputs):
            produced_shapes.add(ref.shape_code)
            shape_node = get_shape_node(ref, "intermediate")
            slot = _slot_name(index)
            edges.append(
                SolverGraphEdge(
                    from_id=operation_node.id,
                    to_id=shape_node.id,
                    kind="output",
                    slot=slot,
                    label=f"Output {slot}",
                )
            )

    shape_nodes = tuple(
        SolverShapeNode(
            id=draft.id,
            role=draft.role,
            shape_code=draft.shape_code,
            label=draft.label,
            reused_count=draft.reused_count,
        )
        for draft in shape_drafts.values()
    )
    return SolverGraph(nodes=(*shape_nodes, *operation_nodes), edges=tuple(edges))


def _slot_name(index: int) -> str:
    names = ("A", "B", "C", "D")
    if index < len(names):
        return names[index]
    return str(index + 1)
