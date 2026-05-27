# P1-ELCP-RF-C0 — Post-B1 Commit-Layer Re-Gate — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Read-only Gate A dual-run forensics — compare `GREEDY_REGRET` vs `GREEDY_REGRET_OVERLAP_PACK` primary commit outcomes on the same SHA/config; publish delta table + Layer 2 bucket histograms; re-gate `lane_capacity_shortfall` B-spec (decision only, no nomination).

**Architecture:** `harness/investigation/rttp_elcp_c0_dual_mode.py` loads recovery-map RF.1 fixture once, runs `run_rttp_pipeline` twice with identical `RttpPipelineConfig` except `selection_mode`, captures first `incremental_commit` via patch, builds M1 mirror ledger per mode, emits comparison row + re-gate verdict helper. Investigation test asserts mirror parity, ≥95% bucket coverage, and fresh baseline `commit_order_len` parity with B1 guards. **No production edits.**

**Tech Stack:** Python 3.12+, pytest, ruff; `SelectionMode`, `run_rttp_pipeline`, `rttp_elcp_reprobe_forensics`, `rttp_elcp_universe_sanity`, `rttp-core-recovery-test-map`.

**Design spec:** [`docs/superpowers/specs/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-design.md`](../specs/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-design.md)

---

## File structure

| File | Responsibility |
|------|----------------|
| `tests/support/rttp_c0_historical_anchors.py` | Appendix-only frozen RF/A2/B1 numbers (not assertion SoT) |
| `harness/investigation/rttp_elcp_c0_dual_mode.py` | Gate A fixture builder, per-mode run snapshot, dual-run compare, re-gate verdict helper, `git_sha` |
| `tests/investigation/test_rttp_elcp_rf_c0_post_b1_commit_regate.py` | Slow integration: dual-run + parity + coverage + publish prints |
| `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-report.md` | Delta table, histograms, re-gate verdict, historical appendix |
| `documents/ai/current_plan.md` | ACTIVE C0 row → CLOSED when report + acceptance |

**Not modified:** `incremental_commit.py`, `pipeline.py`, `greedy_regret.py`, `overlap_pack.py`, `selection_mode.py`, `test_rttp_elcp_reprobe_forensics.py` (RF.1 stays separate).

---

## Spec → plan coverage

| Spec § | Task |
|--------|------|
| §2 fresh dual-run Policy B | Tasks 2–4 |
| §2.2 historical appendix only | Task 1 |
| §4.1 primary first-call capture | Task 2 |
| §4.2 comparison table + informational labels | Tasks 2–3, 5 |
| §4.3 M1 histogram ×2, ≥95% | Task 4 |
| §4.4 M2 cross-check | Task 4 |
| §6 decision heuristic (report prose) | Task 5 |
| §7 re-gate BLOCKED/NARROWED/UNBLOCKED | Tasks 2, 5 |
| §10 acceptance (7 bullets) | Tasks 4–6 |
| No production change | All tasks |

---

### Task 0: Queue + spec linkage

**Files:**
- Modify: `documents/ai/current_plan.md`

- [ ] **Step 1: Add ACTIVE row** after B1 CLOSED line:

```markdown
**ACTIVE (2026-05-27):** **P1-ELCP-RF-C0** — Post-B1 commit-layer re-gate (fresh dual-run `GREEDY_REGRET` vs `GREEDY_REGRET_OVERLAP_PACK`, Gate A). Spec: [`2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-design.md`](../../docs/superpowers/specs/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-design.md) · plan: [`2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate.md`](../../docs/superpowers/plans/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate.md).
```

- [ ] **Step 2: Commit** (only if user requests commit)

```bash
git add documents/ai/current_plan.md docs/superpowers/specs/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-design.md docs/superpowers/plans/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate.md
git commit -m "docs: add P1-ELCP-RF-C0 post-B1 commit re-gate spec and plan"
```

---

### Task 1: Historical anchors (appendix-only constants)

**Files:**
- Create: `tests/support/rttp_c0_historical_anchors.py`

- [ ] **Step 1: Add constants module**

```python
"""Appendix-only historical anchors for P1-ELCP-RF-C0 (NOT primary evidence)."""

from __future__ import annotations

# P1-ELCP-RF RF.1 / A2 (frozen reports — reference only)
HISTORICAL_GREEDY_REGRET_COMMIT_ORDER_LEN = 59
HISTORICAL_PRIMARY_COMMITTED_COUNT = 3
HISTORICAL_PRIMARY_REPROBE_FAILED_COUNT = 29

# B1 Gate A overlap-pack target_floor (reference only)
HISTORICAL_OVERLAP_PACK_COMMIT_ORDER_LEN = 67

__all__ = [
    "HISTORICAL_GREEDY_REGRET_COMMIT_ORDER_LEN",
    "HISTORICAL_OVERLAP_PACK_COMMIT_ORDER_LEN",
    "HISTORICAL_PRIMARY_COMMITTED_COUNT",
    "HISTORICAL_PRIMARY_REPROBE_FAILED_COUNT",
]
```

- [ ] **Step 2: Run ruff**

Run: `python -m ruff check tests/support/rttp_c0_historical_anchors.py`  
Expected: PASS

---

### Task 2: C0 harness — snapshot DTO + single-mode runner

**Files:**
- Create: `harness/investigation/rttp_elcp_c0_dual_mode.py`

- [ ] **Step 1: Write failing unit test for snapshot builder (no DB)**

Create: `tests/unit/harness/test_rttp_elcp_c0_dual_mode.py`

```python
"""Unit tests for C0 dual-mode comparison helpers (no Django DB)."""

from __future__ import annotations

from harness.investigation.rttp_elcp_c0_dual_mode import (
    ElcpC0ModeRunSnapshot,
    build_dual_run_comparison_table,
    derive_lane_capacity_shortfall_regate,
)


def _snap(
    *,
    mode: str,
    commit_order_len: int,
    primary_committed_count: int,
    lane_capacity_shortfall_count: int,
    stale_candidate_reachable_count: int,
    dominant_bucket: str,
    dominant_bucket_pct: float,
) -> ElcpC0ModeRunSnapshot:
    return ElcpC0ModeRunSnapshot(
        selection_mode=mode,
        git_sha="test-sha",
        commit_order_len=commit_order_len,
        primary_committed_count=primary_committed_count,
        primary_conflict_count=commit_order_len - primary_committed_count,
        primary_reprobe_failed_count=0,
        lane_capacity_shortfall_count=lane_capacity_shortfall_count,
        route_feasible_shortfall_count=0,
        stale_candidate_reachable_count=stale_candidate_reachable_count,
        validation_passed=True,
        throughput_shortfall_reason=None,
        bucket_coverage=1.0,
        bucket_histogram={"lane_capacity_shortfall": lane_capacity_shortfall_count},
        dominant_bucket=dominant_bucket,
        dominant_bucket_pct=dominant_bucket_pct,
    )


def test_build_dual_run_comparison_table_delta() -> None:
    baseline = _snap(
        mode="greedy_regret",
        commit_order_len=59,
        primary_committed_count=3,
        lane_capacity_shortfall_count=10,
        stale_candidate_reachable_count=27,
        dominant_bucket="stale_candidate_reachable",
        dominant_bucket_pct=0.48,
    )
    overlap = _snap(
        mode="greedy_regret_overlap_pack",
        commit_order_len=67,
        primary_committed_count=3,
        lane_capacity_shortfall_count=12,
        stale_candidate_reachable_count=30,
        dominant_bucket="lane_capacity_shortfall",
        dominant_bucket_pct=0.42,
    )
    table = build_dual_run_comparison_table(baseline=baseline, overlap=overlap)
    row = next(r for r in table if r["metric"] == "commit_order_len")
    assert row["greedy_regret"] == 59
    assert row["greedy_regret_overlap_pack"] == 67
    assert row["delta"] == 8


def test_derive_regate_unblocked_when_lane_dominant_on_overlap() -> None:
    baseline = _snap(
        mode="greedy_regret",
        commit_order_len=59,
        primary_committed_count=3,
        lane_capacity_shortfall_count=5,
        stale_candidate_reachable_count=27,
        dominant_bucket="stale_candidate_reachable",
        dominant_bucket_pct=0.48,
    )
    overlap = _snap(
        mode="greedy_regret_overlap_pack",
        commit_order_len=67,
        primary_committed_count=3,
        lane_capacity_shortfall_count=20,
        stale_candidate_reachable_count=10,
        dominant_bucket="lane_capacity_shortfall",
        dominant_bucket_pct=0.45,
    )
    verdict, _reason = derive_lane_capacity_shortfall_regate(
        baseline=baseline,
        overlap=overlap,
        validation_regression=False,
    )
    assert verdict in ("UNBLOCKED", "NARROWED_TO_COMMIT_ORDER")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/harness/test_rttp_elcp_c0_dual_mode.py -v`  
Expected: FAIL — `ModuleNotFoundError` or import error for `rttp_elcp_c0_dual_mode`

- [ ] **Step 3: Implement harness module (part 1 — DTOs + table + regate)**

```python
"""P1-ELCP-RF-C0: Gate A dual-mode primary commit forensics (not solver input)."""

from __future__ import annotations

import subprocess
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping, Sequence
from unittest.mock import patch

from django_apps.asteroid_lab.contracts.selection_mode import SelectionMode
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflictReason,
    CommitResult,
    incremental_commit,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpPipelineConfig,
)
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from harness.investigation.rttp_elcp_reprobe_forensics import (
    ElcpProbeFailureClass,
    assert_mirror_parity,
    build_elcp_primary_mirror_ledger,
)
from harness.investigation.rttp_elcp_reprobe_step_forensics import extract_elcp_reprobe_forensics
from harness.investigation.rttp_elcp_universe_sanity import extract_elcp_attempt_universe_sanity

GATE_A_RECOVERY_SLUG = "rttp-core-recovery-test-map"
DOMINANT_BUCKET_MIN_PCT = 0.40


@dataclass(frozen=True, slots=True)
class ElcpC0ModeRunSnapshot:
    selection_mode: str
    git_sha: str
    commit_order_len: int
    primary_committed_count: int
    primary_conflict_count: int
    primary_reprobe_failed_count: int
    lane_capacity_shortfall_count: int
    route_feasible_shortfall_count: int
    stale_candidate_reachable_count: int
    validation_passed: bool
    throughput_shortfall_reason: str | None
    bucket_coverage: float
    bucket_histogram: dict[str, int]
    dominant_bucket: str
    dominant_bucket_pct: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "selection_mode": self.selection_mode,
            "git_sha": self.git_sha,
            "commit_order_len": self.commit_order_len,
            "primary_committed_count": self.primary_committed_count,
            "primary_conflict_count": self.primary_conflict_count,
            "primary_reprobe_failed_count": self.primary_reprobe_failed_count,
            "lane_capacity_shortfall_count": self.lane_capacity_shortfall_count,
            "route_feasible_shortfall_count": self.route_feasible_shortfall_count,
            "stale_candidate_reachable_count": self.stale_candidate_reachable_count,
            "validation_passed": self.validation_passed,
            "throughput_shortfall_reason": self.throughput_shortfall_reason,
            "bucket_coverage": self.bucket_coverage,
            "bucket_histogram": dict(self.bucket_histogram),
            "dominant_bucket": self.dominant_bucket,
            "dominant_bucket_pct": self.dominant_bucket_pct,
        }


def resolve_git_sha() -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return proc.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _bucket_stats(ledger_failed: Sequence[object]) -> tuple[float, dict[str, int], str, float]:
    histogram = Counter(
        row.probe_failure_class.value  # type: ignore[attr-defined]
        for row in ledger_failed
    )
    if not ledger_failed:
        return 1.0, {}, "none", 0.0
    known = sum(
        1
        for row in ledger_failed
        if row.probe_failure_class is not ElcpProbeFailureClass.UNKNOWN_REPROBE_FAILED  # type: ignore[attr-defined]
    )
    coverage = known / len(ledger_failed)
    dominant_bucket, dominant_count = histogram.most_common(1)[0]
    dominant_pct = dominant_count / len(ledger_failed)
    return coverage, dict(histogram), dominant_bucket, dominant_pct


def _extract_throughput_shortfall_reason(algorithm_steps: Sequence[Mapping[str, object]]) -> str | None:
    for step in algorithm_steps:
        metrics = step.get("metrics")
        if not isinstance(metrics, Mapping):
            continue
        reason = metrics.get("throughput_shortfall_reason")
        if isinstance(reason, str) and reason:
            return reason
        summary = step.get("summary")
        if isinstance(summary, str) and "throughput" in summary.lower():
            return summary
    return None


def build_dual_run_comparison_table(
    *,
    baseline: ElcpC0ModeRunSnapshot,
    overlap: ElcpC0ModeRunSnapshot,
) -> list[dict[str, Any]]:
    def _row(metric: str, base_val: Any, overlap_val: Any, *, delta: Any | None = None) -> dict[str, Any]:
        if delta is None and isinstance(base_val, int) and isinstance(overlap_val, int):
            delta = overlap_val - base_val
        return {
            "metric": metric,
            "greedy_regret": base_val,
            "greedy_regret_overlap_pack": overlap_val,
            "delta": delta,
        }

    return [
        _row("commit_order_len", baseline.commit_order_len, overlap.commit_order_len),
        _row("primary_committed_count", baseline.primary_committed_count, overlap.primary_committed_count),
        _row("primary_conflict_count", baseline.primary_conflict_count, overlap.primary_conflict_count),
        _row(
            "primary_reprobe_failed_count",
            baseline.primary_reprobe_failed_count,
            overlap.primary_reprobe_failed_count,
        ),
        _row(
            "lane_capacity_shortfall_count",
            baseline.lane_capacity_shortfall_count,
            overlap.lane_capacity_shortfall_count,
        ),
        _row(
            "route_feasible_shortfall_count",
            baseline.route_feasible_shortfall_count,
            overlap.route_feasible_shortfall_count,
        ),
        _row(
            "stale_candidate_reachable_count",
            baseline.stale_candidate_reachable_count,
            overlap.stale_candidate_reachable_count,
        ),
        {
            "metric": "validation_passed",
            "greedy_regret": baseline.validation_passed,
            "greedy_regret_overlap_pack": overlap.validation_passed,
            "delta": None,
            "signal_class": "informational_e2e",
        },
        {
            "metric": "throughput_shortfall_reason",
            "greedy_regret": baseline.throughput_shortfall_reason,
            "greedy_regret_overlap_pack": overlap.throughput_shortfall_reason,
            "delta": None,
            "signal_class": "informational",
        },
    ]


def derive_lane_capacity_shortfall_regate(
    *,
    baseline: ElcpC0ModeRunSnapshot,
    overlap: ElcpC0ModeRunSnapshot,
    validation_regression: bool,
) -> tuple[str, str]:
    if validation_regression:
        return (
            "BLOCKED",
            "validation_passed E2E regression on overlap-pack (informational_e2e); C0 blocked pending B1 follow-up",
        )
    committed_delta = overlap.primary_committed_count - baseline.primary_committed_count
    if overlap.dominant_bucket == ElcpProbeFailureClass.STALE_CANDIDATE_REACHABLE.value:
        if overlap.dominant_bucket_pct >= DOMINANT_BUCKET_MIN_PCT:
            return (
                "BLOCKED",
                "stale_candidate_reachable dominant on overlap-pack; lane_capacity_shortfall B-spec not appropriate",
            )
    if overlap.dominant_bucket == ElcpProbeFailureClass.LANE_CAPACITY_SHORTFALL.value:
        if overlap.dominant_bucket_pct >= DOMINANT_BUCKET_MIN_PCT:
            if committed_delta <= 1:
                return (
                    "UNBLOCKED",
                    "lane_capacity_shortfall dominant on overlap-pack with low committed lift; Layer 2 B-spec may be drafted separately",
                )
            return (
                "NARROWED_TO_COMMIT_ORDER",
                "lane_capacity_shortfall dominant but primary_committed improved; scope commit-order universe",
            )
    if committed_delta >= 2:
        return (
            "BLOCKED",
            "primary_committed meaningfully increased; re-evaluate next bottleneck before lane_capacity_shortfall B-spec",
        )
    if baseline.commit_order_len < overlap.commit_order_len and committed_delta <= 1:
        return (
            "UNBLOCKED",
            "commit_order grew but primary_committed flat; Layer 2 lane_capacity_shortfall is primary suspect",
        )
    return (
        "BLOCKED",
        "no clear lane_capacity_shortfall dominance or committed lift; keep program B-spec blocked",
    )
```

- [ ] **Step 4: Run unit test**

Run: `python -m pytest tests/unit/harness/test_rttp_elcp_c0_dual_mode.py -v`  
Expected: PASS (partial — `run_gate_a_elcp_c0_mode` not yet implemented)

- [ ] **Step 5: Commit** (only if user requests)

```bash
git add harness/investigation/rttp_elcp_c0_dual_mode.py tests/unit/harness/test_rttp_elcp_c0_dual_mode.py tests/support/rttp_c0_historical_anchors.py
git commit -m "feat(harness): add ELCP C0 dual-mode snapshot and regate helpers"
```

---

### Task 3: C0 harness — Gate A fixture + `run_gate_a_elcp_c0_mode`

**Files:**
- Modify: `harness/investigation/rttp_elcp_c0_dual_mode.py`

- [ ] **Step 1: Add Gate A loader + pipeline runner** (append to same module)

Import pattern from [`tests/investigation/test_rttp_elcp_reprobe_forensics.py`](../../../tests/investigation/test_rttp_elcp_reprobe_forensics.py) lines 108–176. Add:

```python
def build_gate_a_rf1_inputs(
    *,
    imported_game_data_batch_module: object,
) -> tuple[OptimizationInput, RttpPipelineConfig]:
    from django_apps.asteroid_lab import models as m
    from django_apps.asteroid_lab.management.commands.import_rttp_core_recovery_test_map import (
        import_core_recovery_test_map,
    )
    from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
        optimization_input_from_reconstruction,
    )
    from django_apps.asteroid_lab.reconstruction.complete_map import build_reconstruction_complete_map
    from django_apps.asteroid_lab.reconstruction.field_cells import (
        asteroid_field_cell_count_for_placement,
    )
    from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
        run_reconstruction_for_map_input,
    )
    from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
        build_reconstruction_capacity_envelope,
    )
    from django_apps.asteroid_lab.services.throughput_target import (
        compute_target_throughput_per_min,
        parse_throughput_target_percent,
        primary_reconstruction_max_per_min,
    )
    from django_apps.web.services.asteroid_game_data_snapshot import (
        build_asteroid_game_data_snapshot_with_provenance,
    )

    _ = imported_game_data_batch_module
    project_id = import_core_recovery_test_map(replace=True)
    build = build_asteroid_game_data_snapshot_with_provenance()
    inp_row = m.AsteroidMapInput.objects.filter(project_id=project_id).first()
    if inp_row is None:
        msg = "recovery map AsteroidMapInput missing"
        raise AssertionError(msg)
    cleanup, recon = run_reconstruction_for_map_input(
        int(inp_row.pk),
        boundary_run_id="elcp-c0-post-b1-regate",
    )
    complete_map = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    inp = optimization_input_from_reconstruction(
        recon,
        cleanup=cleanup,
        catalog_slice=build.catalog_slice,
        complete_map=complete_map,
    )
    cap = build_reconstruction_capacity_envelope(complete_map=complete_map)
    percent = parse_throughput_target_percent({})
    target = compute_target_throughput_per_min(
        reconstruction_max=primary_reconstruction_max_per_min(cap),
        percent=percent,
    )
    platform = asteroid_field_cell_count_for_placement(complete_map, inp.transport_kind)
    pipeline_config = RttpPipelineConfig(
        target_throughput_per_min=target,
        placement_target_percent=percent,
        placement_platform_cell_count=platform,
        reconstruction_max_throughput_per_min=primary_reconstruction_max_per_min(cap),
    )
    return inp, pipeline_config


def run_gate_a_elcp_c0_mode(
    *,
    inp: OptimizationInput,
    pipeline_config: RttpPipelineConfig,
    selection_mode: SelectionMode,
    git_sha: str,
) -> ElcpC0ModeRunSnapshot:
    config = RttpPipelineConfig(
        target_throughput_per_min=pipeline_config.target_throughput_per_min,
        placement_target_percent=pipeline_config.placement_target_percent,
        placement_platform_cell_count=pipeline_config.placement_platform_cell_count,
        reconstruction_max_throughput_per_min=pipeline_config.reconstruction_max_throughput_per_min,
        max_placement_goal_count=pipeline_config.max_placement_goal_count,
        selection_mode=selection_mode,
        deferred_retry_shadow=pipeline_config.deferred_retry_shadow,
        ga_evolution_shadow=pipeline_config.ga_evolution_shadow,
        catalog_placement_validation_mode=pipeline_config.catalog_placement_validation_mode,
    )
    captured: dict[str, object] = {}
    primary_results: list[CommitResult] = []
    real_commit = incremental_commit

    def _capture_primary(*args: object, **kwargs: object) -> CommitResult:
        result = real_commit(*args, **kwargs)
        primary_results.append(result)
        captured["genome"] = args[0]
        captured["candidates_by_id"] = args[1]
        captured["inp"] = args[2]
        captured["skeleton"] = args[3]
        captured["domain"] = kwargs["domain"]
        captured["exterior_lane_plan"] = kwargs.get("exterior_lane_plan")
        captured["route_probe_start_policy"] = kwargs.get("route_probe_start_policy")
        captured["resource_kind"] = kwargs.get("resource_kind")
        return result

    with patch(
        "django_apps.asteroid_lab.optimization.pipeline.incremental_commit",
        side_effect=_capture_primary,
    ):
        pipeline_result = run_rttp_pipeline(
            inp,
            policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
            fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
            route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
            pipeline_config=config,
        )

    if not primary_results:
        msg = "primary incremental_commit was not called"
        raise AssertionError(msg)
    primary = primary_results[0]
    plan = captured.get("exterior_lane_plan")
    if plan is None:
        msg = "ELCP exterior_lane_plan required for C0 Gate A"
        raise AssertionError(msg)

    mirror = build_elcp_primary_mirror_ledger(
        genome=captured["genome"],
        candidates_by_id=captured["candidates_by_id"],
        inp=captured["inp"],
        skeleton=captured["skeleton"],
        domain=captured["domain"],
        exterior_lane_plan=plan,
        route_probe_start_policy=captured["route_probe_start_policy"],
        resource_kind=str(captured["resource_kind"]),
    )
    assert_mirror_parity(production=primary, mirror=mirror)

    failed = mirror.ledger
    coverage, histogram, dominant_bucket, dominant_pct = _bucket_stats(failed)
    stale_count = histogram.get(ElcpProbeFailureClass.STALE_CANDIDATE_REACHABLE.value, 0)
    reprobe_count = sum(
        1
        for conflict in primary.conflicts
        if conflict.reason is CommitConflictReason.REPROBE_FAILED
    )

    step_forensics = extract_elcp_reprobe_forensics(pipeline_result.algorithm_steps)
    assert step_forensics["lane_capacity_shortfall_count"] == primary.lane_capacity_shortfall_count
    assert step_forensics["route_feasible_shortfall_count"] == primary.route_feasible_shortfall_count

    _ = extract_elcp_attempt_universe_sanity(
        algorithm_steps=pipeline_result.algorithm_steps,
        inp=inp,
        pipeline_config=config,
        primary_commit_result=primary,
        exterior_lane_plan=plan,
    )

    genome = captured["genome"]
    commit_order_len = len(genome.commit_order)  # type: ignore[attr-defined]

    return ElcpC0ModeRunSnapshot(
        selection_mode=selection_mode.value,
        git_sha=git_sha,
        commit_order_len=commit_order_len,
        primary_committed_count=len(primary.committed_ids),
        primary_conflict_count=len(primary.conflicts),
        primary_reprobe_failed_count=reprobe_count,
        lane_capacity_shortfall_count=primary.lane_capacity_shortfall_count,
        route_feasible_shortfall_count=primary.route_feasible_shortfall_count,
        stale_candidate_reachable_count=stale_count,
        validation_passed=pipeline_result.validation_passed,
        throughput_shortfall_reason=_extract_throughput_shortfall_reason(
            pipeline_result.algorithm_steps
        ),
        bucket_coverage=coverage,
        bucket_histogram=histogram,
        dominant_bucket=dominant_bucket,
        dominant_bucket_pct=dominant_pct,
    )


def run_gate_a_elcp_c0_dual_mode(
    *,
    imported_game_data_batch_module: object,
) -> tuple[ElcpC0ModeRunSnapshot, ElcpC0ModeRunSnapshot, list[dict[str, Any]], str, str]:
    git_sha = resolve_git_sha()
    inp, pipeline_config = build_gate_a_rf1_inputs(
        imported_game_data_batch_module=imported_game_data_batch_module,
    )
    baseline = run_gate_a_elcp_c0_mode(
        inp=inp,
        pipeline_config=pipeline_config,
        selection_mode=SelectionMode.GREEDY_REGRET,
        git_sha=git_sha,
    )
    overlap = run_gate_a_elcp_c0_mode(
        inp=inp,
        pipeline_config=pipeline_config,
        selection_mode=SelectionMode.GREEDY_REGRET_OVERLAP_PACK,
        git_sha=git_sha,
    )
    table = build_dual_run_comparison_table(baseline=baseline, overlap=overlap)
    validation_regression = baseline.validation_passed and not overlap.validation_passed
    verdict, reason = derive_lane_capacity_shortfall_regate(
        baseline=baseline,
        overlap=overlap,
        validation_regression=validation_regression,
    )
    return baseline, overlap, table, verdict, reason
```

- [ ] **Step 2: Export `__all__`** at module bottom:

```python
__all__ = [
    "ElcpC0ModeRunSnapshot",
    "GATE_A_RECOVERY_SLUG",
    "build_dual_run_comparison_table",
    "build_gate_a_rf1_inputs",
    "derive_lane_capacity_shortfall_regate",
    "resolve_git_sha",
    "run_gate_a_elcp_c0_dual_mode",
    "run_gate_a_elcp_c0_mode",
]
```

- [ ] **Step 3: Ruff**

Run: `python -m ruff check harness/investigation/rttp_elcp_c0_dual_mode.py tests/unit/harness/test_rttp_elcp_c0_dual_mode.py`  
Expected: PASS

---

### Task 4: Investigation integration test

**Files:**
- Create: `tests/investigation/test_rttp_elcp_rf_c0_post_b1_commit_regate.py`

- [ ] **Step 1: Add slow integration test**

```python
"""P1-ELCP-RF-C0: Gate A dual-mode primary commit re-gate (read-only)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.contracts.selection_mode import SelectionMode
from harness.investigation.rttp_elcp_c0_dual_mode import run_gate_a_elcp_c0_dual_mode
from tests.support.rttp_b1_gate_a_frozen_bounds import GATE_A_TARGET_FLOOR
from tests.support.rttp_c0_historical_anchors import (
    HISTORICAL_GREEDY_REGRET_COMMIT_ORDER_LEN,
    HISTORICAL_OVERLAP_PACK_COMMIT_ORDER_LEN,
)


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


@pytest.mark.django_db
@pytest.mark.slow
def test_gate_a_elcp_c0_dual_mode_primary_regate(
    imported_game_data_batch_module: object,
) -> None:
    baseline, overlap, table, verdict, reason = run_gate_a_elcp_c0_dual_mode(
        imported_game_data_batch_module=imported_game_data_batch_module,
    )

    assert baseline.git_sha == overlap.git_sha
    assert baseline.selection_mode == SelectionMode.GREEDY_REGRET.value
    assert overlap.selection_mode == SelectionMode.GREEDY_REGRET_OVERLAP_PACK.value

    # Fresh dual-run SoT (not historical constants)
    assert baseline.commit_order_len == HISTORICAL_GREEDY_REGRET_COMMIT_ORDER_LEN
    assert overlap.commit_order_len >= GATE_A_TARGET_FLOOR
    assert overlap.commit_order_len >= baseline.commit_order_len

    assert baseline.bucket_coverage >= 0.95
    assert overlap.bucket_coverage >= 0.95

    assert verdict in ("BLOCKED", "NARROWED_TO_COMMIT_ORDER", "UNBLOCKED")

    print(f"C0_GIT_SHA={baseline.git_sha}")
    print(f"C0_DUAL_RUN_TABLE={table}")
    print(f"C0_BASELINE_SNAPSHOT={baseline.to_dict()}")
    print(f"C0_OVERLAP_SNAPSHOT={overlap.to_dict()}")
    print(f"C0_REGATE_VERDICT={verdict}")
    print(f"C0_REGATE_REASON={reason}")
    print(
        "C0_HISTORICAL_APPENDIX="
        f"greedy={HISTORICAL_GREEDY_REGRET_COMMIT_ORDER_LEN} "
        f"overlap_target={HISTORICAL_OVERLAP_PACK_COMMIT_ORDER_LEN} "
        "(not primary SoT)"
    )
```

**Note:** If fresh `GREEDY_REGRET` `commit_order_len` drifts from 59 on this SHA, replace the equality assert with `pytest.fail` message documenting drift and keep `>= 1` overlap delta vs baseline — per spec §2.3.

- [ ] **Step 2: Run investigation test**

Run: `python -m pytest tests/investigation/test_rttp_elcp_rf_c0_post_b1_commit_regate.py::test_gate_a_elcp_c0_dual_mode_primary_regate -v`  
Expected: PASS — prints `C0_*` lines with `primary_committed_count` for both modes

- [ ] **Step 3: Run unit harness tests**

Run: `python -m pytest tests/unit/harness/test_rttp_elcp_c0_dual_mode.py -v`  
Expected: PASS

- [ ] **Step 4: Commit** (only if user requests)

```bash
git add harness/investigation/rttp_elcp_c0_dual_mode.py tests/investigation/test_rttp_elcp_rf_c0_post_b1_commit_regate.py tests/unit/harness/test_rttp_elcp_c0_dual_mode.py
git commit -m "test(investigation): add P1-ELCP-RF-C0 Gate A dual-mode re-gate"
```

---

### Task 5: C0 report + re-gate narrative

**Files:**
- Create: `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-report.md`

- [ ] **Step 1: Run investigation test and capture stdout**

Run: `python -m pytest tests/investigation/test_rttp_elcp_rf_c0_post_b1_commit_regate.py::test_gate_a_elcp_c0_dual_mode_primary_regate -v -s`  
Expected: `C0_DUAL_RUN_TABLE`, histograms, `C0_REGATE_VERDICT`

- [ ] **Step 2: Write report** with sections:

1. **Header** — Status CLOSED, `git_sha`, slug, spec/plan links  
2. **§1 Dual-run table** — paste markdown table from `build_dual_run_comparison_table`  
3. **§2 Histograms** — baseline vs overlap `bucket_histogram` + coverage %  
4. **§3 Decision heuristic** — committed delta, dominant buckets (reference spec §6)  
5. **§4 Re-gate** — `lane_capacity_shortfall`: `BLOCKED` | `NARROWED_TO_COMMIT_ORDER` | `UNBLOCKED` + reason string from harness  
6. **§5 Historical appendix** — 59/3/29 and 67 target_floor with “not primary SoT” banner  
7. **§6 Next track** — one row from user decision table (lane B-spec vs stale vs B1 keep)

- [ ] **Step 3: Link report in spec** (optional header status → CLOSED with date)

- [ ] **Step 4: Commit** (only if user requests)

```bash
git add docs/superpowers/reports/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-report.md
git commit -m "docs: P1-ELCP-RF-C0 post-B1 commit re-gate report"
```

---

### Task 6: Close queue + parent report pointer

**Files:**
- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/reports/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-report.md` (add § C0 follow-up link only)

- [ ] **Step 1: Mark C0 CLOSED in `current_plan.md`**; keep P1-ELCP-RF REOPENED until product closes or opens B-spec.

- [ ] **Step 2: Add to primary RF report** (short §):

```markdown
## C0 follow-up (post-B1)

Report: [`2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-report.md`](2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-report.md)
Fresh dual-run re-gate on same SHA; frozen 59/3/29 is appendix only.
```

- [ ] **Step 3: Commit** (only if user requests)

```bash
git add documents/ai/current_plan.md docs/superpowers/reports/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-report.md
git commit -m "docs: close P1-ELCP-RF-C0 queue entry"
```

---

### Task 7: Validation gate

- [ ] **Step 1: Narrow pytest**

Run: `python -m pytest tests/unit/harness/test_rttp_elcp_c0_dual_mode.py tests/investigation/test_rttp_elcp_rf_c0_post_b1_commit_regate.py -v`  
Expected: PASS

- [ ] **Step 2: Ruff**

Run: `python -m ruff check harness/investigation/rttp_elcp_c0_dual_mode.py tests/investigation/test_rttp_elcp_rf_c0_post_b1_commit_regate.py tests/unit/harness/test_rttp_elcp_c0_dual_mode.py tests/support/rttp_c0_historical_anchors.py`  
Expected: PASS

- [ ] **Step 3: Confirm no production files changed**

Run: `git diff --name-only django_apps/`  
Expected: empty (C0 is harness/tests/docs only)

---

## Plan self-review

| Check | Result |
|-------|--------|
| Spec §2 dual-run Policy B | Tasks 3–4 |
| Primary first-call only | Task 3 `run_gate_a_elcp_c0_mode` |
| informational_e2e / informational throughput | Task 2 table rows + report §1 |
| No B-spec nomination | Task 5 §4 verdict only |
| §10 acceptance 7 bullets | Tasks 4–7 |
| Placeholders | None |
| Type names consistent | `ElcpC0ModeRunSnapshot` throughout |

---

## Execution handoff

Plan saved to [`docs/superpowers/plans/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate.md`](2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate.md).

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute tasks in this session with executing-plans checkpoints  

**Which approach?**

**Spec review gate:** Design spec is at [`docs/superpowers/specs/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-design.md`](../specs/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-design.md). Please review and confirm before implementation starts (or note changes).
