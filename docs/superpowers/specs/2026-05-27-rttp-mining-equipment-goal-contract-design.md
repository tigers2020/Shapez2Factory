# RTTP Mining Equipment Goal Contract — Design Spec

**Document type:** Canonical product / validation contract (RTTP Layer 4 + recovery)  
**Status:** **Approved (Contract + Plan Review Lead 2026-05-27)** — MEG-C1/C2 implementation authorized  
**Implementation plan:** [`2026-05-27-rttp-mining-equipment-goal.md`](../plans/2026-05-27-rttp-mining-equipment-goal.md) — **APPROVED**, Subagent-Driven execution  
**Work classification:** contract change · implementation change (phased)  
**Parent:** [`2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md`](2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md) (amends §A4 placement goal semantics)  
**Transport:** [`2026-05-26-rttp-external-void-transport-capacity-contract.md`](2026-05-26-rttp-external-void-transport-capacity-contract.md) (EVTC) · [`2026-05-30-rttp-exterior-lane-capacity-planner-design.md`](2026-05-30-rttp-exterior-lane-capacity-planner-design.md) (ELCP)  
**Reservation:** [`2026-05-27-rttp-elcp-rf-f0-private-route-overlap-reservation-policy-design.md`](2026-05-27-rttp-elcp-rf-f0-private-route-overlap-reservation-policy-design.md) (F0 merge trunk)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)

**Korean one-liner:** 467 = 외부 pass가 증명된 추출기+확장기 장비 셀 수; 벨트/파이프는 카운트하지 않고 pass 증거로만 쓴다.

---

## §1 — Executive summary

**Locked product choice: C** — the optimization goal is **not** “467 disjoint bundle anchors” or “467 mineable cells with any equipment,” but:

```text
target_mining_equipment_cells
  = ceil(mineable_cell_count × placement_target_percent / 100)

confirmed_passed_mining_equipment_cells
  = Σ |mining_equipment_cells(bundle)|
    over committed bundles bundle
    where has_confirmed_exterior_pass(bundle) == true
```

**Mining equipment cells** = extractor tiles + extension tiles on mineable asteroid cells for the active `transport_kind`. **Transport route cells** (belt, pipe, trunk, stub, exterior connector, void-only route) are **excluded from the numerator** but **required as pass evidence**.

This spec separates:

1. **Structural validation** — layout/connectivity/ELCP contract consistency (no contradictions).  
2. **Optimization goal** — pass-qualified mining equipment cell count vs target.

Treating `validation_passed == true` when a single route line exists while **confirmed_passed_mining_equipment_cells ≪ target** is a **contract bug**, not an acceptable product outcome on representative maps.

---

## §2 — Goals and non-goals

### Goals

| ID | Goal |
|----|------|
| G1 | Stable names: `target_mining_equipment_cells`, `confirmed_passed_mining_equipment_cells` |
| G2 | `placement_goal_count` documented as **deprecated alias** for `target_mining_equipment_cells` (same integer; semantics fixed) |
| G3 | Exterior-pass predicate aligned with EVTC/ELCP + F0 merge-capable trunk |
| G4 | Two-layer validation + explicit run status (`success` / `partial_success` / `fail`) |
| G5 | Issue code `mining_equipment_goal_shortfall` with structured payload |
| G6 | Replay/solver metrics expose numerator, transport debug metrics, and shortfall |

### Non-goals (this spec)

| Item | Disposition |
|------|-------------|
| Expanding candidate pool to guarantee 467 in one PR | Phased **C3** optimization track |
| Validation repair inside `validate_final_layout` | Forbidden (B-CS3); read-only asserts only |
| Replay/artifact as algorithm input | Forbidden |
| Counting belt/pipe/trunk toward 467 | **Forbidden** |
| Replacing EVTC ceildiv or lane capacity formulas | Extend only |

---

## §3 — Terminology

| Term | Definition |
|------|------------|
| `mineable_cell_count` | Shape/fluid field platform cells from `asteroid_field_cell_count_for_placement(complete_map, transport_kind)` — same source as today’s `asteroid_field_cell_count` in `PlacementGoalPlan` |
| `mining_equipment_cells(bundle)` | Absolute coords of extractor + extension tiles for that bundle; subset ∩ `inp.mineable_cells` |
| `has_confirmed_exterior_pass(bundle)` | Predicate in §5 — all clauses required |
| `external_link` / exterior lane | ELCP `ExteriorTransportLane` connector + EVTC `RouteGoal(EXTERNAL_MARGIN)` semantics |
| `merge-capable same-kind trunk` | F0 `ShareableTrunkCells` / `commit_time_shareable_trunk_cells` policy at commit time |

---

## §4 — Target formula (normative)

```python
from decimal import Decimal, ROUND_CEILING

def target_mining_equipment_cells(
    *,
    mineable_cell_count: int,
    placement_target_percent: int,
) -> int:
    if mineable_cell_count <= 0 or placement_target_percent <= 0:
        return 0
    product = (
        Decimal(mineable_cell_count) * Decimal(placement_target_percent) / Decimal(100)
    )
    return int(product.to_integral_value(rounding=ROUND_CEILING))
```

**Example (recovery test map):** `mineable_cell_count = 583`, `placement_target_percent = 80` → **467**.

**Rationale:** “At least 80%” → **ceil**, not floor (466) or round.

**Backward compatibility:**

```text
placement_goal_count  # JSON/replay legacy key
  MUST equal target_mining_equipment_cells
  MUST NOT mean "number of committed bundle IDs" in new code/docs
```

---

## §5 — Numerator: mining equipment cells

### §5.1 Included in count

| Cell kind | Included when |
|-----------|----------------|
| Extractor tile | Bundle committed + pass-qualified + coord ∈ mineable |
| Extension tile | Same |

Derived from `BundlePattern` (`extractor_offset`, `extension_offsets`) projected to anchor coordinates (same rules as catalog candidate generation / overlay projection).

### §5.2 Excluded from count (always)

| Cell kind | Role |
|-----------|------|
| `output_stub` | Route attachment only |
| Fixed output transport (FOT) | Transport face, not mining equipment |
| Internal / external space belt or pipe | Pass **evidence** only |
| Trunk belt/pipe cells | Shared infrastructure |
| Exterior connector / `external_link` coord | Lane anchor, not mining equipment |
| Void-only route cells | Traversal only |
| Replay overlay cells | Projection only |

### §5.3 Confirmed exterior-pass predicate

Bundle `b` contributes its `mining_equipment_cells` to **confirmed_passed_mining_equipment_cells** iff:

```text
P0  b.candidate_id ∈ commit_result.committed_ids

P1  Route reservation confirmed:
    output_stub ∈ reserved_route_cells (FL-06 rules satisfied at commit)

P2  Same transport_kind throughout (shape belt vs fluid pipe)

P3  Exterior reach:
    When ExteriorLaneCapacityPlan is active for the run:
      ∃ exterior_lane_assignment row for b with valid lane_id
      AND commit-time probe reached that lane's connector_goal / ELCP goals
    When plan is absent (legacy EVTC-only path):
      route evidence reaches ≥1 RouteGoal(EXTERNAL_MARGIN) coord
      AND layout connectivity does not emit missing_exterior_route

P4  Merge-capable trunk (F0):
    ReservationCandidateCells overlap with CommittedRouteCells
    only within ShareableTrunkCells at commit (no private branch widen)
    — operationalized by existing _private_route_cell_overlap + ELCP reservation policy

P5  Lane capacity budget (when ELCP active):
    assigned_load_per_min(lane) + candidate_throughput_per_min(b) ≤ lane.capacity_per_min
    at commit time (no over-capacity assignment row)
```

**Normative sentence (English):**

```text
467 is the target count of confirmed extractor + extension equipment cells placed on
mineable asteroid cells. A cell contributes only if its owning bundle has a confirmed
same-kind exterior pass through merge-capable space belt/pipe trunk within lane capacity
when ELCP is active. Transport route cells and exterior connector cells are excluded
from the 467 count but required as pass evidence.
```

**ELCP vs legacy fallback (locked):**

| Run mode | Pass-qualified for numerator |
|----------|------------------------------|
| ELCP plan active (`reconstruction_max_throughput_per_min` set) | **P3 ELCP path only** — legacy fallback commit may be structurally valid but **does not** increment `confirmed_passed_mining_equipment_cells` unless P3–P5 satisfied via real lane assignment |
| ELCP plan absent | P3 legacy exterior reach + P4 as today |

Rationale: User contract requires `external_link lane` + `capacity budget satisfied`; bookkeeping-only lane rows without ELCP reach do not qualify.

### §5.4 Exterior-pass evidence DTO (aggregator input — normative)

Implementers MUST NOT scatter-read commit state, ELCP rows, and route overlap flags inside the aggregator. A single builder produces frozen evidence per committed bundle; the predicate and metrics read **only** this DTO.

```python
@dataclass(frozen=True)
class ExteriorPassEvidence:
    candidate_id: str
    transport_kind: TransportKind
    output_stub_reserved: bool
    reached_elcp_lane_id: str | None
    reached_external_margin: bool
    shareable_trunk_overlap_only: bool
    lane_capacity_ok: bool
```

**Field mapping to §5.3:**

| Field | Satisfies |
|-------|-----------|
| `output_stub_reserved` | P1 |
| `transport_kind` | P2 (caller supplies run kind; evidence must match) |
| `reached_elcp_lane_id is not None` | P3 (ELCP active runs) |
| `reached_external_margin` | P3 (legacy EVTC-only runs when ELCP plan absent) |
| `shareable_trunk_overlap_only` | P4 |
| `lane_capacity_ok` | P5 (when ELCP active; MUST be `true` when plan absent — builder sets default `true`) |

```python
def has_confirmed_exterior_pass(
    evidence: ExteriorPassEvidence,
    *,
    elcp_plan_active: bool,
) -> bool:
    if not evidence.output_stub_reserved:
        return False
    if not evidence.shareable_trunk_overlap_only:
        return False
    if elcp_plan_active:
        return (
            evidence.reached_elcp_lane_id is not None
            and evidence.lane_capacity_ok
        )
    return evidence.reached_external_margin
```

**Builder ownership (MEG-C2):** one function after commit (e.g. `build_exterior_pass_evidence_for_committed_bundles(...)`) — sole writer of `ExteriorPassEvidence`; aggregator and validation consume it read-only.

---

## §6 — Aggregates and DTOs

### §6.1 Plan (input)

```python
@dataclass(frozen=True)
class MiningEquipmentGoalPlan:
    mineable_cell_count: int
    placement_target_percent: int
    target_mining_equipment_cells: int

    @property
    def placement_goal_count(self) -> int:
        """Deprecated alias — same value as target_mining_equipment_cells."""
        return self.target_mining_equipment_cells
```

### §6.2 Result (output)

```python
@dataclass(frozen=True)
class MiningEquipmentGoalResult:
    target_mining_equipment_cells: int
    confirmed_passed_mining_equipment_cells: int
    confirmed_committed_bundle_count: int
    shortfall: int  # max(0, target - confirmed_passed)

    # Debug / validation (not numerator)
    confirmed_transport_route_cell_count: int
    confirmed_trunk_cell_count: int
    confirmed_external_link_touch_count: int
```

### §6.3 Bundle helper (pure)

```python
def mining_equipment_cells(
    candidate: BundleCandidate,
    *,
    mineable_cells: frozenset[Coord],
) -> frozenset[Coord]:
    """Extractor + extension absolute coords ∩ mineable."""
```

`ExteriorPassEvidence`, `has_confirmed_exterior_pass`, and `aggregate_mining_equipment_goal_result` live in a **read-only** module (e.g. `services/mining_equipment_goal.py`) — **not** imported by selection ordering.

### §6.4 Bundle count vs equipment cell count (normative distinction)

| Metric | Meaning | MUST NOT equal |
|--------|---------|----------------|
| `confirmed_committed_bundle_count` | `len(committed_ids)` with P0 only | equipment cell target |
| `confirmed_passed_mining_equipment_cells` | Σ equipment tiles on pass-qualified bundles | bundle count |

**Regression guard:** when one pass-qualified bundle has 1 extractor + 3 extensions on mineable cells, `confirmed_committed_bundle_count == 1` and `confirmed_passed_mining_equipment_cells == 4`. Tests MUST assert both values (see T7).

---

## §7 — Validation and run status

### §7.1 Two layers

```python
structural_validation_passed: bool
  = validate_final_layout(...)
    AND NOT layout_connectivity_issue_codes
    AND NOT elcp_contract_issue_codes
    # catalog validation per existing CatalogValidationMode

optimization_goal_passed: bool
  = (
      confirmed_passed_mining_equipment_cells
      >= target_mining_equipment_cells
  )
```

**Forbidden:** `validation_passed = structural_validation_passed` alone without exposing `optimization_goal_passed`.

### §7.2 Pipeline / solver run status

| structural | optimization | `run_status` | `validation_passed` (product) |
|------------|----------------|--------------|-------------------------------|
| pass | pass | `success` | `true` |
| pass | fail | `partial_success` | `false` |
| fail | * | `fail` | `false` |

Gate A tests today that allow `validation_passed` with `committed_count < target` must be **split**: structural may pass for diagnostic fixtures; **optimization_goal_passed** is the product gate for “80% equipment goal.”

### §7.3 Optimization goal block (normative — separate from layout issues)

**MUST NOT** emit `mining_equipment_goal_shortfall` inside `layout_connectivity_issue_codes` — that list is **structural** only; mixing goal shortfall there makes structural failure and goal shortfall indistinguishable in UI and Gate A.

Solver summary / replay / validation result MUST expose a dedicated block:

```json
{
  "optimization_goal": {
    "passed": false,
    "issue_code": "mining_equipment_goal_shortfall",
    "target_mining_equipment_cells": 467,
    "confirmed_passed_mining_equipment_cells": 25,
    "shortfall": 442,
    "confirmed_committed_bundle_count": 25
  }
}
```

| Field | When set |
|-------|----------|
| `passed` | `true` iff `optimization_goal_passed` |
| `issue_code` | `null` when passed; else `mining_equipment_goal_shortfall` (enum/const — no free-form strings) |
| `shortfall` | `max(0, target - confirmed_passed)` |

**Product `validation_passed`:** `structural_validation_passed AND optimization_goal.passed`.

**Throughput diagnostics (legacy):** `placement_goal_shortfall` in `ThroughputShortfallReason` MAY remain for throughput attribution; it MUST NOT be the sole signal for MEG — consumers read `optimization_goal` first.

---

## §8 — Implementation phases (recommended)

| Phase | Scope | Delivers |
|-------|--------|----------|
| **MEG-C1** | Contract only: DTOs, rename docs, `compute_target_mining_equipment_cells`, replay keys | Correct metrics language |
| **MEG-C2** | `ExteriorPassEvidence` builder + post-commit aggregator + `optimization_goal` block + split `validation_passed` | **Phase-1 done:** e.g. 25/467 → `partial_success`, `validation_passed=false`, shortfall visible — **not** 467 achievement |
| **MEG-C3** | Selection/commit toward pass-qualified **cells** (void cost, merge trunk, ELCP fallback policy, candidate coverage) | Raise `confirmed_passed_mining_equipment_cells` |
| **MEG-C4** | CI/Lab gates: `optimization_goal_passed` on evidence slug or ratio threshold | Prevent regression |

**Do not** block MEG-C1/C2 on reaching 467 — measurement and gates come before optimization.

---

## §9 — Relationship to recovery §A4

Recovery spec §A4 stated:

```text
placement_goal_count = ceil(asteroid_field_cell_count × placement_target_percent / 100)
```

**Amendment:** The formula is unchanged; the **counted unit** is now explicitly **pass-qualified mining equipment cells**, not “bundles selected in genome” or “committed_ids length.”

Diagnostic caps (`route_feasible_candidate_cap`, `non_overlapping_anchor_cap`) remain **diagnostic only** — they MUST NOT clamp `target_mining_equipment_cells`.

---

## §10 — Testing contract

| ID | Test |
|----|------|
| T1 | `target_mining_equipment_cells(583, 80) == 467` |
| T2 | Bundle with 1 extractor + 2 extensions, pass-qualified → contributes **3** |
| T3 | Same bundle, route cells only → contributes **0** |
| T4 | Committed bundle failing P4 → contributes **0** cells |
| T5 | `structural_validation_passed` true, `optimization_goal_passed` false → `validation_passed` false; `optimization_goal.issue_code == mining_equipment_goal_shortfall`; **not** in `layout_connectivity_issue_codes` |
| T6 | Replay / solver summary include `optimization_goal` block with target and confirmed_passed |
| T7 | One pass-qualified bundle: 1 extractor + 3 extensions → `confirmed_committed_bundle_count == 1`, `confirmed_passed_mining_equipment_cells == 4` |

---

## §11 — Safety invariants (re-affirmed)

| ID | Rule |
|----|------|
| INV-MEG-1 | Numerator ⊆ mineable equipment tiles only |
| INV-MEG-2 | No transport tile in numerator |
| INV-MEG-3 | Pass predicate uses commit-time state, not candidate order |
| INV-MEG-4 | No replay/NDJSON as solver input |
| INV-MEG-5 | Validation remains read-only (no repair) |

---

## §12 — Review history

| Date | Role | Outcome |
|------|------|---------|
| 2026-05-27 | Contract Architect | C locked; initial spec |
| 2026-05-27 | Contract Review Lead | **Approved** — §5.4 `ExteriorPassEvidence`, §7.3 `optimization_goal` block, T7 bundle vs cells; MEG-C2 phase-1 exit = honest 25/467 fail |

**Root cause (review):** The product failure was not “467 is impossible” but “467 pass-qualified mining equipment cells were never enforced as the optimization goal.”

---

## §13 — Spec self-review (post-review 2026-05-27)

| Check | Result |
|-------|--------|
| Placeholders | None |
| Contradictions | ceil target vs floor(466) resolved — **ceil normative** |
| Scope | MEG-C1/C2: measurement + gates only; 467 in C3 |
| Ambiguity | Predicate inputs centralized in `ExteriorPassEvidence` |
| Layout vs goal | Shortfall only in `optimization_goal` block |
| Free-form issue strings | `mining_equipment_goal_shortfall` enum in implementation plan |

---

## §14 — References

- [`django_apps/asteroid_lab/services/placement_goal.py`](../../../django_apps/asteroid_lab/services/placement_goal.py) — current goal plumbing  
- [`django_apps/asteroid_lab/optimization/validation/catalog_layout_validation.py`](../../../django_apps/asteroid_lab/optimization/validation/catalog_layout_validation.py) — merge point for two-layer validation  
- [`django_apps/asteroid_lab/optimization/routing/lift_lane_domain.py`](../../../django_apps/asteroid_lab/optimization/routing/lift_lane_domain.py) — void traversable, step costs  
