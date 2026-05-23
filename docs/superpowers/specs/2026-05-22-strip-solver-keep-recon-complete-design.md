# Strip Solver — Keep Reconstruction Complete — Design Spec

**Status:** Approved 2026-05-22 (implementation gated on spec review)  
**Owner:** solver-runtime-pipeline / asteroid-lab  
**Track:** Repository surgery — **A-safe / extraction-first solver strip**  
**Supersedes / cancels (do not implement):**
- [`2026-05-22-reprobe-drift-shadow-domain-design.md`](2026-05-22-reprobe-drift-shadow-domain-design.md)
- [`2026-05-22-phase-i-commit-survivability-design.md`](2026-05-22-phase-i-commit-survivability-design.md)
- [`2026-05-22-commit-order-inlet-aware-design.md`](2026-05-22-commit-order-inlet-aware-design.md)
- [`2026-05-22-commit-order-probe-fragile-first-design.md`](2026-05-22-commit-order-probe-fragile-first-design.md)
- Plan: [`2026-05-22-reprobe-drift-shadow-domain.md`](../plans/2026-05-22-reprobe-drift-shadow-domain.md)

## Problem

Solver / optimization work (candidate pool, route probe, commit, shadow experiments, RD gate) is not salvageable in the current tree. Lab **topology reconstruction through `reconstruction.complete`** remains correct and must stay the only algorithm path.

**Goal:** Remove post-reconstruction optimization algorithm code while preserving decode → cleanup → reconstruction → display_map → persist → reconstruction replay, with minimal UI/API churn.

## Approved boundary

```text
KEEP:
  decode / cleanup / reconstruction / display_map / persist
  reconstruction replay / Lab UI shell (Reconstruct flow)

REMOVE:
  candidate / route probe / genome / fitness / evolutionary search
  commit / validation / solver runtime / RD gate / shadow experiments
```

This matches the layered model in [`documents/Algorithm/`](../../../documents/Algorithm/README.md): reconstruction produces the map; optimization is a separate layer that this surgery deletes.

## Approved approach: A-safe / extraction-first

**Order is mandatory:** extract shared non-solver contracts → rewire reconstruction/confidence → delete `optimization/` → stub solver entrypoints → prune tests/docs.

Do **not** delete `django_apps/asteroid_lab/optimization/` until GATE-1 passes.

---

## Approval gates (spec contract — all required before merge)

| Gate | Requirement |
|------|-------------|
| **GATE-1** | `reconstruction/confidence.py` (and all `reconstruction/`) **no longer imports** `django_apps.asteroid_lab.optimization` |
| **GATE-2** | `django_apps/asteroid_lab/optimization/` **removed** after extraction (directory absent or empty `__init__.py` only if re-export shim required — prefer absent) |
| **GATE-3** | Reconstruction-complete replay/persist tests pass (see §Verification) |
| **GATE-4** | `run_solver` HTTP endpoint returns `SOLVER_NOT_AVAILABLE` JSON, **never 500** |
| **GATE-5** | No `solver_runtime_pipeline` / `solver_runtime_entry` **algorithm body** remains (stub-only modules allowed) |
| **GATE-6** | No `selection_shadow` / `commit_order` / `rd_gate` experiment files remain in repo |
| **GATE-7** | Docs mark solver Phase C–M as **ARCHIVED** or removed; recon phases stay ACTIVE |

---

## Condition 1 — Adapter extraction (mandatory before `optimization/` delete)

### Source

`django_apps/asteroid_lab/optimization/reconstruction_adapter.py`

### Target

`django_apps/asteroid_lab/reconstruction/acceptance_topology.py`

### Extract (no `OptimizationInput`)

Move or reimplement only what reconstruction acceptance needs:

| Capability | Consumers |
|------------|-----------|
| `mineable` cell set (Server X/Y) | `confidence.py`, topology acceptance |
| `external_void` cell set | `confidence.py` |
| Topology acceptance helpers (ambiguous vs mineable, hard evidence preserved) | `confidence.py`, `existing_layout_service` |
| `Coord` / server-xy resolution for cells | `result.py`, `topology_contract.py`, `confidence.py` |

**Forbidden after extraction:** `confidence.py` calling `optimization_input_from_reconstruction` or importing `OptimizationInput`, `LoadedReconstructionSnapshot`, or any `optimization.*` module.

**Allowed public API (suggested names — implementer may align to existing style):**

```python
# reconstruction/acceptance_topology.py
def mineable_server_coords_from_reconstruction(result: ReconstructionResult) -> frozenset[Coord]: ...
def external_void_server_coords_from_reconstruction(result: ReconstructionResult) -> frozenset[Coord]: ...
def constraint_violation_count(result: ReconstructionResult, *, ambiguous: frozenset[Coord]) -> int: ...
```

Full `TopologyGraph` / `OptimizationInput` graph building stays **deleted** with `optimization/` unless a future spec revives it.

### Shared grid types (not solver)

Move minimal types out of `optimization/` **before** delete:

| From | To |
|------|-----|
| `optimization/coords.py` (`Coord`, `neighbors4_server` if needed by acceptance) | `django_apps/asteroid_lab/snapshots/grid_contract.py` |
| `optimization/input_contracts.py` (`BBox`, `bbox_from_coords`, `cells_in_bbox`, `expand_bbox` only) | same file or `reconstruction/grid_contract.py` |

Update `reconstruction/result.py`, `topology_contract.py`, `confidence.py` imports to new paths.

---

## Condition 2 — `game_data` snapshot contracts (not solver)

`game_data_contracts.py`, `game_data_contract_validation.py`, `game_data_snapshot_hash.py` are **web/fixture snapshot stability**, not optimization algorithm.

| From | To |
|------|-----|
| `optimization/game_data_contracts.py` | `django_apps/asteroid_lab/contracts/game_data_snapshot.py` (merge modules if small) |
| `optimization/game_data_contract_validation.py` | same package |
| `optimization/game_data_snapshot_hash.py` | same package |

Update imports:

- `django_apps/web/services/asteroid_game_data_snapshot.py`
- `django_apps/asteroid_lab/adapters/game_data_snapshot_adapter.py`
- tests under `tests/unit/web/`, `tests/unit/asteroid_lab/test_game_data_*`

**GATE-1 scope:** `reconstruction/` must not import `optimization`; `contracts/` and `web/` may import `contracts.game_data_snapshot`.

---

## Condition 3 — Solver URL stub (not delete)

Keep URL routes and `run_solver_url` in page context. **Do not** large-edit `asteroid_miner_layout_lab.js` or templates.

### Module shape

| File | After surgery |
|------|----------------|
| `services/solver_runtime_entry.py` | Stub only: no pipeline, no gene resolver, no replay recorder |
| `services/solver_runtime_pipeline.py` | **Delete** or replace with re-export of stub error — prefer **delete** |
| `web/views/public_pages.py` | Call stub; map to JSON below |

### Response contract (canonical)

HTTP **200** (minimize `fetch().ok` breakage). Body:

```json
{
  "ok": false,
  "error_code": "SOLVER_NOT_AVAILABLE",
  "message": "Solver runtime has been removed; reconstruction is still available."
}
```

- `error_code` must be a **named constant** in `django_apps/asteroid_lab` (enum or `StrEnum`), with unit test — no free-form strings.
- View must catch exceptions from stub path and still return this JSON (GATE-4).

### Management command

`manage.py run_solver` — remove command **or** make it print the same `error_code` and exit non-zero without importing deleted modules.

---

## Condition 4 — GeneticSample preserved

Move solver-adjacent but **non-runtime** gene artifacts out of `optimization/`:

| From | To |
|------|-----|
| `optimization/gene_template.py` | `django_apps/asteroid_lab/genetic_sample/gene_template.py` |
| `optimization/gene_template_loader.py` | `django_apps/asteroid_lab/genetic_sample/gene_template_loader.py` |

Update:

- `admin.py`, `genetic_sample_mini_map.py`, `services/genetic_sample_gene_export.py`
- `services/runtime_gene_template_resolver.py` — **delete** (solver-only) unless admin needs it; if admin needs loader, import from `genetic_sample/`

**Do not** remove `GeneticSample` ORM, migrations, or admin screens in this surgery.

---

## Deletion inventory (after extraction)

### Package: `django_apps/asteroid_lab/optimization/`

Delete entire directory once GATE-1 satisfied. Includes but not limited to:

- candidate_*, route_*, commit_*, final_validation, capacity_planner, route_goal_planner
- gene_projection, fitness_contracts, pipeline_result, timing_metrics
- bundle_selection_targets, placement/route materializers
- All untracked experiment modules: `selection_shadow_*`, `selection_commit_ordering`, `runtime_beam_selection`, `runtime_budget`, `commit_route_feasibility`, `route_path_normalization`, etc.

### Services

- `solver_runtime_pipeline.py` — delete
- `solver_generation_config.py`, `runtime_solver_config.py`, `solver_run_config_keys.py` — delete if only solver; else trim to stub keys only
- `runtime_gene_template_resolver.py` — delete
- `sample_gene_exhaustive_generator.py` — delete if only solver feed

### Replay / observability

- `replay/solver_runtime_replay_recorder.py` — delete
- `replay/replay_recording_cells.py` — delete if only solver overlay
- `observability/solver_summary_stack_log.py` — delete

### Scripts / var artifacts (repo hygiene)

- `scripts/compare_m2_commit_order_smoke.*`
- `scripts/sweep_solver_rd_gate.*`
- `scripts/confirm_rd_gate_lab_config.py`
- `scripts/run_solver.py` (if duplicate of management command)
- `var/solver_sweep_*`, `var/rd_gate_confirm.json` — delete from working tree (do not commit secrets)

### Tests — remove

All tests whose primary subject is removed algorithm, including:

- `test_solver_runtime_pipeline.py`, `test_solver_runtime_entry.py`, `test_run_solver_management_command.py`
- `test_candidate_*`, `test_route_probe.py`, `test_incremental_commit.py`, `test_final_validation.py`
- `test_selection_shadow_*`, `test_selection_commit_ordering.py`, `test_commit_order_diversity.py`
- `test_runtime_budget.py`, `test_route_path_normalization.py`, `test_placement_materializer.py`, `test_route_materializer.py`
- `test_solver_summary_stack_log.py`, `test_solver_runtime_replay_recorder.py`, `test_solver_runtime_performance.py`
- `tests/integration/asteroid_lab/test_solver_button_pipeline.py`, `test_solver_runtime_replay_timeline.py`
- `tests/integration/web/test_asteroid_run_solver.py`, `test_solver_with_game_data_snapshot.py` (solver path only — keep snapshot contract tests if they only hit `contracts/`)
- `tests/test_golden_candidate_selector.py`

### Tests — keep (GATE-3)

- `test_reconstruction_*`, `test_cleanup_*`, `test_reconstruction_persist_full_map_bbox.py`
- `test_reconstruction_fixture_contract.py`, `test_reconstruction_replay_merge.py`
- `test_replay_timeline_dto.py` (reconstruction_complete keyframes)
- `test_timeline_composer.py` (RECONSTRUCTION_COMPLETED retention)
- `test_game_data_contracts.py` / snapshot tests after import path update

### New test (GATE-4)

- `tests/unit/asteroid_lab/test_solver_stub_not_available.py` (or web integration): POST run_solver → 200, `ok: false`, `error_code == SOLVER_NOT_AVAILABLE`

---

## Documentation (GATE-7)

| Path | Action |
|------|--------|
| `documents/Algorithm/solver_runtime/phase_c_*.md` … `phase_m_*.md` | Header `status: ARCHIVED` + one-line pointer to this spec |
| `documents/Algorithm/solver_runtime/README.md` | Runtime execution C–M struck; PR3–7 row note **removed 2026-05-22**; Phase A–B note **adapter removed — recon-only** |
| `documents/Algorithm/solver_runtime/phase_a_*.md`, `phase_b_*.md` | ARCHIVED or “load/adapter superseded by recon-only” |
| `docs/superpowers/plans/2026-05-22-reprobe-drift-shadow-domain.md` | `status: CANCELLED` |
| Other `docs/superpowers/specs/2026-05-22-*commit*`, `*shadow*` | `status: CANCELLED` superseded by this spec |

**Keep ACTIVE:** `documents/Algorithm/asteroid_lab_*` reconstruction/replay docs, `documents/ai/plans/reconstructed_asteroid_persistence.md`, cleanup topology plans.

---

## Out of scope (explicit)

- Removing `SolverRun` / `GeneticSample` ORM models or migrations
- Rewriting Lab JS replay HUD for optimization events (may no-op)
- Re-implementing solver in `src/shapez2_factory/`
- Golden harness phase2 datasets for removed solver

---

## Implementation sequence (for plan author)

```text
1. Add snapshots/grid_contract.py + reconstruction/acceptance_topology.py (copy logic from reconstruction_adapter)
2. Rewire reconstruction/* imports; run GATE-1 grep + reconstruction unit tests
3. Add contracts/game_data_snapshot.py; rewire web/adapters/tests
4. Move genetic_sample/gene_template*.py; rewire admin/export
5. Add solver stub + error enum + GATE-4 test; trim public_pages view
6. Delete optimization/ + solver services + replay recorder + scripts + experiment tests
7. GATE-6 file grep (selection_shadow, commit_order, rd_gate)
8. Doc ARCHIVED pass (GATE-7)
9. Full narrow pytest per §Verification
```

---

## Verification (post-implementation)

```bash
# GATE-1 (zero imports)
rg "django_apps\.asteroid_lab\.optimization" django_apps/asteroid_lab/reconstruction

# GATE-2 (dir gone)
test ! -d django_apps/asteroid_lab/optimization  # or only empty shim — prefer gone

# GATE-3
python -m pytest tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py
python -m pytest tests/unit/asteroid_lab/test_reconstruction_persist_full_map_bbox.py
python -m pytest tests/unit/asteroid_lab/test_reconstruction_replay_merge.py
python -m pytest tests/unit/asteroid_lab/test_timeline_composer.py

# GATE-4
python -m pytest tests/unit/asteroid_lab/test_solver_stub_not_available.py
# or tests/integration/web/test_asteroid_run_solver.py (updated)

# GATE-6
rg "selection_shadow|commit_order_diversity|rd_gate" django_apps scripts tests

# Lint (changed paths)
python -m ruff check django_apps/asteroid_lab/reconstruction django_apps/asteroid_lab/contracts django_apps/asteroid_lab/services/solver_runtime_entry.py
```

---

## Risks

| Risk | Mitigation |
|------|------------|
| `confidence.py` regression | GATE-3 fixture contract + persist bbox tests |
| Web snapshot hash drift | Keep `contracts/` move behavior-identical; run `test_game_data_snapshot_*` |
| Admin genetic sample import break | Move templates before deleting `optimization/gene_template.py` |
| CI still collects deleted tests | Delete test files in same PR |

---

## Spec self-review (2026-05-22)

- [x] No TBD sections
- [x] Gates 1–7 map to user approval conditions 1–4
- [x] Extraction-before-delete order explicit
- [x] Stub HTTP 200 + `ok: false` documented
- [x] Scope bounded (recon keep / solver remove)

---

## Next step

1. **Human review** of this file — comment or approve.
2. On approval → invoke **writing-plans** skill → `docs/superpowers/plans/2026-05-22-strip-solver-keep-recon-complete.md`
3. Implement only after plan + protocol step 4 (human approval) per [`AGENTS.md`](../../../AGENTS.md).
