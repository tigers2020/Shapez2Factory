# PR-2c — Throughput Target Percent & Budget Correctness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users set `throughput_target_percent` (10–80, default 80), compute `target_throughput_per_min = ceil(reconstruction_max × percent / 100)`, set `throughput_budget_satisfied` from `actual_committed_output_per_min >= target`, and render target/status/utilization in Lab UI — without changing RTTP selection or commit logic.

**Architecture:** Pure `throughput_target.py` for parse/ceil/evaluate; config key on `SolverRun.config_json`; `solver_runtime_entry` merges budget into `build_rttp_solver_summary`; Lab POST + slider send percent; fail-closed validation on web + CLI.

**Tech Stack:** Django 5.x, `Decimal`, `math.ceil`, pytest-django, ruff, gettext/`shapezUiT`, `scripts/build_locale_ko.py`

**Spec:** [`docs/superpowers/specs/2026-05-24-throughput-target-percent-pr2c-design.md`](../specs/2026-05-24-throughput-target-percent-pr2c-design.md)

**Depends on:** PR-2b merged (or branch rebased) — `actual_committed_output_per_min` on `PipelineResult` / `solver_summary`

**Branch:** `feat/asteroid-lab-throughput-target-percent-pr2c` (worktree recommended)

**Out of scope:** PR-2d selection scoring · Space Belt/Pipe grid install · `capacity_goals` rewrite

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `django_apps/asteroid_lab/services/throughput_target.py` | Parse percent, ceil target, budget eval, ratios |
| Create | `tests/unit/asteroid_lab/test_throughput_target.py` | Pure function contract tests |
| Modify | `django_apps/asteroid_lab/services/solver_run_config_keys.py` | `throughput_target_percent` key constant |
| Modify | `django_apps/asteroid_lab/optimization/rttp_solver_summary.py` | Budget fields; decouple `throughput_budget_satisfied` |
| Modify | `django_apps/asteroid_lab/services/solver_runtime_entry.py` | Parse config, build budget, issue code |
| Modify | `django_apps/web/views/public_pages.py` | POST validation |
| Modify | `django_apps/asteroid_lab/management/commands/run_solver.py` | `--throughput-target-percent` |
| Modify | `django_apps/asteroid_lab/services/solver_run_lab_summary.py` | `throughput_target` nested DTO |
| Modify | `tests/unit/asteroid_lab/test_rttp_solver_summary.py` | Budget vs pipeline_ok |
| Modify | `tests/unit/asteroid_lab/test_solver_run_lab_summary.py` | DTO fields |
| Create | `tests/unit/web/test_asteroid_run_solver_config.py` | HTTP 400 on invalid percent |
| Modify | `django_apps/web/templates/web/asteroid_miner_layout_solver.html` | Slider + labels |
| Modify | `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | POST body + card/detail |
| Modify | `scripts/build_locale_ko.py` | New msgids |
| Modify | `docs/superpowers/specs/2026-05-24-reconstruction-max-throughput-pr2a-design.md` | One-line PR-2c follow-up only |
| Modify | `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | One-line status |

---

### Task 1: Config keys + `throughput_target.py` (TDD)

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_run_config_keys.py`
- Create: `django_apps/asteroid_lab/services/throughput_target.py`
- Create: `tests/unit/asteroid_lab/test_throughput_target.py`

- [ ] **Step 1: Add config key exports**

```python
# solver_run_config_keys.py
SOLVER_RUN_CONFIG_THROUGHPUT_TARGET_PERCENT_KEY = "throughput_target_percent"
```

Add to `__all__`.

- [ ] **Step 2: Write failing tests**

```python
# tests/unit/asteroid_lab/test_throughput_target.py
from decimal import Decimal

import pytest

from django_apps.asteroid_lab.services.throughput_target import (
    DEFAULT_THROUGHPUT_TARGET_PERCENT,
    MAX_THROUGHPUT_TARGET_PERCENT,
    MIN_THROUGHPUT_TARGET_PERCENT,
    compute_target_throughput_per_min,
    evaluate_throughput_budget,
    parse_throughput_target_percent,
    primary_reconstruction_max_per_min,
    throughput_utilization_ratios,
)


def test_parse_defaults_to_80() -> None:
    assert parse_throughput_target_percent({}) == 80


def test_parse_rejects_below_10() -> None:
    with pytest.raises(ValueError, match="10"):
        parse_throughput_target_percent({"throughput_target_percent": 9})


def test_parse_rejects_above_80() -> None:
    with pytest.raises(ValueError, match="80"):
        parse_throughput_target_percent({"throughput_target_percent": 81})


def test_ceil_target_60_percent_of_4800() -> None:
    target = compute_target_throughput_per_min(
        reconstruction_max=Decimal("4800"),
        percent=60,
    )
    assert target == Decimal("2880")


def test_budget_satisfied_when_actual_ge_target() -> None:
    ev = evaluate_throughput_budget(
        actual=Decimal("3040"),
        target=Decimal("2880"),
    )
    assert ev.satisfied is True
    assert ev.shortfall == Decimal("0")


def test_budget_shortfall() -> None:
    ev = evaluate_throughput_budget(
        actual=Decimal("2400"),
        target=Decimal("2880"),
    )
    assert ev.satisfied is False
    assert ev.shortfall == Decimal("480")


def test_primary_max_from_envelope() -> None:
    env = {
        "primary_resource_kind": "shape",
        "by_resource": {
            "shape": {"max_throughput_per_min": "68160.0000"},
            "fluid": {"max_throughput_per_min": "1000.0000"},
        },
    }
    assert primary_reconstruction_max_per_min(env) == Decimal("68160.0000")


def test_utilization_ratios() -> None:
    target_u, actual_u = throughput_utilization_ratios(
        actual=Decimal("3040"),
        reconstruction_max=Decimal("4800"),
        percent=60,
    )
    assert target_u == Decimal("0.6000")
    assert actual_u == Decimal("0.6333")
```

- [ ] **Step 3: Run — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_throughput_target.py -v --tb=short
```

- [ ] **Step 4: Implement `throughput_target.py`**

```python
"""Throughput target percent and budget evaluation (PR-2c; never replay input)."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import ROUND_CEILING, Decimal
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django_apps.asteroid_lab.services.reconstruction_capacity_summary import decimal_str
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_THROUGHPUT_TARGET_PERCENT_KEY,
)

MIN_THROUGHPUT_TARGET_PERCENT = 10
MAX_THROUGHPUT_TARGET_PERCENT = 80
DEFAULT_THROUGHPUT_TARGET_PERCENT = 80
THROUGHPUT_TARGET_SHORTFALL_ISSUE_CODE = "throughput_target_shortfall"


@dataclass(frozen=True, slots=True)
class ThroughputBudgetEvaluation:
    satisfied: bool
    shortfall: Decimal


def parse_throughput_target_percent(config: Mapping[str, Any]) -> int:
    raw = config.get(SOLVER_RUN_CONFIG_THROUGHPUT_TARGET_PERCENT_KEY, DEFAULT_THROUGHPUT_TARGET_PERCENT)
    if isinstance(raw, bool) or not isinstance(raw, int):
        msg = "throughput_target_percent must be an integer"
        raise ValueError(msg)
    if raw < MIN_THROUGHPUT_TARGET_PERCENT or raw > MAX_THROUGHPUT_TARGET_PERCENT:
        msg = f"throughput_target_percent must be between {MIN_THROUGHPUT_TARGET_PERCENT} and {MAX_THROUGHPUT_TARGET_PERCENT}"
        raise ValueError(msg)
    return raw


def primary_reconstruction_max_per_min(envelope: Mapping[str, Any]) -> Decimal:
    primary = str(envelope.get("primary_resource_kind", "shape"))
    by = dict(envelope.get("by_resource") or {})
    row = dict(by.get(primary) or {})
    raw = row.get("max_throughput_per_min", "0")
    return Decimal(str(raw))


def compute_target_throughput_per_min(*, reconstruction_max: Decimal, percent: int) -> Decimal:
    product = reconstruction_max * Decimal(percent) / Decimal(100)
    return product.to_integral_value(rounding=ROUND_CEILING)


def evaluate_throughput_budget(*, actual: Decimal, target: Decimal) -> ThroughputBudgetEvaluation:
    if actual >= target:
        return ThroughputBudgetEvaluation(satisfied=True, shortfall=Decimal(0))
    return ThroughputBudgetEvaluation(satisfied=False, shortfall=target - actual)


def throughput_utilization_ratios(
    *,
    actual: Decimal,
    reconstruction_max: Decimal,
    percent: int,
) -> tuple[Decimal, Decimal]:
    target_u = (Decimal(percent) / Decimal(100)).quantize(Decimal("0.0001"))
    if reconstruction_max <= 0:
        actual_u = Decimal(0)
    else:
        actual_u = (actual / reconstruction_max).quantize(Decimal("0.0001"))
    return target_u, actual_u


def build_throughput_budget_summary(
    *,
    reconstruction_capacity: Mapping[str, Any],
    throughput_target_percent: int,
    actual_committed_output_per_min: str,
) -> dict[str, Any]:
    recon_max = primary_reconstruction_max_per_min(reconstruction_capacity)
    actual = Decimal(actual_committed_output_per_min)
    target = compute_target_throughput_per_min(
        reconstruction_max=recon_max,
        percent=throughput_target_percent,
    )
    ev = evaluate_throughput_budget(actual=actual, target=target)
    target_u, actual_u = throughput_utilization_ratios(
        actual=actual,
        reconstruction_max=recon_max,
        percent=throughput_target_percent,
    )
    return {
        "reconstruction_max_throughput_per_min": decimal_str(recon_max),
        "throughput_target_percent": throughput_target_percent,
        "target_throughput_per_min": decimal_str(target),
        "actual_committed_output_per_min": actual_committed_output_per_min,
        "throughput_budget_satisfied": ev.satisfied,
        "throughput_shortfall_per_min": decimal_str(ev.shortfall),
        "target_utilization_ratio": decimal_str(target_u),
        "actual_utilization_ratio": decimal_str(actual_u),
    }


__all__ = [
    "DEFAULT_THROUGHPUT_TARGET_PERCENT",
    "MAX_THROUGHPUT_TARGET_PERCENT",
    "MIN_THROUGHPUT_TARGET_PERCENT",
    "THROUGHPUT_TARGET_SHORTFALL_ISSUE_CODE",
    "ThroughputBudgetEvaluation",
    "build_throughput_budget_summary",
    "compute_target_throughput_per_min",
    "evaluate_throughput_budget",
    "parse_throughput_target_percent",
    "primary_reconstruction_max_per_min",
    "throughput_utilization_ratios",
]
```

- [ ] **Step 5: Run — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_throughput_target.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/services/throughput_target.py tests/unit/asteroid_lab/test_throughput_target.py
```

- [ ] **Step 6: Commit**

```bash
git add django_apps/asteroid_lab/services/solver_run_config_keys.py django_apps/asteroid_lab/services/throughput_target.py tests/unit/asteroid_lab/test_throughput_target.py
git commit -m "feat(asteroid_lab): throughput target percent parse and budget eval"
```

---

### Task 2: `build_rttp_solver_summary` decouple budget flag

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/rttp_solver_summary.py`
- Modify: `tests/unit/asteroid_lab/test_rttp_solver_summary.py`

- [ ] **Step 1: Failing test — budget false while pipeline_ok true**

```python
def test_throughput_budget_satisfied_not_pipeline_ok_alias() -> None:
    summary = build_rttp_solver_summary(
        pipeline_ok=True,
        committed_count=1,
        normal_count=1,
        commit_order=("a",),
        algorithm_steps=(),
        throughput_budget_fields={
            "throughput_budget_satisfied": False,
            "throughput_target_percent": 60,
            "target_throughput_per_min": "2880.0000",
            "actual_committed_output_per_min": "2400.0000",
            "throughput_shortfall_per_min": "480.0000",
            "reconstruction_max_throughput_per_min": "4800.0000",
            "target_utilization_ratio": "0.6000",
            "actual_utilization_ratio": "0.5000",
        },
    )
    assert summary["validation_passed"] is True
    assert summary["throughput_budget_satisfied"] is False
```

- [ ] **Step 2: Implement**

Add optional `throughput_budget_fields: Mapping[str, Any] | None = None`.

When provided:
- Merge all keys into `summary`
- Set `throughput_budget_satisfied` from fields (not `pipeline_ok`)
- If `not throughput_budget_satisfied`, append `THROUGHPUT_TARGET_SHORTFALL_ISSUE_CODE` to `issue_codes` when list would otherwise be empty and validation passed

When `None`, keep PR-2b behavior: `throughput_budget_satisfied: pipeline_ok`.

**Do not** derive `throughput_budget_satisfied` from `validation_passed`, `run_success`, `capacity_satisfied`, or `pipeline_ok` when budget fields are provided.

- [ ] **Step 3: pytest**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_solver_summary.py -v --tb=short
```

- [ ] **Step 4: Commit**

```bash
git add django_apps/asteroid_lab/optimization/rttp_solver_summary.py tests/unit/asteroid_lab/test_rttp_solver_summary.py
git commit -m "feat(asteroid_lab): decouple throughput budget from pipeline_ok"
```

---

### Task 3: Runtime entry + CLI + HTTP validation

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- Modify: `django_apps/web/views/public_pages.py`
- Modify: `django_apps/asteroid_lab/management/commands/run_solver.py`
- Create: `tests/unit/web/test_asteroid_run_solver_config.py`

- [ ] **Step 1: Parse percent in `run_solver_runtime_for_project` early**

Wrap `parse_throughput_target_percent(run_config)` in try/except → return `_failure_result` with new error code or re-raise `ValueError` mapped to 400.

Persist validated percent back into `run_config` copy used for `create_solver_run`.

- [ ] **Step 2: After pipeline, build budget summary**

```python
from django_apps.asteroid_lab.services.throughput_target import (
    build_throughput_budget_summary,
    parse_throughput_target_percent,
)

percent = parse_throughput_target_percent(run_config)
capacity_env = build_reconstruction_capacity_envelope(recon=recon)
budget_fields = None
if pipeline_result.actual_committed_output_per_min is not None:
    budget_fields = build_throughput_budget_summary(
        reconstruction_capacity=capacity_env,
        throughput_target_percent=percent,
        actual_committed_output_per_min=pipeline_result.actual_committed_output_per_min,
    )
summary = build_rttp_solver_summary(
    ...
    throughput_budget_fields=budget_fields,
)
```

- [ ] **Step 3: HTTP validation helper in `public_pages.py`**

```python
def _validate_throughput_target_percent(config: dict[str, Any]) -> JsonResponse | None:
    if "throughput_target_percent" not in config:
        return None
    try:
        parse_throughput_target_percent(config)
    except ValueError:
        return JsonResponse({"ok": False, "error": "invalid_throughput_target_percent"}, status=400)
    return None
```

Call from `_run_solver_request_config` merge path before `run_solver_runtime_for_project`.

- [ ] **Step 4: CLI flag**

```python
parser.add_argument(
    "--throughput-target-percent",
    type=int,
    default=None,
    help="Throughput target as percent of reconstruction max (10-80).",
)
...
if options["throughput_target_percent"] is not None:
    config[SOLVER_RUN_CONFIG_THROUGHPUT_TARGET_PERCENT_KEY] = int(options["throughput_target_percent"])
```

- [ ] **Step 5: Web test**

```python
@pytest.mark.django_db
def test_run_solver_rejects_percent_5(client, project_with_map):
    url = reverse("...", kwargs={"slug": project.slug})
    resp = client.post(
        url,
        data=json.dumps({"throughput_target_percent": 5}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid_throughput_target_percent"
```

- [ ] **Step 6: Run tests**

```powershell
python -m pytest tests/unit/web/test_asteroid_run_solver_config.py tests/unit/asteroid_lab/test_throughput_target.py -v --tb=short
```

- [ ] **Step 7: Commit**

```bash
git add django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/web/views/public_pages.py django_apps/asteroid_lab/management/commands/run_solver.py tests/unit/web/test_asteroid_run_solver_config.py
git commit -m "feat(asteroid_lab): wire throughput target percent on solver runtime"
```

---

### Task 4: Lab DTO `throughput_target` section

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_run_lab_summary.py`
- Modify: `tests/unit/asteroid_lab/test_solver_run_lab_summary.py`

- [ ] **Step 1: Add `_section_throughput_target`**

```python
def _section_throughput_target(summary: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "reconstruction_max_throughput_per_min",
        "throughput_target_percent",
        "target_throughput_per_min",
        "actual_committed_output_per_min",
        "throughput_budget_satisfied",
        "throughput_shortfall_per_min",
        "target_utilization_ratio",
        "actual_utilization_ratio",
        "budget_status",  # "satisfied" | "shortfall" | "—"
    )
    ...
```

`budget_status`: `"satisfied"` if `throughput_budget_satisfied` else `"shortfall"` if actual+target present else `"—"`.

- [ ] **Step 2: Attach to row** `"throughput_target": _section_throughput_target(solver_summary)`

- [ ] **Step 3: pytest + commit**

---

### Task 5: Lab UI slider + card/detail + i18n

**Files:**
- Modify: `django_apps/web/templates/web/asteroid_miner_layout_solver.html`
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- Modify: `scripts/build_locale_ko.py`
- Modify: `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py`

- [ ] **Step 1: Template — range input in left **Extractor Constraints** card (below rule list, not header)**

Per spec: `asteroid_miner_layout_solver.html` — border-top block after extractor rules loop, before the `—` placeholder footnote.

```html
<div class="mt-4 border-t border-slate-800 pt-4">
  <label for="lab-throughput-target-percent" class="text-xs font-medium text-slate-400">{% trans "Target throughput" %}</label>
  <div class="mt-2 flex items-center gap-3">
    <input type="range" id="lab-throughput-target-percent" class="flex-1" min="10" max="80" step="10" value="80" />
    <span id="lab-throughput-target-percent-label" class="w-10 text-right text-sm font-semibold text-slate-100">80%</span>
  </div>
  <p class="mt-1 text-xs text-slate-500">{% trans "% of theoretical max" %}</p>
</div>
```

Wire `input` event → update `#lab-throughput-target-percent-label` text (`NN%`).

- [ ] **Step 2: JS — include in POST body**

```javascript
const percent = parseInt(document.getElementById("lab-throughput-target-percent").value, 10);
const body = { throughput_target_percent: percent };
```

- [ ] **Step 3: JS — card 5 + detail panel C rows**

Use `run.throughput_target` nested object; format shortfall and utilization %.

- [ ] **Step 4: KO locale entries**

Msgids: `Target throughput`, `Target percent`, `Committed output`, `Short by`, `satisfied`, `shortfall`, `Utilization`.

```powershell
python scripts/build_locale_ko.py
```

- [ ] **Step 5: UI string regression** — forbid `actual output pending` when throughput_target has actual

- [ ] **Step 6: Commit**

```bash
git add django_apps/web/templates/web/asteroid_miner_layout_solver.html django_apps/web/static/web/js/asteroid_miner_layout_lab.js scripts/build_locale_ko.py tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py
git commit -m "feat(web): Lab throughput target percent control and budget display"
```

---

### Task 6: Doc touch-ups (PR-2a one line only)

**Files:**
- Modify: `docs/superpowers/specs/2026-05-24-reconstruction-max-throughput-pr2a-design.md` (PR split table row for PR-2c only)
- Modify: `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` (one line queued → in flight when PR opens)

- [ ] **Step 1: PR-2a follow-up row**

```markdown
| PR-2c | User `throughput_target_percent` 10–80; `target_throughput_per_min`; real `throughput_budget_satisfied` — see [throughput-target-percent-pr2c-design.md](2026-05-24-throughput-target-percent-pr2c-design.md) |
```

- [ ] **Step 2: Commit docs only**

```bash
git add docs/superpowers/specs/2026-05-24-reconstruction-max-throughput-pr2a-design.md docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md
git commit -m "docs: link PR-2c throughput target percent spec"
```

---

## Acceptance checklist (PR-2c UI + backend)

- [ ] Header contains no target slider
- [ ] Extractor Constraints contains target slider
- [ ] Slider does not auto-run solver
- [ ] Run Solver POST includes `throughput_target_percent`
- [ ] Backend rejects &lt;10 or &gt;80
- [ ] `target = ceil(reconstruction_max * percent / 100)`
- [ ] `throughput_budget_satisfied` only uses `actual >= target`
- [ ] Actual unavailable does not display shortfall
- [ ] Korean strings go through gettext / `shapezUiT`

## Plan gate (pre-merge)

- [ ] PR-2b dependency satisfied (`actual_committed_output_per_min` present)
- [ ] `throughput_budget_satisfied` never copied from `pipeline_ok` when budget fields built
- [ ] Config 10–80 enforced web + CLI + parse helper
- [ ] No greedy_regret / commit changes
- [ ] Narrow pytest green

```powershell
python -m pytest tests/unit/asteroid_lab/test_throughput_target.py tests/unit/asteroid_lab/test_committed_throughput_summary.py tests/unit/asteroid_lab/test_rttp_solver_summary.py tests/unit/asteroid_lab/test_solver_run_lab_summary.py tests/unit/web/test_asteroid_run_solver_config.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/services/throughput_target.py django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/web/views/public_pages.py
python scripts/build_locale_ko.py
```

---

## Self-review (spec coverage)

| Spec requirement | Task |
|------------------|------|
| Config 10–80 default 80 | Task 1, 3 |
| ceil target | Task 1 |
| budget satisfied = actual >= target | Task 1–2 |
| decouple pipeline_ok | Task 2 |
| solver_summary JSON fields | Task 2–3 |
| Lab slider + card/detail | Task 5 |
| issue code shortfall | Task 2 |
| PR-2a body unchanged (one line) | Task 6 |
| PR-2d out of scope | header |

PR-2d (selection scoring): separate spec `2026-05-24-throughput-target-selection-pr2d-design.md` — not in this plan.
