"""Input/output wire carrier (material vs fluid) for recipe graph validation."""

from __future__ import annotations

from typing import Any, Literal

from django_apps.shapez_solver.domain.operations import OperationType

Carrier = Literal["material", "fluid"]

_TWO_INPUT_OPS = frozenset(
    {
        OperationType.SWAPPER,
        OperationType.STACKER,
        OperationType.COLOR_MIXER,
        OperationType.PAINTER,
    },
)


def required_input_count(op_type: OperationType, op_node: dict[str, Any]) -> int:
    """Aligns with ``_required_input_count_for_recompute`` in ``recipe_graph_recompute``."""

    if op_type == OperationType.PAINTER:
        return 1 if str(op_node.get("paint_color", "")).strip() else 2
    if op_type == OperationType.CRYSTAL_GENERATOR:
        return 1 if str(op_node.get("crystal_color", "")).strip() else 2
    if op_type in _TWO_INPUT_OPS:
        return 2
    return 1


def expected_input_carriers(op_type: OperationType, op_node: dict[str, Any]) -> tuple[Carrier, ...]:
    """Per logical input index after ``sorted_shape_input_edges_to_operation`` order."""

    if op_type == OperationType.PAINTER:
        if str(op_node.get("paint_color", "")).strip():
            return ("material",)
        return ("fluid", "material")
    if op_type == OperationType.COLOR_MIXER:
        return ("fluid", "fluid")
    if op_type == OperationType.CRYSTAL_GENERATOR:
        if str(op_node.get("crystal_color", "")).strip():
            return ("material",)
        return ("fluid", "material")
    if op_type in (OperationType.SWAPPER, OperationType.STACKER):
        return ("material", "material")
    return ("material",)


def sorted_shape_input_edges_to_operation(
    input_edges: list[dict[str, Any]],
    node_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Same ordering as ``_sorted_input_codes_for_operation`` (slot edges before unsorted)."""

    rows: list[tuple[tuple[bool, str, str], dict[str, Any]]] = []
    for e in input_edges:
        sid = str(e.get("from", ""))
        shape = node_by_id.get(sid)
        if not shape or shape.get("kind") != "shape":
            continue
        slot = e.get("slot")
        slot_key = slot if isinstance(slot, str) and slot.strip() else ""
        has_slot = bool(slot_key)
        key = (not has_slot, slot_key, sid)
        rows.append((key, e))
    rows.sort(key=lambda t: (t[0][0], t[0][1], t[0][2]))
    return [t[1] for t in rows]


def shape_node_is_fluid(shape: dict[str, Any]) -> bool:
    return str(shape.get("source_carrier", "")).strip() == "fluid"


def operation_output_lane_carrier(op_type: OperationType, lane: int) -> Carrier:
    if op_type == OperationType.COLOR_MIXER and lane == 0:
        return "fluid"
    return "material"


def assert_input_output_carriers_for_document(doc: dict[str, Any]) -> None:
    """Raise ``ValueError`` if any input/output edge violates material/fluid rules."""

    nodes = doc.get("nodes")
    edges = doc.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return
    by_id: dict[str, dict[str, Any]] = {}
    for n in nodes:
        if isinstance(n, dict) and n.get("id") is not None:
            by_id[str(n["id"])] = n

    input_by_to: dict[str, list[dict[str, Any]]] = {}
    output_by_from: dict[str, list[dict[str, Any]]] = {}
    for _i, e in enumerate(edges):
        if not isinstance(e, dict):
            continue
        ek = str(e.get("kind", ""))
        if ek == "input":
            tid = str(e.get("to", ""))
            input_by_to.setdefault(tid, []).append(e)
        elif ek == "output":
            fid = str(e.get("from", ""))
            output_by_from.setdefault(fid, []).append(e)

    for i, e in enumerate(edges):
        if not isinstance(e, dict):
            continue
        if str(e.get("kind", "")) != "output":
            continue
        op_id = str(e.get("from", ""))
        tgt_id = str(e.get("to", ""))
        op_n = by_id.get(op_id)
        tgt = by_id.get(tgt_id)
        if not op_n or op_n.get("kind") != "operation" or not tgt or tgt.get("kind") != "shape":
            continue
        if str(tgt.get("role", "")).strip() != "intermediate":
            continue
        op_key = str(op_n.get("operation", "")).strip()
        try:
            op_type = OperationType(op_key)
        except ValueError:
            continue
        slot_raw = e.get("slot")
        lane = 0
        if isinstance(slot_raw, str) and slot_raw.strip().isdigit():
            lane = int(slot_raw.strip())
        want = operation_output_lane_carrier(op_type, lane)
        got_fluid = shape_node_is_fluid(tgt)
        if want == "fluid" and not got_fluid:
            raise ValueError(
                f"edges[{i}]: operation {op_id!r} ({op_key}) output lane {lane} is fluid; "
                f"target {tgt_id!r} must have source_carrier=fluid",
            )
        if want == "material" and got_fluid:
            raise ValueError(
                f"edges[{i}]: operation {op_id!r} ({op_key}) output lane {lane} is material; "
                f"target {tgt_id!r} must not use source_carrier=fluid",
            )

    for op_id, op_n in by_id.items():
        if op_n.get("kind") != "operation":
            continue
        op_key = str(op_n.get("operation", "")).strip()
        try:
            op_type = OperationType(op_key)
        except ValueError:
            continue
        need = required_input_count(op_type, op_n)
        expected = expected_input_carriers(op_type, op_n)
        sorted_edges = sorted_shape_input_edges_to_operation(input_by_to.get(op_id, []), by_id)
        if len(sorted_edges) < need:
            continue
        trimmed = sorted_edges[:need]
        for idx, edge in enumerate(trimmed):
            if idx >= len(expected):
                break
            slot_raw = edge.get("slot")
            slot = str(slot_raw).strip() if isinstance(slot_raw, str) else ""
            if (
                op_type in (OperationType.PAINTER, OperationType.CRYSTAL_GENERATOR)
                and len(
                    expected,
                )
                == 2
            ):
                # React Flow ``in-1`` → domain ``slot`` "1" = fluid; bare ``in`` = shape (material).
                want = "fluid" if slot == "1" else "material"
            else:
                want = expected[idx]
            from_id = str(edge.get("from", ""))
            src = by_id.get(from_id)
            if not src:
                continue
            got_fluid = shape_node_is_fluid(src)
            got: Carrier = "fluid" if got_fluid else "material"
            if got != want:
                raise ValueError(
                    f"edges: input to operation {op_id!r} ({op_key}) "
                    f"must be {want}, got {got} (from node {from_id!r})",
                )


__all__ = [
    "assert_input_output_carriers_for_document",
    "expected_input_carriers",
    "operation_output_lane_carrier",
    "required_input_count",
    "shape_node_is_fluid",
    "sorted_shape_input_edges_to_operation",
]
