# PR-2c — Throughput Target Percent & Budget Correctness — Design Spec

**Date:** 2026-05-24  
**Status:** Approved for implementation planning  
**Depends on:** PR-1 `MiningExtractionRule` · PR-2a `reconstruction_capacity` · **PR-2b** `actual_committed_output_per_min`  
**Follow-up:** PR-2d placement goals — [`2026-05-24-throughput-target-selection-pr2d-design.md`](2026-05-24-throughput-target-selection-pr2d-design.md)  
**Parent:** [`2026-05-24-reconstruction-max-throughput-pr2a-design.md`](2026-05-24-reconstruction-max-throughput-pr2a-design.md) · [`2026-05-24-mining-extraction-rule-design.md`](2026-05-24-mining-extraction-rule-design.md)

---

## Problem

PR-2a exposes `reconstruction_max_throughput_per_min` as a **terrain upper bound**. PR-2b exposes `actual_committed_output_per_min` from route-confirmed commits. Today `throughput_budget_satisfied` aliases `pipeline_ok` and does not reflect user intent.

Users need a **configurable target** between 10% and 80% of the theoretical max, with explicit satisfied/shortfall reporting in Lab UI and `solver_summary`.

## PR-2b invariants (dependency)

`actual_committed_output_per_min` is implemented in PR-2b before this spec ships.

```text
actual_committed_output_per_min
  = sum(route-confirmed committed physical extractor bundle outputs)

Each committed bundle is counted exactly once.
Macro parent IDs must not be summed with their child bundle IDs.
```

**Allowed inputs:** `BundleCandidate.throughput_factor`, `transport_kind` → `resource_kind`, `MiningExtractionRule.output_per_min`, confirmed ID list from commit result.

**Forbidden inputs:** `candidate_id` string parsing, `commit_order` text parsing, prior `solver_summary`, replay frames (same as PR-2a capacity).

**Numeric:** `Decimal` only internally; persisted rates as 4dp strings (no float).

---

## Non-goals (PR-2c)

- Changing RTTP candidate generation, greedy-regret scoring, or commit order (PR-2d)
- Installing Space Belt / Space Pipe building grids (deferred transport-install track)
- Rewriting `capacity_goals` skeleton heuristic
- Using replay or prior `solver_summary` as computation input
- Merging PR-2b actual-rate computation into this PR (PR-2b ships first)

PR-2a document body is **unchanged** except an optional one-line follow-up pointer (see Parent doc PR split table).

---

## Metric model (canonical)

| Symbol | Field | Meaning |
|--------|-------|---------|
| A | `reconstruction_max_throughput_per_min` | Primary-resource theoretical max from `reconstruction_capacity.by_resource[primary].max_throughput_per_min` (decimal string) |
| B | `throughput_target_percent` | User config, integer **10..80**, default **80** |
| C | `target_throughput_per_min` | `ceil(A × B / 100)` as decimal string (4 dp) |
| D | `actual_committed_output_per_min` | PR-2b; sum of committed platform rates (route-confirmed commit set only) |

**Success rule:**

```text
throughput_budget_satisfied = (D >= C)
throughput_shortfall_per_min = max(0, C - D)   # decimal string when unsatisfied; "0.0000" when satisfied
```

**Utilization (display-only ratios, decimal strings 4 dp):**

```text
target_utilization_ratio   = B / 100
actual_utilization_ratio   = D / A   (0 when A == 0)
```

`reconstruction_max_throughput_per_min` remains **non-authoritative for production**. Only `actual_committed_output_per_min` is committed production authority.

---

## Config contract

**Module:** `django_apps/asteroid_lab/services/solver_run_config_keys.py`

```python
SOLVER_RUN_CONFIG_THROUGHPUT_TARGET_PERCENT_KEY = "throughput_target_percent"
```

**Bounds module:** `django_apps/asteroid_lab/services/throughput_target.py`

```python
MIN_THROUGHPUT_TARGET_PERCENT = 10
MAX_THROUGHPUT_TARGET_PERCENT = 80
DEFAULT_THROUGHPUT_TARGET_PERCENT = 80
```

**Parsing (fail-closed):**

- HTTP POST `run_solver` JSON body and `manage.py run_solver --throughput-target-percent N`
- Invalid type, `< 10`, or `> 80` → `CommandError` (CLI) or HTTP 400 JSON `{ "ok": false, "error": "invalid_throughput_target_percent" }` (web)
- Omitted key → default **80** (stored on `SolverRun.config_json` at run creation)

**Forbidden:** reading `throughput_target_percent` from `solver_summary` when building a new run.

---

## Pure functions (`throughput_target.py`)

| Function | Responsibility |
|----------|----------------|
| `parse_throughput_target_percent(config: Mapping[str, Any]) -> int` | Validate + default |
| `primary_reconstruction_max_per_min(envelope: Mapping[str, Any]) -> Decimal` | Resolve A from `primary_resource_kind` |
| `compute_target_throughput_per_min(*, reconstruction_max: Decimal, percent: int) -> Decimal` | `(max * percent / 100).to_integral_value(rounding=ROUND_CEILING)` — no float |
| `evaluate_throughput_budget(*, actual: Decimal, target: Decimal) -> ThroughputBudgetEvaluation` | frozen dataclass: `satisfied`, `shortfall` |
| `throughput_ratios(*, actual, reconstruction_max, percent) -> tuple[Decimal, Decimal]` | target + actual utilization |

Reuse `decimal_str` from `reconstruction_capacity_summary` (import, do not duplicate).

---

## `solver_summary` fields (persisted)

All throughput **rates** are decimal strings with 4 fractional digits (match PR-2a capacity JSON).

```json
{
  "reconstruction_max_throughput_per_min": "68160.0000",
  "throughput_target_percent": 60,
  "target_throughput_per_min": "40896.0000",
  "actual_committed_output_per_min": "38400.0000",
  "throughput_budget_satisfied": false,
  "throughput_shortfall_per_min": "2496.0000",
  "target_utilization_ratio": "0.6000",
  "actual_utilization_ratio": "0.5634"
}
```

**`throughput_budget_satisfied` decoupling:** MUST NOT be derived from `pipeline_ok`, `validation_passed`, `run_success`, `capacity_satisfied`, or `placement_capacity_satisfied`. It reflects **only** `D >= C` when `D` is available.

**Legacy / missing actual (Lab DTO):**

| Field | Values |
|-------|--------|
| `actual_output_status` | `pending_pr_2b` \| `available` \| `unavailable` |
| `throughput_target_status` | `no_actual_output` \| `satisfied` \| `shortfall` |

When `actual_output_status` is not `available`:

- Do **not** set `throughput_budget_satisfied` to `false` silently (false means “computed and short”).
- Omit `throughput_budget_satisfied` / `throughput_shortfall_per_min` from summary, or set `throughput_target_status: "no_actual_output"`.
- Lab budget chip shows `—`, not “shortfall”.

**Issue code (enum constant, not free-form):**

```python
THROUGHPUT_TARGET_SHORTFALL_ISSUE_CODE = "throughput_target_shortfall"
```

Append to `issue_codes` when `not throughput_budget_satisfied` and `validation_passed` is otherwise true; when validation failed, shortfall issue is optional (v0: append whenever budget unsatisfied regardless of validation).

---

## Wire sites

1. **`solver_runtime_entry._run_rttp_solver_for_map_input`**
   - Parse percent from `run_config` before pipeline.
   - After PR-2b: read `actual` from `pipeline_result.actual_committed_output_per_min`.
   - Build target/budget from `reconstruction_capacity` envelope + percent.
   - Pass into `build_rttp_solver_summary(...)`.

2. **`build_rttp_solver_summary`**
   - New optional kwargs: `throughput_target_percent`, `throughput_budget: Mapping[str, Any] | None`
   - When provided, merge scalar fields; set `throughput_budget_satisfied` from evaluation (not `pipeline_ok`).

3. **`lab_run_summary_from_solver_summary`**
   - New nested `throughput_target` section for template/JS (see Lab UI).

4. **`public_pages._run_solver_request_config`**
   - Validate `throughput_target_percent` if present in POST body.

5. **`run_solver` management command**
   - `--throughput-target-percent` optional argument.

---

## Lab UI contract

**Control placement (decided):** Left column **Input** stack, in the **Extractor Constraints** card, **below** the rule list and **above** the placeholder footnote box (`asteroid_miner_layout_solver.html` ~L215). **Not** in the header Run Solver toolbar.

Rationale: groups solver tuning with other constraints; keeps header actions (Reset / Run Solver) compact.

| Property | Value |
|----------|-------|
| min | 10 |
| max | 80 |
| default | 80 |
| step | 10 (v0; 5 allowed if layout permits) |
| DOM ids | `lab-throughput-target-percent`, `lab-throughput-target-percent-label` |
| Helper copy | `{% trans "% of theoretical max" %}` under the slider |

Client-side clamp; server fail-closed on out-of-range. Value is read on **Run Solver** POST only (no auto re-run on slide). Optional: persist last value in `sessionStorage` key `lab-throughput-target-percent` for UX between visits (not required v0).

**Markup sketch (inside Extractor Constraints card):**

```html
<div class="mt-4 border-t border-slate-800 pt-4">
  <label for="lab-throughput-target-percent" class="text-xs font-medium text-slate-400">
    {% trans "Target throughput" %}
  </label>
  <div class="mt-2 flex items-center gap-3">
    <input type="range" id="lab-throughput-target-percent" class="flex-1" min="10" max="80" step="10" value="80" />
    <span id="lab-throughput-target-percent-label" class="w-10 text-right text-sm font-semibold text-slate-100">80%</span>
  </div>
  <p class="mt-1 text-xs text-slate-500">{% trans "% of theoretical max" %}</p>
</div>
```

**Card 5 (RTTP Committed) after PR-2c:**

| Line | Content |
|------|---------|
| Primary | `{actual_committed_output_per_min}/min` compact |
| Subtitle | `Target {percent}% · {actual} / {target} per min` |
| Status chip | `satisfied` / `shortfall {throughput_shortfall_per_min}/min` |

**Detail panel C (RTTP Result):** add rows for Target %, Target throughput, Utilization (actual / max), Budget status.

**i18n:** English msgids + `scripts/build_locale_ko.py` entries; JS via `shapezUiT` only (no Korean literals in `.js`).

Required msgids (minimum):

- `Target Throughput`
- `Target percent`
- `% of theoretical max`
- `Target satisfied`
- `Short by {amount}/min` (or separate amount + unit fragments)
- `Invalid throughput target percent`
- `throughput target shortfall`
- `Committed output` (PR-2b subtitle)

---

## PR split (this arc)

| PR | Delivers |
|----|----------|
| PR-2a | Unchanged — reconstruction max + Lab observability |
| PR-2b | `actual_committed_output_per_min` computation + card subtitle |
| **PR-2c** | Config 10–80, target/shortfall/ratios, real `throughput_budget_satisfied`, Lab control + cards |
| PR-2d | Selection/fitness penalizes target shortfall (no transport grid) |

---

## Tests (required)

| Module | Cases |
|--------|-------|
| `test_throughput_target.py` | parse default 80; reject 9/81; ceil 60% of 4800 → 2880; satisfied/shortfall; ratios |
| `test_rttp_solver_summary.py` | budget fields; `throughput_budget_satisfied` false when actual < target even if `pipeline_ok` true |
| `test_solver_run_lab_summary.py` | nested `throughput_target`; legacy `—` |
| `test_run_solver_config.py` (new or extend web tests) | POST invalid percent → 400 |
| `test_asteroid_lab_ui_strings.py` | no stale `actual output pending` after PR-2c when actual present |

---

## Forbidden shortcuts

- `throughput_budget_satisfied := pipeline_ok` after PR-2c
- Treating A as committed production
- Reading replay frames for A/B/C/D
- Changing commit order / validation repair in PR-2c

---

## Validation (narrow)

```powershell
python -m pytest tests/unit/asteroid_lab/test_throughput_target.py tests/unit/asteroid_lab/test_committed_throughput_summary.py tests/unit/asteroid_lab/test_rttp_solver_summary.py tests/unit/asteroid_lab/test_solver_run_lab_summary.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/services/throughput_target.py django_apps/asteroid_lab/services/committed_throughput_summary.py django_apps/asteroid_lab/services/solver_runtime_entry.py
```
