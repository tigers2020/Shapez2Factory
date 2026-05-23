from django.test import Client, override_settings
from django.urls import reverse

_EN_HEADERS = {"HTTP_ACCEPT_LANGUAGE": "en"}


@override_settings(LANGUAGE_CODE="en")
def test_pattern_lab_page_renders_empty_state() -> None:
    response = Client().get(reverse("web:pattern-lab"), **_EN_HEADERS)
    assert response.status_code == 200
    content = response.content.decode()
    assert "Pattern Lab" in content
    assert "Enter a shape code" in content


@override_settings(LANGUAGE_CODE="en")
def test_pattern_lab_page_shows_signature_without_macro_candidates() -> None:
    response = Client().get(
        reverse("web:pattern-lab"),
        {"code": "CuRuSuSu"},
        **_EN_HEADERS,
    )
    assert response.status_code == 200
    content = response.content.decode()
    assert "CuRuSuSu" in content
    assert "ABCC" in content
