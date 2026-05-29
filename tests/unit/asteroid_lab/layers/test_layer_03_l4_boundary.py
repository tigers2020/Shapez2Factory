"""Layer 03 / Layer 04 responsibility boundary (skeleton)."""

from __future__ import annotations

import inspect

from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles import run as layer03_run
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement import run as layer04_run


def test_layer03_run_does_not_import_provisional_overlay_builder() -> None:
    source = inspect.getsource(layer03_run)
    assert "build_provisional_overlay" not in source
    assert "ProvisionalLayoutOverlay" not in source
    assert "select_non_overlapping_candidates" not in source


def test_layer04_run_is_stub_without_selection_graph() -> None:
    source = inspect.getsource(layer04_run)
    assert "select_non_overlapping_candidates_v2" not in source
    assert "exact_pack" not in source
