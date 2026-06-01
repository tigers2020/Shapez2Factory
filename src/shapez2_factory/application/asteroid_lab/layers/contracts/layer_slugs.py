"""Canonical layer slug strings for stack_runner and observability."""

from __future__ import annotations

LAYER_01_RECONSTRUCTION = "layer_01_reconstruction"
LAYER_02_EXTERIOR_TRANSPORT = "layer_02_exterior_transport"
LAYER_03_RIM_GREEDY_PLACEMENT = "layer_03_rim_greedy_placement"
LAYER_03_RIM_MINING_BUNDLES = "layer_03_rim_mining_bundles"  # deprecated import only
LAYER_04_INNER_PATTERN_FILL = "layer_04_inner_pattern_fill"
LAYER_05_TRANSPORT_ROUTING = "layer_05_transport_routing"
LAYER_06_COMMIT_VALIDATE = "layer_06_commit_validate"

# Deprecated inactive rim bundle slug (historical).
LAYER_04_RIM_BUNDLE_PLACEMENT = "layer_04_rim_bundle_placement"

# Deprecated misnumbered slug literals — read-compat only; do not use in new code.
DEPRECATED_SLUG_LAYER_04_TRANSPORT_ROUTING = "layer_04_transport_routing"
DEPRECATED_SLUG_LAYER_05_INNER_PATTERN_FILL = "layer_05_inner_pattern_fill"

_DEPRECATED_SLUG_TO_CANONICAL: dict[str, str] = {
    DEPRECATED_SLUG_LAYER_04_TRANSPORT_ROUTING: LAYER_05_TRANSPORT_ROUTING,
    DEPRECATED_SLUG_LAYER_05_INNER_PATTERN_FILL: LAYER_04_INNER_PATTERN_FILL,
    LAYER_04_RIM_BUNDLE_PLACEMENT: LAYER_04_RIM_BUNDLE_PLACEMENT,
}

LAYERS_02_TO_06_ACTIVE: tuple[str, ...] = (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
    LAYER_06_COMMIT_VALIDATE,
)

LAYERS_02_TO_06: tuple[str, ...] = LAYERS_02_TO_06_ACTIVE

# Deprecated import aliases (PR-3c / misnumbered transport PR).
LAYERS_02_TO_05 = LAYERS_02_TO_06
LAYER_05_COMMIT_VALIDATE = LAYER_06_COMMIT_VALIDATE

# Transitional: old constant names pointing at deprecated slug strings (remove after PR-2).
LAYER_04_TRANSPORT_ROUTING = DEPRECATED_SLUG_LAYER_04_TRANSPORT_ROUTING
LAYER_05_INNER_PATTERN_FILL = DEPRECATED_SLUG_LAYER_05_INNER_PATTERN_FILL


def resolve_canonical_layer_slug(slug: str) -> str:
    """Map persisted misnumbered slug literals to canonical slugs."""

    return _DEPRECATED_SLUG_TO_CANONICAL.get(slug, slug)


__all__ = [
    "DEPRECATED_SLUG_LAYER_04_TRANSPORT_ROUTING",
    "DEPRECATED_SLUG_LAYER_05_INNER_PATTERN_FILL",
    "LAYER_01_RECONSTRUCTION",
    "LAYER_02_EXTERIOR_TRANSPORT",
    "LAYER_03_RIM_GREEDY_PLACEMENT",
    "LAYER_03_RIM_MINING_BUNDLES",
    "LAYER_04_INNER_PATTERN_FILL",
    "LAYER_04_RIM_BUNDLE_PLACEMENT",
    "LAYER_04_TRANSPORT_ROUTING",
    "LAYER_05_COMMIT_VALIDATE",
    "LAYER_05_INNER_PATTERN_FILL",
    "LAYER_05_TRANSPORT_ROUTING",
    "LAYER_06_COMMIT_VALIDATE",
    "LAYERS_02_TO_05",
    "LAYERS_02_TO_06",
    "LAYERS_02_TO_06_ACTIVE",
    "resolve_canonical_layer_slug",
]
