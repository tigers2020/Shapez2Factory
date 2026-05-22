# Pytest Slim & Optimization (Phase D) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Shrink fast pytest wall time and test-suite boilerplate without weakening contract coverage—conservative dedup (D1), structural consolidation (D2), duration-driven slow tagging with evidence artifacts (D3).

**Architecture:** Three PRs extending A+B+C. D1 finishes invariant ownership audit and any remaining Phase 2 deletes. D2 migrates inline exhaustive generators and parametrizes `source_object` coverage; adds integration gene seed fixture. D3 measures `--durations`; if fast slice >70s, documents slow-tag candidates and a timing table—no deletion expansion.

**Tech Stack:** Python 3.12, pytest 8, pytest-django, pytest-xdist, PowerShell scripts.

**Spec:** [`docs/superpowers/specs/2026-05-23-pytest-slim-optimization-design.md`](../specs/2026-05-23-pytest-slim-optimization-design.md)

**Prerequisites:** `scripts/test_*.ps1`, auto `slow` in `tests/conftest.py`, `imported_game_data_batch_module`, `exhaustive_genes_*`, CI pytest matrix.

---

## File map

| File | PR | Responsibility |
|------|-----|----------------|
| `docs/superpowers/specs/2026-05-23-pytest-slim-optimization-design.md` | D1 | Ownership table + **Removed in D1** audit |
| `tests/unit/game_data/test_simulation_*.py` | D1 | Drop generic re-import dupes if any remain |
| `tests/unit/asteroid_lab/test_sample_gene_exhaustive.py` | D2 | Inline generator → fixtures |
| `tests/unit/game_data/test_source_object_coverage.py` | D2 | Parametrize domain roots |
| `tests/unit/game_data/_assertions.py` | D2 | Optional shared assert helper |
| `tests/integration/conftest.py` | D2 | `seed_gene_templates_from_exhaustive` fixture |
| `tests/integration/web/test_*.py` | D2 | Use integration conftest |
| `tests/integration/asteroid_lab/test_solver_runtime_replay_timeline.py` | D2 | Use integration conftest |
| `tests/conftest.py` | D3 | Extend `_SLOW_MODULE_SUFFIXES` if justified |
| `docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md` | D3 | Timings + slow-tag candidate table |

---

## PR D1 — Ownership-backed dedup

**Done when:** Spec **Invariant coverage ownership table** is current and **Removed in D1** lists every deletion (or explicit “skipped—already absent” rows); owner modules pytest green.

### Task 1: Baseline fast timing (before D1)

**Files:**
- Modify: `docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md`

- [ ] **Step 1: Record pre-D1 wall**

Run:

```powershell
powershell -File scripts/test_fast.ps1
```

Append under heading `Phase D pre-D1 (YYYY-MM-DD)`:

```markdown
- collect: `python -m pytest -m "unit and not slow" --collect-only -q`
- wall: <seconds>s
- passed/skipped: <N> passed, <M> skipped
```

- [ ] **Step 2: Commit baseline note only (optional)**

```bash
git add docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md
git commit -m "docs: Phase D pytest fast slice baseline"
```

---

### Task 2: Verify Phase 2 exhaustive/golden deletes (skip or delete)

**Files:**
- Modify: `tests/unit/asteroid_lab/test_sample_gene_exhaustive.py` (only if names still exist)
- Modify: `docs/superpowers/specs/2026-05-23-pytest-slim-optimization-design.md` § Removed in D1

- [ ] **Step 1: Grep for planned duplicate names**

Run:

```powershell
rg "test_exhaustive_connected_branch_pipe_matches_user_golden_json|test_exhaustive_connected_branch_encode_not_spread_bug_fixture|test_encode_layout_with_suffix_roundtrip|test_connected_branch_gene_matches_user_fixture_layout" tests/
```

Expected: **no matches** (already removed per 2026-05-22 baseline).

- [ ] **Step 2: Update spec audit table**

In `2026-05-23-pytest-slim-optimization-design.md` § **Removed in D1**, add rows:

```markdown
| test_exhaustive_connected_branch_pipe_matches_user_golden_json | test_official_canonical_export.py | skipped—pre-D |
| test_exhaustive_connected_branch_encode_not_spread_bug_fixture | test_official_canonical_export.py | skipped—pre-D |
| test_encode_layout_with_suffix_roundtrip | test_official_canonical_export.py | skipped—pre-D |
| test_connected_branch_gene_matches_user_fixture_layout | test_official_canonical_export.py | skipped—pre-D |
```

If grep finds any name still present, delete that function and record PR commit in the table instead of `skipped—pre-D`.

- [ ] **Step 3: Run canonical owners**

```powershell
python -m pytest tests/unit/asteroid_lab/test_decode_adapter.py tests/unit/asteroid_lab/test_official_canonical_export.py tests/unit/asteroid_lab/test_sample_gene_exhaustive.py tests/unit/asteroid_lab/test_blueprint_equivalence_golden.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-05-23-pytest-slim-optimization-design.md tests/unit/asteroid_lab/
git commit -m "test: Phase D audit exhaustive/golden dedup ownership"
```

---

### Task 3: Audit game_data re-import idempotency copies

**Files:**
- Modify: `tests/unit/game_data/test_simulation_speed_import.py`
- Modify: `tests/unit/game_data/test_simulation_parameter_registry.py`
- Modify: `tests/unit/game_data/test_simulation_systems_import.py`
- Modify: `tests/unit/game_data/test_import_idempotency.py` (comment only if deletes)
- Modify: spec § Removed in D1 + ownership Notes

- [ ] **Step 1: List re-import tests**

Run:

```powershell
rg "def test_reimport" tests/unit/game_data/
```

For each hit, read the test body. **Delete** only if it solely asserts row counts unchanged after second `GameDataImporter.run()` on the same manifest already covered by `test_import_idempotency.py`.

**Keep** (already in tree—do not delete):

- `test_converter_audit_issue_unique_and_reimport_idempotent`
- `test_reimport_does_not_inflate_occurrence_count`
- `test_reimport_speed_rows_idempotent`
- `test_reimport_ignored_simulation_parameter_is_idempotent`

- [ ] **Step 2: If any generic duplicate deleted, add owner pointer**

In `test_import_idempotency.py` module docstring or a short comment:

```python
# Global manifest re-import idempotency: test_import_is_idempotent.
# Domain-specific re-import tests live in test_simulation_* modules.
```

- [ ] **Step 3: Run game_data unit**

```powershell
python -m pytest tests/unit/game_data/ -q
```

Expected: PASS.

- [ ] **Step 4: Update ownership table**

For each deletion, add **Removed in D1** row with owner `test_import_idempotency.py`. If nothing deleted, add one audit row: `| _(none)_ | test_import_idempotency.py | D1—no generic dupes remain |`.

- [ ] **Step 5: Commit**

```bash
git add tests/unit/game_data/ docs/superpowers/specs/2026-05-23-pytest-slim-optimization-design.md
git commit -m "test: Phase D game_data re-import dedup audit"
```

---

### Task 4: D1 gate — ownership table sign-off

- [ ] **Step 1: Self-check spec**

Confirm:

1. Every invariant in the ownership table has an existing test function in the owner path (grep `def test_`).
2. **Removed in D1** has no empty placeholder rows without explanation.
3. `documents/ai/manuals/testing.md` forbidden shortcuts unchanged.

- [ ] **Step 2: Record post-D1 collect**

```powershell
python -m pytest -m "unit and not slow" --collect-only -q
```

Append count to baseline doc `Phase D post-D1`.

- [ ] **Step 3: Commit spec if only table updates remain**

```bash
git add docs/superpowers/specs/2026-05-23-pytest-slim-optimization-design.md docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md
git commit -m "docs: Phase D1 coverage ownership table complete"
```

---

## PR D2 — Fixture & parametrize consolidation

### Task 5: Parametrize `test_source_object_coverage.py`

**Files:**
- Create: `tests/unit/game_data/_assertions.py`
- Modify: `tests/unit/game_data/test_source_object_coverage.py`

- [ ] **Step 1: Add helper**

Create `tests/unit/game_data/_assertions.py`:

```python
from __future__ import annotations

from django.db.models import Model, QuerySet

from django_apps.game_data.models import ImportBatch


def assert_import_batch_has_no_missing_source_object(
    model: type[Model],
    batch: ImportBatch,
    *,
    extra_filter: dict[str, object] | None = None,
) -> None:
    qs: QuerySet[Model] = model.objects.filter(import_batch=batch)
    if extra_filter:
        qs = qs.filter(**extra_filter)
    assert qs.filter(source_object__isnull=True).count() == 0
```

- [ ] **Step 2: Replace six duplicate tests with parametrized test**

Replace the six `test_*_have_source_object` functions with:

```python
from tests.unit.game_data._assertions import assert_import_batch_has_no_missing_source_object

_SOURCE_OBJECT_MODELS: list[tuple[str, type]] = [
    ("shape_recipe", ShapeRecipe),
    ("building_variant", BuildingVariant),
    ("building_group", BuildingGroup),
    ("content_asset", GameContentAsset),
    ("simulation_system", SimulationSystem),
    ("toolbar_tree_node", ToolbarTreeNode),
]


@pytest.mark.django_db
@pytest.mark.parametrize("label,model", _SOURCE_OBJECT_MODELS, ids=[x[0] for x in _SOURCE_OBJECT_MODELS])
def test_domain_root_has_source_object(
    label: str,
    model: type,
    imported_batch_module: ImportBatch,
) -> None:
    if label == "toolbar_tree_node":
        assert ToolbarTreeNode.objects.filter(import_batch=imported_batch_module).exists()
    assert_import_batch_has_no_missing_source_object(model, imported_batch_module)
```

Keep `test_research_milestones_have_source_object_when_present` and `test_source_object_auxiliary_path_on_toolbar` unchanged.

- [ ] **Step 3: Run file**

```powershell
python -m pytest tests/unit/game_data/test_source_object_coverage.py -q
```

Expected: PASS (6 parametrized cases + 2 dedicated tests).

- [ ] **Step 4: Commit**

```bash
git add tests/unit/game_data/_assertions.py tests/unit/game_data/test_source_object_coverage.py
git commit -m "test: parametrize game_data source_object coverage"
```

---

### Task 6: Migrate `test_sample_gene_exhaustive.py` to module fixtures

**Files:**
- Modify: `tests/unit/asteroid_lab/test_sample_gene_exhaustive.py`

- [ ] **Step 1: Add fixture parameters to tests that call `max_extensions=3`**

Example pattern—change:

```python
def test_exhaustive_generator_all_layout_entries_raw_x_nonzero() -> None:
    genes, _stats = generate_exhaustive_sample_genes(max_extensions=3)
```

To:

```python
def test_exhaustive_generator_all_layout_entries_raw_x_nonzero(
    exhaustive_genes_ext3: tuple[list, dict],
) -> None:
    genes, _stats = exhaustive_genes_ext3
```

Apply to every test in the file that uses `generate_exhaustive_sample_genes(max_extensions=3)` (grep the file). Use `exhaustive_genes_ext0_belt` / `exhaustive_genes_ext1_belt` where `max_extensions` is 0 or 1 with belt transport.

Remove unused import `generate_exhaustive_sample_genes` if no inline calls remain.

- [ ] **Step 2: Run module**

```powershell
python -m pytest tests/unit/asteroid_lab/test_sample_gene_exhaustive.py -q
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/asteroid_lab/test_sample_gene_exhaustive.py
git commit -m "test: use module exhaustive gene fixtures in exhaustive tests"
```

---

### Task 7: Integration conftest for gene seeding

**Files:**
- Create: `tests/integration/conftest.py`
- Modify: `tests/integration/web/test_asteroid_run_solver.py`
- Modify: `tests/integration/asteroid_lab/test_solver_runtime_replay_timeline.py`

- [ ] **Step 1: Create shared autouse fixture**

Create `tests/integration/conftest.py`:

```python
from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m


@pytest.fixture(autouse=True)
def seed_gene_templates_from_exhaustive(exhaustive_genes_ext0_belt: tuple[list, dict]) -> None:
    genes, _stats = exhaustive_genes_ext0_belt
    for g in genes:
        m.GeneticSample.objects.update_or_create(
            gene_key=g.key,
            defaults={
                "name": g.name,
                "code": g.encoded_copy_string,
                "metadata_json": dict(g.metadata),
            },
        )
```

Note: `exhaustive_genes_ext0_belt` is defined in `tests/unit/asteroid_lab/conftest.py`; pytest discovers it for integration tests under `tests/`.

- [ ] **Step 2: Remove duplicate autouse blocks from integration files**

In each integration file listed above, delete local `seed_gene_templates_db` fixture and `generate_exhaustive_sample_genes` import if unused.

If a file needs `max_extensions=3`, add a file-level fixture overriding autouse (document in comment).

- [ ] **Step 3: Run integration slice**

```powershell
python -m pytest tests/integration/web/test_asteroid_run_solver.py tests/integration/asteroid_lab/test_solver_runtime_replay_timeline.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/integration/
git commit -m "test: shared integration fixture for exhaustive gene seed"
```

---

### Task 8: D2 timing checkpoint

- [ ] **Step 1: Run test_fast and record**

```powershell
powershell -File scripts/test_fast.ps1
```

Append `Phase D post-D2` to baseline doc with wall seconds.

- [ ] **Step 2: Commit baseline**

```bash
git add docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md
git commit -m "docs: Phase D2 fast slice timing"
```

---

## PR D3 — Durations, slow tags, evidence artifacts

**Done when:** `test_fast` ≤70s **or** baseline contains **slow-tag candidate list** + **duration evidence table** and Caveman Risks documents the gap (no extra test deletion).

### Task 9: Collect duration evidence (fast slice)

**Files:**
- Modify: `docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md`

- [ ] **Step 1: Run durations**

```powershell
python -m pytest -m "unit and not slow" -n auto --dist loadscope --durations=25 -q
```

- [ ] **Step 2: Paste evidence table into baseline**

Under `## Phase D D3 — duration evidence (fast slice)`:

```markdown
| Rank | Duration (s) | Test node id |
|------|--------------|--------------|
| 1 | ... | ... |
...
```

Also run slow slice for reference:

```powershell
python -m pytest -m slow -n auto --dist loadscope --durations=15 -q
```

Add subsection `### slow slice top 15`.

- [ ] **Step 3: Commit evidence**

```bash
git add docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md
git commit -m "docs: Phase D3 pytest duration evidence"
```

---

### Task 10: Slow-tag candidate list (if fast >70s)

**Files:**
- Modify: `docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md`
- Modify: `tests/conftest.py` (only if applying tags)

- [ ] **Step 1: Run test_fast wall check**

```powershell
powershell -File scripts/test_fast.ps1
```

- [ ] **Step 2a: If wall ≤70s**

Append baseline: `Phase D3: fast target met (<70s). No slow-tag changes required.`

Skip Step 2b; go to Task 11.

- [ ] **Step 2b: If wall >70s — write candidate list (required deliverable)**

Append to baseline under `## Phase D3 — slow-tag candidates (do not delete tests)`:

```markdown
| Candidate | Type | Rationale (from durations) | Applied? |
|-----------|------|----------------------------|----------|
| e.g. tests/unit/foo/test_bar.py | module suffix | top 5 wall | yes/no |
| e.g. some_fixture_name | fixture name | setup >2s | yes/no |
```

Rules:

- Prefer tagging **whole modules** already heavy in durations over individual test deletion.
- Only add to `_SLOW_MODULE_SUFFIXES` or `_SLOW_FIXTURE_NAMES` in `tests/conftest.py` when duration table supports it.
- Re-run `test_fast.ps1` after each applied tag; record new wall in baseline.

- [ ] **Step 3: Commit candidates and any conftest change**

```bash
git add tests/conftest.py docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md
git commit -m "test: Phase D3 slow-tag candidates and auto-slow extensions"
```

---

### Task 11: D3 final gate & Risks template

- [ ] **Step 1: Full scripts smoke**

```powershell
powershell -File scripts/test_fast.ps1
powershell -File scripts/test_slow.ps1
powershell -File scripts/test_full.ps1
```

- [ ] **Step 2: PR full gate (local)**

```powershell
python -m ruff check .
python -m black --check .
python -m mypy django_apps config src
```

- [ ] **Step 3: Document Risks if still >70s**

In PR description or agent Caveman **Risks**:

```markdown
assumption: Win dev, -n auto, shapez2solver env
uncertain: fast slice wall <goal> after slow-tag pass
evidence: see baseline § Phase D D3 duration evidence + slow-tag candidates
recommended next: apply next candidate row; do not delete tests for speed
```

- [ ] **Step 4: Commit final baseline**

```bash
git add docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md
git commit -m "docs: Phase D3 final fast/slow/full timings"
```

---

## Plan self-review (spec coverage)

| Spec section | Task(s) |
|--------------|---------|
| Ownership table + Removed in D1 | 2, 3, 4 |
| D1 done = table complete | 4 |
| game_data re-import dedup | 3 |
| exhaustive inline → fixtures | 6 |
| source_object parametrize | 5 |
| integration conftest | 7 |
| D3 ≤70s or candidates + durations | 9, 10, 11 |
| Forbidden session DB / mass delete | (no tasks—enforced by review) |
| Baseline timings | 1, 8, 9, 11 |

No TBD placeholders in task steps.

---

## Execution summary

| PR | Tasks | Primary success signal |
|----|-------|------------------------|
| D1 | 1–4 | **Coverage owner table + Removed in D1 complete** |
| D2 | 5–8 | LOC ↓; fixtures; post-D2 timing |
| D3 | 9–11 | ≤70s **or** slow-tag list + duration table in baseline |
