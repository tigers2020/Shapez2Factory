"""Recipe graph 엣지 토폴로지: shape ↔ operation 및 intermediate→target(delivery) 규칙."""

from __future__ import annotations


def index_recipe_graph_nodes_by_id(
    nodes: list[dict[str, object]],
) -> dict[str, dict[str, object]]:
    """``graph_document`` 의 ``nodes`` 리스트에서 ``str(id) -> 노드 dict`` 맵을 만든다.

    ``validate_graph_document`` 통과 후 노드만 넘기는 것을 전제로 한다(비 dict·id 없음은 건너뜀).
    """
    by_id: dict[str, dict[str, object]] = {}
    for n in nodes:
        if isinstance(n, dict) and n.get("id") is not None:
            by_id[str(n["id"])] = n
    return by_id


def _resolved_edge_nodes(
    by_id: dict[str, dict[str, object]], fr: str, to: str
) -> tuple[dict[str, object], dict[str, object]] | None:
    nf = by_id.get(fr)
    nt = by_id.get(to)
    if not nf or not nt:
        return None
    return nf, nt


def _validate_input_edge(i: int, nf: dict[str, object], nt: dict[str, object]) -> None:
    if nf.get("kind") != "shape" or nt.get("kind") != "operation":
        raise ValueError(
            f"edges[{i}]: input edge must be shape → operation, "
            f"got {nf.get('kind')} → {nt.get('kind')}"
        )


def _validate_output_edge(i: int, nf: dict[str, object], nt: dict[str, object]) -> None:
    if nf.get("kind") != "operation" or nt.get("kind") != "shape":
        raise ValueError(
            f"edges[{i}]: output edge must be operation → shape, "
            f"got {nf.get('kind')} → {nt.get('kind')}"
        )
    role = str(nt.get("role") or "intermediate").strip()
    if role != "intermediate":
        raise ValueError(
            f"edges[{i}]: operation output must target "
            f"role=intermediate shape, got role={role!r}"
        )


def _validate_delivery_edge(i: int, nf: dict[str, object], nt: dict[str, object]) -> None:
    if nf.get("kind") != "shape" or nt.get("kind") != "shape":
        raise ValueError(
            f"edges[{i}]: delivery edge must be shape → shape, "
            f"got {nf.get('kind')} → {nt.get('kind')}"
        )
    rs = str(nf.get("role") or "intermediate").strip()
    rt = str(nt.get("role") or "intermediate").strip()
    if rs != "intermediate":
        raise ValueError(f"edges[{i}]: delivery source must be role=intermediate, got role={rs!r}")
    if rt != "target":
        raise ValueError(f"edges[{i}]: delivery target must be role=target, got role={rt!r}")


def assert_recipe_graph_edge_topology(doc: dict[str, object]) -> None:
    """
    검증 통과용 graph_document에 대해 연결 규칙을 강제한다.

    - ``input`` 엣지: ``shape`` → ``operation`` 만 허용.
    - ``output`` 엣지: ``operation`` → ``shape`` 이며, 대상 shape의 ``role`` 은
      ``intermediate`` 만 허용(operation 출력은 중간 shape 노드로만).
    - ``delivery`` 엣지: ``role=intermediate`` 인 ``shape`` → ``role=target`` 인 ``shape``
      (중간 산출물을 납품 목표 노드로 연결).

    ``validate_graph_document`` 로 노드·엣지 형식이 이미 통과한 뒤 호출한다.
    """
    nodes = doc.get("nodes")
    edges = doc.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return
    by_id = index_recipe_graph_nodes_by_id(nodes)
    for i, e in enumerate(edges):
        if not isinstance(e, dict):
            continue
        fr = str(e.get("from", ""))
        to = str(e.get("to", ""))
        k = str(e.get("kind", ""))
        pair = _resolved_edge_nodes(by_id, fr, to)
        if pair is None:
            continue
        nf, nt = pair
        if k == "input":
            _validate_input_edge(i, nf, nt)
        elif k == "output":
            _validate_output_edge(i, nf, nt)
        elif k == "delivery":
            _validate_delivery_edge(i, nf, nt)


def assert_delivery_targets_unique(edges: list[dict[str, object]]) -> None:
    """각 target shape에는 최대 하나의 ``delivery`` 입력만 허용한다."""
    seen: set[str] = set()
    for i, e in enumerate(edges):
        if not isinstance(e, dict):
            continue
        if str(e.get("kind", "")) != "delivery":
            continue
        tid = str(e.get("to", "")).strip()
        if tid in seen:
            raise ValueError(f"edges[{i}]: duplicate delivery edge to target {tid!r}")
        seen.add(tid)


__all__ = [
    "assert_delivery_targets_unique",
    "assert_recipe_graph_edge_topology",
    "index_recipe_graph_nodes_by_id",
]
