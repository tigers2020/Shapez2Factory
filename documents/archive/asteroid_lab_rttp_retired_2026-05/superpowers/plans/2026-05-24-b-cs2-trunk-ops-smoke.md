# B-CS2 Trunk Ops Smoke Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close Axis B milestone B-CS2 by proving commit-time RTTP closure on real slug `copy-import-495e552c` using output-only `solver_summary` evidence — no solver code changes.

**Architecture:** Docs-only ops milestone. B-CS1 pytest holds the reprobe invariant; B-CS2 runs `manage.py run_solver`, extracts persisted `config_json.solver_summary`, asserts spec IDs B-CS2-1..17, then updates `current_plan.md` and roadmap.

**Tech Stack:** Django `manage.py run_solver`, `SolverRun.config_json`, PowerShell, optional `python manage.py shell`

**Spec:** [`docs/superpowers/specs/2026-05-24-b-cs2-trunk-ops-smoke-design.md`](../specs/2026-05-24-b-cs2-trunk-ops-smoke-design.md)

---

## File map

| Action | Path | Why |
|--------|------|-----|
| Read | `docs/superpowers/specs/2026-05-24-b-cs2-trunk-ops-smoke-design.md` | Pass/fail authority |
| Read | `django_apps/asteroid_lab/optimization/rttp_solver_summary.py` | Step id strings |
| Read | `django_apps/asteroid_lab/optimization/pipeline.py` | Commit / route_domain metrics |
| Run | `manage.py run_solver` | Ops smoke |
| Modify | `documents/ai/current_plan.md` | B-CS2 CLOSED evidence |
| Modify | `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | B-CS2 ✅, Axis B % |

**No** changes under `django_apps/asteroid_lab/optimization/` unless smoke fails and a **separate** bug fix is approved.

---

### Task 0 — Preconditions (BLOCK gate)

**Files:** none

- [x] **Step 1: Confirm branch and merges**

```powershell
git fetch origin
git rev-parse HEAD
git merge-base --is-ancestor dfbda7b8 HEAD; if ($LASTEXITCODE -ne 0) { throw "PR-3 merge dfbda7b8 not on HEAD" }
```

Expected: `HEAD` includes `dfbda7b8` (D+ PR-3 on `master`).

- [ ] **Step 2: Confirm B-CS1 regression exists**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_commit_survivability.py -v
```

Expected: all tests PASS.

- [ ] **Step 3: Confirm slug project exists locally**

```powershell
python manage.py shell -c "from django_apps.asteroid_lab import models as m; p=m.AsteroidProject.objects.filter(slug='copy-import-495e552c').first(); print('project_id', p.pk if p else None)"
```

Expected: `project_id` is a positive integer (not `None`). If `None`, **BLOCKED:** import or restore Lab slug before smoke.

---

### Task 1 — Ops smoke execution (plan Step 1)

**Files:** none (runtime only)

- [ ] **Step 1: Run canonical smoke**

```powershell
python manage.py run_solver --slug copy-import-495e552c
```

Expected: process exit code `0`. Capture stdout for `solver_run_id` / `run_key` if printed.

- [ ] **Step 2: On non-zero exit**

Stop. Do **not** change pass criteria. File `BLOCKED:` with stderr tail + last `SolverRun` row if any. Open bug track separate from B-CS2 doc edits.

---

### Task 2 — Evidence extraction

**Files:** none

- [ ] **Step 1: Dump summary + steps (copy output into PR/plan notes)**

```powershell
python manage.py shell -c @"
from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId

slug = 'copy-import-495e552c'
proj = m.AsteroidProject.objects.get(slug=slug)
run = m.SolverRun.objects.filter(project_id=proj.pk).order_by('-id').first()
print('solver_run_id', run.pk)
print('run_key', run.run_key)
cfg = run.config_json or {}
ss = cfg.get('solver_summary') or {}
print('algorithm', ss.get('algorithm'))
print('validation_passed', ss.get('validation_passed'))
print('run_success', ss.get('run_success'))
print('confirmed_count', ss.get('confirmed_count'))
print('commit_order_len', len(ss.get('commit_order') or []))
print('issue_codes', ss.get('issue_codes'))

def step(sid):
    for row in ss.get('algorithm_steps') or []:
        if row.get('step_id') == sid:
            return row
    return None

rd = step(RttpAlgorithmStepId.RTTP_ROUTE_DOMAIN.value)
cp = step(RttpAlgorithmStepId.RTTP_CANDIDATE_POOL.value)
gs = step(RttpAlgorithmStepId.RTTP_GENOME_SELECTION.value)
cm = step(RttpAlgorithmStepId.RTTP_COMMIT.value)
cat = step(RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION.value)

print('route_domain.metrics', (rd or {}).get('metrics'))
print('candidate_pool.metrics', (cp or {}).get('metrics'))
print('genome_selection.metrics', (gs or {}).get('metrics'))
print('commit.metrics', (cm or {}).get('metrics'))
print('commit.passed', (cm or {}).get('passed'))
print('catalog_placement.metrics', (cat or {}).get('metrics'))
"@
```

- [ ] **Step 2: Fill evidence checklist**

Record in working notes (then `current_plan.md`):

| Field | Value |
|-------|-------|
| `solver_run_id` | from shell |
| `run_key` | from shell |
| `confirmed_count` | |
| `commit_order` length | |
| `committed_ids` length | |
| `conflict_count` | informational |
| `skeleton_id` | route_domain |
| `mismatched_existing_transport_count` | route_domain |
| `normal_count` | candidate_pool (informational) |
| `unmapped_candidate_count` | catalog step if present (informational, not B-CS2 gate) |

---

### Task 3 — Assert B-CS2-1..17 (manual gate)

**Files:** none

- [ ] **Step 1: Map shell output to spec table**

Use [`2026-05-24-b-cs2-trunk-ops-smoke-design.md`](../specs/2026-05-24-b-cs2-trunk-ops-smoke-design.md) § Pass criteria.

Minimum programmatic spot-check (optional; run after shell dump):

```powershell
python manage.py shell -c @"
from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId

proj = m.AsteroidProject.objects.get(slug='copy-import-495e552c')
run = m.SolverRun.objects.filter(project_id=proj.pk).order_by('-id').first()
ss = (run.config_json or {}).get('solver_summary') or {}

assert ss.get('algorithm') == 'rttp_v0.1'
assert ss.get('validation_passed') is True
assert ss.get('run_success') is True
assert ss.get('issue_codes') == []
assert int(ss.get('confirmed_count') or 0) > 0
assert len(ss.get('commit_order') or []) > 0

steps = {r['step_id']: r for r in (ss.get('algorithm_steps') or [])}
commit = steps[RttpAlgorithmStepId.RTTP_COMMIT.value]
rd = steps[RttpAlgorithmStepId.RTTP_ROUTE_DOMAIN.value]
sel = steps[RttpAlgorithmStepId.RTTP_GENOME_SELECTION.value]

assert commit['passed'] is True
cm = commit['metrics']
assert len(cm.get('committed_ids') or []) > 0
assert cm.get('validation_passed') is True
assert list(cm.get('commit_order') or []) == list(ss.get('commit_order') or [])
assert rd['metrics'].get('skeleton_id')
assert 'mismatched_existing_transport_count' in (rd.get('metrics') or {})
assert len(sel['metrics'].get('commit_order') or []) > 0

order = [r['step_id'] for r in ss.get('algorithm_steps') or []]
core = [
    'reconstruction',
    'rttp.route_domain',
    'rttp.candidate_pool',
    'rttp.genome_selection',
    'rttp.commit',
]
idx = [order.index(s) for s in core]
assert idx == sorted(idx), order

# B-CS2-17: optional catalog_slice before route_domain; audit tail after commit
if 'rttp.catalog_slice' in order:
    assert order.index('rttp.catalog_slice') < order.index('rttp.route_domain'), order
assert order.index('rttp.commit') < order.index(
    RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION.value
), order

print('B-CS2 assertions OK', run.pk)
"@
```

Expected: `B-CS2 assertions OK <id>` and no AssertionError.

- [ ] **Step 2: On assertion failure**

`BLOCKED:` — attach failing ID (e.g. B-CS2-9), metrics snapshot, **do not** edit spec to match broken runtime without architect review.

---

### Task 4 — Narrow regression (safety net)

**Files:** none

- [ ] **Step 1: B-CS1 + RTTP narrow gate**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_commit_survivability.py -v
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map and not synthetic_lin_patterns" -v
```

Expected: PASS (no code changed; confirms no accidental env drift).

---

### Task 5 — Close plan docs

**Files:**

- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`

- [ ] **Step 1: Add to `current_plan.md` Closed section**

Template (fill values from Task 2):

```markdown
- B-CS2 — Trunk-connected commit ops smoke (real slug)
  - Status: **CLOSED**
  - Slug: `copy-import-495e552c`
  - Evidence: `python manage.py run_solver --slug copy-import-495e552c` exit 0 (`solver_run_id` <id>, `run_key` <key>)
  - `confirmed_count` > 0; `commit_order` non-empty; `rttp.commit` passed with non-empty `committed_ids`
  - `rttp.route_domain`: `skeleton_id` present; `mismatched_existing_transport_count` <n>
  - `validation_passed` / `run_success` true; `issue_codes` `[]`
  - Spec: [`2026-05-24-b-cs2-trunk-ops-smoke-design.md`](../../docs/superpowers/specs/2026-05-24-b-cs2-trunk-ops-smoke-design.md)
  - Prerequisite: B-CS1 `test_rttp_commit_survivability.py`; not a substitute for E5
```

- [ ] **Step 2: Update `Next focus` line**

Remove B-CS2 from open queue; set next to **B-CS3** validation gate audit (or whatever `current_plan.md` already lists after B-CS2).

- [ ] **Step 3: Roadmap B-CS2 row**

In § B-CS table: B-CS2 → ✅ with `solver_run_id` and date 2026-05-24.

Adjust Axis B progress bar note: B-CS2 closed; B-CS3 open.

- [ ] **Step 4: Commit docs-only (when user requests git commit)**

```powershell
git add docs/superpowers/specs/2026-05-24-b-cs2-trunk-ops-smoke-design.md docs/superpowers/plans/2026-05-24-b-cs2-trunk-ops-smoke.md documents/ai/current_plan.md docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md
git commit -m "docs(asteroid-lab): B-CS2 trunk ops smoke spec and closure"
```

---

## Plan self-review

| Spec section | Task |
|--------------|------|
| B-CS2-1..5 run shell | Task 1, 3 |
| B-CS2-6..12 commit proxy | Task 2, 3 |
| B-CS2-13..16 route-domain | Task 2, 3 |
| B-CS2-17 step order | Task 3 assert script |
| Forbidden (no solver edits) | File map + Task 1 Step 2 |
| Known slug zero transport | Spec § Known slug; no assert transport > 0 |
| E5 not gate | Spec § Explicitly not |
| Deliverables current_plan + roadmap | Task 5 |

**Placeholder scan:** none.

---

## Execution handoff

**Plan saved to:** `docs/superpowers/plans/2026-05-24-b-cs2-trunk-ops-smoke.md`

**Recommended mode:** **Inline execution** — single session, Tasks 0→5 sequential; no feature branch unless smoke fails and code fix is approved.

**First executable step after this plan:** Task 0 → Task 1 `run_solver` (not before spec/plan exist).

**Two execution options for follow-up:**

1. **Inline (recommended)** — run Tasks 0–5 in this session; report `solver_run_id` + assertion output.
2. **Subagent-Driven** — one subagent per task with review between Task 1 and Task 3.

Which approach do you want for smoke execution?

---

## Execution record (2026-05-24, Inline)

| Task | Result |
|------|--------|
| 0 | `dfbda7b8` ancestor OK; B-CS1 5/5 pass; `project_id` 1 |
| 1 | `run_solver` exit 0; `solver_run_id` 55; `macro_only_mode` False |
| 2–3 | Evidence dump + `B-CS2 assertions OK 55` (B-CS2-1..17) |
| 4 | B-CS1 + 127 narrow RTTP tests pass (~70s) |
| 5 | `current_plan.md` + roadmap B-CS2 CLOSED |

**Committed candidate:** `0,-10:cat_variant_BeltDefaultForwardInternalVariant_E:shape_belt` (catalog-native; commit proxy satisfied).
