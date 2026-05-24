# Decontamination PR-B — Optimization Contamination Gates (Design)

**Status:** CLOSED (implemented 2026-05-24 on `feat/decontamination-pr-b-optimization-gates`; merge SHA pending)  
**Date:** 2026-05-24  
**Owner:** Release / Solver Architecture Lead  
**Track:** Decontamination PR-B (Axis: repo health; not Axis A/B algorithm feature)  
**Parent:** [`2026-05-24-repo-decontamination-authority-design.md`](2026-05-24-repo-decontamination-authority-design.md) §9  
**Implementation plan:** [`../plans/2026-05-24-decontamination-pr-b-optimization-gates.md`](../plans/2026-05-24-decontamination-pr-b-optimization-gates.md)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)

**Related:**

- [`documents/ai/contamination_policy.md`](../../../documents/ai/contamination_policy.md) — PR playbook PR-B
- [`2026-05-24-b-cs3-validation-gate-audit-design.md`](2026-05-24-b-cs3-validation-gate-audit-design.md) — validation behaviour audit (out of scope)
- [`2026-05-24-b-cs4-reconstruction-replay-boundary-design.md`](2026-05-24-b-cs4-reconstruction-replay-boundary-design.md) — reconstruction/replay behaviour audit (out of scope)
- [`2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md)

---

## Problem

Axis A (catalog) and Axis B formal milestones (B-CS1–B-CS4) are CLOSED on `master`, but **optimization import canon** is only partially enforced:

| Gap | Risk |
|-----|------|
| Substring-only milestone test (`test_optimization_milestone_import_boundary.py`) | False negatives on structured imports; duplicates future AST gates |
| No consolidated forbidden-prefix allowlist | Replay adapters, monolith paths, or `lab_rttp_snapshot_compose` can re-enter `optimization/` |
| No decision-path token gate for `solver_summary` / NDJSON / replay ORM reads | Output artifacts become algorithm inputs (contamination case F) |
| PR-C replay/validation gates split across B-CS3/4 | PR-B must **not** re-audit behaviour; it must **lock import boundaries** |

---

## Goal

```text
PR-B = Optimization import canon + decision-path contamination gate (AST/static only)
```

**No solver behaviour change.** Production code changes are allowed only when required to remove forbidden imports without changing runtime semantics. The default delivery is **tests + docs only**.

---

## Non-goals

- Reopen or extend B-CS3/B-CS4 behavioural audits
- Duplicate `test_catalog_consumption_boundaries.py` symbol rules
- Raw/server coord rules (`test_coordinate_boundary.py`)
- Cross-package private helper imports (`_rotation_matrix` — PR-B v2)
- PR-D quarantine moves, PR-E dead-code deletion
- Deferred commit retry, Track D+ PR-4, macro RTTP (PAUSE)

---

## §1 — Entry Gate A (Post-merge verification)

**Precondition:** Branch `test/b-cs3-validation-gate-audit` (or equivalent) merged into `master`.

### Steps

1. `git checkout master && git pull`
2. **Gate 1 (blocking):** `powershell -File scripts/test_reconstruction_narrow.ps1`
3. **Gate 2 (blocking):** `python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map"`
4. **Gate 3 (recommended, non-blocking):** `python manage.py run_solver --slug copy-import-495e552c`
5. **Gate 4 (docs):** `current_plan.md` + roadmap reflect B-CS3/B-CS4 CLOSED, Axis B complete, PR-B as next ACTIVE work

### PR-B start conditions

```text
PR-B may start only after Gate 1 and Gate 2 are green on master.

Gate 3 is recommended ops smoke, but non-blocking when failure is attributable to
local DB, missing slug, environment drift, or fixture availability.

Gate 4 must be resolved before PR-B is marked ACTIVE/CLOSED in roadmap docs.
```

### Failure handling

```text
Gate 1/2 failure after merge: open maintenance regression track.
Do not reopen B-CS3/B-CS4 merely because a later regression appears.
Reopen B-CS3/B-CS4 only if failure proves the original closure evidence was invalid.

Gate 3-only failure: classify ops/env vs solver regression; do not block PR-B on env alone.
Gate 4-only failure: fix docs before PR-B status transition.
```

---

## §2 — PR-B scope (optimization contamination gate)

### 2.1 Scanned package root

```text
django_apps/asteroid_lab/optimization/**/*.py
```

Include all `*.py` under the tree. Exclude `tests/`, `management/`, `migrations/`.

Scan mechanism: per-file `ast.parse` for import and decision-token rules below.

---

### 2.2 Forbidden import prefixes

Default rule: any `Import` / `ImportFrom` target module string matching a forbidden rule fails unless the file is on the **explicit allowlist** (§2.4).

| Rule | Module string criterion |
|------|-------------------------|
| Removed namespace | starts with `django_apps.shapez_asteroid` or `shapez_asteroid` |
| Replay package | starts with `django_apps.asteroid_lab.replay` |
| Lab replay read adapters | equals or starts with listed `services.lab_*` replay payload modules (see §2.3B needles) |
| Lab RTTP compose | `django_apps.asteroid_lab.services.lab_rttp_snapshot_compose` |
| Monolith pipeline | any imported module name **containing** `solver_runtime_pipeline` |
| Legacy segment | any dot-separated **import module segment** equal to `legacy` (not free-text substring) |
| Pass-first | module name contains `pass_first` |
| Genetic sample | starts with `django_apps.asteroid_lab.genetic_sample` |

**`legacy` clarification:**

```text
"legacy" is forbidden only as an import module segment, not as a free-text substring.
```

**`solver_runtime_pipeline` clarification:**

```text
Any imported module name containing "solver_runtime_pipeline" is forbidden.
```

(File path substrings are not used.)

**Reconstruction imports:**

- `django_apps.asteroid_lab.reconstruction.*` allowed **only** in:
  - `reconstruction_adapter.py`
  - `rttp_solver_summary.py`

**Services imports:**

- `django_apps.asteroid_lab.services.*` allowed **only** in:
  - `reconstruction_adapter.py`
  - `pipeline.py`
  - `replay_sink.py`

**Adapters imports:**

- Only modules matching `django_apps.asteroid_lab.adapters.catalog_*` are allowed.
- Any other `django_apps.asteroid_lab.adapters.*` import is forbidden.

**Replay package exception (allowlisted files only):**

- `pipeline.py` and `rttp_solver_summary.py` may import `django_apps.asteroid_lab.replay` (typically `event_types`).

---

### 2.3 Forbidden symbols / decision-use tokens

#### 2.3A Geometry symbols (covered-by, not duplicated)

`BuildingFootprintCell`, `BuildingConnectorSnapshot`, `BuildingSnapshot` imports from `game_data_snapshot` remain owned by:

`tests/unit/architecture/test_catalog_consumption_boundaries.py`

PR-B must not duplicate those assertions.

#### 2.3B Service adapter needles (absorbed from milestone test)

Forbidden as **import module strings** (same as milestone substring targets, but evaluated via AST `ImportFrom.module` / alias resolution):

```text
lab_optimization_milestone_payload
lab_unified_replay_append
lab_replay_timeline_payload
```

#### 2.3C Decision-path token gate (AST-only)

**Scanned subtrees** (relative to `optimization/`):

```text
commit/
selection/
routing/
candidates/
validation/
macros/
skeleton/
```

**Excluded files** (writers / orchestration / I/O boundary — no token scan):

```text
pipeline.py
rttp_solver_summary.py
rttp_replay_diagnostics.py
replay_sink.py
replay_track_keys.py
reconstruction_adapter.py
input_contracts.py
coords.py
```

**Forbidden identifiers** (match on AST nodes, not raw file text):

```text
solver_summary
ndjson
ReplayFrame
lab_replay_timeline
```

**AST node kinds to inspect:**

```text
- Import / ImportFrom module and imported symbol names
- ast.Name
- ast.Attribute (attr id)
- ast.Constant string literals (when isinstance(value, str))
```

**Exclusions:**

- Module docstrings via `ast.get_docstring(tree)` — excluded from literal scan
- Comments — not in AST; naturally excluded
- Free-text substring scan of entire file is **forbidden** (avoids comment/docstring false positives)

**Allowed in excluded writer modules:**

- `build_rttp_solver_summary`, `RttpAlgorithmStepId`, module `rttp_solver_summary`, etc.

---

### 2.4 Explicit allowlist (closed set)

| Relative path under `optimization/` | Extra import permissions |
|-------------------------------------|---------------------------|
| `reconstruction_adapter.py` | `reconstruction.*`, `adapters.catalog_transport_policy`, `services.dto` |
| `rttp_solver_summary.py` | `reconstruction.confidence`, `reconstruction.result`, `replay` (event_types), `adapters.catalog_footprint_policy` |
| `pipeline.py` | `replay` (event_types), `services.dto`, `adapters.catalog_placement_audit`, `adapters.catalog_placement_validation` |
| `replay_sink.py` | `services.replay_recorder`, `services.dto` |
| `candidates/candidate_generator.py` | `adapters.catalog_candidate_placements` |
| `validation/catalog_layout_validation.py` | `adapters.catalog_placement_validation`; `optimization.rttp_solver_summary.RttpAlgorithmStepId` |

**Always allowed (all files):**

- `django_apps.asteroid_lab.contracts.*`
- `django_apps.asteroid_lab.snapshots.grid_contract`, `coord_frames`
- Internal `django_apps.asteroid_lab.optimization.*`

**Closed-set enforcement (required test):**

```text
test_optimization_allowlist_files_are_closed_set
```

The test must fail if a new file under `optimization/` imports from `reconstruction`, `services`, `replay`, or non-`catalog_*` `adapters` but is not listed above.

---

### 2.5 Absorbed / deleted tests

| Action | Path |
|--------|------|
| **Create** | `tests/unit/architecture/test_optimization_contamination_gates.py` |
| **Delete** | `tests/unit/asteroid_lab/test_optimization_milestone_import_boundary.py` |
| **Keep** | `tests/unit/architecture/test_catalog_consumption_boundaries.py` |
| **Keep** | `test_b_cs3_validation_gate_boundary.py`, `test_b_cs4_*`, `test_validation_readonly_guards.py` |

---

### 2.6 Gate inclusion policy

| Gate | Includes PR-B? |
|------|----------------|
| `scripts/test_reconstruction_narrow.ps1` | **No** |
| RTTP narrow `-k "rttp and not macro_real_map"` | **No** |
| PR-B standing (new) | **Yes** |
| `scripts/test_full.ps1` | **Yes** (via `tests/unit/architecture/`) |

**Standing command** (`current_plan.md` § Maintenance):

```powershell
python -m pytest tests/unit/architecture/test_optimization_contamination_gates.py tests/unit/architecture/test_catalog_consumption_boundaries.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/optimization
```

Optional follow-up: `scripts/test_optimization_contamination.ps1` wrapper (plan may add if useful).

---

### 2.7 Out-of-scope / covered-by references

| Topic | Owner |
|-------|--------|
| Validation read-only, no repair | B-CS3, `test_validation_readonly_guards.py` |
| Persist vs replay ORM | B-CS4, `test_persistence_does_not_read_replay_frames.py` |
| Building geometry in optimization | `test_catalog_consumption_boundaries.py` |
| Raw/server coord | `test_coordinate_boundary.py`, `reconstruction_adapter.py` |
| Private cross-module imports | PR-B v2 (deferred) |
| Quarantine moves | PR-D |
| Dead code | PR-E |
| Deferred commit retry | [`2026-05-22-deferred-commit-retry-design.md`](2026-05-22-deferred-commit-retry-design.md) — after PR-B |
| Track D+ PR-4 | Not defined |
| Macro RTTP | PAUSE |

---

### 2.8 Closure definition

**PR-B is CLOSED when:**

1. Entry Gate A Gate 1–2 were green on `master` before PR-B merge (record date/SHA in `current_plan.md`)
2. `tests/unit/architecture/test_optimization_contamination_gates.py` green on `master`
3. `test_optimization_milestone_import_boundary.py` deleted (absorbed)
4. `current_plan.md` + roadmap list PR-B CLOSED with merge SHA
5. Standing command documented in §2.6

**Behaviour:**

```text
No solver behaviour change.
Production code changes are allowed only when required to remove forbidden imports
without changing runtime semantics.
```

Default delivery: tests + docs only (current tree is expected to pass without production edits).

---

## Self-review checklist (design)

- [x] PR-B does not duplicate B-CS3/B-CS4 behavioural audits — import canon only
- [x] PR-B does not duplicate catalog consumption geometry symbols — cross-ref §2.3A
- [x] Allowlist is a closed set — §2.4 + required test
- [x] Token gate uses AST nodes, not raw comment/docstring substring — §2.3C

---

## Rollback

Revert PR-B merge commit. No schema or runtime config changes expected.
