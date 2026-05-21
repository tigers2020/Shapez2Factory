# Risks and Open Questions — `asset_references.json`

## Fields with uncertain meaning

| Field | Risk | Mitigation |
| ----- | ---- | ---------- |
| `source_guid` | Misleading name; value is path string | Rename to `source_label` on import; document in mapping |
| `stable_id` vs `ref_stable_id` | Dual hash namespaces without published hash algorithm | Golden test on re-dump; document assumption in import audit |
| `display_name_key` | May imply i18n indirection but equals `source_path` everywhere | Treat as path key until `translations.json` links appear |

---

## Inferred entities requiring human review

| Entity | Question |
| ------ | -------- |
| `asset_meta_reference` | Is this table needed for Shapez2 Factory Planner, or can apps use content tables only? |
| Path variant parsing | Should `_LOD0`, `BakedMesh`, `PartialFluid` become structured columns or stay in `logical_path`? |
| Polymorphic FK | DB-enforced vs application-enforced polymorphic reference — team preference? |

---

## Runtime metadata mistaken for domain data

| Signal | Risk | Action |
| ------ | ---- | ------ |
| `source_type_name: asset.meta` | Copied into domain model name | Keep in `dump_source_type` audit column only |
| `source_guid` | Treated as Unity GUID in UI/debug | Never show as GUID; clarify in admin |
| Sibling `UnityEngine.Object` | Same risk on content tables | Parallel provenance column |

No `Game.Content.*` strings in this file — **low risk** for this specific JSON.

---

## Ambiguous IDs

| ID | Ambiguity |
| -- | --------- |
| `meta_stable_id` | Not referenced elsewhere in bundle — purpose vs `content_stable_id` needs product decision |
| `ref_stable_id` | Clear FK to content, but name suggests “reference” not “content canonical ID” — consider rename `content_stable_id` in DB |
| Path strings | Unique but not hashed — collision risk only if dump normalizes paths differently across versions |

---

## Dynamic schemas

| Scenario | Impact |
| -------- | ------ |
| New `asset_type` value (e.g. `shader`, `audio`) | Import enum validation fails — good; requires schema migration |
| Extra keys per row | Must flow to `unknown_property` — pipeline supports |
| Row count ≠ 829 | Manifest hash + count assertion fails — signals new game version |

Current dump: **fully homogeneous** — lowest dynamic schema risk in `game_data/`.

---

## Possible version drift

| Source | Drift signal |
| ------ | ------------ |
| `manifest.dump_schema_version` | Bump triggers full re-import |
| `manifest.game_version` | `unknown+1.0.3-rc3` — non-semver label |
| `file_hashes.asset_references.json` | CI golden mismatch |
| Count mismatch prefab+sprite+material ≠ meta rows | Structural break |

---

## Missing cross-reference targets

| Expected consumer | Status |
| ----------------- | ------ |
| `buildings.json` / `building_variants.json` | **No** `stable_id` overlap with meta or content IDs in current dump |
| `toolbar_entries.json` | Not verified — may use paths not hashes |
| `translations.json` | Empty/incomplete per manifest warning |
| Application code | **No** Python/JS references to `asset_references` in repo yet |

**Risk:** Meta table may be orphaned from planner features until linking spec is written.

---

## Tables that should not be implemented yet

| Table | Reason to defer |
| ----- | --------------- |
| `asset_path_variant_hint` | Inferred from path regex only; no JSON fields |
| `game_content_asset` supertable | Polymorphic union adds complexity; three content tables sufficient |
| Any `raw_json` / `asset_references_dump` | Explicitly forbidden |
| M2M join tables | No evidence in data |

**Implement first:** `prefab_asset`, `sprite_asset`, `material_asset`, then `asset_meta_reference` if dual-ID proven necessary.

---

## Redundancy risk

829 meta rows + 829 content rows with identical `source_path` pairs suggest **duplicate registry**. If product only needs content IDs:

- Import meta table as **audit-only** (optional feature flag)
- Or replace with DB view over content tables

Decision needed before Django models ship.

---

## Summary risk level

| Area | Level |
| ---- | ----- |
| Schema complexity | **Low** (flat, 7 fields) |
| FK resolution | **Low** (100% resolved in bundle) |
| Domain ambiguity | **Medium** (dual stable ID purpose) |
| Planner integration | **High** (no downstream consumer defined) |
| Version drift | **Medium** (reflection dump, rc game version) |
