# Validation Plan — `materials.json`

> **pytest:** [documents/ai/manuals/testing.md](../../../documents/ai/manuals/testing.md) — `-q` / `--quiet` / `--tb=no` **forbidden**.

## Module (proposed)

`tests/unit/game_data_import/test_materials_import.py`

## Required checks

| # | Invariant | Test |
| - | --------- | ---- |
| 1 | No orphan FK rows | Meta material refs without `material_asset` |
| 2 | Unique canonical IDs | 4 unique `stable_id` and `material_path` |
| 3 | Referenced IDs resolve | All material `ref_stable_id` in asset_references |
| 4 | Enum values valid | `asset_kind=material` count = 4 |
| 5 | Required fields present | All envelope keys |
| 6 | Ordered arrays preserve order | `source_row_index` 0..3 stable |
| 7 | Same input → same output | Double import identical |
| 8 | Runtime IDs not domain keys | No PK `UnityEngine.Object` |
| 9 | No raw_json primary table | Schema guard |
| 10 | JSONField audit-only | `unknown_property` only |
| 11 | Sampled objects traceable | Indices 0,1,2 paths match golden |
| 12 | Manifest hash gate | File bytes match manifest |
| 13 | Path field alignment | `material_path == source_path` for all 4 |
| 14 | Import order | materials before asset_references |

## Example tests

```python
def test_materials_four_unique_stable_ids(materials_fixture, importer):
    rows = importer.import_materials(materials_fixture)
    assert rows.count() == 4
    assert rows.values("stable_id").distinct().count() == 4

def test_sample_index_1_mixer_fluid(materials_fixture, importer):
    m = importer.get_by_index(1)
    assert m.material_path == "MixerFluidMaterial"
```

## Golden fixture

`tests/golden/game_data/materials/checksum.json` — stable_id list + manifest hash.

## CI

- Run when `materials.json` or `asset_references.json` changes.
