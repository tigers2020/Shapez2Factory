"""Layer 03 / Layer 04 responsibility boundary (no overlay in L3)."""

from __future__ import annotations

import inspect

from django_apps.asteroid_lab.layers import layer_03_rim_mining_bundles


def test_layer03_package_does_not_import_provisional_overlay_builder() -> None:
    source = inspect.getsource(layer_03_rim_mining_bundles)
    assert "build_provisional_overlay" not in source
    assert "ProvisionalLayoutOverlay" not in source
    assert "select_non_overlapping_candidates" not in source
    assert "select_non_overlapping_candidates_v2" not in source
