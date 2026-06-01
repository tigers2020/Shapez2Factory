"""Canonical L4/L5 slug constants and deprecated slug resolver (PR-1 renumber)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
    LAYERS_02_TO_06_ACTIVE,
    resolve_canonical_layer_slug,
)


def test_canonical_slug_constants() -> None:
    assert LAYER_04_INNER_PATTERN_FILL == "layer_04_inner_pattern_fill"
    assert LAYER_05_TRANSPORT_ROUTING == "layer_05_transport_routing"


def test_active_stack_order_fill_before_transport() -> None:
    slugs = list(LAYERS_02_TO_06_ACTIVE)
    assert slugs.index(LAYER_04_INNER_PATTERN_FILL) < slugs.index(LAYER_05_TRANSPORT_ROUTING)


def test_resolve_deprecated_transport_slug() -> None:
    assert resolve_canonical_layer_slug("layer_04_transport_routing") == (
        LAYER_05_TRANSPORT_ROUTING
    )


def test_resolve_deprecated_inner_fill_slug() -> None:
    assert resolve_canonical_layer_slug("layer_05_inner_pattern_fill") == (
        LAYER_04_INNER_PATTERN_FILL
    )


def test_canonical_slug_is_identity() -> None:
    assert resolve_canonical_layer_slug(LAYER_05_TRANSPORT_ROUTING) == (LAYER_05_TRANSPORT_ROUTING)
