# Asteroid Lab — Reconstruction Complete-Map Decontamination — Design Spec

**Document type:** Canonical repository surgery / DTO meaning cleanup  
**Status:** **CLOSED (implementation 2026-05-27, branch-local)** — PR-B on `feat/decontamination-recon-complete-map-pr-b`; merge PR link TBD  
**Implementation plan:** [`2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination.md`](../plans/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination.md)  
**Work classification:** contract change · implementation change · documentation change  
**Scope:** `django_apps/asteroid_lab/` only — **`shapez_solver` and recipe-graph UI are OUT OF SCOPE**  
**Queue authority:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md) — P0 **CLOSED (2026-05-27, branch-local)**  

**Extends:** [`2026-05-22-strip-solver-keep-recon-complete-design.md`](2026-05-22-strip-solver-keep-recon-complete-design.md) (extraction order, GATE-1–7 pattern)  
**Normative DTO semantics:** [`2026-05-26-reconstruction-complete-map-dto-design.md`](2026-05-26-reconstruction-complete-map-dto-design.md) (unchanged — enforced by decontamination)  
**Retires (runtime + active docs):** RTTP v0.2 recovery queue, active RTTP superpowers specs/plans, `optimization/` package  
**Frozen reference (do not implement until reconciliation):** [`2026-05-27-rttp-mining-equipment-goal-contract-design.md`](2026-05-27-rttp-mining-equipment-goal-contract-design.md) — **FROZEN** pending post-decontamination RTTP retain/bridge/remove decision  

**Korean title (reference):** Asteroid Lab reconstruction complete-map 제품 슬라이스 정화 (RTTP 폐기)

### Locked direction (2026-05-27 — do not drift)

```text
Ultimate goal:
  Hard-delete all Asteroid Lab RTTP / optimization layers except the
  reconstruction / ReconstructionCompleteMap product slice.

Priority:
  P0 Decontamination > RTTP MEG > v0.2 recovery

KEEP:
  decode, cleanup, reconstruction, ReconstructionCompleteMap,
  persist, reconstruction replay / Lab Reconstruct shell,
  complete-map-based capacity / topology / rim-highlight

DELETE / freeze (no implementation queue):
  RTTP, optimization, placement, routing, commit, GA / evolutionary search,
  MEG implementation, RTTP runtime, RTTP docs/tests/harness/evidence

MEG spec: reference FROZEN only — MUST NOT re-enter implementation queue until
  RTTP retention is explicitly re-opened by a new approved spec.
```

---

## §1 — Executive summary

### Problem

Most recent drift (overlay vs complete map, `placement_goal_count` meaning collapse, structural vs optimization mixing, replay artifact confusion, reachable vs confirmed pass) is **DTO / topology meaning contamination**, not missing solver heuristics alone.

Continuing RTTP Layer-4 work (e.g. MEG-C2) on the current tree would stack new optimization contracts on **unstable map semantics**, forcing migration of otherwise sound contracts (`ExteriorPassEvidence`, `optimization_goal`, equipment-cell numerators).

### Decision (governance — locked)

| Priority | Track |
|----------|--------|
| **P0** | **This spec** — reconstruction complete-map product slice only |
| P1 | DTO/DTD meaning cleanup (overlay vs complete, replay output-only) |
| P2 | Overlay / runtime artifact isolation |
| P3 | RTTP runtime retain / bridge / remove (default: **remove**) |
| P4 | MEG-C2 revival **only if** P3 explicitly re-opens RTTP |

```text
Authoritative:  C+D reconstruction-complete-map decontamination
                > RTTP MEG continuation (BLOCKED)
```

### Product boundary (North Star)

The **only** Asteroid Lab algorithm product slice after decontamination:

```text
decode → cleanup → reconstruction overlay
  → build_reconstruction_complete_map(cleanup, recon)
  → persist (ReconstructedAsteroidMap)
  → reconstruction replay / Lab Reconstruct shell
  → complete-map SoT consumers (capacity envelope, field topology, rim-highlight)
```

**Terrain / capacity SoT:** `ReconstructionCompleteMap` only.  
**`ReconstructionResult.cells`:** overlay only — never capacity, mineable, or placement domain.

### Default runtime outcome

```text
run_solver / optimization entrypoint → SOLVER_NOT_AVAILABLE (fail-closed)
ASTEROID_LAB_RTTP_ENABLED → removed or ignored (no RTTP resurrection via flag)
```

Reconstruction (`run_reconstruction_for_map_input`, persist, replay) remains available.

---

## §2 — Goals and non-goals

### Goals

| ID | Goal |
|----|------|
| G1 | Single canonical map: `ReconstructionCompleteMap` for product + observability |
| G2 | `reconstruction/**` imports **zero** `optimization` or RTTP `catalog` placement modules |
| G3 | Hard-delete RTTP runtime code; stub solver entry with enum `SOLVER_NOT_AVAILABLE` |
| G4 | Hybrid doc hygiene — `rg rttp` noise minimized; minimal audit archive |
| G5 | Inverted contamination gates (package absent; reconstruction clean) |
| G6 | `current_plan.md` reflects P0 decontamination; MEG-C2 **BLOCKED** |

### Non-goals

| Item | Disposition |
|------|-------------|
| `django_apps/shapez_solver/`, `/solver/` UI, pattern lab | **Out of scope (D)** |
| Removing `SolverRun` / `GeneticSample` ORM or migrations | Keep tables; stub runtime only |
| Re-implementing RTTP in `src/shapez2_factory/` | Future spec only |
| Implementing MEG-C2 during this surgery | **Forbidden** — spec frozen |
| Validation repair / replay as algorithm input | Re-affirm forbidden shortcuts |

---

## §3 — KEEP vs DELETE (code)

### §3.1 KEEP — reconstruction complete-map product slice

| Area | Paths / behavior |
|------|------------------|
| Pipeline | `cleanup/`, `reconstruction/` (`complete_map`, `display_map`, `field_cells`, `acceptance_topology`, `confidence`, `pipeline`, `rim_highlight`, `rim_topology`) |
| Snapshots / decode | `snapshots/`, decode adapters, `run_reconstruction_for_map_input` |
| Persist / replay | `reconstructed_map_persist_builder`, reconstruction replay frames, B-CS4 boundaries |
| Capacity (reconstruction-derived) | `reconstruction_capacity_summary` — `capacity_basis: terrain_upper_bound`; keys MUST NOT imply committed throughput or placement success |
| Contracts (non-RTTP) | `contracts/game_data_snapshot*` (per strip-solver Condition 2 if not already moved) |
| Admin adjunct | `genetic_sample/` (ORM/admin; non-runtime) |
| Stub | `solver_runtime_entry` — **stub only** after PR-B |

### §3.2 DELETE — hard delete (after extraction)

| Area | Rationale |
|------|-----------|
| `django_apps/asteroid_lab/optimization/` | Entire RTTP Hybrid C runtime |
| `django_apps/asteroid_lab/catalog/` | Placement projection; `reconstruction/` does not import; depends on `optimization` types |
| RTTP `contracts/` | `catalog_*`, `exterior_lane_*`, `ga_evolution_*`, etc. |
| RTTP services | `placement_goal`, `throughput_target`, `committed_throughput_summary`, `rttp_recovery_evidence`, `rttp_route_connectivity`, `lab_rttp_snapshot_compose`, RTTP portions of `solver_run_lab_summary` |
| Adapters | `catalog_candidate_placements`, etc. |
| Management commands | `capture_rttp_recovery_evidence`, `scan_rttp_slug_certification`, etc. |
| Tests / harness | `tests/**/*rttp*`, `tests/**/*optimization*` (subject quarantine registry update), `tests/investigation/*rttp*`, `harness/investigation/rttp_*` |
| Scripts | RTTP evidence / sweep / certification scripts |

### §3.3 Extraction before delete (mandatory — GATE-1)

| From (deleted with `optimization/`) | To |
|-------------------------------------|-----|
| `optimization/coords.py` (`Coord`, neighbors if needed) | `snapshots/grid_contract.py` (merge if exists) |
| `optimization/input_contracts.py` (`BBox`, bbox helpers only) | `snapshots/grid_contract.py` |
| `optimization/reconstruction_adapter.py` (topology slices only) | Already largely in `reconstruction/acceptance_topology.py` — verify parity |
| `optimization/game_data_contracts*.py` | `contracts/game_data_snapshot.py` (if not done) |
| `optimization/gene_template*.py` | `genetic_sample/` (if not done) |

**Do not extract:** `OptimizationInput`, `TransportKind`, `run_rttp_pipeline`, commit/selection/routing types.

---

## §4 — DTO / meaning contracts (normative)

### §4.1 `ReconstructionResult` (overlay)

```text
ReconstructionResult.cells = sparse reconstruction overlay on cleanup structural base.
MUST NOT be used for: capacity, mineable_cells, field counts, optimization placement domain.
```

### §4.2 `ReconstructionCompleteMap` (canonical)

Built only via `build_reconstruction_complete_map(cleanup, recon)`.

| Field | Meaning |
|-------|---------|
| `cells` | Merged structural + overlay (replay `reconstruction_final` parity) |
| `field_cells` | `asteroid_*_field` on merged map |
| `external_void_cells` | Topology from merged map |
| Counts | `shape_field_cell_count`, `fluid_field_cell_count` |

### §4.3 Replay / persist

| Artifact | Role |
|----------|------|
| `full_map` / persist `decoded_json` | **Output** of reconstruction — not solver algorithm input |
| RTTP optimization replay tracks | **Not emitted** after decontamination |
| Lab timeline | Reconstruction keyframes only; no placement/commit overlay |

### §4.4 Metrics language (remove or rename)

| Remove / forbid | Keep (reconstruction-derived) |
|-----------------|-------------------------------|
| `placement_goal_count` as live solver target (alias doc only if needed in JSON compat) | `target_mining_equipment_cells` — **only in frozen MEG spec**, not live runtime |
| `committed_throughput`, `bundles_needed`, pass-capable, route-feasibility product gates | `build_reconstruction_capacity_envelope` with explicit `terrain_upper_bound` |
| `validation_passed` implying optimization success | Structural replay/persist contract tests only |

---

## §5 — Runtime stub (fail-closed)

### HTTP `run_solver`

**200** + body:

```json
{
  "ok": false,
  "error_code": "SOLVER_NOT_AVAILABLE",
  "message": "Solver runtime has been removed; reconstruction is still available."
}
```

- `error_code` = enum / `StrEnum` in `django_apps/asteroid_lab` — no free-form strings.
- View MUST NOT 500 on stub path.

### `ASTEROID_LAB_RTTP_ENABLED`

**Remove** setting or document as **ignored** with no branch to `run_rttp_pipeline`. Prevents flag-based RTTP resurrection.

### `manage.py run_solver`

Remove command or exit non-zero with same `error_code` without importing deleted modules.

---

## §6 — Documentation hygiene (Hybrid C — locked)

| Class | Action |
|-------|--------|
| **Code / tests / harness** | Hard delete |
| **Active RTTP `docs/superpowers/specs/`** | Hard delete except **this spec** + **keep normative** [`2026-05-26-reconstruction-complete-map-dto-design.md`](2026-05-26-reconstruction-complete-map-dto-design.md) |
| **RTTP plans (ACTIVE / recovery / evidence recapture)** | Hard delete |
| **Closed milestone plans** | ≤10 files → `documents/archive/asteroid_lab_rttp_retired_2026-05/plans/` with front matter: `status: RETIRED_ARCHIVE`, `do_not_execute: true`, `superseded_by: <this spec>` |
| **Reports JSON (large / repeated)** | Default hard delete |
| **Forensic summary** | 1–3 MD + `documents/archive/asteroid_lab_rttp_retired_2026-05/README.md` + `evidence_summary.md` |
| **MEG spec** | **FROZEN** — not deleted; not implemented |
| **v0.2 recovery spec** | Hard delete (superseded by this surgery) |
| **`current_plan.md`** | P0 row for this spec; RTTP ACTIVE queues struck or BLOCKED |

### Archive front matter (template)

```yaml
status: RETIRED_ARCHIVE
do_not_execute: true
superseded_by: docs/superpowers/specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md
reason: RTTP runtime retired; reconstruction complete-map slice only
```

---

## §7 — Implementation approach (recommended)

**Approach:** Strip-solver re-execution (extends 2026-05-22) in **two PRs**:

| PR | Scope |
|----|--------|
| **PR-A** | Extract shared types; rewire `reconstruction/`; stub `solver_runtime_entry`; invert contamination tests; update `current_plan` header |
| **PR-B** | Delete `optimization/`, `catalog/`, RTTP services/tests/harness; doc hard-delete + selective archive; GATE-R1–R4 green |

**Rejected:** Big-bang single PR (harder debug); docs-only PR without code (leaves agent queue/code mismatch).

### Sequence (normative)

```text
1. Verify extraction targets (grid_contract, acceptance_topology, game_data_snapshot, genetic_sample)
2. PR-A: stub + rewire + GATE-1 grep green on reconstruction/**
3. PR-A: SOLVER_NOT_AVAILABLE test; remove RTTP flag branch
4. PR-B: delete optimization/, catalog/, RTTP tests/harness
5. PR-B: doc hygiene (Hybrid C)
6. PR-B: update test_optimization_contamination → test_reconstruction_decontamination gates
7. scripts/test_reconstruction_narrow.ps1 + test_capacity_sot.ps1 green
8. current_plan CLOSED row for this spec when merged
```

---

## §8 — Approval gates

| Gate | Requirement |
|------|-------------|
| **GATE-R1** | `django_apps/asteroid_lab/optimization/` absent (or empty forbidden shim) |
| **GATE-R2** | `reconstruction/**` imports no `optimization` or `catalog` placement modules |
| **GATE-R3** | `rg "run_rttp_pipeline"` → 0 hits outside `documents/archive/` |
| **GATE-R4** | `powershell -File scripts/test_reconstruction_narrow.ps1` green |
| **GATE-R5** | `run_solver` → 200, `ok: false`, `error_code == SOLVER_NOT_AVAILABLE` |
| **GATE-R6** | `rg "django_apps\.asteroid_lab\.optimization" django_apps/asteroid_lab/reconstruction` → 0 |
| **GATE-R7** | `current_plan.md` lists this spec P0 ACTIVE; MEG-C2 BLOCKED |
| **GATE-R8** | No solver-like metrics in reconstruction-only API without `terrain_upper_bound` / `reconstruction-derived` labeling |

---

## §9 — Verification commands

```bash
# GATE-R1
test ! -d django_apps/asteroid_lab/optimization

# GATE-R2 / GATE-R6
rg "django_apps\.asteroid_lab\.(optimization|catalog)" django_apps/asteroid_lab/reconstruction

# GATE-R3
rg "run_rttp_pipeline" --glob "!documents/archive/**"

# GATE-R4
powershell -File scripts/test_reconstruction_narrow.ps1

# GATE-R5
python -m pytest tests/unit/asteroid_lab/test_solver_stub_not_available.py
# or updated tests/integration/web/test_asteroid_run_solver.py

# Capacity SoT (unchanged owner)
powershell -File scripts/test_capacity_sot.ps1
```

Post PR-B: `python -m ruff check django_apps/asteroid_lab/reconstruction django_apps/asteroid_lab/contracts django_apps/asteroid_lab/services/solver_runtime_entry.py`

---

## §10 — Frozen contracts (post-decontamination revival)

These specs are **quality-approved** but **implementation BLOCKED** until P3 decision:

| Spec | Status | Revival condition |
|------|--------|-------------------|
| [`2026-05-27-rttp-mining-equipment-goal-contract-design.md`](2026-05-27-rttp-mining-equipment-goal-contract-design.md) | **FROZEN** | New spec explicitly re-opens RTTP runtime + MEG-C2 |

Do not partially implement MEG aggregator or `optimization_goal` block on a stub runtime — creates hybrid semantics.

---

## §11 — Risks

| Risk | Mitigation |
|------|------------|
| `confidence.py` regression | GATE-R4 fixture + persist bbox tests |
| Accidental deletion of complete-map factory | `test_complete_map.py` in narrow gate |
| CI collects deleted tests | Delete files in PR-B; update quarantine registry |
| Agent re-opens RTTP from roadmap | Hard-delete active RTTP specs; archive index only |
| `GeneticSample` admin break | Extract gene templates before optimization delete |

---

## §12 — `current_plan.md` delta (normative on merge)

Insert at top (replace conflicting ACTIVE RTTP/v0.2 recovery banner):

```markdown
**Status (2026-05-27): P0 ACTIVE — Reconstruction complete-map decontamination**
- **Authoritative spec:** [2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md](...)
- **BLOCKED:** RTTP MEG-C2, v0.2 core algorithm recovery implementation, all ACTIVE RTTP plans
- **Frozen reference:** [2026-05-27-rttp-mining-equipment-goal-contract-design.md](...) — do not implement until RTTP retention decided
- **Runtime target:** reconstruction + persist + replay only; `SOLVER_NOT_AVAILABLE`
```

---

## §13 — Review history

| Date | Role | Outcome |
|------|------|---------|
| 2026-05-27 | Brainstorm + Architecture Governance Lead | **Approved** — C+D scope, Hybrid C docs, decontamination > MEG; MEG FROZEN |

---

## §14 — Spec self-review

| Check | Result |
|-------|--------|
| Placeholders | None |
| Contradictions | Aligns with 2026-05-26 complete-map DTO; supersedes v0.2 recovery ACTIVE intent |
| Scope | Single implementation plan; shapez_solver excluded |
| Ambiguity | Default RTTP outcome = remove; revival requires new spec |
| MEG | Frozen, not deleted |

---

## §15 — Next step

1. ~~Human review~~ — **Approved 2026-05-27** (Decontamination Release Lead).  
2. **Implementation plan:** [`2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination.md`](../plans/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination.md)  
3. Implement only after plan + protocol step 4 approval per [`AGENTS.md`](../../../AGENTS.md).
