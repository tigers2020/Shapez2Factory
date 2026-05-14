from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.decode.existing_layout_analysis import (  # noqa: E501
    analyze_decoded_layout,
    trivial_unknown_analysis,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import SourceKind


def test_trivial_unknown_analysis_contract() -> None:
    ctx = trivial_unknown_analysis()
    assert ctx.source_kind is SourceKind.UNKNOWN
    assert ctx.issues == ()


def test_analyze_decoded_layout_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        analyze_decoded_layout({})
