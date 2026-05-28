---
status: ARCHIVED
owner: solver-runtime-pipeline
last_reviewed: 2026-05-22
archived_reason: Solver optimization pipeline removed from repository (2026-05-22)
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
related_docs:
  - documents/Algorithm/solver_runtime/README.md
  - documents/Algorithm/asteroid_lab_10_development_sequence.md
  - documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md
---

> **2026-05-22:** `django_apps/asteroid_lab/optimization/` and A→M orchestration **deleted**. The inventory·「PR complete」 tables below are **historical snapshots**.

# Architecture Reconciliation — Runtime vs Legacy Documents

**Role:** Solver Runtime Architecture Reviewer  
**Purpose:** Resolve conflicts between the Runtime series and `asteroid_lab_*`·deleted `shapez_asteroid` references in one place.

## 1. Identity of this series (conflict #1)

### Verdict

Runtime documents are the **「Solver Button E2E Pipeline v0」 contract·PR checklist**.  
They do **not** mean **「optimization not started anywhere in the repository」**.

### Separate the two axes

| Axis | Meaning | Canonical |
|----|------|------|
| **Runtime execution order** | A→M **execution order** on one button click | Phase docs·README pipeline |
| **Implementation order (PR)** | Development·review·merge **unit** | [`implementation_sequence.md`](implementation_sequence.md) |
| **Code inventory** | Modules already in `django_apps/asteroid_lab/optimization/` | §5 table below |
| **Legacy narrative** | GA·`BundlePattern`·`shapez_asteroid` pytest paths | [`asteroid_lab_*`](../) — **historical·design reference**, not Runtime PR completion proof |

### Relationship to `asteroid_lab_10`

- [`asteroid_lab_10_development_sequence.md`](../asteroid_lab_10_development_sequence.md) top baseline (2026-05-18): resetting optimization checklist to **`[ ]` not started** is **for document tracking** only; it does not mean code deletion.
- **「Implementation complete」** in [`asteroid_lab_12_runtime_replay_wiring.md`](../asteroid_lab_12_runtime_replay_wiring.md) 12F–12L etc. is **limited to Lab replay persist/read/HUD boundaries**. Not the same PR as Solver Runtime Phase C–K.

**「Not started」 in Runtime PR table** = **Solver-button contract·tests for that PR not yet green** (or orchestration not wired).  
**≠** concept in legacy doc absent from code.

---

## 2. Package boundaries (conflict #2)

### Verdict (repository 2026-05-19)

```text
django_apps/shapez_asteroid/  — removed from repository (git history only)
django_apps/asteroid_lab/optimization/  — sole optimization implementation package
```

### Canonical

| Role | Path |
|------|------|
| **New Runtime PR (PR1–7)** | `django_apps/asteroid_lab/optimization/` |
| **Lab ORM·decode·reconstruction·Lab replay** | `django_apps/asteroid_lab/` (outside optimization) |
| **Legacy references** | `tests/unit/shapez_asteroid/`, `django_apps.shapez_asteroid` — **forbidden·historical**; no new imports |

**Forbidden:** Describing or importing `shapez_asteroid.optimization` as "current package" in Runtime docs·code.

---

## 3. v0 selector: greedy vs GA (conflict #3)

### Verdict

**Solver Button v0 canonical = A: capacity-aware greedy selector only** ([`phase_i_candidate_selection.md`](phase_i_candidate_selection.md), [OD-4](open_decisions.md)).

| Item | Runtime v0 | Legacy (`asteroid_lab_05`/`06`, `asteroid_lab_10` Seq 4–5) |
|------|------------|--------------------------------------------------------------|
| Selection | PR4 greedy | Evolution Search v0·`Genome`·`Gene.commit_order` |
| Purpose | **reference·future v1** | **Not required path** for Solver button v0 |

Even if DTO has `EvolutionConfig`·`EvolutionConvergenceReason` etc., **Solver orchestration v0 does not call GA** (fields are schema placeholders).

---

## 4. Coordinate terminology (conflict #4)

### Canonical (alias forbidden)

| Name | Meaning |
|------|------|
| `fixed_output_transport` | **First belt/pipe reservation cell** immediately after extractor output (offset `(1,0)` from extractor, canonical E) |
| `route_probe_start` | Route search **start cell** (offset `(2,0)`; **not occupied**) |
| `output_stub` | **Legacy** — **forbidden** in Runtime·new code·DTO field names |

Legacy [`asteroid_lab_04`](../asteroid_lab_04_route_probe.md) `output_stub` should be mentally replaced with **`route_probe_start`** when reading.

`CandidateRejectReason.output_stub_*` enum values may **retain legacy names**; semantics are `route_probe_start` ([`phase_f_geometry_validation.md`](phase_f_geometry_validation.md)).

Materialization: [OD-1](open_decisions.md) — recommend prepending `fixed_output_transport` **before** reservation path.

---

## 5. Code inventory vs Runtime PR (status separation)

**Exists in code** ≠ **Runtime PR complete** (includes integration tests·§0.3·orchestration·event contract).

| Module·contract | Code | Runtime PR | Notes |
|-----------|------|------------|------|
| DTO·enum·`RouteDomainSnapshotBuilder` | exists | 1A (legacy Seq) | Consumed with PR1B in PR table |
| `optimization_input_from_reconstruction` | exists | **PR1B complete** | `LoadedReconstructionSnapshot`·`mineable_field_kind` (§0.3 adapter) |
| `GeneTemplate`·projection | exists | **PR1 complete** | |
| `candidate_geometry`·`route_probe` | exists | **PR2 complete** | `provisional_blocked_cells` |
| capacity·route goal planner | exists | **PR2.5 complete** | |
| candidate pool (`GeneCandidate`, dedupe, truncate) | exists | **PR3 complete** | |
| candidate selection (score, greedy, `SelectedCandidatePlan`) | exists | **PR4 complete** | |
| incremental commit (`commit_selected_candidates`, reservation overlay) | exists | **PR5 complete** | |
| route network materialization (`materialize_route_network`) | exists | **PR6 complete** | |
| `validate_final_layout` (read-only) | exists | **PR7 complete** | |
| Solver A→M orchestration (`run_solver_runtime_pipeline`) | exists | **PR7 complete** | |
| HTTP entry (`solver_runtime_entry`·POST run-solver) | exists | **PR8 complete** | |
| optimization replay persist v0 (`optimization_replay_persist`·`optimization_ui_payload`) | exists | **PR7 complete** | Lab `ReplayFrame` ORM unused; §6 |
| Lab optimization replay read (12G page context) | exists | **PR8 complete** | `optimization_replay_read` |
| Lab optimization replay HUD + Run Solver JS (12H) | exists | **PR9 complete** | `asteroid_miner_layout_lab.js` |

---

## 6. Replay persist (conflict #6)

### Verdict

PR7 Phase M does **not** build a new persist stack from scratch.

### Canonical

```text
Existing: SolverRun.config_json · optimization replay frame list · read validation · HUD diagnostic
      (asteroid_lab_12, web Lab JS, replay pipeline — implementation·tests may already exist)
New: thin adapter connecting event_type set emitted by Solver Runtime to existing writer/reader
Forbidden: reimplement 12F–12L semantics, implicit Lab↔Optimization sync
```

Details: [`phase_m_persist_replay_ui.md`](phase_m_persist_replay_ui.md).

---

## 7. Recommended implementation order (PR) vs execution order (Phase)

### Runtime execution order (one button click)

```text
A → B → C → D → E → F → G → H → I → J → K → L → M
```

### Implementation order (merge unit)

```text
PR1 (complete) → PR1B (partial) → PR2.5 → PR2 → PR3 → PR4 → PR5 → PR6 → PR7
```

PR1 finishing Phase D first is for **fixing gene contract**; at runtime execution D is called after C and before E.

---

## 8. Review conclusion checklist

- [x] Canonical package: `django_apps/asteroid_lab/optimization/`
- [x] v0 selector: greedy only; GA = legacy reference
- [x] Terminology: `route_probe_start` / `fixed_output_transport`; `output_stub` legacy
- [x] PR table vs code inventory separated
- [x] PR7 replay: thin adapter·reuse existing wiring

When changing, update this document and [`README.md`](README.md) PR table **together**.

---

## 9. Preventing implementer misunderstanding (2nd review, 2026-05-19)

| Item | Canonical |
|------|------|
| **PR2.5 prerequisite** | PR1B → **PR2.5** → PR2. `route_probe` needs planned `RouteGoal`. See README PR table bottom line. |
| **`route_goals`** | Phase B: seed/empty only. Phase C: planned canonical. |
| **Candidate route domain** | `provisional_blocked_cells=` recommended; `committed_occupied_cells=` is transitional·do not confuse with commit ([`phase_g_route_probe.md`](phase_g_route_probe.md)). |
| **New test names** | `route_probe_start_*`; enum `output_stub_*` values retained·rename forbidden ([`00_core_principles.md`](00_core_principles.md) §0.7). |
