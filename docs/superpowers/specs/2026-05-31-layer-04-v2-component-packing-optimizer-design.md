# Layer 04 v2 — Component-Local Packing Optimizer — Design Spec

**Document type:** Solver / Lab contract (L4 selection algorithm · layer boundary · observability)  
**Status:** **APPROVED — Placement Contract Architect (2026-05-31, blocking amendments applied)**  
**Work classification:** contract change · implementation change  
**Scope:** `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/` · `layers/contracts/rim_placement.py` · `replay/layer04_segment.py` (projection only)  
**Parent / supersedes (selection only):**

- [`2026-05-28-layer-04-rim-bundle-placement-design.md`](2026-05-28-layer-04-rim-bundle-placement-design.md) §3.4 (sequential greedy)
- [`2026-05-30-outer-rim-direction-arbitration-design.md`](2026-05-30-outer-rim-direction-arbitration-design.md) §3–§4 (mining-first greedy as sole overlap resolver) · §8 escalation criteria **promoted** into this track

**Preserves (unchanged):**

- L3 direction enumeration and route probe ([`2026-05-28-layer-03-rim-mining-bundles-design.md`](2026-05-28-layer-03-rim-mining-bundles-design.md))
- `ProvisionalLayoutOverlay` · CompleteMap immutability · replay assembler authority
- Overlap rejection metadata fields on `RimPlacementRejection` (additive extensions allowed)

**Korean title (reference):** L4 v2 — 방향·footprint packing 밀도 실패 해결 (component-local exact pack + capped fallback)

**Problem names (normative):**

- `L4_packing_density_failure`
- `orientation_induced_space_fragmentation`

---

## §0 — Layer boundary (normative)

### 0.1 Roles

| Layer | MUST | MUST NOT |
|-------|------|----------|
| **L3** `layer_03_rim_mining_bundles` | Generate candidates; estimate footprints; route probe; expose `normal_candidates` with probe status, costs, gains | Select a non-overlapping subset; global candidate reservation; component packing; MWIS; `ProvisionalLayoutOverlay`; `PROVISIONAL_PLACED` |
| **L4** `layer_04_rim_bundle_placement` | Consume L3 `normal_candidates` **as-is**; build conflict graph; component-local packing; materialize `PROVISIONAL_PLACED` + overlay | Re-run route probe; regenerate L3 candidates; change L3 enumeration policy; mutate `ReconstructionCompleteMap` |
| **L5+** | Inner fill / commit / validate using L4 overlay | Reverse L4 selection from replay artifacts |

### 0.2 Normative statements

```text
L3 is a candidate estimation and feasibility-probe layer.
L4 is the first physical placement selection layer.

Any algorithm that chooses a non-overlapping subset of candidates —
including greedy selection, component-local packing, MWIS, or fallback packing —
belongs to L4, not L3.
```

```text
L3 MUST NOT perform global candidate reservation, component packing,
or provisional placement materialization.
```

### 0.3 No duplicate work

```text
L3: expensive candidate + route-probe data generation (once).
L4: consume that data for packing only — MUST NOT re-probe or re-derive footprints
     that L3 already attached to BundleCandidate / RouteProbedBundleCandidate.
```

`throughput_factor` on L3 candidates is **estimate / observability input** to L4 metrics; it is **not** the L4 v2 primary objective (§4).

---

## §1 — Problem

### 1.1 Symptom

Candidates with **equal or similar** `effective_mining_gain` can block **many** other equal-gain candidates when a **direction choice** fragments occupied space (horizontal vs vertical footprints on a shared strip). Sequential mining-first greedy treats winners **one candidate at a time** and ignores **set opportunity cost**.

**Example class (Run #286 strip `y=11`, `x∈[-8,-2]`):** Early `E` / `W` placements occupy strip cells; later `S` candidates with the same per-candidate gain are rejected with `PHYSICAL_OVERLAP`. User throughput may be far below a better **non-overlapping set** in the same conflict component. Note: three adjacent `S` m3e seeds at `(-6,11)`, `(-5,11)`, `(-4,11)` **mutually overlap** — they cannot all appear in one feasible set; tests MUST NOT assert “all three selected.”

### 1.2 Root cause

```text
L4 v1 compares: candidate vs candidate (sort order + first-fit occupancy)
L4 v2 MUST compare: candidate set vs candidate set (per conflict component)
```

This is **not** an L3 enumeration bug. L3 MUST keep all feasible directions in the pool.

### 1.3 Non-goals (v2.0)

| Item | Status |
|------|--------|
| Global full-pool MWIS | **Non-goal** |
| Greedy + ad-hoc local replacement pass | **Non-goal** |
| `throughput_factor` as primary optimizer objective | **Forbidden** unless L3→L4 contract explicitly extended in a future spec |
| L3 packing / reservation | **Forbidden** |
| L5/L6 implementation | Out of scope |
| Replay/UI lazy-load | Separate track |

---

## §2 — Objective (Option C)

### 2.1 Primary (solver / tests)

**A — `effective_mining_gain` only** for optimization and automated assertions.

```text
effective_mining_gain(candidate) = len(candidate.mining_occupied_cells)   # v2 unchanged
```

### 2.2 Secondary (observability)

**B — throughput** (e.g. `throughput_factor` sum) MAY be recorded on `Layer04RimPlacementResult.packing_observability` and projected into replay for Lab/benchmark. MUST NOT drive `EXACT_PACK` branch decisions in v2.0.

---

## §3 — Conflict graph

### 3.1 Nodes and edges

| Item | Contract |
|------|----------|
| Node | `RouteProbedBundleCandidate` with `route_probe_status == SUCCEEDED` |
| `occupied_cells` | `mining_occupied_cells \| transport_stub_cells` (same union as L4 v1 `select.py`) |
| Edge | Undirected edge when `occupied_cells(a) ∩ occupied_cells(b) ≠ ∅` |
| Forbidden | Building edges on `mining_occupied_cells` alone (misses stub conflicts) |

### 3.2 Components

Connected components of the overlap graph are **independent** for the additive objective in §4 (disjoint footprints between components).

### 3.3 Component processing order

Components MUST be processed in **ascending** lexicographic order of:

```text
(component_sort_key) = (
  min(anchor_y among nodes in C),
  min(anchor_x among nodes in C),
  min(candidate_id among nodes in C),
)
```

Rationale: spatially understandable order when `LayerBudgetContext` interrupts mid-pass.

---

## §4 — Set score

For a feasible non-overlapping set `S` of candidates within one component:

```text
set_score(S) — lexicographic (maximize):
  1. total_effective_mining_gain     = sum(effective_mining_gain(c))     DESC
  2. selected_count                  = |S|                              DESC
  3. total_route_cost                = sum(route_cost(entry))          ASC
  4. total_connector_goal_distance   = sum(connector_goal_distance(entry)) ASC
  5. selected_candidate_ids          = tuple(sorted(candidate_id))     ASC
```

Per-candidate `route_cost` and `connector_goal_distance` MUST use the same definitions as [`sort_keys.py`](../../../django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/sort_keys.py) today.

**Winner:** set with lexicographically greatest `set_score` among all non-overlapping subsets in the component (exact branch) or greedy fallback output (large component).

---

## §5 — Algorithm

### 5.1 Adopted approach — component-local capped exact optimizer

```text
1. Partition SUCCEEDED candidates into overlap connected components.
2. For each component C in component_sort_key order:
     if |C| <= MAX_EXACT_COMPONENT_SIZE:
       strategy = EXACT_PACK
       compute component_winner_set = maximum set_score independent set (§5.5)
     else:
       strategy = GREEDY_FALLBACK
       component_winner_set = output of L4 v1 greedy on nodes in C only
3. Materialize component_winner_set (§5.2) in global component order.
4. Build rejections for all candidates not materialized (§7.4).
```

**Normative constant:**

```text
MAX_EXACT_COMPONENT_SIZE = 20
```

Values in the 18–22 range MAY be tuned in implementation plans; default in code MUST be **20** unless this spec is amended.

### 5.2 Budget and materialization

**Logical selection vs physical materialization are separate phases.**

```text
L4 v2 computes each component_winner_set as a logical candidate set first (no budget).
Materialization then accepts winners in deterministic materialization order.

Materialization order (within one component_winner_set):
  ascending candidate_sort_key(entry) — same tuple as L4 v1 mining-first sort.

Global materialization order:
  components in component_sort_key order (§3.3);
  within each component, materialization order above.

Before each materialized placement:
  LayerBudgetContext.remaining_budget_ms() MUST be checked (same as L4 v1).
```

**Budget policy when materialization is interrupted:**

```text
If budget is exhausted during materialization:
- already materialized placements remain valid;
- remaining selected-but-not-materialized candidates receive BUDGET_INTERRUPTED;
- non-selected candidates in a component whose winner was fully computed receive
  PACKING_SET_LOSER (§7.4) with reason PHYSICAL_OVERLAP for wire compatibility;
- packing_observability MUST set budget_limited = true;
- packing_observability MUST set budget_interrupted_component_id when interruption
  occurs mid-component materialization.
```

A **partial materialized prefix** of a component winner is allowed under budget pressure; it is **not** required to remain `set_score`-optimal after truncation.

`GREEDY_FALLBACK` component winners are computed without budget; budget applies only at materialization (same as `EXACT_PACK`).

### 5.3 Rejected approaches

| Approach | Status |
|----------|--------|
| Full-pool MWIS | Non-goal (explosion risk) |
| Global greedy only (v1) | Superseded by this spec |
| Greedy + local replacement | Non-goal |

### 5.4 Fallback scope

`GREEDY_FALLBACK` MUST run **only on nodes in component C**, not on the global sorted pool. Inter-component greedy ordering MUST NOT contaminate fallback results.

### 5.5 Exact pack implementation bound

For `|C| <= MAX_EXACT_COMPONENT_SIZE` (20 nodes):

```text
MUST NOT use naive 2^|C| full enumeration without pruning.
MUST use conflict-aware search with pruning (bitset / adjacency mask + branch-and-bound
or DP on small |C|), using set_score upper bounds to cut branches.
```

Implementation plan MUST document the chosen algorithm and worst-case guard (node cap + branch limit).

`RimSelectionStrategy` MUST NOT add `EXACT_PACK_BUDGET_PARTIAL`; partial outcomes are expressed via `packing_observability.budget_limited` only.

---

## §6 — Core contracts

### 6.1 MUST

```text
L4 v2 MUST optimize candidate sets, not individual greedy order,
inside each conflict component (subject to MAX_EXACT_COMPONENT_SIZE and budget).

L4 v2 MUST NOT select a placement solely because it appears earlier in mining-first
greedy order when another non-overlapping subset in the same component has a higher set_score.

L4 v2 MUST use total_effective_mining_gain as the primary objective (§4).
```

### 6.2 MUST NOT

```text
MUST NOT use throughput_factor as the v2.0 primary objective.

MUST NOT perform route probe or L3 candidate regeneration in L4.

MUST NOT move component packing or provisional overlay materialization to L3.
```

### 6.3 L3 candidate fields required by L4 v2

L4 v2 MUST consume existing `RouteProbedBundleCandidate` / `BundleCandidate` fields without recomputation:

```text
candidate_id, anchor_coord, output_dir,
mining_occupied_cells, transport_stub_cells,
route_probe_status, route_probe_result (route_cost, goal_coord),
route_probe_start_coord,
intrinsic_priority_rank, equivalence_key, gene_key, transport_kind, resource_kind,
placements, throughput_factor (observability only)
```

---

## §7 — DTO and observability

### 7.1 `RimSelectionStrategy`

Path: `layers/contracts/rim_placement.py` (or adjacent enum module)

```python
class RimSelectionStrategy(StrEnum):
    EXACT_PACK = "EXACT_PACK"
    GREEDY_FALLBACK = "GREEDY_FALLBACK"
```

### 7.2 Per-component record

```python
@dataclass(frozen=True, slots=True)
class RimComponentSelectionRecord:
    component_id: str  # MUST be f"component_{ordinal:04d}" (ordinal from §3.3 sort, 0-based)
    component_sort_key: tuple[int, int, str]
    node_count: int
    selection_strategy: RimSelectionStrategy
    selected_candidate_ids: tuple[str, ...]  # logical winner set (may exceed materialized under budget)
    materialized_candidate_ids: tuple[str, ...]  # subset actually placed
    total_effective_mining_gain: int  # sum over logical winner set
    selected_count: int  # len(logical winner set)
```

### 7.3 `Layer04PackingObservability`

Attached to `Layer04RimPlacementResult` (authoritative wire). Replay segment **projects** a subset; replay is not source of truth.

```python
@dataclass(frozen=True, slots=True)
class Layer04PackingObservability:
    greedy_baseline_total_gain: int | None
    selected_total_gain: int
    greedy_baseline_throughput_factor_sum: int | None = None
    selected_throughput_factor_sum: int | None = None
    greedy_baseline_skipped_reason: str | None = None
    budget_limited: bool = False
    budget_interrupted_component_id: str | None = None
    component_records: tuple[RimComponentSelectionRecord, ...] = ()
```

**Greedy baseline (observability only):**

```text
greedy_baseline_* MUST be computed by running L4 v1 select_non_overlapping_candidates
on the same normal_candidates input with a cloned / synthetic non-consuming budget context.

It MUST NOT consume or mutate the runtime LayerBudgetContext used for committed L4 v2
materialization.

If baseline computation cannot finish within the observability budget envelope,
greedy_baseline_total_gain MAY be None and greedy_baseline_skipped_reason MUST be set.
```

Recommended: `LayerBudgetContext.from_budget_ms(observability_budget_ms)` with a fixed cap (e.g. 60_000 ms) independent of stack deadline; never call `remaining_budget_ms()` on the runtime ctx for baseline.

### 7.4 Rejection metadata (additive)

```python
class RimPackingRejectionKind(StrEnum):
    PACKING_SET_LOSER = "PACKING_SET_LOSER"
    BUDGET_INTERRUPTED = "BUDGET_INTERRUPTED"
    NON_SUCCEEDED_PROBE = "NON_SUCCEEDED_PROBE"
```

Existing `RimPlacementRejectReason` values remain for wire compatibility:

| Situation | `reason` | `packing_rejection_kind` |
|-----------|----------|---------------------------|
| EXACT_PACK loser in fully computed component | `PHYSICAL_OVERLAP` | `PACKING_SET_LOSER` |
| Budget during materialization | `BUDGET_INTERRUPTED` | `BUDGET_INTERRUPTED` |
| Failed probe | `NON_SUCCEEDED_PROBE` | `NON_SUCCEEDED_PROBE` |
| GREEDY_FALLBACK pairwise loser | `PHYSICAL_OVERLAP` | `PACKING_SET_LOSER` or omit (implementation MAY set for consistency) |

Additional fields on `RimPlacementRejection`:

```text
packing_component_id: str | None
packing_rejection_kind: RimPackingRejectionKind | None
winner_selected_due_to_higher_set_score: bool | None
```

For `PACKING_SET_LOSER`, `conflicting_winner_candidate_id` SHOULD reference one materialized or logical winner from the same component (deterministic: first in `materialized_candidate_ids`, else first in logical winner set).

`winner_selected_due_to_higher_mining_gain` (v1 pairwise) remains for backward-compatible replay.

Optional debug-only field (not contract-stable): `component_node_hash: str | None` — MUST NOT be used in tests or replay assertions.

---

## §8 — Replay

Per [`2026-05-28-layer-04-rim-bundle-placement-design.md`](2026-05-28-layer-04-rim-bundle-placement-design.md) §4:

```text
Layer04RimPlacementResult.packing_observability = authoritative
replay/layer04_segment.py = projection only (MUST NOT re-run packing)
```

New optional frame metadata keys (register in `event_types.py` when implementing):

```text
selection_strategy
packing_component_id
component_total_gain
greedy_baseline_total_gain
selected_total_gain
```

---

## §9 — Tests

### 9.1 Synthetic packing-density fixture (required)

Construct minimal `ReconstructionCompleteMap` + L2 plan + L3-normal pool stub:

```text
Blocker A: horizontal footprint, effective_mining_gain = 4, overlaps B..F
B, C, D, E, F: vertical footprints, each gain = 4, pairwise non-overlapping among B..F

Expected (EXACT_PACK component):
  selected = {B, C, D, E, F}
  total_effective_mining_gain = 20
  A not selected
```

### 9.2 Tie-break fixtures (required)

**9.2a — `selected_count`**

```text
Set X: total_gain = 12, selected_count = 2
Set Y: total_gain = 12, selected_count = 3
Expected: Y wins
```

**9.2b — `total_route_cost`**

```text
Set P and Set Q: total_gain = 8, selected_count = 2
Set P: total_route_cost = 20
Set Q: total_route_cost = 5
Expected: Q wins (lower route cost at same gain and count)
```

### 9.3 Fallback fixture (required)

```text
|C| > MAX_EXACT_COMPONENT_SIZE
Expected: selection_strategy == GREEDY_FALLBACK, deterministic across runs
```

### 9.4 Run #286 derived fixture (required)

Capture strip-derived conflict component from project 23 (or frozen JSON fixture).

```text
MUST NOT assert: S@(-6,11), S@(-5,11), S@(-4,11) all selected (mutual overlap).

MUST assert:
  selected set is pairwise non-overlapping on occupied_cells
  selected_total_gain >= greedy_baseline_total_gain
  (strict > preferred when fixture proves strict improvement)
```

### 9.5 Regression — corner W/S

Existing outer-rim corner W/S overlap fixture MUST still pass when W and S lie in the **same** conflict component (higher-gain direction wins via set_score, not sort order alone).

### 9.6 Layer boundary test

```text
L3 run on fixture: normal_candidates contains competing directions; no ProvisionalLayoutOverlay
L4 run: overlay non-empty when selections exist; L3 package MUST NOT import overlay builder
```

---

## §10 — Relation to outer-rim §8

[`2026-05-30-outer-rim-direction-arbitration-design.md`](2026-05-30-outer-rim-direction-arbitration-design.md) §8 listed MWIS escalation when:

1. Corner W/S fixture still fails after mining-first greedy — **addressed by #127** for pairwise same-component cases.
2. Repeated fixtures where medium placements beat one high-yield greedy choice — **this spec**.
3. Benchmark mining coverage regression from greedy — **this spec**.
4. Overlap graph exists and MWIS cost is low — **component-local cap satisfies (4) with bound |C|≤20**.

**Decision:** MWIS/packing is **no longer YAGNI** for bounded components; it is **L4 v2**, not an outer-rim follow-up.

---

## §11 — Implementation plan (out of band)

Implementation plan file MUST be created via **writing-plans** after this spec is approved:

```text
docs/superpowers/plans/2026-05-31-layer-04-v2-component-packing-optimizer.md
```

Suggested package layout:

```text
layer_04_rim_bundle_placement/
  conflict_graph.py      # nodes, edges, components
  set_score.py           # set_score + aggregates
  exact_pack.py          # |C| <= 20 MWIS / enumeration
  select_v2.py           # orchestration + budget
  select.py              # v1 greedy (fallback + baseline observability)
```

---

## Approval log

| Decision | Status |
|----------|--------|
| Objective Option C (A primary, B observability) | **APPROVED** (Placement Contract Architect, 2026-05-31) |
| Algorithm: component-local capped exact + greedy fallback | **APPROVED** |
| `MAX_EXACT_COMPONENT_SIZE = 20` + budget checks | **APPROVED** |
| Component order: `(min anchor_y, min anchor_x, min candidate_id)` | **APPROVED** |
| `packing_observability` on `Layer04RimPlacementResult` | **APPROVED** |
| L3 estimate / L4 install boundary | **APPROVED** |
| Blocking amendments (budget, component_id, baseline budget, PACKING_SET_LOSER) | **APPROVED** (2026-05-31) |
| Spec document | **APPROVED** |
