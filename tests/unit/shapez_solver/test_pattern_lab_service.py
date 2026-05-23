import pytest

from django_apps.shapez_solver.services.pattern_lab_service import (
    analyze_pattern_lab_shape,
    explain_pattern_family_mismatch,
)


@pytest.mark.django_db
def test_pattern_lab_analyzes_signature_without_db_candidates() -> None:
    analysis = analyze_pattern_lab_shape("CuRuSuSu")

    assert analysis.error == ""
    assert analysis.canonical_code == "CuRuSuSu"
    assert analysis.signature == "ABCC"
    assert analysis.db_candidates == ()


@pytest.mark.django_db
def test_pattern_lab_reports_parse_error() -> None:
    analysis = analyze_pattern_lab_shape("bad-code")

    assert analysis.error
    assert analysis.signature == ""


def test_explain_pattern_family_mismatch_inventory_strict() -> None:
    assert (
        explain_pattern_family_mismatch(
            "CuRuSuSu",
            family_signature="ABCC",
            allow_rotation=False,
        )
        is None
    )
    assert (
        explain_pattern_family_mismatch(
            "RuSuSuCu",
            family_signature="ABCC",
            allow_rotation=False,
        )
        is not None
    )


def test_explain_pattern_family_mismatch_rotation_union() -> None:
    assert (
        explain_pattern_family_mismatch(
            "RuSuSuCu",
            family_signature="ABCC",
            allow_rotation=True,
        )
        is None
    )


def test_explain_pattern_family_mismatch_multi_layer_each_layer_must_match() -> None:
    assert (
        explain_pattern_family_mismatch(
            "CuCuCuCu:CuCuCuCu",
            family_signature="AAAA",
            allow_rotation=False,
        )
        is None
    )
    detail = explain_pattern_family_mismatch(
        "CuCuCuCu:RcRcCuCu",
        family_signature="AAAA",
        allow_rotation=False,
    )
    assert detail is not None
    assert detail.startswith("layer 1:")
