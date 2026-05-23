# RTTP v1 — MacroBundleT3 Design Spec

**Status:** Approved for algorithm direction (2026-05-23). **No implementation** until [`2026-05-23-rttp-v1-macrobundle-t3.md`](../plans/2026-05-23-rttp-v1-macrobundle-t3.md) slices (PR-A..H) execute.  
**Owner:** asteroid-lab / RTTP  
**Parent:** [`2026-05-22-rttp-hybrid-c-layout-design.md`](2026-05-22-rttp-hybrid-c-layout-design.md) § v1 — MacroBundle T3  
**Prerequisite:** RTTP Hybrid C **v0.1** gates RTTP-G1~G8 green on `master`; v0.2 replay parity + 3B-S Lab compose merged  
**Out of scope here:** DB `run_solver` + `:rttp` integration hardening (separate small PR after v1 plan approval)

---

## Purpose

Lock the **v1 algorithm direction** before more code lands:

```text
MacroBundleT3 is NOT “one BundlePattern with 3 miners”.
MacroBundleT3 IS “three existing BundleCandidate footprints + shared lift/trunk intent,
                 exposed as ONE selection/commit slot”.
```

This spec defines DTOs, invariants, selection/commit contracts, replay surface, validation boundary, and **v1-only gates** (RTTP-G9+). Implementation is a follow-on plan; **do not** extend `BundlePattern` with triple-miner templates.

---

## Type hierarchy (normative)

| Type | Layer | Role |
|------|-------|------|
| `BundlePattern` | 2 | Single-extractor linear template (extension 0..3, one rotation family) |
| `BundleCandidate` | 2 | One pattern instance + **per-child** route probe + normal/rejected pool membership |
| `MacroBundleT3` | 2→3 bridge | Frozen triple of **child** `BundleCandidate` refs + shared route intent metadata |
| `MacroBundleCandidate` | 2 output | One macro row in the macro normal pool (probe + equivalence at macro level) |
| `PlacementGenome` | 3 | Ordered list of **macro slot ids** (v1); each id resolves to one `MacroBundleT3` |

```text
BundlePattern        → local footprint template
BundleCandidate      → probed single bundle
MacroBundleT3        → composition of 3 BundleCandidates + shared intent
MacroBundleCandidate → one genome/regret/competition unit
```

**Forbidden (v1):**

- `BundlePattern` with `miner_count == 3` or “T3 pattern id”
- Triple/Y merger auto-placement on trunk (deferred v1+ optional)
- Macro slot that commits children in separate genome positions without atomic macro wrapper

---

## 1. MacroBundleT3 DTO

Frozen dataclass (names stable once shipped):

```python
@dataclass(frozen=True, slots=True)
class MacroBundleT3:
    macro_id: str                          # deterministic, content-addressed
    child_a_id: str                        # BundleCandidate.candidate_id
    child_b_id: str
    child_c_id: str
    children: tuple[BundleCandidate, ...]  # len == 3, sorted by child_*_id
    shared_lift_stub_plan: SharedLiftStubPlan
    shared_ring_port_intent: SharedRingPortIntent
    combined_occupied_cells: frozenset[Coord]  # union(children.occupied_cells); disjoint union
    macro_throughput_factor: int           # aggregate policy (see §8)
    topology_signature: tuple[str, ...]    # child pattern_ids + relative offset signature
```

Supporting frozen types:

```python
@dataclass(frozen=True, slots=True)
class SharedLiftStubPlan:
    """Route-only cells; NOT equipment footprint."""
    lift_column_coords: frozenset[Coord]   # platform→lift edges materialized on domain
    trunk_entry_coord: Coord | None        # lane entry on trunk_mask after shared lift
    reserved_route_cells: frozenset[Coord] # subset of route cells shared by all children

@dataclass(frozen=True, slots=True)
class SharedRingPortIntent:
    """Skeleton-relative; does not add occupied_cells."""
    primary_ring_port_coord: Coord
    preferred_dir: str                     # N|E|S|W; matches skeleton.ring_ports when possible
    secondary_port_coords: frozenset[Coord]  # optional alternates for probe scoring only
```

**`macro_id` derivation (deterministic):**

```text
macro_id = hash_sorted(
  child_a_id, child_b_id, child_c_id,
  shared_lift_stub_plan canonical json,
  shared_ring_port_intent canonical json,
)
```

Wire format: lowercase hex or existing `candidate_id` charset; **no free-form** ids in persisted replay.

---

## 2. Child BundleCandidate composition rules

A valid `MacroBundleT3` references exactly **three** distinct `BundleCandidate` instances from the **same** `CandidateGenerationResult.normal_candidates` pass (same skeleton + `OptimizationInput` snapshot).

| Rule | Requirement |
|------|-------------|
| Count | `len(children) == 3` |
| Distinct ids | `child_a_id`, `child_b_id`, `child_c_id` pairwise distinct |
| Pool membership | Each child was `reachable is True` at generation-time probe |
| Transport | All children share `transport_kind` (macro is single belt family per run) |
| Policy | Each child satisfied `ExtractorPlacementPolicy` at generation (v1 default `INTERIOR_AND_RIM`) |
| Pattern | Each child uses a **v0.1** `BundlePattern` (extension 0..3); no macro-only pattern table |
| Ordering | `children` sorted by `candidate_id` ascending for canonical `macro_id` |

**Composition search (v1 compiler — implementation detail, contract only):**

- Input: deduped `BundleCandidate` pool + `RttpSkeleton` + `OptimizationInput`
- Output: zero or more `MacroBundleCandidate` rows
- v1 **does not** require enumerating all C(n,3); use skeleton-guided triples (shared ring port neighborhood, compatible lift columns, throughput band) with a hard cap `max_macro_candidates` in config

---

## 3. Internal `occupied_cells` disjoint

```text
∀ i ≠ j: children[i].occupied_cells ∩ children[j].occupied_cells = ∅
```

- `combined_occupied_cells = ⋃ children[k].occupied_cells` (disjoint union equals set union)
- Violation → macro rejected at compile time with `MacroRejectReason.CHILD_OCCUPANCY_OVERLAP` (StrEnum)
- Shared lift/trunk cells **must not** appear in any `occupied_cells` (already v0.1 rule for routes)

---

## 4. `shared_lift_stub_plan` meaning

**Intent:** Three extractors share one lift column / trunk entry story instead of three independent lift escapes.

| Field | Semantics |
|-------|-----------|
| `lift_column_coords` | Cells reserved for vertical lift edges (route layer only) |
| `trunk_entry_coord` | Single attachment point on `skeleton.trunk_mask_cells` (or existing trunk seed) |
| `reserved_route_cells` | Union of lift column + trunk segment shared by all child probes at **macro** compile time |

**Probe contract (macro generation):**

1. Each child’s `output_stub` must reach `trunk_entry_coord` (or declared goal set) via child probe **or** shared segment declared in plan.
2. Macro-level probe runs **after** children are chosen: validates shared segment ∪ per-child stub→goal with **one** domain snapshot (no commit mutations).

**Forbidden:** Treating shared lift cells as miner/building footprint.

---

## 5. `shared_ring_port_intent` meaning

**Intent:** Align three child output directions with skeleton ring geometry for stable regret scoring (extends v0.1 `rim_port_alignment`).

- `primary_ring_port_coord` must be a `skeleton.ring_ports` coord or external-margin goal adjacent to rim.
- `preferred_dir` matches `RingPort.preferred_dir` when port exists at that coord.
- `secondary_port_coords` used only for tie-break / diagnostics; **not** extra occupied cells.

Macro compile rejects when no ring port within configured graph distance of the triple’s centroid anchor ( `MacroRejectReason.RING_PORT_MISMATCH` ).

---

## 6. Macro candidate generation conditions

`MacroBundleCandidate` enters the **macro normal pool** only if all hold:

| # | Condition |
|---|-----------|
| M1 | §2 composition rules |
| M2 | §3 disjoint occupancy |
| M3 | §4 shared lift plan validates on static route domain |
| M4 | §5 ring port intent consistent with skeleton |
| M5 | Macro probe reachable (bounded BFS budget; same order of magnitude as v0.1 `max_expansions`) |
| M6 | `combined_occupied_cells ⊆ inp.mineable_cells` |
| M7 | No child `occupied_cells` intersects `inp.protected_corridor_cells` |
| M8 | No overlap with `existing_trunk_cells` except via **route** reservation (footprint forbidden on trunk seed) |

Rejected macros go to `macro_rejected` with `MacroRejectReason` StrEnum (no free strings).

**Pool separation:**

```text
normal_candidates          → BundleCandidate (v0.1, unchanged)
macro_normal_candidates    → MacroBundleCandidate (v1)
```

v1 selection operates on **macro** pool only; single-bundle candidates are inputs to macro compiler, not competing genome slots (unless config flag `allow_singleton_genome_slots` — default **false** for v1).

---

## 7. Macro equivalence key

Analogous to v0.1 `CandidateEquivalenceKey` but at macro granularity:

```python
@dataclass(frozen=True, slots=True)
class MacroEquivalenceKey:
    combined_occupied_cells: frozenset[Coord]
    child_equivalence_keys: tuple[CandidateEquivalenceKey, ...]  # sorted
    shared_lift_signature: tuple[Coord, ...]   # sorted lift_column_coords + trunk_entry
    transport_kind: TransportKind
    macro_throughput_factor: int
```

Dedupe: keep lowest `macro_id` per key before regret (mirror `dedupe_candidates`).

---

## 8. Macro score / regret priority

Extend v0.1 greedy-regret **macro slot** competition (same `SelectionConfig` weights unless v1 config adds `macro_lambda`):

```text
priority(m) =
    base_macro_score(m)
  + λ * regret(m)
  - inlet_fragility_macro(m)
  - fragmentation_macro(m)
```

| Term | Definition |
|------|------------|
| `base_macro_score` | `Σ child.throughput_factor` with optional rim alignment bonus per child; minus aggregate probe cost |
| `regret(m)` | Best alternative macro lost when `m` is chosen — scarcity on **macro equivalence class** or anchor triple |
| `inlet_fragility_macro` | Penalize shared trunk entry if already in `committed_route_cells` |
| `fragmentation_macro` | v0.1-style isolated mineable fraction after `combined_occupied_cells` |

**Genome:** `PlacementGenome.commit_order: tuple[str, ...]` lists **`macro_id`** strings only (RTTP-G4 v1: order ≠ rim scan, ≠ child id lexicographic).

---

## 9. Macro commit atomicity

**Normative:** One macro genome slot commits **all three** children in a single atomic transaction.

```text
incremental_commit_macro(macro_id) → CommitResult
  either all three child candidate_ids ∈ committed_ids
  or none of the three are added (rollback to pre-macro domain version)
```

Per-child `incremental_commit` calls are **internal**; external API exposes macro only.

**Re-probe:** After each successful macro, domain version increments (RTTP-G6 analog). Commit-time reprobe uses post-domain shared trunk reservations from §4.

**Inlet rule:** If any child would trigger `INLET_ON_SHARED_TRANSPORT` against shared trunk segment → whole macro fails with `CommitConflictReason` (existing enum).

---

## 10. Failure rollback / partial commit

| Policy | v1 decision |
|--------|-------------|
| Partial macro commit | **Forbidden** — all-or-nothing per macro slot |
| Domain rollback | Restore `CommitDomainState` snapshot taken before macro attempt |
| LNS | May swap macro slot or reorder; **must not** leave 1-of-3 children committed |
| Child-level commit in genome | **Forbidden** in v1 default pipeline |

`CommitConflictReason` may add `MACRO_CHILD_CONFLICT` if internal child ordering fails mid-macro (implementation), but external observers see macro failure only.

---

## 11. Replay milestone payload (minimum fields)

v1 continues four canonical product milestones (`rttp.*`). Macro phase enriches **metrics** and **cell_overlay_json** only; **no new** product `event_type` strings in v1 unless 3B-S contract amendment is approved separately.

Minimum additions on existing milestones:

| Milestone | Extra `metrics` | Extra overlay |
|-----------|-----------------|---------------|
| `rttp.route_domain_snapshot` | `macro_compile_candidate_count` (optional 0 pre-compile) | unchanged |
| `rttp.candidate_pool_snapshot` | `macro_normal_count`, `macro_rejected_count`, `child_normal_count` | highlight `combined_occupied_cells` outline + shared lift segment |
| `rttp.genome_selection_snapshot` | `commit_order` (macro_ids), `macro_count_selected` | per-macro child anchors |
| `rttp.commit_domain_snapshot` | `committed_macro_ids`, `committed_child_ids` | committed route cells incl. shared lift |

**Rules (inherit v0.2 / 3B-S):**

- Replay is **not** algorithm input
- Overlays clipped to mineable footprint at compose time
- No `render_mode: inherited_snapshot` on product frames

---

## 12. Validation read-only

`validate_final_layout` (or `validate_macro_layout` wrapper) remains **assert-only**:

- No route repair, no placement mutation, no topology fix
- Validates: disjoint committed footprints, shared route ⊆ reserved cells, all committed children ⊆ mineable
- `ValidationIssueCode` StrEnum extension allowed in v1 **only** with spec + test updates (no ad-hoc strings)

Macro validation runs **after** full genome commit sequence, same as v0.1.

---

## 13. v1 gate tests (RTTP-G9+)

Implement only after this spec is approved. Suggested gates:

| Gate | Test intent |
|------|-------------|
| **RTTP-G9** | Macro compiler: valid triple → one `MacroBundleCandidate`; overlap triple → `CHILD_OCCUPANCY_OVERLAP` |
| **RTTP-G10** | Macro probe: shared lift plan required; unreachable shared trunk → rejected |
| **RTTP-G11** | Macro equivalence dedupe deterministic |
| **RTTP-G12** | Regret selects macro slot; `commit_order` is macro_ids, not child candidate_ids |
| **RTTP-G13** | Atomic commit: success commits 3 ids; reprobe failure commits 0 |
| **RTTP-G14** | Pipeline greenfield with macro-only genome deterministic (two runs equal) |
| **RTTP-G15** | Replay on/off parity unchanged for `PipelineResult` (extends RTTP-G8) |
| **RTTP-G16** | `optimization/` does not import Lab compose modules; replay sink orchestration-only |

**Test fixtures:**

- Extend `greenfield_optimization_input` with macro compiler smoke
- New `macro_triple_greenfield` synthetic (three non-overlapping anchors + shared lift) — small grid
- Optional: one reconstruction fixture line after macro pipeline exists (P1)

**Narrow pytest (future plan):**

```bash
python -m pytest tests/unit/asteroid_lab/test_rttp_macro_bundle_t3.py -v
```

---

## Non-goals (v1)

- Dense interior tetris / macro slot packing beyond fixed triple compiler
- Merger nodes on trunk
- Trunk-layer JPS / CP-SAT
- `BundlePattern` “3-extension mega-pattern”
- Using replay frames as solver input
- Second product replay timeline or `inherited_snapshot` revival

---

## Relationship to v0.1 (must not break)

| v0.1 artifact | v1 change |
|---------------|-----------|
| `BundlePattern` / `candidate_generator` | Remains; feeds macro compiler |
| `BundleCandidate` probe | Per-child probe still required before macro pairing |
| `PlacementGenome` | Same type; **semantic** shift to macro ids when macro-only mode |
| RTTP-G1~G8 | Stay green; v1 adds G9+ |
| Four `rttp.*` milestones | Same event types; richer metrics/overlays |

---

## Locked decisions (2026-05-23)

| ID | Question | Decision |
|----|----------|----------|
| **OD-MACRO-1** | Allow singleton + macro slots in same genome? | **No.** v1 selection is **macro-only** when `macro_only_mode=True`. `PlacementGenome.commit_order` lists **`macro_id` only**. `allow_singleton_genome_slots` default **false**; do not implement mixed-mode regret in v1. |
| OD-MACRO-2 | `macro_throughput_factor` = sum or min of children? | **Sum** (CANON throughput story) |
| OD-MACRO-3 | Max macro candidates enumerated per run? | `RttpPipelineConfig.max_macro_candidates: int = 64` |
| OD-MACRO-4 | New replay `event_type` for macro-only debug? | **No** (metrics on existing four `rttp.*` milestones) |
| OD-MACRO-5 | LNS swaps macros or re-runs compiler? | **Swap macro slots** only; compiler deterministic |

---

## Approval checklist

- [x] Hierarchy: MacroBundleT3 composes BundleCandidates, not BundlePatterns
- [x] Atomic macro commit (no partial 1-of-3)
- [x] Shared lift/trunk = route-only reservation
- [x] RTTP-G9+ gate list accepted
- [x] Replay / validation boundaries unchanged
- [x] OD-MACRO-1: macro-only genome (no singleton+macro mix)
- [x] Implementation plan: [`2026-05-23-rttp-v1-macrobundle-t3.md`](../plans/2026-05-23-rttp-v1-macrobundle-t3.md)

---

## References

- [`2026-05-22-rttp-hybrid-c-layout-design.md`](2026-05-22-rttp-hybrid-c-layout-design.md)
- [`2026-05-23-rttp-v0.2-replay-parity-design.md`](2026-05-23-rttp-v0.2-replay-parity-design.md)
- [`2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md`](2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md)
- [`documents/Algorithm/asteroid_lab_10_development_sequence.md`](../../../documents/Algorithm/asteroid_lab_10_development_sequence.md)
