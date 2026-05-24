---
status: ARCHIVED
do_not_use_as_authority: true
archived_reason: pre-RTTP plan snapshot; see documents/Algorithm/ and docs/superpowers/specs/
superseded_by:
  - documents/ai/current_plan.md
  - docs/superpowers/specs/2026-05-22-rttp-hybrid-c-layout-design.md
---

# Phase 3 — Bundle Candidate Generator


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_03_candidate_generator.md`](../../Algorithm/asteroid_lab_03_candidate_generator.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

## Purpose

Place PatternLibrary on actual asteroid topology to generate feasible bundle candidates.

## Implementation philosophy (required)

Regardless of doc Phase numbers, **in implementation sequence** the following is one block:

```text
candidate generation
→ local geometry validation
→ immediate route feasibility probe
→ reachable only → normal pool
```

“Generate candidates first, probe later” is treated as near-forbidden. Details: `asteroid_lab_10_development_sequence.md` Sequence 3.

## Greedy rim installation forbidden (required)

Candidate Generator **does not confirm extractor / extension on layout.** (Same for belt·pipe entities.)

This stage performs only:

```text
BundleCandidate generation
local geometry validation
low-cost route feasibility probe
normal pool / rejected separation
```

**Selection** is Phase 6 Evolutionary Search; **confirmation** is Phase 7 Incremental Commit.

`ExtractorPlacementPolicy.RIM_ONLY` and doc **rim-only** expressions are **candidate generation constraints** (extractor anchor coord ∈ `rim_cells`), not a **greedy pass that walks rim and installs in order**.

```text
search-space pruning ≠ greedy installation
```

## Input

```python
OptimizationInput
tuple[BundlePattern, ...]
CandidateGenerationConfig
```

### `CandidateGenerationConfig`

```python
class ExtractorPlacementPolicy(Enum):
    RIM_ONLY = "rim_only"

@dataclass(frozen=True)
class CandidateGenerationConfig:
    extractor_policy: ExtractorPlacementPolicy
    allow_diagnostic_unreachable: bool
    max_candidates: int | None
    route_probe_max_expansions: int
    transport_kinds: frozenset[TransportKind]
    route_probe_goal_priority_weight: int
```

`ExtractorPlacementPolicy` defines **how to open the candidate pool** only. v0 default `RIM_ONLY` **limits extractor anchor to `rim_cells`** to reduce combinatorics (not all mineable). **Unrelated to install order·immediate commit.**

`route_probe_goal_priority_weight` passes to Phase 4 `RouteProbeInput.goal_priority_weight`.

When `max_candidates` is not `None`, after **normal pool(`normal_candidates`) is finalized**, truncate if count exceeds cap. `rejected_candidates` not counted toward cap. Sort key before truncation (v0 authority, deterministic):

```text
1) base_score descending
2) route_probe_result.cost ascending
3) candidate_id ascending
```

Then keep first `max_candidates` only.

When `allow_diagnostic_unreachable=True`, unreachable candidates may remain in `rejected_candidates` or separate diagnostic list, **not normal pool**.

## Candidate equivalence / dedupe (combinatorial explosion mitigation)

`rim_cell × pattern × rotation × transport_kind × goal matching` etc. can explode candidate count. Collapse equivalent candidates to one **before evolution**.

### `CandidateEquivalenceKey`

Same **occupied geometry·output stub·throughput contract·topology_signature** ≈ duplicate for search·fitness. v0 authority key (field names adjustable in implementation, **semantics preserved**):

```python
@dataclass(frozen=True)
class CandidateEquivalenceKey:
    occupied_cells: frozenset[Coord]
    output_stub: Coord
    output_dir: Direction
    transport_kind: TransportKind
    base_throughput: int
    topology_signature: str
```

When same key appears multiple times, **keep one**. Representative tie-break (v0 authority): first by `candidate_id` ascending.

Apply dedupe **before `max_candidates` truncation** so truncation is not random but **post-equivalence reduction** then score sort.

### `CandidateSpatialHash` (optional)

Coordinate bucketing is **optional optimization**. Determinism·equivalence key authority is `CandidateEquivalenceKey`.

## Output

Separate success and rejected candidates **by type** so “normal pool = success only” is near compile-time fixed.

```python
@dataclass(frozen=True)
class BundleCandidate:
    candidate_id: str
    pattern_id: str
    topology_signature: str
    extractor: Coord
    extensions: tuple[Coord, ...]
    occupied_cells: frozenset[Coord]
    output_stub: Coord
    output_dir: Direction
    transport_kind: TransportKind
    base_throughput: int
    base_score: float
    route_probe_result: RouteProbeResult
```

Path cost uses **`route_probe_result.cost`** only (no duplicate `route_cost` field).

Do **not** construct `BundleCandidate` directly; factory/builder only, asserting success contract `route_probe_result.reachable`·`reached_goal` in one place.

Goal kind uses **`route_probe_result.reached_goal.goal_kind`** only (no alias like `matched_goal_kind`).

```python
@dataclass(frozen=True)
class RejectedBundleCandidate:
    attempted_pattern_id: str
    extractor: Coord | None
    rejection_reason: CandidateRejectReason
    route_probe_result: RouteProbeResult | None
```

When blocked at geometry stage, `route_probe_result` may be `None`.

```python
@dataclass(frozen=True)
class CandidateGenerationResult:
    normal_candidates: tuple[BundleCandidate, ...]
    rejected_candidates: tuple[RejectedBundleCandidate, ...]
```

### Probe result snapshot

`route_probe_result` is first-pass probe result at **candidate phase**.

- Reused in fitness·diagnostic·pool re-evaluation.
- **incremental commit** must re-run probe (doc Phase 5·7).

### topology_signature

If candidate granularity bundles only `extractor + extensions + stub`, genome bloats when mutation wants **extension topology only** changes.

v0 uses `topology_signature` as **deterministic string** (or fixed hex from int hash) identifying **geometry·attachment·stub direction·throughput·transport kind**. When splitting `PlacementGene` / `TopologyGene` / `RoutingPreferenceGene` in v1, extend field set without splitting string meaning.

**Recommended inclusion (deterministic serialization order):**

```text
pattern_id
linear_extension_count (0~3)
rotation·symmetry canonical id (pattern library canonical rotation id)
extractor direction / extension chain direction summary (one enum order fixed in project)
output_stub·output_dir
transport_kind
base_throughput (or base_throughput bucket)
sorted listing or deterministic hash of occupied_cells (coord lex order)
```

Short abbreviation-only strings like `lin_e_len3_outE` cause **signature drift** as pattern library grows. Include above items **without omission** in serialization rules.

## v0 policy

```text
extractor anchor ∈ rim_cells (candidate generation constraint; not immediate install)
extension ∈ mineable asteroid cells
output_stub = non-occupied route start
```

The loop below is **enumeration to fill pool** only; `rim_cell` order must **not** become commit order·greedy install order.

```text
for rim_cell in rim_cells:
    for pattern in pattern_library:
        project pattern onto rim_cell
        validate occupied cells
        validate extension cells
        validate output stub
        build RouteProbeInput (route_domain + route_goals from OptimizationInput)
        run route feasibility probe
        append BundleCandidate to normal_candidates OR RejectedBundleCandidate to rejected_candidates
```

Nested `for rim_cell`·`for pattern` order is for **deterministic enumeration**. Must **not** become authority for layout confirmation·commit_order (commit_order is genome `Gene.commit_order`, Phase 7).

## Reject reasons

Listed values match **`CandidateRejectReason` enum** members 1:1 (free strings forbidden).

```text
extractor_not_rim
extension_not_mineable
occupied_outside_asteroid
output_stub_inside_occupied
output_stub_invalid_coord
pattern_overlap_self
route_probe_unreachable
```

## Relationship to Route Probe

First-pass route feasibility probe runs **immediately before a candidate is accepted**.

Unreachable candidates do not enter normal pool. Diagnostic follows `allow_diagnostic_unreachable` policy.

## Invariant

```text
[ ] Candidate Generator does not confirm placement (commit)
[ ] rim traversal order does not leak as commit order (commit_order is genome)
[ ] topology_signature deterministic (pattern·rotation·extension·stub·throughput·transport·occupied geometry summary)
[ ] CandidateEquivalenceKey dedupe applied before max_candidates truncation
[ ] occupied_cells contains extractor and extensions only
[ ] output_stub not in occupied_cells
[ ] extractor in rim_cells
[ ] extensions in mineable_cells
[ ] topology_graph·occupied consistent with island map grid·`grid_contract.neighbors4` (copy JSON X==0 allowed)
[ ] all absolute Coord·cell sets island-local (x, y) (same as Phase 1 coordinate rules)
[ ] each normal_candidates element: route_probe_result.reachable is True
[ ] normal_candidates: route_probe_result.reached_goal is not None (v0 success contract)
[ ] rejected_candidates: rejection_reason always CandidateRejectReason
[ ] probe pass/fail distinguished by type before normal pool registration
```

## Tests

```text
test_candidate_generator_rim_only_extractors
test_candidate_generator_extensions_must_be_mineable
test_candidate_generator_output_stub_not_occupied
test_candidate_generator_island_coord_contract
test_candidate_generator_deterministic_ids
test_candidate_generator_topology_signature_deterministic
test_candidate_generator_records_rejection_reason_enum
test_candidate_generator_stores_probe_snapshot_on_success
test_candidate_generator_immediate_probe_excludes_unreachable_from_normal_pool
test_candidate_generator_equivalence_dedupe_deterministic
```

## Completion criteria

```text
[ ] rim-only extractor **candidate generation only** (no commit·greedy rim install)
[ ] linear extension candidate generation
[ ] reject reason recording
[ ] CandidateRejectReason·RouteProbeFailureReason·ValidationIssueCode defined
[ ] CandidateEquivalenceKey + dedupe (before max_candidates)
[ ] topology_signature field (matches serialization component docs)
[ ] CandidateGenerationConfig DTO defined
[ ] route_probe invoked in same sequence (normal pool gate)
[ ] route_probe_result recorded on success candidates (no alias matched_goal_kind·route_cost)
[ ] BundleCandidate created only via factory/builder
[ ] CandidateGenerationResult (normal vs rejected type separation)
```
