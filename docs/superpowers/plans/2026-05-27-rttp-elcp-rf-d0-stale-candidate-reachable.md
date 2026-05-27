# P1-ELCP-RF-D0 — stale_candidate_reachable Attribution — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Read-only Gate A forensics on `GREEDY_REGRET_OVERLAP_PACK` — enrich all `stale_candidate_reachable` ledger rows with per-row attribution, domain-diff signals, histogram, and `ElcpD0Verdict`; publish 34-row report artifact. No production changes.

**Architecture:** Reuse C0 Gate A fixture + primary capture; extend M1 mirror walk with post-success domain snapshots; `rttp_elcp_d0_stale_attribution.py` filters stale rows, classifies `ElcpStaleAttributionClass`, computes verdict. Unit tests cover pure classifiers; slow investigation test asserts row count/coverage/verdict on Gate A only.

**Tech Stack:** Python 3.12+, pytest, ruff; `SelectionMode.GREEDY_REGRET_OVERLAP_PACK`, `rttp_elcp_reprobe_forensics`, `rttp_elcp_c0_dual_mode.build_gate_a_rf1_inputs`.

**Design spec:** [`docs/superpowers/specs/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-design.md`](../specs/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-design.md)

---

## File structure

| File | Responsibility |
|------|----------------|
| `tests/support/rttp_d0_gate_a_frozen_bounds.py` | Gate A investigation constants (`EXPECTED_OVERLAP_STALE_ROW_COUNT = 34`) |
| `harness/investigation/rttp_elcp_d0_stale_attribution.py` | Enums, row DTO, stale classifier, domain diff, verdict, overlap run orchestrator |
| `tests/unit/harness/test_rttp_elcp_d0_stale_attribution.py` | Pure classifier + verdict tests (no DB) |
| `tests/investigation/test_rttp_elcp_rf_d0_stale_attribution.py` | Slow Gate A integration + publish prints |
| `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-report.md` | §1–§6 + JSON appendix |
| `documents/ai/current_plan.md` | ACTIVE D0 row → CLOSED when report done |

**Not modified:** `django_apps/**` production, `rttp_elcp_reprobe_forensics.py` (unless mirror hook requires minimal snapshot export — prefer D0-only wrapper).

---

## Spec → plan coverage

| Spec § | Task |
|--------|------|
| §2.1 overlap primary SoT | Tasks 3–4 |
| §2.2 baseline aggregate §1 | Task 5 (report prose from C0) |
| §2.4 non-causal blocking cells | Task 2 docstring + report §5 |
| §3.3 domain diff | Task 3 |
| §3.4 row schema | Tasks 2–3 |
| §3.5 attribution taxonomy | Task 2 |
| §4 verdict | Task 2 |
| §4.3 CI assertions | Task 4 |
| §7 architecture paths | All tasks |
| No production change | All tasks |

---

### Task 0: Queue + spec linkage

**Files:**
- Modify: `documents/ai/current_plan.md`

- [ ] **Step 1: Add ACTIVE row** after C0 CLOSED line:

```markdown
**ACTIVE (2026-05-27):** **P1-ELCP-RF-D0** — stale_candidate_reachable commit-time drift (overlap-pack 34-row attribution, Gate A). Spec: [`2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-design.md`](../../docs/superpowers/specs/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-design.md) · plan: [`2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable.md`](../../docs/superpowers/plans/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable.md).
```

- [ ] **Step 2: Commit** (only if user requests)

```bash
git add documents/ai/current_plan.md docs/superpowers/specs/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-design.md docs/superpowers/plans/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable.md
git commit -m "docs: add P1-ELCP-RF-D0 stale attribution spec and plan"
```

---

### Task 1: Gate A frozen bounds (investigation test only)

**Files:**
- Create: `tests/support/rttp_d0_gate_a_frozen_bounds.py`

- [ ] **Step 1: Add constants**

```python
"""Gate A frozen bounds for P1-ELCP-RF-D0 (investigation test assertions only).

Update only when rttp-core-recovery-test-map Gate A overlap-pack stale universe changes.
Source: docs/superpowers/reports/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-report.md
"""

from __future__ import annotations

EXPECTED_OVERLAP_STALE_ROW_COUNT = 34
D0_ATTRIBUTION_COVERAGE_MIN = 0.95
D0_UNATTRIBUTED_RATIO_MAX = 0.10
D0_VERDICT_DOMINANCE_THRESHOLD = 0.50

__all__ = [
    "D0_ATTRIBUTION_COVERAGE_MIN",
    "D0_UNATTRIBUTED_RATIO_MAX",
    "D0_VERDICT_DOMINANCE_THRESHOLD",
    "EXPECTED_OVERLAP_STALE_ROW_COUNT",
]
```

- [ ] **Step 2: Run ruff**

Run: `python -m ruff check tests/support/rttp_d0_gate_a_frozen_bounds.py`  
Expected: PASS

---

### Task 2: D0 harness — enums, classifier, verdict (pure)

**Files:**
- Create: `harness/investigation/rttp_elcp_d0_stale_attribution.py` (initial pure functions; Task 3 adds orchestrator)

- [ ] **Step 1: Write failing unit tests**

Create: `tests/unit/harness/test_rttp_elcp_d0_stale_attribution.py`

```python
"""Unit tests for D0 stale attribution (no Django DB)."""

from __future__ import annotations

from harness.investigation.rttp_elcp_d0_stale_attribution import (
    ElcpD0Verdict,
    ElcpStaleAttributionClass,
    classify_stale_attribution,
    compute_d0_verdict,
)
from harness.investigation.rttp_elcp_reprobe_forensics import ElcpProbeFailureClass


def test_classify_post_probe_reservation_block() -> None:
    assert (
        classify_stale_attribution(
            probe_failure_class=ElcpProbeFailureClass.STALE_CANDIDATE_REACHABLE,
            commit_probe_reachable=True,
            commit_conflict_reason="overlap",
            probe_start=(1, 2),
            candidate_route_probe_start=(1, 2),
            goals_nonempty_at_commit=True,
            global_goal_count=5,
            committed_route_cell_count=10,
            traversable_cell_count=100,
            new_blocking_cells_since_last_commit_count=3,
        )
        is ElcpStaleAttributionClass.POST_PROBE_RESERVATION_BLOCK
    )


def test_classify_probe_start_drift() -> None:
    assert (
        classify_stale_attribution(
            probe_failure_class=ElcpProbeFailureClass.STALE_CANDIDATE_REACHABLE,
            commit_probe_reachable=True,
            commit_conflict_reason=None,
            probe_start=(1, 2),
            candidate_route_probe_start=(3, 4),
            goals_nonempty_at_commit=True,
            global_goal_count=5,
            committed_route_cell_count=10,
            traversable_cell_count=100,
            new_blocking_cells_since_last_commit_count=0,
        )
        is ElcpStaleAttributionClass.PROBE_START_DRIFT
    )


def test_compute_verdict_reservation_dominant() -> None:
    classes = [ElcpStaleAttributionClass.POST_PROBE_RESERVATION_BLOCK] * 20 + [
        ElcpStaleAttributionClass.SELECTION_SURVIVABILITY_GAP
    ] * 14
    verdict = compute_d0_verdict(
        attribution_classes=classes,
        new_blocking_cells_counts=[5] * 20 + [0] * 14,
        reservation_conflict_flags=[True] * 20 + [False] * 14,
    )
    assert verdict is ElcpD0Verdict.RESERVATION_DRIFT_DOMINANT


def test_compute_verdict_inconclusive_when_unattributed_high() -> None:
    classes = [ElcpStaleAttributionClass.UNATTRIBUTED_STALE] * 5 + [
        ElcpStaleAttributionClass.SELECTION_SURVIVABILITY_GAP
    ] * 29
    verdict = compute_d0_verdict(
        attribution_classes=classes,
        new_blocking_cells_counts=[0] * 34,
        reservation_conflict_flags=[False] * 34,
    )
    assert verdict is ElcpD0Verdict.INCONCLUSIVE_NEEDS_TELEMETRY
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m pytest tests/unit/harness/test_rttp_elcp_d0_stale_attribution.py -v`  
Expected: FAIL (import / not defined)

- [ ] **Step 3: Implement minimal harness (enums + classify + verdict)**

In `harness/investigation/rttp_elcp_d0_stale_attribution.py` implement:

- `ElcpStaleAttributionClass` StrEnum (spec §3.5 names, lowercase values)
- `ElcpD0Verdict` StrEnum (4 verdicts)
- `RESERVATION_CONFLICT_REASONS: frozenset[str]` per spec §3.5.1
- `classify_stale_attribution(...)` — ordered first-match per spec
- `compute_d0_verdict(attribution_classes, new_blocking_cells_counts, reservation_conflict_flags)` — spec §4.1 thresholds (`0.50`, tie → inconclusive)
- `_DOMAIN_CONGESTION_ROUTE_CELL_RATIO = 0.15` (match RF)

- [ ] **Step 4: Run unit tests — expect PASS**

Run: `python -m pytest tests/unit/harness/test_rttp_elcp_d0_stale_attribution.py -v`  
Expected: PASS

- [ ] **Step 5: Ruff**

Run: `python -m ruff check harness/investigation/rttp_elcp_d0_stale_attribution.py tests/unit/harness/test_rttp_elcp_d0_stale_attribution.py`  
Expected: PASS

---

### Task 3: Domain diff + row builder + mirror integration

**Files:**
- Modify: `harness/investigation/rttp_elcp_d0_stale_attribution.py`
- Modify: `harness/investigation/rttp_elcp_reprobe_forensics.py` (only if needed: export `MirrorStepSnapshot` dataclass from mirror loop — **prefer** copying snapshot logic into D0 wrapper to avoid RF regression)

**Recommended:** Add `build_elcp_primary_mirror_ledger_with_snapshots(...)` in **D0 harness** that duplicates the mirror loop body but records `(committed_route_cells, committed_occupied)` after each success, OR add optional `snapshots: list[MirrorDomainSnapshot] | None = None` parameter to mirror — **minimal diff**: new function `run_mirror_with_domain_snapshots` in `rttp_elcp_d0_stale_attribution.py` calling shared helpers from reprobe forensics.

- [ ] **Step 1: Add `MirrorDomainSnapshot` + diff helpers**

```python
@dataclass(frozen=True, slots=True)
class MirrorDomainSnapshot:
    commit_index: int
    committed_route_cells: frozenset[Coord]
    committed_occupied: frozenset[Coord]


def diff_blocking_cells(
    *,
    before: MirrorDomainSnapshot | None,
    at_attempt_route: frozenset[Coord],
    at_attempt_occupied: frozenset[Coord],
) -> tuple[int, tuple[Coord, ...]]:
    """Return count and up to 10 sample coords (lex sort). See spec §2.4."""
    ...
```

- [ ] **Step 2: Add `ElcpStaleAttributionRow` dataclass + `to_dict()`**

All fields from spec §3.4; `new_blocking_cells_sample` as `list[list[int]]` in JSON.

- [ ] **Step 3: Add `build_stale_attribution_rows(...)`**

Inputs: mirror ledger + snapshots + `candidates_by_id` + `global_goal_count`. Filter `STALE_CANDIDATE_REACHABLE` only. Map each to `ElcpStaleAttributionRow`.

- [ ] **Step 4: Add `run_gate_a_elcp_d0_overlap_stale_forensics(imported_game_data_batch_module)`**

- Reuse `build_gate_a_rf1_inputs`, `resolve_git_sha` from C0 harness
- `selection_mode=GREEDY_REGRET_OVERLAP_PACK`
- Patch primary `incremental_commit`, mirror + snapshots, parity assert
- Return dataclass `ElcpD0ForensicsResult(rows, histogram, verdict, git_sha, c0_carry_forward_dict)`

- [ ] **Step 5: Unit test diff helper**

Add to `tests/unit/harness/test_rttp_elcp_d0_stale_attribution.py`:

```python
def test_diff_blocking_cells_sample_bounded() -> None:
    from harness.investigation.rttp_elcp_d0_stale_attribution import (
        MirrorDomainSnapshot,
        diff_blocking_cells,
    )

    before = MirrorDomainSnapshot(0, frozenset({(0, 0)}), frozenset())
    count, sample = diff_blocking_cells(
        before=before,
        at_attempt_route=frozenset({(0, 0), (1, 0), (2, 0)}),
        at_attempt_occupied=frozenset(),
    )
    assert count == 2
    assert len(sample) <= 10
```

- [ ] **Step 6: Run unit tests**

Run: `python -m pytest tests/unit/harness/test_rttp_elcp_d0_stale_attribution.py -v`  
Expected: PASS

---

### Task 4: Investigation integration test

**Files:**
- Create: `tests/investigation/test_rttp_elcp_rf_d0_stale_attribution.py`

- [ ] **Step 1: Write integration test**

```python
"""P1-ELCP-RF-D0: overlap-pack stale_candidate_reachable attribution (read-only)."""

from __future__ import annotations

import pytest

from harness.investigation.rttp_elcp_d0_stale_attribution import (
    ElcpD0Verdict,
    ElcpStaleAttributionClass,
    run_gate_a_elcp_d0_overlap_stale_forensics,
)
from tests.support.rttp_d0_gate_a_frozen_bounds import (
    D0_ATTRIBUTION_COVERAGE_MIN,
    D0_UNATTRIBUTED_RATIO_MAX,
    EXPECTED_OVERLAP_STALE_ROW_COUNT,
)


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


@pytest.mark.django_db
@pytest.mark.slow
def test_gate_a_elcp_d0_overlap_stale_attribution(
    imported_game_data_batch_module: object,
) -> None:
    result = run_gate_a_elcp_d0_overlap_stale_forensics(
        imported_game_data_batch_module=imported_game_data_batch_module,
    )

    assert result.git_sha != "unknown"
    assert len(result.rows) == EXPECTED_OVERLAP_STALE_ROW_COUNT
    assert all(
        r.probe_failure_class.value == "stale_candidate_reachable" for r in result.rows
    )

    unattributed = sum(
        1
        for r in result.rows
        if r.stale_attribution_class is ElcpStaleAttributionClass.UNATTRIBUTED_STALE
    )
    coverage = 1.0 - (unattributed / len(result.rows))
    assert coverage >= D0_ATTRIBUTION_COVERAGE_MIN
    assert (unattributed / len(result.rows)) <= D0_UNATTRIBUTED_RATIO_MAX

    assert isinstance(result.verdict, ElcpD0Verdict)

    print(f"D0_GIT_SHA={result.git_sha}")
    print(f"D0_VERDICT={result.verdict.value}")
    print(f"D0_HISTOGRAM={result.histogram}")
    print(f"D0_ROWS_JSON={[r.to_dict() for r in result.rows]}")
```

- [ ] **Step 2: Run investigation test (narrow)**

Run: `python -m pytest tests/investigation/test_rttp_elcp_rf_d0_stale_attribution.py::test_gate_a_elcp_d0_overlap_stale_attribution -v`  
Expected: PASS (after Task 3 complete)

- [ ] **Step 3: Ruff on new paths**

Run: `python -m ruff check harness/investigation/rttp_elcp_d0_stale_attribution.py tests/investigation/test_rttp_elcp_rf_d0_stale_attribution.py`  
Expected: PASS

---

### Task 5: Report publication

**Files:**
- Create: `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-report.md`

- [ ] **Step 1: Run investigation test and capture stdout**

Run: `python -m pytest tests/investigation/test_rttp_elcp_rf_d0_stale_attribution.py::test_gate_a_elcp_d0_overlap_stale_attribution -v -s`  
Copy `D0_*` print lines into report draft.

- [ ] **Step 2: Write report §1–§6**

- §1: C0 table from [`2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-report.md`](../reports/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-report.md) §1 (no re-interpretation)
- §2: universe N=34 definition
- §3: histogram from `result.histogram`
- §4: full 34-row markdown table + fenced JSON array
- §5: drift synthesis; include spec §2.4 non-causal note for `new_blocking_cells_*`
- §6: `ElcpD0Verdict` + next-track hint (no B-spec nomination)
- Appendix: baseline aggregate from C0 only

- [ ] **Step 3: Set spec Status line** to `CLOSED (YYYY-MM-DD)` when report signed

- [ ] **Step 4: Update `documents/ai/current_plan.md`** — D0 ACTIVE → CLOSED with report link

---

### Task 6: Acceptance sweep

- [ ] **Step 1: Unit harness tests**

Run: `python -m pytest tests/unit/harness/test_rttp_elcp_d0_stale_attribution.py -v`  
Expected: PASS

- [ ] **Step 2: Confirm no production diff**

Run: `git diff --name-only django_apps/`  
Expected: empty

- [ ] **Step 3: Optional RF regression (unchanged)**

Run: `python -m pytest tests/investigation/test_rttp_elcp_reprobe_forensics.py::test_recovery_map_primary_reprobe_mass_reproduced -v`  
Expected: PASS

---

## Plan self-review (completed)

| Check | Result |
|-------|--------|
| Spec §3.4 row fields | Task 3 `ElcpStaleAttributionRow` |
| Spec §3.5 taxonomy | Task 2 `classify_stale_attribution` |
| Spec §4 verdict | Task 2 `compute_d0_verdict` |
| Spec §4.3 CI | Task 4 investigation test |
| §2.4 non-causal | Task 5 §5 prose + harness docstring |
| No production change | Task 6 step 2 |
| No placeholder TBD in tasks | Verified |

---

## Execution handoff

**Plan saved to** `docs/superpowers/plans/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute in this session with executing-plans checkpoints  

Which approach do you want?
