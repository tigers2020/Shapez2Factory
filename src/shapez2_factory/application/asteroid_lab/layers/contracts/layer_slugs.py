"""Canonical layer slug strings for stack_runner and observability."""

from __future__ import annotations

LAYER_01_RECONSTRUCTION = "layer_01_reconstruction"
LAYER_02_EXTERIOR_TRANSPORT = "layer_02_exterior_transport"
LAYER_03_RIM_GREEDY_PLACEMENT = "layer_03_rim_greedy_placement"
LAYER_03_RIM_MINING_BUNDLES = "layer_03_rim_mining_bundles"  # deprecated import only
LAYER_04_RIM_BUNDLE_PLACEMENT = "layer_04_rim_bundle_placement"  # inactive; shim only
LAYER_05_INNER_PATTERN_FILL = "layer_05_inner_pattern_fill"
LAYER_06_COMMIT_VALIDATE = "layer_06_commit_validate"

LAYERS_02_TO_06_ACTIVE: tuple[str, ...] = (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_05_INNER_PATTERN_FILL,
    LAYER_06_COMMIT_VALIDATE,
)

LAYERS_02_TO_06: tuple[str, ...] = LAYERS_02_TO_06_ACTIVE

# Deprecated alias (PR-3c renumber); remove when external callers migrate.
LAYERS_02_TO_05 = LAYERS_02_TO_06
LAYER_04_INNER_PATTERN_FILL = LAYER_05_INNER_PATTERN_FILL
LAYER_05_COMMIT_VALIDATE = LAYER_06_COMMIT_VALIDATE
