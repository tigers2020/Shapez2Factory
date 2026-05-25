# RTTP Commit — Cross-Commit Fixed Output Transport Reservation (Hotfix / PR1.5)

**Status:** Implemented — **PR [#85](https://github.com/tigers2020/Shapez2Factory/pull/85)** (2026-05-27)  
**Branch:** `feat/rttp-miner-output-transport-topology-pr1` — PR1.5 commit `04bf7b4f`; Phase 1 topology WIP remains unstaged locally  
**Work classification:** contract change · regression fix (Commit Path B)  
**Related:** [`2026-05-27-rttp-miner-output-transport-topology-design.md`](2026-05-27-rttp-miner-output-transport-topology-design.md) (Phase 1 per-candidate INV-R) · [`../plans/2026-05-27-rttp-commit-fot-cross-commit-hotfix.md`](../plans/2026-05-27-rttp-commit-fot-cross-commit-hotfix.md) (implementation plan) · [`documents/Algorithm/asteroid_lab_07_incremental_commit.md`](../../../documents/Algorithm/asteroid_lab_07_incremental_commit.md)

**Problem (Lab regression):** N miner at `(-1,-9)` reserves FOT at `(-1,-10)`. W miner at `(-1,-10)` commits because `occupied_cells` are disjoint; FOT was not in `committed_occupied`, so the output cell was treated as free for another extractor.

**Not in scope here:** Phase 1 candidate geometry (`INV-R-*`), overlay field-kind sprite override (`Layout_FluidMiner` on fluid fields), Phase 2 extension synthesis.

---

## Core distinction

```text
extractor occupied cell  !=  fixed_output_transport cell
```

Per-candidate `INV-R-01` does not imply cross-commit protection. **Commit-domain state** must reserve FOT cells across the incremental commit sequence.

---

## Invariants

| ID | Rule |
|----|------|
| **INV-COMMIT-FOT-01** | A confirmed extractor's `fixed_output_transport` cell is **reserved transport space**. No later confirmed placement may occupy it with extractor or extension equipment (`occupied_cells`). |
| **INV-COMMIT-FOT-02** | A candidate whose `fixed_output_transport` cell overlaps existing `committed_occupied` must fail commit with `CommitConflictReason.FIXED_OUTPUT_TRANSPORT_CONFLICT`. |
| **INV-VALIDATION-FOT-01** | `validate_final_layout` must return `False` if any confirmed equipment `occupied_cells` intersect another confirmed candidate's FOT cell. **Read-only** — no repair. |

Symmetric commit gate (both required):

```text
1. new_candidate.occupied_cells ∩ committed_fixed_output_transport_cells
   → FIXED_OUTPUT_TRANSPORT_CONFLICT   (INV-COMMIT-FOT-01)

2. fixed_output_transport_cell(new_candidate) ∈ committed_occupied
   → FIXED_OUTPUT_TRANSPORT_CONFLICT   (INV-COMMIT-FOT-02)
```

Commit order must not matter (e.g. W → N and N → W both blocked).

---

## `CommitDomainState` contract

Add field (**append-only** — do not reorder or remove existing fields; replay builders, deferred retry, macro commit, and any positional dataclass consumers ripple here):

```python
committed_fixed_output_transport_cells: frozenset[Coord]
```

- Initialized empty in `initial_commit_domain`.
- On successful commit: union `{fixed_output_transport_cell(candidate)}`.
- Propagated through `incremental_commit_macro._domain_after_single_commit` and deferred retry state rebuild (`_state_after_primary`).

**Do not** merge FOT cells into `reserved_route_cells` or `committed_route_cells`:

```text
FOT reservation     = equipment placement exclusion (extractor/extension forbidden)
route reservation   = belt/pipe path materialization
```

Mixing them re-blends placement validation with route validation.

### FOT helper (projected pattern only)

```python
# optimization/candidates/placement_cells.py
fixed_output_transport_cell(candidate: BundleCandidate) -> Coord
```

- Uses `candidate.anchor_coord + candidate.pattern.fixed_output_transport_offset` only.
- **Forbidden in commit/validation path:** rotation re-derivation, catalog attachment lookup, footprint evidence fallback, or inferring FOT from `output_dir` at commit time.
- Authority for offset values remains candidate generation / `miner_placement_topology` (Phase 1); commit consumes the projected `BundlePattern` SoT.

---

## `CommitConflictReason`

| Value | Meaning |
|-------|---------|
| `fixed_output_transport_conflict` | `FIXED_OUTPUT_TRANSPORT_CONFLICT` — cross-commit FOT reservation violated (rules 1 or 2 above). Distinct from per-candidate `CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_IN_OCCUPIED` at generation time. |

Free-form strings forbidden (project invariant).

---

## Validation layer

`validate_final_layout` — assert-only, no mutation (INV-VALIDATION-FOT-01):

- Track `occupied_seen` and `fot_seen` in genome commit order.
- Return `False` if `fot_cell in occupied_seen` or `candidate.occupied_cells & fot_seen`.
- **No repair** of layout, routes, or placements.

### Validation issue code (contract hook)

v0 `validate_final_layout` returns `bool` only. When structured validation is added, map the same rule to a **validation-layer** enum (separate type from `CommitConflictReason`):

| Proposed code | When |
|---------------|------|
| `fixed_output_transport_occupied` | Confirmed `occupied_cells` intersect another confirmed candidate's FOT cell (symmetric with commit gate) |

Naming aligns with commit `fixed_output_transport_conflict` but **types stay split** (validation vs commit). Until structured validation ships, tests assert `validate_final_layout(...) is False`; replay/summary may log the string above as documentation-only.

Does **not** add FOT cells to `reserved_route_cells`.

---

## Replay / Lab

- Existing replay frames (e.g. `frame_index: 22`) remain **output-only** artifacts until a new `SolverRun`.
- Post-fix acceptance: at N FOT coord (e.g. `(-1,-10)`), hover shows `placement.confirmed_fixed_output_transport` only — **not** `placement.confirmed_extractor` on the same cell.

---

## Tests (minimum gate)

| Path | Covers |
|------|--------|
| `tests/unit/asteroid_lab/test_rttp_commit_fot_conflict.py` | N→W and W→N commit rejection |
| `tests/unit/asteroid_lab/test_final_validation_route_disjoint.py` | Existing route ∩ occupied + FOT cross-check via dedicated test in fot_conflict module |

### Selection (quality assist; commit is authoritative)

`greedy_regret.py` / `macro_greedy_regret.py` pre-filter FOT-conflicting candidates from the pool so genomes are less likely to schedule commit-failing pairs. **Final authority remains `incremental_commit.py`** — selection omission is not proof of commit safety.

**Narrow gate (PR1.5):**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_commit_fot_conflict.py
python -m pytest tests/unit/asteroid_lab/test_rttp_commit.py tests/unit/asteroid_lab/test_final_validation_route_disjoint.py
python -m pytest tests/unit/asteroid_lab/test_rttp_greedy_regret.py
python -m ruff check django_apps/asteroid_lab/optimization/commit django_apps/asteroid_lab/optimization/validation django_apps/asteroid_lab/optimization/candidates/placement_cells.py django_apps/asteroid_lab/optimization/selection/greedy_regret.py tests/unit/asteroid_lab/test_rttp_commit_fot_conflict.py
```

**Merge前 broader (may include unrelated Phase 1 / catalog failures):**

```powershell
python -m pytest tests/unit/asteroid_lab -k "rttp and not macro_real_map"
python -m ruff check django_apps/asteroid_lab tests/unit/asteroid_lab
```

---

## Implementation map

| Module | Change |
|--------|--------|
| `optimization/commit/incremental_commit.py` | `committed_fixed_output_transport_cells`, bidirectional FOT checks |
| `optimization/commit/incremental_macro_commit.py` | Domain field propagation |
| `optimization/commit/deferred_retry_execute.py` | Primary state rebuild includes FOT set |
| `optimization/candidates/placement_cells.py` | `fixed_output_transport_cell` |
| `optimization/validation/final_validation.py` | INV-VALIDATION-FOT-01 |
| `optimization/selection/greedy_regret.py` | Filter pool by FOT conflict (genome must not pre-schedule commit-failing pairs) |
| `optimization/selection/macro_greedy_regret.py` | Same per macro child |

**Phase 1 plan exception:** hotfix **requires** `incremental_commit.py` edit; document as PR1.5, not a rollback of Phase 1 topology work.

**Conflict precedence (commit):** `INLET_ON_SHARED_TRANSPORT` is evaluated before FOT cross-commit checks when `output_stub ∈ committed_route_cells` (narrower inlet rule).
