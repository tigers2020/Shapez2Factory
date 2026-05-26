# RTTP Task 6 — Lab pass_capable Badge (Execution Plan)

**Status:** **IMPLEMENTED** (2026-05-30, branch `feat/rttp-lab-pass-capable-badge`)  
**Classification:** UI change + narrow regression  
**Parent:** [`2026-05-30-rttp-pass-capable-slug-certification.md`](2026-05-30-rttp-pass-capable-slug-certification.md) Task 6  
**Design:** [`../specs/2026-05-30-rttp-pass-capable-slug-certification-design.md`](../specs/2026-05-30-rttp-pass-capable-slug-certification-design.md) §7  
**Branch (suggested):** `feat/rttp-lab-pass-capable-badge`

**Prerequisite (CLOSED):** Track B #101 — `rttp-cert-candidate-tiny-passable-v2` in `RTTP_PASS_CAPABLE_SLUGS`.

---

## Goal

Lab and CLI show **slug class** (`diagnostic_canon` | `pass_capable` | `unknown`) without weakening D-PR diagnostic copy on `copy-import-495e552c`.

---

## Already on master (do not redo)

| Area | State |
|------|--------|
| `solver_run_lab_summary.py` | `rttp_ops_slug_class` in `_t2_policy_section_fields` / throughput section |
| `rttp_solver_summary.py` | Persists `rttp_ops_slug_class` on `SolverRun` summary |
| D-PR Lab JS | `diagnostic_expected_shortfall` copy + capacity-failed guard |
| Registry | `RTTP_PASS_CAPABLE_SLUGS`, `resolve_rttp_ops_slug_class` |

---

## Remaining work

### Task A — Lab run list / HUD badge

**Files:**

- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- `django_apps/web/static/web/css/app.css` (minimal badge class only)

**Steps:**

1. Read `rttp_ops_slug_class` from Lab summary API row (same path as `diagnostic_expected_shortfall`).
2. Render badge:
   - `diagnostic_canon` → existing D-PR strings (no regression)
   - `pass_capable` → e.g. “T3 reference slug” when `t3_ops_eligible` or cert-consistent; T2 shortfall = regression wording
   - `unknown` → neutral; no “expected diagnostic” on shortfall
3. Do **not** treat `throughput_budget_satisfied === false` as milestone failure when `diagnostic_expected_shortfall === true` (preserve D-PR).

### Task B — CLI one-liner (optional)

**File:** `django_apps/asteroid_lab/management/commands/run_solver.py`

- After run: print `rttp_ops_slug_class=<class>` when slug in registry or summary present.

### Task C — Tests

**Narrow:**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py tests/unit/asteroid_lab/test_rttp_ops_slug_classification.py -v --tb=short
```

**Control (must not change):**

```powershell
python manage.py run_solver --slug copy-import-495e552c --no-replay
```

Expect `expected_diagnostic_shortfall` / diagnostic canon class.

**Pass-capable smoke:**

```powershell
python manage.py run_solver --slug rttp-cert-candidate-tiny-passable-v2 --no-replay
```

### Task D — Gates

```powershell
powershell -File scripts/test_optimization_contamination.ps1
python -m ruff check django_apps/asteroid_lab/services/solver_run_lab_summary.py django_apps/asteroid_lab/management/commands/run_solver.py django_apps/web/static/web/js/asteroid_miner_layout_lab.js
```

---

## Forbidden

- Promote `copy-import-495e552c` to `pass_capable`
- Mask T2 shortfall on diagnostic canon
- Change throughput formulas or `validation_passed` semantics

---

## Close criteria

- [x] Lab shows distinct badge/copy for `pass_capable` on v2 slug
- [x] Diagnostic canon behavior unchanged (D-PR tests green)
- [ ] `current_plan.md` Task 6 row → CLOSED with PR link (after merge)
