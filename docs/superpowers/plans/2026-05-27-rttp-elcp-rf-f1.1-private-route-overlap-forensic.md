# P1-ELCP-RF-F1.1 — Private Route Overlap Row-Level Forensic — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Read-only Gate A forensic: classify all **20** post-F1 `private_route_overlap` stale rows into secondary root causes, emit row-level JSON + histogram + F1.2 nomination (or withheld reason). **Does not** change production code or make G1 pass.

**Architecture:** New `rttp_elcp_f11_private_overlap_forensic.py` runs parent `run_gate_a_elcp_e0_reservation_forensics`, filters slice rows, extended commit-order replay captures **M/R/O** partition evidence, `classify_f11_root_cause` (first-match), `evaluate_f12_nomination`. Unit tests first (no DB), then slow investigation test + report.

**Tech Stack:** Python 3.12+, pytest, ruff; reuse `rttp_elcp_e0_reservation_mechanism`, `rttp_elcp_c0_dual_mode`, production commit helpers (import only).

**Design spec:** [`docs/superpowers/specs/2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic-design.md`](../specs/2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic-design.md)

**Review (2026-05-27):** Spec approved. Plan approved with amendments. Implementation mode: **Subagent-Driven**. No commits unless explicitly requested.

### Review amendments (locked before implementation)

| Amendment | Resolution |
|-----------|------------|
| Remove `second_n` from nomination tie-break | `evaluate_f12_nomination` uses `_FIXABLE_CAUSES_ORDERED.index` only (no `second_n`) |
| `_FIXABLE_CAUSES` as deterministic `tuple`, not `frozenset` | `_FIXABLE_CAUSES_ORDERED: tuple[ElcpF11PrivateOverlapRootCause, ...]` |
| Unit test matrix (classify + nomination) | `tests/unit/harness/test_rttp_elcp_f11_private_overlap_forensic.py` — 13 tests: spine/stub, unclear, F1.2a/b/c dominant nomination, `UNCLEAR_TOO_HIGH`, `SPLIT_FIXABLE_CLASSES`, `PARENT_MIRROR_FAIL` |

### Execution phases (Subagent-Driven)

| Phase | Scope | Status |
|-------|--------|--------|
| 1 Pure Contract | constants, enum, classify, nomination, unit tests | **DONE** |
| 2 Replay Forensic | E0 walk parity, evidence cache, row builder, orchestrator | **DONE** |
| 3 Gate/Report | slow investigation test, `F11_ROWS_JSON`, report | **DONE** |
| 4 Review Lead | spec compliance, no `django_apps/**`, G1 still RED | **this session** |

---

## File structure

| File | Responsibility |
|------|----------------|
| `tests/support/rttp_f11_gate_a_frozen_bounds.py` | `F11_EXPECTED_PRIVATE_OVERLAP_ROW_COUNT = 20`, `F11_UNCLEAR_MAX_ROWS = 2`, dominance threshold |
| `harness/investigation/rttp_elcp_f11_private_overlap_forensic.py` | F1.1 enums, evidence, classify, nomination, extended replay, orchestrator |
| `tests/unit/harness/test_rttp_elcp_f11_private_overlap_forensic.py` | Pure classify + nomination tests |
| `tests/investigation/test_rttp_elcp_rf_f11_private_overlap_forensic.py` | Slow Gate A + `F11_ROWS_JSON` print |
| `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic-report.md` | Histogram, nomination, synthesis |
| `documents/ai/current_plan.md` | F1 PARTIAL + F1.1 ACTIVE |

**Not modified:** `django_apps/**`, `test_rttp_elcp_rf_f1_reservation_policy_gate_a.py` (G1 stays RED), E0 classifier behavior.

---

## Spec → plan coverage

| Spec § | Task |
|--------|------|
| §4 symbols / partition | Task 2–3 |
| §5 taxonomy + rule 4 conservative | Task 2 |
| §6 F1.2 nomination + split prose | Task 2, 5 |
| §7 row schema | Task 3 |
| §8 success / CI | Task 4 |
| §9 report | Task 5 |
| §10 non-goals | Task 6 |

---

### Task 0: Queue + spec linkage

**Files:**
- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/specs/2026-05-27-rttp-elcp-rf-f0-private-route-overlap-reservation-policy-design.md` (F1.1 link in header)
- Modify: `docs/superpowers/plans/2026-05-27-rttp-elcp-rf-f1-private-route-overlap-reservation-policy.md` (F1.1 follow-on note in §4 Next)

- [ ] **Step 1: Update `current_plan.md`** — add after F1 ACTIVE line:

```markdown
**ACTIVE (2026-05-27):** **P1-ELCP-RF-F1.1** — private_route_overlap 20-row read-only forensic (secondary root cause + F1.2 nomination). Spec: [`2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic-design.md`](../../docs/superpowers/specs/2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic-design.md) · plan: [`2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic.md`](../../docs/superpowers/plans/2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic.md). Parent F1: **PARTIAL** (G1 not met).
```

- [ ] **Step 2: F0 spec header** — add line:

```markdown
**F1.1 forensic (read-only):** [`2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic-design.md`](2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic-design.md)
```

- [ ] **Step 3: Commit** (only when user explicitly requests)

---

### Task 1: Gate A frozen bounds (F1.1)

**Files:**
- Create: `tests/support/rttp_f11_gate_a_frozen_bounds.py`

- [ ] **Step 1: Add file**

```python
"""Gate A frozen bounds for P1-ELCP-RF-F1.1 (investigation test assertions only).

Update only when post-F1 Gate A private_route_overlap slice count changes.
"""

from __future__ import annotations

F11_EXPECTED_PRIVATE_OVERLAP_ROW_COUNT = 20
F11_UNCLEAR_MAX_ROWS = 2
F11_ROOT_CAUSE_DOMINANCE_MIN_COUNT = 10  # 50% of 20

__all__ = [
    "F11_EXPECTED_PRIVATE_OVERLAP_ROW_COUNT",
    "F11_ROOT_CAUSE_DOMINANCE_MIN_COUNT",
    "F11_UNCLEAR_MAX_ROWS",
]
```

- [ ] **Step 2: Run** (import sanity)

Run: `python -c "from tests.support.rttp_f11_gate_a_frozen_bounds import F11_EXPECTED_PRIVATE_OVERLAP_ROW_COUNT; assert F11_EXPECTED_PRIVATE_OVERLAP_ROW_COUNT == 20"`

Expected: no output (success)

---

### Task 2: Pure classify + nomination (TDD, no DB)

**Files:**
- Create: `harness/investigation/rttp_elcp_f11_private_overlap_forensic.py` (enums + pure functions first)
- Create: `tests/unit/harness/test_rttp_elcp_f11_private_overlap_forensic.py`

- [ ] **Step 1: Write failing unit tests**

Create `tests/unit/harness/test_rttp_elcp_f11_private_overlap_forensic.py`:

```python
"""Unit tests for F1.1 private overlap forensic (no Django DB)."""

from __future__ import annotations

from harness.investigation.rttp_elcp_f11_private_overlap_forensic import (
    ElcpF11PrivateOverlapRootCause,
    F12NominationWithheldReason,
    classify_f11_root_cause,
    evaluate_f12_nomination,
)


def test_classify_trunk_evidence_missing_when_undercoverage_in_overlap() -> None:
    assert (
        classify_f11_root_cause(
            overlap_undercoverage_cells=frozenset({(1, 0)}),
            overlap_full_not_reserved=frozenset({(2, 0)}),
            overlap_spine_stub=frozenset(),
            overlap_branch_only=frozenset(),
            overlap_trunk_mask=frozenset({(1, 0)}),
        )
        is ElcpF11PrivateOverlapRootCause.TRUNK_EVIDENCE_MISSING
    )


def test_classify_committed_growth_artifact_from_full_route_not_reserved() -> None:
    assert (
        classify_f11_root_cause(
            overlap_undercoverage_cells=frozenset(),
            overlap_full_not_reserved=frozenset({(3, 0)}),
            overlap_spine_stub=frozenset(),
            overlap_branch_only=frozenset(),
            overlap_trunk_mask=frozenset(),
        )
        is ElcpF11PrivateOverlapRootCause.COMMITTED_GROWTH_ARTIFACT
    )


def test_classify_true_peer_conservative_empty_trunk_only_when_no_other_buckets() -> None:
    assert (
        classify_f11_root_cause(
            overlap_undercoverage_cells=frozenset(),
            overlap_full_not_reserved=frozenset(),
            overlap_spine_stub=frozenset(),
            overlap_branch_only=frozenset(),
            overlap_trunk_mask=frozenset(),
        )
        is ElcpF11PrivateOverlapRootCause.TRUE_PEER_BRANCH_OVERLAP
    )


def test_classify_true_peer_not_from_empty_trunk_when_full_route_bucket_nonempty() -> None:
    assert (
        classify_f11_root_cause(
            overlap_undercoverage_cells=frozenset(),
            overlap_full_not_reserved=frozenset({(1, 0)}),
            overlap_spine_stub=frozenset(),
            overlap_branch_only=frozenset(),
            overlap_trunk_mask=frozenset(),
        )
        is ElcpF11PrivateOverlapRootCause.COMMITTED_GROWTH_ARTIFACT
    )


def test_f12_nomination_withheld_when_true_peer_dominant() -> None:
    nomination = evaluate_f12_nomination(
        root_cause_counts={
            ElcpF11PrivateOverlapRootCause.TRUE_PEER_BRANCH_OVERLAP.value: 12,
            ElcpF11PrivateOverlapRootCause.TRUNK_EVIDENCE_MISSING.value: 8,
        },
        unclear_count=0,
        mirror_parity_ok=True,
        row_count=20,
    )
    assert nomination.withheld_reason is F12NominationWithheldReason.TRUE_PEER_DOMINANT
    assert nomination.nominated_track is None


def test_classify_spine_or_stub_residual_overlap() -> None:
    assert (
        classify_f11_root_cause(
            overlap_undercoverage_cells=frozenset(),
            overlap_full_not_reserved=frozenset(),
            overlap_spine_stub=frozenset({(4, 0)}),
            overlap_branch_only=frozenset(),
            overlap_trunk_mask=frozenset({(4, 0)}),
        )
        is ElcpF11PrivateOverlapRootCause.SPINE_OR_STUB_RESIDUAL_OVERLAP
    )


def test_classify_unclear_when_only_trunk_mask_present_without_undercoverage() -> None:
    assert (
        classify_f11_root_cause(
            overlap_undercoverage_cells=frozenset(),
            overlap_full_not_reserved=frozenset(),
            overlap_spine_stub=frozenset(),
            overlap_branch_only=frozenset(),
            overlap_trunk_mask=frozenset({(1, 0)}),
        )
        is ElcpF11PrivateOverlapRootCause.UNCLEAR_NEEDS_TRACE
    )


def test_f12_nomination_dominant_fixable_trunk() -> None:
    nomination = evaluate_f12_nomination(
        root_cause_counts={
            ElcpF11PrivateOverlapRootCause.TRUNK_EVIDENCE_MISSING.value: 12,
            ElcpF11PrivateOverlapRootCause.COMMITTED_GROWTH_ARTIFACT.value: 8,
        },
        unclear_count=0,
        mirror_parity_ok=True,
        row_count=20,
    )
    assert nomination.nominated is True
    assert nomination.nominated_track == "F1.2a"
    assert nomination.withheld_reason is F12NominationWithheldReason.NONE


def test_f12_nomination_unclear_too_high() -> None:
    nomination = evaluate_f12_nomination(
        root_cause_counts={},
        unclear_count=3,
        mirror_parity_ok=True,
        row_count=20,
    )
    assert nomination.withheld_reason is F12NominationWithheldReason.UNCLEAR_TOO_HIGH


def test_f12_nomination_split_fixable_classes() -> None:
    nomination = evaluate_f12_nomination(
        root_cause_counts={
            ElcpF11PrivateOverlapRootCause.TRUNK_EVIDENCE_MISSING.value: 8,
            ElcpF11PrivateOverlapRootCause.COMMITTED_GROWTH_ARTIFACT.value: 8,
            ElcpF11PrivateOverlapRootCause.TRUE_PEER_BRANCH_OVERLAP.value: 4,
        },
        unclear_count=0,
        mirror_parity_ok=True,
        row_count=20,
    )
    assert nomination.withheld_reason is F12NominationWithheldReason.SPLIT_FIXABLE_CLASSES


def test_f12_nomination_parent_mirror_fail() -> None:
    nomination = evaluate_f12_nomination(
        root_cause_counts={},
        unclear_count=0,
        mirror_parity_ok=False,
        row_count=20,
    )
    assert nomination.withheld_reason is F12NominationWithheldReason.PARENT_MIRROR_FAIL
```

**Nomination `row_count` guard (option B):** `len(f11_rows) == 20` is asserted by the investigation test; `evaluate_f12_nomination` does not add a separate `expected_row_count` enum — mismatch is a harness error, not a withheld reason.

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m pytest tests/unit/harness/test_rttp_elcp_f11_private_overlap_forensic.py -v`

Expected: FAIL — `ModuleNotFoundError` or missing `classify_f11_root_cause`

- [ ] **Step 3: Implement enums + pure functions** in `harness/investigation/rttp_elcp_f11_private_overlap_forensic.py`:

```python
"""P1-ELCP-RF-F1.1: private_route_overlap row-level forensic (not solver input)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class ElcpF11PrivateOverlapRootCause(StrEnum):
    TRUNK_EVIDENCE_MISSING = "trunk_evidence_missing"
    COMMITTED_GROWTH_ARTIFACT = "committed_growth_artifact"
    SPINE_OR_STUB_RESIDUAL_OVERLAP = "spine_or_stub_residual_overlap"
    TRUE_PEER_BRANCH_OVERLAP = "true_peer_branch_overlap"
    UNCLEAR_NEEDS_TRACE = "unclear_needs_trace"


class F12NominationWithheldReason(StrEnum):
    NONE = "none"
    UNCLEAR_TOO_HIGH = "unclear_too_high"
    NO_DOMINANT_ROOT_CAUSE = "no_dominant_root_cause"
    TRUE_PEER_DOMINANT = "true_peer_dominant"
    SPLIT_FIXABLE_CLASSES = "split_fixable_classes"
    PARENT_MIRROR_FAIL = "parent_mirror_fail"


_FIXABLE_CAUSES_ORDERED: tuple[ElcpF11PrivateOverlapRootCause, ...] = (
    ElcpF11PrivateOverlapRootCause.TRUNK_EVIDENCE_MISSING,
    ElcpF11PrivateOverlapRootCause.COMMITTED_GROWTH_ARTIFACT,
    ElcpF11PrivateOverlapRootCause.SPINE_OR_STUB_RESIDUAL_OVERLAP,
)

_F12_TRACK_BY_CAUSE: dict[ElcpF11PrivateOverlapRootCause, str] = {
    ElcpF11PrivateOverlapRootCause.TRUNK_EVIDENCE_MISSING: "F1.2a",
    ElcpF11PrivateOverlapRootCause.COMMITTED_GROWTH_ARTIFACT: "F1.2b",
    ElcpF11PrivateOverlapRootCause.SPINE_OR_STUB_RESIDUAL_OVERLAP: "F1.2c",
}


def classify_f11_root_cause(
    *,
    overlap_undercoverage_cells: frozenset[tuple[int, int]],
    overlap_full_not_reserved: frozenset[tuple[int, int]],
    overlap_spine_stub: frozenset[tuple[int, int]],
    overlap_branch_only: frozenset[tuple[int, int]],
    overlap_trunk_mask: frozenset[tuple[int, int]],
) -> ElcpF11PrivateOverlapRootCause:
    if overlap_undercoverage_cells:
        return ElcpF11PrivateOverlapRootCause.TRUNK_EVIDENCE_MISSING
    if overlap_full_not_reserved:
        return ElcpF11PrivateOverlapRootCause.COMMITTED_GROWTH_ARTIFACT
    if overlap_spine_stub:
        return ElcpF11PrivateOverlapRootCause.SPINE_OR_STUB_RESIDUAL_OVERLAP
    if overlap_branch_only:
        return ElcpF11PrivateOverlapRootCause.TRUE_PEER_BRANCH_OVERLAP
    if not overlap_trunk_mask:
        return ElcpF11PrivateOverlapRootCause.TRUE_PEER_BRANCH_OVERLAP
    return ElcpF11PrivateOverlapRootCause.UNCLEAR_NEEDS_TRACE


@dataclass(frozen=True, slots=True)
class F12PolicyNomination:
    nominated: bool
    nominated_track: str | None
    title: str | None
    withheld_reason: F12NominationWithheldReason

    def to_dict(self) -> dict[str, Any]:
        return {
            "nominated": self.nominated,
            "nominated_track": self.nominated_track,
            "title": self.title,
            "withheld_reason": self.withheld_reason.value,
        }


def evaluate_f12_nomination(
    *,
    root_cause_counts: dict[str, int],
    unclear_count: int,
    mirror_parity_ok: bool,
    row_count: int,
    dominance_min: int = 10,
    unclear_max: int = 2,
    split_fixable_min: int = 7,
) -> F12PolicyNomination:
    if not mirror_parity_ok:
        return F12PolicyNomination(
            nominated=False,
            nominated_track=None,
            title=None,
            withheld_reason=F12NominationWithheldReason.PARENT_MIRROR_FAIL,
        )
    if row_count == 0:
        return F12PolicyNomination(
            nominated=False,
            nominated_track=None,
            title=None,
            withheld_reason=F12NominationWithheldReason.NO_DOMINANT_ROOT_CAUSE,
        )
    if unclear_count > unclear_max:
        return F12PolicyNomination(
            nominated=False,
            nominated_track=None,
            title=None,
            withheld_reason=F12NominationWithheldReason.UNCLEAR_TOO_HIGH,
        )

    true_peer_n = root_cause_counts.get(
        ElcpF11PrivateOverlapRootCause.TRUE_PEER_BRANCH_OVERLAP.value, 0
    )
    if true_peer_n >= dominance_min:
        return F12PolicyNomination(
            nominated=False,
            nominated_track=None,
            title="Retain private overlap reject policy (true peer dominant)",
            withheld_reason=F12NominationWithheldReason.TRUE_PEER_DOMINANT,
        )

    fixable_counts = [
        (cause, root_cause_counts.get(cause.value, 0))
        for cause in _FIXABLE_CAUSES_ORDERED
    ]
    fixable_counts.sort(
        key=lambda item: (-item[1], _FIXABLE_CAUSES_ORDERED.index(item[0])),
    )
    top_cause, top_n = fixable_counts[0]

    if top_n >= dominance_min:
        track = _F12_TRACK_BY_CAUSE[top_cause]
        return F12PolicyNomination(
            nominated=True,
            nominated_track=track,
            title=f"Bounded {track}: {top_cause.value}",
            withheld_reason=F12NominationWithheldReason.NONE,
        )

    fixable_at_split = [c for c, n in fixable_counts if n >= split_fixable_min]
    if len(fixable_at_split) >= 2:
        return F12PolicyNomination(
            nominated=False,
            nominated_track=None,
            title="Split fixable classes — one F1.2 policy change per PR",
            withheld_reason=F12NominationWithheldReason.SPLIT_FIXABLE_CLASSES,
        )

    return F12PolicyNomination(
        nominated=False,
        nominated_track=None,
        title=None,
        withheld_reason=F12NominationWithheldReason.NO_DOMINANT_ROOT_CAUSE,
    )
```

- [ ] **Step 4: Run unit tests**

Run: `python -m pytest tests/unit/harness/test_rttp_elcp_f11_private_overlap_forensic.py -v`

Expected: PASS

- [ ] **Step 5: Ruff**

Run: `python -m ruff check harness/investigation/rttp_elcp_f11_private_overlap_forensic.py tests/unit/harness/test_rttp_elcp_f11_private_overlap_forensic.py tests/support/rttp_f11_gate_a_frozen_bounds.py`

Expected: PASS

---

### Task 3: Extended replay + row builder + orchestrator

**Files:**
- Modify: `harness/investigation/rttp_elcp_f11_private_overlap_forensic.py` (add evidence dataclass, partition builder, walk, rows, orchestrator)

- [ ] **Step 1: Add `F11OverlapReplayEvidence` + `compute_overlap_partitions`**

Implement helper that, given `O, S, R, M, trunk_mask, branch, spine_aug, probe_diff, stub_adj, undercoverage`:

- Builds `O_full_not_reserved = O & (M - R)`
- Builds `O_spine_stub`, `O_branch_only`, `overlap_partition` dict per spec §4.2
- Returns struct used by row builder

- [ ] **Step 2: Add `build_f11_overlap_evidence_cache`**

Copy commit-order walk pattern from `rttp_elcp_e0_reservation_mechanism.build_stale_replay_signal_cache` into F1.1 module (same imports: `incremental_commit`, `reservation_overlap_policy`, `exterior_lane_trunk`, etc.). On each `STALE_CANDIDATE_REACHABLE` failure:

- Recompute `R` via `compute_elcp_reservation_candidate_cells`
- Recompute `M` via same augment/stub chain as E0 `_mechanism_signals_from_route_bundle` (already builds augmented route)
- Capture `outcome.committed_route_delta` as debug field
- Store `F11OverlapReplayEvidence` keyed by `(commit_index, candidate_id)`

**Do not** change E0 module behavior.

- [ ] **Step 3: Add `ElcpF11OverlapForensicRow` + `build_f11_forensic_rows`**

Filter parent E0 rows where `elcp_e0_mechanism_class == PRIVATE_ROUTE_OVERLAP` and `private_overlap_cell_count > 0`. Join with evidence cache; call `classify_f11_root_cause` on overlap subsets (e.g. `overlap_full_not_reserved = O & (M-R)` passed as frozensets).

Set `f11_root_cause_owner` from spec §5.4 table (string constants).

- [ ] **Step 4: Add `ElcpF11ForensicsResult` + `run_gate_a_elcp_f11_private_overlap_forensics`**

```python
@dataclass(frozen=True, slots=True)
class ElcpF11ForensicsResult:
    git_sha: str
    parent_stale_row_count: int
    private_overlap_row_count: int
    rows: tuple[ElcpF11OverlapForensicRow, ...]
    root_cause_histogram: dict[str, int]
    unclear_count: int
    mirror_parity_ok: bool
    f12_nomination: F12PolicyNomination
```

Orchestrator:

1. `parent = run_gate_a_elcp_e0_reservation_forensics(...)`
2. If not `parent.mirror_parity_ok`: return inconclusive result (empty rows, withheld `PARENT_MIRROR_FAIL`)
3. Assert `len(parent.rows) == EXPECTED_OVERLAP_STALE_ROW_COUNT` (33) — import from `rttp_e0_gate_a_frozen_bounds`
4. Build evidence cache via Gate A inputs (reuse `build_gate_a_rf1_inputs` + genome walk — same as E0 orchestrator tail)
5. Build F1.1 rows + histogram + `evaluate_f12_nomination`

Reference `run_gate_a_elcp_e0_reservation_forensics` in `rttp_elcp_e0_reservation_mechanism.py` for input wiring.

- [ ] **Step 5: Run unit tests again**

Run: `python -m pytest tests/unit/harness/test_rttp_elcp_f11_private_overlap_forensic.py -v`

Expected: PASS

---

### Task 4: Investigation integration test

**Files:**
- Create: `tests/investigation/test_rttp_elcp_rf_f11_private_overlap_forensic.py`

- [ ] **Step 1: Write test**

```python
"""P1-ELCP-RF-F1.1: Gate A private_route_overlap slice forensic (read-only)."""

from __future__ import annotations

import pytest

from harness.investigation.rttp_elcp_f11_private_overlap_forensic import (
    ElcpF11PrivateOverlapRootCause,
    run_gate_a_elcp_f11_private_overlap_forensics,
)
from tests.support.rttp_e0_gate_a_frozen_bounds import EXPECTED_OVERLAP_STALE_ROW_COUNT
from tests.support.rttp_f11_gate_a_frozen_bounds import (
    F11_EXPECTED_PRIVATE_OVERLAP_ROW_COUNT,
    F11_UNCLEAR_MAX_ROWS,
)


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


@pytest.mark.django_db
@pytest.mark.slow
def test_gate_a_f11_private_overlap_forensic(
    imported_game_data_batch_module: object,
) -> None:
    result = run_gate_a_elcp_f11_private_overlap_forensics(
        imported_game_data_batch_module=imported_game_data_batch_module,
    )
    assert result.git_sha != "unknown"
    assert result.mirror_parity_ok is True
    assert result.parent_stale_row_count == EXPECTED_OVERLAP_STALE_ROW_COUNT
    assert len(result.rows) == F11_EXPECTED_PRIVATE_OVERLAP_ROW_COUNT
    assert result.unclear_count <= F11_UNCLEAR_MAX_ROWS

    print(f"F11_GIT_SHA={result.git_sha}")
    print(f"F11_PARENT_STALE={result.parent_stale_row_count}")
    print(f"F11_SLICE_ROWS={len(result.rows)}")
    print(f"F11_ROOT_CAUSE_HISTOGRAM={result.root_cause_histogram}")
    print(f"F11_UNCLEAR_COUNT={result.unclear_count}")
    print(f"F11_F12_NOMINATION={result.f12_nomination.to_dict()}")
    print(f"F11_ROWS_JSON={[r.to_dict() for r in result.rows]}")

    for row in result.rows:
        assert row.f11_root_cause is not ElcpF11PrivateOverlapRootCause.UNCLEAR_NEEDS_TRACE or (
            result.unclear_count <= F11_UNCLEAR_MAX_ROWS
        )
```

- [ ] **Step 2: Run investigation test**

Run: `python -m pytest tests/investigation/test_rttp_elcp_rf_f11_private_overlap_forensic.py::test_gate_a_f11_private_overlap_forensic -v`

Expected: PASS (if unclear > 2 on real data, adjust classification rules per spec — **do not** weaken gates without spec amendment)

- [ ] **Step 3: Confirm G1 still RED (sanity, not F1.1 scope)**

Run: `python -m pytest tests/investigation/test_rttp_elcp_rf_f1_reservation_policy_gate_a.py::test_gate_a_f1_private_route_overlap_mechanism_g1 -v`

Expected: **FAIL** (20 > 11) — confirms F1.1 did not green G1

---

### Task 5: Report

**Files:**
- Create: `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic-report.md`

- [ ] **Step 1: Run investigation test and capture prints**

- [ ] **Step 2: Fill report §0–§8** per spec §9 using histogram + nomination from test output. Include normative header:

```text
D0/E0 historical stale baseline = 34; current Gate A stale universe = 33;
F1.1 analyzes 20 private_route_overlap rows only.
```

Include split withheld prose when applicable:

```text
Split fixable classes means F1.1 produced diagnosis, but F1.2 implementation
must not combine multiple policy changes in one PR.
```

- [ ] **Step 3: Set report Status CLOSED** when investigation test green

---

### Task 6: Validation + regression

- [ ] **Step 1: Unit + investigation**

Run: `python -m pytest tests/unit/harness/test_rttp_elcp_f11_private_overlap_forensic.py tests/investigation/test_rttp_elcp_rf_f11_private_overlap_forensic.py -v`

Expected: PASS

- [ ] **Step 2: E0 + F1 G1 unchanged behavior**

Run: `python -m pytest tests/investigation/test_rttp_elcp_rf_e0_reservation_mechanism.py -v`

Expected: PASS

Run: `python -m pytest tests/investigation/test_rttp_elcp_rf_f1_reservation_policy_gate_a.py::test_gate_a_f1_private_route_overlap_mechanism_g1 -v`

Expected: FAIL (G1 RED)

- [ ] **Step 3: Ruff on all touched paths**

Run: `python -m ruff check harness/investigation/rttp_elcp_f11_private_overlap_forensic.py tests/support/rttp_f11_gate_a_frozen_bounds.py tests/unit/harness/test_rttp_elcp_f11_private_overlap_forensic.py tests/investigation/test_rttp_elcp_rf_f11_private_overlap_forensic.py`

Expected: PASS

---

### Task 7: Close F1.1 in queue (after report)

**Files:**
- Modify: `documents/ai/current_plan.md`

- [ ] **Step 1: Mark F1.1 CLOSED** with date; keep F1 PARTIAL until G1 met by F1.2

- [ ] **Step 2: Commit** (only when user explicitly requests)

---

## Plan self-review

| Spec requirement | Task |
|------------------|------|
| Read-only / no django_apps | Tasks 3–6 |
| O_full_not_reserved SoT | Task 2–3 |
| Conservative true_peer rule | Task 2 tests |
| unclear ≤ 2, rows == 20 | Task 1, 4 |
| G1 RED unchanged | Task 4 step 3 |
| F1.2 nomination / split prose | Task 2, 5 |
| Counterfactual B deferred | Spec only |
| Report + JSON SoT | Task 4–5 |

No TBD steps. Type names consistent: `ElcpF11PrivateOverlapRootCause`, `F12PolicyNomination`, `run_gate_a_elcp_f11_private_overlap_forensics`.
