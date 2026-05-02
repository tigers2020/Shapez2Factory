from django.test import Client


def test_solver_api_returns_target_count_and_base_demands() -> None:
    response = Client().post(
        "/api/solver/solve/",
        data='{"code":"CuRuSuSu","target_count":4}',
        content_type="application/json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["target_count"] == 4
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
    target_node = next(
        node
        for node in payload["graph"]["nodes"]
        if node["kind"] == "shape" and node["role"] == "target"
    )
    assert target_node["quantity"] == 4
    assert target_node["label"] == "Target x4"


def test_solver_api_rejects_invalid_target_count() -> None:
    response = Client().post(
        "/api/solver/solve/",
        data='{"code":"CuRuSuSu","target_count":0}',
        content_type="application/json",
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["code"] == "INVALID_TARGET_COUNT"
