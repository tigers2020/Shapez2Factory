"""PR-CLI-2f Step 2 (tests-first) — relocated pipeline shims preserve object identity.

After PR-CLI-2f moves the 15 decode/cleanup/reconstruction modules into core, the original
``django_apps`` modules become pure re-export shims. This guard locks in that each key public symbol
resolves to the **identical object** (``is``) on both the Django path and the core path, proving the
shims re-export rather than redefine.

RED until PR-CLI-2f Step 4: the core modules do not exist yet, so importing ``core_path`` raises.
"""

from __future__ import annotations

import importlib

import pytest

_DJ = "django_apps.asteroid_lab"
_CORE = "shapez2_factory.domain.asteroid_lab"

# (symbol, django_dotted_module, core_dotted_module)
_CASES = [
    ("decode_copy_string", f"{_DJ}.adapters.decode_adapter", f"{_CORE}.copy_decode"),
    ("AsteroidLabCopyDecodeError", f"{_DJ}.adapters.decode_adapter", f"{_CORE}.copy_decode"),
    ("normalize_decoded_blueprint", f"{_DJ}.adapters.normalization", f"{_CORE}.normalization"),
    (
        "build_decoded_blueprint_snapshot",
        f"{_DJ}.snapshots.decoded_blueprint_snapshot",
        f"{_CORE}.decoded_blueprint_snapshot",
    ),
    ("classify_blueprint_entry", f"{_DJ}.snapshots.cell_classifier", f"{_CORE}.cell_classifier"),
    ("entry_island_raw_coord", f"{_DJ}.snapshots.copy_json_coords", f"{_CORE}.copy_json_coords"),
    ("deconstruct_snapshot", f"{_DJ}.cleanup.pipeline", f"{_CORE}.cleanup.pipeline"),
    (
        "run_topology_reconstruction",
        f"{_DJ}.reconstruction.pipeline",
        f"{_CORE}.reconstruction.pipeline",
    ),
    (
        "apply_confidence_to_result",
        f"{_DJ}.reconstruction.confidence",
        f"{_CORE}.reconstruction.confidence",
    ),
    (
        "external_reachable",
        f"{_DJ}.reconstruction.flood_fill",
        f"{_CORE}.reconstruction.flood_fill",
    ),
    ("stamp_islands_uniform", f"{_DJ}.reconstruction.island", f"{_CORE}.reconstruction.island"),
    (
        "close_diagonal_leaks",
        f"{_DJ}.reconstruction.perimeter_closing",
        f"{_CORE}.reconstruction.perimeter_closing",
    ),
    (
        "ReconstructionTraceCollector",
        f"{_DJ}.reconstruction.trace",
        f"{_CORE}.reconstruction.trace",
    ),
    (
        "build_normalized_reconstruction_topology",
        f"{_DJ}.reconstruction.topology_contract",
        f"{_CORE}.reconstruction.topology_contract",
    ),
]


@pytest.mark.parametrize(
    ("symbol", "django_path", "core_path"),
    [
        pytest.param(symbol, dj, core, id=f"{symbol}::{core.rsplit('.', 1)[-1]}")
        for symbol, dj, core in _CASES
    ],
)
def test_pipeline_shim_preserves_identity(symbol: str, django_path: str, core_path: str) -> None:
    django_module = importlib.import_module(django_path)
    core_module = importlib.import_module(core_path)
    django_obj = getattr(django_module, symbol)
    core_obj = getattr(core_module, symbol)
    assert django_obj is core_obj, (
        f"shim identity broken: {django_path}.{symbol} is not {core_path}.{symbol}; "
        "the django shim must re-export the core symbol, not redefine it"
    )
