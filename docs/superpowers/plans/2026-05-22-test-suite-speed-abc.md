# Test Suite Speed (A+B+C) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver one-command local test loops (A), shorten the fast unit slice (B), and shorten CI test wall time via sharded pytest jobs (C) without weakening contract coverage.

**Architecture:** Three small PRs on top of existing xdist/`slow`/auto-marking work. PR1 adds PowerShell entrypoints and docs only. PR2 adds a module-scoped `game_data` import fixture (not session), Phase-2 duplicate test removal, and fixture migration. PR3 splits CI `test` into fast/slow/integration matrix jobs. Baseline timings recorded before/after each PR.

**Tech Stack:** Python 3.12, pytest 8, pytest-django (`--reuse-db`), pytest-xdist (`--dist loadscope`), PowerShell scripts, GitHub Actions.

**Spec:** [`docs/superpowers/specs/2026-05-22-test-suite-speed-abc-design.md`](../specs/2026-05-22-test-suite-speed-abc-design.md)

**Prerequisites (already in repo):** `pytest-xdist`, `slow` marker, auto `slow` in `tests/conftest.py`, `tests/unit/asteroid_lab/conftest.py` exhaustive module fixtures, CI `pytest -n auto --dist loadscope`.

---

## File map

| File | PR | Responsibility |
|------|-----|----------------|
| `scripts/test_fast.ps1` | 1 | Daily: unit ∧ ¬slow, parallel |
| `scripts/test_slow.ps1` | 1 | Slow marker slice |
| `scripts/test_full.ps1` | 1 | Full pytest (PR pre-check) |
| `documents/ai/manuals/testing.md` | 1 | Document scripts + agent default |
| `AGENTS.md` | 1 | One-line local test default |
| `tests/unit/game_data/conftest.py` | 2 | Add `imported_game_data_batch_module` |
| `tests/unit/game_data/test_toolbar_tree.py` | 2 | Use module fixture |
| `tests/unit/game_data/test_source_object_coverage.py` | 2 | Use module fixture |
| `tests/unit/game_data/test_*.py` | 2 | Migrate per spec; keep idempotency double-runs |
| `tests/unit/asteroid_lab/test_*.py` | 2 | Inline exhaustive → fixtures; Phase 2 deletes |
| `tests/conftest.py` | 2 | Extend `_SLOW_MODULE_SUFFIXES` after durations |
| `docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md` | 2–3 | Append timings |
| `.github/workflows/ci.yml` | 3 | pytest matrix: fast / slow / integration |

---

## PR 1 — Workflow scripts (A)

### Task 1: Add `scripts/test_fast.ps1`

**Files:**
- Create: `scripts/test_fast.ps1`

- [ ] **Step 1: Create script**

```powershell
# Daily TDD — fast unit slice (see documents/ai/manuals/testing.md)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m pytest -m "unit and not slow" -n auto --dist loadscope -q @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
```

- [ ] **Step 2: Smoke run**

Run: `powershell -File scripts/test_fast.ps1`  
Expected: `863+ passed`, wall **<120s** on dev machine (baseline ~100s).

- [ ] **Step 3: Commit**

```bash
git add scripts/test_fast.ps1
git commit -m "chore: add test_fast.ps1 for daily pytest loop"
```

---

### Task 2: Add `scripts/test_slow.ps1` and `scripts/test_full.ps1`

**Files:**
- Create: `scripts/test_slow.ps1`
- Create: `scripts/test_full.ps1`

- [ ] **Step 1: Create test_slow.ps1**

```powershell
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m pytest -m slow -n auto --dist loadscope -q @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
```

- [ ] **Step 2: Create test_full.ps1**

```powershell
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m pytest -n auto --dist loadscope -q @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
```

- [ ] **Step 3: Smoke both**

Run: `powershell -File scripts/test_slow.ps1`  
Expected: ~117 tests pass.

Run: `powershell -File scripts/test_full.ps1`  
Expected: full suite pass (may take several minutes).

- [ ] **Step 4: Commit**

```bash
git add scripts/test_slow.ps1 scripts/test_full.ps1
git commit -m "chore: add test_slow and test_full pytest scripts"
```

---

### Task 3: Document local defaults

**Files:**
- Modify: `documents/ai/manuals/testing.md` (§ 구간 실행 table or new § 로컬 속도)
- Modify: `AGENTS.md` (Validation commands subsection)

- [ ] **Step 1: Add to testing.md after 구간 실행 table**

```markdown
### 로컬 스크립트 (권장)

| 스크립트 | 용도 |
|----------|------|
| `powershell -File scripts/test_fast.ps1` | **일상 TDD** — `unit and not slow`, 병렬 |
| `powershell -File scripts/test_slow.ps1` | 느린 계약·import·exhaustive |
| `powershell -File scripts/test_full.ps1` | PR 직전 — 전체 pytest |

에이전트 반복 검증 기본: changed narrow path → `test_fast.ps1`. PR/CI: full gate.
```

- [ ] **Step 2: Add to AGENTS.md under Validation commands**

```markdown
로컬 pytest 기본: `powershell -File scripts/test_fast.ps1` (상세: documents/ai/manuals/testing.md).
```

- [ ] **Step 3: Commit**

```bash
git add documents/ai/manuals/testing.md AGENTS.md
git commit -m "docs: document test_fast/slow/full scripts as local default"
```

---

## PR 2 — Fast slice + dedup (B)

### Task 4: Baseline timings (before PR2 changes)

**Files:**
- Modify: `docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md`

- [ ] **Step 1: Record fast slice**

```powershell
cd f:\Python_Projects\shapez2Factory
Measure-Command { powershell -File scripts/test_fast.ps1 } | Select-Object TotalSeconds
```

Append line: `PR2-before test_fast: <N>s`

- [ ] **Step 2: Record slow top tests (optional, ~2–5 min)**

```powershell
python -m pytest -m slow --durations=20 -q --tb=no 2>&1 | Select-Object -Last 25
```

Append slowest module names to baseline file.

- [ ] **Step 3: Commit baseline note**

```bash
git add docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md
git commit -m "docs: PR2-before pytest timings"
```

---

### Task 5: Module-scoped `game_data` import fixture

**Files:**
- Modify: `tests/unit/game_data/conftest.py`

- [ ] **Step 1: Add module fixture (keep function fixture)**

Append to `tests/unit/game_data/conftest.py`:

```python
@pytest.fixture(scope="module")
def imported_game_data_batch_module(
    game_data_dir: Path,
    django_db_blocker,
) -> ImportBatch:
    """One full import per test module; use when tests only read imported state."""
    with django_db_blocker.unblock():
        GameDataImporter(game_data_dir, batch_name="pytest-module").run()
        batch = ImportBatch.objects.order_by("-imported_at").first()
        assert batch is not None
    return batch


@pytest.fixture
def imported_batch_module(imported_game_data_batch_module: ImportBatch) -> ImportBatch:
    return imported_game_data_batch_module
```

Keep existing function-scoped `imported_game_data_batch` unchanged for tests that mutate rows or need per-test rollback.

- [ ] **Step 2: Register module fixture as slow trigger**

Modify `tests/conftest.py` `_SLOW_FIXTURE_NAMES` add:

```python
        "imported_game_data_batch_module",
        "imported_batch_module",
```

- [ ] **Step 3: Run game_data collect smoke**

```powershell
python -m pytest tests/unit/game_data/ --collect-only -q 2>&1 | Select-Object -Last 1
```

Expected: collect succeeds.

- [ ] **Step 4: Commit**

```bash
git add tests/unit/game_data/conftest.py tests/conftest.py
git commit -m "test: module-scoped game_data import fixture"
```

---

### Task 6: Migrate `test_toolbar_tree.py` to module fixture

**Files:**
- Modify: `tests/unit/game_data/test_toolbar_tree.py`

- [ ] **Step 1: Replace fixture parameter**

In every test using `imported_game_data_batch: ImportBatch`, change to:

```python
imported_game_data_batch_module: ImportBatch,
```

and `del imported_game_data_batch` → `del imported_game_data_batch_module`.

Keep `game_data_dir` where JSON source rows are read from disk.

- [ ] **Step 2: Run file**

```powershell
python -m pytest tests/unit/game_data/test_toolbar_tree.py -q
```

Expected: all pass; **one** import per module (watch logs or time — faster than 7× import).

- [ ] **Step 3: Commit**

```bash
git add tests/unit/game_data/test_toolbar_tree.py
git commit -m "test: toolbar_tree uses module-scoped game_data import"
```

---

### Task 7: Migrate `test_source_object_coverage.py`

**Files:**
- Modify: `tests/unit/game_data/test_source_object_coverage.py`

- [ ] **Step 1: Switch `imported_batch` → `imported_batch_module`**

Replace parameter `imported_batch` with `imported_batch_module` in all tests; update `del` lines if present.

- [ ] **Step 2: Run file**

```powershell
python -m pytest tests/unit/game_data/test_source_object_coverage.py -q
```

Expected: pass.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/game_data/test_source_object_coverage.py
git commit -m "test: source_object_coverage uses module game_data import"
```

---

### Task 8: Migrate remaining `imported_game_data_batch` consumers (function scope only where needed)

**Files:**
- Modify: `tests/unit/game_data/test_cross_references.py`
- Modify: `tests/unit/game_data/test_lazy_localized_text.py`
- Modify: `tests/unit/game_data/test_toolbar_identity.py`
- Modify: `tests/unit/game_data/test_snapshot_builder.py`
- Modify: `tests/unit/game_data/test_snapshot_selectors.py`

**Do not migrate** `test_import_idempotency.py` tests that call `GameDataImporter` twice for idempotency behavior.

- [ ] **Step 1: Per file — use module fixture if test only queries ORM**

Same rename pattern as Task 6. If a test runs a **second** `GameDataImporter.run()`, keep function-scoped `imported_game_data_batch` or inline import for that test only.

- [ ] **Step 2: Run game_data unit**

```powershell
python -m pytest tests/unit/game_data/ -n auto --dist loadscope -q
```

Expected: pass.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/game_data/
git commit -m "test: migrate game_data tests to module import where safe"
```

---

### Task 9: Phase 2 — remove duplicate exhaustive / golden tests

**Files:**
- Modify: `tests/unit/asteroid_lab/test_sample_gene_exhaustive.py`

**Invariant ownership:** roundtrip/golden → `test_official_canonical_export.py`, `test_decode_adapter.py` (see 2026-05-21 plan Task 8).

- [ ] **Step 1: Delete duplicate test functions**

Remove these functions entirely from `test_sample_gene_exhaustive.py`:

- `test_exhaustive_connected_branch_pipe_matches_user_golden_json`
- `test_exhaustive_connected_branch_encode_not_spread_bug_fixture`
- `test_encode_layout_with_suffix_roundtrip`

- [ ] **Step 2: Run owners + exhaustive**

```powershell
python -m pytest tests/unit/asteroid_lab/test_decode_adapter.py tests/unit/asteroid_lab/test_official_canonical_export.py tests/unit/asteroid_lab/test_sample_gene_exhaustive.py -q
```

Expected: pass.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/asteroid_lab/test_sample_gene_exhaustive.py
git commit -m "test: drop duplicate roundtrip/golden from exhaustive module"
```

---

### Task 10: Phase 2 — blueprint golden dedup

**Files:**
- Modify: `tests/unit/asteroid_lab/test_blueprint_equivalence_golden.py`

- [ ] **Step 1: Remove duplicate connected_branch test**

Delete `test_connected_branch_gene_matches_user_fixture_layout` if `test_official_canonical_export.py` already covers layout + golden bytes (grep both files first; keep test if it asserts a **different** function).

- [ ] **Step 2: Run**

```powershell
python -m pytest tests/unit/asteroid_lab/test_blueprint_equivalence_golden.py tests/unit/asteroid_lab/test_official_canonical_export.py -q
```

- [ ] **Step 3: Commit**

```bash
git add tests/unit/asteroid_lab/test_blueprint_equivalence_golden.py
git commit -m "test: remove duplicate connected_branch golden"
```

---

### Task 11: Phase 2 — trim redundant game_data re-import tests

**Files:**
- Modify: `tests/unit/game_data/test_simulation_speed_import.py`
- Modify: `tests/unit/game_data/test_simulation_parameter_registry.py`
- Modify: `tests/unit/game_data/test_simulation_systems_import.py`

- [ ] **Step 1: Delete generic `test_reimport_*_idempotent` duplicates**

Remove tests that only assert row counts unchanged on second `GameDataImporter.run()` on the same manifest as `test_import_idempotency.py`.

**Keep** tests with domain-specific constraints (e.g. `test_converter_audit_issue_unique_and_reimport_idempotent`).

- [ ] **Step 2: Run game_data**

```powershell
python -m pytest tests/unit/game_data/ -q
```

- [ ] **Step 3: Commit**

```bash
git add tests/unit/game_data/
git commit -m "test: drop redundant game_data re-import idempotency copies"
```

---

### Task 12: Migrate inline `generate_exhaustive_sample_genes`

**Files:**
- Modify: `tests/unit/asteroid_lab/test_gene_template_loader.py`
- Modify: `tests/unit/asteroid_lab/test_genetic_sample_gene_export.py`
- Modify: `tests/unit/asteroid_lab/test_solver_runtime_entry.py`
- Modify: `tests/unit/asteroid_lab/test_solver_runtime_replay_recorder.py` (only if params match fixtures)

- [ ] **Step 1: Replace matching calls**

Example replacement:

```python
# before
genes, _stats = generate_exhaustive_sample_genes(max_extensions=1, transport_kinds=("belt",))
# after
genes, _stats = exhaustive_genes_ext1_belt
```

Add fixture parameters to test signatures. Use `exhaustive_genes_ext3` / `exhaustive_genes_ext0_belt` when `max_extensions` matches.

- [ ] **Step 2: Run asteroid_lab unit**

```powershell
python -m pytest tests/unit/asteroid_lab/ -n auto --dist loadscope -q
```

- [ ] **Step 3: Commit**

```bash
git add tests/unit/asteroid_lab/
git commit -m "test: use module exhaustive gene fixtures in asteroid_lab"
```

---

### Task 13: PR2 verification + baseline after

**Files:**
- Modify: `docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md`

- [ ] **Step 1: Fast slice timing**

```powershell
Measure-Command { powershell -File scripts/test_fast.ps1 } | Select-Object TotalSeconds
python -m pytest -m "unit and not slow" --collect-only -q 2>&1 | Select-Object -Last 1
```

Target: fewer collected tests than 864 if dedup removed unit tests from fast slice; wall **≤70s** aspirational.

- [ ] **Step 2: Full gate local**

```powershell
python -m ruff check .
python -m black --check .
python -m mypy django_apps config src
powershell -File scripts/test_full.ps1
```

- [ ] **Step 3: Append PR2-after to baseline + commit**

```bash
git add docs/superpowers/plans/2026-05-21-test-suite-speed-baseline.md
git commit -m "docs: PR2-after pytest timings"
```

---

## PR 3 — CI sharding (C)

### Task 14: Split pytest into matrix shards

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Replace test matrix cell**

Change matrix from:

```yaml
task: [lint, typecheck, format, test]
```

to:

```yaml
task: [lint, typecheck, format, test-fast, test-slow, test-integration]
```

- [ ] **Step 2: Extend case statement**

```yaml
          case "${{ matrix.task }}" in
            lint)      ruff check . ;;
            typecheck) mypy django_apps config src ;;
            format)    black --check . ;;
            test-fast) pytest -m "unit and not slow" -n auto --dist loadscope -q ;;
            test-slow) pytest -m slow -n auto --dist loadscope -q ;;
            test-integration) pytest -m integration -n auto --dist loadscope -q ;;
          esac
```

Note: align `mypy` with AGENTS.md (`django_apps config src`) if not already updated on branch.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: shard pytest into fast, slow, and integration jobs"
```

---

### Task 15: PR3 verification

- [ ] **Step 1: Local emulate shards**

```powershell
python -m pytest -m "unit and not slow" -n auto --dist loadscope -q
python -m pytest -m slow -n auto --dist loadscope -q
python -m pytest -m integration -n auto --dist loadscope -q
```

Expected: all three pass.

- [ ] **Step 2: Document CI in testing.md**

Add under 로컬 스크립트:

```markdown
CI는 동일 세 shard를 병렬 job으로 실행: `test-fast`, `test-slow`, `test-integration`.
```

- [ ] **Step 3: Commit docs**

```bash
git add documents/ai/manuals/testing.md
git commit -m "docs: document CI pytest shards"
```

---

## Plan self-review (spec coverage)

| Spec requirement | Task |
|------------------|------|
| A scripts | 1–3 |
| B module import | 5–8 |
| B Phase 2 dedup | 9–11 |
| B exhaustive fixtures | 12 |
| B measure | 4, 13 |
| C CI shards | 14–15 |
| Forbidden session import | Task 5 uses **module** only |
| Baseline record | 4, 13 |

---

## Execution handoff

**Plan saved:** `docs/superpowers/plans/2026-05-22-test-suite-speed-abc.md`  
**Spec saved:** `docs/superpowers/specs/2026-05-22-test-suite-speed-abc-design.md`

`/write-plan` 커맨드는 deprecated — 앞으로는 채팅에서 **「superpowers writing-plans로 실행해줘」** 또는 **「PR1부터 executing-plans로 진행」**처럼 요청하세요.

**Two execution options:**

1. **Subagent-Driven (recommended)** — task마다 fresh subagent + 단계 리뷰  
2. **Inline Execution** — 이 세션에서 `executing-plans`로 PR1→PR2→PR3 순차 진행

어느 쪽으로 진행할까요?
