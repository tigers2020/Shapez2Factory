# game_data pytest dump-only Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `documents/game_data` full-bundle pytest usage with pinned `game_data_backup/game_data_dump.json` via `loaddata`, delete Tier A importer tests from unit pytest, and document Tier A as manual CI / release gate.

**Architecture:** Centralize seeding in `tests/unit/game_data/fixtures.py` (app-local flush → `loaddata` → pinned `ImportBatch` assert). ORM contract tests read `_dump_expectations.py` constants bound to `PINNED_MANIFEST_HASH`. Slice importer tests keep `tests/fixtures/game_data/*.json` only.

**Tech Stack:** Python 3.12, Django 5, pytest-django, `loaddata`, existing `_flush_committed_game_data`

**Spec:** [`docs/superpowers/specs/2026-05-22-game-data-pytest-dump-only-design.md`](../specs/2026-05-22-game-data-pytest-dump-only-design.md)

---

## File map

| File | Action |
| ---- | ------ |
| `tests/unit/game_data/_dump_expectations.py` | **Create** — pinned hash + counts |
| `tests/unit/game_data/fixtures.py` | **Rewrite** — loaddata module fixture, CI fail |
| `tests/unit/game_data/test_import_idempotency.py` | **Delete** |
| `tests/unit/game_data/test_import_game_data_verify.py` | **Delete** |
| `tests/unit/game_data/test_toolbar_closure.py` | **Modify** — ORM-only |
| `tests/unit/game_data/test_toolbar_tree.py` | **Modify** — drop JSON/re-import |
| `tests/unit/game_data/test_shape_recipe_provenance.py` | **Modify** — ORM-only |
| `tests/unit/game_data/test_simulation_systems_import.py` | **Modify** — remove full 180-row test |
| `tests/unit/game_data/test_simulation_speed_import.py` | **Modify** — remove full JSON scan test |
| `docs/runbooks/game_data_tier_a_release_gate.md` | **Create** |
| `docs/domain/game_data_coverage.md` | **Modify** — pytest Tier B |
| `documents/ai/manuals/testing.md` | **Modify** — dump fixture section |
| `docs/runbooks/game_data_snapshot_deploy.md` | **Modify** — link Tier A gate |
| `docs/superpowers/specs/2026-05-23-pytest-slim-optimization-design.md` | **Modify** — ownership row |

---

### Task 1: Pinned expectations module

**Files:**
- Create: `tests/unit/game_data/_dump_expectations.py`

- [ ] **Step 1: Create expectations file**

```python
"""Pinned ORM counts for game_data_backup/game_data_dump.json.

All values are valid only when ImportBatch.manifest_self_hash == PINNED_MANIFEST_HASH.
Regenerate via docs/runbooks/game_data_tier_a_release_gate.md when the dump changes.
"""

from __future__ import annotations

PINNED_MANIFEST_HASH = (
    "sha256:a7f71325bb779ff6c2a1665ff6c9fa3067943cc6335a7926567d2ee76be8dd09"
)

PINNED_IMPORT_BATCH_PK = 1
PINNED_BATCH_NAME = "default"

TOOLBAR_TREE_NODE_COUNT = 204
TOOLBAR_ELEMENT_COUNT = 142
TOOLBAR_ACTION_KIND_NODE_COUNT = 142

SHAPE_RECIPE_COUNT = 1170
ITEMS_SOURCE_APPEARANCE_COUNT = 70
FULL_SOURCE_APPEARANCE_COUNT = 1170

SIMULATION_SYSTEM_COUNT = 180
```

- [ ] **Step 2: Run ruff**

Run: `python -m ruff check tests/unit/game_data/_dump_expectations.py`  
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/unit/game_data/_dump_expectations.py
git commit -m "test(game_data): add pinned dump expectations for Tier B fixture"
```

---

### Task 2: Rewrite shared fixtures (loaddata + CI fail)

**Files:**
- Modify: `tests/unit/game_data/fixtures.py`

- [ ] **Step 1: Replace fixture implementation**

Full new content for `fixtures.py`:

```python
"""Shared fixtures for game_data unit tests (Tier B pinned dump)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from django.core.management import call_command

from django_apps.game_data.models import ImportBatch
from tests.unit.game_data._dump_expectations import (
    PINNED_BATCH_NAME,
    PINNED_IMPORT_BATCH_PK,
    PINNED_MANIFEST_HASH,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_GAME_DATA_DUMP = _REPO_ROOT / "game_data_backup" / "game_data_dump.json"


def _require_game_data_dump(path: Path) -> None:
    if path.is_file():
        return
    if os.environ.get("CI") or os.environ.get("REQUIRE_GAME_DATA_DUMP") == "1":
        pytest.fail(f"Missing pinned game_data dump: {path}")
    pytest.skip(f"Missing pinned game_data dump: {path}")


def _flush_committed_game_data(django_db_blocker: Any) -> None:
    """Delete all game_data app rows (module teardown / pre-loaddata). Never global flush."""
    from django.apps import apps
    from django.db import connection

    tables = [model._meta.db_table for model in apps.get_app_config("game_data").get_models()]
    with django_db_blocker.unblock():
        with connection.cursor() as cursor:
            if connection.vendor == "sqlite":
                cursor.execute("PRAGMA foreign_keys = OFF")
            for table in tables:
                cursor.execute(f'DELETE FROM "{table}"')
            if connection.vendor == "sqlite":
                cursor.execute("PRAGMA foreign_keys = ON")


def _assert_pinned_import_batch() -> ImportBatch:
    batch = ImportBatch.objects.get(pk=PINNED_IMPORT_BATCH_PK)
    assert batch.batch_name == PINNED_BATCH_NAME
    assert batch.manifest_self_hash == PINNED_MANIFEST_HASH
    return batch


@pytest.fixture(scope="module")
def game_data_dump_path() -> Path:
    _require_game_data_dump(_GAME_DATA_DUMP)
    return _GAME_DATA_DUMP


@pytest.fixture(scope="module")
def imported_game_data_batch_module(
    game_data_dump_path: Path,
    django_db_setup: None,
    django_db_blocker,
) -> Iterator[ImportBatch]:
    """One loaddata per test module; app-local flush only (no global flush)."""
    with django_db_blocker.unblock():
        _flush_committed_game_data(django_db_blocker)
        call_command("loaddata", str(game_data_dump_path), verbosity=0)
        batch = _assert_pinned_import_batch()
    yield batch
    _flush_committed_game_data(django_db_blocker)


@pytest.fixture
def imported_game_data_batch(
    imported_game_data_batch_module: ImportBatch,
    db: None,
) -> ImportBatch:
    return imported_game_data_batch_module


@pytest.fixture
def imported_batch(imported_game_data_batch: ImportBatch) -> ImportBatch:
    return imported_game_data_batch


@pytest.fixture(scope="module")
def imported_batch_module(imported_game_data_batch_module: ImportBatch) -> ImportBatch:
    return imported_game_data_batch_module
```

- [ ] **Step 2: Smoke one test that uses module fixture**

Run: `python -m pytest tests/unit/game_data/test_cross_references.py::test_asset_meta_links_content -v`  
Expected: PASS (or FAIL with loaddata error — fix before continuing)

- [ ] **Step 3: ruff**

Run: `python -m ruff check tests/unit/game_data/fixtures.py`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add tests/unit/game_data/fixtures.py
git commit -m "test(game_data): load pinned dump via loaddata module fixture"
```

---

### Task 3: Delete Tier A importer unit tests

**Files:**
- Delete: `tests/unit/game_data/test_import_idempotency.py`
- Delete: `tests/unit/game_data/test_import_game_data_verify.py`

- [ ] **Step 1: Delete files**

```bash
git rm tests/unit/game_data/test_import_idempotency.py tests/unit/game_data/test_import_game_data_verify.py
```

- [ ] **Step 2: Confirm no imports reference deleted modules**

Run: `python -m pytest tests/unit/game_data/ --collect-only`  
Expected: collect OK, no ImportError

- [ ] **Step 3: Commit**

```bash
git commit -m "test(game_data): drop Tier A import/verify from unit pytest"
```

---

### Task 4: Remove full-bundle tests from simulation modules

**Files:**
- Modify: `tests/unit/game_data/test_simulation_systems_import.py`
- Modify: `tests/unit/game_data/test_simulation_speed_import.py`

- [ ] **Step 1: Delete `test_full_simulation_systems_import_180_rows`**

Remove the entire function (lines ~154–170) and remove unused imports: `GameDataImporter`, `Path` if only used there.

Keep `min_sim_rows` fixture path:

`Path(__file__).resolve().parents[2] / "fixtures" / "game_data" / "simulation_systems_min.json"`

- [ ] **Step 2: Delete `test_full_dump_speed_key_counts`**

Remove entire function in `test_simulation_speed_import.py` (~lines 120–end of test). Remove `json` / `game_data_dir` imports if unused.

- [ ] **Step 3: Run slice tests still pass**

Run: `python -m pytest tests/unit/game_data/test_simulation_systems_import.py tests/unit/game_data/test_simulation_speed_import.py -v`  
Expected: PASS (slow tests may need `-m slow` if marked)

- [ ] **Step 4: Commit**

```bash
git add tests/unit/game_data/test_simulation_systems_import.py tests/unit/game_data/test_simulation_speed_import.py
git commit -m "test(game_data): remove full-bundle simulation tests from unit pytest"
```

---

### Task 5: Rewrite toolbar tests (ORM + expectations)

**Files:**
- Modify: `tests/unit/game_data/test_toolbar_closure.py`
- Modify: `tests/unit/game_data/test_toolbar_tree.py`

- [ ] **Step 1: Rewrite `test_toolbar_closure.py`**

Replace file body (no `load_json`, no `game_data_dir`):

```python
"""Toolbar flatten equivalence: pinned dump ORM invariants."""

from __future__ import annotations

import pytest

from django_apps.game_data.models import ImportBatch, ToolbarTreeNode
from django_apps.game_data.services.toolbar_node_kind import parent_path_from_tree_path
from tests.unit.game_data._dump_expectations import TOOLBAR_TREE_NODE_COUNT


def _parent_edges(paths: set[str]) -> set[tuple[str, str]]:
    edges: set[tuple[str, str]] = set()
    for path in paths:
        if path == "root":
            continue
        parent = parent_path_from_tree_path(path)
        assert parent is not None
        edges.add((parent, path))
    return edges


@pytest.mark.django_db
def test_toolbar_path_count_matches_pinned_dump(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    del imported_game_data_batch_module
    assert ToolbarTreeNode.objects.count() == TOOLBAR_TREE_NODE_COUNT


@pytest.mark.django_db
def test_toolbar_parent_child_edges(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    del imported_game_data_batch_module
    paths = set(ToolbarTreeNode.objects.values_list("tree_path", flat=True))
    expected_edges = _parent_edges(paths)
    nodes = {n.tree_path: n for n in ToolbarTreeNode.objects.select_related("parent")}
    actual_edges: set[tuple[str, str]] = set()
    for child_path, node in nodes.items():
        if node.parent_id is None:
            continue
        actual_edges.add((node.parent.tree_path, child_path))
    assert actual_edges == expected_edges


@pytest.mark.django_db
def test_toolbar_no_dangling_parent(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    del imported_game_data_batch_module
    paths = set(ToolbarTreeNode.objects.values_list("tree_path", flat=True))
    for path in paths:
        if path == "root":
            continue
        parent = parent_path_from_tree_path(path)
        assert parent in paths


@pytest.mark.django_db
def test_toolbar_acyclic(imported_game_data_batch_module: ImportBatch) -> None:
    del imported_game_data_batch_module
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

- [ ] **Step 2: Update `test_toolbar_tree.py`**

1. Remove imports: `GameDataImporter`, `load_json`, `Path` (if unused), stratified merge helpers if only used by deleted test.
2. Replace `test_tree_node_count_matches_source` → `test_tree_node_count_matches_pinned_dump`:

```python
@pytest.mark.django_db
def test_tree_node_count_matches_pinned_dump(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    del imported_game_data_batch_module
    assert ToolbarTreeNode.objects.count() == TOOLBAR_TREE_NODE_COUNT
```

3. Replace `test_actionable_count_matches_source` → use `TOOLBAR_ELEMENT_COUNT` and `TOOLBAR_ACTION_KIND_NODE_COUNT` from `_dump_expectations`.
4. Delete: `test_canonical_id_fast_stability_stratified_toolbar_sample`, `test_canonical_id_stable_across_reimport_full_toolbar_tree`.
5. Rename `test_island_placer_id_matches_json` → `test_island_placer_id_matches_pinned_dump` (body unchanged).
6. Remove `_source_rows`, `_expected_node_count`, `_expected_action_count`.

- [ ] **Step 3: Run toolbar tests**

Run: `python -m pytest tests/unit/game_data/test_toolbar_closure.py tests/unit/game_data/test_toolbar_tree.py -v`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add tests/unit/game_data/test_toolbar_closure.py tests/unit/game_data/test_toolbar_tree.py
git commit -m "test(game_data): toolbar contracts use pinned dump ORM counts"
```

---

### Task 6: Rewrite shape recipe provenance (ORM-only)

**Files:**
- Modify: `tests/unit/game_data/test_shape_recipe_provenance.py`

- [ ] **Step 1: Remove JSON fixtures and pure-JSON test**

Delete: `items_rows` fixture, `_overlap_keys(game_data_dir)`, `test_shape_recipe_items_keys_subset_of_shapes`, all `game_data_dir` parameters.

Add helper:

```python
def _recipe_with_full_and_items_sources(batch: ImportBatch) -> ShapeRecipe:
    overlap_ids = (
        ShapeRecipeSourceAppearance.objects.filter(import_batch=batch)
        .values("shape_recipe_id")
        .annotate(n=models.Count("catalog_source", distinct=True))
        .filter(n__gte=2)
    )
    recipe_id = overlap_ids.first()["shape_recipe_id"]
    return ShapeRecipe.objects.get(pk=recipe_id)
```

(Import `django.db.models` as `models`.)

- [ ] **Step 2: Update count tests**

```python
@pytest.mark.django_db
def test_items_recipe_count_matches_pinned_dump(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    batch = imported_game_data_batch_module
    assert (
        ShapeRecipeSourceAppearance.objects.filter(
            import_batch=batch,
            catalog_source="items",
        ).count()
        == ITEMS_SOURCE_APPEARANCE_COUNT
    )
```

```python
@pytest.mark.django_db
def test_shape_recipe_count_matches_pinned_dump(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    del imported_game_data_batch_module
    assert ShapeRecipe.objects.count() == SHAPE_RECIPE_COUNT
```

Overlap tests: use `_recipe_with_full_and_items_sources(batch)` instead of `_overlap_keys`.

- [ ] **Step 3: Rewrite `test_items_layer_slot_parity_by_source_object` (ORM-only)**

Iterate `ShapeRecipeSourceAppearance.objects.filter(import_batch=batch, catalog_source="items")` and assert:

```python
recipe = appearance.shape_recipe
layer_count = ShapeRecipeLayer.objects.filter(shape_recipe=recipe).count()
slot_count = ShapeQuadrantSlot.objects.filter(layer__shape_recipe=recipe).count()
assert layer_count > 0
assert slot_count > 0
```

Remove JSON `definition_snapshot` comparison.

- [ ] **Step 4: Run**

Run: `python -m pytest tests/unit/game_data/test_shape_recipe_provenance.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/game_data/test_shape_recipe_provenance.py
git commit -m "test(game_data): shape provenance uses pinned dump ORM only"
```

---

### Task 7: Tier A manual CI / release runbook

**Files:**
- Create: `docs/runbooks/game_data_tier_a_release_gate.md`
- Modify: `docs/runbooks/game_data_snapshot_deploy.md`
- Modify: `docs/domain/game_data_coverage.md`
- Modify: `documents/ai/manuals/testing.md`
- Modify: `docs/superpowers/specs/2026-05-23-pytest-slim-optimization-design.md`

- [ ] **Step 1: Create runbook** (`game_data_tier_a_release_gate.md`)

Include title **manual CI / release gate**, steps 1–5 from spec, and note: **not** part of `test_fast`.

- [ ] **Step 2: Update `game_data_coverage.md`**

Add subsection under A vs B:

```markdown
### pytest (unit)

- Full bundle seed: `game_data_backup/game_data_dump.json` via `loaddata` only.
- Tier A import/verify: manual CI / release gate — see [game_data_tier_a_release_gate.md](../runbooks/game_data_tier_a_release_gate.md).
```

- [ ] **Step 3: Update `testing.md`**

Add short section: `game_data_dump` fixture, `REQUIRE_GAME_DATA_DUMP=1`, CI fails if dump missing, no `-q`.

- [ ] **Step 4: Update `game_data_snapshot_deploy.md`**

Replace prerequisite `documents/game_data/` bundle with pointer to Tier A gate for dump refresh; keep deploy Step 1 as environment import if still needed for production, or clarify deploy uses existing DB batch.

- [ ] **Step 5: Update pytest-slim ownership table**

Change row:

```markdown
| full `documents/game_data` import idempotent | manual CI / release gate (`game_data_tier_a_release_gate.md`) | Removed from unit pytest 2026-05-22 |
```

- [ ] **Step 6: Commit**

```bash
git add docs/runbooks/game_data_tier_a_release_gate.md docs/domain/game_data_coverage.md documents/ai/manuals/testing.md docs/runbooks/game_data_snapshot_deploy.md docs/superpowers/specs/2026-05-23-pytest-slim-optimization-design.md
git commit -m "docs(game_data): Tier A release gate; pytest uses Tier B dump only"
```

---

### Task 8: Full verification + durations

**Files:**
- (none — commands only)

- [ ] **Step 1: game_data unit suite with durations**

Run: `python -m pytest tests/unit/game_data/ --durations=20`  
Expected: PASS; note top fixtures in Caveman **Tests**

- [ ] **Step 2: Fast slice**

Run: `powershell -File scripts/test_fast.ps1`  
Expected: PASS (CI has `CI=true` and committed dump)

- [ ] **Step 3: Confirm CI would fail without dump (optional local)**

Run: `$env:REQUIRE_GAME_DATA_DUMP='1'; Remove-Item Env:CI -ErrorAction SilentlyContinue` then temporarily rename dump and run one test — expect `pytest.fail`. Restore dump after.

- [ ] **Step 4: ruff on touched tests**

Run: `python -m ruff check tests/unit/game_data/`  
Expected: PASS

- [ ] **Step 5: Final commit if doc/test fixes remain**

```bash
git status
# commit any remaining fixes
```

---

## Self-review (plan vs spec)

| Spec requirement | Task |
| ---------------- | ---- |
| CI fail missing dump | Task 2 `_require_game_data_dump` |
| Pinned hash assert | Task 2 `_assert_pinned_import_batch` |
| App-local flush only | Task 2 (explicit comment + no `flush` command) |
| `django_db_blocker` module pattern | Task 2 |
| Keep slice fixtures | Task 4 keeps `min_sim_rows` path |
| manual CI / release gate naming | Task 7 |
| Delete Tier A unit tests | Task 3–4 |
| ORM rewrite | Tasks 5–6 |
| `--durations=20` | Task 8 |
| Ownership table update | Task 7 |

No placeholders remain in task steps.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-22-game-data-pytest-dump-only.md`. Spec at `docs/superpowers/specs/2026-05-22-game-data-pytest-dump-only-design.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — run tasks in this session with executing-plans checkpoints  

Which approach do you want?
