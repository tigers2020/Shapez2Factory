# Phase 3 — Bundle Candidate Generator

## Purpose

Place PatternLibrary on actual asteroid topology to generate feasible bundle candidates.

## Implementation philosophy (required)

Regardless of doc Phase numbers, **in the implementation sequence** the following is one unit.

```text
candidate generation
→ local geometry validation
→ immediate route feasibility probe
→ reachable only in normal pool
```

“Generate candidates first and probe later” is treated as nearly forbidden. Details in `asteroid_lab_10_development_sequence.md` Sequence 3.

## Greedy rim installation forbidden (required)

Candidate Generator **does not commit extractor / extension to the layout.** (Same for belt·pipe entities.)

This phase performs only the following:

```text
BundleCandidate generation
local geometry validation
low-cost route feasibility probe
normal pool / rejected separation
```

**Selection** is done by Phase 6 Evolutionary Search; **commitment** is done by Phase 7 Incremental Commit.

`ExtractorPlacementPolicy.RIM_ONLY` and doc **rim-only** expressions are **candidate generation constraints** (extractor anchor coord ∈ `rim_cells`), not a **greedy pass that installs in order at feasible rim positions**.

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

`ExtractorPlacementPolicy` determines **only how to open the candidate pool**. v0 default `RIM_ONLY` **restricts extractor anchor to `rim_cells`** to reduce combinatorial breadth (not placed across all mineable). **Unrelated to installation order·immediate commit**.

`route_probe_goal_priority_weight` is passed to Phase 4 `RouteProbeInput.goal_priority_weight`.

When `max_candidates` is not `None`, after **normal pool (`normal_candidates`) is finalized**, if candidate count exceeds the cap, trim. `rejected_candidates` are not counted toward the cap. **Sort key before trimming (v0 canonical, deterministic):**

```text
1) base_score descending
2) route_probe_result.cost ascending
3) candidate_id ascending
```

Then keep only the first `max_candidates`.

When `allow_diagnostic_unreachable=True`, unreachable candidates may remain in `rejected_candidates` or a separate diagnostic list, **not in normal pool**.

## Catalog-native generation (Track D+ PR-3)

Production `generate_candidates` enumerates `CatalogPlacementSpec` values from
`OptimizationInput.catalog_slice` via `build_catalog_placement_specs`. Every normal
`BundleCandidate` sets `catalog_placement_ref` at generation time.
`build_pattern_library()` / `lin_*` patterns are **test-only** (`synthetic_lin_patterns` marker).

## Candidate equivalence / dedupe (combinatorial explosion mitigation)

`rim_cell × pattern × rotation × transport_kind × goal matching` etc. can inflate candidate count. **Before passing to evolution**, collapse equivalent candidates to one.

### `CandidateEquivalenceKey`

If **occupied geometry·output stub·throughput contract·topology_signature** are identical, they are near-duplicates from search·fitness perspective. v0 canonical key (field names adjustable in implementation, **semantics preserved**):

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

When the same key appears multiple times, **keep only one**. Representative selection tie-break (v0 canonical): first by `candidate_id` ascending.

Apply dedupe **before `max_candidates` trimming** so trimming is not random but **score-sorted after equivalence reduction**.

### `CandidateSpatialHash` (optional)

Coordinate-based bucketing is an **optional optimization**. Determinism·equivalence key canonical form is `CandidateEquivalenceKey`.

## Output

Separate successful and rejected candidates **by type** to fix “normal pool = success only” near compile time.

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

Path cost uses **`route_probe_result.cost` only** (no duplicate `route_cost` field).

Do **not** construct `BundleCandidate` directly; use factory/builder only so success contract such as `route_probe_result.reachable`·`reached_goal` is asserted in one place.

Goal kind uses **`route_probe_result.reached_goal.goal_kind` only** (no alias fields like `matched_goal_kind`).

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

`route_probe_result` is the first-pass probe result in **candidate phase**.

- Reused in fitness·diagnostic·pool re-evaluation.
- **incremental commit** phase must always re-run probe (docs Phase 5·7).

### topology_signature

If candidate granularity bundles only `extractor + extensions + stub`, genome becomes bloated when later mutation wants to change **extension topology only**.

In v0, `topology_signature` identifies **geometry·attachment·stub direction·throughput·transport kind** as a **deterministic string** (or fixed hex string from integer hash). When reviewing v1 `PlacementGene` / `TopologyGene` / `RoutingPreferenceGene` split, extend field set so **string meaning does not diverge**.

**Recommended inclusion (serialize in deterministic order):**

```text
pattern_id
linear_extension_count (0~3)
rotation·symmetry canonical id (pattern library canonical rotation id)
extractor direction / extension chain direction summary (fixed to one enum order in project)
output_stub·output_dir
transport_kind
base_throughput (or base_throughput bucket)
sorted listing or deterministic hash of occupied_cells (coord lex order)
```

Short abbreviation-only strings like `lin_e_len3_outE` cause **signature drift** as pattern library grows. Include the above items **without omission** in serialization rules.

## v0 policy

```text
extractor anchor ∈ rim_cells (candidate generation constraint; not immediate installation)
extension ∈ mineable asteroid cells
output_stub = non-occupied route start
```

The loop above is **enumeration to fill the pool** only; `rim_cell` order must **not** be used as **commit order·greedy installation order.**

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

The nested `for rim_cell`·`for pattern` order is for **deterministic enumeration**. Must **not** become canonical for layout commit·commit_order (commit_order is genome `Gene.commit_order`, Phase 7).

## Reject reasons

Doc listed values map 1:1 to **`CandidateRejectReason` enum** members (no free strings).

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

Unreachable candidates are not placed in normal pool. Diagnostic follows `allow_diagnostic_unreachable` policy.

## Invariant

```text
[ ] Candidate Generator does not commit placement
[ ] rim traversal order does not leak as commit order (commit_order is genome)
[ ] topology_signature deterministic (pattern·rotation·extension·stub·throughput·transport·occupied geometry summary)
[ ] CandidateEquivalenceKey dedupe applied before max_candidates truncation
[ ] occupied_cells contains extractor and extensions only
[ ] output_stub not in occupied_cells
[ ] extractor in rim_cells
[ ] extensions in mineable_cells
[ ] topology_graph·occupied consistent with island grid·`grid_contract.neighbors4` (copy `X==0` allowed)
[ ] all absolute Coord·cell sets use Server X/Y (same as Phase 1 coordinate rules)
[ ] each normal_candidates element: route_probe_result.reachable is True
[ ] normal_candidates: route_probe_result.reached_goal is not None (v0 success contract)
[ ] rejected_candidates: rejection_reason is always CandidateRejectReason
[ ] probe pass/fail before normal pool registration distinguished by type
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
[ ] rim-only extractor **candidate generation only** (no commit·greedy rim installation)
[ ] linear extension candidate generation
[ ] reject reason recording
[ ] CandidateRejectReason·RouteProbeFailureReason·ValidationIssueCode definitions
[ ] CandidateEquivalenceKey + dedupe (before max_candidates)
[ ] topology_signature field (matches serialization component docs)
[ ] CandidateGenerationConfig DTO definition
[ ] route_probe invoked in same sequence (normal pool gate)
[ ] route_probe_result recorded on successful candidates (no alias matched_goal_kind·route_cost)
[ ] BundleCandidate created only via factory/builder
[ ] CandidateGenerationResult (normal vs rejected type separation)
```
