# Validation Plan — `items.json`

## Test module (proposed)

`tests/unit/game_data_import/test_items_import.py`

## Required checks

| # | Invariant | Test approach |
| - | --------- | --------------- |
| 1 | No orphan FK rows | After import, ORM query: slots without layer, layers without recipe |
| 2 | Unique canonical IDs | `operation_uid` UNIQUE; `shape_hash` UNIQUE (70 each) |
| 3 | All referenced IDs resolve | Every non-empty `Color.name` → `fluid_color`; every `Shape.name` → `shape_component_kind` |
| 4 | Enum values valid | Parametrize 8 shape names + 9 color names; reject unknown |
| 5 | Required fields present | `Hash`, `UniqueOperationId`, 4 parts per layer |
| 6 | Ordered arrays preserve order | `layer_index`, `quadrant_index` monotonic per parent |
| 7 | Same input → same output | Import twice; compare row counts + checksum DTO |
| 8 | Runtime/debug IDs not domain keys | Assert no model uses `stable_id` or `instance_id` as PK/unique business key |
| 9 | No primary `raw_json` dump table | Schema/migration test: no table named `*raw*` with JSONField as sole payload |
| 10 | JSONField limited to audit/unknown | Only `unknown_property` / audit tables may store JSON extensions |
| 11 | Sampled objects traceable | Fixtures from indices 8, 51, 57 round-trip to expected slot counts |
| 12 | Layer count vs hash | `len(Layers) == Hash.count(':') + 1` for all 70 |
| 13 | PartCount invariant | All `quadrant_count == 4` |
| 14 | Duplicate stable_id allowed in source only | Import 70 `source_object_record` rows; `shape_recipe` still 70 |

## Pytest examples (sketch)

```python
def test_items_import_unique_hashes(items_fixture, importer):
    recipes = importer.run(items_fixture)
    assert recipes.count() == 70
    assert recipes.values("shape_hash").distinct().count() == 70

def test_sample_index_51_four_layers(items_fixture, importer):
    r = importer.get_by_operation_uid(1029)
    assert r.layers.count() == 4
    assert r.shape_hash.startswith("P-P-P-P-")

def test_empty_shape_slot_index_8_layer_0(items_fixture, importer):
    slots = ...  # layer 0, all is_empty_shape
    assert all(s.is_empty_shape for s in slots)
```

## Django management command (future)

`import_game_data --only items --verify` runs stages 1–11 and emits audit JSON.

## Golden fixture

- Subset: 3 sampled recipes + 1 single-layer (`CrCrCrCr`) checksum file under `tests/golden/game_data/items/`.

## CI gate

- Run on change to `documents/game_data/items.json` or import code.
- Fail if manifest hash in repo docs diverges from computed SHA-256.
