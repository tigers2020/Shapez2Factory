# Layer Stack L4/L5 Renumber (PR-1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct layer contract so **L4 = inner pattern fill** and **L5 = transport routing**, with canonical slugs, read-compat slug resolver, stack order L3→L4→L5→L6, and updated Lab/replay surfaces—without physical directory moves (PR-2).

**Architecture:** Add canonical constants + `resolve_canonical_layer_slug()` in `layer_slugs.py`; introduce `layer05_route.py` DTOs with `layer04_route.py` re-export shim; runner entrypoints get canonical names on misnumbered packages via thin `run.py` aliases; `stack_runner` swaps branch order and removes fill←transport dependency; replay emits `layer05_transport_routing_*` while registering deprecated wire strings; tests lock acceptance A1–A6 from spec.

**Tech Stack:** Python 3.12, Django `django_apps/asteroid_lab`, `src/shapez2_factory`, pytest, ruff, mypy, black.

**Spec:** [`docs/superpowers/specs/2026-05-31-layer-stack-l4-l5-renumber-design.md`](../../specs/2026-05-31-layer-stack-l4-l5-renumber-design.md) (APPROVED)

**Out of scope (PR-2):** Moving `layer_04_transport_routing/` ↔ `layer_05_inner_pattern_fill/` directories.

**Verification (per task):** `python -m pytest <path> -v`  
**Verification (PR gate):** `powershell -File scripts/test_fast.ps1` → `ruff check .` → `mypy django_apps config src` → `black --check .`

**Commits:** Only when the user explicitly requests a commit (repo `AGENTS.md`).

---

## File structure (PR-1)

| Path | Responsibility |
| ---- | -------------- |
| `src/.../contracts/layer_slugs.py` | Canonical L4/L5 slug strings; `LAYERS_02_TO_06_ACTIVE` order; `resolve_canonical_layer_slug` |
| `django_apps/.../contracts/layer_slugs.py` | Shim re-export (existing pattern) |
| `src/.../contracts/layer05_route.py` | **New** canonical transport DTOs (`Layer05RoutePlan`, …) |
| `src/.../contracts/layer04_route.py` | **Shim** re-export `Layer04*` aliases → `Layer05*` |
| `src/.../contracts/layer04_inner_fill.py` | **New** stub `Layer04InnerFillResult` |
| `src/.../layer_04_transport_routing/run.py` | Add `run_layer_05_transport_routing`; deprecate alias `run_layer_04_*` |
| `src/.../layer_05_inner_pattern_fill/run.py` | Add `run_layer_04_inner_pattern_fill` (no route plan); deprecate `run_layer_05_*` |
| `src/.../stack_runner.py` | L4 fill branch before L5 transport; wire `last_layer05_plan` |
| `src/.../run_stack.py` | Runner tuple order + slug constants |
| `django_apps/.../stack_runner.py` | Mirror core stack |
| `django_apps/.../replay/replay_enums.py` | `LAYER05_TRANSPORT_*` canonical enum values |
| `django_apps/.../replay/event_types.py` | Register `layer05_transport_*` + keep `layer04_transport_*` |
| `django_apps/.../replay/layer05_transport_segment.py` | **New** segment (copy from layer04, canonical events) |
| `django_apps/.../replay/layer04_transport_segment.py` | Shim re-export from layer05 |
| `django_apps/.../replay/solver_runtime_assembler.py` | L3→L4 fill→L5 transport compose order |
| `django_apps/.../services/solver_run_lab_summary.py` | Layer cards index 4=fill, 5=transport |
| `src/.../observability/layer05_post_summary_metrics.py` | **New** `build_layer05_transport_post_summary_metrics` |
| `src/.../observability/layer04_post_summary_metrics.py` | Shim to layer05 |
| `src/.../observability/layer_behavior_catalog.py` | Slug keys L4 fill / L5 transport |
| `tests/unit/asteroid_lab/layers/contracts/test_layer_slug_resolver.py` | **New** A2 |
| `tests/unit/asteroid_lab/layers/test_stack_runner_l4_l5_order.py` | **New** A1, A6 |
| `tests/unit/asteroid_lab/replay/test_layer05_transport_segment.py` | **New** A4 (migrate from layer04 test) |
| Docs | Spec amendments + transport plan banner |

---

## Task 1: Canonical slugs + resolver (A2)

**Files:**
- Modify: `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer_slugs.py`
- Modify: `django_apps/asteroid_lab/layers/contracts/layer_slugs.py` (re-export only if auto-generated pattern)
- Create: `tests/unit/asteroid_lab/layers/contracts/test_layer_slug_resolver.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/asteroid_lab/layers/contracts/test_layer_slug_resolver.py
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
    LAYERS_02_TO_06_ACTIVE,
    resolve_canonical_layer_slug,
)


def test_canonical_slug_constants() -> None:
    assert LAYER_04_INNER_PATTERN_FILL == "layer_04_inner_pattern_fill"
    assert LAYER_05_TRANSPORT_ROUTING == "layer_05_transport_routing"


def test_active_stack_order_fill_before_transport() -> None:
    slugs = list(LAYERS_02_TO_06_ACTIVE)
    assert slugs.index(LAYER_04_INNER_PATTERN_FILL) < slugs.index(LAYER_05_TRANSPORT_ROUTING)


def test_resolve_deprecated_transport_slug() -> None:
    assert resolve_canonical_layer_slug("layer_04_transport_routing") == (
        LAYER_05_TRANSPORT_ROUTING
    )


def test_resolve_deprecated_inner_fill_slug() -> None:
    assert resolve_canonical_layer_slug("layer_05_inner_pattern_fill") == (
        LAYER_04_INNER_PATTERN_FILL
    )


def test_canonical_slug_is_identity() -> None:
    assert resolve_canonical_layer_slug(LAYER_05_TRANSPORT_ROUTING) == (
        LAYER_05_TRANSPORT_ROUTING
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/layers/contracts/test_layer_slug_resolver.py -v`  
Expected: FAIL (missing `resolve_canonical_layer_slug` or wrong `LAYERS_02_TO_06_ACTIVE` order)

- [ ] **Step 3: Implement slugs + resolver**

In `layer_slugs.py`, set:

```python
LAYER_04_INNER_PATTERN_FILL = "layer_04_inner_pattern_fill"
LAYER_05_TRANSPORT_ROUTING = "layer_05_transport_routing"
LAYER_04_RIM_BUNDLE_PLACEMENT = "layer_04_rim_bundle_placement"  # deprecated inactive

_DEPRECATED_SLUG_TO_CANONICAL: dict[str, str] = {
    "layer_04_transport_routing": LAYER_05_TRANSPORT_ROUTING,
    "layer_05_inner_pattern_fill": LAYER_04_INNER_PATTERN_FILL,
}

LAYERS_02_TO_06_ACTIVE: tuple[str, ...] = (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
    LAYER_06_COMMIT_VALIDATE,
)

_LAYER_INDEX: dict[str, int] = {
  # ... L4 inner, L5 transport ...
}


def resolve_canonical_layer_slug(slug: str) -> str:
    return _DEPRECATED_SLUG_TO_CANONICAL.get(slug, slug)
```

Remove misleading lines:

```python
LAYER_04_INNER_PATTERN_FILL = LAYER_05_INNER_PATTERN_FILL  # DELETE
```

Remove `LAYER_04_TRANSPORT_ROUTING` as a **canonical** constant; if needed for grep-compat in shims only, define in shim modules—not in canonical `layer_slugs.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/asteroid_lab/layers/contracts/test_layer_slug_resolver.py -v`  
Expected: PASS

---

## Task 2: Transport DTO rename — `Layer05RoutePlan` (contract)

**Files:**
- Create: `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer05_route.py`
- Modify: `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer04_route.py` (shim only)
- Modify: `tests/unit/asteroid_lab/layers/test_layer04_route_contracts.py` (import canonical `layer05_route` for new assertions; keep one alias test)

- [ ] **Step 1: Write failing alias test**

```python
# append to tests/unit/asteroid_lab/layers/test_layer04_route_contracts.py
from shapez2_factory.application.asteroid_lab.layers.contracts import layer04_route as shim
from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
    LAYER05_ROUTE_PLAN_VERSION,
    Layer05RoutePlan,
)


def test_layer04_route_shim_aliases_layer05_types() -> None:
    assert shim.Layer04RoutePlan is Layer05RoutePlan
    assert shim.LAYER04_ROUTE_PLAN_VERSION == LAYER05_ROUTE_PLAN_VERSION
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer04_route_contracts.py::test_layer04_route_shim_aliases_layer05_types -v`

- [ ] **Step 3: Create `layer05_route.py`**

Copy body from `layer04_route.py`, rename:

- `LAYER04_ROUTE_PLAN_VERSION` → `LAYER05_ROUTE_PLAN_VERSION = "layer05_route_plan_v1"`
- `Layer04RoutePlan` → `Layer05RoutePlan`
- `Layer04FailureReason` → `Layer05FailureReason`
- `Layer04SourceView` → `Layer05SourceView`
- `Layer04Failure` → `Layer05Failure`
- `Layer04Metrics` → `Layer05Metrics`

In `Layer05RoutePlan.from_payload` / version check: accept **both** `layer05_route_plan_v1` and deprecated `layer04_route_plan_v1`.

Replace `layer04_route.py` with:

```python
"""Deprecated import path; use layer05_route."""
from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
    LAYER05_ROUTE_PLAN_VERSION as LAYER04_ROUTE_PLAN_VERSION,
    Layer05Failure as Layer04Failure,
    Layer05FailureReason as Layer04FailureReason,
    Layer05Metrics as Layer04Metrics,
    Layer05RoutePlan as Layer04RoutePlan,
    Layer05SourceView as Layer04SourceView,
)
__all__ = [/* mirror exports */]
```

- [ ] **Step 4: Update transport package imports to `layer05_route`**

Grep `layer04_route` under `layer_04_transport_routing/` and change to `layer05_route` (sequential_router, run.py, source_adapter, tests under `test_layer04_*` may keep filenames but import `layer05_route`).

- [ ] **Step 5: Run transport unit tests**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer04_route_contracts.py tests/unit/asteroid_lab/layers/test_layer04_sequential_router.py tests/unit/asteroid_lab/layers/test_layer04_source_adapter.py -q`  
Expected: PASS

---

## Task 3: Inner fill stub contract (A3)

**Files:**
- Create: `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer04_inner_fill.py`
- Modify: `src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/run.py`
- Modify: `django_apps/asteroid_lab/layers/layer_05_inner_pattern_fill/run.py`
- Create: `tests/unit/asteroid_lab/layers/test_layer04_inner_fill_stub.py`

- [ ] **Step 1: Write failing test**

```python
import inspect
from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill.run import (
    run_layer_04_inner_pattern_fill,
)


def test_inner_fill_stub_has_no_route_plan_parameter() -> None:
    params = inspect.signature(run_layer_04_inner_pattern_fill).parameters
    assert "layer04_route_plan" not in params
    assert "layer05_route_plan" not in params
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement**

`layer04_inner_fill.py`:

```python
@dataclass(frozen=True, slots=True)
class Layer04InnerFillResult:
    interior_occupied_cells: frozenset[Coord] = frozenset()

    @classmethod
    def empty(cls) -> Layer04InnerFillResult:
        return cls()
```

`run.py`:

```python
def run_layer_04_inner_pattern_fill(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    provisional_overlay: ProvisionalLayoutOverlay,
    budget_ctx: LayerBudgetContext,
) -> Layer04InnerFillResult:
    _ = (complete_map, exterior_plan, provisional_overlay, budget_ctx)
    return Layer04InnerFillResult.empty()

run_layer_05_inner_pattern_fill = run_layer_04_inner_pattern_fill  # deprecated
```

- [ ] **Step 4: Run test — expect PASS**

---

## Task 4: Transport runner canonical name

**Files:**
- Modify: `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py`
- Modify: `django_apps/asteroid_lab/layers/layer_04_transport_routing/run.py`

- [ ] **Step 1: Rename entrypoint**

In core `run.py`, rename public function:

```python
def run_layer_05_transport_routing(...) -> Layer05RoutePlan:
    ...

run_layer_04_transport_routing = run_layer_05_transport_routing
```

Django delegate re-exports canonical name.

- [ ] **Step 2: Run** `python -m pytest tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py -v`

---

## Task 5: `stack_runner` order + wiring (A1, A6)

**Files:**
- Modify: `src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- Modify: `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- Modify: `django_apps/asteroid_lab/layers/stack_runner.py`
- Create: `tests/unit/asteroid_lab/layers/test_stack_runner_l4_l5_order.py`

- [ ] **Step 1: Write failing stack order test**

```python
from unittest.mock import MagicMock, patch
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
)
from shapez2_factory.application.asteroid_lab.stack_runner import run_layers_02_to_06
# ... patch L2/L3/L4/L5/L6 runners recording call order ...
# assert call_order == [..., LAYER_04_INNER_PATTERN_FILL, LAYER_05_TRANSPORT_ROUTING, ...]
```

(Follow pattern in `tests/unit/asteroid_lab/layers/test_stack_runner_layer04.py`.)

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Swap branches in `stack_runner.py`**

Execution order in loop / `_LAYER_INDEX`:

1. Replace `LAYER_04_TRANSPORT_ROUTING` branch with **inner fill** calling `run_layer_04_inner_pattern_fill`, store `last_inner_fill: Layer04InnerFillResult | None`.
2. Add **transport** branch on `LAYER_05_TRANSPORT_ROUTING` calling `run_layer_05_transport_routing`, pass `interior_occupied_cells=last_inner_fill.interior_occupied_cells if last_inner_fill else frozenset()` (extend signature in run.py stub param if needed).
3. Remove `layer04_route_plan` from fill path entirely.
4. Delete old L5 fill branch body that built empty `Layer04RoutePlan` for fill input.

Update `run_stack.py` runners tuple:

```python
_LayerStackRunner(LAYER_04_INNER_PATTERN_FILL, run_layer_04_inner_pattern_fill),
_LayerStackRunner(LAYER_05_TRANSPORT_ROUTING, run_layer_05_transport_routing),
```

Mirror `django_apps/asteroid_lab/layers/stack_runner.py`.

- [ ] **Step 4: Run stack tests**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_stack_runner_l4_l5_order.py tests/unit/asteroid_lab/layers/test_stack_runner_layer04.py tests/unit/asteroid_lab/layers/test_stack_runner_accepts_empty_l3.py -v`

Rename `test_stack_runner_layer04.py` → `test_stack_runner_layer05_transport.py` and update slug assertions to `LAYER_05_TRANSPORT_ROUTING`.

---

## Task 6: Replay — canonical `layer05_transport_*` events (A4)

**Files:**
- Modify: `django_apps/asteroid_lab/replay/replay_enums.py`
- Modify: `django_apps/asteroid_lab/replay/event_types.py`
- Create: `django_apps/asteroid_lab/replay/layer05_transport_segment.py`
- Modify: `django_apps/asteroid_lab/replay/layer04_transport_segment.py` (shim re-export)
- Modify: `tests/unit/asteroid_lab/replay/test_layer04_transport_segment.py` → `test_layer05_transport_segment.py`

- [ ] **Step 1: Write failing test for canonical event wire**

```python
from django_apps.asteroid_lab.replay.layer05_transport_segment import (
    build_layer05_transport_frames,
)
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
    Layer05RoutePlan,
    # ... minimal plan fixture ...
)

def test_transport_segment_emits_layer05_event_types() -> None:
    frames = build_layer05_transport_frames(plan)
    assert frames[0].event_type == ReplayEventType.LAYER05_TRANSPORT_ROUTING_BEGIN
    assert frames[1].event_type == ReplayEventType.LAYER05_TRANSPORT_ROUTING_COMPLETE
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement**

`replay_enums.py`:

```python
LAYER05_TRANSPORT_ROUTING_BEGIN = "layer05_transport_routing_begin"
LAYER05_TRANSPORT_ROUTING_COMPLETE = "layer05_transport_routing_complete"
# Keep LAYER04_TRANSPORT_* with OLD string values for persisted frame compat
```

`event_types.py`: add `EVENT_TYPE_LAYER05_TRANSPORT_ROUTING_BEGIN/COMPLETE` to `SNAPSHOT_EVENT_TYPES`.

`layer05_transport_segment.py`: copy from `layer04_transport_segment.py`; use `LAYER05_TRANSPORT_PHASE = "layer_05_transport_routing"`; `build_layer05_transport_frames`.

`layer04_transport_segment.py`:

```python
from django_apps.asteroid_lab.replay.layer05_transport_segment import (
    build_layer05_transport_frames as build_layer04_transport_frames,
)
```

Update segment builder tests; add test that `is_registered_event_type("layer04_transport_routing_begin")` still True.

- [ ] **Step 4: Run replay tests**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_layer05_transport_segment.py tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py -q`

---

## Task 7: Replay assembler compose order

**Files:**
- Modify: `django_apps/asteroid_lab/replay/solver_runtime_assembler.py`
- Modify: `django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py`

- [ ] **Step 1: Write failing assembler order test** (optional if covered in Task 5 integration)

Assert frame `event_type` list: greedy complete appears **before** `layer05_transport_routing_begin`.

- [ ] **Step 2: Update imports and builders**

- `build_layer05_transport_frames` / `layer04_route_plan` param → rename to `layer05_route_plan: Layer05RoutePlan | None`
- Compose order: L2 → L3 → **(optional L4 fill frames stub)** → L5 transport
- `build_persistent_committed_equipment_overlay_wire` unchanged; still on transport frames

`artifact_runtime_replay_compose.py`: call `run_layer_05_transport_routing`; pass `layer05_route_plan` into `build_solver_runtime_replay_frames`.

- [ ] **Step 3: Run** `python -m pytest tests/unit/asteroid_lab/replay/test_layer03_persistent_equipment_replay.py tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py -q`

---

## Task 8: Lab summary layer cards (A5)

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_run_lab_summary.py`
- Modify: `tests/unit/asteroid_lab/test_solver_run_lab_summary_greedy.py`

- [ ] **Step 1: Update greedy tests**

Layer 4 card: slug `layer_04_inner_pattern_fill`, title `"Inner pattern fill"`, outcome pending/completed from `resolve_canonical_layer_slug`.

Layer 5 card: slug `layer_05_transport_routing`, title `"Transport routing"`, metrics from `layer_summaries` slug `layer_05_transport_routing`.

Remove conflation where L4 row was rim-bundle superseded / transport.

- [ ] **Step 2: Use resolver in `_resolved_completed_layer_slugs`**

Normalize each slug through `resolve_canonical_layer_slug` when comparing membership.

- [ ] **Step 3: Run** `python -m pytest tests/unit/asteroid_lab/test_solver_run_lab_summary_greedy.py tests/unit/asteroid_lab/test_solver_summary_validation_contract.py -q`

---

## Task 9: Observability slugs

**Files:**
- Create: `src/.../observability/layer05_post_summary_metrics.py` (move body from layer04)
- Modify: `src/.../observability/layer04_post_summary_metrics.py` (shim)
- Modify: `src/.../observability/layer_behavior_catalog.py`
- Modify: `src/.../observability/post_summary_metrics.py` (`build_layer04_inner_fill_post_summary_metrics` stub)
- Modify: `documents/ai/manuals/environment.md` (JSONL slug list)

- [ ] **Step 1:** `build_layer05_transport_post_summary_metrics(plan: Layer05RoutePlan)`
- [ ] **Step 2:** `stack_runner` calls metrics builder with `LAYER_05_TRANSPORT_ROUTING` slug
- [ ] **Step 3:** `layer_behavior_catalog` keys: L4 fill, L5 transport

---

## Task 10: Docs amendments

**Files:**
- Modify: `docs/superpowers/specs/2026-05-31-layer-03-rim-placement-v2-design.md` (L4 fill / L5 transport refs)
- Modify: `docs/superpowers/specs/2026-05-31-layer-04-transport-routing-design.md` (header amendment → owner slug L5)
- Modify: `docs/superpowers/plans/2026-05-31-layer-04-transport-routing/README.md` (banner: renumber spec; pause new L4 transport tasks until PR-1 lands)

- [ ] **Step 1:** Apply editorial amendments only; no algorithm changes.

---

## Task 11: Full gate + grep hygiene

- [ ] **Step 1:** Grep for stale **canonical** usage (must be zero in new code):

```powershell
rg "LAYER_04_TRANSPORT_ROUTING|layer_04_transport_routing" src django_apps tests --glob '!*layer04*' --glob '!*layer05_route*'
```

Allowed: shim files, resolver map, deprecated enum members, compat tests.

- [ ] **Step 2:** Run full fast gate

```powershell
powershell -File scripts/test_fast.ps1
ruff check .
mypy django_apps config src
black --check .
```

Expected: all green.

---

## Spec coverage self-review

| Spec requirement | Task |
| ---------------- | ---- |
| A1 stack order | Task 5 |
| A2 slugs + resolver | Task 1 |
| A3 fill no route plan | Task 3 |
| A4 replay layer05 events | Task 6 |
| A5 Lab cards | Task 8 |
| A6 fill before transport | Task 5 |
| DTO Layer05RoutePlan + alias | Task 2 |
| Runner shims | Tasks 3–4 |
| Replay compose order | Task 7 |
| JSONL / observability | Task 9 |
| Doc amendments | Task 10 |
| PR-2 out of scope | — |
| Optional L4 fill replay segment | **Deferred** (stub has no observability; add begin/complete only if product needs timeline row before transport) |

**Placeholder scan:** None intended.

**Type consistency:** Use `Layer05RoutePlan` / `last_layer05_plan` in all new stack/replay code after Task 2.

---

## Execution handoff

Plan saved to [`docs/superpowers/plans/2026-05-31-layer-stack-l4-l5-renumber/README.md`](README.md).

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute in this session via executing-plans with checkpoints  

Which approach?
