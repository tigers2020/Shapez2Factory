import pytest

from django_apps.shapez_solver.services.pattern_classifier import (
    is_full_source_signature,
    pattern_signature,
)


def test_pattern_signature_rc_cu_rc_cu_is_abab() -> None:
    assert pattern_signature("RcCuRcCu") == "ABAB"


def test_pattern_signature_rc_rc_cu_cu_is_aabb() -> None:
    assert pattern_signature("RcRcCuCu") == "AABB"


def test_pattern_signature_rc_rc_rc_cu_is_aaab() -> None:
    assert pattern_signature("RcRcRcCu") == "AAAB"


def test_pattern_signature_rejects_multi_layer() -> None:
    with pytest.raises(ValueError, match="single-layer"):
        pattern_signature("CuCuCuCu:RuRuRuRu")


def test_is_full_source_signature() -> None:
    assert is_full_source_signature("RuRuRuRu") is True
    assert is_full_source_signature("RcCuRcCu") is False
