# RTTP Pass-Capable Slug Certification (Track B) Implementation Plan

**Status:** **CLOSED (2026-05-30)** — Task 4 complete; registered `rttp-cert-candidate-tiny-passable-v2`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Register at least one **pass_capable** Lab slug with recorded T3 certification evidence under v0.1 RTTP default config, while keeping `copy-import-495e552c` as **diagnostic_canon** only.

**Architecture:** Extend `contracts/rttp_ops_policy.py` with pass-capable registry + pure `evaluate_t3_certification`; batch scan via management command calling existing `run_solver_runtime_for_project`; wire slug class into `classify_t2_policy` / `build_rttp_solver_summary`; Lab/CLI display only.

**Tech Stack:** Python 3.12+, Django 5.2, pytest, ruff, mypy (`django_apps config src`).

**Design spec (APPROVED):** [`docs/superpowers/specs/2026-05-30-rttp-pass-capable-slug-certification-design.md`](../specs/2026-05-30-rttp-pass-capable-slug-certification-design.md)

**Prerequisite:** D-PR [#99](https://github.com/tigers2020/Shapez2Factory/pull/99) merged (`rttp_ops_slug_class` + T2 policy on diagnostic canon).

---

## File structure

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/contracts/rttp_ops_policy.py` | `RTTP_PASS_CAPABLE_SLUGS`, `resolve_rttp_ops_slug_class`, `evaluate_t3_certification`, cert status tokens |
| `django_apps/asteroid_lab/management/commands/scan_rttp_slug_certification.py` | Batch/single slug scan + JSON report |
| `django_apps/asteroid_lab/optimization/rttp_solver_summary.py` | Use resolved slug class in T2 policy merge |
| `django_apps/asteroid_lab/services/solver_run_lab_summary.py` | Project `rttp_ops_slug_class`, optional `ops_tier_summary` |
| `django_apps/asteroid_lab/management/commands/run_solver.py` | Optional pass_capable stdout line |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | Badge/copy by slug class |
| `tests/unit/asteroid_lab/test_rttp_ops_slug_classification.py` | Registry + precedence |
| `tests/unit/asteroid_lab/test_rttp_t3_certification_evaluator.py` | B-T3-* evaluator |
| `tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py` | Extend pass_capable shortfall cases |
| `docs/superpowers/reports/YYYY-MM-DD-rttp-pass-capable-slug-certification.json` | Ops evidence (not algorithm input) |
| `documents/ai/current_plan.md` | ACTIVE → CLOSED + evidence row |
| `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | Open next → B CLOSED |

**Not modified:** `throughput_target.py`, `pipeline.py` validation logic, `final_validation.py`, macro path, GA selection beyond default config.

---

## Spec → plan coverage

| Spec § | Task |
|--------|------|
| §3 Slug classes | Task 1 |
| §4 T3 certification | Task 1 |
| §5 Scan policy | Tasks 2–3 |
| §6 Evidence | Tasks 3–5 |
| §7 Lab/CLI | Task 6 |
| §8 Tests | Task 7 |
| §9 Rollout / close | Task 8 |

---

### Task 0 — Read current ops tier / D policy / roadmap

**Files:** Read-only

- [ ] **Step 1:** Read [`2026-05-30-rttp-ops-authority-tier-design.md`](../specs/2026-05-30-rttp-ops-authority-tier-design.md) §4–§6 (T3 criteria).
- [ ] **Step 2:** Read [`2026-05-30-rttp-throughput-policy-t2-diagnostic-canon-design.md`](../specs/2026-05-30-rttp-throughput-policy-t2-diagnostic-canon-design.md) §3–§6 (`rttp_ops_slug_class`).
- [ ] **Step 3:** Confirm D-PR merged on `master` (`rttp_ops_policy.py` has `classify_t2_policy`).
- [ ] **Step 4:** Note post-FL-06 diagnostic canon readback (T1b PASS; T2 expected shortfall) from `current_plan.md`.

---

### Task 1 — Slug class contract + T3 evaluator

**Files:**
- Modify: `django_apps/asteroid_lab/contracts/rttp_ops_policy.py`
- Create: `tests/unit/asteroid_lab/test_rttp_ops_slug_classification.py`
- Create: `tests/unit/asteroid_lab/test_rttp_t3_certification_evaluator.py`

- [ ] **Step 1: Write failing tests for registry precedence**

```python
# test_rttp_ops_slug_classification.py (sketch)
from django_apps.asteroid_lab.contracts.rttp_ops_policy import (
    RTTP_DIAGNOSTIC_CANON_SLUG,
    RTTP_PASS_CAPABLE_SLUGS,
    RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON,
    RTTP_OPS_SLUG_CLASS_PASS_CAPABLE,
    RTTP_OPS_SLUG_CLASS_UNKNOWN,
    resolve_rttp_ops_slug_class,
)

def test_diagnostic_canon_not_pass_capable_even_if_in_both_lists() -> None:
    # If misconfigured, diagnostic wins — add test once RTTP_PASS_CAPABLE_SLUGS exists
    assert resolve_rttp_ops_slug_class(RTTP_DIAGNOSTIC_CANON_SLUG) == RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON
```

- [ ] **Step 2: Write failing tests for `evaluate_t3_certification`**

Fixture dicts mimicking `solver_summary` + minimal `pipeline_steps` list:
- `certified_pass` — all B-T3 fields true
- `fail_t2` — `throughput_budget_satisfied` false
- `fail_t1b` — `rttp.commit` step `passed` false

- [ ] **Step 3: Implement tokens + registry**

Add to `rttp_ops_policy.py`:

```python
RTTP_OPS_SLUG_CLASS_PASS_CAPABLE = "pass_capable"
RTTP_PASS_CAPABLE_SLUGS: frozenset[str] = frozenset()  # populate in Task 5

CERT_STATUS_CERTIFIED_PASS = "certified_pass"
CERT_STATUS_FAIL_T1B = "fail_t1b"
# ... per spec §4 failure taxonomy
```

- [ ] **Step 4: Implement `resolve_rttp_ops_slug_class` and `evaluate_t3_certification`**

- [ ] **Step 5: Update `classify_t2_policy` to call `resolve_rttp_ops_slug_class`**

Rules:
- `pass_capable` + budget false → `shortfall`, never `expected_diagnostic_shortfall`
- `diagnostic_canon` unchanged from D-PR

- [ ] **Step 6: Run narrow pytest**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_ops_slug_classification.py tests/unit/asteroid_lab/test_rttp_t3_certification_evaluator.py tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py -v
python -m ruff check django_apps/asteroid_lab/contracts/rttp_ops_policy.py
```

---

### Task 2 — Scan command skeleton

**Files:**
- Create: `django_apps/asteroid_lab/management/commands/scan_rttp_slug_certification.py`
- Create: `tests/unit/asteroid_lab/test_scan_rttp_slug_certification_command.py` (dry-run + mocked runtime)

- [ ] **Step 1: Failing test — dry-run lists slugs, excludes diagnostic canon**

- [ ] **Step 2: Implement command**

Behavior:
- Query `AsteroidProject` with map input
- Skip `RTTP_DIAGNOSTIC_CANON_SLUG` with `cert_status=skipped_diagnostic`
- For each slug: invoke same runtime as `run_solver` (import `run_solver_runtime_for_project` or shared helper)
- Build row via `evaluate_t3_certification` from returned summary + steps
- Write JSON per spec §6

Flags: `--slug`, `--all`, `--limit`, `--output`, `--dry-run`, `--no-replay` (default true)

- [ ] **Step 3: pytest + ruff**

```powershell
python -m pytest tests/unit/asteroid_lab/test_scan_rttp_slug_certification_command.py -v
python -m ruff check django_apps/asteroid_lab/management/commands/scan_rttp_slug_certification.py
```

---

### Task 3 — Run default RTTP scan on stored projects

**Files:**
- Create: `docs/superpowers/reports/2026-05-30-rttp-pass-capable-slug-certification.json` (initial empty or dry-run)

- [ ] **Step 1: Dry-run inventory**

```powershell
python manage.py scan_rttp_slug_certification --all --dry-run
```

Record slug count in PR notes.

- [ ] **Step 2: Batch scan (local DB)**

```powershell
python manage.py scan_rttp_slug_certification --all --no-replay --output docs/superpowers/reports/2026-05-30-rttp-pass-capable-slug-certification.json
```

Optional: `--limit 10` for first pass.

- [ ] **Step 3: Identify `first_certified_slug`**

If none: **stop** — document in report + `current_plan` BLOCKED note (no cert criteria weakening). Do not proceed to Task 5 registration without product decision (Track A or new map).

---

### Task 4 — Register first pass_capable slug

**Depends on:** Task 3 found `certified_pass` candidate

**Files:**
- Modify: `django_apps/asteroid_lab/contracts/rttp_ops_policy.py` — `RTTP_PASS_CAPABLE_SLUGS`
- Modify: evidence JSON `registered_pass_capable_slugs`

- [x] **Step 1: Confirmation re-run**

```powershell
python manage.py run_solver --slug <candidate_slug> --no-replay
```

Record second `solver_run_id` in JSON `confirmation_run`.

- [x] **Step 2: Add slug to `RTTP_PASS_CAPABLE_SLUGS`**

```python
RTTP_PASS_CAPABLE_SLUGS: frozenset[str] = frozenset({"<candidate_slug>"})
```

- [x] **Step 3: Re-run policy tests — pass_capable shows `rttp_ops_slug_class=pass_capable` on summary**

```powershell
python manage.py run_solver --slug <candidate_slug> --no-replay
```

Verify B-T3-* readback on confirmation run.

---

### Task 5 — T3 evidence row in current_plan.md

**Files:**
- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`

- [x] **Step 1: Add CLOSED block** — see `current_plan.md` (2026-05-30)

- [x] **Step 2: Demote ACTIVE Track B row** — Track A not opened

- [x] **Step 3: Roadmap table** — Pass-capable slug (B) CLOSED

---

### Task 6 — Lab / CLI diagnostic distinction

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_run_lab_summary.py`
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- Modify: `django_apps/asteroid_lab/management/commands/run_solver.py` (optional line)
- Modify: `django_apps/web/static/web/css/app.css` only if badge needs minimal class (avoid unrelated edits)

- [ ] **Step 1: Project `rttp_ops_slug_class` into Lab summary API**

- [ ] **Step 2: JS — diagnostic vs pass_capable vs unknown copy (spec §7)**

Do not remove D-PR `diagnostic_expected_shortfall` behavior.

- [ ] **Step 3: CLI line when pass_capable + validation passed**

- [ ] **Step 4: Narrow web/unit tests if present for lab summary**

---

### Task 7 — Narrow tests + standing gates

- [ ] **Step 1: Full Track B unit set**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_ops_slug_classification.py tests/unit/asteroid_lab/test_rttp_t3_certification_evaluator.py tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py tests/unit/asteroid_lab/test_scan_rttp_slug_certification_command.py -v
```

- [ ] **Step 2: RTTP narrow gate**

```powershell
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v
```

- [ ] **Step 3: Contamination gate**

```powershell
powershell -File scripts/test_optimization_contamination.ps1
```

- [ ] **Step 4: Control — diagnostic canon unchanged**

```powershell
python manage.py run_solver --slug copy-import-495e552c --no-replay
```

Expect `expected_diagnostic_shortfall`; exit code may remain non-zero per validation — **do not** “fix” for this task.

---

### Task 8 — Docs close (B-GOV + B-PR)

- [ ] **Step 1:** Mark spec §11 acceptance checkboxes for B-PR items completed.
- [ ] **Step 2:** Update design spec **Status** to `CLOSED (YYYY-MM-DD)` when all B-PR criteria met.
- [ ] **Step 3:** Plan file — mark tasks checked; add Self-review table (below).

---

## Forbidden shortcuts checklist (Task 7+)

| Forbidden | Verify |
|-----------|--------|
| Lower `reconstruction_max` | No capacity module edits |
| Change throughput target formula | `throughput_target.py` untouched |
| Weaken `validation_passed` | Evaluator read-only; pipeline unchanged |
| Promote diagnostic canon to pass_capable | Registry excludes `copy-import-495e552c` |
| Fake `throughput_budget_satisfied` | Tests assert numeric truth preserved |
| Use replay as algorithm input | Scan uses live runtime only |
| Full GA / macro unpause | No scope |

---

## Self-review (plan author)

| Check | Result |
|-------|--------|
| Spec §1–§10 covered | Tasks 0–8 |
| Same runtime path as `run_solver` | Task 2 |
| T3 = commit + validation + T2 | Task 1 evaluator |
| D-PR coexistence | Task 1 updates `classify_t2_policy` |
| Null scan outcome documented | Task 3 Step 3 |

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-30-rttp-pass-capable-slug-certification.md`.

**Recommended sequence:**

```text
Merge D-PR #99
→ Task 1–2 (contracts + scan command)
→ Task 3–4 (scan + register slug)
→ Task 5–8 (evidence + UI + close)
```

**1. Subagent-Driven** — fresh subagent per task, review between tasks  

**2. Inline Execution** — this session with executing-plans checkpoints  

---

## BLOCKED template (no pass_capable candidate found)

```text
BLOCKED:
- missing context: No AsteroidProject slug satisfied B-T3-* on certification config after full scan.
- risky change: Weakening cert criteria or promoting copy-import-495e552c would violate Track B/D contracts.
- recommended next step: Product chooses Track A (algorithm on diagnostic canon) or import/register simpler Lab map; re-run Task 3.
```
