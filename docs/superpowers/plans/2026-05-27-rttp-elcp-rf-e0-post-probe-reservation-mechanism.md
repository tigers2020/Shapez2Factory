# P1-ELCP-RF-E0 — Post-Probe Reservation Mechanism — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Read-only Gate A forensics on `GREEDY_REGRET_OVERLAP_PACK` — deep mechanism decomposition of D0’s 34 `stale_candidate_reachable` rows (22 `route_cell_conflict` + 12 `inlet_on_shared_transport`), reservation-class failed-row appendix aggregate, `ElcpE0Verdict`, and optional single bounded B-spec nomination when owner is clear. No production changes.

**Architecture:** Reuse D0/C0 Gate A capture + M1 mirror with domain snapshots; new `rttp_elcp_e0_reservation_mechanism.py` replays post-probe commit checks via production helpers (`_private_route_cell_overlap`, spine augment, stub merge) and classifies `ElcpE0MechanismClass`. Verdict uses spec §4.1 precedence; appendix qualifies/vetoes nomination; owner-split can withhold nomination while verdict is dominant.

**Tech Stack:** Python 3.12+, pytest, ruff; `SelectionMode.GREEDY_REGRET_OVERLAP_PACK`, `rttp_elcp_d0_stale_attribution`, `rttp_elcp_reprobe_forensics`, `rttp_elcp_c0_dual_mode`.

**Design spec:** [`docs/superpowers/specs/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-design.md`](../specs/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-design.md)

---

## File structure

| File | Responsibility |
|------|----------------|
| `tests/support/rttp_e0_gate_a_frozen_bounds.py` | Gate A investigation constants (`EXPECTED_OVERLAP_STALE_ROW_COUNT = 34`, coverage thresholds) |
| `harness/investigation/rttp_elcp_e0_reservation_mechanism.py` | E0 enums, mechanism classifier, verdict precedence, appendix veto, nomination evaluation, replay row builder, orchestrator |
| `tests/unit/harness/test_rttp_elcp_e0_reservation_mechanism.py` | Pure classifier, verdict precedence, veto, nomination-withheld tests (no DB) |
| `tests/investigation/test_rttp_elcp_rf_e0_reservation_mechanism.py` | Slow Gate A integration + publish prints |
| `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-report.md` | §1–§6 + appendix + JSON |
| `documents/ai/current_plan.md` | ACTIVE E0 row → CLOSED when report done |

**Reuse (read-only):** `harness/investigation/rttp_elcp_d0_stale_attribution.py` (`RESERVATION_CONFLICT_REASONS`, `MirrorDomainSnapshot`, `diff_blocking_cells`, mirror snapshot loop pattern), `rttp_elcp_c0_dual_mode.py`, `rttp_elcp_reprobe_forensics.py`.

**Not modified:** `django_apps/**` production behavior (importing helpers for replay is allowed).

---

## Spec → plan coverage

| Spec § | Task |
|--------|------|
| §2.1 primary 34 stale deep | Tasks 3–4 |
| §2.2 appendix aggregate | Task 3 |
| §2.6 appendix veto | Task 2 |
| §3.3 Approach III replay | Task 3 |
| §3.4 row schema | Task 3 |
| §3.5 mechanism taxonomy | Task 2 |
| §3.7 unattributed helper | Task 2 |
| §4.1 verdict precedence | Task 2 |
| §4.2–§4.4 nomination | Task 2–3, 5 |
| §4.6 CI assertions | Task 4 |
| §6 report | Task 5 |
| §7 paths | All tasks |
| No production change | Task 6 |

---

### Task 0: Queue + spec linkage

**Files:**
- Modify: `documents/ai/current_plan.md`

- [ ] **Step 1: Add ACTIVE row** after D0 CLOSED line:

```markdown
**ACTIVE (2026-05-27):** **P1-ELCP-RF-E0** — post-probe reservation / shared-transport mechanism forensics (D0 34-row deep + reservation-class appendix, Gate A). Spec: [`2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-design.md`](../../docs/superpowers/specs/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-design.md) · plan: [`2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism.md`](../../docs/superpowers/plans/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism.md).
```

- [ ] **Step 2: Commit** (only if user requests)

```bash
git add documents/ai/current_plan.md docs/superpowers/specs/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-design.md docs/superpowers/plans/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism.md
git commit -m "docs: add P1-ELCP-RF-E0 reservation mechanism spec and plan"
```

---

### Task 1: Gate A frozen bounds (investigation test only)

**Files:**
- Create: `tests/support/rttp_e0_gate_a_frozen_bounds.py`

- [ ] **Step 1: Add constants**

```python
"""Gate A frozen bounds for P1-ELCP-RF-E0 (investigation test assertions only).

Update only when rttp-core-recovery-test-map Gate A overlap-pack stale universe changes.
Source: docs/superpowers/reports/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-report.md
"""

from __future__ import annotations

EXPECTED_OVERLAP_STALE_ROW_COUNT = 34
# D0 report mix (informational; investigation test asserts row count only)
EXPECTED_ROUTE_CELL_CONFLICT_COUNT = 22
EXPECTED_INLET_ON_SHARED_TRANSPORT_COUNT = 12

E0_MECHANISM_COVERAGE_MIN = 0.95
E0_UNATTRIBUTED_RATIO_MAX = 0.10
E0_VERDICT_DOMINANCE_THRESHOLD = 0.50
E0_SPLIT_FAMILY_MIN_RATIO = 0.35
E0_MECHANISM_CLASS_DOMINANCE_FOR_NOMINATION = 0.50

__all__ = [
    "E0_MECHANISM_CLASS_DOMINANCE_FOR_NOMINATION",
    "E0_MECHANISM_COVERAGE_MIN",
    "E0_SPLIT_FAMILY_MIN_RATIO",
    "E0_UNATTRIBUTED_RATIO_MAX",
    "E0_VERDICT_DOMINANCE_THRESHOLD",
    "EXPECTED_INLET_ON_SHARED_TRANSPORT_COUNT",
    "EXPECTED_OVERLAP_STALE_ROW_COUNT",
    "EXPECTED_ROUTE_CELL_CONFLICT_COUNT",
]
```

- [ ] **Step 2: Run ruff**

Run: `python -m ruff check tests/support/rttp_e0_gate_a_frozen_bounds.py`  
Expected: PASS

---

### Task 2: E0 harness — enums, classifier, verdict, nomination (pure)

**Files:**
- Create: `harness/investigation/rttp_elcp_e0_reservation_mechanism.py` (pure functions first; Task 3 adds replay + orchestrator)

- [ ] **Step 1: Write failing unit tests**

Create: `tests/unit/harness/test_rttp_elcp_e0_reservation_mechanism.py`

```python
"""Unit tests for E0 reservation mechanism (no Django DB)."""

from __future__ import annotations

from harness.investigation.rttp_elcp_e0_reservation_mechanism import (
    ElcpE0MechanismClass,
    ElcpE0Verdict,
    AppendixAggregate,
    BSpecNomination,
    BSpecNominationWithheldReason,
    classify_e0_mechanism,
    compute_e0_verdict,
    evaluate_appendix_veto,
    evaluate_b_spec_nomination,
    is_route_cell_mechanism_family,
    is_inlet_mechanism_family,
    is_unattributed_mechanism_class,
)


def test_is_unattributed_prefix() -> None:
    assert is_unattributed_mechanism_class(
        ElcpE0MechanismClass.UNATTRIBUTED_ROUTE_CELL_MECHANISM
    )
    assert not is_unattributed_mechanism_class(
        ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP
    )


def test_classify_private_route_overlap() -> None:
    assert (
        classify_e0_mechanism(
            commit_conflict_reason="route_cell_conflict",
            private_overlap_cells=frozenset({(1, 2)}),
            shareable_trunk_undercoverage_cells=frozenset(),
            spine_augment_cells=frozenset(),
            probe_merged_route_diff_cells=frozenset(),
            output_stub_in_committed_route=False,
            inlet_stub_adjacent_committed_route_cells=frozenset(),
        )
        is ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP
    )


def test_classify_inlet_stub_on_committed_route() -> None:
    assert (
        classify_e0_mechanism(
            commit_conflict_reason="inlet_on_shared_transport",
            private_overlap_cells=frozenset(),
            shareable_trunk_undercoverage_cells=frozenset(),
            spine_augment_cells=frozenset(),
            probe_merged_route_diff_cells=frozenset(),
            output_stub_in_committed_route=True,
            inlet_stub_adjacent_committed_route_cells=frozenset(),
        )
        is ElcpE0MechanismClass.INLET_STUB_ON_COMMITTED_ROUTE
    )


def test_verdict_precedence_mirror_fail_inconclusive() -> None:
    verdict = compute_e0_verdict(
        mechanism_classes=[ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP] * 20
        + [ElcpE0MechanismClass.INLET_STUB_ON_COMMITTED_ROUTE] * 14,
        mirror_parity_ok=False,
        appendix_veto=False,
    )
    assert verdict is ElcpE0Verdict.INCONCLUSIVE_NEEDS_TELEMETRY


def test_verdict_precedence_appendix_veto_split() -> None:
    verdict = compute_e0_verdict(
        mechanism_classes=[ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP] * 20
        + [ElcpE0MechanismClass.INLET_STUB_ON_COMMITTED_ROUTE] * 14,
        mirror_parity_ok=True,
        appendix_veto=True,
    )
    assert verdict is ElcpE0Verdict.SPLIT_RESERVATION_POLICY_NEEDS_DECOMPOSITION


def test_verdict_route_cell_dominant() -> None:
    verdict = compute_e0_verdict(
        mechanism_classes=[ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP] * 18
        + [ElcpE0MechanismClass.INLET_STUB_ON_COMMITTED_ROUTE] * 16,
        mirror_parity_ok=True,
        appendix_veto=False,
    )
    assert verdict is ElcpE0Verdict.ROUTE_CELL_RESERVATION_CONFLICT_DOMINANT


def test_appendix_veto_opposite_family_dominant() -> None:
    veto = evaluate_appendix_veto(
        primary_dominant_family="route_cell",
        appendix_route_cell_family_count=10,
        appendix_inlet_family_count=20,
        appendix_total=30,
    )
    assert veto is True


def test_nomination_withheld_owner_split() -> None:
    nomination = evaluate_b_spec_nomination(
        verdict=ElcpE0Verdict.ROUTE_CELL_RESERVATION_CONFLICT_DOMINANT,
        mechanism_classes=[
            ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP,
            ElcpE0MechanismClass.SHAREABLE_TRUNK_UNDERCOVERAGE,
            ElcpE0MechanismClass.SPINE_AUGMENTATION_CONFLICT,
            ElcpE0MechanismClass.PROBE_VS_MERGED_ROUTE_MISMATCH,
        ]
        * 9,
        appendix_veto=False,
    )
    assert nomination.nominated is False
    assert nomination.withheld_reason is BSpecNominationWithheldReason.OWNER_SPLIT
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m pytest tests/unit/harness/test_rttp_elcp_e0_reservation_mechanism.py -v`  
Expected: FAIL (import / not defined)

- [ ] **Step 3: Implement minimal harness (enums + pure logic)**

In `harness/investigation/rttp_elcp_e0_reservation_mechanism.py` implement:

- `ElcpE0MechanismClass` StrEnum (spec §3.5 names)
- `ElcpE0Verdict` StrEnum (4 verdicts)
- `is_unattributed_mechanism_class`, `is_route_cell_mechanism_family`, `is_inlet_mechanism_family`
- `classify_e0_mechanism(...)` — ordered first-match per `commit_conflict_reason` branch (spec §3.5)
- `compute_e0_verdict(mechanism_classes, *, mirror_parity_ok, appendix_veto)` — **spec §4.1 precedence steps 1–5**
- `evaluate_appendix_veto(...)` — §2.6 (>50% opposite family AND lead ≥1 row)
- `BSpecNomination` frozen dataclass + `evaluate_b_spec_nomination(...)` — §4.2–§4.3 (owner split → withheld)
- Re-export or import `RESERVATION_CONFLICT_REASONS` from `rttp_elcp_d0_stale_attribution`

- [ ] **Step 4: Run unit tests — expect PASS**

Run: `python -m pytest tests/unit/harness/test_rttp_elcp_e0_reservation_mechanism.py -v`  
Expected: PASS

- [ ] **Step 5: Ruff**

Run: `python -m ruff check harness/investigation/rttp_elcp_e0_reservation_mechanism.py tests/unit/harness/test_rttp_elcp_e0_reservation_mechanism.py`  
Expected: PASS

---

### Task 3: Mirror replay, row builder, appendix aggregate, orchestrator

**Files:**
- Modify: `harness/investigation/rttp_elcp_e0_reservation_mechanism.py`

- [ ] **Step 1: Add `ElcpE0MechanismRow` dataclass + `to_dict()`**

All fields from spec §3.4; bounded samples ≤10 coords lex-sorted.

- [ ] **Step 2: Add `replay_post_probe_mechanism_signals(...)`**

Inputs: `BundleCandidate`, `MirrorDomainSnapshot` at attempt, ledger row (`probe`, `precomputed_route_cells`, `lane_shareable` if captured in mirror — extend mirror ledger export in D0 harness **only if** field missing; prefer reading from existing `ElcpAttemptLedgerRow` fields).

Call production helpers (import only):

- `_private_route_cell_overlap`
- `_augment_route_cells_with_output_spine`
- `_route_cells_with_required_output_stub`
- `_route_cells_from_path` (or equivalent path extraction)

Return signal bundle for `classify_e0_mechanism`.

**Mirror parity:** replay uses same `committed_route_cells`, `committed_occupied`, `shareable_trunk_cells` as mirror at `commit_index`.

- [ ] **Step 3: Add `build_e0_mechanism_rows(...)`**

Filter ledger `STALE_CANDIDATE_REACHABLE` only; map to `ElcpE0MechanismRow`; attach `mechanism_owner_module` from spec §3.5 table.

- [ ] **Step 4: Add `build_reservation_class_appendix_aggregate(ledger)`**

Count all failed rows with `commit_conflict_reason in RESERVATION_CONFLICT_REASONS`; stale vs non-stale; conflict histogram; route-cell vs inlet family counts for veto inputs.

- [ ] **Step 5: Add `ElcpE0ForensicsResult` + `run_gate_a_elcp_e0_reservation_forensics(...)`**

Pattern copy from `run_gate_a_elcp_d0_overlap_stale_forensics`:

- `build_gate_a_rf1_inputs`, `GREEDY_REGRET_OVERLAP_PACK`, patch capture, mirror + snapshots, `assert_mirror_parity`
- Build primary rows + appendix aggregate
- `appendix_veto = evaluate_appendix_veto(...)`
- `verdict = compute_e0_verdict(...)`
- `nomination = evaluate_b_spec_nomination(...)`
- Include `d0_carry_forward` dict for report §1

- [ ] **Step 6: Unit test replay helper with synthetic coords**

Add to `tests/unit/harness/test_rttp_elcp_e0_reservation_mechanism.py` a small synthetic test for `replay_post_probe_mechanism_signals` using minimal candidate + snapshot (no DB).

- [ ] **Step 7: Run unit tests**

Run: `python -m pytest tests/unit/harness/test_rttp_elcp_e0_reservation_mechanism.py -v`  
Expected: PASS

---

### Task 4: Investigation integration test

**Files:**
- Create: `tests/investigation/test_rttp_elcp_rf_e0_reservation_mechanism.py`

- [ ] **Step 1: Write integration test**

```python
"""P1-ELCP-RF-E0: overlap-pack post-probe reservation mechanism (read-only)."""

from __future__ import annotations

import pytest

from harness.investigation.rttp_elcp_e0_reservation_mechanism import (
    ElcpE0Verdict,
    is_unattributed_mechanism_class,
    run_gate_a_elcp_e0_reservation_forensics,
)
from tests.support.rttp_e0_gate_a_frozen_bounds import (
    E0_MECHANISM_COVERAGE_MIN,
    E0_UNATTRIBUTED_RATIO_MAX,
    EXPECTED_OVERLAP_STALE_ROW_COUNT,
)


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


@pytest.mark.django_db
@pytest.mark.slow
def test_gate_a_elcp_e0_overlap_reservation_mechanism(
    imported_game_data_batch_module: object,
) -> None:
    result = run_gate_a_elcp_e0_reservation_forensics(
        imported_game_data_batch_module=imported_game_data_batch_module,
    )

    assert result.git_sha != "unknown"
    assert len(result.rows) == EXPECTED_OVERLAP_STALE_ROW_COUNT
    assert result.mirror_parity_ok is True

    unattributed = sum(
        1 for r in result.rows if is_unattributed_mechanism_class(r.elcp_e0_mechanism_class)
    )
    coverage = 1.0 - (unattributed / len(result.rows))
    assert coverage >= E0_MECHANISM_COVERAGE_MIN
    assert (unattributed / len(result.rows)) <= E0_UNATTRIBUTED_RATIO_MAX

    assert isinstance(result.verdict, ElcpE0Verdict)

    print(f"E0_GIT_SHA={result.git_sha}")
    print(f"E0_VERDICT={result.verdict.value}")
    print(f"E0_NOMINATION={result.nomination.to_dict()}")
    print(f"E0_MECHANISM_HISTOGRAM={result.mechanism_histogram}")
    print(f"E0_APPENDIX={result.appendix_aggregate.to_dict()}")
    print(f"E0_ROWS_JSON={[r.to_dict() for r in result.rows]}")
```

- [ ] **Step 2: Run investigation test (narrow)**

Run: `python -m pytest tests/investigation/test_rttp_elcp_rf_e0_reservation_mechanism.py::test_gate_a_elcp_e0_overlap_reservation_mechanism -v`  
Expected: PASS (after Task 3 complete)

- [ ] **Step 3: Ruff on new paths**

Run: `python -m ruff check harness/investigation/rttp_elcp_e0_reservation_mechanism.py tests/investigation/test_rttp_elcp_rf_e0_reservation_mechanism.py`  
Expected: PASS

---

### Task 5: Report publication

**Files:**
- Create: `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-report.md`

- [ ] **Step 1: Run investigation test and capture stdout**

Run: `python -m pytest tests/investigation/test_rttp_elcp_rf_e0_reservation_mechanism.py::test_gate_a_elcp_e0_overlap_reservation_mechanism -v -s`  
Copy `E0_*` print lines into report draft.

- [ ] **Step 2: Write report §1–§6 + appendices**

- §1: D0 carry-forward (`RESERVATION_DRIFT_DOMINANT`, 22/12) — no re-litigation
- §2: primary universe N=34
- §3: `ElcpE0MechanismClass` histogram + owner rollup
- §4: 34-row table + fenced JSON (or reference test print)
- §5: mechanism synthesis; spec §2.4 non-causal note
- §6: `ElcpE0Verdict` + nomination block **or** withheld reason enum
- Appendix A: reservation-class aggregate + veto qualification narrative
- Appendix B: stale vs non-stale ratio if useful

- [ ] **Step 3: Set spec Status** to `CLOSED (YYYY-MM-DD)` when report signed

- [ ] **Step 4: Update `documents/ai/current_plan.md`** — E0 ACTIVE → CLOSED with report link

---

### Task 6: Acceptance sweep

- [ ] **Step 1: Unit harness tests**

Run: `python -m pytest tests/unit/harness/test_rttp_elcp_e0_reservation_mechanism.py -v`  
Expected: PASS

- [ ] **Step 2: Confirm no production diff**

Run: `git diff --name-only django_apps/`  
Expected: empty (helper imports do not modify files)

- [ ] **Step 3: D0 regression (unchanged)**

Run: `python -m pytest tests/investigation/test_rttp_elcp_rf_d0_stale_attribution.py::test_gate_a_elcp_d0_overlap_stale_attribution -v`  
Expected: PASS

---

## Plan self-review (completed)

| Check | Result |
|-------|--------|
| Spec §4.1 verdict precedence | Task 2 `compute_e0_verdict` + unit tests |
| Spec §3.7 unattributed | Task 2 `is_unattributed_mechanism_class` |
| Spec §2.6 appendix veto | Task 2–3 |
| Spec §4.3 verdict≠nomination | Task 2 `evaluate_b_spec_nomination` |
| Spec §3.3 Approach III | Task 3 replay |
| Spec §4.6 CI | Task 4 |
| No production change | Task 6 step 2 |
| No placeholder TBD | Verified |

---

## Execution handoff

**Plan saved to** `docs/superpowers/plans/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute in this session with executing-plans checkpoints  

Which approach do you want?
