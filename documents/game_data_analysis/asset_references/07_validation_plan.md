# Validation Plan — `asset_references.json`

> **pytest:** [documents/ai/manuals/testing.md](../../../documents/ai/manuals/testing.md) — `-q` / `--quiet` / `--tb=no` **금지**.

Pytest-focused tests for import pipeline and schema invariants. Tests should run against **fixture slices** (3 sampled rows + minimal prefab/sprite/material targets) and **full bundle integration** (optional, marked slow).

Path suggestion: `tests/unit/game_data/test_asset_meta_reference_import.py`

---

## 1. No orphan FK rows

```python
def test_asset_meta_reference_content_fk_resolves(
    db, game_data_batch, imported_content_assets, imported_meta_references
):
    for row in AssetMetaReference.objects.all():
        if row.asset_kind == AssetKind.PREFAB:
            assert PrefabAsset.objects.filter(stable_id=row.content_stable_id).exists()
        elif row.asset_kind == AssetKind.SPRITE:
            assert SpriteAsset.objects.filter(stable_id=row.content_stable_id).exists()
        else:
            assert MaterialAsset.objects.filter(stable_id=row.content_stable_id).exists()
```

**Fixture:** use indices 65, 415, 463 from seed `20260521` plus matching prefab fixture rows.

---

## 2. Unique canonical IDs

```python
def test_meta_stable_id_unique(db, imported_meta_references):
    ids = list(AssetMetaReference.objects.values_list("meta_stable_id", flat=True))
    assert len(ids) == len(set(ids))

def test_logical_path_unique(db, imported_meta_references):
    paths = list(AssetMetaReference.objects.values_list("logical_path", flat=True))
    assert len(paths) == len(set(paths))
```

---

## 3. All referenced IDs resolve

```python
@pytest.mark.parametrize("asset_kind,expected_count", [
    (AssetKind.PREFAB, 764),
    (AssetKind.SPRITE, 61),
    (AssetKind.MATERIAL, 4),
])
def test_ref_stable_id_partition_counts(db, imported_meta_references, asset_kind, expected_count):
    assert AssetMetaReference.objects.filter(asset_kind=asset_kind).count() == expected_count

def test_zero_orphan_ref_stable_id(db, imported_meta_references, all_content_stable_ids):
    qs = AssetMetaReference.objects.exclude(content_stable_id__in=all_content_stable_ids)
    assert qs.count() == 0
```

---

## 4. Enum values are valid

```python
def test_asset_type_enum_only(db, imported_meta_references):
    assert (
        AssetMetaReference.objects.exclude(
            asset_kind__in=[AssetKind.PREFAB, AssetKind.SPRITE, AssetKind.MATERIAL]
        ).count()
        == 0
    )

def test_dump_source_type_constant(db, imported_meta_references):
    assert AssetMetaReference.objects.exclude(dump_source_type="asset.meta").count() == 0
```

---

## 5. Required fields are present

```python
REQUIRED = ["meta_stable_id", "content_stable_id", "asset_kind", "logical_path", "display_name_key"]

@pytest.mark.parametrize("field", REQUIRED)
def test_required_fields_non_null(db, imported_meta_references, field):
    assert AssetMetaReference.objects.filter(**{f"{field}__isnull": True}).count() == 0
```

---

## 6. Ordered arrays preserve order

```python
def test_source_row_index_matches_fixture_order(db, game_data_batch):
    rows = AssetMetaReference.objects.filter(import_batch=game_data_batch).order_by("source_row_index")
    assert list(rows.values_list("source_row_index", flat=True)) == list(range(rows.count()))

def test_deterministic_row_checksum_stable(import_service, asset_references_path, tmp_path):
    r1 = import_service.checksum(asset_references_path)
    r2 = import_service.checksum(asset_references_path)
    assert r1 == r2
```

---

## 7. Same input gives same output

```python
def test_import_idempotent_row_count(db, import_game_data_twice):
    assert AssetMetaReference.objects.count() == 829
    assert import_game_data_twice.duplicate_insert_count == 0

def test_import_idempotent_content_stable_ids(db, import_game_data_twice):
    first = set(AssetMetaReference.objects.values_list("content_stable_id", flat=True))
    # second run
    second = set(AssetMetaReference.objects.values_list("content_stable_id", flat=True))
    assert first == second
```

---

## 8. Runtime/debug identifiers are not domain keys

```python
def test_no_runtime_type_names_as_table_names():
    assert "asset_meta" not in [m._meta.db_table for m in apps.get_models()]  # example
    # Explicit: no model named UnityEngineObject

def test_source_type_name_not_used_as_pk(db, imported_meta_references):
    # PK must be meta_stable_id surrogate or meta_stable_id natural, never dump_source_type
    assert AssetMetaReference._meta.pk.name in ("id", "meta_stable_id")
```

---

## 9. No primary raw_json dump tables

```python
def test_domain_models_have_no_primary_jsonfield(db):
    for model in [AssetMetaReference, PrefabAsset, SpriteAsset, MaterialAsset]:
        json_fields = [f.name for f in model._meta.fields if isinstance(f, JSONField)]
        assert json_fields == [], f"{model.__name__} must not store domain arrays in JSONField"

def test_unknown_property_only_json_holder(db):
    # UnknownProperty may use JSONField; domain tables may not
    ...
```

---

## 10. JSONField limited to audit/unknown extension

```python
def test_jsonfield_allowed_only_on_unknown_property():
    allowed = {UnknownProperty}
    for model in apps.get_app_config("game_data").get_models():
        for field in model._meta.fields:
            if isinstance(field, JSONField):
                assert model in allowed
```

---

## 11. Sampled objects traceable to proposed schema

```python
@pytest.mark.parametrize("index,path", [
    (65, "ConstantSignal_Main_BakedMesh_Main_LOD0"),
    (415, "Pipe_2UpLeft_PartialFluid_5"),
    (463, "Rotator_90CW_ArrowsBlueprint_Mesh_LOD2"),
])
def test_sampled_rows_imported(db, imported_meta_references, index, path):
    row = AssetMetaReference.objects.get(source_row_index=index)
    assert row.logical_path == path
    assert row.meta_stable_id != row.content_stable_id
```

---

## 12. Cross-file integrity (integration)

```python
def test_meta_and_content_paths_align_for_prefabs(db, imported_meta_references):
    for meta in AssetMetaReference.objects.filter(asset_kind=AssetKind.PREFAB):
        prefab = PrefabAsset.objects.get(stable_id=meta.content_stable_id)
        assert meta.logical_path == prefab.logical_path
```

---

## Test fixtures

| Fixture file | Contents |
| ------------ | -------- |
| `tests/fixtures/game_data/asset_references_sample.json` | 3 sampled rows |
| `tests/fixtures/game_data/prefabs_sample.json` | Matching `ref_stable_id` targets |
| `tests/fixtures/game_data/manifest_snippet.json` | Hash + schema version |

Generate fixtures from seed `20260521` for reproducibility.

---

## CI placement

| Tier | Command | Scope |
| ---- | ------- | ----- |
| Narrow | `pytest tests/unit/game_data/test_asset_meta_reference_import.py` | fixtures |
| Full gate | `pytest` after all game_data importers exist | whole suite |

---

## Not in scope yet (defer until models exist)

- Django migrations lint
- mypy strict on DTO modules
- Golden hash of full 829-row import (slow; add to `tests/golden/` when importer lands)
