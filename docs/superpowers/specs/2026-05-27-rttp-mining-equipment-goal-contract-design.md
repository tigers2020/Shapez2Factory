# RTTP Mining Equipment Goal Contract — Design Spec

**Document type:** Canonical product / validation contract (RTTP Layer 4 + recovery)  
**Status:** **FROZEN (pending decontamination reconciliation)** — Contract approved 2026-05-27; **MEG-C2 implementation BLOCKED** until [`2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md`](2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md) completes and RTTP retain/bridge/remove is decided · **Amended 2026-05-27** (P3 normalized exterior-pass evidence; §A `target_ratio_percent`)  
**Implementation plan:** [`2026-05-27-rttp-mining-equipment-goal.md`](../plans/2026-05-27-rttp-mining-equipment-goal.md) — **APPROVED HISTORICALLY, now SUSPENDED** by [`2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md`](2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md) — **DO NOT EXECUTE**  
**Work classification:** contract change · implementation change (phased)  
**Parent:** [`2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md`](2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md) (amends §A4 placement goal semantics)  
**Transport:** [`2026-05-26-rttp-external-void-transport-capacity-contract.md`](2026-05-26-rttp-external-void-transport-capacity-contract.md) (EVTC) · [`2026-05-30-rttp-exterior-lane-capacity-planner-design.md`](2026-05-30-rttp-exterior-lane-capacity-planner-design.md) (ELCP)  
**Reservation:** [`2026-05-27-rttp-elcp-rf-f0-private-route-overlap-reservation-policy-design.md`](2026-05-27-rttp-elcp-rf-f0-private-route-overlap-reservation-policy-design.md) (F0 merge trunk)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)

**Korean one-liner:** 467 = 외부 pass가 증명된 추출기+확장기 장비 셀 수; 벨트/파이프는 카운트하지 않고 pass 증거로만 쓴다.

**Decision (Contract Review Lead 2026-05-27 — normative):**

```text
Decision: P3 uses normalized exterior-pass evidence. ELCP lane assignment is preferred but not exclusive.
Legacy fallback can be pass-qualified only when it satisfies the same RouteGoal, reservation,
shareable-trunk, and capacity-budget contract.
```

**Exterior-pass SoT (normative):**

```text
A committed bundle is exterior-pass-qualified if its confirmed reservation reaches a valid same-kind
exterior RouteGoal (external margin, lane connector, existing trunk attachment, or equivalent exterior
connector), and the route is backed by reserved cells, shareable-trunk policy, and capacity budget
evidence.

ELCP lane assignment is preferred evidence, but not the only acceptable evidence.
Legacy fallback may count only if it can be normalized into the same exterior-pass evidence contract.
```

> **Governance (2026-05-27):** **Authoritative track = reconstruction complete-map decontamination (C+D).** This document is a **frozen reference contract** — **MUST NOT re-enter the implementation queue** (no MEG-C2, no partial aggregator wiring). Revival only after decontamination CLOSED and a new spec explicitly re-opens RTTP runtime. See decontamination design spec (link in Status).

---

## §1 — Executive summary

**Locked product choice: C** — the optimization goal is **not** “467 disjoint bundle anchors” or “467 mineable cells with any equipment,” but:

```text
target_mining_equipment_cells
  = ceildiv(mineable_cell_count × target_ratio_percent, 100)

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
    target_ratio_percent: int,
) -> int:
    if mineable_cell_count <= 0 or target_ratio_percent <= 0:
        return 0
    product = (
        Decimal(mineable_cell_count) * Decimal(target_ratio_percent) / Decimal(100)
    )
    return int(product.to_integral_value(rounding=ROUND_CEILING))
```

**Example (recovery test map):** `mineable_cell_count = 583`, `target_ratio_percent = 80` → **467**.

**Rationale:** “At least 80%” → **ceil** (`ceildiv`), not floor (466) or round. Use `target_ratio_percent` (integer percent, e.g. `80` = 80%) — not `0.80`.

**Backward compatibility:**

```text
placement_goal_count  # JSON/replay legacy key — deprecated alias for target_mining_equipment_cells
  MUST equal target_mining_equipment_cells
  MUST NOT mean "number of committed bundle IDs" in new code/docs
  Means extractor+extension equipment cells, excluding transport cells. It is not a bundle count.
  Production code MUST prefer target_mining_equipment_cells.
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

P3  The confirmed route reaches a valid same-transport exterior RouteGoal.

    Preferred evidence:
      ELCP lane assignment + route evidence (reached_elcp_lane_id, connector_goal).

    Allowed fallback evidence (normalized — same predicate envelope):
      legacy probe/reprobe reached_goal evidence,
      confirmed reservation path,
      same-kind connectivity to external margin / existing exterior trunk / external connector,
      shareable trunk policy pass,
      capacity budget evidence or derived fallback capacity accounting.

    Forbidden for numerator:
      generic void reach without a valid exterior RouteGoal contract,
      legacy fallback without normalized capacity accounting (may be structural-only),
      stub/reservation missing.

    Normative: ELCP lane assignment is preferred but not exclusive. Unlimited legacy pass without
    the same RouteGoal + reservation + shareable-trunk + capacity-budget envelope is forbidden.

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
same-kind exterior pass through merge-capable space belt/pipe trunk with capacity budget
evidence (ELCP lane assignment preferred; legacy fallback allowed only when normalized to the
same exterior-pass evidence contract). Transport route cells and exterior connector cells are
excluded from the 467 count but required as pass evidence.
```

**Pass-qualified cases (locked — P3 option 2):**

| Case | structural OK | pass-qualified numerator |
|------|:-------------:|:------------------------:|
| ELCP lane assignment + route evidence + capacity OK | yes | **count** |
| Legacy fallback + same-kind exterior `RouteGoal` + reservation + shareable trunk + capacity accounting | yes | **count** |
| Legacy fallback reaches exterior but **no** capacity accounting | yes possible | **do not count** |
| Route reaches generic void only | no / issue | do not count |
| Stub/reservation missing | no | do not count |

Rationale: P3 tests **exterior RouteGoal reach**, not “ELCP row exists.” P5 capacity budget stays normative; `legacy_elcp_fallback` is **not** a diagnostic label — it is a **normalized evidence row** that satisfies the same predicate envelope as ELCP assignment.

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
    capacity_accounting_ok: bool
    exterior_pass_evidence_kind: Literal[
        "elcp_lane_assignment",
        "legacy_normalized_exterior_pass",
    ]
```

**Field mapping to §5.3:**

| Field | Satisfies |
|-------|-----------|
| `output_stub_reserved` | P1 |
| `transport_kind` | P2 (caller supplies run kind; evidence must match) |
| `reached_elcp_lane_id is not None` | P3 preferred (ELCP lane + route evidence) |
| `reached_external_margin` | P3 fallback (same-kind exterior `RouteGoal`) |
| `shareable_trunk_overlap_only` | P4 |
| `capacity_accounting_ok` | P5 — **required for numerator**; legacy without accounting → structural-only, `exterior_pass_evidence_kind` MUST NOT be `legacy_normalized_exterior_pass` |
| `exterior_pass_evidence_kind` | `elcp_lane_assignment` (preferred) or `legacy_normalized_exterior_pass` (fallback envelope satisfied) |

**Deprecated alias:** `lane_capacity_ok` → `capacity_accounting_ok` in new code (same semantics).

```python
def has_confirmed_exterior_pass(evidence: ExteriorPassEvidence) -> bool:
    if not evidence.output_stub_reserved:
        return False
    if not evidence.shareable_trunk_overlap_only:
        return False
    exterior_route_goal_reached = (
        evidence.reached_elcp_lane_id is not None or evidence.reached_external_margin
    )
    if not exterior_route_goal_reached:
        return False
    if not evidence.capacity_accounting_ok:
        return False
    return evidence.exterior_pass_evidence_kind in (
        "elcp_lane_assignment",
        "legacy_normalized_exterior_pass",
    )
```

**Builder ownership (MEG-C2):** one function after commit (e.g. `build_exterior_pass_evidence_for_committed_bundles(...)`) — sole writer of `ExteriorPassEvidence`; aggregator and validation consume it read-only.

---

## §6 — Aggregates and DTOs

### §6.1 Plan (input)

```python
@dataclass(frozen=True)
class MiningEquipmentGoalPlan:
    mineable_cell_count: int
    target_ratio_percent: int  # integer percent, e.g. 80 = 80% (not 0.80)
    target_mining_equipment_cells: int

    @property
    def placement_goal_count(self) -> int:
        """Deprecated JSON/replay alias — same value as target_mining_equipment_cells."""
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
placement_goal_count = ceildiv(asteroid_field_cell_count × target_ratio_percent, 100)
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
| T8 | Legacy exterior reach + reservation + shareable trunk, `capacity_accounting_ok=false` → structural may pass; `has_confirmed_exterior_pass` false; numerator **+0** |
| T9 | `legacy_normalized_exterior_pass` + `capacity_accounting_ok=true` + same-kind `RouteGoal` → `has_confirmed_exterior_pass` true |

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
| 2026-05-27 | Contract Review Lead | **§A/C approved** — `target_ratio_percent`, `ceildiv`; **P3 option (2)** normalized exterior-pass; legacy fallback counts only with capacity accounting; unlimited legacy pass forbidden |

**Root cause (review):** The product failure was not “467 is impossible” but “467 pass-qualified mining equipment cells were never enforced as the optimization goal.”

---

## §13 — Spec self-review (post-review 2026-05-27)

| Check | Result |
|-------|--------|
| Placeholders | None |
| Contradictions | ceil target vs floor(466) resolved — **ceil normative** |
| Scope | MEG-C1/C2: measurement + gates only; 467 in C3 |
| Ambiguity | P3 = exterior `RouteGoal` reach, not ELCP-row-only; legacy normalized vs structural-only split explicit |
| Predicate inputs | Centralized in `ExteriorPassEvidence`; `has_confirmed_exterior_pass` does not branch on `elcp_plan_active` for numerator denial |
| Layout vs goal | Shortfall only in `optimization_goal` block |
| Free-form issue strings | `mining_equipment_goal_shortfall` enum in implementation plan |

---

## §14 — References

- [`django_apps/asteroid_lab/services/placement_goal.py`](../../../django_apps/asteroid_lab/services/placement_goal.py) — current goal plumbing  
- [`django_apps/asteroid_lab/optimization/validation/catalog_layout_validation.py`](../../../django_apps/asteroid_lab/optimization/validation/catalog_layout_validation.py) — merge point for two-layer validation  
- [`django_apps/asteroid_lab/optimization/routing/lift_lane_domain.py`](../../../django_apps/asteroid_lab/optimization/routing/lift_lane_domain.py) — void traversable, step costs  
