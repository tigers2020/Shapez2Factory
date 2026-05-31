# PR-CLI-2d — L2 + shared + contracts Move (NO stack_runner)

**Type:** refactoring (relocation)
**Depends on:** PR-CLI-2b, PR-CLI-2c
**Enables:** PR-CLI-2e
**L3 gate:** L3 NOT touched; **stack_runner NOT moved** (BA-1 purity preserved)
**Branch (suggested):** `feat/asteroid-cli-first-l2-move`

> File renamed from `pr-cli-2d-l2-stack-runner-move.md` (2026-05-30, 2nd review) — the name implied a
> stack_runner move that this PR explicitly does **not** do.

---

## Goal

Move only the dependency-light layer pieces — `layers/contracts`, `layers/layer_01_reconstruction`
facade, `layers/layer_02_exterior_transport`, and `layers/shared` — into core. **`stack_runner` stays in
`django_apps` for now**, because it transitively needs L3–L6, which are not yet moved. Moving stack_runner
here would force a `django_apps` bridge and break BA-1.

> **Structural amendment (2026-05-30):** Previous draft moved `stack_runner` + an `_l3_l6_bridge` shim.
> That violated BA-1 (`src/shapez2_factory/** must not import django_apps`). The bridge is removed from
> scope. `stack_runner` moves in PR-CLI-2e **together with** L3–L6, leaving no bridge behind.

## Behavior contract

- L2 capacity uses injected `GameDataRulesPort` (from 2b).
- Core `plan.py`/`run.py` make `rules: GameDataRulesPort` **required** (no ORM import). The django `plan.py`/`run.py` shims expose the original public signature with `rules: GameDataRulesPort | None = None` and inject `build_orm_game_data_rules()` when `None`, then delegate to core. This is an **intentional, non-breaking** extension of `execute_`/`run_` (originals had no `rules`); existing shim callers can still call without `rules`. The django `run.py` shim preserves the original stub-hold early-return (None when inputs missing) **before** building ORM rules. The former `solver_runtime_layer02` caller was removed by PR-CLI-6.
- Moved modules are core-pure (no `django`, no `django_apps`).
- `stack_runner` (still in `django_apps`) imports moved L1/L2 via their core path; L3–L6 from current location — this is allowed because stack_runner is still a `django_apps` module.
- **Shim identity preserved:** `django_apps` shim re-exports must be the *same object* as the core symbol (no copy/redefine).

## Non-goals

- **No `stack_runner` move.**
- **No `_l3_l6_bridge` creation** (forbidden — would break BA-1).
- No L3 algorithm change.
- No CLI.

---

## Move set

| From | To |
|------|-----|
| [`layers/contracts/*.py`](../../../../django_apps/asteroid_lab/layers/contracts/) **except `rim_placement.py`, `layer04_disabled.py`** | `application/asteroid_lab/layers/contracts/*.py` |
| `genetic_sample/enums.py` (`Direction`; prereq for `candidates`) | `domain/asteroid_lab/genetic_sample/enums.py` |
| `layer_01_reconstruction/output.py` **only** | `application/asteroid_lab/layers/layer_01_reconstruction/output.py` |
| `layers/layer_02_exterior_transport/` (all submodules) | `application/asteroid_lab/layers/layer_02_exterior_transport/` |
| [`layers/shared/route_probe.py`](../../../../django_apps/asteroid_lab/layers/shared/route_probe.py) + `shared/ceildiv.py` + `shared/equivalence_key.py` | `application/asteroid_lab/layers/shared/*.py` |
| pure part of [`layers/observability/`](../../../../django_apps/asteroid_lab/layers/observability/) (`layer_behavior_catalog` + 6 `build_layerNN_*_metrics`) | `application/asteroid_lab/layers/observability/` |

**Actual-scope deviations (recorded post-implementation, commit 35fb0030):**
- `contracts/rim_placement.py` + `contracts/layer04_disabled.py` import `services.dto.ReplayFrameAppendDTO` → **deferred to PR-CLI-2e** (cannot be core-pure yet).
- `genetic_sample/enums.py` moved as a **prerequisite** (`candidates` needs `Direction`; pure `StrEnum`).
- Layer-01: only `output.py` moved. `run.py`/`__init__.py` stay Django (import `services.reconstruction_capacity_summary` → `game_data` ORM).
- Observability: `build_layer04_post_summary_metrics` (uses `contracts.rim_placement`) stays Django with the settings session.

**Stays in `django_apps` (this PR):** `stack_runner.py`, `layer_03..layer_06`,
`contracts/{rim_placement,layer04_disabled}.py`, `layer_01_reconstruction/{run,__init__}.py`,
`observability/layer_post_summary_log.py` (uses `django.conf.settings` + `django.utils.timezone`; retains `build_layer04`).

## layer_post_summary_log handling

`layer_post_summary_log.py` uses Django settings/timezone. **Do not move it here.** Instead:

- Move the **pure metric builders** (`build_layerNN_post_summary_metrics`) into core observability.
- Keep the **log session / settings-driven emit** in `django_apps` (consumes core builders).

This keeps the move purely additive and avoids a settings dependency in core.

---

## BLOCKING — shim identity test (architect-required, 2026-05-30)

Relocating a contract + leaving a `django_apps` shim risks enum/dataclass **identity drift** (two distinct
classes with the same name → `isinstance` / `is` failures across the boundary). Add a test asserting the
shim re-export is the **same object** as the core symbol.

```python
# tests/unit/architecture/test_contract_shim_identity.py
import pytest

@pytest.mark.parametrize("old_path, new_path, name", [
    ("django_apps.asteroid_lab.layers.contracts.transport_kind",
     "shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind", "TransportKind"),
    ("django_apps.asteroid_lab.layers.contracts.transport_kind",
     "shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind", "ResourceKind"),
    ("django_apps.asteroid_lab.layers.contracts.placement_state",
     "shapez2_factory.application.asteroid_lab.layers.contracts.placement_state", "PlacementCommitState"),
    ("django_apps.asteroid_lab.layers.contracts.stack_status",
     "shapez2_factory.application.asteroid_lab.layers.contracts.stack_status", "StackRunStatus"),
    ("django_apps.asteroid_lab.layers.contracts.layer_budget",
     "shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget", "LayerBudgetContext"),
    ("django_apps.asteroid_lab.layers.contracts.provisional_overlay",
     "shapez2_factory.application.asteroid_lab.layers.contracts.provisional_overlay", "ProvisionalLayoutOverlay"),
])
def test_contract_shims_preserve_identity(old_path, new_path, name):
    import importlib
    old = getattr(importlib.import_module(old_path), name)
    new = getattr(importlib.import_module(new_path), name)
    assert old is new, f"{name}: shim re-export must be the same object as core"
```

**Coverage:** `TransportKind`, `ResourceKind`, `PlacementCommitState`, `StackRunStatus`,
`LayerBudgetContext`, `ProvisionalLayoutOverlay` (extend as more contracts move).

---

## Tasks

- [x] **Step 1:** Move contracts (+ `genetic_sample.enums` prereq); rewrite intra-core imports; shim originals (explicit `from core import X` re-export, not redefinition). Deferred: `rim_placement`, `layer04_disabled`.
- [x] **Step 2:** Move L1 `output.py` + L2 + shared (route_probe, ceildiv, equivalence_key); wire L2 `GameDataRulesPort` (`rules`-required core + ORM default in django `plan`/`run` shim); shim originals.
- [x] **Step 3:** Split observability: 6 pure metric builders + `layer_behavior_catalog` → core; settings emit + `build_layer04` stay Django.
- [x] **Step 4 (TDD):** Added `tests/unit/architecture/test_contract_shim_identity.py`; 15 parametrized symbols `is`-identical.
- [x] **Step 5:** `stack_runner` (still Django) imports moved L1/L2 via core path (through shims), L3–L6 via current path — runs unchanged (719 passed).
- [x] **Step 6:** Purity gate green with **zero `django_apps` exceptions** (no bridge). Added `src/shapez2_factory/py.typed` (PEP 561) so django↔core imports are type-checked, not `import-untyped`.
- [x] **Step 7:** Layer + budget + reconstruction gates green; ruff clean; `mypy src` clean (83 files).

## Tests / verification

```powershell
python -m pytest tests/unit/architecture/test_contract_shim_identity.py -v
python -m pytest tests/unit/asteroid_lab/layers/ -v
python -m pytest tests/unit/shapez2_factory/ tests/unit/architecture/test_shapez2_factory_core_purity.py -v
python -m mypy src   # required gate (strict, files=["src"]); full `mypy django_apps config src` has pre-existing baseline errors
```

## Risks

- `invariant:` single `route_domain` owner — do not duplicate during move.
- `invariant:` EVTC caps via resolver/port, never literals.
- Identity drift if shim redefines instead of re-exporting — guarded by shim identity test.
- If a moved L2 module transitively imports L3+, it is **not** ready to move — defer that submodule to 2e.
- Purity gate must have **no** allowlist exception after this PR.

## Done criteria

- contracts + L1 + L2 + shared in core, fully pure; shim identity test green; stack_runner still Django and green; no bridge; layer tests pass.
