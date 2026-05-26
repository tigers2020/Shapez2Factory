# Reconstruction Capacity C-GATE — Design Spec

**Date:** 2026-05-29  
**Status:** CLOSED (merged to `master` `ec1b6a26`, PR #94, 2026-05-29)  
**Owner:** asteroid-lab / reconstruction SoT governance  
**Track:** v0.1 next track — **Capacity C-GATE** (Approach 2: gates + contract hardening)  
**Parent SoT:** [`2026-05-26-reconstruction-complete-map-dto-design.md`](2026-05-26-reconstruction-complete-map-dto-design.md)  
**Implementation plan:** `docs/superpowers/plans/2026-05-29-reconstruction-capacity-c-gate.md` (created after spec review via writing-plans)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)

**Related (closed / reference only):**

- [`2026-05-24-decontamination-pr-b-optimization-gates-design.md`](2026-05-24-decontamination-pr-b-optimization-gates-design.md) — AST gate pattern
- [`2026-05-24-b-cs4-reconstruction-replay-boundary-design.md`](2026-05-24-b-cs4-reconstruction-replay-boundary-design.md) — replay boundary (out of scope)
- [`2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md) — GA deferred until C-GATE CLOSED

**Supersedes as executable authority:**

- [`2026-05-25-reconstruction-field-cell-capacity-contract.md`](../plans/2026-05-25-reconstruction-field-cell-capacity-contract.md) — **OBSOLETE / DO NOT EXECUTE** (tombstone only)

---

## §1 — Purpose and scope

### Problem

`ReconstructionCompleteMap` and `build_reconstruction_complete_map` are implemented on `master`, and production solver paths already thread `complete_map` into capacity, topology, and `OptimizationInput`. However:

| Gap | Risk |
|-----|------|
| Overlay-only APIs remain importable from optimization | `mineable_coords_from_reconstruction` / `acceptance_topology_from_reconstruction` can re-enter decision paths |
| Ambiguous observability keys (`cell_count`) | Lab operators and future GA fitness work may treat overlay size as terrain SoT |
| No standing architecture gate for capacity SoT | Regression reintroduces `recon.cells` counting (32 vs hundreds field-cell drift) |
| Complete-map DTO plan checklist not closed as **governance** | Implementation exists; **enforcement** does not |

### Goal

```text
C-GATE = Architecture gates + observability vocabulary contract
         that lock ReconstructionCompleteMap as the sole terrain SoT
         for capacity, mineable, and OptimizationInput — without changing solver semantics.
```

### In scope (PR-CGATE-1 default)

- New spec (this document) and implementation plan
- `tests/unit/architecture/test_capacity_complete_map_sot_gates.py` (G1, G2)
- Regression extensions (G3) on existing `test_complete_map.py` / capacity / optimization-input tests
- Lab summary contract test (G4)
- Standing script `scripts/test_capacity_sot.ps1` (G5)
- `documents/ai/current_plan.md` ACTIVE row + one-line roadmap pointer

### Out of scope

- Full GA / genome evolution promotion
- Macro unpause / macro child-pool fixture
- PR-1b route tile synthesis / PR-2 island materializer (Lab UX defer)
- `ReconstructionResult.cells` → `overlay_cells` rename (follow-up PR)
- Deleting `acceptance_topology_from_reconstruction` (follow-up after confidence migration)
- Solver commit order, validation repair, FOT, catalog, deferred retry behaviour changes

### Non-goals (normative)

| Item | Rationale |
|------|-----------|
| Re-implement complete-map factory | Already on `master`; C-GATE enforces, not rebuilds |
| Blanket `recon.cells` ban in repo | Breaks replay merge and diagnostic writers |
| Coincidental equality tests | e.g. `cell_count == platform_count` fails on sparse fixtures by accident |

---

## §2 — Complete-map SoT contract

**Single factory (unchanged from 2026-05-26 spec):**

```python
build_reconstruction_complete_map(cleanup=..., recon=...) -> ReconstructionCompleteMap
```

**Terrain SoT consumers (must use `complete_map` only):**

| Consumer | Field / API |
|----------|-------------|
| Capacity envelope | `build_reconstruction_capacity_envelope(complete_map=...)` |
| Capacity per resource | `build_reconstruction_capacity_summary(complete_map=..., resource_kind=...)` |
| Optimization input | `optimization_input_from_reconstruction(..., cleanup=...)` → `mineable_cells == complete_map.field_cells` |
| Acceptance topology (solver) | `acceptance_topology_from_complete_map(complete_map)` |
| Lab capacity platform counts | `capacity_upper_bound_platform_count` from envelope `by_resource` |

**Parity invariant (regression-tested, G3):**

```text
len(overlay_field_cells) < len(complete_map.field_cells)   # on canon reconstruction fixture
len(complete_map.field_cells) == snapshot_summary_from_rows(full_map_rows).field_count
inp.mineable_cells == complete_map.field_cells
```

---

## §3 — Forbidden and allowed

### Forbidden (solver / capacity / topology / OptimizationInput)

```text
- Deriving capacity platform count or mineable_cells from ReconstructionResult.cells alone
- Public terrain SoT APIs taking only ReconstructionResult (no complete_map) for field counts
- optimization/ importing overlay mineable/topology helpers (§5 G1)
- Decision/capacity paths using recon.cells as mineable or field-count SoT (§5 G2)
- Lab capacity section using overlay_cell_count or deprecated cell_count as platform SoT (§5 G4)
- Reading replay persisted full_map or prior solver_summary as algorithm input (existing bans; not relaxed)
```

### Allowed

```text
- ReconstructionResult.cells for pipeline overlay, confidence masks, trace, replay row merge
- display_map.merge_reconstruction_display_cells (same merge as factory; no second SoT)
- replay full_map / solver_summary as UI output-only artifacts
- acceptance_topology_from_reconstruction in:
    • tests/unit/** (explicit contract / overlay-vs-complete assertions)
    • reconstruction/confidence.py when cleanup is None (fallback only; documented)
- recon.cells in observability/replay/diagnostic modules on allowlist (§5 G2)
```

---

## §4 — Observability key vocabulary

Normative keys for `build_reconstruction_observability`, `reconstruction_step_from_result` metrics, and Lab `reconstruction_*` summary section.

| Key | Definition | Role |
|-----|------------|------|
| `cell_count` | **Deprecated / ambiguous** | Legacy alias only; MUST NOT be used for capacity or platform SoT in new code or Lab capacity cards |
| `overlay_cell_count` | `len(recon.cells)` | Diagnostic: sparse reconstruction overlay size |
| `display_cell_count` | `len(complete_map.cells)` | Lab display map size (merged structural + overlay) |
| `asteroid_field_cell_count` | `len(complete_map.field_cells)` | **Capacity SoT** — matches mineable field set |
| `shape_field_cell_count` | `complete_map.shape_field_cell_count` | Per-resource capacity SoT |
| `fluid_field_cell_count` | `complete_map.fluid_field_cell_count` | Per-resource capacity SoT |

**Deprecation policy (PR-CGATE-1):**

- Gates and tests **forbid** new uses of `cell_count` on capacity/decision paths.
- PR-CGATE-1 does **not** remove `cell_count` from production JSON (backward compatibility).
- PR-CGATE-1b (only if needed): emit `overlay_cell_count` alongside deprecated `cell_count` in observability writers; update Lab mapper to prefer `overlay_cell_count` for display-only reconstruction stats.

**Lab capacity section rule:**

```text
platform_upper_bound, shape_platform_count, fluid_platform_count
  MUST come from reconstruction_capacity.by_resource.*.capacity_upper_bound_platform_count
  (complete_map-derived envelope only).

MUST NOT be derived from reconstruction.cell_count or overlay_cell_count.
```

---

## §5 — Architecture gates

### G1 — AST import guard

**File:** `tests/unit/architecture/test_capacity_complete_map_sot_gates.py`

**Scanned roots:**

```text
django_apps/asteroid_lab/optimization/**/*.py
django_apps/asteroid_lab/services/solver_runtime_entry.py
django_apps/asteroid_lab/services/reconstruction_capacity_summary.py
django_apps/asteroid_lab/optimization/reconstruction_adapter.py
```

**Forbidden import symbols** (any `ImportFrom` / `import` binding to these names):

```text
mineable_coords_from_reconstruction
external_void_coords_from_reconstruction
asteroid_field_cells_from_reconstruction   # if symbol still exists — gate fails until deleted
```

**Forbidden module-level call** (AST `Call` on imported overlay topology in scanned roots):

```text
acceptance_topology_from_reconstruction(
```

**Explicit allowlist (no change without spec amendment):**

- PR-B reconstruction allowlist unchanged (`reconstruction_adapter.py`, `rttp_solver_summary.py`, etc.)
- `reconstruction/complete_map.py`, `field_cells.py`, `acceptance_topology.py` may define overlay helpers; optimization may import `build_reconstruction_complete_map`, `acceptance_topology_from_complete_map`, `*_from_complete_map` only

**Confidence / tests:**

```text
reconstruction/confidence.py may import acceptance_topology_from_reconstruction
  — excluded from optimization scan; not a decision-path consumer.
tests/unit/** may import overlay topology for contract tests.
```

### G2 — Semantic token gate (not blanket grep)

**Problem:** A repo-wide ban on `recon.cells` breaks replay merge, `display_map`, and observability.

**Rule:** Token scan applies only to **decision/capacity/topology/OptimizationInput paths** — same subtree idea as PR-B §2.3C:

```text
Scanned: optimization/{commit,selection,routing,candidates,validation,macros,skeleton}/
         reconstruction_adapter.py
         solver_runtime_entry.py (build path that constructs OptimizationInput)

Excluded files (writers / observability — no token scan):
  pipeline.py, rttp_solver_summary.py, rttp_replay_diagnostics.py, replay_sink.py,
  reconstruction_capacity_summary.py (envelope builders use complete_map param only),
  reconstruction/complete_map.py, reconstruction/display_map.py, replay/**
```

**Forbidden patterns in scanned files** (AST attribute `recon.cells` or `result.cells` when used as):

- Argument to functions whose names contain `mineable`, `field_cell`, `capacity`, `platform_count` (closed list in test module)
- Subscript/len used to populate `mineable_cells` or `capacity_upper_bound` without `complete_map` in the same function scope (heuristic: fail if `mineable_cells` assignment traces to `.cells` on `ReconstructionResult` parameter)

**Allowed `recon.cells` uses in excluded observability modules:**

- Must be exposed in metrics as **`overlay_cell_count`** after PR-CGATE-1b, or remain as `cell_count` only in excluded files until 1b
- `reconstruction_step_from_result`, `build_reconstruction_observability` — excluded from token scan; covered by §4 contract tests

### G3 — Complete-map regression (extend existing tests)

**Required tests (may already exist — gate script asserts collection):**

| Test | Assertion |
|------|-----------|
| `test_overlay_field_count_less_than_complete_on_canon_fixture` | `overlay_field_cell_count(recon) < len(complete.field_cells)` and `complete_n >= 50` |
| `test_complete_field_count_matches_full_map_row_summary` | complete field count == replay row summary `field_count` |
| `test_optimization_input_adapter` (existing) | `inp.mineable_cells == complete.field_cells` with `cleanup` required |
| `test_reconstruction_capacity_summary` | `capacity_upper_bound_platform_count == complete_map.shape_field_cell_count` (shape path) |

**Canon fixture:** `load_reconstruction_fixture_line_pairs()[1]` via `test_complete_map._canon_cleanup_recon()` — guarantees sparse overlay vs dense complete map.

### G4 — Lab summary contract

**File:** extend `tests/unit/asteroid_lab/test_solver_run_lab_summary.py` or add `test_lab_capacity_complete_map_contract.py`

**Test name (required):** `test_lab_capacity_uses_complete_map_even_when_overlay_is_sparse`

**Fixture requirements (must all hold — avoids coincidental equality):**

```text
overlay_cell_count != display_cell_count
overlay_field_cell_count < asteroid_field_cell_count   # overlay_field_cell_count from complete_map.overlay helper
capacity.shape.capacity_upper_bound_platform_count == shape_field_cell_count
capacity.shape.capacity_upper_bound_platform_count != overlay_field_cell_count   # when overlay sparse on canon
```

**Construction:** Build `reconstruction_observability` + `reconstruction_capacity` from `build_reconstruction_observability` / `build_reconstruction_capacity_envelope` on canon `complete_map` (not hand-picked equal integers). Pass through `lab_run_summary_from_solver_summary`. Assert Lab `row["capacity"]["platform_upper_bound"]` equals complete-map shape platform count and `row["reconstruction"]["asteroid_field_cell_count"]` matches; assert overlay metrics are strictly smaller than complete field metrics on canon.

**Forbidden test pattern:**

```text
DO NOT: assert cell_count != platform_count as sole drift detector
        (coincidental equality on small synthetic fixtures)
```

### G5 — Standing script

**File:** `scripts/test_capacity_sot.ps1`

```powershell
python -m pytest tests/unit/architecture/test_capacity_complete_map_sot_gates.py -v --tb=short
python -m pytest tests/unit/asteroid_lab/test_complete_map.py tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py -v --tb=short
python -m pytest tests/unit/asteroid_lab/test_solver_run_lab_summary.py -k "complete_map_even_when_overlay_is_sparse" -v --tb=short
python -m ruff check django_apps/asteroid_lab/reconstruction django_apps/asteroid_lab/services/reconstruction_capacity_summary.py tests/unit/architecture/test_capacity_complete_map_sot_gates.py
```

**Ownership:** Document in `documents/ai/current_plan.md` Maintenance section. **Not** merged into `test_reconstruction_narrow.ps1` or `test_optimization_contamination.ps1`.

---

## §6 — Known drift and PR-CGATE-1b fallback

**Known drift on `master` (observability only — no solver semantics):**

| Location | Current | Target (1b) |
|----------|---------|-------------|
| `build_reconstruction_observability` | `cell_count: len(recon.cells)` | Add `overlay_cell_count`; keep `cell_count` as deprecated alias |
| `reconstruction_step_from_result` | `cell_count: len(recon.cells)` | Add `overlay_cell_count` in metrics |
| `solver_run_lab_summary._section_reconstruction` | maps `cell_count` | Prefer `overlay_cell_count` when present |

**PR-CGATE-1 delivery:** docs + tests + gates only. **Default: no production edits.**

**PR-CGATE-1b trigger:** G1/G2/G4 green only after observability renames, or explicit maintainer decision to emit dual keys before removing deprecated alias.

**1b constraints:** Observability/Lab mapping only; no changes to `OptimizationInput` construction, commit, validation, or FOT.

---

## §7 — Verification

### Iteration (PR-CGATE-1)

```bash
powershell -File scripts/test_capacity_sot.ps1
```

### PR merge (unchanged standing gates)

```bash
powershell -File scripts/test_reconstruction_narrow.ps1
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
powershell -File scripts/test_optimization_contamination.ps1
```

### Success criteria (C-GATE closure)

```text
1. All G1–G5 tests pass on master after PR merge.
2. No new optimization import of overlay mineable topology.
3. Canon fixture proves overlay_field_count < complete_field_count in Lab+capacity contract test.
4. current_plan ACTIVE → CLOSED with PR link.
5. Roadmap records: GA promotion unblocked (next spec still required).
```

---

## §8 — Governance

### `current_plan.md` ACTIVE row (normative text)

```text
ACTIVE: Capacity C-GATE — complete-map SoT architecture gates
Spec: docs/superpowers/specs/2026-05-29-reconstruction-capacity-c-gate-design.md
Plan: docs/superpowers/plans/2026-05-29-reconstruction-capacity-c-gate.md
Blocks: GA promotion until CLOSED (new GA spec still required after C-GATE)
Standing gate: scripts/test_capacity_sot.ps1
```

### Roadmap update

In [`2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md) Axis A “Open next”:

```text
ACTIVE: Capacity C-GATE (spec 2026-05-29)
GA: blocked until C-GATE CLOSED
Macro: PAUSED (unchanged)
```

### Promotion order after CLOSED

```text
1. C-GATE CLOSED
2. GA spec + current_plan ACTIVE (evolutionary search promotion)
3. Macro child-pool fixture spec
4. Lab/replay UX defer
```

---

## §9 — Deferred follow-ups

| Item | When |
|------|------|
| Rename `ReconstructionResult.cells` → `overlay_cells` | Separate PR; after C-GATE green |
| Remove `acceptance_topology_from_reconstruction` from public `__all__` | After confidence always receives `cleanup` in production |
| Remove deprecated `cell_count` from persisted solver_summary | Optional migration note; old runs retain legacy keys |
| Full GA / macro / UX tracks | Separate specs per `current_plan` queue rules |

---

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| G2 heuristic false positive | Narrow scanned subtrees; excluded observability files; amend allowlist via spec |
| Lab test brittle on canon fixture change | Assert inequality chains, not single equality |
| Operators confused by dual keys during 1b | Document in spec + Lab template comments (English) |
| C-GATE mistaken for complete-map re-implementation | §1 states factory already exists; gates only |

---

## Approval record

| Role | Decision | Date |
|------|----------|------|
| RTTP Governance Architect | Approved Approach 2 + five spec amendments | 2026-05-29 |
| Implementation | Pending spec file review → writing-plans → PR-CGATE-1 |
