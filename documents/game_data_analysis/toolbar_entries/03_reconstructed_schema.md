# Reconstructed Schema — `toolbar_entries.json`

## Overview

| Table | Purpose | Domain question answered | Source paths | Cross references | Review status |
| ----- | ------- | ------------------------ | ------------ | ---------------- | ------------- |
| `toolbar_tree_node` | Full tree (204 rows) | What nodes exist? | `[*]` envelope | parent FK, sibling UK | Observed |
| `toolbar_element` | ACTION leaves (142) | What is placeable? | placer rows | 1:1 `tree_node` | Observed |
| `toolbar_building_placement` | Build action | Which building variant? | BuildingBased rows | building_groups | Observed |
| `toolbar_island_placement` | Island action | Which island group? | IslandBased rows | transport/sim | Observed |
| (no separate group/separator tables) | GROUP/FOLDER/SEPARATOR/ROOT | Structure only | Group/Category/Separator rows | `node_kind` on tree node | Observed |
| `game_data_import_batch` | Provenance | Which dump? | manifest | → all | Observed |
| `unknown_property` | Extensions | Unmapped keys | any | audit | Planned |

---

## `toolbar_tree_node`

| Column | Meaning | Source | Constraints |
| ------ | ------- | ------ | ----------- |
| `canonical_id` | Stable identity | `stable_id` first, else parent+child_index | UNIQUE |
| `source_stable_id` | Dump hash | `[*].stable_id` | optional blank |
| `parent`, `child_index`, `depth` | Hierarchy | path parse in import | UK `(parent, child_index)` |
| `node_kind` | ROOT/FOLDER/GROUP/SEPARATOR/ACTION | classifier | enum |
| `tree_path` | Debug/audit | `display_name_key` | indexed, not unique |

Import: in-memory 4-pass; `tree_path` is not upsert key.

**Domain question:** “What is the toolbar tree shape (including separators and folders)?”

---

## `toolbar_element`

| Column | Meaning | Source | Constraints |
| ------ | ------- | ------ | ----------- |
| `tree_node_id` | ACTION node | FK 1:1 | only `node_kind=action` |
| `stable_key`, `display_name` | UX identity | snapshot | not `root/Children[...]` |
| `element_kind` | building / island / other | `source_type_name` | enum |

---

## `toolbar_building_placement`

| Column | Source |
| ------ | ------ |
| `toolbar_element_id` | FK 1:1 |
| `building_definition_key` | `BuildingDefinition.Id.Id` |
| `placer_id` | `IPlacementToolbarElementData.PlacerId.Id` |
| `is_transport_building` | bool |
| `player_buildable` | bool |
| `icon_sprite_name` | `BuildingDefinition.Icon.name` |

**Do not** store full `BuildingDefinition` JSON (5 MB driver).

---

## `toolbar_island_placement`

| Column | Source |
| ------ | ------ |
| `toolbar_element_id` | FK |
| `island_group_name` | `IslandGroup.Id.Name` |
| `placer_id` | placement ids |

---

## Anti-patterns rejected

| Rejected | Why |
| -------- | --- |
| `toolbar_entries_raw_json` | 5.7 MB |
| 204 `BuildingBasedPlacementToolbarElementData` tables | CLR names |
| JSONField `Children` on domain row | Normalize via `ToolbarTreeNode` parent FK |
| `ToolbarTreeEdge` table | Replaced by `ToolbarTreeNode.parent` |
