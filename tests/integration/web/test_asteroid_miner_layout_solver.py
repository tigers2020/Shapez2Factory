from django.test import Client
from django.urls import reverse


def test_asteroid_miner_layout_page_renders_lab_shell() -> None:
    response = Client().get(reverse("web:asteroid-miner-layout"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Asteroid Mining Lab" in content
    assert "Greenfield Solver Workspace" in content
    assert "Replay Timeline" in content
    assert "lab-cell-overlay-matrix-data" in content


def test_asteroid_miner_layout_page_preserves_code_query() -> None:
    response = Client().get(
        reverse("web:asteroid-miner-layout"),
        {"code": "TEST_BLUEPRINT_SNIPPET"},
    )

    assert response.status_code == 200
    assert b"TEST_BLUEPRINT_SNIPPET" in response.content
