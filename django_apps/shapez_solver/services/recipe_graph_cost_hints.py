"""graph_document에서 카탈로그·솔버 메타와 정합할 수 있는 비용 힌트(파생)."""

from __future__ import annotations

from typing import Any


def graph_cost_hint_from_document(graph_document: dict[str, Any]) -> dict[str, Any]:
    """
    재계산된 graph_document에서 연산 노드 수 등 구조 기반 힌트를 만든다.

    스태프 그래프 저장 시 `macro_recipe_staff_catalog.apply_graph_derived_catalog_fields`가
    이 힌트를 바탕으로 ``MacroRecipe`` 비용·priority를 갱신할 수 있다(메타 수동 입력과 별개).
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
            "MacroRecipe의 estimated_*·priority가 이 힌트로 갱신될 수 있다."
        ),
    }


__all__ = ["graph_cost_hint_from_document"]
