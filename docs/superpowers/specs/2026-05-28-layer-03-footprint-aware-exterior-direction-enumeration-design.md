# Layer 03 — Footprint-Aware Exterior Direction Enumeration — Design Spec

**Document type:** Solver / Lab contract amendment (L3 projection enumeration)  
**Status:** **APPROVED (2026-05-28)** — Solver Contract Architect R2-lite  
**Work classification:** contract change · implementation change  
**Scope:** `layer_03_rim_mining_bundles/rim_anchors.py` · `expand.py` · `project.py` (read-only formula) · `candidates.py` · observability · parent L3 spec §1.4  
**Parent:** [`2026-05-28-layer-03-rim-mining-bundles-design.md`](2026-05-28-layer-03-rim-mining-bundles-design.md) (§1.4 **superseded** by this document for direction policy)  
**Depends on:** [`2026-05-28-layer-03-virtual-exterior-transport-domain-design.md`](2026-05-28-layer-03-virtual-exterior-transport-domain-design.md) (APPROVED — `placeable_cells`, probe path semantics)

**Korean title (reference):** L3 rim 앵커별 exterior 방향 열거 + M/E footprint fit 후 투영

---

## §1 — Problem restatement

### 1.1 Symptom (583-cell Lab, post virtual-exterior + connectivity split)

```text
rim_anchor_count = 81
seed_projection_attempt_count = 1458   # 81 × 18
local_geometry_rejected_count = 1458
route_probe_attempt_count = 0
reject_reason_counts (top):
  mining_cell_off_field: 925
  local_geometry_invalid: 402
  transport_collides_with_field: 131
```

### 1.2 Withdrawn root cause

```text
M-anchor projection uses wrong origin (anchor + rotate(local) without subtracting local_M)
```

**Verified:** `project_miner_seed_at_anchor` already computes:

```text
abs = anchor_abs + rotate(local_cell - local_miner, output_dir)
```

### 1.3 Correct root cause (normative)

```text
583-cell pool 0 is NOT primarily caused by M-anchor formula error.
Primary cause: R1 single output_dir per anchor + 2D/long mining footprint catalog
on thick/concave rim — feasible rotations are not enumerated before rejection.
```

A colinear seed (e.g. local `E E E M B`, M at `(4,0)`) MAY succeed at rim anchor `(7,3)` with `output_dir=E` while failing with `output_dir=N`. R1 commits to one direction before testing footprint fit.

### 1.4 PR identity

| This PR | Not this PR |
|---------|-------------|
| R2-lite: enumerate bounded exterior cardinal `output_dir` candidates per anchor | Unbounded direction sweep (R3) |
| Footprint fit gate before full projection cost where specified | Change M-anchor formula (already correct) |
| P0: `route_probe_attempt_count > 0` on R1-fail / R2-success fixture | 583-cell pool recovery guarantee (evidence metric only) |
| Direction + subreason observability | L4/L5 commit semantics |
| EEEMB M-anchor regression fixture | Catalog ingest / new seed authoring |

---

## §2 — Contract change: R1 → R2-lite

### 2.1 Withdrawn (parent §1.4)

```text
One fieldward output_dir per anchor (not R2 multi-void, not R3 cardinal-4 sweep).
select_exterior_output_dir → choose single best direction.
```

### 2.2 New normative policy (R2-lite)

```text
Layer 3 MUST NOT commit to a single exterior output_dir before testing mining-footprint fit.
For each rim anchor, L3 enumerates bounded exterior cardinal output_dir candidates,
then evaluates each (anchor, output_dir, seed) tuple.
```

**Korean reference:**

```text
L3는 앵커마다 output_dir 하나를 먼저 확정하면 안 된다.
rim anchor에서 가능한 exterior 방향들을 먼저 열거하고,
각 방향별로 seed의 M/E footprint가 field 안에 들어가는지 검사해야 한다.
```

### 2.3 Bounded enumeration (not R3)

```text
exterior_output_dir_candidates(anchor):
  at most 4 cardinal directions
  direction d is included iff step(anchor, d) ∉ field_cells
  optional: prefer ordering when step(anchor, d) ∈ external_void_cells (diagnostic only)
  MUST NOT use external_void_cells as belt installability SoT (virtual exterior spec)
```

A non-field first step is only a direction candidate, not proof of exterior reachability. Interior-hole or disconnected candidates are rejected later by the virtual exterior domain (`placeable_cells`).

L2 route goal Manhattan distance is **sorting/scoring only** — MUST NOT drop other feasible directions before footprint enumeration.

```text
sort candidates by (min_goal_dist, NESW tie-break)
enumerate ALL candidates in sorted order
```

### 2.4 Projection formula (unchanged)

```python
miner_local = find_miner_local_coord(seed)
rel = local_cell - miner_local
abs_coord = anchor_abs + rotate(rel, output_dir)
```

No change to `project_miner_seed_at_anchor` formula in this PR unless regression test proves otherwise.

---

## §3 — L3 enumeration flow (revised)

```text
FOR anchor IN outer_rim:
  output_dirs ← exterior_output_dir_candidates(anchor, ...)
  IF output_dirs empty:
    diagnostic NO_EXTERIOR_VOID_NEIGHBOR
    CONTINUE

  FOR output_dir IN output_dirs:          # sorted by goal distance, all feasible dirs
    FOR seed IN catalog.by_intrinsic_priority_rank():
      direction_seed_attempt_count += 1

      # Optional fast pre-check: projected mining_cells ⊆ field without full BundleCandidate
      IF mining_footprint_off_field(seed, anchor, output_dir, complete_map):
        reject MINING_CELL_OFF_FIELD (or prefilter counter + skip)
        CONTINUE

      projection ← project_miner_seed_at_anchor(...)
      IF projection.candidate is None:
        diagnostic SKIPPED_GEOMETRY + reject_reason (+ subreason when LOCAL_GEOMETRY_INVALID)
        CONTINUE

      domain ← build_exterior_transport_domain(...)
      placeable gate + immediate_route_probe(...)   # virtual exterior spec unchanged
      ...
```

**Forbidden:**

```text
output_dir ← select_single_best_exterior_output_dir(anchor)
FOR seed: project only that output_dir
```

---

## §4 — Direction candidate API

### 4.1 New function (sole factory for candidate list)

```python
def exterior_output_dir_candidates(
    anchor: Coord,
    *,
    complete_map: ReconstructionCompleteMap,
    route_goals: tuple[RouteGoal, ...],
    transport_kind: TransportKind,
) -> tuple[Direction, ...]:
    """Up to 4 exterior cardinal dirs where first step is not field; sorted by goal distance."""
```

Location: `layer_03_rim_mining_bundles/rim_anchors.py`

### 4.2 `select_exterior_output_dir` (deprecated for expand)

Retain for tests or rename to `preferred_exterior_output_dir` for **sort key only** — expand MUST NOT call it as sole direction.

---

## §5 — Reject reasons and subreasons

### 5.1 Existing reasons (unchanged semantics)

| Reason | When |
|--------|------|
| `MINING_CELL_OFF_FIELD` | `mining_occupied_cells ⊄ field_cells` after projection (or prefilter) |
| `TRANSPORT_COLLIDES_WITH_FIELD` | transport ∩ field ≠ ∅ |
| `LOCAL_GEOMETRY_INVALID` | see §5.2 |
| `NO_EXTERIOR_VOID_NEIGHBOR` | zero exterior cardinal candidates |

### 5.2 `LOCAL_GEOMETRY_INVALID` subreasons (observability, v1)

Emit in diagnostic metadata / metrics (string suffix or parallel counter keys):

```text
local_geometry_invalid.missing_extractor
local_geometry_invalid.anchor_not_in_mining_cells
local_geometry_invalid.mining_transport_overlap
local_geometry_invalid.probe_start_not_transport
local_geometry_invalid.unknown_layout
```

Implementation MAY use dotted keys in `reject_reason_counts` histogram (contract change for Lab display).

---

## §6 — Metrics (normative)

Add to `Layer03ExpansionMetrics` (output-only for solver; not algorithm input):

| Metric | Meaning |
|--------|---------|
| `exterior_direction_candidate_count` | Σ len(candidates(anchor)) over processed anchors |
| `direction_seed_attempt_count` | Σ (len(candidates) × seeds tried) — replaces naive 81×18 interpretation |
| `mining_footprint_prefilter_rejected_count` | Fast off-field rejects before full candidate build (if implemented) |
| `seed_projection_attempt_count` | Full `project_miner_seed_at_anchor` calls |
| `reject_reason_counts` | All diagnostic rejects (geometry + probe); sum need not equal `local_geometry_rejected_count` |

Retain virtual-exterior metrics from prior spec.

---

## §7 — Testing (normative)

### 7.1 P0 — EEEMB M-anchor regression

```text
Given:
  seed local colinear E E E M B, M at (4,0)
  anchor_abs = (7,3)
  field_cells ⊇ {(4,3),(5,3),(6,3),(7,3)}
  exterior/placeable allows B at (8,3)
  output_dir = E

Expect:
  projected M == (7,3)
  projected E ⊆ field_cells
  projected B ∩ field_cells == ∅
  projection succeeds
```

Proves formula; does not prove R2-lite alone.

### 7.2 P0 — R1-fail / R2-lite-success fixture

```text
Given:
  anchor with exterior dirs N and E
  seed fits only with output_dir=E
  legacy R1 scorer would pick N first and exclusively

Expect:
  enumeration tries E
  route_probe_attempt_count > 0
```

(`normal_candidate_count > 0` is evidence-only, not a hard gate — probe may fail on route goals while projection succeeds.)

### 7.3 Evidence — 583-shaped map (optional committed fixture)

```text
route_probe_attempt_count > 0
mining_cell_off_field count < 925 (baseline from Run #268 class map)
```

Not a hard merge gate unless fixture is committed in repo.

---

## §8 — Parent spec amendment

Replace [`2026-05-28-layer-03-rim-mining-bundles-design.md`](2026-05-28-layer-03-rim-mining-bundles-design.md) §1.4 with:

```text
R2-lite (2026-05-28): enumerate exterior_output_dir_candidates per anchor (≤4 cardinals).
L2 goal distance sorts enumeration order only.
See footprint-aware-exterior-direction-enumeration-design.md.
```

---

## §9 — Related documents

| Doc | Relationship |
|-----|----------------|
| Virtual exterior transport domain | Probe after projection; `placeable_cells` |
| Transport connectivity split | `path_coords` ≠ full placeable component |
| Rim mining bundles parent | Pool, metrics, skip reasons |

---

## §10 — Approval record

```text
Status: APPROVED (2026-05-28)

Decision:
  Supersede parent L3 §1.4 R1 single-output-dir policy.
  Adopt R2-lite: enumerate all bounded exterior cardinal output_dir candidates per rim anchor.
  L2 goal distance sorts candidates only; MUST NOT drop feasible directions.
  M-anchor projection formula remains unchanged.
  P0 hard gate: route_probe_attempt_count > 0 on R1-fail/R2-lite-success fixture.

Implementation plan:
  docs/superpowers/plans/2026-05-28-layer-03-footprint-aware-exterior-direction-enumeration.md
```
