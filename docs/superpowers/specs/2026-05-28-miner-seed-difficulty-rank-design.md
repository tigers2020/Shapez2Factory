# Miner Seed Difficulty Rank — Design Spec

**Status:** Approved (contract review 2026-05-28: `compactness_approx`, `difficulty_score: int`, dry-run ambiguity)  
**Date:** 2026-05-28  
**Track:** Asteroid Lab `GeneticSample` miner seed metadata (follow-up to miner seed v2 equivalence)  
**Work classification:** Contract change (metadata only; no bootstrap reorder)

**Related:**

- Parent catalog: [`2026-05-28-miner-seed-19-equivalence-design.md`](2026-05-28-miner-seed-19-equivalence-design.md)
- Decontamination (legacy rank semantics): [`2026-05-28-miner-seed-decontamination-design.md`](2026-05-28-miner-seed-decontamination-design.md)
- Fitness / map placement (deferred): [`documents/Algorithm/asteroid_lab_05_genome_fitness.md`](../../../documents/Algorithm/asteroid_lab_05_genome_fitness.md)

---

## §1 — Problem and goals

### Problem

`metadata_json.seed_rank` is assigned as **bootstrap line index** (`enumerate(EXPECTED_PATTERN_IDS)`). It is stable for admin/replay but **does not** encode:

- Install simplicity (flat footprint, low branch/turn complexity)
- Pattern-only compactness proxy (not map coverage)
- Curriculum ordering distinct from raw extension count

Using `seed_rank` as “difficulty” or “GA try order” causes drift between catalog stability and solver pedagogy.

### Goals

| Goal | Contract |
|------|----------|
| Preserve catalog stability | `seed_rank` unchanged = `catalog_rank` ≡ bootstrap `line_no` |
| Add intrinsic difficulty | `difficulty_score`, `difficulty_rank`, `difficulty_tier`, `rank_reason` at ingest |
| Defer map-aware priority | `search_priority_rank` null until Phase 5 fitness DTO exists |
| Determinism | Same decoded root → same score; full catalog resort is ingest-global |
| No catalog identity change | `gene_key`, `equivalence_signature`, bootstrap line order **unchanged** |

### Non-goals

- Reordering `var/default_miner_pattern.txt` or `EXPECTED_PATTERN_IDS`
- Using difficulty rank as solver commit order or probe gate
- Map-level coverage probes (candidate generation / fitness)
- Fluid-specific seed rows (shape-only catalog unchanged)
- Implementing `FitnessBreakdown` / `route_fragility_penalty` in this track

---

## §2 — Field separation (metadata contract)

### 2.1 Aliases and consumers

| Field | Alias | Writer | Readers |
|-------|-------|--------|---------|
| `seed_rank` | `catalog_rank` | `seed_miner_patterns` (fixed zip order) | Admin default sort, bootstrap `line_no`, replay/debug |
| `difficulty_score` | — | ingest scorer (`int`, v1 integer-valued formula) | Admin column, curriculum docs, tests |
| `difficulty_rank` | — | ingest (global sort 1..18) | Gene picker / future GA initialization |
| `difficulty_tier` | — | ingest (derived) | UI grouping, coarse curriculum |
| `rank_reason` | — | ingest (breakdown) | Debug, golden tests |
| `search_priority_rank` | — | **null** in this track | Phase 5+: map-aware gene try order |
| `search_priority_source` | — | `"deferred_phase5"` | Explains null rank |

**Forbidden:** Treating `seed_rank` as difficulty, throughput sort key, or solver commit sequence.

### 2.2 Extended `miner_seed_v2` metadata example

```json
{
  "schema": "miner_seed_v2",
  "is_seed": true,
  "seed_rank": 7,
  "pattern_id": "m3e_01",
  "difficulty_score": 337,
  "difficulty_rank": 7,
  "difficulty_tier": 4,
  "rank_reason": {
    "extension_count": 3,
    "occupied_cell_count": 4,
    "bbox_width": 4,
    "bbox_height": 1,
    "bbox_area": 4,
    "max_span": 4,
    "branch_count": 0,
    "turn_count": 0,
    "linear_chain_bonus": 15,
    "throughput_soft_penalty": 12,
    "compactness_approx": 1.0
  },
  "search_priority_rank": null,
  "search_priority_source": "deferred_phase5",
  "extension_count": 3,
  "throughput_factor": 16,
  "equivalence_signature": "<hex>",
  "topology_signature": "<hex>",
  "resource_kind_stored": "shape",
  "layout_types": ["Layout_ShapeMiner", "Layout_ShapeMinerExtension", "SpaceBelt_Forward"]
}
```

`throughput_factor` remains `4 × (1 + extension_count)` — game contract unchanged.

---

## §3 — Intrinsic difficulty scorer

### 3.1 Module boundary

New pure module (proposed path):

`django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py`

- **Inputs:** decoded `BP.Entries` root (post-strict validation)
- **Outputs:** `IntrinsicDifficultyResult` dataclass: `score`, `tier`, `reason` dict
- **Reuses:** `_equipment_nodes`, `_parent_edges_bfs` from `miner_seed_equivalence` (export shared helpers or import private BFS — prefer **shared** `miner_seed_parent_tree.py` if import cycles appear)

**Excluded from score:** belt cells, miner `R`, raw extension `R` (same as equivalence signature policy).

### 3.2 Feature definitions

Equipment cells = miner + extensions (island-local `X`/`Y`).

| Feature | Definition |
|---------|------------|
| `occupied_cell_count` | `len(equipment nodes)` |
| `bbox_*` | `island_bbox_from_xy_dicts` over equipment coords |
| `bbox_area` | `width × height` |
| `max_span` | `max(width, height)` |
| `branch_count` | Equipment nodes with **>1 child** in BFS parent tree (miner root) |
| `turn_count` | Sum over leaves: direction changes along miner→leaf path |
| `linear_chain` | `extension_count > 0` and `branch_count == 0` |
| `compactness_approx` | `occupied_cell_count / bbox_area` (pattern-only **density** proxy; not map coverage) |
| `throughput_soft_penalty` | `min(throughput_factor × 2, 12)` |

### 3.3 Score formula (lower = easier)

```text
difficulty_score: int =
    extension_count × 100
  + occupied_cell_count × 8
  + bbox_area × 5
  + max_span × 3
  + branch_count × 25
  + turn_count × 10
  - linear_chain_bonus        # 15 if linear_chain else 0
  - throughput_soft_penalty   # min(throughput_factor × 2, 12)
```

All operands are integers; result is always an `int` (no floats in `difficulty_score`).
`compactness_approx` in `rank_reason` may be a `float` (ratio).

No `output_axis_conflict_penalty` in v1 — strict ingest already rejects extensions on miner forward cell; keeps scorer aligned with validated seeds only.

### 3.4 Tier assignment

| `difficulty_tier` | Rule |
|-------------------|------|
| 0 | `extension_count == 0` |
| 1 | `extension_count == 1` |
| 2 | `extension_count == 2` and `branch_count == 0` |
| 3 | `extension_count == 2` and `branch_count >= 1` |
| 4 | `extension_count == 3` and `branch_count == 0` and `turn_count <= 1` |
| 5 | `extension_count == 3` and (`branch_count >= 1` or `turn_count >= 2`) |

Throughput does **not** set tier; it only affects score via capped soft penalty.

### 3.5 Global `difficulty_rank` assignment

After scoring all 18 bootstrap patterns in one ingest run:

```python
sort_key = (
    difficulty_tier,      # ascending
    difficulty_score,     # ascending
    -compactness_approx,  # higher density first within tie
    throughput_factor,    # ascending (curriculum: lower production first)
    pattern_id,           # deterministic tie-break
)
```

Assign `difficulty_rank = 1..18` by sorted position.

**Invariant:** `difficulty_rank` is recomputed on every `seed_miner_patterns` run; `seed_rank` is **not** recomputed from score.

### 3.6 Golden expected order (bootstrap v2, 2026-05-28)

Probe on `var/default_miner_pattern.txt` with §3.3–§3.5:

| `difficulty_rank` | `pattern_id` | `tier` | `score` |
|------------------:|--------------|-------|--------:|
| 1 | `m0e_01` | 0 | 8 |
| 2 | `m1e_01` | 1 | 105 |
| 3 | `m2e_01` | 2 | 221 |
| 4 | `m2e_02` | 2 | 233 |
| 5 | `m2e_04` | 3 | 261 |
| 6 | `m2e_03` | 3 | 263 |
| 7 | `m3e_01` | 4 | 337 |
| 8 | `m3e_02` | 4 | 354 |
| 9 | `m3e_04` | 4 | 354 |
| 10 | `m3e_03` | 5 | 364 |
| 11 | `m3e_07` | 5 | 377 |
| 12 | `m3e_09` | 5 | 381 |
| 13 | `m3e_06` | 5 | 384 |
| 14 | `m3e_13` | 5 | 384 |
| 15 | `m3e_05` | 5 | 394 |
| 16 | `m3e_11` | 5 | 394 |
| 17 | `m3e_12` | 5 | 394 |
| 18 | `m3e_08` | 5 | 404 |

Note: `m3e_01` (linear 3-chain) is the easiest ext-3 pattern; branched / multi-turn ext-3 patterns sort later. This matches the product intent “flat/simple before branch/corridor risk.”

---

## §4 — Ingest and admin

### 4.1 `seed_miner_patterns` changes

1. Decode + strict validate each line (unchanged).
2. Compute per-pattern `IntrinsicDifficultyResult`.
3. Collect all 18 results; assign global `difficulty_rank`.
4. Write metadata including `rank_reason`; set `search_priority_rank = null`, `search_priority_source = "deferred_phase5"`.
5. `seed_rank` remains `enumerate(..., start=1)` on `EXPECTED_PATTERN_IDS` order.

**`--dry-run`:** Computes all 18 scores and prints the rank table (tier, score, `difficulty_rank`, `pattern_id`). Does **not** write to the database. Never fails on duplicate `difficulty_score` in default mode — `pattern_id` is the deterministic final tie-break.

**`--strict-rank-ambiguity` (optional, off by default):** After dry-run or before write, fail if two distinct `pattern_id` values share the same pre-`pattern_id` sort key:

```text
(difficulty_tier, difficulty_score, compactness_approx, throughput_factor)
```

Use only when tightening the formula; default ingest allows score ties resolved by `pattern_id`.

### 4.2 Admin

- Add readonly columns: `difficulty_rank`, `difficulty_tier`, `difficulty_score` (short).
- Default changelist ordering: `metadata_json__seed_rank` (catalog) — **not** difficulty.
- Optional filter by `difficulty_tier`.

### 4.3 Phase 5 — `search_priority_rank` (future)

When `FitnessBreakdown` and conservative penalties exist:

```text
search_priority_rank = sort(
  difficulty_rank,
  candidate_effective_score   # map + probe + fitness proxies
)
```

**Contract:** Map-aware score never overwrites `difficulty_rank`; solver may read both. Document in `asteroid_lab_05` cross-link.

---

## §5 — Testing

| Test | Path (proposed) | Asserts |
|------|-----------------|---------|
| Scorer unit | `tests/unit/asteroid_lab/test_miner_seed_intrinsic_difficulty.py` | Known trees: linear chain, L-branch, tier boundaries |
| Golden order | same file or `test_seed_miner_patterns.py` | Full 18 `pattern_id` → `difficulty_rank` table §3.6 |
| Ingest round-trip | `test_seed_miner_patterns.py` | After command, DB rows have ranks + `rank_reason` keys |
| Catalog stability | `test_miner_seed_bootstrap_sync.py` | `seed_rank` still matches `EXPECTED_PATTERN_IDS` index |
| Uniqueness | ingest test | `difficulty_rank` 1..18 permutation on canonical keys |

**Forbidden:** Using difficulty rank in solver integration tests as commit order.

---

## §6 — Risks and mitigations

| Risk | Mitigation |
|------|------------|
| `compactness_approx` misread as map coverage | Name + docs; Phase 5 uses map fitness |
| Score weights drift | Golden table §3.6; change weights only with explicit spec amendment |
| Confusion with `seed_rank` | Admin labels: “Catalog rank” vs “Difficulty rank” |
| Import cycle equivalence ↔ difficulty | Extract parent-tree helpers to small shared module |

---

## §7 — Implementation phases (for planning)

| Phase | Scope |
|-------|--------|
| **PR-D1** | Scorer module + unit tests + golden order |
| **PR-D2** | `seed_miner_patterns` metadata + admin columns |
| **PR-D3** (blocked) | `search_priority_rank` when Phase 5 fitness DTO lands |

---

## §8 — Approval checklist

- [x] §1 Metadata separation (`seed_rank` = catalog)
- [x] §3 Intrinsic formula and golden order
- [x] User sign-off on full spec (contract review 2026-05-28)
- [x] Implementation plan: [`../plans/2026-05-28-miner-seed-difficulty-rank.md`](../plans/2026-05-28-miner-seed-difficulty-rank.md)
