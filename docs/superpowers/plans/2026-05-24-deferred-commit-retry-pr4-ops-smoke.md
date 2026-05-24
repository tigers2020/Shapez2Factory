# Deferred Commit Retry PR-4 Ops Smoke Implementation Plan

**Status:** CLOSED 2026-05-24 — ops smoke PASS (`solver_run_id` 57); PR pending merge

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close deferred commit retry slice **4/4** by adding normative `--deferred-retry-execute` CLI plumbing and running real-map ops smoke on `copy-import-495e552c` with output-only readback (shadow + execute steps, no `recovered_count > 0` gate).

**Architecture:** Thin config injection in `manage.py run_solver` and `scripts/run_solver.ps1` only. Runtime mapper and pipeline unchanged. Ops closure records `solver_run_id` / metrics in `current_plan.md` and roadmap — same pattern as B-CS2/E5.

**Tech Stack:** Python 3.12+, Django management command, PowerShell, pytest, `SolverRun.config_json`

**Spec:** [`docs/superpowers/specs/2026-05-24-deferred-commit-retry-pr4-ops-smoke-design.md`](../specs/2026-05-24-deferred-commit-retry-pr4-ops-smoke-design.md)

**Branch:** `feat/deferred-commit-retry-pr4-ops-smoke` (from `master` after PR-3 merge `d3de9645`)

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `django_apps/asteroid_lab/management/commands/run_solver.py` | `--deferred-retry-execute` → fixed `deferred_retry_shadow` object |
| Modify | `scripts/run_solver.ps1` | `-DeferredRetryExecute` switch |
| Modify | `tests/unit/asteroid_lab/test_run_solver_management_command.py` | CLI config persistence + flag composition |
| Modify | `documents/ai/current_plan.md` | PR-4 CLOSED evidence (after smoke PASS) |
| Modify | `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | PR-4 ✅; slice 1–4 complete |
| Modify | `docs/superpowers/specs/2026-05-24-deferred-commit-retry-pr4-ops-smoke-design.md` | Status CLOSED on ops PASS |
| Modify | `docs/superpowers/plans/2026-05-24-deferred-commit-retry-pr4-ops-smoke.md` | Status CLOSED on ops PASS |

**No change:** `deferred_retry_execute.py`, `incremental_commit.py`, `pipeline.py`, `solver_runtime_entry.py` mapper logic (unless smoke FAIL → separate bug track).

**No change:** `--config-json-path`, full GA, macro unpause, capacity gates.

---

### Task 0: Preflight (BLOCK if red)

**Files:** none

- [ ] **Step 1: Branch from master**

```powershell
git checkout master
git pull origin master
git checkout -b feat/deferred-commit-retry-pr4-ops-smoke
git merge-base --is-ancestor d3de9645 HEAD
```

Expected: exit code 0 (PR-3 on ancestor chain).

- [ ] **Step 2: Confirm `current_plan` priority**

Open [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md). Expected: **Priority** mentions PR-4 (real-map ops smoke); PR-3 CLOSED `d3de9645`.

- [ ] **Step 3: Confirm CLI lacks deferred retry flag**

```powershell
python manage.py run_solver --help
```

Expected: no `--deferred-retry-execute` yet (pre-Task-1).

- [ ] **Step 4: Standing regression baseline**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py tests/unit/asteroid_lab/test_run_solver_management_command.py -v --tb=short
powershell -File scripts/test_optimization_contamination.ps1
```

Expected: all PASS.

- [ ] **Step 5: Confirm canonical slug exists locally**

```powershell
python manage.py shell -c "from django_apps.asteroid_lab import models as m; p=m.AsteroidProject.objects.filter(slug='copy-import-495e552c').first(); print('project_id', p.pk if p else None)"
```

Expected: positive `project_id`. If `None`, **BLOCKED:** restore/import slug before Task 4.

---

### Task 1: CLI plumbing (`--deferred-retry-execute`)

**Files:**
- Modify: `django_apps/asteroid_lab/management/commands/run_solver.py`

- [ ] **Step 1: Add import and argument**

At top imports, extend `solver_run_config_keys`:

```python
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY,
    SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY,
    SOLVER_RUN_CONFIG_RTTP_RECORD_REPLAY_KEY,
)
```

In `add_arguments`, after `--json`:

```python
        parser.add_argument(
            "--deferred-retry-execute",
            action="store_true",
            help=(
                "Set config_json deferred_retry_shadow to enabled=true, "
                "observe_only=false (PR-4 normative ops entrypoint)."
            ),
        )
```

- [ ] **Step 2: Inject fixed config in `handle`**

After building `config: dict[str, Any] = {}` and existing `macro_only` / `no_replay` blocks, add:

```python
        if options["macro_only"] and options["deferred_retry_execute"]:
            raise CommandError(
                "Cannot combine --macro-only with --deferred-retry-execute "
                "(v0.1 normal RTTP path only)."
            )
        if options["deferred_retry_execute"]:
            config[SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY] = {
                "enabled": True,
                "observe_only": False,
            }
```

- [ ] **Step 3: Ruff on touched file**

```powershell
python -m ruff check django_apps/asteroid_lab/management/commands/run_solver.py
python -m black --check django_apps/asteroid_lab/management/commands/run_solver.py
```

Expected: PASS.

- [ ] **Step 4: Commit**

```powershell
git add django_apps/asteroid_lab/management/commands/run_solver.py
git commit -m "feat(asteroid-lab): add --deferred-retry-execute to run_solver CLI"
```

---

### Task 2: PowerShell wrapper

**Files:**
- Modify: `scripts/run_solver.ps1`

- [ ] **Step 1: Add switch and pass-through**

Update param block:

```powershell
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Slug,

    [string]$RunKey,
    [switch]$MacroOnly,
    [switch]$NoReplay,
    [switch]$Json,
    [switch]$DeferredRetryExecute
)
```

After `$Json` block:

```powershell
if ($DeferredRetryExecute) {
    $argsList += "--deferred-retry-execute"
}
```

- [ ] **Step 2: Smoke help text (optional comment at top of file)**

Add one-line comment above `param`:

```powershell
# PR-4 ops: -DeferredRetryExecute -> manage.py --deferred-retry-execute
```

- [ ] **Step 3: Commit**

```powershell
git add scripts/run_solver.ps1
git commit -m "chore(scripts): run_solver.ps1 -DeferredRetryExecute switch"
```

---

### Task 3: Unit / command regression tests

**Files:**
- Modify: `tests/unit/asteroid_lab/test_run_solver_management_command.py`

- [ ] **Step 1: Add import**

```python
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY,
    SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY,
)
```

- [ ] **Step 2: Write `test_run_solver_deferred_retry_execute_sets_config`**

```python
@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_deferred_retry_execute_sets_config() -> None:
    proj = m.AsteroidProject.objects.create(name="CliDefer", slug="cli-run-defer-exec")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    out = StringIO()
    with pytest.raises(SystemExit) as exc_info:
        call_command(
            "run_solver",
            slug=proj.slug,
            deferred_retry_execute=True,
            no_replay=True,
            stdout=out,
            stderr=StringIO(),
        )
    assert exc_info.value.code == 1
    run = m.SolverRun.objects.filter(project_id=proj.pk).order_by("-id").first()
    assert run is not None
    shadow = (run.config_json or {}).get(SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY)
    assert shadow == {"enabled": True, "observe_only": False}
    assert run.config_json.get(SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY) is not True
```

- [ ] **Step 3: Write `test_run_solver_deferred_retry_execute_json_stdout`**

```python
@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_deferred_retry_execute_json_stdout() -> None:
    proj = m.AsteroidProject.objects.create(name="CliDeferJson", slug="cli-run-defer-json")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    out = StringIO()
    with pytest.raises(SystemExit) as exc_info:
        call_command(
            "run_solver",
            slug=proj.slug,
            deferred_retry_execute=True,
            no_replay=True,
            json=True,
            stdout=out,
            stderr=StringIO(),
        )
    assert exc_info.value.code == 1
    body = json.loads(out.getvalue())
    assert body.get("solver_run_id") is not None
    assert "solver_summary" in body
```

- [ ] **Step 4: Write `test_run_solver_macro_only_and_deferred_retry_raises`**

```python
def test_run_solver_macro_only_and_deferred_retry_raises() -> None:
    proj = m.AsteroidProject.objects.create(name="CliConflict", slug="cli-run-defer-conflict")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    with pytest.raises(CommandError, match="Cannot combine"):
        call_command(
            "run_solver",
            slug=proj.slug,
            macro_only=True,
            deferred_retry_execute=True,
            stderr=StringIO(),
        )
```

- [ ] **Step 5: Run tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_run_solver_management_command.py -v --tb=short
```

Expected: all PASS (including new tests).

- [ ] **Step 6: Commit**

```powershell
git add tests/unit/asteroid_lab/test_run_solver_management_command.py
git commit -m "test(asteroid-lab): run_solver --deferred-retry-execute config wiring"
```

---

### Task 4: Ops smoke (real slug)

**Files:** none (runtime + shell readback)

**Normative command:**

```powershell
python manage.py run_solver --slug copy-import-495e552c --deferred-retry-execute
```

Alternative:

```powershell
powershell -File scripts/run_solver.ps1 -Slug copy-import-495e552c -DeferredRetryExecute
```

- [ ] **Step 1: Run smoke**

```powershell
python manage.py run_solver --slug copy-import-495e552c --deferred-retry-execute
```

Expected: exit code `0`. Capture `solver_run_id` from stdout.

On non-zero exit: **BLOCKED:** do not change PR-4 criteria; open separate bug track.

- [ ] **Step 2: Extract evidence + PR-4 assertions (shell)**

```powershell
python manage.py shell -c @"
from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId

slug = 'copy-import-495e552c'
proj = m.AsteroidProject.objects.get(slug=slug)
run = m.SolverRun.objects.filter(project_id=proj.pk).order_by('-id').first()
cfg = run.config_json or {}
ss = cfg.get('solver_summary') or {}
shadow_cfg = cfg.get('deferred_retry_shadow') or {}

print('solver_run_id', run.pk)
print('run_key', run.run_key)
print('shadow_cfg', shadow_cfg)
print('algorithm', ss.get('algorithm'))
print('validation_passed', ss.get('validation_passed'))
print('run_success', ss.get('run_success'))
print('issue_codes', ss.get('issue_codes'))
print('confirmed_count', ss.get('confirmed_count'))

def step(sid):
    for row in ss.get('algorithm_steps') or []:
        if row.get('step_id') == sid:
            return row
    return None

steps = ss.get('algorithm_steps') or []
ids = [row.get('step_id') for row in steps]

def idx(sid):
    return ids.index(sid) if sid in ids else -1

commit_i = idx(RttpAlgorithmStepId.RTTP_COMMIT.value)
shadow_i = idx(RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value)
exec_i = idx(RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_EXECUTE.value)
cat_i = idx(RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION.value)

print('order_commit', commit_i, 'shadow', shadow_i, 'execute', exec_i, 'catalog', cat_i)

sh = step(RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value)
ex = step(RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_EXECUTE.value)
print('shadow.metrics.enabled', (sh or {}).get('metrics', {}).get('enabled'))
print('shadow.metrics.observe_only', (sh or {}).get('metrics', {}).get('observe_only'))
print('execute.metrics', (ex or {}).get('metrics'))
print('execute.passed', (ex or {}).get('passed'))

# PR-4-19
m = (ex or {}).get('metrics') or {}
attempted = m.get('deferred_retry_attempted_count')
recovered = m.get('deferred_retry_recovered_count')
still = m.get('deferred_retry_still_failed_count')
if attempted is not None and recovered is not None and still is not None:
    print('pr4_19_ok', still == attempted - recovered)
"@
```

- [ ] **Step 3: Manual checklist PR-4-1..23**

Map shell output to spec table [`2026-05-24-deferred-commit-retry-pr4-ops-smoke-design.md`](../specs/2026-05-24-deferred-commit-retry-pr4-ops-smoke-design.md).

| ID | Pass when |
|----|-----------|
| PR-4-1..5 | exit 0; algorithm `rttp_v0.1`; validation/run_success true; issue_codes `[]` |
| PR-4-6..8 | `shadow_cfg.enabled` true; `observe_only` false; run completed |
| PR-4-9..13 | shadow step exists; metrics keys present |
| PR-4-14..17 | execute step exists; order `shadow < execute < commit(final) < catalog`; execute metrics keys; `passed` true if present |
| PR-4-18..19 | rounds ∈ {0,1}; `still == attempted - recovered` |
| PR-4-20 | record `recovered_count` / `recovered_candidate_ids` only — **not** gate |
| PR-4-21..23 | commit, route_domain, catalog_placement_validation steps OK |

**Forbidden:** assert `deferred_retry_recovered_count > 0`.

- [ ] **Step 4: Standing regression after smoke**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py tests/unit/asteroid_lab/test_rttp_commit_survivability.py tests/unit/asteroid_lab/test_run_solver_management_command.py -v --tb=short
powershell -File scripts/test_optimization_contamination.ps1
```

Expected: all PASS.

---

### Task 5: Evidence + docs close

**Files:**
- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`
- Modify: `docs/superpowers/specs/2026-05-24-deferred-commit-retry-pr4-ops-smoke-design.md`
- Modify: `docs/superpowers/plans/2026-05-24-deferred-commit-retry-pr4-ops-smoke.md`

- [ ] **Step 1: Add `current_plan.md` CLOSED entry**

After PR-3 row, add:

```markdown
- Deferred commit retry PR-4 — Real-map ops smoke (`--deferred-retry-execute`)
  - Status: **CLOSED** (master)
  - Merged into master: `<plumbing-merge-sha>` (PR #<n>)
  - Ops evidence: `python manage.py run_solver --slug copy-import-495e552c --deferred-retry-execute` exit 0 (`solver_run_id` <id>, `run_key` <key>)
  - Config readback: `deferred_retry_shadow.enabled` true, `observe_only` false
  - Steps: `rttp.deferred_commit_retry_shadow`, `rttp.deferred_commit_retry_execute` present; order commit → shadow → execute
  - Execute metrics (informational): `deferred_retry_recovered_count` <n>, `deferred_retry_eligible_count` <n>
  - `validation_passed` / `run_success` true; `issue_codes` `[]`
  - Spec: [`docs/superpowers/specs/2026-05-24-deferred-commit-retry-pr4-ops-smoke-design.md`](...)
  - Plan: [`docs/superpowers/plans/2026-05-24-deferred-commit-retry-pr4-ops-smoke.md`](...)
```

Update **Priority** line: deferred retry slice 1–4 CLOSED; next queue TBD (no GA/macro/capacity).

- [ ] **Step 2: Update roadmap**

In deferred retry section:

```markdown
| PR-4 ops smoke | ✅ | [`<merge-sha>`](...) PR #<n>; ops `solver_run_id` <id> |
```

**Open next:** remove PR-4 design; optional note: deferred commit retry slice 1–4 CLOSED.

- [ ] **Step 3: Mark spec + plan CLOSED**

Spec front matter:

```markdown
**Status:** CLOSED 2026-05-24 — ops smoke PASS; plumbing `<merge-sha>` PR #<n>
```

Plan front matter:

```markdown
**Status:** CLOSED 2026-05-24 — ops smoke PASS
```

- [ ] **Step 4: Commit docs (same PR as plumbing or follow-up on master after merge)**

```powershell
git add documents/ai/current_plan.md docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md docs/superpowers/specs/2026-05-24-deferred-commit-retry-pr4-ops-smoke-design.md docs/superpowers/plans/2026-05-24-deferred-commit-retry-pr4-ops-smoke.md
git commit -m "docs(asteroid-lab): close deferred commit retry PR-4 ops smoke"
```

---

### Task 6: PR, CI, merge

**Files:** none

- [ ] **Step 1: Full gate before PR**

```powershell
powershell -File scripts/test_full.ps1
python -m ruff check django_apps/asteroid_lab/management/commands/run_solver.py tests/unit/asteroid_lab/test_run_solver_management_command.py
python -m black --check django_apps/asteroid_lab/management/commands/run_solver.py tests/unit/asteroid_lab/test_run_solver_management_command.py scripts/run_solver.ps1
```

Expected: pytest PASS; ruff/black PASS.

- [ ] **Step 2: Push and open PR**

```powershell
git push -u origin feat/deferred-commit-retry-pr4-ops-smoke
```

PR title: `feat(asteroid-lab): deferred commit retry PR-4 ops smoke CLI`

PR body:

```markdown
## Summary
- Add normative `--deferred-retry-execute` to `manage.py run_solver` (fixed deferred_retry_shadow config)
- Add `-DeferredRetryExecute` to `scripts/run_solver.ps1`
- Unit tests for config persistence and flag composition
- Ops smoke evidence on `copy-import-495e552c` (docs close)

## Test plan
- [x] test_run_solver_management_command.py (new deferred retry tests)
- [x] deferred retry PR-1..PR-3 regression pytest
- [x] test_optimization_contamination.ps1
- [x] `python manage.py run_solver --slug copy-import-495e552c --deferred-retry-execute` exit 0
```

- [ ] **Step 3: CI green → squash merge**

Monitor `ci` + `rttp-lab-macro-smoke`. Merge when green.

---

### Task 7: Self-review (PR-4-1..23 + scope)

**Files:** none

- [ ] **Step 1: Spec coverage matrix**

| Spec section | Task |
|--------------|------|
| Normative `--deferred-retry-execute` | Task 1, 2 |
| Fixed JSON inject | Task 1 |
| No `--config-json-path` | File map explicit |
| No algorithm change | File map explicit |
| PR-4-1..23 criteria | Task 4 Step 3 |
| No recovered_count gate | Task 4 Forbidden |
| Closure artifacts | Task 5 |
| Standing regression | Task 0, 4, 6 |

- [ ] **Step 2: Out-of-scope scan**

Confirm diff excludes: `deferred_retry_execute.py`, `pipeline.py`, `incremental_commit.py`, generic config loader, GA/macro/capacity docs.

- [ ] **Step 3: Optional roadmap sentence (informational only)**

After PR-4 CLOSED, may add one line under deferred retry: **slice 1–4 CLOSED**. **Commit survivability arc CLOSED** remains optional human declaration — not a PR-4 pass criterion.

---

## Plan self-review

| Check | Result |
|-------|--------|
| Placeholder / TBD in task steps | None |
| Spec PR-4-1..23 mapped | Task 4 Step 3 + shell script |
| A normative only | Tasks 1–2; no config-json-path |
| Complete test code in plan | Task 3 |
| Ops slug preflight | Task 0 Step 5 |
| BLOCKED on smoke fail | Task 4 Step 1 |

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-24-deferred-commit-retry-pr4-ops-smoke.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration  
2. **Inline Execution** — this session with `executing-plans`, batch execution with checkpoints  

**Which approach?**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** superpowers:subagent-driven-development

**If Inline Execution chosen:**
- **REQUIRED SUB-SKILL:** superpowers:executing-plans
