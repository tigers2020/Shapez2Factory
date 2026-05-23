"""graph_document에서 카탈로그·솔버 메타와 정합할 수 있는 비용 힌트(파생)."""

from __future__ import annotations

from typing import Any


def graph_cost_hint_from_document(graph_document: dict[str, Any]) -> dict[str, Any]:
    """
    재계산된 graph_document에서 연산 노드 수 등 구조 기반 힌트를 만든다.

    레시피 그래프 재계산·저장 경로에서 `estimated_*` 필드와 정합할 때
    이 힌트는 그래프 문서의 예상 비용·우선순위 메타와 정합 검사에 쓸 수 있다.
    """
    nodes = graph_document.get("nodes") or []
    if not isinstance(nodes, list):
        op_count = 0
        shape_count = 0
    else:
        op_count = sum(1 for n in nodes if isinstance(n, dict) and n.get("kind") == "operation")
        shape_count = sum(1 for n in nodes if isinstance(n, dict) and n.get("kind") == "shape")
    return {
        "operation_node_count": op_count,
        "shape_node_count": shape_count,
        "estimated_stage_count": op_count,
        "graph_operation_cost_sum_min": op_count,
        "note": (
            "구조 기반 최소치(연산·shape 노드 수). 스태프에서 그래프를 커밋하면 "
            "graph cost hint may be used to validate estimated cost metadata."
        ),
    }


__all__ = ["graph_cost_hint_from_document"]
