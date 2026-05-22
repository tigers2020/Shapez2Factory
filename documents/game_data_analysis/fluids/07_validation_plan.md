# Validation Plan — `fluids.json`

> **pytest:** [documents/ai/manuals/testing.md](../../../documents/ai/manuals/testing.md) — `-q` / `--quiet` / `--tb=no` **금지**.

Path: `tests/unit/game_data/test_fluid_color_import.py`

---

## 1. No orphan FK rows

N/A for flat palette. Post-import:

```python
def test_items_reference_known_fluid_colors(db, imported_items, imported_fluid_colors):
    unknown = imported_items.color_names - set(
        FluidColor.objects.values_list("color_name", flat=True)
    )
    assert unknown == set()
```

---

## 2. Unique canonical IDs

```python
def test_color_name_unique(db, imported_fluid_colors):
    assert FluidColor.objects.count() == 9
    names = list(FluidColor.objects.values_list("color_name", flat=True))
    assert len(names) == len(set(names))

def test_stable_id_not_unique_in_dump(import_service, fluids_path):
    ids = import_service.stable_ids(fluids_path)
    assert len(set(ids)) == 1  # documented dump quirk
```

---

## 3. All referenced IDs resolve

```python
EXPECTED = {"Red", "Green", "Blue", "Cyan", "Magenta", "Yellow", "White", "Black", "Uncolored"}

def test_all_palette_colors_imported(db, imported_fluid_colors):
    assert set(FluidColor.objects.values_list("color_name", flat=True)) == EXPECTED
```

---

## 4. Enum values valid

```python
def test_fluid_kind_constant(db, imported_fluid_colors):
    assert FluidColor.objects.exclude(fluid_kind=FluidKind.COLOR_PAINT).count() == 0
```

---

## 5. Required fields

```python
def test_color_name_non_null(db, imported_fluid_colors):
    assert FluidColor.objects.filter(color_name__isnull=True).count() == 0
```

---

## 6. Ordered arrays preserve order

```python
def test_source_row_index_order(db, imported_fluid_colors):
    rows = list(FluidColor.objects.order_by("source_row_index").values_list("color_name", flat=True))
    assert rows[0] == "Red" and rows[-1] == "Uncolored"
```

---

## 7. Idempotent import

```python
def test_import_idempotent(db, import_twice):
    assert FluidColor.objects.count() == 9
```

---

## 8. Runtime names not domain keys

```python
def test_no_color_fluid_model():
    assert "ColorFluid" not in [m.__name__ for m in apps.get_models()]
```

---

## 9. No raw JSON / JSONField on domain table

```python
def test_fluid_color_no_jsonfield(db):
    assert not any(isinstance(f, JSONField) for f in FluidColor._meta.fields)
```

---

## 11. Sampled traceability

```python
@pytest.mark.parametrize("index,name", [(1, "Green"), (3, "Cyan"), (6, "Yellow")])
def test_sampled_rows(db, imported_fluid_colors, index, name):
    assert FluidColor.objects.get(source_row_index=index).color_name == name
```

---

## CI

`pytest tests/unit/game_data/test_fluid_color_import.py`
