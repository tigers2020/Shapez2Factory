# Refactor Execution Order

## Phase 0 — Freeze the Truth Surface

### Goal

Formalize that canonical docs and live `asteroid_lab` are not the same system.

### Work

| Order | Scope | Why now | Touch policy |
|---|---|---|---|
| 0.1 | document canonical/live mapping | prevent wrong refactoring | `freeze` |
| 0.2 | decide whether `asteroid_lab` is inspection/replay shell or solver runtime | basis for all subsequent naming/model cleanup | `freeze` |
| 0.3 | confirm dangerous orchestrator list | understand blast radius before large file splits | `freeze` |

## Phase 1 — Separate Replay Output from Runtime Calculation

### Targets

- `django_apps/asteroid_lab/replay/snapshot_map_replay.py`
- `django_apps/asteroid_lab/services/cell_snapshot_service.py`
- `django_apps/asteroid_lab/services/existing_layout_service.py`

### Purpose

Remove `run_reconstruction(...)` calls and phase synthesis from replay layer; shrink to projection-only adapter.

### Rationale

Without decoupling this first, subsequent DTO split, UI contract cleanup, and validation migration will all distort.

## Phase 2 — Break Orchestration Monolith

### Targets

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `django_apps/web/views/public_pages.py`

### Purpose

Separate decode / normalize / persist / run scaffolding / replay build / retry policy.

### Caution

- keep `"force=True"` string branch as temporary adapter only until replaced with typed result.
- prevent web view from directly interpreting rebuild policy.

## Phase 3 — Split DTO and Serializer Seams

### Targets

- `django_apps/asteroid_lab/services/dto.py`
- `django_apps/web/services/asteroid_lab_page_context.py`

### Purpose

Clean up DTO monolith and UI serializer fallback rules; consolidate contract authority in one place.

## Phase 4 — Deprecate Shadow Solver Models

### Targets

- `CandidateBundle`, `RoutingProbe`, `SolverMetricSnapshot` in `django_apps/asteroid_lab/models.py`
- `PatternTemplate`, `PatternVariant` if needed

### Purpose

Isolate speculative schema existing without actual solver runtime.

### Conditions

- write admin/tests/live usage inventory first
- prefer `deprecate` label and migration note over immediate deletion

## Phase 5 — Define Missing Canonical Systems Explicitly

### Targets

- validation
- recovery
- protected corridor
- cycle streaming replay

### Purpose

Mark canonical systems absent from current tree as “not implemented”; do not force them into `asteroid_lab` inspection layer.

## Phase 6 — Strengthen Structural Tests

### Tests to add

| Test | Purpose |
|---|---|
| import graph allowed-edge test | fix layer direction |
| no-SCC test | early hidden cycle detection |
| replay no-runtime-import test | fix output-only rule |
| canonical/live inventory test | early namespace drift detection |
| serializer contract test | block UI fallback drift |

## Early No-Touch List

- `django_apps/asteroid_lab/reconstruction/pipeline.py`
- `django_apps/asteroid_lab/reconstruction/fill.py`
- `django_apps/asteroid_lab/snapshots/transport_components.py`
- `django_apps/asteroid_lab/snapshots/server_coords.py`
- `tests/unit/asteroid_lab/test_reconstruction_topology.py`

## Final Outcome Definition

“Stabilization” per this audit means:

1. canonical/live mapping is documented.
2. replay/output does not call runtime calculation.
3. orchestration is split into step-wise services.
4. unused shadow models are deprecate or isolate state.
5. validation/recovery/protected corridor boundary is clear: absent vs implemented.
