# L4-1 Scope: Deterministic Greedy Inner Fill

**Canonical contract:** [`2026-06-08-l4-inner-pattern-fill-contract.md`](../specs/2026-06-08-l4-inner-pattern-fill-contract.md)  
**Prerequisite:** L4-S0 contract closure complete (this document).  
**Phase:** L4-1 implementation — TDD red → green (separate execution cycle from L4-S0).

---

## In-Scope for L4-1

- Deterministic tiny built-in pattern: `builtin_1x1_field_block` only (no `GeneCatalogSnapshot`)
- Greedy scan over `interior_candidates` in coord lex order `(x, y)` ascending
- Hard constraint: `interior_occupied_cells` ⊆ field equipment footprint only (void/transport/probe contamination forbidden)
- Overlap check vs `l3_authoritative_equipment_footprint` (not wholesale `provisional_overlay.occupied_cells`)
- `budget_interrupt` → partial fill safety; `budget_interrupted` metric vs `skip_reason` separation per contract
- `coverage_ratio` with denominator `len(interior_candidates)`

## Out-of-Scope for L4-1

- `GeneCatalogSnapshot` integration (deferred to L4-3)
- `builtin_1x1_shape` / fluid-shape split (L4-3)
- Coverage benchmark vs `golden_map_result` (equality assertion forbidden)
- Corridor hard reservation via `interior_occupied_cells`
- `corridor_shadow_cells` passed to L5
- Fluid/shape field split rules (open question L4-2+)
- Full replay segment for `layer_04_frames`

---

## Fixture contract: `golden_5x5_interior`

**Base map:** `golden_5x5_complete_map()` from `tests/unit/asteroid_lab/layers/fixtures/layer_03_golden_map.py` — field origin `(2,2)`, size 5×5, coords `x,y ∈ [2,6]`.

### ASCII topology

```text
golden_5x5_interior topology (y increases upward; field x,y ∈ [2,6]):

  6  I R R R I
  5  R I I I R
  4  R I I I R
  3  R I I I R
  2  I R R R I
     2 3 4 5 6

R = L3 authoritative equipment footprint (fixture-frozen, 12 cells)
I = interior_candidate = field_cell − R (13 cells: 4 rim corners + 3×3 center)
```

### Legend (normative)

```text
interior_candidates = complete_map.field_cells − l3_authoritative_equipment_footprint
L4-1 minimum assertion: len(interior_occupied_cells) >= 1
Each placed cell MUST be ∈ interior_candidates
L4-1 does NOT require filling all I cells — only ≥1 placement proof
```

### Frozen coordinates

```python
l3_authoritative_equipment_footprint = frozenset({
    (2, 3), (2, 4), (2, 5),   # west rim column
    (6, 3), (6, 4), (6, 5),   # east rim column
    (3, 2), (4, 2), (5, 2),   # south rim row
    (3, 6), (4, 6), (5, 6),   # north rim row
})

interior_candidates = frozenset({
    # rim corners (4)
    (2, 2), (6, 2), (2, 6), (6, 6),
    # center 3×3 (9)
    (3, 3), (4, 3), (5, 3),
    (3, 4), (4, 4), (5, 4),
    (3, 5), (4, 5), (5, 5),
})  # |interior_candidates| == 13
```

**Implementation note:** Fixture module `tests/unit/asteroid_lab/layers/fixtures/layer_04_interior_golden.py` (L4-1 Red phase) must freeze these coords — no “programmatic rim 1–2 placements”.

---

## L4-1 Acceptance Tests (golden_5x5_interior)

- [ ] `len(interior_occupied_cells) >= 1`
- [ ] `interior_occupied_cells ⊆ interior_candidates`
- [ ] `interior_occupied_cells ∩ l3_authoritative_equipment_footprint == ∅`
- [ ] `interior_occupied_cells ∩ complete_map.external_void_cells == ∅`
- [ ] No route_probe / belt / pipe cell in `interior_occupied_cells`
- [ ] `coverage_ratio == len(interior_occupied_cells) / 13` (when candidates non-empty)
- [ ] `budget_interrupt` partial fill: accepted placements retained; `skip_reason is None`; `metrics.budget_interrupted is True`

---

## L5 coupling regression (reuse existing fixtures)

Fixture: `tests/unit/asteroid_lab/layers/fixtures/l5_l4_occupancy_barrier.py`  
Existing tests: `tests/unit/asteroid_lab/layers/test_layer05_l4_interior_occupancy.py`

**Do not use `or reroute` / `or INTERIOR_OCCUPIED_BLOCKED` as a single assertion.**

### Case A — hard block (domain)

| Given | Expected |
|-------|----------|
| Route would cross `interior_occupied` cell | `interior_occupied` cell ∉ `domain.walkable_cells` |

Aligns with: `test_l5_interior_block_excluded_from_walkable_domain`, `test_l5_blocks_l4_interior_occupied_cell`.

### Case B — reroute (alternate void path)

| Given | Expected |
|-------|----------|
| `l5_l4_occupancy_barrier_basic_map()`; interior blocks choke only; `L5_L4_SOUTH_DETOUR` available | `len(routes) == 1`; `L5_L4_CHOKE_VOID ∉ path_coords`; detour path used |

Aligns with: `test_l5_reroutes_around_l4_interior_occupied_cell`.

### Case C — no alternate path (search failure)

| Given | Expected |
|-------|----------|
| `l5_l4_occupancy_barrier_no_detour_map()`; interior blocks all void paths | `routes == ()`; `failures[0].reason == ROUTE_NOT_FOUND`; `"blocked_by_l4_interior_count=" in failures[0].detail` |

**Case C uses `ROUTE_NOT_FOUND` only** — not `INTERIOR_OCCUPIED_BLOCKED` (preflight validator failure).

Aligns with: `test_l5_route_not_found_when_l4_blocks_all_paths`.

### Failure enum split (normative)

```text
ROUTE_NOT_FOUND           = search exhausted after domain excludes interior_occupied cells
INTERIOR_OCCUPIED_BLOCKED = commit/preflight validator rejects a proposed path cell
```

---

## Forbidden Assertions

- ❌ `result == golden_map_result`
- ❌ L4 `coverage_ratio` or potential score == routed throughput
- ❌ L4 consumes `Layer05RoutePlan`
- ❌ `corridor_shadow_cells` passed as L5 hard blocker
- ❌ `interior_occupied_cells` contains void / belt / pipe / route_probe cells
- ❌ Case C expects `INTERIOR_OCCUPIED_BLOCKED` when testing search exhaustion
- ❌ Ambiguous `or reroute` single assertion for L5 coupling

---

## TDD Task Breakdown (L4-1 execution — not L4-S0)

1. **Fixture:** `tests/unit/asteroid_lab/layers/fixtures/layer_04_interior_golden.py` — frozen coords above + `provisional_overlay` / L3 seed builder
2. **Red:** `tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py` — acceptance list above
3. **Red:** Extend DTO in `contracts/layer04_inner_fill.py` per spec schema
4. **Green:** `run_layer_04_inner_pattern_fill` greedy (`builtin_1x1_field_block`, lex scan)
5. **Regression:** L5 Case A/B/C remain green on `test_layer05_l4_interior_occupancy.py`

---

## Verification (PR gate — per `AGENTS.md`)

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py -v
python -m pytest tests/unit/asteroid_lab/layers/test_layer05_l4_interior_occupancy.py -v
python -m pytest tests/unit/asteroid_lab/layers/test_layer04_inner_fill_stub.py -v
powershell -File scripts/test_fast.ps1
ruff check .
mypy django_apps config src
black --check .
```
