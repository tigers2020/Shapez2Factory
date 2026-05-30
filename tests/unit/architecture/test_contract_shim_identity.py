"""Architecture guard: relocated contract symbols re-exported through ``django_apps`` shims
MUST be the *same object* as the core symbols.

PR-CLI-2d moved many Asteroid Lab contract modules out of
``django_apps/asteroid_lab/layers/contracts/`` (and ``genetic_sample/enums.py``) into the
Django-free core under ``shapez2_factory.application.asteroid_lab.layers.contracts.*`` and
``shapez2_factory.domain.asteroid_lab.genetic_sample.enums``, leaving the ``django_apps`` originals
as pure re-export shims. This guard locks in that the django path and the core path resolve to the
identical object (``is`` identity), proving the shims re-export rather than redefine.

These contract shims are pure re-exports, so importing them requires ZERO Django setup (no ORM,
no settings access). Symbols deferred to PR-CLI-2e (``rim_placement``, ``layer04_disabled``) are
intentionally excluded.
"""

from __future__ import annotations

import importlib

import pytest

_DJANGO_CONTRACTS = "django_apps.asteroid_lab.layers.contracts"
_CORE_CONTRACTS = "shapez2_factory.application.asteroid_lab.layers.contracts"

# (symbol, contract submodule) sharing the django/core contract package bases above.
_CONTRACT_CASES = [
    # Required coverage (per plan).
    ("TransportKind", "transport_kind"),
    ("ResourceKind", "transport_kind"),
    ("PlacementCommitState", "placement_state"),
    ("StackRunStatus", "stack_status"),
    ("LayerBudgetContext", "layer_budget"),
    ("ProvisionalLayoutOverlay", "provisional_overlay"),
    # Broadened coverage.
    ("CardinalEdge", "cardinal_edge"),
    ("DiagnosticLayerSnapshot", "diagnostic"),
    ("ExteriorConnectionPlan", "exterior_connection"),
    ("ExteriorConnector", "exterior_connection"),
    ("RimBundleCandidateSet", "candidates"),
    ("BundleCellRole", "candidates"),
    ("Layer03Observability", "layer03_observability"),
    ("IntegratedRimGreedyResult", "rim_greedy"),
]

# (symbol, django_dotted_path, core_dotted_path) — full triples (paths differ from contracts base).
_FULL_PATH_CASES = [
    (
        "Direction",
        "django_apps.asteroid_lab.genetic_sample.enums",
        "shapez2_factory.domain.asteroid_lab.genetic_sample.enums",
    ),
]

_SHIM_IDENTITY_CASES = [
    (symbol, f"{_DJANGO_CONTRACTS}.{module}", f"{_CORE_CONTRACTS}.{module}")
    for symbol, module in _CONTRACT_CASES
] + _FULL_PATH_CASES


@pytest.mark.parametrize(
    ("symbol", "django_path", "core_path"),
    [
        pytest.param(symbol, dj, core, id=f"{symbol}::{dj.rsplit('.', 1)[-1]}")
        for symbol, dj, core in _SHIM_IDENTITY_CASES
    ],
)
def test_contract_shims_preserve_identity(symbol: str, django_path: str, core_path: str) -> None:
    """The django shim symbol MUST be the identical object exported by the core module."""
    django_module = importlib.import_module(django_path)
    core_module = importlib.import_module(core_path)

    django_obj = getattr(django_module, symbol)
    core_obj = getattr(core_module, symbol)

    assert django_obj is core_obj, (
        f"shim identity broken: {django_path}.{symbol} is not {core_path}.{symbol}; "
        "the django shim must re-export the core symbol, not redefine it"
    )
