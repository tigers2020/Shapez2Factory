# Solver Runtime Wires Replay Projection — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist `solver_runtime_wires.v1.json` at CLI solve time and project overlays in Django compose without re-running L2–L5 (`algorithm_rerun_count == 0`).

**Architecture:** Core serializes finalized layer outputs to an artifact-relative wire file after stack execution. Django deserializes wires via `src/shapez2_factory/adapters/asteroid_lab/runtime_wires/`, calls `build_solver_runtime_replay_frames` (projection only), then existing timeline merge + enrichments. Legacy artifacts without wires degrade to terrain-only with `diagnostic_severity`.

**Tech Stack:** Python 3.14, Django 5/6, pytest, existing `solver_runtime_assembler.py`, `asteroid_solve.py` artifact writer.

**Design spec:** [`docs/superpowers/specs/2026-06-10-solver-runtime-wires-replay-projection-design.md`](../specs/2026-06-10-solver-runtime-wires-replay-projection-design.md)

---

## File map

| File | Responsibility |
|------|----------------|
| `src/shapez2_factory/adapters/asteroid_lab/runtime_wires/envelope.py` | Schema constants, outcome enum, validation errors |
| `src/shapez2_factory/adapters/asteroid_lab/runtime_wires/serialize.py` | Layer DTOs → wire JSON |
| `src/shapez2_factory/adapters/asteroid_lab/runtime_wires/deserialize.py` | Wire JSON → projection DTOs |
| `src/shapez2_factory/application/asteroid_lab/stack_runner.py` | Extend `CoreStackRunResult` with layer output handles |
| `src/shapez2_factory/application/asteroid_lab/run_stack.py` | Pass layer outputs to wire builder |
| `src/shapez2_factory/interfaces/cli/asteroid_solve.py` | Write `output/solver_runtime_wires.v1.json` + manifest path |
| `django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py` | Wire load, validate, project, degraded fallback |
| `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py` | Cache schema v3, stale wire detection |
| `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py` | Diagnostic reason + severity constants |
| `django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py` | **Delete** (SHA-64 residue) |
| `tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py` | Import + execution gates |
| `tests/unit/asteroid_lab/test_runtime_wire_serde.py` | Round-trip serde |
| `tests/unit/asteroid_lab/test_runtime_wire_projection_compose.py` | Compose projection + degraded |
| `tests/integration/web/test_lab_replay_runtime_wires.py` | HTTP lab-replay path |

---

## Slice 1 — Architecture gates + remove runtime recompose

### Task 1: Delete Django layer re-execution compose path

**Files:**
- Delete: `django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py`
- Modify: `django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py`
- Test: `tests/unit/asteroid_lab/test_artifact_replay_viewer_compose.py`

- [ ] **Step 1: Ensure viewer compose has no import of runtime recompose**

In `artifact_replay_viewer_compose.py`, `compose_lab_replay_frames_from_artifact_run` must only map `replay_core` + `complete_map` until Slice 4 wires projection lands. Remove any `build_solver_runtime_replay_frames_from_artifact_run` call.

- [ ] **Step 2: Delete `artifact_runtime_replay_compose.py`**

- [ ] **Step 3: Update tests**

Replace `test_compose_artifact_run_runtime_recompose_includes_l3_overlays` with `test_compose_artifact_run_maps_replay_core_without_solver_reexecution` asserting `replay_source == artifact_replay_core`.

Run: `python -m pytest tests/unit/asteroid_lab/test_artifact_replay_viewer_compose.py tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py -v`

- [ ] **Step 4: Commit**

```bash
git add django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py
git add tests/unit/asteroid_lab/test_artifact_replay_viewer_compose.py
git rm django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py
git commit -m "refactor(asteroid_lab): remove Django L2-L5 runtime recompose path (SHA-64)"
```

---

### Task 2: Architecture import gate

**Files:**
- Modify: `tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py`

- [ ] **Step 1: Add test**

```python
def test_artifact_compose_services_do_not_import_solver_execution_run_modules() -> None:
    root = Path(__file__).resolve().parents[3]
    services_dir = root / "django_apps" / "asteroid_lab" / "services"
    offenders: list[str] = []
    for path in sorted(services_dir.glob("artifact_*compose*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for module in _imported_modules(tree):
            if module.startswith(
                "shapez2_factory.application.asteroid_lab.layers.layer_"
            ) and module.endswith(".run"):
                offenders.append(f"{path.relative_to(root)}: import {module}")
    assert offenders == []
```

- [ ] **Step 2: Run and commit**

```bash
python -m pytest tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py -v
git add tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py
git commit -m "test(architecture): gate artifact compose against layer run imports"
```

---

### Task 3: Execution gate skeleton (fails until Slice 4)

**Files:**
- Create: `tests/unit/asteroid_lab/test_runtime_wire_projection_compose.py`

- [ ] **Step 1: Write failing execution gate test**

```python
"""algorithm_rerun_count == 0 on lab replay compose."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db

LAYER_RUN_PATCHES = [
    "shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.run.execute_layer_02_exterior_transport_plan",
    "shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run.run_layer_03_rim_greedy_placement",
    "shapez2_factory.application.asteroid_lab.layers.layer_04_inner_pattern_fill.run.run_layer_04_inner_pattern_fill",
    "shapez2_factory.application.asteroid_lab.layers.layer_05_transport_routing.run.run_layer_05_transport_routing",
]


def _raise_if_called(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("solver layer must not execute during replay compose")


@pytest.fixture
def block_layer_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    for target in LAYER_RUN_PATCHES:
        monkeypatch.setattr(target, _raise_if_called)


def test_compose_with_valid_wires_never_executes_layers(
    block_layer_execution: None,
    runtime_wire_artifact_fixture,  # defined in Slice 4
) -> None:
    from django_apps.asteroid_lab.services.artifact_replay_viewer_compose import (
        compose_lab_replay_frames_from_artifact_run,
    )

    run = runtime_wire_artifact_fixture
    frames = compose_lab_replay_frames_from_artifact_run(run)
    assert frames is not None
    l3_complete = next(
        f for f in frames if f.get("event_type") == "layer03_rim_greedy_complete"
    )
    overlay = (l3_complete.get("map_view") or {}).get("overlay_cells") or []
    assert overlay, "L3 complete must carry overlays from wire projection"
```

- [ ] **Step 2: Mark xfail or skip until Slice 4, commit skeleton**

```bash
git add tests/unit/asteroid_lab/test_runtime_wire_projection_compose.py
git commit -m "test(asteroid_lab): add execution gate skeleton for wire projection compose"
```

---

## Slice 2 — Core wire serde

### Task 4: Envelope + validation errors

**Files:**
- Create: `src/shapez2_factory/adapters/asteroid_lab/runtime_wires/envelope.py`
- Create: `src/shapez2_factory/adapters/asteroid_lab/runtime_wires/__init__.py`
- Test: `tests/unit/asteroid_lab/test_runtime_wire_serde.py`

- [ ] **Step 1: Write failing test for schema constant**

```python
from shapez2_factory.adapters.asteroid_lab.runtime_wires.envelope import (
    RUNTIME_WIRES_SCHEMA_VERSION,
    LayerOutcome,
)

def test_runtime_wire_schema_version() -> None:
    assert RUNTIME_WIRES_SCHEMA_VERSION == "solver_runtime_wires_v1"

def test_layer_outcome_values() -> None:
    assert set(LayerOutcome) == {
        LayerOutcome.COMPLETED,
        LayerOutcome.PARTIAL_BUDGET,
        LayerOutcome.SKIPPED,
        LayerOutcome.FAILED,
    }
```

- [ ] **Step 2: Implement envelope.py**

```python
from enum import StrEnum

RUNTIME_WIRES_SCHEMA_VERSION = "solver_runtime_wires_v1"
RUNTIME_WIRES_ARTIFACT_REL_PATH = "output/solver_runtime_wires.v1.json"
MANIFEST_PATH_KEY = "solver_runtime_wires"

class LayerOutcome(StrEnum):
    COMPLETED = "completed"
    PARTIAL_BUDGET = "partial_budget"
    SKIPPED = "skipped"
    FAILED = "failed"

class RuntimeWireValidationError(ValueError):
    code: str
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)
```

- [ ] **Step 3: Run tests, commit**

---

### Task 5: L2 wire serialize (reuse exterior plan v2)

**Files:**
- Modify: `src/shapez2_factory/adapters/asteroid_lab/runtime_wires/serialize.py`
- Test: `tests/unit/asteroid_lab/test_runtime_wire_serde.py`

- [ ] **Step 1: Failing round-trip test using minimal L2 plan fixture**

Use `exterior_connector_plan_to_metrics_dict` from core wire module; assert `layers.layer_02_exterior_transport.exterior_connector_plan.version == exterior_connector_plan.v2`.

- [ ] **Step 2: Implement `serialize_layer02_wire(plan, *, outcome) -> dict`**

- [ ] **Step 3: Run tests, commit**

---

### Task 6: L3 wire serialize with commit_index + projection_hints

**Files:**
- Modify: `serialize.py`, `deserialize.py`
- Test: `tests/unit/asteroid_lab/test_runtime_wire_serde.py`

- [ ] **Step 1: Failing test — placement round-trip preserves commit_index**

```python
def test_l3_wire_commit_index_order_enforced_on_deserialize() -> None:
    wire = {
        "committed_placements": [
            {"commit_index": 1, "placement_id": "b", ...},
            {"commit_index": 0, "placement_id": "a", ...},
        ]
    }
    with pytest.raises(RuntimeWireValidationError) as exc:
        deserialize_l3_wire(wire)
    assert exc.value.code == "runtime_wire_l3_order_invalid"
```

- [ ] **Step 2: Implement serialize/deserialize for `IntegratedRimGreedyResult`**

Map `route_probe_path` → `projection_hints.route_probe_path`.

- [ ] **Step 3: Run tests, commit**

---

### Task 7: L4 + L5 wire serde

**Files:**
- Modify: `serialize.py`, `deserialize.py`
- Test: `tests/unit/asteroid_lab/test_runtime_wire_serde.py`

- [ ] **Step 1: Failing L4 placements vs interior_occupied_cells consistency test**

- [ ] **Step 2: Implement L4/L5 serialize + deserialize**

L5 reuses existing `layer05_route_plan_v1` dict shape from `Layer05RoutePlan`.

- [ ] **Step 3: Run tests, commit**

---

### Task 8: Full envelope builder

**Files:**
- Modify: `serialize.py`
- Test: `tests/unit/asteroid_lab/test_runtime_wire_serde.py`

- [ ] **Step 1: Test `build_runtime_wires_envelope(...)` includes `projection_contract`, `complete_map_ref`, `transport_summary`**

- [ ] **Step 2: Implement `build_runtime_wires_document(...)` returning JSON-ready dict**

- [ ] **Step 3: Commit**

---

## Slice 3 — CLI write path

### Task 9: Expose layer outputs from stack runner

**Files:**
- Modify: `src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- Modify: `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- Test: `tests/unit/shapez2_factory/test_cli_run_artifact.py`

- [ ] **Step 1: Extend `CoreStackRunResult` dataclass**

```python
@dataclass(frozen=True, slots=True)
class CoreStackRunResult:
    stack_result: StackRunResult
    layer_summaries: tuple[LayerPostSummaryRecord, ...]
    exterior_plan: ExteriorConnectionPlan | None = None
    rim_greedy: IntegratedRimGreedyResult | None = None
    inner_fill: Layer04InnerFillResult | None = None
    route_plan: Layer05RoutePlan | None = None
```

Populate fields in `run_layers_02_to_06` return path (already tracked as locals).

- [ ] **Step 2: Failing test — successful CLI artifact includes wires file in manifest**

- [ ] **Step 3: Implement, run tests, commit**

---

### Task 10: Write wire in `asteroid_solve._run_artifact`

**Files:**
- Modify: `src/shapez2_factory/interfaces/cli/asteroid_solve.py`
- Test: `tests/unit/shapez2_factory/test_cli_run_artifact.py`

- [ ] **Step 1: Failing test asserts manifest.paths contains `solver_runtime_wires` and file exists post-run**

- [ ] **Step 2: After stack success and before manifest finalize:**

```python
wires_doc = build_runtime_wires_document(
    run_key=run_key,
    complete_map_hash=...,
    exterior_plan=core_result.exterior_plan,
    rim_greedy=core_result.rim_greedy,
    inner_fill=core_result.inner_fill,
    route_plan=core_result.route_plan,
    transport_summary=...,
)
writer.write_output("output/solver_runtime_wires.v1.json", _json_bytes(wires_doc))
manifest_paths["solver_runtime_wires"] = "output/solver_runtime_wires.v1.json"
```

**Normative:** Write only after layer outputs finalized; do not write wires if stack failed before L2 outputs exist.

- [ ] **Step 3: Run `pytest tests/unit/shapez2_factory/test_cli_run_artifact.py -v`, commit**

---

## Slice 4 — Django projection compose

### Task 11: Wire load + validation in viewer compose

**Files:**
- Modify: `django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py`
- Create: `django_apps/asteroid_lab/services/runtime_wire_compose.py` (optional split if compose file grows)
- Test: `tests/unit/asteroid_lab/test_runtime_wire_projection_compose.py`

- [ ] **Step 1: Add `load_and_validate_runtime_wires(root, manifest) -> RuntimeWireLoadResult`**

Returns: `ok | degraded_reason | severity | document`.

Validate: schema_version, complete_map_ref hash, L3 order, L4 consistency.

- [ ] **Step 2: Failing tests for each diagnostic_reason in design §5.3**

- [ ] **Step 3: Implement, commit**

---

### Task 12: Project wires via assembler

**Files:**
- Modify: `artifact_replay_viewer_compose.py` or `runtime_wire_compose.py`
- Test: `tests/unit/asteroid_lab/test_runtime_wire_projection_compose.py`

- [ ] **Step 1: Implement `compose_lab_replay_frames_from_runtime_wires(run, wires_doc, complete_map)`**

```python
frames = build_solver_runtime_replay_frames(
    complete_map=complete_map,
    lab_frames_before_append=lab_source,
    exterior_plan_wire=plan_wire,
    layer03=rim_greedy,
    layer04_inner_fill=inner_fill,
    layer05_route_plan=route_plan,
    transport_kind=...,
)
for frame in frames:
    inspector = frame.setdefault("inspector", {})
    inspector["replay_source"] = "artifact_runtime_wire_projection"
    inspector["wire_schema_version"] = RUNTIME_WIRES_SCHEMA_VERSION
```

- [ ] **Step 2: Wire into `compose_lab_replay_frames_from_artifact_run` priority:**

```text
1. valid runtime wires → project
2. else degraded fallback (§5.3 priority)
```

- [ ] **Step 3: Enable execution gate test (remove skip), run full unit suite, commit**

---

### Task 13: Partial budget per-layer projection

**Files:**
- Modify: `runtime_wire_compose.py`
- Test: `tests/unit/asteroid_lab/test_runtime_wire_projection_compose.py`

- [ ] **Step 1: Tests for L3/L4/L5 `partial_budget` — partial overlays + `diagnostic_severity: warning`**

- [ ] **Step 2: Implement layer-truncation in projector (stop at first failed/skipped; partial_budget continues with available wire)**

- [ ] **Step 3: Commit**

---

## Slice 5 — Degraded, cache, diagnostics

### Task 14: Diagnostic severity in timeline payload

**Files:**
- Modify: `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py`
- Modify: `django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py`

- [ ] **Step 1: Add constants**

```python
DIAGNOSTIC_MISSING_RUNTIME_WIRES = "missing_runtime_wires"
DIAGNOSTIC_RUNTIME_WIRE_SCHEMA_UNKNOWN = "runtime_wire_schema_unknown"
# ... per design §5.3

DIAGNOSTIC_SEVERITY_BY_REASON: dict[str, str] = {
    DIAGNOSTIC_MISSING_RUNTIME_WIRES: "warning",
    DIAGNOSTIC_RUNTIME_WIRE_SCHEMA_UNKNOWN: "error",
    # ...
}
```

- [ ] **Step 2: Set `replay_track_metrics.diagnostic_severity` alongside `diagnostic_reason`**

- [ ] **Step 3: Commit**

---

### Task 15: Degraded fallback priority

**Files:**
- Modify: `artifact_replay_viewer_compose.py`

- [ ] **Step 1: Implement `_compose_degraded_terrain_frames(complete_map, replay_core_optional)`**

Priority:
1. complete_map + replay_core markers if readable
2. complete_map-only single terrain frame
3. return None only if complete_map unreadable

- [ ] **Step 2: Unit tests for missing replay_core, corrupt replay_core, missing wires**

- [ ] **Step 3: Commit**

---

### Task 16: Cache schema v3 + stale detection

**Files:**
- Modify: `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`
- Test: `tests/unit/asteroid_lab/test_solver_run_fast_cache.py`

- [ ] **Step 1: Bump `CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION` to 3**

Add fields: `wire_schema_version`, `wire_content_hash`, `replay_projection_mode`.

- [ ] **Step 2: Extend `_is_stale_thin_artifact_l3_cache` → `_is_stale_composed_replay_cache`**

Stale if:
- old `artifact_replay_core` thin L3
- wires exist but cache `replay_source != artifact_runtime_wire_projection`
- cached `wire_schema_version` != artifact wire schema (cache miss → re-project if supported)

- [ ] **Step 3: Tests + commit**

---

## Slice 6 — Integration + verification

### Task 17: HTTP lab-replay integration test

**Files:**
- Create: `tests/integration/web/test_lab_replay_runtime_wires.py`

- [ ] **Step 1: Test first lab-replay GET on run with wires — overlay present, diagnostic none**

- [ ] **Step 2: Test legacy artifact without wires — 200 terrain-only, `missing_runtime_wires` warning**

- [ ] **Step 3: Test second GET cache hit — faster (optional timing assert loose)**

Run: `python -m pytest tests/integration/web/test_lab_replay_runtime_wires.py -v`

- [ ] **Step 4: Commit**

---

### Task 18: Manual verification checklist

- [ ] Run solver on `copy-import-*` project via UI
- [ ] Confirm artifact contains `output/solver_runtime_wires.v1.json`
- [ ] First `lab-replay/` < 5s, miners visible mid-timeline, belts on final frame
- [ ] Server log: no multi-second L3 spans; `algorithm_rerun_count == 0` in perf trace if enabled
- [ ] Legacy run without wires still loads terrain with diagnostic HUD

---

## Plan self-review (vs spec)

| Spec requirement | Task |
|------------------|------|
| artifact-relative wire path | Task 10 |
| algorithm_rerun_count == 0 | Tasks 3, 12 |
| valid wires full projection | Tasks 11–12 |
| degraded priority | Task 15 |
| partial_budget per layer | Task 13 |
| diagnostic_severity | Task 14 |
| stale cache re-project only | Task 16 |
| wire write after finalize | Task 10 |
| import + execution gates | Tasks 2–3 |

No TBD placeholders in task code blocks above.

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-06-10-solver-runtime-wires-replay-projection.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per slice, review between slices  
2. **Inline Execution** — execute in this session with executing-plans checkpoints

Which approach?
