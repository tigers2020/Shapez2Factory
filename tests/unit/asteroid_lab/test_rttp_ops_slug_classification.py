"""Track B — RTTP ops slug class registry (diagnostic vs pass_capable vs unknown)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.contracts import rttp_ops_policy as policy
from django_apps.asteroid_lab.contracts.rttp_ops_policy import (
    RTTP_DIAGNOSTIC_CANON_SLUG,
    RTTP_DIAGNOSTIC_CANON_SLUGS,
    RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON,
    RTTP_OPS_SLUG_CLASS_PASS_CAPABLE,
    RTTP_OPS_SLUG_CLASS_UNKNOWN,
    RTTP_PASS_CAPABLE_SLUGS,
    RTTP_PASS_CAPABLE_TINY_PASSABLE_V2_SLUG,
    classify_rttp_ops_slug,
    is_diagnostic_canon_slug,
)


def test_diagnostic_canon_slug_in_registry() -> None:
    assert RTTP_DIAGNOSTIC_CANON_SLUG in RTTP_DIAGNOSTIC_CANON_SLUGS
    assert is_diagnostic_canon_slug(RTTP_DIAGNOSTIC_CANON_SLUG)


def test_copy_import_classified_diagnostic_canon() -> None:
    assert classify_rttp_ops_slug("copy-import-495e552c") == RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON


def test_unregistered_slug_is_unknown() -> None:
    assert classify_rttp_ops_slug("some-other-slug") == RTTP_OPS_SLUG_CLASS_UNKNOWN


def test_tiny_passable_v2_in_pass_capable_registry() -> None:
    assert RTTP_PASS_CAPABLE_TINY_PASSABLE_V2_SLUG in RTTP_PASS_CAPABLE_SLUGS
    assert (
        classify_rttp_ops_slug(RTTP_PASS_CAPABLE_TINY_PASSABLE_V2_SLUG)
        == RTTP_OPS_SLUG_CLASS_PASS_CAPABLE
    )


def test_diagnostic_canon_wins_when_slug_in_both_lists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        policy,
        "RTTP_PASS_CAPABLE_SLUGS",
        frozenset({RTTP_DIAGNOSTIC_CANON_SLUG}),
    )
    assert (
        classify_rttp_ops_slug(RTTP_DIAGNOSTIC_CANON_SLUG)
        == RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON
    )


def test_pass_capable_when_registered(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        policy,
        "RTTP_PASS_CAPABLE_SLUGS",
        frozenset({"cert-reference-slug"}),
    )
    assert classify_rttp_ops_slug("cert-reference-slug") == RTTP_OPS_SLUG_CLASS_PASS_CAPABLE


def test_classify_strips_whitespace() -> None:
    assert (
        classify_rttp_ops_slug(f"  {RTTP_DIAGNOSTIC_CANON_SLUG}  ")
        == RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON
    )
