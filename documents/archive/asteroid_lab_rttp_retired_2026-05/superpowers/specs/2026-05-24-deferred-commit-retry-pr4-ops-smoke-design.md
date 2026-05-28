# Deferred Commit Retry — PR-4 Real-Map Ops Smoke (Design)

**Status:** CLOSED 2026-05-24 — merged `64473a87` (PR #76); ops `solver_run_id` 57  
**Owner:** asteroid-lab / RTTP deferred commit retry  
**Track:** RTTP core — deferred commit retry slice **4 of 4** (Axis B)  
**Prerequisite:** PR-3 CLOSED `d3de9645` (PR #75) — bounded execution on `master`  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)

**Related:**

- [`2026-05-24-deferred-commit-retry-pr3-bounded-execution-design.md`](2026-05-24-deferred-commit-retry-pr3-bounded-execution-design.md) — execute semantics; PR-4 defers real-map proof
- [`2026-05-24-deferred-commit-retry-pr2-policy-design.md`](2026-05-24-deferred-commit-retry-pr2-policy-design.md) — `config_json` mapper
- [`2026-05-24-deferred-commit-retry-shadow-pr1-design.md`](2026-05-24-deferred-commit-retry-shadow-pr1-design.md) — shadow envelope
- [`2026-05-24-b-cs2-trunk-ops-smoke-design.md`](2026-05-24-b-cs2-trunk-ops-smoke-design.md) — ops smoke pattern (slug, evidence readback)
- [`2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md) — deferred retry row

---

## Problem

PR-3 proves bounded deferred retry execution in pytest (including `observe_only=false` pipeline wiring and LNS merged-input spy tests).

The canonical real Lab slug `copy-import-495e552c` has **not** been exercised with **`observe_only=false`** end-to-end through:

```text
CLI / SolverRun.config_json → runtime mapper → pipeline → persist → readback
```

Today `manage.py run_solver` exposes only `--macro-only`, `--no-replay`, and `--json`. It does **not** pass `deferred_retry_shadow`. When the key is absent, the mapper uses `DeferredRetryShadowConfig()` defaults (`enabled=true`, `observe_only=true`), so **no execute step** is appended.

Without a written PR-4 contract, ops runs risk conflating default shadow-only runs with execute-path smoke.

---

## Goal

Close **deferred commit retry slice 4/4** by one documented ops smoke on `copy-import-495e552c` that proves:

1. **Config delivery** — execute mode is requested reproducibly via CLI.
2. **Runtime path** — shadow + execute algorithm steps persist on a real `SolverRun`.
3. **Readback** — `config_json` and `solver_summary.algorithm_steps` match PR-2/PR-3 contracts.
4. **Safety** — `validation_passed` / `run_success` remain true on the healthy slug (no validation repair, no criteria drift).

**Not the goal:** prove `deferred_retry_recovered_count > 0` on this slug (may be zero if no eligible `REPROBE_FAILED` rows).

---

## Non-goals (PR-4)

| Item | Deferred to |
|------|-------------|
| New deferred retry algorithm / eligibility rules | Out of scope (PR-3 closed) |
| `max_retry_rounds > 1` | Future slice |
| Generic `--config-json-path` loader | Separate runtime config governance slice (optional later) |
| `recovered_count > 0` as pass/fail | Forbidden — flaky on real slug |
| pytest replacing ops smoke | B-CS2 precedent — ops closure only |
| Full GA, macro unpause, capacity C-GATE | Roadmap promotion requires new spec |
| Asserting LNS received merged `CommitResult` on real slug | PR-3 unit tests (`test_lns_receives_merged_not_primary_when_execution_ran`); PR-4 asserts **step order** only |
| Solver logic changes to force recovery | Forbidden |

---

## Normative ops entrypoint (Approach A)

PR-4 uses a dedicated **`--deferred-retry-execute`** CLI flag as the **only normative** ops command for this smoke.

**Canonical command:**

```powershell
python manage.py run_solver --slug copy-import-495e552c --deferred-retry-execute
```

**PowerShell wrapper (implementation plan):**

```powershell
powershell -File scripts/run_solver.ps1 -Slug copy-import-495e552c -DeferredRetryExecute
```

### Fixed injected config

The flag injects **only** this object under the stable wire key `SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY` (`"deferred_retry_shadow"`):

```json
{
  "deferred_retry_shadow": {
    "enabled": true,
    "observe_only": false
  }
}
```

No other keys are added or overridden by this flag. PR-2 parse rules (strict bool, integer types for optional fields) apply to any explicit subfields; omitted fields use mapper defaults (`max_retry_rounds=1`, `max_candidates=null`, `route_probe_max_expansions=500`).

**Explicitly out of scope for PR-4:**

```text
Generic --config-json-path support is not part of PR-4.
If needed, open later as a separate runtime configuration governance slice.
```

---

## Architecture (Approach 2 + 2b)

| Layer | PR-4 change | Responsibility |
|-------|-------------|----------------|
| CLI | `manage.py run_solver` + `scripts/run_solver.ps1` | Map `--deferred-retry-execute` → fixed `deferred_retry_shadow` object |
| Runtime | `solver_runtime_entry.py` (unchanged logic) | Existing `_deferred_retry_shadow_config_from_run_config` |
| Pipeline | `pipeline.py` (unchanged) | Shadow always → execute when `enabled && !observe_only` |
| Evidence | Human + `current_plan.md` / roadmap | Record `solver_run_id`, metrics snapshot |

PR-4 is **not** a second algorithm PR. It is **config plumbing + ops contract + closure metadata**.

---

## Smoke procedure

**Slug:** `copy-import-495e552c`

**Constraints:**

- Do **not** pass `macro_only_mode: true`.
- Do **not** use replay frames, NDJSON, or `solver_summary` as algorithm input.
- `ASTEROID_LAB_RTTP_ENABLED=True` (default).

**Evidence source (read-only):**

- CLI exit code
- Latest `SolverRun` after exit 0: `config_json["deferred_retry_shadow"]`, `config_json["solver_summary"]`
- Top-level: `validation_passed`, `run_success`, `issue_codes`, `solver_run_id`, `run_key`

---

## Pass criteria (PR-4-1 … PR-4-23)

### Run shell (aligned with B-CS2 / E5)

| ID | Assertion |
|----|-----------|
| PR-4-1 | CLI exit code `0` |
| PR-4-2 | `solver_summary.algorithm` == `rttp_v0.1` |
| PR-4-3 | `solver_summary.validation_passed` == `true` |
| PR-4-4 | `solver_summary.run_success` == `true` |
| PR-4-5 | `solver_summary.issue_codes` == `[]` (healthy slug convention) |

### Config readback (runtime boundary)

| ID | Assertion |
|----|-----------|
| PR-4-6 | `config_json.deferred_retry_shadow.enabled` == `true` |
| PR-4-7 | `config_json.deferred_retry_shadow.observe_only` == `false` |
| PR-4-8 | Run completes without mapper rejecting `observe_only: false` (PR-3 lift remains active) |

### Shadow step (PR-2 envelope, primary-only diagnostics)

| ID | Assertion |
|----|-----------|
| PR-4-9 | Step `rttp.deferred_commit_retry_shadow` exists in `algorithm_steps` |
| PR-4-10 | `metrics.enabled` == `true` |
| PR-4-11 | `metrics.observe_only` == `false` (execute mode still records primary-phase shadow) |
| PR-4-12 | `metrics.source_phase` == `primary_incremental_commit` |
| PR-4-13 | Shadow metrics JSON-safe: required keys `candidate_count`, `eligible_candidate_ids`, `budget`, `domain_context` present |

### Execute step (PR-3)

| ID | Assertion |
|----|-----------|
| PR-4-14 | Step `rttp.deferred_commit_retry_execute` exists |
| PR-4-15 | **Step order** (indices ascending): `rttp.genome_selection` → `rttp.deferred_commit_retry_shadow` → `rttp.deferred_commit_retry_execute` → `rttp.commit` (final post-LNS snapshot) → `rttp.catalog_placement_validation`. Primary `incremental_commit` is not a separate algorithm step; shadow/execute record the deferred-retry slice before the final commit step. |
| PR-4-16 | Execute step has **JSON-safe metrics** with required keys: `deferred_retry_rounds_executed`, `deferred_retry_eligible_count`, `deferred_retry_attempted_count`, `deferred_retry_recovered_count`, `deferred_retry_still_failed_count`, `recovered_candidate_ids`, `deferred_retry_failed_reason_counts` |
| PR-4-17 | If execute step includes `passed`, then `passed` == `true` (v0 hardcodes `true`; absence of key is not a failure) |

### Execute semantics (non-flaky)

| ID | Assertion |
|----|-----------|
| PR-4-18 | `deferred_retry_rounds_executed` ∈ `{0, 1}` |
| PR-4-19 | `deferred_retry_still_failed_count` == `deferred_retry_attempted_count - deferred_retry_recovered_count` |
| PR-4-20 | **Informational only:** `deferred_retry_recovered_count` and `recovered_candidate_ids` — record in evidence; **not** pass/fail |

### B-CS2 regression guard (subset)

| ID | Assertion |
|----|-----------|
| PR-4-21 | Step `rttp.commit` exists; `passed` == `true`; `metrics.committed_ids` non-empty; top-level `confirmed_count` > 0 |
| PR-4-22 | Step `rttp.route_domain` exists; `metrics.skeleton_id` non-empty string |
| PR-4-23 | Step `rttp.catalog_placement_validation` exists (D+ tail audit) |

### Explicitly **not** PR-4 pass/fail

| Item | Note |
|------|------|
| `deferred_retry_recovered_count > 0` | Eligible queue may be empty on real slug |
| Shadow `candidate_count > 0` | Zero eligible is valid |
| E5 `unmapped_candidate_count == 0` | E5 CLOSED — context only |
| Non-zero summary `conflict_count` alone | OK if PR-4-3..5 pass (LNS may run) |
| Direct observation of LNS merged input | PR-3 unit tests only |
| Separate `rttp.lns` algorithm step | LNS is inline after execute in v0.1 pipeline |

---

## Known slug context

Per [`current_plan.md`](../../../documents/ai/current_plan.md) Ops B/C and B-CS2:

- Pre-reconstruction map may have `transport_component_count` 0.
- Trunk signal is primarily **route-domain / skeleton**, not mixed existing transport on this slug class.
- Default runs (no flag) use shadow-only path (`observe_only=true`); PR-4 smoke **must** use `--deferred-retry-execute`.

---

## Forbidden (hard)

- Validation repair or relaxing fail-closed catalog rules to pass smoke
- Changing `deferred_retry_execute`, `incremental_commit`, or `pipeline` **for smoke green**
- Using replay / NDJSON / `solver_summary` as algorithm input
- `macro_only_mode` smoke as substitute
- Requiring recovery on real slug
- Opening generic config-json loader in PR-4

**On smoke FAIL:** Stop with `BLOCKED:` and open a **separate** bug track — do not drift PR-4 criteria.

---

## Implementation scope (follow-on plan; not this document)

| Action | Path |
|--------|------|
| Add `--deferred-retry-execute` | `django_apps/asteroid_lab/management/commands/run_solver.py` |
| Add `-DeferredRetryExecute` | `scripts/run_solver.ps1` |
| Ops run + evidence | `documents/ai/current_plan.md`, roadmap PR-4 row |
| Optional evidence table | `docs/superpowers/reports/` (informational) |

**No change** to `deferred_retry_execute.py` algorithm unless smoke exposes a real defect (separate bug PR).

---

## Verification commands

**After PR-4 plumbing merged:**

```powershell
python manage.py run_solver --slug copy-import-495e552c --deferred-retry-execute
```

**Standing regression (must stay green):**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py -v --tb=short
python -m pytest tests/unit/asteroid_lab/test_rttp_commit_survivability.py -v --tb=short
powershell -File scripts/test_optimization_contamination.ps1
```

---

## Closure artifacts

| Artifact | On PR-4 ops PASS |
|----------|------------------|
| This spec | Status → CLOSED with merge SHA of plumbing PR + ops evidence |
| `current_plan.md` | PR-4 CLOSED entry: `solver_run_id`, `run_key`, metric bullets |
| Roadmap | PR-4 ✅; deferred retry slice 1–4 complete |
| Plan doc | `2026-05-24-deferred-commit-retry-pr4-ops-smoke.md` (from writing-plans) |

**Commit survivability arc CLOSED** declaration remains **after** PR-4 ops smoke PASS — optional one-line in roadmap; not embedded in PR-4 pass criteria.

---

## Spec self-review

| Check | Result |
|-------|--------|
| Placeholder / TBD | None |
| Internal consistency | A normative; B/C out of scope; order PR-4-15 matches pipeline |
| Scope | Single slug, single flag, ops + thin CLI |
| Ambiguity | `passed` conditional on PR-4-17; recovery informational on PR-4-20 |
| Axis | B (deferred retry / commit survivability), not Axis A catalog |

---

## Follow-on

| Item | When |
|------|------|
| Implementation plan | `writing-plans` → `2026-05-24-deferred-commit-retry-pr4-ops-smoke.md` |
| Generic `--config-json-path` | Separate spec if promoted |
| Full GA / macro / capacity | Roadmap governance + new board section |
