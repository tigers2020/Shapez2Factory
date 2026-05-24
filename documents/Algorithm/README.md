# Algorithm Documentation

Collects algorithm and Lab contract notes. **Implementation authority** takes precedence: code, `CANON` in [`documents/index/document_inventory.md`](../index/document_inventory.md), and [`documents/ai/START_HERE.md`](../ai/START_HERE.md).

## Implementation baseline (2026-05-22)

| Layer | Status | Code |
|--------|------|------|
| **Reconstruction** | **ACTIVE** | `django_apps/asteroid_lab/reconstruction/`, `cleanup/`, Lab persist·replay |
| **Optimization / Solver runtime** | **REMOVED** | `django_apps/asteroid_lab/optimization/` deleted; `solver_runtime_entry` is `SOLVER_NOT_AVAILABLE` stub only |
| **Genetic sample (admin)** | **ACTIVE** | `django_apps/asteroid_lab/genetic_sample/` |
| **Game data snapshot** | **ACTIVE** | `django_apps/asteroid_lab/contracts/game_data_snapshot.py` |

**Surgery spec:** [`docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md`](../../docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md)

## Solver Runtime (ARCHIVED)

**Status:** Removed 2026-05-22. Phase C–M and PR3–7 contracts are historical archive.

- **Index:** [`solver_runtime/README.md`](solver_runtime/README.md) (`status: ARCHIVED`)
- **Reconciliation (historical):** [`solver_runtime/ARCHITECTURE_RECONCILIATION.md`](solver_runtime/ARCHITECTURE_RECONCILIATION.md)
- **HTTP entry (stub):** [`solver_runtime/01_entry_point.md`](solver_runtime/01_entry_point.md) → `run_solver_runtime_for_project` → `SOLVER_NOT_AVAILABLE`

## Reading order (reconstruction-first)

1. [`asteroid_lab_00_overview.md`](asteroid_lab_00_overview.md) — overview, coordinates, prohibitions
2. Reconstruction·cleanup·topology — `reconstruction/` code + [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md) (Lab replay **ACTIVE**)
3. **Legacy optimization series** `asteroid_lab_01`–`08` — `RESEARCH` / historical reference only (implementation deleted)
4. [`asteroid_lab_10_development_sequence.md`](asteroid_lab_10_development_sequence.md) — sequence checklist (many items not yet updated)
5. **Deleted solver button:** `solver_runtime/phase_*` — all `ARCHIVED`
6. **Miner·extension (authority realignment):** [`asteroid_lab_mining_installation/README.md`](asteroid_lab_mining_installation/README.md) → `00` → `01` → `02` → `03` (DB cross-reference); `04` (installation guide)

## File list

| File | Status | Description |
|------|------|------|
| `asteroid_lab_00_overview.md` | `RESEARCH` | Lab·coordinate principles |
| `asteroid_lab_01`–`08` | `ARCHIVED` | Optimization layer (no code) |
| `asteroid_lab_09_replay_timeline.md` | `ACTIVE` | Lab Step Replay Timeline |
| `asteroid_lab_09_replay_debug.md` | `ARCHIVED` | dual-track history |
| `asteroid_lab_10`–`13` | `RESEARCH` | roadmap·wiring |
| [`solver_runtime/`](solver_runtime/) | `ARCHIVED` | Solver button Phase A–M (removed 2026-05-22) |
| [`plans/asteroid_lab_optimization/`](plans/asteroid_lab_optimization/README.md) | `ARCHIVED` | Pre-2026-05 optimization plan copies |
| [`asteroid_lab_mining_installation/`](asteroid_lab_mining_installation/) | `AUDIT` | Miner·extension authority·contradiction table·drift·installation guide (D2) |

## Drafts (`drafts/`)

| File | Status | Description |
|------|------|------|
| [`drafts/Asteroid Mining Page Rebuild.txt`](drafts/Asteroid%20Mining%20Page%20Rebuild.txt) | `DRAFT` | Page rebuild design draft |
| [`drafts/asteroid_lab_development_plan.txt`](drafts/asteroid_lab_development_plan.txt) | `DRAFT` | Start-to-end development plan draft |

> **Note:** If a memo with the former name `Branch · Asteroid Mining Page Rebuild.txt` (UI debug notes, modal JSX, etc.) existed, place similar memos under `drafts/` or move them to a separate issue.

## Path·package notes

- **`django_apps/shapez_asteroid`** · **`asteroid_lab/optimization/`** — removed from repository. Document references are historical.
- Gene template·coord: **`genetic_sample/`** · grid: **`snapshots/grid_contract.py`**
- Cross-check: [`documents/refactor_audit/00_global_summary.md`](../refactor_audit/00_global_summary.md)

Add new algorithm authority after updating `documents/ai/` plans and `document_inventory.md`.
