# Validation Plan — `building_variants.json`

> **pytest:** [documents/ai/manuals/testing.md](../../../documents/ai/manuals/testing.md) — `-q` / `--quiet` / `--tb=no` **forbidden**.

Path: `tests/unit/game_data/test_building_variant_import.py`

Fixtures from seed `20260521` indices 16, 103, 115.

---

## 1. No orphan FK rows

```python
def test_connector_has_variant(db, imported_variants):
    assert BuildingConnector.objects.filter(building_variant__isnull=True).count() == 0

def test_footprint_has_variant(db, imported_variants):
    assert BuildingFootprintTile.objects.filter(building_variant__isnull=True).count() == 0
```

---

## 2. Unique canonical IDs

```python
def test_internal_name_unique(db, imported_variants):
    names = list(BuildingVariant.objects.values_list("internal_name", flat=True))
    assert len(names) == 131 and len(set(names)) == 131

def test_stable_id_unique(db, imported_variants):
    ids = list(BuildingVariant.objects.values_list("stable_id", flat=True))
    assert len(ids) == len(set(ids))
```

---

## 3. All referenced IDs resolve

```python
@pytest.mark.parametrize("name", [
    "DisplayDefaultInternalVariant",
    "VirtualUnstackerDefaultInternalVariant",
    "WireDefault1UpForwardInternalVariant",
])
def test_sampled_variants_exist(db, imported_variants, name):
    assert BuildingVariant.objects.filter(internal_name=name).exists()

def test_group_embedded_names_resolve(db, imported_variants, group_embed_names_fixture):
    for name in group_embed_names_fixture:
        assert BuildingVariant.objects.filter(internal_name=name).exists()
```

---

## 4. Enum values valid

```python
def test_connector_role_enum(db, imported_variants):
    assert BuildingConnector.objects.exclude(connector_role__in=ConnectorRole.values).count() == 0

def test_io_channel_type_enum(db, imported_variants):
    assert BuildingConnector.objects.exclude(io_channel_type__in=IOChannelType.values).count() == 0
```

---

## 5. Required fields present

```python
@pytest.mark.parametrize("field", ["stable_id", "internal_name", "size_x", "size_y", "size_z"])
def test_variant_required(db, imported_variants, field):
    assert BuildingVariant.objects.filter(**{f"{field}__isnull": True}).count() == 0
```

---

## 6. Ordered arrays preserve order

```python
def test_connector_ordinals(db, variant_wire_1up):
    ordinals = list(
        BuildingConnector.objects.filter(building_variant=variant_wire_1up)
        .order_by("ordinal")
        .values_list("ordinal", flat=True)
    )
    assert ordinals == [0, 1]

def test_wire_1up_two_tiles(db, variant_wire_1up):
    assert BuildingFootprintTile.objects.filter(building_variant=variant_wire_1up).count() == 2
```

---

## 7. Same input gives same output

```python
def test_import_idempotent_131(db, import_twice):
    assert BuildingVariant.objects.count() == 131
    assert import_twice.duplicate_count == 0
```

---

## 8. Runtime identifiers not domain keys

```python
def test_no_building_definition_model():
    assert "BuildingDefinition" not in [m.__name__ for m in apps.get_models()]

def test_no_backing_field_columns(db):
    for f in BuildingVariant._meta.fields:
        assert "k__BackingField" not in f.name
```

---

## 9. No raw_json primary tables

```python
def test_variant_no_jsonfield(db):
    assert not any(isinstance(f, JSONField) for f in BuildingVariant._meta.fields)
```

---

## 10. JSONField only on unknown_property

```python
def test_jsonfield_audit_only():
    ...
```

---

## 11. Sampled objects traceable

```python
@pytest.mark.parametrize("index,name", [(16, "DisplayDefaultInternalVariant"), (103, "VirtualUnstackerDefaultInternalVariant"), (115, "WireDefault1UpForwardInternalVariant")])
def test_sampled_by_row_index(db, imported_variants, index, name):
    row = BuildingVariant.objects.get(source_row_index=index)
    assert row.internal_name == name
```

---

## 12. Cross-file integrity

```python
def test_mirrored_variant_count(db, imported_variants):
    assert BuildingVariant.objects.filter(is_mirrored=True).count() == 34

def test_source_guid_equals_internal_name(db, imported_variants):
    for v in BuildingVariant.objects.all():
        assert v.display_name_key == v.internal_name  # dump invariant
```

---

## CI

`pytest tests/unit/game_data/test_building_variant_import.py`
