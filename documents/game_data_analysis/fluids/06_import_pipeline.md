# Import Pipeline Plan — `fluids.json`

Small file (9 rows). Import early in pipeline (no FK prerequisites except manifest).

---

## Stages 1–12

### 1. Load JSON

- Parse array length **9**.

### 2. Validate structure

| Rule | Failure |
| ---- | ------- |
| 9 elements | Hard fail if count changes |
| Required keys per row | Hard fail |
| `Color.name` present and unique | Hard fail |
| `stable_id` constant across rows | **Warn** (expected) |
| `$type == ColorFluid` | Warn on drift |
| Extra keys | `unknown_property` |

### 3. Normalize

- `color_name` ← `Color.name` (PascalCase preserved to match items dump).
- `fluid_kind` ← `color_paint`.
- `solver_color_code` ← lookup table from `COLOR_KINDS` (validate all names map except Black).
- `is_primary_source` ← `name in {Red, Green, Blue}`.
- `source_row_index` ← enumerate.

### 4. Register batch

- Manifest hash for `fluids.json`.

### 5. Random sample audit

- Seed `20260521`, indices `[1, 3, 6]` → Green, Cyan, Yellow.

### 6. DTO

```python
@dataclass(frozen=True)
class FluidColorDTO:
    color_name: str
    fluid_kind: str
    solver_color_code: str | None
    is_primary_source: bool
    dump_stable_id: str
    unity_instance_id: int | None
    source_row_index: int
```

### 7. Validate DTOs

- All nine catalog names present.
- `solver_color_code` unique where not null.
- Black handling documented if unmapped.

### 8. Upsert root

- `fluid_color` upsert on **`color_name`** (not `stable_id`).

### 9. Upsert children

- None (flat palette).

### 10. Resolve FKs

- Post-import: scan `items.json` import for `Color.name` ⊆ `fluid_color.color_name`.

### 11. Invariants

| Check | Expected |
| ----- | -------- |
| Row count | 9 |
| Unique `color_name` | 9 |
| `source_row_index` | 0..8 |
| Duplicate `stable_id` allowed | 9 identical `dump_stable_id` values |

### 12. Audit

```json
{
  "file": "fluids.json",
  "fluid_colors_upserted": 9,
  "duplicate_stable_id_warning": true,
  "unmapped_solver_codes": ["Black"]
}
```

---

## Idempotency

Upsert on `color_name`; replace scalars; stable `source_row_index` ordering.

---

## Order in bundle import

```text
import_fluid_colors      # this file — early
import_items             # validate Color.name FK
import_shapes
```
