# P1-ELCP-RF-A2 — Selection Universe Attrition — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Read-only Layer 1 forensics — prove how `normal_candidate_count=356` becomes `commit_order_len=59` under greedy-regret with `placement_goal_count=467`, via per-round trace + normal-pool attrition ledger; re-gate `lane_capacity_shortfall` B-spec only (no nomination).

**Architecture:** `harness/investigation/rttp_greedy_regret_selection_trace.py` mirrors the `select_genome` while-loop in `greedy_regret.py` (same `dedupe_candidates`, `_overlaps`, `_fot_conflict`, scoring helpers) and emits §5.1 round rows + §6 attrition rows. A parity assertion requires `trace.commit_order == select_genome(...).commit_order`. Recovery-map integration reuses the Gate A `run_rttp_pipeline` fixture pattern from P1-ELCP-RF; captures `generation.normal_candidates`, `selection_goal`, and production `genome` from pipeline (patch or step metrics). **No production edits.**

**Tech Stack:** Python 3.12+, pytest, ruff; `greedy_regret`, `placement_goal`, `run_rttp_pipeline`, `rttp-core-recovery-test-map`.

**Design spec:** [`docs/superpowers/specs/2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-design.md`](../specs/2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-design.md)

---

## File structure

| File | Responsibility |
|------|----------------|
| `harness/investigation/rttp_greedy_regret_selection_trace.py` | DTOs, `trace_greedy_regret_selection`, attrition builder, parity, reconciliation summary |
| `tests/investigation/test_rttp_greedy_regret_selection_attrition.py` | Synthetic parity + recovery-map integration |
| `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-report.md` | Trace tables, H1–H7 verdicts, 59 verdict, B-spec re-gate |
| `documents/ai/current_plan.md` | ACTIVE A2 → CLOSED when report + acceptance |

**Not modified:** `greedy_regret.py`, `pipeline.py`, `incremental_commit.py`, selection policy, placement percents.

---

## Spec → plan coverage

| Spec § | Task |
|--------|------|
| Layer 1 only (356→59) | Tasks 1–7; no commit ledger |
| §5.1 per-round trace | Task 1–2 |
| §6 attrition classes + 95% gate | Task 2–3 |
| §5 H1–H7 prove/reject | Task 6 (report) |
| §9 acceptance sentences | Task 3, 6 |
| §10 B-spec re-gate only | Task 6 |
| Universe 9328→356→59→3 | Task 5 |
| No production change | All tasks |

---

### Task 0: Queue + spec/plan linkage

**Files:**
- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/specs/2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-design.md` (plan path in header — already linked)

- [ ] **Step 1: Ensure `current_plan.md` has ACTIVE A2 row** pointing to spec + this plan; P1-ELCP-RF remains REOPENED until A2 CLOSED.

- [ ] **Step 2: Commit** (only if user requests commit)

```bash
git add documents/ai/current_plan.md docs/superpowers/plans/2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition.md
git commit -m "docs: add P1-ELCP-RF-A2 selection attrition plan"
```

---

### Task 1: Investigation DTOs + enums

**Files:**
- Create: `harness/investigation/rttp_greedy_regret_selection_trace.py`

- [ ] **Step 1: Add frozen dataclasses and enums**

```python
"""Read-only greedy-regret selection trace (P1-ELCP-RF-A2; not solver input)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from django_apps.asteroid_lab.optimization.coords import Coord


class SelectionStopReason(StrEnum):
    GOAL_REACHED = "goal_reached"
    POOL_EXHAUSTED = "pool_exhausted"


class AttritionClass(StrEnum):
    SELECTED = "selected"
    DEDUPE_REMOVED = "dedupe_removed"
    REMOVED_BY_OVERLAP = "removed_by_overlap"
    REMOVED_BY_FOT = "removed_by_fot"
    UNPICKED_SCORE = "unpicked_score"
    UNKNOWN_ATTRITION = "unknown_attrition"


@dataclass(frozen=True, slots=True)
class GreedyRegretRoundTraceRow:
    round_index: int
    pool_size_before: int
    resolved_goal: int
    selected_candidate_id: str
    selected_occupied_cells_count: int
    selected_output_stub: Coord
    selected_fot_cell: Coord
    removed_by_overlap_count: int
    removed_by_fot_conflict_count: int
    removed_by_other_count: int
    pool_size_after: int
    commit_order_len_so_far: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "round_index": self.round_index,
            "pool_size_before": self.pool_size_before,
            "resolved_goal": self.resolved_goal,
            "selected_candidate_id": self.selected_candidate_id,
            "selected_occupied_cells_count": self.selected_occupied_cells_count,
            "selected_output_stub": list(self.selected_output_stub),
            "selected_fot_cell": list(self.selected_fot_cell),
            "removed_by_overlap_count": self.removed_by_overlap_count,
            "removed_by_fot_conflict_count": self.removed_by_fot_conflict_count,
            "removed_by_other_count": self.removed_by_other_count,
            "pool_size_after": self.pool_size_after,
            "commit_order_len_so_far": self.commit_order_len_so_far,
        }


@dataclass(frozen=True, slots=True)
class NormalCandidateAttritionRow:
    candidate_id: str
    attrition_class: AttritionClass
    round_index: int | None
    anchor_coord: Coord

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "attrition_class": self.attrition_class.value,
            "round_index": self.round_index,
            "anchor_coord": list(self.anchor_coord),
        }


@dataclass(frozen=True, slots=True)
class GreedyRegretSelectionTraceResult:
    commit_order: tuple[str, ...]
    stop_reason: SelectionStopReason
    resolved_goal: int
    pool_size_after_dedupe: int
    normal_candidate_count: int
    dedupe_removed_count: int
    round_trace: tuple[GreedyRegretRoundTraceRow, ...]
    attrition_ledger: tuple[NormalCandidateAttritionRow, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "commit_order": list(self.commit_order),
            "stop_reason": self.stop_reason.value,
            "resolved_goal": self.resolved_goal,
            "pool_size_after_dedupe": self.pool_size_after_dedupe,
            "normal_candidate_count": self.normal_candidate_count,
            "dedupe_removed_count": self.dedupe_removed_count,
            "round_trace": [row.to_dict() for row in self.round_trace],
            "attrition_ledger": [row.to_dict() for row in self.attrition_ledger],
        }
```

- [ ] **Step 2: Run ruff on new file**

```bash
python -m ruff check harness/investigation/rttp_greedy_regret_selection_trace.py
```

Expected: PASS (may need import fixes after Task 2).

---

### Task 2: Mirror loop + attrition ledger

**Files:**
- Modify: `harness/investigation/rttp_greedy_regret_selection_trace.py`

- [ ] **Step 1: Implement `trace_greedy_regret_selection`**

Mirror `select_genome` in `greedy_regret.py` lines 141–206:

- Import production helpers: `dedupe_candidates`, `_overlaps`, `_fot_conflict`, `_base_score`, `_regret_scores`, `_priority`, `fixed_output_transport_cell`, `SelectionConfig`.
- Before loop: `deduped = dedupe_candidates(normal_candidates)`; record `dedupe_removed` ids = normal ids − deduped ids.
- Each round **before** pick: `pool_size_before = len(pool)`.
- After pick, classify each removed candidate (not the winner):
  - if `_overlaps(c, committed_occ)` → `REMOVED_BY_OVERLAP`, record `round_index`
  - elif `_fot_conflict(...)` → `REMOVED_BY_FOT`, record `round_index`
  - else → increment `removed_by_other_count` (should stay 0; if not, document in report).
- After filter: `pool_size_after = len(pool)`.
- `stop_reason`: `GOAL_REACHED` if `len(commit_order) >= resolved_goal` else `POOL_EXHAUSTED`.
- **After loop (attrition — corrected):**
  - if `stop_reason == GOAL_REACHED`: remaining `pool` members → `UNPICKED_SCORE`
  - if `stop_reason == POOL_EXHAUSTED`: remaining `pool` must be empty; **no** `UNPICKED_SCORE` from remaining pool
- Winners → `SELECTED`.
- Pre-loop dedupe losers → `DEDUPE_REMOVED`.
- Any normal id missing from ledger → `UNKNOWN_ATTRITION`.

Export:

```python
def trace_greedy_regret_selection(
    normal_candidates: tuple[BundleCandidate, ...],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    *,
    config: SelectionConfig | None = None,
    goal_count: int | None = None,
) -> GreedyRegretSelectionTraceResult:
    ...
```

- [ ] **Step 2: Implement parity helper**

```python
def assert_selection_trace_parity(
    *,
    production: PlacementGenome,
    trace: GreedyRegretSelectionTraceResult,
) -> None:
    assert production.commit_order == trace.commit_order, (
        f"trace commit_order mismatch: {len(production.commit_order)} vs {len(trace.commit_order)}"
    )
```

Call `select_genome` with identical args inside test or helper `build_selection_trace_with_parity`.

- [ ] **Step 3: Implement coverage + reconciliation helpers**

```python
def attrition_class_coverage(trace: GreedyRegretSelectionTraceResult) -> float:
    removed = [
        row
        for row in trace.attrition_ledger
        if row.attrition_class is not AttritionClass.SELECTED
    ]
    if not removed:
        return 1.0
    known = sum(
        1
        for row in removed
        if row.attrition_class is not AttritionClass.UNKNOWN_ATTRITION
    )
    return known / len(removed)


def build_universe_reconciliation_row(
    *,
    candidate_pool_total: int,
    normal_candidate_count: int,
    commit_order_len: int,
    primary_committed_count: int,
) -> dict[str, int]:
    return {
        "candidate_pool_total": candidate_pool_total,
        "normal_candidate_count": normal_candidate_count,
        "commit_order_len": commit_order_len,
        "primary_committed_count": primary_committed_count,
    }
```

- [ ] **Step 4: Ruff**

```bash
python -m ruff check harness/investigation/rttp_greedy_regret_selection_trace.py
```

---

### Task 3: Unit tests — synthetic parity + attrition

**Files:**
- Create: `tests/investigation/test_rttp_greedy_regret_selection_attrition.py`

- [ ] **Step 1: Write failing test `test_trace_matches_select_genome_on_tiny_pool`**

Use existing greedy-regret tests as fixture source if present; otherwise build 3–5 `BundleCandidate` stubs via factory in `tests/` (grep `BundleCandidate(` in `tests/unit` for pattern). Assert:

- `trace.commit_order == select_genome(...).commit_order`
- `len(trace.round_trace) == len(trace.commit_order)` when `POOL_EXHAUSTED` or equals goal rounds
- `attrition_class_coverage(trace) >= 0.95` for tiny pool

- [ ] **Step 2: Run test (expect FAIL until Task 2 complete)**

```bash
python -m pytest tests/investigation/test_rttp_greedy_regret_selection_attrition.py::test_trace_matches_select_genome_on_tiny_pool -v
```

- [ ] **Step 3: Green + ruff**

```bash
python -m pytest tests/investigation/test_rttp_greedy_regret_selection_attrition.py -v
python -m ruff check harness/investigation/rttp_greedy_regret_selection_trace.py tests/investigation/test_rttp_greedy_regret_selection_attrition.py
```

---

### Task 4: Recovery-map integration (356 → 59)

**Files:**
- Modify: `tests/investigation/test_rttp_greedy_regret_selection_attrition.py`

- [ ] **Step 1: Add `@pytest.mark.django_db` `@pytest.mark.slow` test**

Copy setup from `test_recovery_map_primary_reprobe_mass_reproduced` in `test_rttp_elcp_reprobe_forensics.py` (import map, reconstruction, `RttpPipelineConfig` with `reconstruction_max_throughput_per_min`).

Capture from pipeline run:

- `generation.normal_candidates` — patch `generate_candidates` return or read from pipeline internals via patch on `select_primary_genome` inputs (preferred: patch `select_primary_genome` wrapper to capture `normal_candidates`, `goal_count`, and returned `genome`).

After pipeline:

```python
trace = trace_greedy_regret_selection(
    normal_candidates=tuple(captured_normal),
    skeleton=skeleton,
    inp=inp,
    goal_count=captured_goal,
)
assert_selection_trace_parity(production=captured_genome, trace=trace)
```

**Test name:** `test_recovery_map_selection_attrition_trace_gate_a_parity_config`

**Docstring + comment (required):** These constants are valid **only** for `rttp-core-recovery-test-map` under **Gate A parity config** (same `RttpPipelineConfig` as P1-ELCP-RF RF.1). If they drift, treat as input baseline change—not algorithm regression—until re-baselined.

Assertions (Gate A frozen anchors — not universal):

```python
# Gate A only: rttp-core-recovery-test-map + RF.1 pipeline_config
assert trace.normal_candidate_count == 356
assert len(trace.commit_order) == 59
assert trace.resolved_goal == 467
# stop_reason: assert from trace outcome (H1 evidence); do not hard-code in report text
assert trace.stop_reason is SelectionStopReason.POOL_EXHAUSTED
assert attrition_class_coverage(trace) >= 0.95
```

Print diagnostics (allowed): `A2_ROUND_TRACE_LEN`, `A2_ATTRITION_HISTOGRAM`, `A2_STOP_REASON`.

- [ ] **Step 2: Run integration test**

```bash
python -m pytest tests/investigation/test_rttp_greedy_regret_selection_attrition.py -v -k recovery
```

Expected: PASS on Gate A config.

---

### Task 5: Cross-check step metrics + universe sanity

**Files:**
- Modify: `tests/investigation/test_rttp_greedy_regret_selection_attrition.py`

- [ ] **Step 1: In recovery test, call `extract_elcp_attempt_universe_sanity`**

Assert reconciliation:

- `candidate_pool_total == 9328` (356+8972)
- `commit_order_len == len(trace.commit_order)`
- `placement_goal_count == trace.resolved_goal`

- [ ] **Step 2: Re-run recovery test**

```bash
python -m pytest tests/investigation/test_rttp_greedy_regret_selection_attrition.py::test_recovery_map_selection_attrition_trace -v
```

---

### Task 6: Report + hypothesis verdicts + B-spec re-gate

**Files:**
- Create: `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-report.md`
- Modify: `documents/ai/current_plan.md` (A2 CLOSED; P1-ELCP-RF re-gate note)

Report sections (English):

1. **Executive** — Layer 1 question only
2. **Per-round trace** — table or CSV path reference; last row `stop_reason`
3. **Attrition histogram** — counts per `AttritionClass`
4. **H1–H7 matrix** — confirmed / rejected / inconclusive with evidence pointer
5. **Verdict on 59** — `intended_cap` | `algorithmic_side_effect` | `bug` (from trace only)
6. **Universe reconciliation** — 9328 → 356 → 59 → 3 (3 = context)
7. **B-spec re-gate** — one of BLOCKED | NARROWED_TO_COMMIT_ORDER | POOL_SCALE_CANDIDATE; **no B-spec nomination**
8. **Acceptance checklist** — copy §9 from spec with checked boxes

**Forbidden in report:** claiming overlap/FOT exhaustion without citing round trace rows; dominant B-spec bucket nomination.

- [ ] **Step 2: Mark A2 CLOSED in `current_plan.md` only when §9 all boxes true**

---

### Task 7: Narrow gate + parent report pointer

**Files:**
- Modify: `docs/superpowers/reports/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-report.md` (add § "A2 follow-up" link — do not close P1-ELCP-RF until re-gate done)

- [ ] **Step 1: Run investigation test module**

```bash
python -m pytest tests/investigation/test_rttp_greedy_regret_selection_attrition.py -v
python -m ruff check harness/investigation/rttp_greedy_regret_selection_trace.py tests/investigation/test_rttp_greedy_regret_selection_attrition.py
```

---

## Self-review (plan author)

| Spec requirement | Task |
|------------------|------|
| Per-round §5.1 fields | Task 2 |
| 95% attrition gate | Task 3–4 |
| H1 hypothesis not pre-concluded | Task 4 asserts `stop_reason` from trace; report Task 6 |
| Layer 2 out of scope | No commit mirror tasks |
| B-spec blocked | Task 6 re-gate only |
| No production change | File structure |

**Placeholder scan:** none.

---

## Execution handoff

**Plan saved to** `docs/superpowers/plans/2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition.md`.

**Options:**

1. **Subagent-Driven** — fresh subagent per task + review between tasks  
2. **Inline Execution** — this session, `executing-plans`, batch with checkpoints  

**Which approach?**
