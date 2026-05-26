# RTTP Throughput Policy — T2 Diagnostic Canon (Track D)

**Date:** 2026-05-30  
**Status:** Approved (2026-05-30)  
**Approval:** User approved Track D approach **C** (policy/observability only; no forced T2 PASS on diagnostic canon).  
**Owner:** RTTP throughput policy / asteroid-lab runtime  
**Track:** **D** — throughput policy (T2 ops authority), **observation-first**  
**User decision:** **C** — policy and observability only; do **not** force T2 PASS on diagnostic canon  
**Parent:** [`2026-05-30-rttp-ops-authority-tier-design.md`](2026-05-30-rttp-ops-authority-tier-design.md) §9 Track **D**  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)  
**Roadmap:** [`2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md)

**Predecessors (CLOSED, unchanged semantics):**

- PR-2a reconstruction max — [`2026-05-24-reconstruction-max-throughput-pr2a-design.md`](2026-05-24-reconstruction-max-throughput-pr2a-design.md)
- PR-2b actual committed — [`2026-05-24-actual-committed-throughput-pr2b.md`](../plans/2026-05-24-actual-committed-throughput-pr2b.md) (plan)
- PR-2c target percent — [`2026-05-24-throughput-target-percent-pr2c-design.md`](2026-05-24-throughput-target-percent-pr2c-design.md)
- PR-2d placement goals — [`2026-05-24-throughput-target-selection-pr2d-design.md`](2026-05-24-throughput-target-selection-pr2d-design.md)
- FL-06 T1b layout — [`2026-05-30-rttp-fl06-output-stub-route-reservation-alignment-design.md`](2026-05-30-rttp-fl06-output-stub-route-reservation-alignment-design.md) (MERGED PR #98)

**Follow-up (out of scope for D v1 implementation unless separate spec):**

- Track **B** — designate T3 pass-capable slug
- Track **A** — restore T2 PASS on legacy slug (explicit product approval only)
- Approach 3 target-cap policy — comparison appendix only; not v1 deliverable

---

## §1 — Problem

After FL-06, diagnostic canon `copy-import-495e552c` is authoritative for **T0** (selection-path) and **T1a/T1b** (commit executed + layout valid on recent runs). **T2** still fails at every allowed `throughput_target_percent` (10–80%):

| Metric | Typical readback (post complete-map C-GATE class) | Role |
|--------|---------------------------------------------------|------|
| A `reconstruction_max_throughput_per_min` | ~75360 | Theoretical terrain upper bound (observation) |
| D `actual_committed_output_per_min` | ~3840 | Route-feasible committed production (authority) |
| C `target_throughput_per_min` | ≥7536 at min 10% | User budget vs A |
| `throughput_budget_satisfied` | `false` | **Truthful** numeric compare `D >= C` |
| `throughput_target_shortfall` | in `issue_codes` | Emitted when budget unsatisfied |

The gap (~2×) is not a wiring bug: it reflects **route-feasible placement** under v0.1 greedy-regret + commit survivability, not failure to read catalog or reconstruct terrain.

**Symptoms without policy:**

- Lab UI treats `throughput_budget_satisfied === false` as generic “capacity failed” (`asteroid_miner_layout_lab.js` `runCapacityFailed`).
- Ops readers conflate **T3 full-ops-pass** failure with unrelated PR regressions.
- Pressure to “fix” T2 via validation repair, denominator manipulation, or disguised PASS — all forbidden.

**Goal:**

```text
Fix policy authority: on diagnostic canon, T2 shortfall is an EXPECTED diagnostic outcome.
Preserve truthful throughput_budget_satisfied and issue_codes.
Add explicit t2_policy_* observability and Lab copy so T3 remains blocked until Track B.
```

---

## §2 — Non-goals (Track D v1)

| Item | Follow-up |
|------|-----------|
| Force T2 PASS on `copy-import-495e552c` (Track **A**) | Separate approved spec |
| New pass-capable slug (Track **B**) | Separate spec after D |
| Lower `MIN_THROUGHPUT_TARGET_PERCENT` without product decision | Forbidden in D |
| Change `reconstruction_max` computation (C-GATE) | Capacity track |
| Validation repair or weaken layout asserts | Track **E** closed; forbidden |
| Macro unpause, full GA, capacity solver changes | PAUSE / new spec |
| Target cap policy (Approach 3) as v1 deliverable | Appendix §13 only |
| Using replay / prior `solver_summary` as algorithm input | Forbidden (global) |

---

## §3 — Authority model

### Metric roles (normative)

```text
reconstruction_max_throughput_per_min (A)
  = theoretical observation from complete-map capacity envelope
  ≠ committed production authority
  ≠ implied achievable rate on diagnostic canon

actual_committed_output_per_min (D)
  = sum of route-confirmed committed bundle rates (PR-2b)
  = production authority for committed set

target_throughput_per_min (C)
  = ceil(A × throughput_target_percent / 100)   (PR-2c, unchanged)

throughput_budget_satisfied
  = (D >= C) only — never derived from pipeline_ok or validation_passed
```

### Ops tier alignment (C-track, unchanged)

| Tier | Diagnostic canon after FL-06 |
|------|------------------------------|
| T0 | PASS |
| T1a | PASS |
| T1b | PASS (layout; FL-06 class) |
| T2 | FAIL (numeric budget) + **expected policy** (this spec) |
| T3 | FAIL (requires T0+T1b+T2; blocked until pass-capable slug) |

**Invariant:** `t2_policy_status` explains **how to interpret** T2; it does **not** redefine `throughput_budget_satisfied`.

---

## §4 — Policy decision (Approach 1 + dual readback)

### Diagnostic canon registry

```python
# contracts/rttp_ops_policy.py (new module — name fixed at implementation)
RTTP_DIAGNOSTIC_CANON_SLUG = "copy-import-495e552c"
```

Slug list is **configuration/registry**, not hard-coded in validation. Additional diagnostic slugs require spec amendment + test.

### When slug is diagnostic canon and `throughput_budget_satisfied` is false

```text
t2_policy_status = "expected_diagnostic_shortfall"
t2_policy_reason  = "diagnostic_canon_route_feasible_gap"   # stable token; see §5
diagnostic_expected_shortfall = true
t3_ops_eligible = false
t3_blocked_reason = "t2_not_pass_capable_on_diagnostic_canon"
```

### When slug is not diagnostic (pass-capable or unknown) and budget false

```text
t2_policy_status = "shortfall"
diagnostic_expected_shortfall = false
t3_ops_eligible = false   # until T2 satisfied
```

### When budget satisfied

```text
t2_policy_status = "satisfied"
diagnostic_expected_shortfall = false
t3_ops_eligible = true    # T3 still needs T0+T1b per ops tier spec
```

### Forbidden mappings

```text
NEVER set throughput_budget_satisfied = true when D < C.
NEVER remove throughput_target_shortfall from issue_codes when D < C.
NEVER set validation_passed / run_success from t2_policy_status alone.
NEVER set t2_policy_status = "satisfied" on diagnostic canon solely because shortfall is expected.
```

---

## §5 — Contract tokens (no free-form strings)

All new persisted tokens MUST be defined in `django_apps/asteroid_lab/contracts/rttp_ops_policy.py` (or sibling const module) and covered by unit tests per repository forbidden-shortcut rules.

### `t2_policy_status` (required on RTTP runs with throughput fields)

| Value | Meaning |
|-------|---------|
| `satisfied` | `throughput_budget_satisfied == true` |
| `shortfall` | Budget false; slug not diagnostic canon |
| `expected_diagnostic_shortfall` | Budget false; diagnostic canon — **expected** |

### `t2_policy_reason` (optional detail; omit when satisfied)

| Value | When |
|-------|------|
| `diagnostic_canon_route_feasible_gap` | `expected_diagnostic_shortfall` on registered diagnostic slug |
| `throughput_target_below_actual` | Reserved; unused in v1 |
| `reconstruction_max_zero` | A == 0 edge (if ever emitted) |

### Top-level boolean helpers (persisted on `solver_summary`)

| Field | Type | Meaning |
|-------|------|---------|
| `diagnostic_expected_shortfall` | bool | True only when status is `expected_diagnostic_shortfall` |
| `t3_ops_eligible` | bool | False when T3 milestone ops must not be claimed on this run |

### Existing fields (unchanged meaning)

| Field | Track D rule |
|-------|----------------|
| `throughput_budget_satisfied` | Unchanged PR-2c semantics |
| `throughput_target_shortfall` | Remains in `issue_codes` when unsatisfied |
| `validation_passed` / `run_success` | Still `pipeline_result.validation_passed` only (throughput does not flip layout validation) |
| `reconstruction_max_throughput_per_min`, `target_throughput_per_min`, `actual_committed_output_per_min` | Unchanged |

---

## §6 — Summary / Lab UI contract

### `solver_summary` extension (persisted on `SolverRun`)

When `throughput_budget_fields` is present, also persist:

```json
{
  "throughput_budget_satisfied": false,
  "throughput_target_shortfall": "issue_codes only — not a duplicate top-level field",
  "t2_policy_status": "expected_diagnostic_shortfall",
  "t2_policy_reason": "diagnostic_canon_route_feasible_gap",
  "diagnostic_expected_shortfall": true,
  "t3_ops_eligible": false,
  "t3_blocked_reason": "t2_not_pass_capable_on_diagnostic_canon",
  "rttp_ops_slug_class": "diagnostic_canon"
}
```

`rttp_ops_slug_class` values: `diagnostic_canon` | `pass_capable` | `unknown` (unknown → treat as non-diagnostic until B track registers slug).

### Lab UI (`asteroid_miner_layout_lab.js`)

| Condition | Current behavior | Required behavior |
|-----------|------------------|-------------------|
| `diagnostic_expected_shortfall === true` | Generic capacity failed | Distinct copy: e.g. “Expected diagnostic T2 shortfall (route-feasible vs reconstruction max); not a regression gate.” |
| `runCapacityFailed` | `throughput_budget_satisfied === false` → failed | Do **not** classify as milestone capacity failure when `diagnostic_expected_shortfall` |
| Issue chip `throughput_target_shortfall` | Shortfall label | Append “(expected on diagnostic canon)” when flag set |

### CLI `manage.py run_solver`

- Exit code remains tied to `validation_passed` / runtime error (unchanged).
- Stdout may append one line when `diagnostic_expected_shortfall`: `t2_policy: expected_diagnostic_shortfall (diagnostic canon; T3 ops not applicable)`.

### `solver_run_lab_summary` projection

Expose `t2_policy_status`, `diagnostic_expected_shortfall`, `t3_ops_eligible` for HUD tables (same keys as summary or nested under `throughput_target` object if already grouped — implementation plan picks one shape; must not break existing keys).

---

## §7 — Merge blocker policy (extends ops tier §8)

| PR class | Tier evidence | Diagnostic canon |
|----------|---------------|------------------|
| Throughput / T2 policy (this track) | T2 policy fields present + tests | `expected_diagnostic_shortfall` is **not** a merge failure |
| Milestone T3 / B-CS2 successor | **T3** on pass-capable slug | T3 FAIL on diagnostic canon **not** blocking |
| Unrelated RTTP | Existing pytest gates | Unchanged |

**Regression:** If `t2_policy_status` missing on diagnostic canon run with throughput fields → test failure after D-PR.

---

## §8 — Implementation phases

### Phase D-GOV (docs-only, may close before code)

- This spec APPROVED
- `current_plan.md` ACTIVE row → Track D policy
- Roadmap “Open next” → D-GOV CLOSED; D-PR or B next
- Ops tier §5 table footnote: T1b PASS post-FL-06; T2 expected shortfall per this spec

### Phase D-PR (code + tests — separate implementation plan)

| Task | Layer |
|------|--------|
| `rttp_ops_policy.py` constants + `classify_t2_policy(...)` pure function | contracts / services |
| Wire into `build_rttp_solver_summary` + `solver_runtime_entry` (project slug known) | optimization / services |
| Unit tests: diagnostic vs pass-capable classification | `tests/unit/asteroid_lab/` |
| Lab JS copy + optional CLI line | web static |
| Architecture gate: no free-form `t2_policy_status` strings in tests | architecture optional |

**Out of D-PR:** changing A, C, D formulas; macro; GA.

---

## §9 — Acceptance criteria

### Design / governance (D-GOV)

- [x] User approved this spec (2026-05-30)
- [x] `current_plan.md` references spec path
- [x] Roadmap / `current_plan` “Open next” points to D-PR or B after D-GOV

### Implementation (D-PR)

- [x] Unit tests: diagnostic canon summary fields (`test_rttp_throughput_policy_diagnostic.py`)
- [x] `validation_passed` unchanged by policy classifier alone (`test_t2_policy_does_not_change_validation_passed`)
- [x] Lab projection + JS: `diagnostic_expected_shortfall` bypasses `runCapacityFailed`
- [x] `test_optimization_contamination.ps1` PASS (2026-05-30)
- [x] Canon slug ops readback: `manage.py run_solver --slug copy-import-495e552c` — `solver_run_id` 110 (2026-05-30, PR #99 branch)
- [x] Forbidden shortcuts: no fake `throughput_budget_satisfied`, no issue_codes stripping

---

## §10 — Verification

**After D-PR:**

```powershell
python manage.py run_solver --slug copy-import-495e552c --no-replay
python -m pytest tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py -v
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v
powershell -File scripts/test_optimization_contamination.ps1
```

Manual readback checklist:

```text
throughput_budget_satisfied == false
"throughput_target_shortfall" in issue_codes
t2_policy_status == "expected_diagnostic_shortfall"
diagnostic_expected_shortfall == true
t3_ops_eligible == false
```

---

## §11 — Recommended sequence after D

```text
1. D-GOV: approve this spec + plan queue updates
2. D-PR: observability + Lab copy (writing-plans)
3. B: pass-capable slug spec + T3 ops evidence
4. A: only if product explicitly requires same-slug T2 PASS
```

---

## §12 — Approach comparison (decision record)

| Approach | Verdict | Notes |
|----------|---------|-------|
| **1 Diagnostic T2 expected** | **Selected (C)** | Honest; matches ops tier; unblocks stable ops language |
| **2 Dual-threshold (`t2_ops_status`)** | **Absorbed** | `t3_ops_eligible` + `rttp_ops_slug_class`; avoid duplicate PASS semantics |
| **3 Target cap** | **Deferred** | Circular-pass risk; separate spec if ever needed |

---

## §13 — Appendix: Target cap policy (not v1)

For future discussion only:

```text
effective_target = min(ceil(A × B / 100), policy_cap)
```

**Risks:** cap derived from actual → circular pass; cap from route-feasible upper bound → new solver problem; appears as “lowering the bar.”

**Track D v1 does not implement Approach 3.**

---

## References

- [`2026-05-30-rttp-ops-authority-tier-design.md`](2026-05-30-rttp-ops-authority-tier-design.md)
- [`2026-05-30-rttp-fl06-output-stub-route-reservation-alignment-design.md`](2026-05-30-rttp-fl06-output-stub-route-reservation-alignment-design.md)
- [`2026-05-24-throughput-target-percent-pr2c-design.md`](2026-05-24-throughput-target-percent-pr2c-design.md)
- [`2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md)
- [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)
