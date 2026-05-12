"""Throughput and grid constants for asteroid extraction MVP."""

from __future__ import annotations

SHAPE_SLOTS_PER_CORE = 4
SHAPE_SLOTS_PER_EXTENSION = 4
EXTENSION_MAX_PER_CLUSTER = 3

ITEMS_PER_MIN_PER_SHAPE_SLOT = 45

SHAPE_SHAPE_THROUGHPUT_PER_CLUSTER_MAX = ITEMS_PER_MIN_PER_SHAPE_SLOT * (
    SHAPE_SLOTS_PER_CORE + EXTENSION_MAX_PER_CLUSTER * SHAPE_SLOTS_PER_EXTENSION
)

ASTEROID_EXTERIOR_MARGIN = 5

DEFAULT_BEAM_WIDTH = 8

CLUSTER_TILE_ESTIMATE = 12

# Beam: cap branching so the in-process worker returns quickly (avoids endless /status polling).
BEAM_ENUM_MAX_EXTENSION_DEPTH = 2
BEAM_MAX_CORE_CANDIDATES_PER_STATE = 12
# Upper bound for explicit user input; time budget keeps large values responsive.
BEAM_HARD_CAP = 256
BEAM_DEFAULT_MAX_CLUSTERS_CAP = 24
BEAM_TIME_BUDGET_SEC = 4.0
