# game_data Domain-Complete Coverage — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove and enforce domain-complete import from `documents/game_data/` via coverage manifest, P1 provenance-preserving `ShapeRecipe` appearances, toolbar flatten equivalence tests, and classified audit paths — without JSONField blobs or ADR-004 snapshot expansion.

**Architecture:** A1 manifest + pytest gates (Phase 0) → P1 `ShapeRecipeSourceAppearance` with safe 1a–1d migrations (Phase 1) → Assembly/simulation classification (Phase 1) → manifest-driven promotion only on parity failure (Phase 2, optional) → domain doc (Phase 3).

**Tech Stack:** Python 3.12, Django 5, pytest-django, `GameDataImporter`, `documents/game_data/` fixture dir.

**Spec:** [`docs/superpowers/specs/2026-05-22-game-data-domain-complete-coverage-design.md`](../specs/2026-05-22-game-data-domain-complete-coverage-design.md)

**Worktree (recommended):** `feature/game-data-domain-complete-coverage` — isolate migrations from asteroid-lab WIP.

---

## File map

| File | Responsibility |
| ---- | -------------- |
| `django_apps/game_data/coverage/manifest.py` | Artifact path → `Disposition` enum |
| `django_apps/game_data/coverage/reason_codes.py` | `UnknownProperty` reason constants |
| `django_apps/game_data/models/shapes.py` | `ShapeRecipeSourceAppearance`; pair-UK on recipe |
| `django_apps/game_data/importers/shape_recipes.py` | Extracted provenance-preserving shape import (new) |
| `django_apps/game_data/importers/importer.py` | Delegate shapes; Assembly audit hook |
| `django_apps/game_data/importers/building_assembly_audit.py` | Scan `Assembly` → `UnknownProperty` |
| `scripts/audit_simulation_nested_paths.py` | One-off path frequency report |
| `tests/unit/game_data/test_shape_recipe_provenance.py` | P1 parity gates |
| `tests/unit/game_data/test_toolbar_closure.py` | Flatten equivalence |
| `tests/unit/game_data/test_domain_coverage_manifest.py` | Manifest registry smoke |
| `tests/unit/game_data/test_cross_references.py` | Add appearance FK asserts |
| `docs/domain/game_data_coverage.md` | Human disposition index (Phase 3) |

---

## Verify commands (repeat)

```powershell
cd f:\Python_Projects\shapez2Factory
python -m pytest tests/unit/game_data/test_shape_recipe_provenance.py -q --tb=short
python -m pytest tests/unit/game_data/test_toolbar_closure.py -q --tb=short
python -m ruff check django_apps/game_data tests/unit/game_data
```

Full slice after Phase 1:

```powershell
powershell -File scripts/test_fast.ps1
```

---

## Phase 0 — Manifest + red tests + audit script (no schema change)

### Task 0.1: Coverage package stub

**Files:**
- Create: `django_apps/game_data/coverage/__init__.py`
- Create: `django_apps/game_data/coverage/reason_codes.py`
- Create: `django_apps/game_data/coverage/manifest.py`

- [ ] **Step 1: Add reason codes**

```python
# django_apps/game_data/coverage/reason_codes.py
REFLECTION_METADATA = "REFLECTION_METADATA"
RUNTIME_DELEGATE = "RUNTIME_DELEGATE"
SIMULATION_FACTORY_STUB = "SIMULATION_FACTORY_STUB"
RUNTIME_UNITY_METADATA = "RUNTIME_UNITY_METADATA"
UNMAPPED_DOMAIN_CANDIDATE = "UNMAPPED_DOMAIN_CANDIDATE"
```

- [ ] **Step 2: Add manifest entries from spec table**

```python
# django_apps/game_data/coverage/manifest.py
from enum import Enum

class Disposition(str, Enum):
    PROMOTED = "promoted"
    CROSS_REF = "cross_ref"
    IGNORE_AUDIT = "ignore_audit"

MANIFEST: dict[str, tuple[Disposition, str]] = {
    "items.json:definition_snapshot.Definition.Layers": (Disposition.PROMOTED, "ShapeRecipe tree"),
    "items.json:catalog": (Disposition.CROSS_REF, "ShapeRecipeSourceAppearance"),
    "shapes.json:definition_snapshot.Definition": (Disposition.PROMOTED, "ShapeRecipe + FULL appearance"),
    "toolbar_entries.json:display_name_key": (Disposition.PROMOTED, "ToolbarTreeNode.tree_path"),
    "toolbar_entries.json:Children": (Disposition.CROSS_REF, "flattened to row paths"),
    "simulation_systems.json:ConnectableSimulations": (Disposition.PROMOTED, "ConnectableSimulation"),
    "simulation_systems.json:ISimulationSystem": (Disposition.IGNORE_AUDIT, RUNTIME_DELEGATE),
    "simulation_systems.json:SimulationFactory": (Disposition.IGNORE_AUDIT, SIMULATION_FACTORY_STUB),
    "buildings.json:definition_snapshot.Assembly": (Disposition.IGNORE_AUDIT, REFLECTION_METADATA),
    "buildings.json:PlacementRequirements": (Disposition.PROMOTED, "BuildingPlacementRule"),
    "buildings.json:Definitions": (Disposition.PROMOTED, "BuildingGroupMember"),
}
```

Import `REFLECTION_METADATA` etc. from `reason_codes` in manifest module.

- [ ] **Step 3: Run** `python -m ruff check django_apps/game_data/coverage`

---

### Task 0.2: Manifest test

**Files:**
- Create: `tests/unit/game_data/test_domain_coverage_manifest.py`

- [ ] **Step 1: Write test**

```python
import pytest
from django_apps.game_data.coverage.manifest import MANIFEST, Disposition

@pytest.mark.parametrize("key", list(MANIFEST.keys()))
def test_manifest_entry_has_disposition_and_note(key: str) -> None:
    disposition, note = MANIFEST[key]
    assert disposition in Disposition
    assert note.strip()
```

- [ ] **Step 2: Run** `python -m pytest tests/unit/game_data/test_domain_coverage_manifest.py -q` → PASS

---

### Task 0.3: Shape recipe provenance tests (expect RED until Phase 1)

**Files:**
- Create: `tests/unit/game_data/test_shape_recipe_provenance.py`
- Create: `tests/unit/game_data/_shape_json_helpers.py` (shared JSON counters)

- [ ] **Step 1: Helpers**

```python
# tests/unit/game_data/_shape_json_helpers.py
from __future__ import annotations
from typing import Any

def count_layers_and_slots(defn: dict[str, Any]) -> tuple[int, int]:
    layers = defn.get("Layers") or []
    slots = sum(len(layer.get("Parts") or []) for layer in layers)
    return len(layers), slots
```

- [ ] **Step 2: Write failing tests**

```python
# tests/unit/game_data/test_shape_recipe_provenance.py
from __future__ import annotations
import pytest
from django_apps.game_data.importers.source_loader import load_json
from django_apps.game_data.models import (
    ImportBatch,
    ShapeRecipe,
    ShapeRecipeLayer,
    ShapeQuadrantSlot,
    SourceObject,
)
from django_apps.game_data.models.shapes import ShapeRecipeSourceAppearance
from tests.unit.game_data._shape_json_helpers import count_layers_and_slots

@pytest.fixture
def items_rows(game_data_dir):
    return load_json(game_data_dir / "items.json")

def _overlap_keys(game_data_dir):
    shapes = load_json(game_data_dir / "shapes.json")
    items = load_json(game_data_dir / "items.json")
    def key(row):
        d = row.get("definition_snapshot", {}).get("Definition", row.get("definition_snapshot", {}))
        if not isinstance(d, dict):
            d = {}
        return (int(d.get("UniqueOperationId") or 0), str(d.get("Hash", "")))
    s_keys = {key(r) for r in shapes}
    i_keys = {key(r) for r in items}
    return s_keys & i_keys

@pytest.mark.django_db
def test_items_recipe_count_matches_source_appearances(
    imported_game_data_batch_module: ImportBatch,
    items_rows: list,
) -> None:
    batch = imported_game_data_batch_module
    assert len(items_rows) == 70
    assert ShapeRecipeSourceAppearance.objects.filter(
        import_batch=batch, catalog_source="items"
    ).count() == 70

@pytest.mark.django_db
def test_shape_recipe_no_catalog_source_overwrite(
    imported_game_data_batch_module: ImportBatch,
    game_data_dir,
) -> None:
    batch = imported_game_data_batch_module
    overlap = _overlap_keys(game_data_dir)
    if not overlap:
        pytest.skip("no FULL/ITEMS overlap in this dump")
    op_uid, shape_hash = next(iter(overlap))
    recipe = ShapeRecipe.objects.get(operation_uid=op_uid, shape_hash=shape_hash)
    apps = ShapeRecipeSourceAppearance.objects.filter(shape_recipe=recipe)
    assert apps.filter(catalog_source="full").exists()
    assert apps.filter(catalog_source="items").exists()

@pytest.mark.django_db
def test_shape_recipe_source_appearance_full_items_overlap(
    imported_game_data_batch_module: ImportBatch,
    game_data_dir,
) -> None:
    batch = imported_game_data_batch_module
    overlap = _overlap_keys(game_data_dir)
    if not overlap:
        pytest.skip("no overlap")
    op_uid, shape_hash = next(iter(overlap))
    recipe = ShapeRecipe.objects.get(operation_uid=op_uid, shape_hash=shape_hash)
    sources = set(
        ShapeRecipeSourceAppearance.objects.filter(shape_recipe=recipe).values_list(
            "catalog_source", flat=True
        )
    )
    assert sources == {"full", "items"}

@pytest.mark.django_db
def test_items_layer_slot_parity_by_source_object(
    imported_game_data_batch_module: ImportBatch,
    items_rows: list,
) -> None:
    batch = imported_game_data_batch_module
    for i, row in enumerate(items_rows):
        src = SourceObject.objects.get(
            import_batch=batch, source_file="items.json", source_row_index=i
        )
        defn = row.get("definition_snapshot", {}).get("Definition", {})
        exp_layers, exp_slots = count_layers_and_slots(defn)
        appearance = ShapeRecipeSourceAppearance.objects.get(
            import_batch=batch, artifact_filename="items.json", source_row_index=i
        )
        recipe = appearance.shape_recipe
        assert ShapeRecipeLayer.objects.filter(shape_recipe=recipe).count() == exp_layers
        assert ShapeQuadrantSlot.objects.filter(layer__shape_recipe=recipe).count() == exp_slots
```

- [ ] **Step 3: Run** `python -m pytest tests/unit/game_data/test_shape_recipe_provenance.py -q`  
  Expected: **FAIL** (`ShapeRecipeSourceAppearance` missing or import not creating rows)

---

### Task 0.4: Toolbar closure tests

**Files:**
- Create: `tests/unit/game_data/test_toolbar_closure.py`

- [ ] **Step 1: Implement helpers mirroring `toolbar_node_kind`**

```python
def _source_paths(game_data_dir: Path) -> list[str]:
    rows = load_json(game_data_dir / "toolbar_entries.json")
    return sorted(str(r["display_name_key"]) for r in rows if r.get("display_name_key"))

def _parent_edges(paths: set[str]) -> set[tuple[str, str]]:
    edges: set[tuple[str, str]] = set()
    for path in paths:
        if path == "root":
            continue
        parent = parent_path_from_tree_path(path)
        assert parent is not None
        edges.add((parent, path))
    return edges
```

- [ ] **Step 2: Tests**

```python
@pytest.mark.django_db
def test_toolbar_path_closure(game_data_dir, imported_game_data_batch_module):
    expected = set(_source_paths(game_data_dir))
    actual = set(ToolbarTreeNode.objects.values_list("tree_path", flat=True))
    assert actual == expected

@pytest.mark.django_db
def test_toolbar_parent_child_edges(game_data_dir, imported_game_data_batch_module):
    paths = set(_source_paths(game_data_dir))
    expected_edges = _parent_edges(paths)
    nodes = {n.tree_path: n for n in ToolbarTreeNode.objects.all()}
    actual_edges = set()
    for child_path, node in nodes.items():
        if node.parent_id is None:
            continue
        parent_path = node.parent.tree_path
        actual_edges.add((parent_path, child_path))
    assert actual_edges == expected_edges

@pytest.mark.django_db
def test_toolbar_no_dangling_parent(game_data_dir):
    paths = set(_source_paths(game_data_dir))
    for path in paths:
        if path == "root":
            continue
        parent = parent_path_from_tree_path(path)
        assert parent in paths

@pytest.mark.django_db
def test_toolbar_acyclic(imported_game_data_batch_module):
    nodes = list(ToolbarTreeNode.objects.select_related("parent"))
    by_id = {n.id: n for n in nodes}
    for node in nodes:
        seen: set[int] = set()
        cur = node
        while cur.parent_id is not None:
            assert cur.parent_id not in seen
            seen.add(cur.id)
            cur = by_id[cur.parent_id]
```

- [ ] **Step 3: Run** `python -m pytest tests/unit/game_data/test_toolbar_closure.py -q` → expect PASS (mostly) or fix importer gaps if fail

---

### Task 0.5: Simulation nested path audit script

**Files:**
- Create: `scripts/audit_simulation_nested_paths.py`

- [ ] **Step 1: Script** (stdout TSV: `path\tcount\tmax_list_len`)

Walk `documents/game_data/simulation_systems.json` recursively; emit paths containing `ChainPosition`, `TileBased`, `Simulation`, `_Lanes` with counts; cap output at 200 lines.

- [ ] **Step 2: Run** `python scripts/audit_simulation_nested_paths.py > documents/game_data_analysis/simulation_systems/_nested_path_audit.tsv`

- [ ] **Step 3: Human/classifier** — add high-count paths to `MANIFEST` as `IGNORE_AUDIT` or `PROMOTED` before Phase 2

**Phase 0 gate:** manifest test PASS; provenance tests RED; toolbar closure PASS.

**Commit bundle 0:** `test(game_data): coverage manifest and toolbar closure gates`

---

## Phase 1 — P1 appearances + safe migrations

### Task 1.1: Migration 1a — `ShapeRecipeSourceAppearance` model

**Files:**
- Modify: `django_apps/game_data/models/shapes.py`
- Modify: `django_apps/game_data/models/__init__.py`
- Create: migration `00XX_shape_recipe_source_appearance.py`

- [ ] **Step 1: Model**

```python
class ShapeRecipeSourceAppearance(models.Model):
    class CatalogSource(models.TextChoices):
        FULL = "full", "shapes.json"
        ITEMS = "items", "items.json"

    shape_recipe = models.ForeignKey(
        ShapeRecipe, on_delete=models.CASCADE, related_name="source_appearances"
    )
    source_object = models.ForeignKey(
        SourceObject, on_delete=models.PROTECT, related_name="shape_recipe_appearances"
    )
    import_batch = models.ForeignKey(
        ImportBatch, on_delete=models.CASCADE, related_name="shape_recipe_appearances"
    )
    catalog_source = models.CharField(max_length=16, choices=CatalogSource.choices)
    artifact_filename = models.CharField(max_length=64)
    source_row_index = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["import_batch", "artifact_filename", "source_row_index"],
                name="uq_shape_appearance_batch_file_row",
            ),
        ]
```

Keep `ShapeRecipe.catalog_source` field **unchanged** in 1a.

- [ ] **Step 2:** `python manage.py makemigrations game_data` → apply 1a

---

### Task 1.2: Migration 1b — backfill appearances

- [ ] **Step 1: Data migration** — for each `ShapeRecipe` with `catalog_source` + `source_object_id`:

```python
ShapeRecipeSourceAppearance.objects.get_or_create(
    import_batch=recipe.import_batch,
    artifact_filename="shapes.json" if recipe.catalog_source == "full" else "items.json",
    source_row_index=recipe.source_object.source_row_index,
    defaults={
        "shape_recipe": recipe,
        "source_object": recipe.source_object,
        "catalog_source": recipe.catalog_source,
    },
)
```

- [ ] **Step 2: Run migration** on dev DB; spot-check overlap recipes have two rows after re-import test

---

### Task 1.3: Provenance-preserving importer

**Files:**
- Create: `django_apps/game_data/importers/shape_recipes.py`
- Modify: `django_apps/game_data/importers/importer.py`

- [ ] **Step 1: Extract `import_shape_rows(ctx, *, catalog_source, filename, rows)`**

Logic:

1. Upsert `ShapeRecipe` by `(operation_uid, shape_hash)` — **do not** set `catalog_source` in defaults after Phase 1b (or set deprecated field only when creating new row for backward compat during 1c).
2. `ShapeRecipeSourceAppearance.objects.update_or_create(import_batch, artifact_filename, source_row_index, ...)`.
3. Refresh layers/slots (idempotent geometry).
4. After all rows for file: set `recipe.source_object` to primary: first linked appearance with `catalog_source=full`, else `items`.

- [ ] **Step 2: Wire importer** — replace `_import_shapes` body with call to `shape_recipes.import_shape_rows`.

- [ ] **Step 3: Run provenance tests** → PASS

---

### Task 1.4: Pair-UK verification + migration 1d prep

- [ ] **Step 1: Add one-off test** `test_shape_recipe_pair_unique_matches_dump` — no duplicate `(operation_uid, shape_hash)` in shapes∪items JSON.

- [ ] **Step 2: If pass** — migration 1c: add `UniqueConstraint(fields=["operation_uid", "shape_hash"])`; remove separate `unique=True` on columns **only if** no duplicates.

- [ ] **Step 3: migration 1d** — `RemoveField(ShapeRecipe, catalog_source)`; update admin `list_display` / filters to use appearances.

---

### Task 1.5: Cross-ref test for appearances

**Files:**
- Modify: `tests/unit/game_data/test_cross_references.py`

- [ ] **Step 1:**

```python
@pytest.mark.django_db
def test_shape_recipe_appearance_links_source_object(imported_game_data_batch_module):
    app = ShapeRecipeSourceAppearance.objects.select_related(
        "shape_recipe", "source_object"
    ).first()
    assert app is not None
    assert app.source_object.source_file == app.artifact_filename
```

---

### Task 1.6: Building Assembly → UnknownProperty

**Files:**
- Create: `django_apps/game_data/importers/building_assembly_audit.py`
- Modify: `django_apps/game_data/importers/importer.py` — call after `_upsert_building_group`

- [ ] **Step 1: Walk `definition_snapshot` for keys `Assembly`, `DeclaredMembers`**

Record via `ctx.record_unknown(..., reason_code=REFLECTION_METADATA, classification="assembly_reflection")` with capped depth (do not explode 21k rows — record prefix paths only or sample + count bump in summary).

**Design choice:** Record **one UnknownProperty per building group** for path `definition_snapshot.Assembly` with hash of subtree, not per member — keeps row count bounded. Test: `test_building_assembly_classified_as_reflection` asserts ≥1 `REFLECTION_METADATA` for buildings.json owners.

---

### Task 1.7: Admin + import_layer

**Files:**
- Modify: `django_apps/game_data/admin.py` — inline `ShapeRecipeSourceAppearance` on `ShapeRecipeAdmin`
- Modify: `django_apps/game_data/import_layer.py` — register model label

- [ ] **Step 1: Read-only inline** appearances list_display: `catalog_source`, `artifact_filename`, `source_row_index`

---

**Phase 1 gate:**

```powershell
python -m pytest tests/unit/game_data/test_shape_recipe_provenance.py tests/unit/game_data/test_toolbar_closure.py tests/unit/game_data/test_cross_references.py -q
python -m ruff check django_apps/game_data
python -m mypy django_apps/game_data
```

**Commit bundles:** 1a model · 1b backfill · 1c importer · 1d drop catalog_source · assembly audit

---

## Phase 2 — Manifest-driven promotion (gated)

**Only if** audit script + parity tests identify a `PROMOTED` path with no ORM home.

- [ ] **Task 2.1:** Update `MANIFEST` from `_nested_path_audit.tsv` review
- [ ] **Task 2.2:** Add failing test for specific path row counts
- [ ] **Task 2.3:** Minimal model + importer (e.g. `SimulationTileChainPosition` **only if** classified promoted)

If audit classifies `ChainPositions` as `IGNORE_AUDIT`, Phase 2 is **skip** — document in `game_data_coverage.md`.

---

## Phase 3 — Documentation

- [x] **Task 3.1:** Create `docs/domain/game_data_coverage.md` — copy manifest table + principles block from spec
- [x] **Task 3.2:** Link from `docs/domain/README.md` and `documents/ai/manuals/django.md` import section
- [x] **Task 3.3:** Update spec status → Phase 0–1d + 3 implemented (commit `097e2a28`)

Optional: `docs/adr/ADR-005-game-data-coverage-boundary.md` (defer unless snapshot/solver touch needed).

---

## ADR-004 explicit non-tasks

- [ ] Do **not** modify `django_apps/game_data/snapshots/builder.py` for appearances
- [ ] Do **not** add `ShapeRecipeSourceAppearance` to `AsteroidGameDataSnapshot`

---

## Plan self-review

| Spec requirement | Task |
| ---------------- | ---- |
| P1 provenance | 0.3, 1.2–1.3 |
| Pair UK | 1.4 |
| Appearance UK `(batch, file, row)` | 1.1 |
| Migration 1a–1d | 1.1–1.4 |
| `source_object` primary rule | 1.3 |
| Toolbar closure | 0.4 |
| Simulation audit-first | 0.5, Phase 2 gated |
| Assembly ignore | 1.6 |
| Manifest | 0.1–0.2 |
| ADR-004 boundary | Non-tasks section |

No TBD steps. Overlap helper uses same key extraction as importer will.

---

## Progress dashboard

| Phase | Status |
| ----- | ------ |
| 0 Manifest + red/green tests + audit script | **Done** (2026-05-22) |
| 1 P1 migrations + importer + assembly audit | **Done** — `0021`–`0024` |
| 1.4 pair-UK `(operation_uid, shape_hash)` | **Done** — `f13fb90e`, migration `0024` |
| 1d `catalog_source` removal | **Done** |
| PR merge | **Done** — [#25](https://github.com/tigers2020/Shapez2Factory/pull/25) → `master` (`70c0da76`) |
| 2 Conditional promotion | **Deferred** — audit TSV human review required |
| 3 Docs | **Done** — `docs/domain/game_data_coverage.md` |
