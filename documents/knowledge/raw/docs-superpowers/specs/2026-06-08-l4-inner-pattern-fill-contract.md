# L4-S0: Inner Pattern Fill Contract Spec

**Status:** APPROVED (L4-S0 contract closure, 2026-06-08)  
**Canonical slug:** `layer_04_inner_pattern_fill`  
**Implementation package (PR-2 rename pending):** `layer_05_inner_pattern_fill/`  
**Amends:** [`2026-05-31-layer-stack-l4-l5-renumber-design.md`](2026-05-31-layer-stack-l4-l5-renumber-design.md)

> **Numbering note:** Historical transport docs may label transport as “L4” or reference `layer_04_transport_routing/`. After the 2026-05-31 stack renumber, **canonical L4 is inner pattern fill** and **canonical L5 is transport routing** (`layer_05_transport_routing`). Transport spec PR tables (e.g. “L4-1 catalog import”) refer to **transport phases**, not inner-fill L4-1.

---

## 경계 (Hard Boundaries)

- **L4는 `layer_04_inner_pattern_fill`이다.** transport layer가 아니다.
- Sequence: L3 (rim placement) → **L4 (interior fill)** → L5 (transport routing) → L6 (commit validate).
- L4는 `Layer05RoutePlan`을 입력받지 않는다. L5가 A* transport authority.
- Output `interior_occupied_cells`는 L5에서 A* hard blocker로 소비된다.
- L4 score / coverage / corridor metrics are **potential score only** until L5/L6 confirmation. L4 must not claim routed throughput.

---

## Interior candidate definition (normative, L4-1)

### Formula

```text
L4-1 interior_candidates =
    complete_map.field_cells
    - l3_authoritative_equipment_footprint
```

`l3_authoritative_equipment_footprint` = committed L3 rim equipment field-cell footprint only (from `IntegratedRimGreedyResult` committed placements / authoritative equipment coords).

### Explicit exclusions (must NOT subtract from candidates)

The following are **not** authoritative equipment and must **not** be used to compute `interior_candidates`:

```text
L3 route_probe_path
L3 candidate_route_path
corridor witness overlays
replay overlays
transport probes
provisional_overlay.occupied_cells (if it mixes probe/witness cells)
```

**Invariant:**

```text
L3 equipment footprint = authoritative blocker for L4 candidate subtraction
L3 route_probe_path = witness only — never authoritative equipment
```

Implementers must not subtract `provisional_overlay.occupied_cells` wholesale when that set may include route-probe or witness cells.

### Corridor policy (Q1 — normative for L4-1)

- **Hard reservation forbidden:** L4 must not hard-reserve corridors via `interior_occupied_cells`.
- **Soft heuristic allowed:** L4 may compute `corridor_risk` and `corridor_shadow_cells` as metrics/diagnostics only.
- `corridor_shadow_cells` and `corridor_risk` must **not** be passed to L5 as hard block input.

### Corridor shadow invariants

```text
corridor_shadow_cells ∩ interior_occupied_cells = ∅
corridor_shadow_cells ∩ L5_hard_block_input = ∅
```

**Adapter prohibition:**

```text
No L5 adapter may merge corridor_shadow_cells into interior_occupied_cells.
```

---

## Contract: `interior_occupied_cells`

- **필수:** `interior_occupied_cells`는 field equipment footprint cell만 포함해야 한다.
- **금지(void/transport 오염):** void, corridor shadow, belt/pipe route cells, output route cells, route probe cells는 절대 넣지 말 것.
  - L5가 void cell을 block으로 인식하면 routing이 깨진다 (regression target: `INTERIOR_OCCUPIED_BLOCKED`).

**L5 dependency rule:** L5 consumes **only** `interior_occupied_cells` from L4. Optional metric fields (`corridor_shadow_cells`, `placements`, `metrics`) must not alter L5 walkable domain construction.

---

## DTO schema (forward-declare — production code in L4-1 Red phase)

Current stub: `Layer04InnerFillResult(interior_occupied_cells)` in `contracts/layer04_inner_fill.py`.  
Normative extended shape (frozen dataclasses when implemented):

### `InnerPlacement`

| Field | Type | Notes |
|-------|------|-------|
| `coord` | `Coord` | Anchor cell of placement |
| `pattern_id` | `str` | L4-1: `builtin_1x1_field_block` only |
| `rotation` | `int` | Degrees; `0` for 1×1 block |

### `Layer04FillMetrics`

| Field | Type | Notes |
|-------|------|-------|
| `interior_occupied_cell_count` | `int` | `len(interior_occupied_cells)` |
| `coverage_ratio` | `float` | See formula below |
| `corridor_risk` | `float` | Diagnostic; potential score only |
| `fragment_penalty` | `float` | Diagnostic; potential score only |
| `budget_interrupted` | `bool` | `true` when run ended early due to budget |

**`coverage_ratio` (normative):**

```text
coverage_ratio =
    len(interior_occupied_cells) / len(interior_candidates)

if len(interior_candidates) == 0:
    coverage_ratio = 0.0
```

**Forbidden denominators:**

```text
occupied / all field cells
occupied / golden_map_result cells
occupied / routeable cells
```

### `Layer04SkipReason` (enum)

| Value | Meaning |
|-------|---------|
| `NO_CANDIDATES` | `interior_candidates` empty after L3 subtract |
| `BUDGET_EXHAUSTED` | Budget ended with **zero** accepted placements |
| `MACRO_ONLY_DEFERRED` | Macro-only mode skip (L4-2+ open) |

`skip_reason` means **layer produced no usable result**. It is **not** used for partial fill.

### `Layer04InnerFillResult` (extended)

| Field | Type | L5 consumes? |
|-------|------|--------------|
| `interior_occupied_cells` | `frozenset[Coord]` | **Yes** (hard block) |
| `placements` | `tuple[InnerPlacement, ...]` | No |
| `metrics` | `Layer04FillMetrics` | No |
| `skip_reason` | `Layer04SkipReason \| None` | No |
| `corridor_shadow_cells` | `frozenset[Coord]` (optional) | **No** — metric only |

---

## Budget interrupt contract

Reuses L3 `LayerBudgetContext` interrupt pattern.

```text
skip_reason          = layer produced no usable result
metrics.budget_interrupted = run ended early due to budget
```

**Budget exhausted, zero placements:**

```text
skip_reason = BUDGET_EXHAUSTED
placements = ()
interior_occupied_cells = ∅
metrics.budget_interrupted = true
```

**Budget exhausted, one or more placements accepted (partial fill — valid result):**

```text
skip_reason = None
placements = accepted partial placements
interior_occupied_cells = accepted partial footprint
metrics.budget_interrupted = true
```

Partial fill is a **valid** L4 result. Do not encode partial fill via `skip_reason`.

---

## Tiny built-in pattern catalog (L4-1)

L4-1 uses a **resource-agnostic** built-in pattern. No `GeneCatalogSnapshot`.

| `pattern_id` | Footprint | Notes |
|--------------|-----------|-------|
| `builtin_1x1_field_block` | Single field cell | L4-1 only pattern |

**Forbidden in L4-1:** `builtin_1x1_shape` (implicit shape/fluid split — deferred to L4-3).

**L4-3 defer (not L4-1):**

```text
builtin_1x1_shape
builtin_1x1_fluid
gene_catalog_shape_bundle
gene_catalog_fluid_bundle
```

### Deterministic anchor scan order

Greedy placement scans `interior_candidates` in **coordinate lexicographic order**: ascending `(x, y)`.  
First feasible anchor wins per greedy step (L4-1 proof scope).

---

## L4-1 Implementation Scope (Greedy Prototype)

- **Pattern source:** `builtin_1x1_field_block` only. No `GeneCatalogSnapshot`.
- **Objective:** coverage maximizing + no-overlap with L3 authoritative footprint + corridor-risk guard (metric only).
- **Acceptance test 기준:**
  - `interior_occupied_cell_count >= 1` on fixture `golden_5x5_interior`
  - Each placed cell ∈ `interior_candidates`
  - No overlap with `l3_authoritative_equipment_footprint`
  - No void / transport / probe cell contamination in `interior_occupied_cells`
  - Budget interruption: partial fill safety per contract above

Detail: [`2026-06-08-l4-1-greedy-scope.md`](../plans/2026-06-08-l4-1-greedy-scope.md).

---

## Forbidden Assertions

- ❌ Full equality: `result == golden_map_result` (L4-1 forbidden; L4–L6 integration territory)
- ❌ Potential score / `coverage_ratio` treated as routed throughput
- ❌ `interior_occupied_cells` contains hard-reserved corridor cells
- ❌ `corridor_shadow_cells` merged into L5 hard block input
- ❌ L4 depends on `Layer05RoutePlan` as input

---

## L5 coupling failure semantics (reference for L4-1 tests)

| Failure | When |
|---------|------|
| `ROUTE_NOT_FOUND` | Search exhausted after domain excludes `interior_occupied_cells` |
| `INTERIOR_OCCUPIED_BLOCKED` | Commit/preflight validator rejects a proposed path cell |

Case “no alternate path” acceptance uses **`ROUTE_NOT_FOUND`**, not `INTERIOR_OCCUPIED_BLOCKED`. See L4-1 plan Case C.

---

## 미결정 사항 (Open Questions / L4-2+)

1. Interior gene catalog: L3와 동일 vs interior 전용? (L4-3)
2. Coverage target 고정 vs throughput envelope (L2) 기반?
3. Fluid field vs shape field fill rule 분리 (Q5 — L4-2+)
4. macro-only mode에서 L4 skip 여부
5. Pattern library / macro tiles (L4-2 beam)
