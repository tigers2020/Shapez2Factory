from django.test import Client


def test_api_asteroid_health_returns_ok() -> None:
    response = Client().get("/api/asteroid/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
