# Deferred Commit Retry — PR-2 Runtime Policy Wiring Design

**Status:** CLOSED 2026-05-24 — merged `a5cfca87` (PR #73)  
**Owner:** asteroid-lab / RTTP deferred commit retry  
**Track:** RTTP core — deferred commit retry slice 2 of 4  
**Prerequisite:** PR-1 CLOSED `1e021f20` (PR #72) — observe-only shadow  
**Related:** [`2026-05-24-deferred-commit-retry-shadow-pr1-design.md`](2026-05-24-deferred-commit-retry-shadow-pr1-design.md)

---

## Problem

PR-1 added `DeferredRetryShadowConfig` on `RttpPipelineConfig` and always records `rttp.deferred_commit_retry_shadow` after primary `incremental_commit`. Operators cannot disable shadow via `SolverRun.config_json`, and runtime entry does not map a stable wire key.

PR-2 closes the **runtime policy contract** without opening retry execution.

---

## Goal

```text
SolverRun.config_json["deferred_retry_shadow"]
  → DeferredRetryShadowConfig
  → RttpPipelineConfig.deferred_retry_shadow
  → pipeline shadow step metrics (observe-only)
```

## Non-goals (PR-2)

| Item | Deferred to |
|------|-------------|
| Deferred retry execution | PR-3 |
| Route probe for shadow | PR-3+ |
| `observe_only=false` (execution enable) | PR-3+ |
| Macro pipeline shadow semantics change | Out of scope (v0.1 path only) |
| Reading replay / solver_summary / NDJSON as input | Forbidden (permanent) |
| Changing commit / LNS / validation outcomes | Forbidden |

---

## Wire contract

### Stable key

`solver_run_config_keys.py`:

```python
SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY = "deferred_retry_shadow"
```

### JSON shape (object value)

```json
{
  "deferred_retry_shadow": {
    "enabled": false,
    "observe_only": true,
    "max_retry_rounds": 1,
    "max_candidates": null,
    "route_probe_max_expansions": 500
  }
}
```

| Field | Type | Default when key absent |
|-------|------|-------------------------|
| `enabled` | bool | `true` |
| `observe_only` | bool | `true` (must stay true in PR-2) |
| `max_retry_rounds` | int | `1` |
| `max_candidates` | int \| null | `null` |
| `route_probe_max_expansions` | int | `500` |

### Mapper policy (`_deferred_retry_shadow_config_from_run_config`)

| Input | Result |
|-------|--------|
| Key absent | `DeferredRetryShadowConfig()` |
| `{"enabled": false}` | `enabled=False`, other fields default |
| `{"enabled": true, ...}` | Parsed fields with strict types |
| `observe_only: false` | `ValueError` (fail-closed; no silent execution enable) |
| `enabled: "false"` (string) | `ValueError` (no truthy string coercion) |
| Non-dict value for key | `ValueError` |

`_rttp_pipeline_config_from_run_config` must pass `deferred_retry_shadow=...` while preserving `macro_only_mode` and `max_macro_candidates` behavior.

---

## Pipeline behavior when `enabled=false` (choice B)

**Always append** `rttp.deferred_commit_retry_shadow` step (stable `algorithm_steps` shape).

`build_deferred_retry_shadow_summary(..., config=DeferredRetryShadowConfig(enabled=False))` already returns:

- `enabled=false`, `candidate_count=0`, empty `candidates`
- `passed=True` on step row

No skip of `_append_deferred_retry_shadow_step`. No change to `primary_commit_result` passed to LNS.

---

## Invariants (PR-2)

| ID | Invariant |
|----|-----------|
| INV-PR2-01 | No retry execution; no new `incremental_commit` / `probe_route` for shadow |
| INV-PR2-02 | `observe_only` must remain `true`; `false` rejects at mapper |
| INV-PR2-03 | Disabled shadow does not change `CommitResult`, LNS input, validation, or genome |
| INV-PR2-04 | Shadow step remains after primary commit, before LNS (PR-1 ordering) |
| INV-PR2-05 | `solver_summary` / replay / NDJSON are never read to build shadow config |
| INV-PR2-06 | Macro-only pipeline path unchanged (separate `_run_macro_rttp_pipeline`) |

---

## Verification

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py -v --tb=short
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py tests/unit/asteroid_lab/test_rttp_db_macro_integration.py -v --tb=short
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
powershell -File scripts/test_optimization_contamination.ps1
python -m ruff check django_apps/asteroid_lab/services/solver_run_config_keys.py django_apps/asteroid_lab/services/solver_runtime_entry.py
python -m black --check django_apps/asteroid_lab/services/solver_run_config_keys.py django_apps/asteroid_lab/services/solver_runtime_entry.py
```

---

## Follow-on

| PR | Scope |
|----|--------|
| PR-3 | Bounded deferred retry execution |
| PR-4 | Real-map regression / ops smoke |
