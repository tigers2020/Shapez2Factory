"""graph_document에서 선형 primitive 체인 추출(Phase 4 모드 B 후속용)."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_solver.domain.operations import OperationType


def try_linear_operation_sequence(graph_document: dict[str, Any]) -> list[str] | None:
    """
    분기 없이 연산 노드가 0~1개일 때만 operation 문자열 시퀀스를 반환한다.

    멀티 연산·분기 DAG는 ``None`` (별도 플래너·토포 추출 확장 전까지).
    """
    nodes = graph_document.get("nodes") if isinstance(graph_document, dict) else None
    if not isinstance(nodes, list):
        return None

    op_nodes = [n for n in nodes if isinstance(n, dict) and n.get("kind") == "operation"]
    if not op_nodes:
        return []
    if len(op_nodes) > 1:
        return None

    raw_op = str(op_nodes[0].get("operation", "")).strip()
    try:
        OperationType(raw_op)
    except ValueError:
        return None
    return [raw_op]


__all__ = ["try_linear_operation_sequence"]
