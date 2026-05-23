---
status: CANCELLED
cancelled_date: 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
---
# Reprobe Drift ??Phase I??Shadow Domain Parity ??Design Spec

**Status:** Approved 2026-05-22 (strong gate revision)  
**Owner:** solver-runtime-pipeline  
**Track:** C (commit survivability) ??reprobe drift (domain + path)  
**Parent / related:**
- [`2026-05-22-phase-i-commit-survivability-design.md`](2026-05-22-phase-i-commit-survivability-design.md) (Tier 1 / 1.2b)
- [`2026-05-22-commit-order-inlet-aware-design.md`](2026-05-22-commit-order-inlet-aware-design.md) (T1.2 commit order ??unchanged)
- [`2026-05-22-shared-transport-inlet-design.md`](2026-05-22-shared-transport-inlet-design.md)
- [`2026-05-22-deferred-commit-retry-design.md`](2026-05-22-deferred-commit-retry-design.md)
- [`phase_i_candidate_selection.md`](../../../documents/Algorithm/solver_runtime/phase_i_candidate_selection.md)
- [`phase_j_incremental_commit.md`](../../../documents/Algorithm/solver_runtime/phase_j_incremental_commit.md)

## Problem

After Tier 1, T1.1, T1.2, and T1.2b (full generation-path inlet mirror), reference run `copy-import-e954a2cb` still shows **reprobe drift**:

```text
selected / ordered: 24 (best_genome_enabled_gene_count)
confirmed_count: 21
commit_route_probe_failed_count: 2
commit_inlet_on_shared_transport_count: 1
selection_skipped_inlet_on_shared_transport_count: 0
validation_passed: true
```

**Root cause (two coupled drifts):**

| Drift | Phase H / I | Phase J (authoritative) |
|-------|-------------|-------------------------|
| **Domain** | Per-candidate `provisional_blocked` domain at generation | `RouteDomainSnapshotBuilder` + accumulated `confirmed_reservations` + `committed_occupied` |
| **Path** | `route_probe_result.path` (generation) | Reprobe path after normalization; `committed_route_cells` union |

Phase I cannot *prove* commit success (forbidden). It must **predict** J failures using the **same in-run DTOs and builders**, not replay or persisted metrics.

## Design goal (explicit)

**Not:** ?œreduce drift a little??or `confirmed_count >= 23` as spec success.

**Yes:** On the reference asteroid, **eliminate residual drift at commit** while keeping selection budget and validation contract:

```text
selected_candidate_count >= 24
confirmed_count >= 24
commit_route_probe_failed_count == 0
commit_inlet_on_shared_transport_count == 0
```

**Milestone only (not spec pass/fail):** `confirmed_count >= 23` during incremental implementation.

## Approved approach: I??Shadow domain parity

Extend Phase I greedy selection with an in-memory **shadow commit state** updated after each pick using **the same** domain builder and reprobe API as Phase J.

```text
Phase H (unchanged) ??generation route_probe_result (reference only)
        ??Phase I??(shadow_domain_parity)
  greedy loop:
    eligible = footprint + trunk + anchor
             + inlet: fot ??shadow.committed_route_cells  (reprobed union, NOT gen mirror)
             + shadow reprobe reachable on RouteDomainSnapshotBuilder snapshot
    pick by score; shadow_try_confirm until success or pool exhausted
    on shadow success ??append ordered id + update shadow reservations / occupied / route cells
        ??SelectedCandidatePlan (??4 ids, target 24)
        ??Phase J (unchanged authority) ??reprobe on live domain; deferred retry unchanged
```

### Authority separation

| Layer | Role |
|-------|------|
| Shadow (Phase I?? | Predictive filter + ordering input; same rules as J pre-confirm checks |
| Commit (Phase J) | **Only** proof of confirmed placement |

Shadow pass + J fail on reference gate = **shadow parity incomplete** (not an acceptable residual).

### Input guards (forbidden shortcuts)

- **No** `ReplayFrame`, `SolverRun` metrics, stack logs, or post-hoc commit counts fed into selection.
- **Yes** `OptimizationInput`, `GeneCandidate` DTOs, `config.route_probe_max_expansions`, in-memory `SelectionShadowState`.

## Architecture

### New module

`django_apps/asteroid_lab/optimization/selection_shadow_state.py`

```python
@dataclass
class SelectionShadowState:
    reservations: tuple[RouteReservation, ...]
    committed_occupied: frozenset[Coord]
    committed_route_cells: frozenset[Coord]
```

**Operations:**

1. `build_shadow_route_domain(inp, state) -> dict[Coord, RouteCellDomain]`  
   `RouteDomainSnapshotBuilder.build_snapshot(inp, confirmed_reservations=state.reservations, committed_occupied_cells=state.committed_occupied)`

2. `shadow_reprobe(candidate, inp, state, *, max_expansions) -> RouteProbeResult`  
   Same `RouteProbeInput` / `run_route_probe` as `commit_best_candidates._attempt_commit_one`.

3. `shadow_try_confirm(candidate, inp, state, *, max_expansions) -> ShadowConfirmOutcome`  
   - Reprobe on shadow domain  
   - `path = normalize_probe_path(candidate, probe.path)`  
   - Apply **same** skip predicates as J (inlet, transport conflict, protected, hard blocked, equipment overlap policy per shared-transport v0)  
   - On success: append `RouteReservation`, extend `committed_route_cells` and `committed_occupied`

4. `empty_selection_shadow_state() -> SelectionShadowState`

### Phase I integration

**File:** `candidate_selector.py`

- New param: `selection_shadow_policy: SelectionShadowPolicy` (default `SHADOW_DOMAIN_PARITY` when wired from pipeline).
- When `OFF`: Tier 1.2b behavior (`selection_mirror_route_cells` inlet accumulation).
- When `SHADOW_DOMAIN_PARITY`:
  - Do **not** use `selection_mirror_route_cells` for inlet (shadow `committed_route_cells` only).
  - Eligible pool: shadow reprobe reachable + inlet hard filter on shadow cells.
  - Pick loop: highest score candidate ??`shadow_try_confirm`; on failure skip candidate for this iteration (diagnostics++), try next score; on success commit to plan + shadow state.

**File:** `solver_runtime_pipeline.py`

- Pass `selection_shadow_policy=SelectionShadowPolicy.SHADOW_DOMAIN_PARITY` and probe budget from run config.
- Summary fields (see Contracts).

### Phase J / commit order

- **No change** to reprobe, deferred retry, or `INLET_AWARE_PROBE_FRAGILE_FIRST` in v0 of this spec.
- Shadow reduces bad IDs **before** commit order runs.

## Contract changes

### `SelectionShadowPolicy` (StrEnum)

```python
class SelectionShadowPolicy(StrEnum):
    OFF = "off"
    SHADOW_DOMAIN_PARITY = "shadow_domain_parity"
```

Pipeline default after implementation: `SHADOW_DOMAIN_PARITY`. Tests keep `OFF` for Tier 1.2b regression.

### `SelectionDiagnostics` extensions

```python
selection_skipped_shadow_probe_failed_count: int = 0
selection_skipped_shadow_inlet_on_shared_transport_count: int = 0
selection_shadow_reprobe_count: int = 0
```

### `solver_summary` keys

| Key | Meaning |
|-----|---------|
| `selection_shadow_policy` | `SelectionShadowPolicy` value |
| `selected_candidate_count` | `len(selection_plan.ordered_candidate_ids)` ??**add if missing** (alias acceptable: document vs `best_genome_enabled_gene_count` only if equal by definition) |
| `selection_skipped_shadow_probe_failed_count` | Shadow reprobe unreachable |
| `selection_skipped_shadow_inlet_on_shared_transport_count` | Shadow inlet hard reject |
| `selection_shadow_reprobe_count` | Total shadow reprobes executed |

Existing commit keys unchanged: `confirmed_count`, `commit_route_probe_failed_count`, `commit_inlet_on_shared_transport_count`, `validation_passed`.

## Success criteria

### Reference hard gate (RD-GATE ??spec pass/fail)

| ID | Gate |
|----|------|
| RD1 | `validation_passed == true` |
| RD2 | `commit_inlet_on_shared_transport_count == 0` |
| RD3 | `commit_route_probe_failed_count == 0` |
| RD4 | `selected_candidate_count >= 24` |
| RD5 | `confirmed_count >= 24` |
| RD6 | `selection_shadow_policy == "shadow_domain_parity"` |
| RD7 | No replay / persisted metric as solver algorithm input (review + tests) |

### Milestone (implementation only ??not spec closure)

| Milestone | Gate |
|-----------|------|
| M1 | `confirmed_count >= 23` with RD2?“RD3 still failing ??continue I??tuning |
| M2 | RD2?“RD3 green, RD5 failing ??commit order / pool size, not rollback shadow |

### Non-goals

- `target_miner_bundle_count` / capacity 96 (`run_success` may stay false)
- Gate C / rim packing / GeneTemplate DB mix
- GA / evolution using commit survivability metrics
- Removing or bypassing Phase J reprobe
- Second deferred retry round
- Post-select 24-ID dry-run that drops below 24 selected (multi-pass selection+commit)
- Score-only Î±/Î² tuning as primary deliverable

## Testing

| Test | Behavior |
|------|----------|
| `test_shadow_reprobe_excludes_unreachable_after_prior_pick` | Prior shadow pick blocks domain ??next candidate gen-reachable but shadow unreachable ??not ordered |
| `test_shadow_inlet_uses_reprobed_path_not_gen_prefix` | Prior shadow reprobed path includes cell X; candidate fot X not on gen path ??skipped at selection |
| `test_selector_shadow_policy_off_matches_tier_1_2b` | `OFF` preserves `selection_mirror_route_cells` inlet behavior |
| `test_shadow_try_confirm_shares_j_skip_reasons` | Inlet on shadow trunk ??same `CommitConflictReason` family as J |
| `test_pipeline_summary_includes_shadow_diagnostics` | Summary keys present when policy ON |

**Regression:**

```bash
python -m pytest tests/unit/asteroid_lab/test_candidate_selector.py
python -m pytest tests/unit/asteroid_lab/test_incremental_commit.py
python -m pytest tests/unit/asteroid_lab/test_solver_runtime_pipeline.py
```

**Manual:**

```bash
python manage.py run_solver --slug copy-import-e954a2cb --run-key agent-smoke
```

## Implementation order (for writing-plans)

1. `SelectionShadowPolicy` enum + `selection_shadow_state.py` + unit tests for shadow reprobe / confirm.
2. RED: shadow unreachable + shadow inlet path-drift selector tests.
3. GREEN: wire `candidate_selector` pick loop with shadow confirm runner-up policy.
4. Pipeline: policy default ON, summary keys, `selected_candidate_count`.
5. Doc sync: `phase_i_candidate_selection.md`, `phase-i` follow-up link.
6. Reference RD-GATE run; if shadow pass but J fail ??treat as parity bug (shared helper extraction), not ?œallowed residual.??
## Risks

| Risk | Mitigation |
|------|------------|
| Selection CPU increase (many shadow reprobes) | Reprobe only eligible pool; cache seed domain; profile reference run |
| Pool cannot fill 24 under shadow | Log shadow skip counts; **do not** weaken RD4?“RD5; investigate pool generation |
| Shadow/J rule drift | Share skip predicates with J via thin shared module or tested parity matrix |
| **Shadow pass Â· J fail on reference** | **Not allowed** for RD-GATE closure ??shadow parity incomplete |

## Alternatives rejected

| Alternative | Why not |
|-------------|---------|
| Gen-path mirror only (Tier 1.2b extension) | Reference still inlet 1 + probe 2 |
| Score-only fragility / pressure tuning | Does not guarantee RD2?“RD3 == 0 |
| Post-select shadow dry-run dropping IDs | Breaks RD4; blurs deferred-retry non-goal |
| `commit_route_probe_failed_count <= 1` as spec gate | User-rejected; masks incomplete parity |
| `confirmed_count >= 23` as spec success | Milestone only; spec requires 24/24/0/0 |
| Commit metrics ??selection / fitness | Forbidden shortcut |

## Rollback

```python
SelectionShadowPolicy.OFF  # Tier 1.2b + T1.2 commit order
```

Document rollback in pipeline constant until RD-GATE green.
