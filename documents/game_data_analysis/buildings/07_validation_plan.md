# Validation Plan — `buildings.json`

> **pytest:** [`documents/ai/manuals/testing.md`](../../../documents/ai/manuals/testing.md) — `-q` / `--quiet` / `--tb=no` **금지**.

Path: `tests/unit/game_data/test_building_import.py`

Fixtures: indices 8, 51, 57 (seed `20260521`).

---

## 1. No orphan FK rows

```python
def test_building_group_member_variant_fk(db, imported_buildings):
    for m in BuildingGroupMember.objects.filter(internal_variant_name__isnull=False):
        assert BuildingVariant.objects.filter(internal_name=m.internal_variant_name).exists()

def test_cycle_members_resolved(db, imported_buildings):
    assert BuildingGroupMember.objects.filter(
        member_resolution="cycle_ref", building_variant_id__isnull=True
    ).count() == 0
```

---

## 2. Unique canonical IDs

```python
def test_group_key_unique(db, imported_buildings):
    keys = list(Building.objects.values_list("group_key", flat=True))
    assert len(keys) == 67 and len(set(keys)) == 67

def test_stable_id_unique(db, imported_buildings):
    ids = list(Building.objects.values_list("stable_id", flat=True))
    assert len(ids) == len(set(ids))
```

---

## 3. All referenced IDs resolve

```python
def test_named_members_exist_in_variants(db, imported_buildings, imported_variants):
    for name in BuildingGroupMember.objects.exclude(internal_variant_name="").values_list(
        "internal_variant_name", flat=True
    ):
        assert BuildingVariant.objects.filter(internal_name=name).exists()
```

---

## 4–12. Enum, required fields, order, idempotency, runtime, JSONField, samples, cross-file

See patterns in `building_groups/07_validation_plan.md` — same invariants with `Building` / `BuildingGroupMember` table names.

**Sampled traceability:**

| Index | `group_key` |
| ----- | ----------- |
| 8 | `CutterDefaultVariant` |
| 51 | `VirtualPainterDefaultVariant` |
| 57 | `VirtualCrystalGeneratorDefaultVariant` |

```python
@pytest.mark.parametrize("index,key", [(8, "CutterDefaultVariant"), (51, "VirtualPainterDefaultVariant"), (57, "VirtualCrystalGeneratorDefaultVariant")])
def test_sampled_buildings(db, imported_buildings, index, key):
    row = Building.objects.get(source_row_index=index)
    assert row.group_key == key
```

```python
def test_snapshot_hash_matches_building_groups(import_service, buildings_path, groups_path):
    assert import_service.building_group_snapshot_pairs(buildings_path, groups_path) == 67
```

---

## CI

`pytest tests/unit/game_data/test_building_import.py`
