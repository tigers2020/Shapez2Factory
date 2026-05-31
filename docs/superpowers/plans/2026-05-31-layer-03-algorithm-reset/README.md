# Layer 03 Algorithm Reset — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove PR-B rim greedy algorithm code from the CLI core, replace Layer 03 with a deterministic empty stub (`reset_stub_v1`), and keep stack/replay/artifact boundaries green.

**Architecture:** Single authority in `src/shapez2_factory/.../layer_03_rim_greedy_placement/run.py`; Django keeps re-export shims only. DTOs (`IntegratedRimGreedyResult`, replay event types) stay stable; `Layer03SkipReason.ALGORITHM_RESET` marks intentional no-op. `shared/route_probe.py` is **retained** in this PR.

**Tech Stack:** Python 3.12+, pytest, ruff; Asteroid Lab hexagonal core + Django adapters.

**SoT (normative):** [`../../specs/2026-05-31-layer-03-algorithm-reset-design.md`](../../specs/2026-05-31-layer-03-algorithm-reset-design.md)

**Historical only (do NOT implement from):** [`../../specs/2026-05-30-layer-03-boundary-m-repack-greedy-design.md`](../../specs/2026-05-30-layer-03-boundary-m-repack-greedy-design.md)

**Checklist tracker:** [`checklist.md`](checklist.md)

---

## File map (decomposition)

| Responsibility | Path |
|----------------|------|
| L3 entry (stub) | `src/.../layer_03_rim_greedy_placement/run.py` |
| Skip reason enum | `src/.../contracts/candidates.py` |
| Empty result builder | `src/.../contracts/rim_greedy.py` |
| Post-summary metrics | `src/.../observability/post_summary_metrics.py` |
| Route probe (RETAIN) | `src/.../layers/shared/route_probe.py` |
| Django re-export | `django_apps/.../layer_03_rim_greedy_placement/run.py` |
| Stack wiring | `django_apps/.../layers/stack_runner.py`, `src/.../run_stack.py` |
| Greedy replay segment | `django_apps/.../replay/layer03_rim_greedy_segment.py` |
| Reset tests | `tests/unit/asteroid_lab/layers/test_layer_03_reset_stub_contract.py` (new) |

---

## Preflight (mandatory)

### Task 0: Authoritative docs + test classification inventory

**Files:**
- Read: `docs/superpowers/specs/2026-05-31-layer-03-algorithm-reset-design.md`
- Create: `docs/superpowers/plans/2026-05-31-layer-03-algorithm-reset/deletion-inventory.md`

- [ ] **Step 1: Record SoT warning at top of deletion inventory**

```markdown
# L3 reset deletion inventory

**SoT:** 2026-05-31-layer-03-algorithm-reset-design.md
**Do NOT use:** 2026-05-30-layer-03-boundary-m-repack-greedy-design.md (SUPERSEDED)
```

- [ ] **Step 2: Classify every file under `tests/unit/asteroid_lab` matching `layer_03` or `layer03`**

Run:

```bash
git ls-files "tests/unit/asteroid_lab/**/test_layer_03*.py" "tests/unit/asteroid_lab/**/test_layer03*.py"
```

Fill a table with columns: `path | class (1-5) | action (DELETE/KEEP/ADD) | rationale`.

**Normative classification (baseline):**

| Path | Class | Action |
|------|-------|--------|
| `tests/.../test_layer_03_boundary_m_repack_acceptance.py` | 1 | DELETE |
| `tests/.../test_layer_03_rim_greedy_pass2.py` | 1 | DELETE |
| `tests/.../test_layer_03_rim_greedy_variants.py` | 1 | DELETE |
| `tests/.../test_layer_03_rim_greedy_append.py` | 1 | DELETE |
| `tests/.../test_layer_03_rim_greedy_reservation.py` | 1 | DELETE |
| `tests/.../test_layer_03_rim_greedy_run.py` | 1 | DELETE |
| `tests/.../test_layer_03_rim_greedy_anchors.py` | 1 | DELETE |
| `tests/.../test_layer_03_rim_greedy_seed_orient.py` | 1 | DELETE |
| `tests/.../test_layer_03_route_goal_builder.py` | 1 | DELETE |
| `tests/.../test_layer_03_04_skeleton.py` | 1 | DELETE |
| `tests/.../replay/test_layer03_append_replay_parity.py` | 1 | DELETE |
| `tests/.../replay/test_layer03_rim_greedy_segment.py` | 1 | DELETE |
| `tests/.../replay/test_layer03_pool_windowing.py` | 1 | DELETE |
| `tests/.../test_lab_replay_timeline_layer03_runtime.py` | 1 | DELETE |
| `tests/.../contracts/test_rim_greedy_contracts.py` | 2 | KEEP (extend) |
| `tests/.../contracts/test_rim_greedy_append_contracts.py` | 2 | KEEP |
| `tests/.../test_stack_runner_core_boundary.py` | 3 | KEEP |
| `tests/.../replay/test_layer03_exterior_connector_overlay_persistence.py` | 4 | KEEP |
| `tests/.../replay/test_layer03_pattern_bundle_highlights.py` | 4 | KEEP (legacy bundle segment) |
| `tests/.../test_layer_03_l4_boundary.py` | 5 | KEEP |
| `tests/.../test_layer_04_disabled_shim.py` | 5 | KEEP |
| `tests/.../test_layer_03_reset_stub_contract.py` | ADD | CREATE |
| `tests/.../test_stack_runner_accepts_empty_l3.py` | ADD | CREATE |
| `tests/.../test_no_django_l3_algorithm_authority.py` | ADD | CREATE |

- [ ] **Step 3: Record core file deletion list (R6)**

```
src/.../layer_03_rim_greedy_placement/greedy_pass1.py
src/.../layer_03_rim_greedy_placement/greedy_pass2.py
src/.../layer_03_rim_greedy_placement/traversal_variants.py
src/.../layer_03_rim_greedy_placement/rim_anchors.py
src/.../layer_03_rim_greedy_placement/append.py
src/.../layer_03_rim_greedy_placement/greedy_seed.py
src/.../layer_03_rim_greedy_placement/seed_orient.py
src/.../layer_03_rim_greedy_placement/cardinal_map.py
src/.../layer_03_rim_greedy_placement/local_window.py
src/.../layer_03_rim_greedy_placement/dps_policy.py
src/.../layer_03_rim_mining_bundles/  (entire package)
django_apps/.../layer_03_rim_greedy_placement/* (same names, except __init__.py + run.py)
django_apps/.../layer_03_rim_mining_bundles/  (entire package)
tests/.../fixtures/layer_03_deep_rim_map.py  (after DELETE class-1 tests)
```

- [ ] **Step 4: Verify `route_probe` retention (R7)**

```bash
git grep -n "shared.route_probe" -- "*.py"
git grep -n "from shapez2_factory.application.asteroid_lab.layers.shared.route_probe" -- "*.py"
```

Expected before deletion: imports only from `greedy_pass1.py` (and django shim). After `greedy_pass1.py` deleted: **no importers** — file still **RETAINED** per spec.

---

## Task 1: `Layer03SkipReason.ALGORITHM_RESET` + contract test

**Files:**
- Modify: `src/shapez2_factory/application/asteroid_lab/layers/contracts/candidates.py`
- Modify: `tests/unit/asteroid_lab/layers/contracts/test_rim_greedy_contracts.py`

- [ ] **Step 1: Write failing test for new enum member**

Add to `test_rim_greedy_contracts.py`:

```python
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import Layer03SkipReason


def test_layer03_skip_reason_includes_algorithm_reset() -> None:
    assert Layer03SkipReason.ALGORITHM_RESET == "algorithm_reset"
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/layers/contracts/test_rim_greedy_contracts.py::test_layer03_skip_reason_includes_algorithm_reset -v
```

Expected: `AttributeError: ALGORITHM_RESET`

- [ ] **Step 3: Add enum member**

In `candidates.py` inside `class Layer03SkipReason(StrEnum):`:

```python
ALGORITHM_RESET = "algorithm_reset"
```

- [ ] **Step 4: Run test — expect PASS**

```bash
python -m pytest tests/unit/asteroid_lab/layers/contracts/test_rim_greedy_contracts.py::test_layer03_skip_reason_includes_algorithm_reset -v
```

- [ ] **Step 5: Commit**

```bash
git add src/shapez2_factory/application/asteroid_lab/layers/contracts/candidates.py tests/unit/asteroid_lab/layers/contracts/test_rim_greedy_contracts.py
git commit -m "feat(asteroid-lab): add Layer03SkipReason.ALGORITHM_RESET"
```

---

## Task 2: Reset stub contract tests (RED)

**Files:**
- Create: `tests/unit/asteroid_lab/layers/test_layer_03_reset_stub_contract.py`

- [ ] **Step 1: Create failing stub contract tests**

```python
"""Layer 03 reset stub — deterministic empty result (spec 2026-05-31)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import Layer03SkipReason
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    RimGreedyObservationPhase,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)

_RESET = Layer03SkipReason.ALGORITHM_RESET


def test_layer_03_returns_empty_result_without_algorithm() -> None:
    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    assert result.committed_placements == ()
    assert result.metrics.committed_placement_count == 0
    assert result.metrics.layer_skip_reason == _RESET
    assert str(result.metrics.layer_skip_reason) == "algorithm_reset"
    assert result.pass2_report.hard_fail is True
    phases = {e.phase for e in result.observability_events}
    assert RimGreedyObservationPhase.RIM_GREEDY_BEGIN in phases
    assert RimGreedyObservationPhase.RIM_GREEDY_COMPLETE in phases


def test_layer_03_missing_exterior_plan_uses_enum_skip_not_reset() -> None:
    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=None,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    assert result.metrics.layer_skip_reason == Layer03SkipReason.MISSING_EXTERIOR_CONNECTION_PLAN
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_reset_stub_contract.py -v
```

Expected: `layer_skip_reason` not `algorithm_reset` (still runs greedy) or missing enum on metrics.

- [ ] **Step 3: Commit test-only**

```bash
git add tests/unit/asteroid_lab/layers/test_layer_03_reset_stub_contract.py
git commit -m "test(asteroid-lab): add L3 reset stub contract tests (red)"
```

---

## Task 3: Replace `run.py` with reset stub (GREEN)

**Files:**
- Modify: `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/run.py` (replace entire module)
- Modify: `src/shapez2_factory/application/asteroid_lab/layers/contracts/rim_greedy.py` (use enum wire values for existing skip paths if needed)

- [ ] **Step 1: Replace `run.py` with stub implementation**

```python
"""Layer 3 — reset stub (algorithm removed; see 2026-05-31-layer-03-algorithm-reset-design)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import Layer03SkipReason
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    IntegratedRimGreedyResult,
    RimGreedyPolicy,
    _skip_observability_events,
    build_empty_integrated_rim_greedy_result,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    ResourceKind,
    TransportKind,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)

ALGORITHM_STUB_ID = "reset_stub_v1"


def run_layer_03_rim_greedy_placement(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    budget_ctx: LayerBudgetContext,
    seed_catalog: object | None = None,
    resource_kind: ResourceKind | None = None,
    transport_kind: TransportKind | None = None,
    policy: RimGreedyPolicy | None = None,
) -> IntegratedRimGreedyResult:
    _ = (
        complete_map,
        budget_ctx,
        seed_catalog,
        resource_kind,
        transport_kind,
        policy,
    )
    if exterior_plan is None:
        return build_empty_integrated_rim_greedy_result(
            layer_skip_reason=Layer03SkipReason.MISSING_EXTERIOR_CONNECTION_PLAN.value,
            rim_anchor_count=0,
        )
    reset_reason = Layer03SkipReason.ALGORITHM_RESET.value
    return build_empty_integrated_rim_greedy_result(
        layer_skip_reason=reset_reason,
        rim_anchor_count=0,
        observability_events=_skip_observability_events(
            layer_skip_reason=reset_reason,
            rim_anchor_count=0,
        ),
    )


__all__ = ["ALGORITHM_STUB_ID", "run_layer_03_rim_greedy_placement"]
```

Note: `_skip_observability_events` may be private — if ruff/mypy blocks import, add a public `build_reset_observability_events()` in `rim_greedy.py` instead (preferred for clean API).

- [ ] **Step 2: Export observability helper if import blocked**

If `_skip_observability_events` cannot be imported from outside `rim_greedy.py`, add:

```python
def build_layer03_reset_observability_events() -> tuple[RimGreedyObservationEvent, ...]:
    return _skip_observability_events(
        layer_skip_reason=Layer03SkipReason.ALGORITHM_RESET.value,
        rim_anchor_count=0,
    )
```

and use that from `run.py`.

- [ ] **Step 3: Run reset contract tests — expect PASS**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_reset_stub_contract.py -v
```

- [ ] **Step 4: Commit**

```bash
git add src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/run.py src/shapez2_factory/application/asteroid_lab/layers/contracts/rim_greedy.py
git commit -m "feat(asteroid-lab): replace L3 run with reset_stub_v1 empty entrypoint"
```

---

## Task 4: Post-summary `algorithm_stub` field

**Files:**
- Modify: `src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py`
- Modify: `tests/unit/asteroid_lab/layers/test_layer_03_reset_stub_contract.py`

- [ ] **Step 1: Add failing assertion on post-summary metrics**

Extend `test_layer_03_returns_empty_result_without_algorithm`:

```python
from shapez2_factory.application.asteroid_lab.layers.observability.post_summary_metrics import (
    build_layer03_rim_greedy_post_summary_metrics,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    ALGORITHM_STUB_ID,
)

# inside test after run:
metrics = build_layer03_rim_greedy_post_summary_metrics(result)
assert metrics["algorithm_stub"] == ALGORITHM_STUB_ID
assert metrics["layer_skip_reason"] == _RESET.value
```

- [ ] **Step 2: Run test — expect FAIL** (`KeyError: algorithm_stub`)

- [ ] **Step 3: Implement metric field**

In `build_layer03_rim_greedy_post_summary_metrics`:

```python
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    ALGORITHM_STUB_ID,
)

# inside returned dict:
"algorithm_stub": (
    ALGORITHM_STUB_ID
    if result.metrics.layer_skip_reason == Layer03SkipReason.ALGORITHM_RESET.value
    else None
),
```

Import `Layer03SkipReason` from `contracts.candidates`.

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py tests/unit/asteroid_lab/layers/test_layer_03_reset_stub_contract.py
git commit -m "feat(asteroid-lab): expose algorithm_stub in L3 post-summary metrics"
```

---

## Task 5: Delete algorithm modules (core + Django mirrors)

**Files:** See Task 0 deletion list.

- [ ] **Step 1: Delete core algorithm files**

```bash
git rm src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/greedy_pass1.py
git rm src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/greedy_pass2.py
git rm src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/traversal_variants.py
git rm src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_anchors.py
git rm src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/append.py
git rm src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/greedy_seed.py
git rm src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/seed_orient.py
git rm src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/cardinal_map.py
git rm src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/local_window.py
git rm src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/dps_policy.py
git rm -r src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_mining_bundles
```

- [ ] **Step 2: Delete Django duplicate algorithm files**

```bash
git rm django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/greedy_pass1.py
git rm django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/greedy_pass2.py
git rm django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/traversal_variants.py
git rm django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_anchors.py
git rm django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/append.py
git rm django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/greedy_seed.py
git rm django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/seed_orient.py
git rm django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/cardinal_map.py
git rm django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/local_window.py
git rm django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/dps_policy.py
git rm -r django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles
```

- [ ] **Step 3: Fix any broken imports** (`grep` for deleted module names)

```bash
git grep -n "greedy_pass1\|greedy_pass2\|rim_anchors\|traversal_variants" -- "*.py"
```

Expected: only historical docs or deletion inventory.

- [ ] **Step 4: Run layers tests — collect failures for Task 6–8**

```bash
python -m pytest tests/unit/asteroid_lab/layers/ -v --tb=short
```

- [ ] **Step 5: Commit**

```bash
git commit -m "refactor(asteroid-lab): remove L3 greedy algorithm modules"
```

---

## Task 6: Django CLI-first shims

**Files:**
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/run.py`
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/__init__.py`
- Modify: `django_apps/asteroid_lab/layers/stack_runner.py` (if still imports django local run)

- [ ] **Step 1: Replace Django `run.py` with re-export**

```python
"""Django shim — Layer 03 authority is in shapez2_factory core."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    ALGORITHM_STUB_ID,
    run_layer_03_rim_greedy_placement,
)

__all__ = ["ALGORITHM_STUB_ID", "run_layer_03_rim_greedy_placement"]
```

- [ ] **Step 2: Ensure `stack_runner` imports core or shim re-export only**

`django_apps/asteroid_lab/layers/stack_runner.py` should keep:

```python
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
```

(no direct `greedy_pass*` imports)

- [ ] **Step 3: Commit**

```bash
git add django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/
git commit -m "refactor(asteroid-lab): django L3 run is core re-export only"
```

---

## Task 7: Replay greedy segment no-op (R4)

**Files:**
- Modify: `django_apps/asteroid_lab/replay/layer03_rim_greedy_segment.py`
- Modify: `django_apps/asteroid_lab/replay/layer03_pool_windowing.py` (early return if no placements)

- [ ] **Step 1: At top of greedy segment builder for committed placements loop, guard:**

```python
if not result.committed_placements:
    # Reset stub: observability-only frames handled elsewhere
    return specs_from_observability_only(result)
```

Implement `specs_from_observability_only` to map `result.observability_events` → frames (BEGIN/COMPLETE only).

- [ ] **Step 2: Pool windowing early return**

```python
if not getattr(layer03_result, "committed_placements", None):
    return ()
```

(Adjust to actual parameter type: `IntegratedRimGreedyResult | RimBundleCandidateSet`.)

- [ ] **Step 3: Run class-4 replay tests**

```bash
python -m pytest tests/unit/asteroid_lab/replay/test_layer03_exterior_connector_overlay_persistence.py tests/unit/asteroid_lab/replay/test_layer03_pattern_bundle_highlights.py -v
```

- [ ] **Step 4: Commit**

```bash
git add django_apps/asteroid_lab/replay/layer03_rim_greedy_segment.py django_apps/asteroid_lab/replay/layer03_pool_windowing.py
git commit -m "fix(asteroid-lab): L3 greedy replay no-op on empty reset result"
```

---

## Task 8: Delete class-1 tests + unused fixtures

**Files:** Per `deletion-inventory.md` class 1 rows.

- [ ] **Step 1: Delete classified tests only (no glob blind delete)**

```bash
git rm tests/unit/asteroid_lab/layers/test_layer_03_boundary_m_repack_acceptance.py
git rm tests/unit/asteroid_lab/layers/test_layer_03_rim_greedy_pass2.py
git rm tests/unit/asteroid_lab/layers/test_layer_03_rim_greedy_variants.py
git rm tests/unit/asteroid_lab/layers/test_layer_03_rim_greedy_append.py
git rm tests/unit/asteroid_lab/layers/test_layer_03_rim_greedy_reservation.py
git rm tests/unit/asteroid_lab/layers/test_layer_03_rim_greedy_run.py
git rm tests/unit/asteroid_lab/layers/test_layer_03_rim_greedy_anchors.py
git rm tests/unit/asteroid_lab/layers/test_layer_03_rim_greedy_seed_orient.py
git rm tests/unit/asteroid_lab/layers/test_layer_03_route_goal_builder.py
git rm tests/unit/asteroid_lab/layers/test_layer_03_04_skeleton.py
git rm tests/unit/asteroid_lab/replay/test_layer03_append_replay_parity.py
git rm tests/unit/asteroid_lab/replay/test_layer03_rim_greedy_segment.py
git rm tests/unit/asteroid_lab/replay/test_layer03_pool_windowing.py
git rm tests/unit/asteroid_lab/test_lab_replay_timeline_layer03_runtime.py
```

- [ ] **Step 2: Delete fixtures with no importers**

```bash
git rm tests/unit/asteroid_lab/layers/fixtures/layer_03_deep_rim_map.py
```

Re-run `git grep layer_03_candidate_set_factory` — delete only if only deleted tests imported it.

- [ ] **Step 3: Commit**

```bash
git commit -m "test(asteroid-lab): remove PR-B greedy assumption tests"
```

---

## Task 9: `hard_fail` consumer audit

**Files:**
- Document in: `deletion-inventory.md` (append audit section)

- [ ] **Step 1: Run audit command**

```bash
git grep -n "hard_fail" -- "*.py"
```

- [ ] **Step 2: For each consumer outside deleted tests, verify no branch treats `hard_fail` as stack failure without checking `layer_skip_reason`**

Expected production consumers after cleanup:

- `rim_greedy.py` — sets `hard_fail=True` on empty builder (OK)
- No `stack_runner` / `run_stack` / L5 branch on `hard_fail` alone

If any consumer fails the rule, patch to:

```python
if result.pass2_report.hard_fail and result.metrics.layer_skip_reason != Layer03SkipReason.ALGORITHM_RESET.value:
    ...
```

- [ ] **Step 3: Add inventory note + commit doc-only or code fix**

```bash
git commit -m "docs(asteroid-lab): record hard_fail consumer audit for L3 reset"
```

---

## Task 10: Stack + Django authority tests

**Files:**
- Create: `tests/unit/asteroid_lab/layers/test_stack_runner_accepts_empty_l3.py`
- Create: `tests/unit/asteroid_lab/layers/test_no_django_l3_algorithm_authority.py`

- [ ] **Step 1: Stack integration test**

```python
"""Stack continues when L3 returns reset stub."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import Layer03SkipReason
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_05_INNER_PATTERN_FILL,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.stack_status import StackRunStatus
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.run import (
    run_layer_02_exterior_transport,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill.run import (
    run_layer_05_inner_pattern_fill,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
    empty_layer04_rim_placement_result,
)
from shapez2_factory.application.asteroid_lab.stack_runner import (
    LAYER_STACK_BUDGET_MS,
    _LayerStackRunner,
    run_layers_02_to_06,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map


def test_stack_runner_accepts_empty_l3_and_reaches_l5() -> None:
    complete_map = golden_5x5_complete_map()
    budget_ctx = LayerBudgetContext.from_budget_ms(LAYER_STACK_BUDGET_MS, now_fn=lambda: 0.0)
    runners = (
        _LayerStackRunner("layer_02_exterior_transport", run_layer_02_exterior_transport),
        _LayerStackRunner(LAYER_03_RIM_GREEDY_PLACEMENT, run_layer_03_rim_greedy_placement),
        _LayerStackRunner("layer_05_inner_pattern_fill", run_layer_05_inner_pattern_fill),
    )
    core = run_layers_02_to_06(complete_map=complete_map, budget_ctx=budget_ctx, runners=runners)
    assert core.stack_result.status == StackRunStatus.SUCCESS
    assert LAYER_03_RIM_GREEDY_PLACEMENT in core.stack_result.completed_layer_slugs
    l3_summary = next(
        s for s in core.layer_summaries if s.layer_slug == LAYER_03_RIM_GREEDY_PLACEMENT
    )
    assert l3_summary.metrics.get("layer_skip_reason") == Layer03SkipReason.ALGORITHM_RESET.value
    assert l3_summary.metrics.get("algorithm_stub") == "reset_stub_v1"
```

(Adjust L2 slug constant to `LAYER_02_EXTERIOR_TRANSPORT` from `layer_slugs`.)

- [ ] **Step 2: Django authority test**

```python
"""Django layer_03 package must not host algorithm modules."""

from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
_DJANGO_L3 = _REPO / "django_apps" / "asteroid_lab" / "layers" / "layer_03_rim_greedy_placement"

_FORBIDDEN = (
    "greedy_pass1.py",
    "greedy_pass2.py",
    "traversal_variants.py",
    "rim_anchors.py",
    "append.py",
)


def test_no_django_l3_algorithm_modules_on_disk() -> None:
    names = {p.name for p in _DJANGO_L3.iterdir() if p.is_file()}
    assert names <= {"__init__.py", "run.py"}
    for forbidden in _FORBIDDEN:
        assert forbidden not in names


def test_django_run_reexports_core_entrypoint() -> None:
    import django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.run as django_run
    import shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run as core_run

    assert django_run.run_layer_03_rim_greedy_placement is core_run.run_layer_03_rim_greedy_placement
```

- [ ] **Step 3: Run new tests**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_stack_runner_accepts_empty_l3.py tests/unit/asteroid_lab/layers/test_no_django_l3_algorithm_authority.py -v
```

- [ ] **Step 4: Commit**

```bash
git add tests/unit/asteroid_lab/layers/test_stack_runner_accepts_empty_l3.py tests/unit/asteroid_lab/layers/test_no_django_l3_algorithm_authority.py
git commit -m "test(asteroid-lab): stack and django authority for L3 reset stub"
```

---

## Task 11: Supersede PR-B plan + update `current_plan`

**Files:**
- Modify: `docs/superpowers/plans/2026-05-30-layer-03-boundary-m-repack-greedy/README.md`
- Modify: `documents/ai/current_plan.md` (if not already)
- Modify: `docs/superpowers/plans/2026-05-31-layer-03-algorithm-reset/checklist.md`

- [ ] **Step 1: Mark PR-B plan README `SUPERSEDED`**

```markdown
**Status:** SUPERSEDED — see [`../2026-05-31-layer-03-algorithm-reset/`](../2026-05-31-layer-03-algorithm-reset/README.md)
```

- [ ] **Step 2: Tick checklist items in `checklist.md`**

- [ ] **Step 3: Commit docs**

```bash
git add docs/superpowers/plans/ documents/ai/current_plan.md
git commit -m "docs(asteroid-lab): supersede PR-B plan; track L3 reset implementation"
```

---

## Task 12: Full verification gate

- [ ] **Step 1: Acceptance tests (spec A1–A7)**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_reset_stub_contract.py -v
python -m pytest tests/unit/asteroid_lab/layers/test_stack_runner_accepts_empty_l3.py -v
python -m pytest tests/unit/asteroid_lab/layers/test_no_django_l3_algorithm_authority.py -v
python -m pytest tests/unit/asteroid_lab/layers/ -v
python -m pytest tests/unit/asteroid_lab/replay/test_layer03_exterior_connector_overlay_persistence.py -v
test -f src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py
python -m ruff check src/shapez2_factory/application/asteroid_lab/layers/ django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/ tests/unit/asteroid_lab/layers/test_layer_03_reset_stub_contract.py tests/unit/asteroid_lab/layers/test_stack_runner_accepts_empty_l3.py tests/unit/asteroid_lab/layers/test_no_django_l3_algorithm_authority.py
```

- [ ] **Step 2: Record pass/fail in `checklist.md`**

---

## Plan self-review (spec coverage)

| Spec | Task |
|------|------|
| R1 S1–S7 | Tasks 3–4, 6 |
| R2 enum | Task 1 |
| R3 hard_fail | Tasks 2–3, 9 |
| R4 replay | Task 7 |
| R5 preserved stack | Task 10 |
| R6 deletion | Task 5 |
| R7 route_probe RETAIN | Task 0, 12 |
| Test classification | Task 0, 8 |
| Docs SUPERSEDED | Task 11 |
| A1–A7 | Task 12 |

No TBD placeholders in task steps.

---

## Execution handoff

**Plan saved to** `docs/superpowers/plans/2026-05-31-layer-03-algorithm-reset/README.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — run tasks in this session with checkpoints (`executing-plans`)

Which approach do you want?
