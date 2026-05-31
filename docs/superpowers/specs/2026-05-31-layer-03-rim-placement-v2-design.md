# Layer 03 Rim Placement v2 (DB-gene, two-phase hybrid) — Normative Design

**Status:** APPROVED (2026-05-31; 5 blocking + 2 minor amendments folded in — spec-first, no production code until checklist approval)
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

---

## Goal

Place mining bundles (genes from DB) on outer-rim field anchors so each bundle's output can route to an
L2 exterior trunk connector, maximizing routed rim throughput while keeping all equipment on the field
and the output stub/route in the void. The result is a **provisional** rim overlay for later layers.

## Non-goals

- Interior full-field fill or coverage optimization (L5).
- Final layout mutation / commit-validate (L6).
- Rim bundle packing role of L4 (remains disabled).
- Reproducing `golden_map_result` cell-for-cell (forbidden as an acceptance target; see Amendment 5).
- Any DB read or ORM import inside the core/CLI solver.

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
| R4 | Gene footprint is oriented from `canonical_output_dir = E` to the anchor's chosen output direction (subset of `void_dirs`). |
| R5 | **Immediate route probe** from `route_probe_start` to nearest matching trunk connector goal (belt=shape, pipe=fluid) decides pool membership. Reuse `shared/route_probe.py`. |
| R6 | Phase 1 produces candidates only — **no commit** (candidate ≠ commit invariant). |
| R7 | Commit-time **re-probe** on the latest `route_domain` (`RouteDomainSnapshotBuilder.build_snapshot`, canonical) finalizes survivors; candidate reachable ≠ final proof. |
| R8 | Provisional survivors populate `IntegratedRimGreedyResult.committed_placements` + overlay + metrics + replay events. Overlap count among survivors MUST be 0. |

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
overlap infeasible.

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
| Determinism | candidate ordering in solver frame (D1), selector consults fitness/conflict state rather than enumeration shortcut (D2), output hash stable (D4). |
| Finalize (Phase D) | commit-time re-probe drops infeasible, overlap count 0. |
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
