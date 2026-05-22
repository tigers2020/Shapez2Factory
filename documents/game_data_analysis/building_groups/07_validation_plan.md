# Validation Plan — `building_groups.json`

> **pytest:** [documents/ai/manuals/testing.md](../../../documents/ai/manuals/testing.md) — `-q` / `--quiet` / `--tb=no` **금지**.

Suggested path: `tests/unit/game_data/test_building_group_import.py`

Fixtures: groups at indices 8, 51, 57 (seed `20260521`) + minimal `buildings` / `building_variants` slices.

---

## 1. No orphan FK rows

```python
def test_group_member_variant_fk(db, imported_groups):
    for m in BuildingGroupMember.objects.filter(internal_variant_name__isnull=False):
        assert BuildingVariant.objects.filter(internal_name=m.internal_variant_name).exists()

def test_group_member_cycle_resolved(db, imported_groups):
    assert BuildingGroupMember.objects.filter(
        member_resolution="cycle_ref", building_variant_id__isnull=True
    ).count() == 0
```

---

## 2. Unique canonical IDs

```python
def test_group_key_unique(db, imported_groups):
    keys = list(BuildingGroup.objects.values_list("group_key", flat=True))
    assert len(keys) == 67 and len(set(keys)) == 67

def test_registry_stable_id_unique(db, imported_groups):
    ids = list(BuildingGroup.objects.values_list("registry_stable_id", flat=True))
    assert len(ids) == len(set(ids))
```

---

## 3. All referenced IDs resolve

```python
def test_snapshot_hash_matches_buildings(import_service, groups_path, buildings_path):
    for dto in import_service.iter_groups(groups_path):
        assert dto.snapshot_content_hash == import_service.building_hash(
            buildings_path, dto.group_key
        )

@pytest.mark.parametrize("variant_name", [
    "CutterDefaultInternalVariant",
    "VirtualPainterDefaultInternalVariant",
    "VirtualCrystalGeneratorDefaultInternalVariant",
])
def test_sampled_variants_exist(db, imported_variants, variant_name):
    assert BuildingVariant.objects.filter(internal_name=variant_name).exists()
```

---

## 4. Enum values are valid

```python
def test_placement_mode_enum(db, imported_groups):
    allowed = {"CodeOverriden", "LinePerpendicular", "Single", "Area", "LineBoth", "LineParallel"}
    assert set(BuildingGroup.objects.values_list("placement_mode", flat=True)) <= allowed

def test_placement_rule_kind_mapped(db, imported_groups):
    assert BuildingPlacementRule.objects.exclude(rule_kind__in=PlacementRuleKind.values).count() == 0
```

---

## 5. Required fields are present

```python
@pytest.mark.parametrize("field", ["group_key", "registry_stable_id", "placement_mode"])
def test_group_required(db, imported_groups, field):
    assert BuildingGroup.objects.filter(**{f"{field}__isnull": True}).count() == 0
```

---

## 6. Ordered arrays preserve order

```python
def test_definitions_ordinal_contiguous(db, group_cutter):
    ordinals = list(
        BuildingGroupMember.objects.filter(building_group=group_cutter)
        .order_by("ordinal")
        .values_list("ordinal", flat=True)
    )
    assert ordinals == list(range(len(ordinals)))

def test_member_count_131(db, imported_groups):
    assert BuildingGroupMember.objects.count() == 131
```

---

## 7. Same input gives same output

```python
def test_import_idempotent_67_groups(db, import_twice):
    assert BuildingGroup.objects.count() == 67
    assert import_twice.duplicate_count == 0
```

---

## 8. Runtime/debug identifiers are not domain keys

```python
def test_no_building_definition_group_model_name():
    assert not any(m.__name__ == "BuildingDefinitionGroup" for m in apps.get_models())

def test_no_backing_field_column_names(db):
    for model in [BuildingGroup, BuildingGroupSimulationSetting]:
        for f in model._meta.fields:
            assert "k__BackingField" not in f.name
```

---

## 9. No primary raw_json dump tables

```python
def test_building_group_no_jsonfield(db):
    assert not any(isinstance(f, JSONField) for f in BuildingGroup._meta.fields)
```

---

## 10. JSONField only on unknown_property

```python
def test_jsonfield_allowed_only_on_unknown_property():
    ...
```

---

## 11. Sampled objects traceable

```python
@pytest.mark.parametrize("index,key", [(8, "CutterDefaultVariant"), (51, "VirtualPainterDefaultVariant"), (57, "VirtualCrystalGeneratorDefaultVariant")])
def test_sampled_groups(db, imported_groups, index, key):
    row = BuildingGroup.objects.get(source_row_index=index)
    assert row.group_key == key

def test_lazytext_parsed(db, group_cutter):
    loc = BuildingGroupLocalizationRef.objects.get(building_group=group_cutter)
    assert loc.title_key.endswith("CutterDefaultVariant.title")
```

---

## 12. Cross-file integrity

```python
def test_transport_building_count(db, imported_groups):
    assert BuildingGroup.objects.filter(is_transport_building=True).count() == 12

def test_groups_match_buildings_guid_set(import_service, groups_path, buildings_path):
    assert import_service.group_keys(groups_path) == import_service.building_guids(buildings_path)
```

---

## CI

| Tier | Command |
| ---- | ------- |
| Narrow | `pytest tests/unit/game_data/test_building_group_import.py` |
| Full | `pytest` when game_data importers exist |
