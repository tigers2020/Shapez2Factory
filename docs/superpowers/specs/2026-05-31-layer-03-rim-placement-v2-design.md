# Layer 03 Rim Placement v2 (DB-gene, two-phase hybrid) — Normative Design

**Status:** APPROVED (2026-05-31; 5 blocking + 2 minor + 1 contract amendment folded in — spec-first, no production code until checklist approval)
**Amendment 6 (2026-05-31):** Footprint transform contract — rotation/mirror are full-footprint rigid transforms (coords + `R` + ports), not orientation-only mutations. See §T.
**Date:** 2026-05-31
**Owner:** `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/`
**Supersedes (algorithm body only):** [`2026-05-31-layer-03-algorithm-reset-design.md`](2026-05-31-layer-03-algorithm-reset-design.md) (the reset stub it defines is the baseline this design replaces)
**Invariants:** [`.cursor/rules/asteroid-lab-invariants.mdc`](../../../.cursor/rules/asteroid-lab-invariants.mdc)

This document is the single source of truth for the from-scratch Layer 03 rim placement algorithm.
It consumes DB gene samples through a hexagonal `GeneCatalogSnapshot` boundary and uses a two-phase
hybrid (deterministic candidate pool + immediate route probe, then bounded selection/search) to
produce route-feasible provisional rim placements. The golden map fixtures are a quality benchmark,
not an equality target.

---

## Process gate (Amendment 1 — spec-first)

This design is a **planning draft for the spec**, not an implementation plan. No production code may
land before all three of the following complete, in order:

1. This normative spec is written.
2. The spec is reviewed and approved.
3. A phase-level implementation checklist is written and approved (`writing-plans`).

Until then, no edits under `src/shapez2_factory/**` or `django_apps/**` (other than this spec and the
plan/checklist documents).

---

## Decision record

| Choice | Value |
|--------|-------|
| Scope | **L3 rim-only** — outer-rim anchor scan, local pattern, output direction, immediate route feasibility, provisional `committed_placements`. No interior fill / coverage / final mutation (L4–L6 excluded). |
| Method | **Two-phase hybrid** — Phase 1 deterministic candidate + immediate route probe → normal pool; Phase 2 bounded selection/search over the pool. |
| Fitness | Maximize **routed throughput** minus predictive penalties (`route_cost`, shared corridor pressure). Overlap is a hard constraint, not a penalty. |
| Gene source | **DB `GeneticSample`** (all rows with `gene_key`) → `GeneCatalogSnapshot` → core L3 alleles. shape/fluid resolved by anchor field type. |
| Boundary | DB read **only** at Django adapter; core/CLI L3 never imports ORM. |
| Phase 2 staging | **C1 deterministic beam first**; C2 local search; C3 GA-lite optional/bounded/seed-stable (Amendment 4). |
| Benchmark | **L3-rim-only metrics** vs golden; full 1:1 golden match is L4–L6 territory (Amendment 5). |
| Footprint transform | **D4 over the full local footprint** (Amendment 6): a rotation/mirror variant transforms equipment coordinates + each building `R` + port/route-seed vectors together, then translates onto the world anchor. `R`-only mutation with unchanged coordinates is invalid. |

---

## Goal

Place mining bundles (genes from DB) on outer-rim field anchors so each bundle's output can route to an
L2 exterior trunk connector, maximizing routed rim throughput while keeping all equipment on the field
and the output stub/route in the void. The result is a **provisional** rim overlay for later layers.

## Non-goals

- Interior full-field fill or coverage optimization (L4 inner pattern fill).
- Final layout mutation / commit-validate (L6).
- Final transport routing (committed `SpaceBelt_*` / `SpacePipe_*` tiles, merge groups, transport replay authority) — **Layer 04** [`2026-05-31-layer-04-transport-routing-design.md`](2026-05-31-layer-04-transport-routing-design.md). L3 does not emit committed space transport tiles.
- Reproducing `golden_map_result` cell-for-cell (forbidden as an acceptance target; see Amendment 5).
- Any DB read or ORM import inside the core/CLI solver.

### Transport authority (L3 vs L4, 2026-05-31)

Layer 3 `route_probe_path`, route probe, and commit-time re-probe are **feasibility witnesses only**. They are not final transport placement, do not reserve transport cells for downstream layers, do not emit committed `SpaceBelt` / `SpacePipe` tiles, and must not be rendered as final transport in Lab replay.

Layer 4 transport routing (`layer_04_transport_routing`) is the **sole authority** for final belt/pipe route cells, transport groups, M-bundle capacity accounting, sprite/tile projection, and transport replay overlay.

## Work classification

`contract change` + `implementation change`. Tests authored first (red) per phase, then green.

---

## Behavior contract (normative)

### G — Gene catalog boundary (Amendment 2)

`GeneCatalogSnapshot` is a pure, immutable, JSON-serializable DTO produced by a Django adapter and
consumed by core L3. **Schema (normative):**

Top level:

- `schema_version: str` — e.g. `"gene_catalog_v1"`. Core rejects unknown major versions.
- `generated_at: str` — ISO-8601 UTC of serialization.
- `provenance_hash: str` — stable hash over sorted entries + `source_batch_id`.
- `source_batch_id: str` — generator/seed batch identifier (e.g. exhaustive generator version, or a
  composite when miner-seed rows are included).
- `deterministic_sort_key: str` — names the canonical entry ordering rule (e.g.
  `"by_gene_id_then_throughput_desc"`); entries MUST already be sorted by it.
- `entries: tuple[GeneCatalogEntry, ...]`.

Per `GeneCatalogEntry`:

- `gene_id: str` — stable identity (from `gene_key`).
- `resource_kind: str` — `"shape" | "fluid" | "both"`. Resolves which field type an entry may anchor on.
- `canonical_output_dir: str` — MUST be present (canonical `"E"`). **Mandatory:** without it the
  E/N/W/S rotation contract is undefined (this was the prior reset's fragility).
- `occupied_offsets: tuple[tuple[int, int], ...]` — canonical-frame equipment footprint.
- `extractor_offset: tuple[int, int]` — canonical `(0, 0)`.
- `extension_offsets: tuple[tuple[int, int], ...]`.
- `output_stub_offset: tuple[int, int]` — canonical `(1, 0)`; void-side output cell.
- `route_probe_start_offset: tuple[int, int]` — canonical `(2, 0)`; first route cell beyond the stub.
- `throughput_factor: int` — one of `{4, 8, 12, 16}`.
- `topology_signature_base: str`.

Rules:

| ID | Rule |
|----|------|
| G1 | Core `GeneCatalogSnapshot.from_payload(dict)` validates schema_version, required fields, offset shapes, `throughput_factor ∈ {4,8,12,16}`, and `canonical_output_dir == "E"`. |
| G2 | The Django serializer is the **only** place that reads ORM (`GeneticSample`). Core/CLI receive the snapshot via CLI `--gene-catalog <path>` (mirrors `--snapshot` for game data). |
| G3 | Entries arrive already sorted by `deterministic_sort_key`; core does not re-sort by nondeterministic keys. |
| G4 | The snapshot is persisted at `input/gene_catalog.json` in the artifact and recorded in the manifest `paths` for provenance. |
| G5 | Genes are algorithm **input** (allowed). Replay/metrics/artifacts MUST NOT feed back as input. |
| G6 | `extractor_offset` MUST be `(0, 0)`. Non-zero values are **invalid** at snapshot parse and L3 expansion (core projects `extractor_cell = rim anchor`). |

### M — Missing / invalid gene catalog (Amendment 3)

Add to `Layer03SkipReason`:

```python
MISSING_GENE_CATALOG = "missing_gene_catalog"
INVALID_GENE_CATALOG = "invalid_gene_catalog"
```

| ID | Rule |
|----|------|
| M1 | If `gene_catalog` is absent or has zero usable entries → L3 returns `build_empty_integrated_rim_greedy_result(layer_skip_reason=MISSING_GENE_CATALOG, ...)`. |
| M2 | If `gene_catalog` payload fails `from_payload` validation → L3 returns empty with `INVALID_GENE_CATALOG`. |
| M3 | **No synthetic genes** are ever fabricated by core; **no DB read from core** under any condition. |
| M4 | `exterior_plan is None` continues to return `MISSING_EXTERIOR_CONNECTION_PLAN` (unchanged), and budget-exhausted continues existing skip behavior. Precedence: exterior-plan gate → gene-catalog gate → run. |

### R — Rim placement contract

| ID | Rule |
|----|------|
| R1 | Rim anchors = field cells adjacent to external void; each carries `void_dirs`. |
| R2 | Equipment (extractor + extensions) ⊆ `field_cells` of the **matching resource type** (shape entry on shape field, fluid on fluid field; `both` may anchor on either). |
| R3 | Output stub ⊆ external void; route may cross field but field is costed higher than void; committed equipment is a hard blocker. |
| R4 | Gene footprint is **rigidly transformed** (full-footprint D4) from `canonical_output_dir = E` to the anchor's chosen output direction (subset of `void_dirs`). See **§T**. Orientation-only mutation (changing building `R`/`output_dir` while equipment coordinates stay fixed) is forbidden. |
| R5 | **Immediate route probe** from `route_probe_start` to nearest matching trunk connector goal (belt=shape, pipe=fluid) decides pool membership. Reuse `shared/route_probe.py`. |
| R6 | Phase 1 produces candidates only — **no commit** (candidate ≠ commit invariant). |
| R7 | Commit-time **re-probe** on the latest `route_domain` (`RouteDomainSnapshotBuilder.build_snapshot`, canonical) finalizes survivors; candidate reachable ≠ final proof. |
| R8 | Provisional survivors populate `IntegratedRimGreedyResult.committed_placements` + overlay + metrics + replay events. Overlap count among survivors MUST be 0. |

### RC — Route merge / routed throughput (corridor sharing)

Same-kind pipe/belt route overlap is **merge/share-capable** and MUST NOT hard-reject.

Routed throughput is the sum of each committed bundle's `throughput_factor`. When multiple bundles
share a corridor toward the same exterior trunk, their producer throughputs aggregate on that trunk as
**merge semantics**. This aggregation is represented by summing committed bundle `throughput_factor`
values, not by double-counting shared corridor cells.

Shared corridor cells MAY contribute **soft** corridor pressure / congestion penalty (Phase C1 fitness),
but they do not create additional throughput beyond the contributing producers.

| ID | Rule |
|----|------|
| RC1 | **Equipment overlap** (miner, extension, transport stub) and **rim-platform invasion** are hard rejection. **Corridor / void-trunk overlap alone** is NOT hard rejection. |
| RC2 | `total_throughput` / `pass2_score` / `routed_rim_throughput` = `Σ throughput_factor` over committed (selected) bundles — one term per producer, regardless of shared corridor cells. |
| RC3 | Shared corridor cells MUST NOT add extra `throughput_factor` per overlapped cell (no cell-level double-count). |
| RC4 | `SHAPE_BELT` and `FLUID_PIPE` use separate route domains; cross-kind corridor merge is forbidden. |
| RC5 | L3 routed throughput sums producer `throughput_factor`; L2 exterior connector saturation caps and L5/L6 validation are separate layers (do not conflate pass2 score with EVTC `/min` caps). |

> Korean (reviewer note): 같은 종류 belt/pipe corridor overlap은 hard reject가 아니다. 여러 bundle이 같은
> exterior trunk로 합류하면 각 producer의 `throughput_factor`가 routed throughput에 한 번씩 누적된다. 겹친
> corridor 셀 자체를 기준으로 throughput을 추가 가산하지 않는다. shared corridor는 soft
> pressure/congestion penalty로만 사용한다.

### T — Footprint transform contract (Amendment 6)

A direction/mirror variant is a **rigid transform of the entire miner-relative footprint**, not an
orientation-only change. The earlier "orientation variant" framing (mutate `R` / `output_dir` only) is
**rejected**. For every equipment item in a variant: `kind`/type is preserved; local coordinate
`(dx, dy)` relative to the miner anchor is rotated/reflected; building rotation `R` is
rotated/reflected; output/input port vectors and route-seed directions are rotated/reflected; the
transformed local coordinates are then translated onto the world anchor.

Transform math (solver frame is **y-down**: +x East, +y South; canonical base orientation East, `R = 0`):

```
rotate_xy(dx, dy, k):        # k = clockwise quarter-turns
  k == 0 -> ( dx,  dy)
  k == 1 -> (-dy,  dx)       # 90°  CW
  k == 2 -> (-dx, -dy)       # 180°
  k == 3 -> ( dy, -dx)       # 270° CW
rotate_r(r, k) = (r + k) % 4
edge -> k:  east = 0, south = 1, west = 2, north = 3
```

Mirror is a **separate** transform (not expressible as a rotation):

```
mirror_x(dx, dy) = (-dx,  dy)   # reflect across vertical axis:   East <-> West, N/S fixed
mirror_y(dx, dy) = ( dx, -dy)   # reflect across horizontal axis:  North <-> South, E/W fixed
```

`R` / port directions reflect with the chosen axis.

| ID | Rule |
|----|------|
| T1 | Variants are the **D4 group** over the full footprint (4 rotations × optional mirror), applied to coords + `R` + ports together. |
| T2 | `R`-only / `output_dir`-only mutation with unchanged equipment coordinates is **invalid** and MUST be rejected (sole exception: a genuinely single-cell, coordinate-invariant building). |
| T3 | Variants are **deduplicated only after full footprint normalization** (post-transform canonicalization). Asymmetric / corner layouts keep mirror and rotation as distinct candidates; `180° rotation ≠ mirror`. |
| T4 | The `rotation` stored on each placement is the transformed `R = rotate_r(base_R, k)` with canonical `base_R = 0` (East) — **not** the NESW ordering rank used by D1. |
| T5 | Test-locked vectors (canonical-East extensions left of the miner, `M = (0,0)`): `E→S` maps `(-n, 0) → (0, -n)`; `E→W` maps `(-n, 0) → (n, 0)`; `E→N` maps `(-n, 0) → (0, n)`. |
| T6 | **Variant enumeration:** core B2 emits the full **D4 set** (4 rotations × {identity, mirror}) of each gene footprint, deduplicated after full normalization (T3). The Django serializer/snapshot keeps the **canonical-East 18 entries** only; expansion happens in core. |
| T7 | **Independent extractor output:** a candidate is `anchor × gene × bundle_orientation × output_side`. `output_side` is any of the extractor's 4 sides **not occupied by an extension cell** in that orientation **and** whose stub cell lies in external void (R3). The **miner** `R = rotate_r(0, output_side_k)`; **extensions** keep `R = rotate_r(0, orientation_k)` (bundle orientation). Per-placement `R` may therefore differ. |

> `assumption:` `GeneCatalogEntry` currently carries no per-building base `R`; all bundle buildings are
> taken as canonical-East `base_R = 0`. Extension `R` follows the bundle orientation; the miner `R`
> follows its independent output side (T7). If a future entry needs heterogeneous base `R`, the schema
> must add a per-cell `r` and `rotate_r` applies per cell.

### D — Determinism (Amendment 4 ordering)

| ID | Rule |
|----|------|
| D1 | **Candidate ordering** is fully deterministic: sort by `(anchor_row, anchor_col, output_dir_rank, -throughput_factor, gene_id)`. `anchor_row`/`anchor_col` are derived from the **canonical solver coordinate frame** used by `ReconstructionCompleteMap`, **not** Lab-render dense coordinates. No raw↔screen or dense projection coordinates may participate in candidate ordering. This ordering is normative and test-locked. |
| D2 | Candidate **enumeration order MUST NOT be used as the sole commit selector**. Commit order is derived from the Phase 2 selector's score/conflict state. Tests prove the selector consults fitness/conflict state (not merely that enumeration order and commit order differ — they may coincide when the pool is trivial). |
| D3 | Any RNG (only in C3) is **seed-stable hash** based; unseeded `random`/`uuid4` forbidden. |
| D4 | Same `(complete_map, exterior_plan, gene_catalog, seed)` → identical output hash. |

### Phase 2 staging (Amendment 4)

- **C1 — deterministic beam selector (MVP):** beam/greedy selection over the normal pool maximizing
  fitness with overlap as a hard constraint. **v2 MVP ships at C1.**
- **C2 — local search:** deterministic neighborhood moves (swap gene variant / drop / add at an anchor)
  to improve fitness; bounded iterations.
- **C3 — GA-lite (optional, bounded, seed-stable):** small population, bounded generations, seed-stable
  operators. Added only after C1/C2 regression baselines exist.

Genome (C2/C3): anchor-indexed allele (each rim anchor → chosen gene variant or none).
Fitness: `Σ throughput_factor(selected) − route_fragility_penalty − shared_corridor_pressure_penalty`;
overlap infeasible. See **§RC** for merge/share vs cell double-count: routed throughput sums producer
`throughput_factor` once each; shared corridor cells affect soft pressure only, not per-cell TF addition.

### Preserved stack surface

`LAYER_03_RIM_GREEDY_PLACEMENT` slug + index 3; `IntegratedRimGreedyResult`, `RimGreedyMetrics`,
`Layer03AppendResult` DTOs; `build_empty_*` builders; replay phase identity; stack/run registration.

---

## Test contract

### L3-rim-only benchmark metrics (Amendment 5)

Acceptance metrics for L3 alone (oracle = [`golden_map_origin.txt`](../../../tests/fixtures/asteroid_lab/golden_map_origin.txt) /
[`golden_map_result.txt`](../../../tests/fixtures/asteroid_lab/golden_map_result.txt)):

- `routed_rim_throughput` — sum of throughput_factor over route-feasible committed rim placements.
- `committed_rim_placement_count`.
- `route_feasible_output_count`.
- `invalid_overlap_count == 0` (hard).
- `deterministic_output_hash` stable across repeated runs.

**Forbidden acceptance assertions:**

- "L3 result must equal `golden_map_result`."
- "L3 must reach full golden throughput."

Golden is used only as an upper-bound sanity check (`routed_rim_throughput ≤ golden total`) and a
non-regression floor (`≥ deterministic beam baseline`).

### Test classes

| Class | Action |
|-------|--------|
| Gene catalog boundary | `GeneCatalogSnapshot.from_payload` round-trip; reject bad schema_version / missing `canonical_output_dir` / bad throughput_factor. |
| Missing/invalid catalog | empty → `MISSING_GENE_CATALOG`; invalid payload → `INVALID_GENE_CATALOG`; no synthetic genes; no core ORM import. |
| Candidate (Phase 1) | equipment-in-field, stub-in-void, immediate-route-feasible pool membership, candidate ≠ commit. |
| Footprint transform (§T) | `E→S`/`E→W`/`E→N` rotate the full footprint (T5 vectors); placement `R == (base_R + k) % 4` (T4); a candidate with mutated `R` but unchanged coordinates is rejected (T2); mirror ≠ rotation for an asymmetric layout (T3). |
| Determinism | candidate ordering in solver frame (D1), selector consults fitness/conflict state rather than enumeration shortcut (D2), output hash stable (D4). |
| Finalize (Phase D) | commit-time re-probe drops infeasible, overlap count 0. |
| Route merge (§RC) | `test_shared_corridor_is_a_penalty_not_a_hard_constraint`; `test_finalize_two_corridor_sharing_bundles_both_commit`; `test_shared_corridor_does_not_double_count_throughput_by_cell_overlap`. |
| Benchmark | L3-rim-only metrics on golden origin within bounds. |
| Architecture gate | core L3 / CLI import no ORM (extend existing no-core-import gate). |

---

## Acceptance matrix

| ID | Check |
|----|-------|
| A1 | `GeneCatalogSnapshot` round-trip + validation tests pass. |
| A2 | Missing/invalid catalog returns correct `Layer03SkipReason`; no synthetic genes; no core DB read. |
| A3 | Phase 1 pool: equipment-in-field, stub-in-void, route-feasible only; no commit. |
| A4 | Deterministic candidate ordering (D1) and stable output hash (D4) locked. |
| A5 | Commit-time re-probe finalize: `invalid_overlap_count == 0`. |
| A6 | L3-rim-only benchmark metrics computed; `routed_rim_throughput ≤ golden total` and `≥ beam baseline`. |
| A7 | Core/CLI L3 imports no ORM (architecture gate green). |
| A8 | `ruff check` on touched paths clean. |
| A9 | Footprint transform (§T): T5 rotation vectors locked, placement `R = (base+k)%4` (T4), R-only-unchanged-coords rejected (T2), mirror distinct from rotation for asymmetric layout (T3). |

---

## Files (anticipated)

- `src/shapez2_factory/adapters/asteroid_lab/gene_catalog_snapshot.py` — `GeneCatalogSnapshot.from_payload`.
- `django_apps/asteroid_lab/services/genetic_sample_catalog_snapshot.py` — ORM → snapshot serializer.
- `django_apps/asteroid_lab/services/solver_subprocess_runner.py` — `gene_catalog` field, `--gene-catalog`.
- `django_apps/asteroid_lab/services/solver_runtime_entry.py` — build + inject snapshot.
- `src/shapez2_factory/interfaces/cli/asteroid_solve.py` — `--gene-catalog` arg + threading + artifact persist.
- `src/shapez2_factory/application/asteroid_lab/run_stack.py`, `stack_runner.py` — thread `gene_catalog` to L3.
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/` — candidate gen, beam selector, finalize.
- `src/shapez2_factory/application/asteroid_lab/layers/contracts/candidates.py` — `Layer03SkipReason` enum additions.

## Risks

- `uncertain:` exact penalty weights (`route_fragility`, `shared_corridor_pressure`) — start conservative, tune against beam baseline.
- `assumption:` miner-seed `gene_key`s can be serialized into the catalog alongside exhaustive keys (current export path is exhaustive-cache only; serializer must be extended).
- `invariant:` core must not import ORM; gene catalog flows only via snapshot file.

## Next step

After spec approval, invoke `writing-plans` to produce
`docs/superpowers/plans/2026-05-31-layer-03-rim-placement-v2/` with a phase-level checklist
(Phase A wiring → Phase B candidates → Phase C1 beam → finalize → benchmark; C2/C3 deferred).
**No production code until the checklist is approved.**
