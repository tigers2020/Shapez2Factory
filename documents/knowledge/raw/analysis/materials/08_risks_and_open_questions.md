# Risks and Open Questions — `materials.json`

## Uncertain meaning

| Field | Risk |
| ----- | ---- |
| No shader/texture properties | Render pipeline cannot reconstruct Material from DB alone |
| `PainterRollMinimalMaterial` vs `PainterRollMaterial` | Usage context only in game assets |

## Human review

| Item | Question |
| ---- | -------- |
| Store `logical_path` separately | Redundant with `material_path` in current dump |
| Planner domain scope | Are materials planner inputs or export-only for UI? |

## Runtime metadata traps

| Trap | Handling |
| ---- | -------- |
| Model `UnityEngineObject` | Reject |
| Using empty `source_guid` as FK | NULL only |

## Ambiguous IDs

- `stable_id` is reliable here (unlike `items.json` duplicate envelope ids).
- `display_name_key` duplicates path string — may differ when translations exist.

## Dynamic schema

- Very small fixed set (4); new materials likely rare.
- New keys should fail closed or land in `unknown_property`.

## Version drift

- Track `manifest.file_hashes.materials.json`.
- Any new material must add matching `asset_references` row or import fails FK check.

## Missing cross-reference targets

| Target | Status |
| ------ | ------ |
| `translations.json` | Empty — display names unresolved |
| Building variant → material | No explicit FK in JSON |
| Shader graph properties | Not exported |

## Deferred tables

| Table | Reason |
| ----- | ------ |
| `material_shader_property` | No source data |
| `material_texture_slot` | Not in dump |

## Highest risk

Importing `asset_references.json` **before** materials — breaks 4 material FK resolutions. **Mitigation:** documented import order and integration test.
