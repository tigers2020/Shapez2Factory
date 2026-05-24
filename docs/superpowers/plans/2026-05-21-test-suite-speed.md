# Test Suite Speed Implementation Plan

> **pytest output:** [`AGENTS.md`](../../../AGENTS.md) · [`documents/ai/manuals/testing.md`](../../../documents/ai/manuals/testing.md) — `-q` / `--quiet` / `--tb=no` **forbidden**. (If `-q` remains in baseline measurement records, that was the command at the time; remove it on re-run.)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut local and CI wall time for `pytest`, `ruff`, and `black` without weakening contract coverage—via shared expensive fixtures, optional parallelism, lint excludes, and removal of provably redundant tests.

**Architecture:** Two PR-sized phases. Phase 1 is infrastructure-only (no test deletion): `pytest-xdist`, `slow` marker, session-scoped `game_data` import fixture, module-scoped exhaustive gene generator fixture, and tool excludes. Phase 2 consolidates duplicate invariant tests (encode roundtrip, connected-branch golden, redundant re-import assertions) after a `--durations` baseline proves which modules dominate time.

**Tech Stack:** Python 3.12, pytest 8, pytest-django (`--reuse-db`), pytest-xdist (`--dist loadscope`), ruff, black, Django 5 test DB.

**Context (brainstorm 2026-05-21):** ~1053 collected tests (977 unit / 75 integration). Hot spots: repeated `generate_exhaustive_sample_genes(max_extensions=3)` (40+ call sites), per-test `GameDataImporter.run()` (e.g. `test_toolbar_tree.py` runs import 9× in one file), full-tree `ruff check .` / `black --check .` on ~597 `.py` files.

**References:** [`documents/ai/manuals/testing.md`](../../../documents/ai/manuals/testing.md) (narrow vs full gate), [`pytest.ini`](../../../pytest.ini), [`tests/conftest.py`](../../../tests/conftest.py), [`.cursor/rules/shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc) (forbidden: delete tests only to go green).

---

## File map

| File | Responsibility |
|------|----------------|
| `pyproject.toml` | Add `pytest-xdist`; ruff/black excludes |
| `pytest.ini` | Register `slow` marker |
| `tests/unit/game_data/conftest.py` | **Create** — session `game_data_dir`, `imported_game_data_batch` |
| `tests/unit/asteroid_lab/conftest.py` | Add module fixtures for exhaustive genes + connected-branch gene |
| `tests/unit/game_data/test_*.py` | Drop local `game_data_dir` / per-test import; use shared fixtures |
| `tests/unit/asteroid_lab/test_sample_gene_exhaustive.py` | Remove redundant roundtrip/golden tests; use fixtures; mark `slow` |
| `tests/unit/asteroid_lab/test_official_canonical_export.py` | Use shared exhaustive fixture; keep canonical export ownership |
| `tests/unit/asteroid_lab/test_blueprint_equivalence_golden.py` | Drop duplicate connected-branch if covered by official export |
| `documents/ai/manuals/testing.md` | Document fast vs full commands |
| `.github/workflows/ci.yml` | Optional: pytest `-n auto --dist loadscope` on CI |

---

## Phase 0: Baseline (do not skip)

### Task 0: Record slow tests and timings

**Files:**
- Create: `docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md` (append-only notes)

- [ ] **Step 1: Collect durations (unit, may take several minutes)**

Run:

```powershell
cd f:\Python_Projects\shapez2Factory
python -m pytest -m unit --durations=40 2>&1 | Tee-Object docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md
```

Expected: file lists ~40 slowest tests; note top modules (`test_sample_gene_exhaustive`, `test_toolbar_tree`, `test_macro_recipe_staff_catalog`, `test_solver_runtime_replay_recorder`, etc.).

- [ ] **Step 2: Note full-suite collect count**

Run:

```powershell
python -m pytest --collect-only 2>&1 | Select-Object -Last 1
```

Expected: `1053 tests collected` (± a few if suite changed).

- [ ] **Step 3: Commit baseline artifact**

```bash
git add docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md
git commit -m "docs: pytest duration baseline before speed work"
```

---

## Phase 1: Infrastructure (no test deletion)

### Task 1: Add pytest-xdist to dev dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add dependency**

In `[project.optional-dependencies]` `dev` list, add:

```toml
    "pytest-xdist>=3.5.0",
```

- [ ] **Step 2: Reinstall dev extras**

```powershell
pip install -e ".[dev]"
python -c "import xdist; print('xdist ok')"
```

Expected: no import error.

- [ ] **Step 3: Smoke parallel collect**

```powershell
python -m pytest --collect-only -n 2 2>&1 | Select-Object -Last 1
```

Expected: same test count as serial collect.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "build: add pytest-xdist for parallel test runs"
```

---

### Task 2: Register `slow` marker and document commands

**Files:**
- Modify: `pytest.ini`
- Modify: `documents/ai/manuals/testing.md`

- [ ] **Step 1: Add marker to pytest.ini**

After existing markers, add:

```ini
    slow: full game_data import, exhaustive gene generation, or >2s typical (see testing.md)
```

- [ ] **Step 2: Extend testing.md “section run” table**

Add rows:

| Method | Example |
|------|-----|
| Parallel full | `python -m pytest -n auto --dist loadscope` |
| Fast unit | `python -m pytest -m "unit and not slow"` |
| Slow only | `python -m pytest -m slow` |

Under PR full gate, note: CI may use `-n auto --dist loadscope`; local iteration should prefer narrow path or `unit and not slow`.

- [ ] **Step 3: Commit**

```bash
git add pytest.ini documents/ai/manuals/testing.md
git commit -m "docs: slow marker and parallel pytest commands"
```

---

### Task 3: Session-scoped game_data import fixture

**Files:**
- Create: `tests/unit/game_data/conftest.py`
- Modify: `tests/unit/game_data/test_toolbar_tree.py` (pilot)
- Modify: `tests/unit/game_data/test_source_object_coverage.py`
- Modify: other `tests/unit/game_data/test_*.py` that define local `game_data_dir` / run `GameDataImporter`

- [ ] **Step 1: Create shared conftest**

Create `tests/unit/game_data/conftest.py`:

```python
"""Shared fixtures for game_data unit tests — one import per session."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.game_data.importers import GameDataImporter
from django_apps.game_data.models import ImportBatch

_REPO_ROOT = Path(__file__).resolve().parents[3]
_GAME_DATA_DIR = _REPO_ROOT / "documents" / "game_data"


@pytest.fixture(scope="session")
def game_data_dir() -> Path:
    if not (_GAME_DATA_DIR / "manifest.json").is_file():
        pytest.skip("documents/game_data not present")
    return _GAME_DATA_DIR


@pytest.fixture(scope="session")
def imported_game_data_batch(game_data_dir: Path) -> ImportBatch:
    GameDataImporter(game_data_dir, batch_name="pytest-session").run()
    batch = ImportBatch.objects.order_by("-imported_at").first()
    assert batch is not None
    return batch
```

Note: pytest-django session DB fixtures require `@pytest.mark.django_db(databases="__all__")` on tests using this fixture, or a `django_db` block fixture. If session fixture hits DB access errors, use this wrapper:

```python
@pytest.fixture(scope="session")
def imported_game_data_batch(
    django_db_setup: None,
    django_db_blocker,
    game_data_dir: Path,
) -> ImportBatch:
    with django_db_blocker.unblock():
        GameDataImporter(game_data_dir, batch_name="pytest-session").run()
        batch = ImportBatch.objects.order_by("-imported_at").first()
        assert batch is not None
        return batch
```

(Use the pattern already working in other session fixtures in the repo if one exists.)

- [ ] **Step 2: Migrate `test_source_object_coverage.py`**

- Remove local `game_data_dir` and `imported_batch` fixtures.
- Rename usages to `imported_game_data_batch` (or alias `imported_batch = imported_game_data_batch` via thin function-scoped fixture if test bodies use `imported_batch` name extensively).

- [ ] **Step 3: Migrate `test_toolbar_tree.py`**

- Remove local `game_data_dir`.
- Replace each `GameDataImporter(...).run()` at test start with reliance on `imported_game_data_batch` where the test only needs imported state.
- **Keep** tests that assert **second** `importer.run()` idempotency (e.g. `tree-a` double-run): those still call importer explicitly; do not delete idempotency behavior.

- [ ] **Step 4: Migrate remaining game_data unit modules**

Files with local `game_data_dir` / `GameDataImporter.run()`:
- `test_cross_references.py`
- `test_import_idempotency.py` (keep double-run test; use session batch for precondition if applicable)
- `test_lazy_localized_text.py`
- `test_simulation_speed_import.py`
- `test_simulation_systems_import.py`
- `test_toolbar_identity.py`

- [ ] **Step 5: Run narrow then game_data unit**

```powershell
python -m pytest tests/unit/game_data/
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add tests/unit/game_data/
git commit -m "test: session-scoped game_data import fixture"
```

---

### Task 4: Module-scoped exhaustive gene fixtures

**Files:**
- Modify: `tests/unit/asteroid_lab/conftest.py`
- Modify: `tests/unit/asteroid_lab/test_placement_materializer.py` (pilot)
- Modify: `tests/unit/asteroid_lab/test_official_canonical_export.py`
- Modify: other files calling `generate_exhaustive_sample_genes(max_extensions=3)` repeatedly

- [ ] **Step 1: Add fixtures to asteroid_lab conftest**

Append to `tests/unit/asteroid_lab/conftest.py`:

```python
from django_apps.asteroid_lab.services.sample_gene_exhaustive_generator import (
    generate_exhaustive_sample_genes,
)
from django_apps.asteroid_lab.services.sample_gene_types import SampleGene  # adjust import to actual type


@pytest.fixture(scope="module")
def exhaustive_genes_ext3() -> tuple[tuple[SampleGene, ...], object]:
    return generate_exhaustive_sample_genes(max_extensions=3)


@pytest.fixture(scope="module")
def exhaustive_genes_ext0_belt() -> tuple[tuple[SampleGene, ...], object]:
    return generate_exhaustive_sample_genes(max_extensions=0, transport_kinds=("belt",))


@pytest.fixture
def connected_branch_gene_ext3(exhaustive_genes_ext3):
    genes, _stats = exhaustive_genes_ext3
    key = (
        '{"e":[[[-1,1],[-1,2],"S"],[[0,0],[0,1],"S"],[[0,1],[-1,1],"W"]],"ec":3,"tk":"pipe"}'
    )
    return next(g for g in genes if g.key == key)
```

Fix `SampleGene` import path to match project (grep `generate_exhaustive_sample_genes` return type).

- [ ] **Step 2: Refactor `test_official_canonical_export.py`**

Replace:

```python
genes, _stats = generate_exhaustive_sample_genes(max_extensions=3)
match = next(g for g in genes if g.key == CONNECTED_BRANCH_GENE_KEY)
```

with `connected_branch_gene_ext3` or `exhaustive_genes_ext3` fixture parameter.

- [ ] **Step 3: Refactor `test_placement_materializer.py`**

Use `exhaustive_genes_ext0_belt` / `exhaustive_genes_ext3` instead of inline `generate_exhaustive_sample_genes(...)`.

- [ ] **Step 4: Refactor remaining call sites**

Grep: `generate_exhaustive_sample_genes` under `tests/` and switch to fixtures where the test does not need a **different** `max_extensions` / `transport_kinds` than the module fixture provides.

- [ ] **Step 5: Mark heavy module**

Add to `tests/unit/asteroid_lab/test_sample_gene_exhaustive.py` module level:

```python
pytestmark = pytest.mark.slow
```

- [ ] **Step 6: Run asteroid_lab unit**

```powershell
python -m pytest tests/unit/asteroid_lab/
```

Expected: pass.

- [ ] **Step 7: Commit**

```bash
git add tests/unit/asteroid_lab/
git commit -m "test: module-scoped exhaustive gene fixtures"
```

---

### Task 5: Ruff and Black excludes

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add ruff exclude**

Under `[tool.ruff]`:

```toml
exclude = [
    ".git",
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "graphify-out",
    "django_apps/game_data/graphify-out",
    "build",
    "dist",
    "node_modules",
]
```

- [ ] **Step 2: Add black extend-exclude**

Under `[tool.black]`:

```toml
extend-exclude = "/(\\.git|\\.venv|graphify-out|django_apps/game_data/graphify-out)/"
```

- [ ] **Step 3: Verify**

```powershell
python -m ruff check .
python -m black --check .
```

Expected: pass (same as before, potentially faster).

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: exclude generated dirs from ruff and black"
```

---

### Task 6: CI optional parallel pytest

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Use xdist on test matrix job**

Change test command from `pytest` to:

```yaml
test)      pytest -n auto --dist loadscope ;;
```

- [ ] **Step 2: Commit** (only after local parallel run green)

```bash
git add .github/workflows/ci.yml
git commit -m "ci: parallel pytest with loadscope for Django DB safety"
```

---

### Task 7: Phase 1 verification gate

- [ ] **Step 1: Fast unit slice**

```powershell
python -m pytest -m "unit and not slow"
```

- [ ] **Step 2: Full unit**

```powershell
python -m pytest -m unit -n auto --dist loadscope
```

- [ ] **Step 3: Full gate (PR)**

```powershell
python -m ruff check .
python -m black --check .
python -m mypy django_apps config src
python -m pytest -n auto --dist loadscope
```

Record before/after wall times in `2026-05-21-test-suite-speed-baseline.md`.

---

## Phase 2: Remove provably duplicate tests

**Invariant ownership (do not leave gaps):**

| Invariant | Canonical test home after cleanup |
|-----------|-------------------------------------|
| `encode_copy_string` / v4 decode roundtrip | `tests/unit/asteroid_lab/test_decode_adapter.py` |
| `encode_layout_with_suffix` + official `V`/`BinaryVersion` | `tests/unit/asteroid_lab/test_official_canonical_export.py::test_encode_layout_with_suffix_roundtrip_decode` |
| connected_branch golden bytes + layout equiv | `tests/unit/asteroid_lab/test_official_canonical_export.py` (3 tests) |
| spread vs connected_branch regression | keep **one** of official export or `test_blueprint_equivalence_golden.py` |
| full `documents/game_data` import idempotent | `tests/unit/game_data/test_import_idempotency.py` |
| per-domain re-import idempotent | keep only where distinct from global import (simulation_systems audit unique constraint) |

### Task 8: Delete redundant tests in `test_sample_gene_exhaustive.py`

**Files:**
- Modify: `tests/unit/asteroid_lab/test_sample_gene_exhaustive.py`

- [ ] **Step 1: Remove duplicate tests (exact names)**

Delete these functions entirely—they duplicate official export / decode_adapter coverage:

- `test_exhaustive_connected_branch_pipe_matches_user_golden_json`
- `test_exhaustive_connected_branch_encode_not_spread_bug_fixture`
- `test_encode_layout_with_suffix_roundtrip`

- [ ] **Step 2: Run owners + exhaustive module**

```powershell
python -m pytest tests/unit/asteroid_lab/test_decode_adapter.py tests/unit/asteroid_lab/test_official_canonical_export.py tests/unit/asteroid_lab/test_sample_gene_exhaustive.py
```

Expected: pass.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/asteroid_lab/test_sample_gene_exhaustive.py
git commit -m "test: drop duplicate roundtrip/golden cases from exhaustive module"
```

---

### Task 9: Deduplicate connected_branch in blueprint golden

**Files:**
- Modify: `tests/unit/asteroid_lab/test_blueprint_equivalence_golden.py`

- [ ] **Step 1: Remove or narrow `test_connected_branch_gene_matches_user_fixture_layout`**

If `test_official_canonical_export.py` already covers layout equivalence + golden bytes, delete the blueprint test. If it covers a **different** equivalence function (`decoded_json_layout_equivalent` vs byte identity), keep one parametrized test in official export only.

- [ ] **Step 2: Run**

```powershell
python -m pytest tests/unit/asteroid_lab/test_blueprint_equivalence_golden.py tests/unit/asteroid_lab/test_official_canonical_export.py
```

- [ ] **Step 3: Commit**

```bash
git add tests/unit/asteroid_lab/test_blueprint_equivalence_golden.py
git commit -m "test: remove duplicate connected_branch golden"
```

---

### Task 10: Trim redundant game_data re-import assertions

**Files:**
- Modify: `tests/unit/game_data/test_simulation_speed_import.py`
- Modify: `tests/unit/game_data/test_simulation_parameter_registry.py`
- Modify: `tests/unit/game_data/test_simulation_systems_import.py`

- [ ] **Step 1: For each `test_reimport_*_idempotent`**

If the test only asserts row counts unchanged after second `GameDataImporter.run()` on the **same** manifest as `test_import_is_idempotent`, delete it and add a one-line comment in `test_import_idempotency.py` pointing to global idempotency.

**Keep** tests that assert **domain-specific** invariants on re-import (e.g. `test_converter_audit_issue_unique_and_reimport_idempotent`).

- [ ] **Step 2: Run game_data unit**

```powershell
python -m pytest tests/unit/game_data/
```

- [ ] **Step 3: Commit**

```bash
git add tests/unit/game_data/
git commit -m "test: drop redundant game_data re-import idempotency copies"
```

---

### Task 11: Final verification and checklist

- [ ] **Step 1: Collect count delta**

```powershell
python -m pytest --collect-only 2>&1 | Select-Object -Last 1
```

Expected: fewer than 1053 tests (roughly 5–15 removed); document exact number in baseline md.

- [ ] **Step 2: Full PR gate**

```powershell
python -m ruff check .
python -m black --check .
python -m mypy django_apps config src
python -m pytest -n auto --dist loadscope
```

- [ ] **Step 3: Update `documents/ai/checklist.md`**

Add line under verification: parallel pytest + session fixtures landed (date).

---

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Session DB fixture breaks test isolation | Scope session fixture to `tests/unit/game_data` only; tests that need empty DB keep explicit `TransactionTestCase` or fresh import batch name |
| xdist + `--reuse-db` flake on Windows | Use `--dist loadscope`; avoid running two pytest **processes** simultaneously |
| Deleting test hides regression | Only delete listed duplicates; run canonical owner modules before commit |
| `documents/game_data` missing locally | Existing `pytest.skip` on `game_data_dir` unchanged |

---

## Success criteria

- Local: `pytest -m "unit and not slow"` completes noticeably faster than pre-change baseline (target: under ~2 minutes on dev machine, environment-dependent).
- Full unit with `-n auto --dist loadscope` faster than serial full unit.
- `ruff check .` / `black --check .` unchanged pass, faster or equal wall time.
- No reduction in coverage of listed invariants (owners table above).
- Test count reduced only by explicit duplicate removal in Phase 2.

---

## Spec self-review (inline)

- [x] All brainstorm items mapped to tasks (xdist, slow, fixtures, excludes, dedupe).
- [x] No TBD steps; commands and file paths concrete.
- [x] Forbidden shortcut avoided: no “delete failing tests”—only named duplicates with owner tests retained.
- [x] Scope fits one plan; Phase 2 can be separate PR if time-boxed.
