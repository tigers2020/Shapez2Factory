# Import Pipeline — `toolbar_entries.json`

**Prerequisites:** `manifest.json`; recommend **`sprites.json`** before icon FK validation.

1. Load streaming (~5.7 MB); verify hash `a54116a4…`.
2. Validate 204 rows; unique `stable_id`, `display_name_key`.
3. Normalize `element_kind` from `source_type_name`; parse `tree_path` parent.
4. Register source metadata per index.
5. Sample 16, 103, 115 (seed 20260521).
6. DTOs per kind; extract scalars only from `BuildingDefinition`.
7. Validate enum kinds; building keys non-empty for BuildingBased rows.
8. Upsert `toolbar_element` on `stable_id` or `tree_path`.
9. Upsert extension tables + `toolbar_tree_edge` from path parse + `Children` order where needed.
10. Resolve sprite names + mechanic ids.
11. Invariants: 204 elements; 78+63+54 kind counts; 9 root children.
12. Audit: payload size, unknown BuildingDefinition keys → `unknown_property`.

## Idempotency

Natural keys: `tree_path`, `stable_id`.

## Anti-pattern

Do not load entire nested `BuildingDefinition` into domain JSONField.
