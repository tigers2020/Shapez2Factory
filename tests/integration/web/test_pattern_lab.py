from django.test import Client
from django.urls import reverse


def test_pattern_lab_page_renders_empty_state() -> None:
    response = Client().get(reverse("web:pattern-lab"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Pattern Lab" in content
    assert "Enter a shape code" in content


def test_pattern_lab_page_shows_signature_without_macro_candidates() -> None:
    response = Client().get(reverse("web:pattern-lab"), {"code": "CuRuSuSu"})

    assert response.status_code == 200
    content = response.content.decode()
    assert "CuRuSuSu" in content
    assert "ABCC" in content
