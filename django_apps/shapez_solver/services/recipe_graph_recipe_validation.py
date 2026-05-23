"""Recipe graph_document vs pattern family signature — validation helpers."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_core.services.shape_code_parser import (
    ShapeCodeParseError,
    parse_shape_code_list,
)
from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.services.pattern_classifier import pattern_signature
from django_apps.shapez_solver.services.pattern_lab_service import explain_pattern_family_mismatch

MAX_GRAPH_SHAPE_LAYERS_PER_PATTERN = 4


def _issue(
    severity: str,
    code: str,
    message: str,
    *,
    node_ids: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "severity": severity,
        "code": code,
        "message": message,
        "node_ids": list(node_ids),
    }


def _shape_code_structural_error(shape_code: str) -> str | None:
    """레시피 그래프 shape_code 구조 검사. 문제가 있으면 메시지, 없으면 ``None``."""
    try:
        patterns = parse_shape_code_list(shape_code.strip())
    except ShapeCodeParseError as exc:
        return f"parse error: {exc}"
    for pi, pattern in enumerate(patterns):
        n_layers = len(pattern.layers)
        if n_layers < 1 or n_layers > MAX_GRAPH_SHAPE_LAYERS_PER_PATTERN:
            return (
                f"multi-layer: pattern {pi} has {n_layers} layers; "
                f"max {MAX_GRAPH_SHAPE_LAYERS_PER_PATTERN} allowed"
            )
        for layer in pattern.layers:
            layer_str = "".join(cell.raw_token for cell in layer.cells)
            try:
                pattern_signature(layer_str)
            except ValueError as exc:
                return str(exc)
    return None


def validate_recipe_graph_context(
    *,
    family_signature: str,
    family_allow_rotation: bool,
    graph_document: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    graph_document(재계산 후 등)을 레시피 패밀리 맥락에서 검사한다.

    severity: ``error`` | ``warning`` | ``info``.
    """
    issues: list[dict[str, Any]] = []
    fam_sig = (family_signature or "").strip()
    nodes = graph_document.get("nodes")
    if not isinstance(nodes, list):
        return issues

    edges = graph_document.get("edges")
    if not isinstance(edges, list):
        edges = []

    target_ids: list[str] = []

    for node in nodes:
        if not isinstance(node, dict):
            continue
        if node.get("kind") != "shape":
            continue
        nid = str(node.get("id", "")).strip()
        if not nid:
            continue
        role = str(node.get("role", "intermediate")).strip()
        if role == "target":
            target_ids.append(nid)

        raw_q = node.get("quantity", 1)
        if isinstance(raw_q, bool) or not isinstance(raw_q, int):
            issues.append(
                _issue(
                    "error",
                    "shape_quantity_type",
                    f"shape node {nid}: quantity must be an integer",
                    node_ids=(nid,),
                ),
            )
        elif raw_q < 1:
            issues.append(
                _issue(
                    "error",
                    "shape_quantity_range",
                    f"shape node {nid}: quantity must be >= 1",
                    node_ids=(nid,),
                ),
            )

        code = str(node.get("shape_code", "")).strip()
        if not code:
            if role == "target":
                issues.append(
                    _issue(
                        "warning",
                        "target_shape_empty",
                        f"target node {nid} has empty shape_code",
                        node_ids=(nid,),
                    ),
                )
            continue

        if role == "target" and fam_sig:
            detail = explain_pattern_family_mismatch(
                code,
                family_signature=fam_sig,
                allow_rotation=family_allow_rotation,
            )
            if detail:
                if detail.startswith("parse error:") or detail.startswith("multi-layer"):
                    issues.append(
                        _issue(
                            "error",
                            "shape_code_invalid",
                            f"shape node {nid}: {detail}",
                            node_ids=(nid,),
                        ),
                    )
                else:
                    issues.append(
                        _issue(
                            "error",
                            "target_signature_mismatch",
                            f"target node {nid}: {detail}",
                            node_ids=(nid,),
                        ),
                    )
            continue

        structural = _shape_code_structural_error(code)
        if structural:
            issues.append(
                _issue(
                    "error",
                    "shape_code_invalid",
                    f"shape node {nid}: {structural}",
                    node_ids=(nid,),
                ),
            )

    if not target_ids:
        issues.append(
            _issue(
                "info",
                "no_target_node",
                "No shape node with role 'target'; catalog / goal alignment unchecked.",
            ),
        )

    for node in nodes:
        if not isinstance(node, dict) or node.get("kind") != "operation":
            continue
        oid = str(node.get("id", "")).strip()
        if not oid:
            continue
        op_key = str(node.get("operation", "")).strip()
        try:
            ot = OperationType(op_key)
        except ValueError:
            continue
        defn = OPERATION_CATALOG.get(ot)
        if defn is None:
            continue
        need = int(defn.output_count)
        if need <= 1:
            continue
        count_out = sum(
            1
            for e in edges
            if isinstance(e, dict)
            and str(e.get("kind", "")) == "output"
            and str(e.get("from", "")).strip() == oid
        )
        if count_out < need:
            issues.append(
                _issue(
                    "warning",
                    "operation_output_edges",
                    f"operation {oid} ({op_key}) catalog expects {need} outputs; "
                    f"graph has {count_out} output edge(s) — add shapes or edges for each slot.",
                    node_ids=(oid,),
                ),
            )

    return issues


def annotate_visual_graph_with_issues(
    visual_graph: dict[str, Any],
    issues: list[dict[str, Any]],
) -> None:
    """``visual_graph.nodes`` 항목에 ``validation_severity``를 붙인다 (graph_markup 소비)."""
    rank = {"error": 3, "warning": 2}
    best: dict[str, int] = {}
    for issue in issues:
        sev = str(issue.get("severity", "warning"))
        r = rank.get(sev, 0)
        if r == 0:
            continue
        for nid in issue.get("node_ids") or []:
            if not isinstance(nid, str):
                continue
            prev = best.get(nid, 0)
            if r > prev:
                best[nid] = r
    inv = {3: "error", 2: "warning", 1: "info"}
    for node in visual_graph.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        nid = node.get("id")
        if not isinstance(nid, str):
            continue
        br = best.get(nid)
        if br and br in inv:
            node["validation_severity"] = inv[br]
        else:
            node.pop("validation_severity", None)


__all__ = [
    "annotate_visual_graph_with_issues",
    "validate_recipe_graph_context",
]
