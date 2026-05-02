from django.test import Client
from django.urls import reverse


def test_solver_api_returns_auto_batch_target_count_and_base_demands() -> None:
    # Same named route as solver page `data-solver-api` (see web/templates/web/solver.html).
    solve_url = reverse("shapez_solver:solve_shape")
    assert solve_url == "/api/solver/solve/"

    response = Client().post(
        solve_url,
        data='{"code":"CuRuSuSu"}',
        content_type="application/json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert "target_count" not in payload
    assert payload["target"]["count"] == 4
    assert payload["base_demands"] == [
        {
            "base_shape_code": "CuCuCuCu",
            "quadrants_per_target": 1,
            "total_quadrants": 4,
            "full_source_count": 1,
        },
        {
            "base_shape_code": "RuRuRuRu",
            "quadrants_per_target": 1,
            "total_quadrants": 4,
            "full_source_count": 1,
        },
        {
            "base_shape_code": "SuSuSuSu",
            "quadrants_per_target": 2,
            "total_quadrants": 8,
            "full_source_count": 2,
        },
    ]
    assert payload["materialized_graph"] is not None
    target_nodes = [
        node
        for node in payload["materialized_graph"]["nodes"]
        if node["kind"] == "shape" and node["role"] == "target"
    ]
    assert len(target_nodes) == 4
    source_count_by_code: dict[str, int] = {}
    for node in payload["materialized_graph"]["nodes"]:
        if node["kind"] != "shape" or node["role"] != "source":
            continue
        shape_code = node["shape_code"]
        source_count_by_code[shape_code] = source_count_by_code.get(shape_code, 0) + 1
    assert source_count_by_code == {"CuCuCuCu": 1, "RuRuRuRu": 1, "SuSuSuSu": 2}
    target_node = next(
        node
        for node in payload["graph"]["nodes"]
        if node["kind"] == "shape" and node["role"] == "target"
    )
    assert target_node["quantity"] == 4
    assert target_node["label"] == "Target x4"
    source_qty = {
        node["shape_code"]: node["quantity"]
        for node in payload["graph"]["nodes"]
        if node["kind"] == "shape" and node["role"] == "source"
    }
    assert source_qty == {"CuCuCuCu": 1, "RuRuRuRu": 1, "SuSuSuSu": 2}
