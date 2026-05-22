"""Pinned ORM counts for game_data_backup/game_data_dump.json.

All values are valid only when ImportBatch.manifest_self_hash == PINNED_MANIFEST_HASH.
Regenerate via docs/runbooks/game_data_tier_a_release_gate.md when the dump changes.
"""

from __future__ import annotations

PINNED_MANIFEST_HASH = (
    "sha256:a7f71325bb779ff6c2a1665ff6c9fa3067943cc6335a7926567d2ee76be8dd09"
)

PINNED_IMPORT_BATCH_PK = 1
PINNED_BATCH_NAME = "default"

TOOLBAR_TREE_NODE_COUNT = 204
TOOLBAR_ELEMENT_COUNT = 142
TOOLBAR_ACTION_KIND_NODE_COUNT = 142

SHAPE_RECIPE_COUNT = 1170
ITEMS_SOURCE_APPEARANCE_COUNT = 70
FULL_SOURCE_APPEARANCE_COUNT = 1170

SIMULATION_SYSTEM_COUNT = 180
