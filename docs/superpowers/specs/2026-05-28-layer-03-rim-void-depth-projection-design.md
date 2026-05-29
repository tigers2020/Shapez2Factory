# Layer 03 — Rim Void-Depth Pre-Gate (Observability) — Design Spec

**Document type:** Solver / Lab contract amendment (Layer 3 geometry classification + metrics)  
**Status:** **SUPERSEDED (2026-05-28)** for pool recovery — observability-only slice optional; canonical fix is [`2026-05-28-layer-03-virtual-exterior-transport-domain-design.md`](2026-05-28-layer-03-virtual-exterior-transport-domain-design.md)  
**Work classification:** contract change · implementation change  
**Scope:** `layer_03_rim_mining_bundles/` · `layers/contracts/candidates.py` · `layers/observability/` · Lab summary (output-only)  
**Parent spec:** [`2026-05-28-layer-03-rim-mining-bundles-design.md`](2026-05-28-layer-03-rim-mining-bundles-design.md) (APPROVED)  
**Follow-up (out of scope):** candidate pool recovery — see [§10](#10--follow-up-pool-recovery-not-this-pr)

**Architect decision (2026-05-28):** Option **A** — keep transport stub ⊆ `external_void_cells`; add void-depth pre-gate for **classification and short-circuit**, not pool rescue. Coordinate model: **seed-local relative**, **validation absolute** on `ReconstructionCompleteMap`.

---

## §1 — Purpose and boundaries

### 1.1 PR identity (normative)

```text
This PR does NOT guarantee candidate pool recovery.
It classifies and short-circuits impossible (anchor, output_dir, seed) triples
before calling project_miner_seed_at_anchor, while preserving absolute projection validation.

Korean reference:
  이 PR은 후보를 살리는 PR이 아니라,
  왜 후보가 0인지 정확히 보이게 만드는 PR이다.
```

| In scope | Out of scope |
|----------|----------------|
| `INSUFFICIENT_VOID_DEPTH` reject reason | Transport stub truncation (Option B) |
| `void_depth_along_dir` + `required_void_extent` pre-gate | Shorter seed catalog / output_dir policy change |
| `reject_reason_counts`, `projection_call_count` metrics | Exterior void topology amendment |
| Lab/JSONL output-only highlights | **Hard requirement** that `route_probe_attempt_count > 0` on real maps |

**Important:** If every rim anchor has `void_depth < required_void_extent` for all 18 seeds, this PR still yields `route_probe_attempt_count == 0`. That is an **expected and valid** outcome.

### 1.2 Observed failure (Lab Run, 583 shape-field map)

| Metric | Value | Interpretation |
|--------|-------|----------------|
| `rim_anchor_count` | 81 | Outer-rim enumeration OK |
| `seed_projection_attempt_count` | 1458 (= 81 × 18) | Catalog + anchor/seed pairs **considered** |
| `local_geometry_rejected_count` | 1458 | 100% geometry reject before route probe |
| `route_probe_attempt_count` | 0 | No candidate reached probe |
| `normal_candidate_count` | 0 | L4 correctly places 0 |

This is **not** empty seed catalog, L2 hold, or L4 selection failure.

### 1.3 Root cause (contract-level)

Miner seed blueprints place transport stubs at **canonical-local offsets** (e.g. `(1,0)`, `(2,0)` east of extractor). After rotation toward `output_dir`, the farthest transport cell often lands **inside `field_cells`** on thick real maps, violating L3 §1.2 `transport_stub_cells ⊆ external_void_cells`.

Golden 5×5 fixtures pass because void corridors are artificially wide; production maps may reject all seeds at almost every rim anchor.

### 1.4 Design response (this PR only)

1. **Keep** absolute validation in `project_miner_seed_at_anchor` (no belt truncate in v1).  
2. **Add** void-depth **pre-gate** (necessary-condition filter) before projection.  
3. **Add** observability: `reject_reason_counts`, `projection_call_count`, `void_depth_pregate_rejected_count`.

---

## §2 — Coordinate model (normative)

### 2.1 Principle

```text
Miner seed geometry is stored in canonical local-relative coordinates.
Layer 3 projection rotates and translates those offsets into
ReconstructionCompleteMap absolute coordinates before any field/void/probe validation.
No Lab/UI/dense/screen coordinate may be used as solver input.
```

### 2.2 Coordinate kinds

| Kind | Definition | Used for |
|------|------------|----------|
| **Seed-local / relative** | Offsets from extractor at canonical `(0,0)`, canonical output = `E` | Catalog, extent precompute, rotation |
| **Map absolute** | `Coord` in `ReconstructionCompleteMap.coord_frame` (island-raw server topology) | `field_cells`, `external_void_cells`, route goals, projection output, all gates |

```text
server/world Coord (ReconstructionCompleteMap)
≠ Lab dense coord
≠ screen / CSS / render coord
```

Lab replay and overlays are **output-only**; they MUST NOT feed void-depth or projection.

### 2.3 Projection (unchanged semantics, explicit naming)

```python
# seed-local (canonical E)
extractor_offset = (0, 0)
transport_offsets = ((1, 0), (2, 0))  # example m0e_01

# projection
steps = steps_from_canonical_e(output_dir)
abs_cell = anchor_abs + rotate_offset(local_offset, steps)

# validation (absolute only)
mining_abs_cells ⊆ field_cells
transport_abs_cells ⊆ external_void_cells
route_probe_start_abs ∈ transport_abs_cells
```

`project_miner_seed_at_anchor` remains the **sole** relative→absolute translator for L3 v1 (no second projection path).

### 2.4 Alignment with gene template invariants

Canonical offsets in [`gene_template.py`](../../../django_apps/asteroid_lab/genetic_sample/gene_template.py): extractor `(0,0)`, FOT `(1,0)`, probe start `(2,0)`. Catalog extent helper MUST use the same rules as `GeneTemplate` / `project.py`.

---

## §3 — Void-depth pre-gate

### 3.1 Absolute void depth

```python
def void_depth_along_dir(
    anchor_abs: Coord,
    output_dir: Direction,
    external_void_cells: frozenset[Coord],
) -> int:
    """
    Count contiguous cells in external_void_cells stepping from anchor_abs
    along output_dir (cardinal). First step must be in external_void_cells.
    Returns 0 if the first step is not void.
    """
```

- Computed on `complete_map.external_void_cells` only (same SoT as L2/L3).  
- Single cardinal ray (v0 colinear transport assumption).

### 3.2 Seed required extent (relative, precomputed)

```python
required_void_extent: int  # canonical E; max local.x among colinear transport offsets
```

Populated at catalog load via `transport_required_void_extent_from_decoded_json(decoded_json)`.

### 3.3 Gate rule

**Necessary-condition filter (normative):**

```text
The void-depth pre-gate is a necessary-condition filter, not a sufficient-condition validator.
Passing the pre-gate does not imply a valid candidate.
Failing the pre-gate implies the seed cannot satisfy the v1 transport-stub-in-external-void
contract for that anchor/output_dir under colinear transport assumptions.
```

**Enumeration:**

```text
void_depth ← void_depth_along_dir(anchor_abs, output_dir, external_void_cells)

IF required_void_extent > void_depth:
  seed_projection_attempt_count += 1
  void_depth_pregate_rejected_count += 1
  local_geometry_rejected_count += 1
  increment reject_reason_counts[INSUFFICIENT_VOID_DEPTH]
  append diagnostic(SKIPPED_GEOMETRY, INSUFFICIENT_VOID_DEPTH)
  CONTINUE   # do NOT call project_miner_seed_at_anchor

ELSE:
  projection_call_count += 1
  projection ← project_miner_seed_at_anchor(...)
  IF projection.candidate is None:
    local_geometry_rejected_count += 1
    increment reject_reason_counts[projection.reject_reason]
    ...
  ELSE:
    route_probe_attempt_count += 1   # existing probe path
```

**Normative:**

- Pre-gate does **not** replace `project_miner_seed_at_anchor` absolute checks.  
- Post-projection `TRANSPORT_STUB_NOT_IN_VOID` **may still occur** after pre-gate pass (non-colinear seeds, lateral misalignment; v0 catalog is colinear so rare).

### 3.4 New reject reason

```python
class CandidateRejectReason(StrEnum):
    ...
    INSUFFICIENT_VOID_DEPTH = "insufficient_void_depth"
```

Update parent L3 design §2.7 cross-reference when implementing.

---

## §4 — Contract changes

### 4.1 `MinerSeedEntry` / catalog

```python
@dataclass(frozen=True, slots=True)
class MinerSeedEntry:
    ...
    required_void_extent: int
```

### 4.2 `Layer03ExpansionMetrics` — metric semantics (normative)

| Field | Meaning |
|-------|---------|
| `seed_projection_attempt_count` | **(anchor, seed) pair considered** at an anchor with valid `output_dir` — includes pre-gate rejects and projection calls. **Preserved for Lab backward compatibility**; name is historical. |
| `projection_call_count` | **Actual** `project_miner_seed_at_anchor` invocations |
| `void_depth_pregate_rejected_count` | Pre-gate rejects with `INSUFFICIENT_VOID_DEPTH` (must equal `reject_reason_counts["insufficient_void_depth"]`) |
| `local_geometry_rejected_count` | All geometry failures (pre-gate + post-projection) |
| `reject_reason_counts` | `dict[str, int]` keyed by `CandidateRejectReason.value`; **sum MUST equal** `local_geometry_rejected_count` when diagnostics are complete |
| `route_probe_attempt_count` | Unchanged — only when probe runs |

```text
Invariant (output wire):
  sum(reject_reason_counts.values()) == local_geometry_rejected_count
  void_depth_pregate_rejected_count == reject_reason_counts.get("insufficient_void_depth", 0)
  projection_call_count <= seed_projection_attempt_count
```

**Forbidden:** Redefining `seed_projection_attempt_count` to mean only `projection_call_count` (breaks existing Lab metric interpretation).

### 4.3 Lab / JSONL (output-only)

- L3 highlights: top-2 `reject_reason_counts` keys, `void_depth_pregate_rejected_count`, `projection_call_count`.  
- `route_probe_attempt_count` may remain `0` without failing this PR.

---

## §5 — Non-goals (this PR)

```text
Candidate pool recovery on production maps
Transport stub truncation at void frontier (Option B)
Changing output_dir / anchor selection policy
Shorter seed catalog
Exterior void topology changes
Using Lab dense/screen coords as solver input
Skipping project_miner_seed_at_anchor absolute checks
Hard acceptance: route_probe_attempt_count > 0
```

---

## §6 — Testing

### 6.1 P0 — Observability regression (required for this PR)

| Test | Acceptance |
|------|------------|
| `void_depth_along_dir` unit | Synthetic ray counts |
| `transport_required_void_extent_from_decoded_json` | m0e_01 → 2 |
| Thick-rim / 583-cell fixture | `reject_reason_counts["insufficient_void_depth"] > 0` |
| Histogram invariant | `sum(reject_reason_counts.values()) == local_geometry_rejected_count` |
| Golden 5×5 | Existing L3 tests remain green |
| Real-map fixture | `route_probe_attempt_count` **may remain 0**; MUST document dominant reject reason |

```text
P0 PASS does NOT require route_probe_attempt_count > 0.
```

### 6.2 P1 — Pool recovery regression (follow-up PR only)

| Test | Acceptance |
|------|------------|
| Real-map or thick-rim | `route_probe_attempt_count > 0` and `normal_candidate_count > 0` |

Requires **one of** (separate spec/PR):

```text
a) shorter seed catalog (min extent filter)
b) anchor/output_dir selection policy change
c) controlled transport truncation spec (Option B)
d) exterior connector / rim void topology amendment
```

---

## §7 — Implementation notes (informative)

1. PR slice: enum + metrics + helpers → expand pre-gate → observability/Lab → P0 fixtures.  
2. No change to `immediate_route_probe` or L4.  
3. Parent spec §3.1: insert pre-gate before `project_miner_seed_at_anchor`.

---

## §8 — Spec self-review

| Check | Result |
|-------|--------|
| Pool rescue vs observability | Explicitly separated (§1.1, §6) |
| Metric semantics | `seed_projection_attempt_count` preserved; `projection_call_count` added |
| Pre-gate role | Necessary-condition only (§3.3) |
| Acceptance | P0 does not require `route_probe_attempt_count > 0` |
| Coordinate model | Seed-local vs map absolute vs Lab output-only |

---

## §9 — Approval checklist (architect)

```text
[x] This PR is observability/classification, not pool recovery
[x] P0 vs P1 regression split
[x] seed_projection_attempt_count meaning preserved; projection_call_count added
[x] void-depth gate = necessary-condition filter
[x] route_probe_attempt_count > 0 removed from hard acceptance
```

**Next step:** Invoke `writing-plans` → `docs/superpowers/plans/2026-05-28-layer-03-rim-void-depth-projection.md`

---

## §10 — Follow-up: pool recovery (not this PR)

When P0 shows `insufficient_void_depth` majority on real maps, open a **separate** spec choosing one recovery strategy:

| Strategy | Trade-off |
|----------|-----------|
| Catalog filter: only seeds with `required_void_extent ≤ min_rim_void_depth` | Simple; may shrink pool aggressively |
| Per-anchor seed filter | More candidates; more CPU |
| Option B truncation | Contract change; equivalence impact |
| Topology / L2 void corridor | Map-dependent; highest leverage |

Do not combine recovery with this observability PR in one merge.
