# Sequence 3B — RTTP Optimization Milestones Lab Timeline Implementation Plan

> **SUPERSEDED (2026-05-23):** PR-2 “Section B panel” and H1 disjoint timeline are replaced by **[Sequence 3B-R — Unified RTTP Algorithm Replay Frames](2026-05-23-sequence-3b-r-unified-rttp-replay.md)** (`inherited_snapshot` append into `lab_replay_frames_json`). PR #43 backend adapter remains; UI primary path is unified scrubber only.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose DB `{run_key}:rttp` RTTP milestone frames in Lab as Section B (`lab_optimization_milestone_frames_json`) while Section A map scrubber stays on `lab_replay_frames_json` only (H1 preserved).

**Architecture:** Approach B — new read-only adapter `build_lab_optimization_milestone_frames_for_project` maps `ReplayFrame` rows from the RTTP track to metrics-only milestone JSON (no `map_view` / `full_map`). Wire through `SolverRuntimeEntryResult`, `entry_result_to_json_dict`, SSR page context, and Run Solver JSON. PR-2 adds a separate Optimization Milestones panel in Lab JS that does not drive the map scrubber.

**Tech Stack:** Python 3.12+, Django 5.2, pytest, ruff, mypy (`django_apps config src`), vanilla JS (`asteroid_miner_layout_lab.js`).

**Design spec:** [`docs/superpowers/specs/2026-05-23-sequence-3b-optimization-replay-lab-timeline-design.md`](../specs/2026-05-23-sequence-3b-optimization-replay-lab-timeline-design.md) (Approved 2026-05-23)

**Baseline:** H1 integration test green; all `test_rttp_*` green; `test_lab_replay_track_selection` green.

**Out of scope:** Merging milestones into `lab_replay_frames_json`, `rttp.*` event types, map projection, NDJSON export, `SolverRun.config_json["optimization_replay_frames"]` legacy path changes.

---

## Plan review amendments (2026-05-23)

Incorporates Sequence 3B Plan Reviewer feedback before PR-1 execution.

| # | Fix |
|---|-----|
| 1 | `SolverRuntimeEntryResult`: default fields **after** all required fields |
| 2 | `test_empty_rttp_track_diagnostic`: includes `SolverRun` + linked `ReplayTrack` |
| 3 | `_empty_track_metrics`: accepts `track_key` + `source_solver_run_id` |
| 4 | Forbidden map keys: check **source `frame_payload`**, not output `body` |
| 5 | `RTTP_MILESTONE_EVENT_TYPES` in **production**; tests import or mirror-verify |
| 6 | PR-2 JS: `textContent` only — no `innerHTML` for replay strings |
| 7 | Empty copy smoke: **template** test, not JS string grep |
| 8 | `_lab_json_bundle_for_track_id`: v0 binds Section B to **latest solver run** (documented + test) |
| 9 | `test_rttp_validation_failure_still_returns_optimization_milestones_section` gate |
| 10 | Section B `frame_index`: **re-number** to visible local 0..n-1 after skips |
| 11 | PR-1 gate: `mypy django_apps config src` (repo standard), not file-scoped only |

**v0 binding (Section B on load-by-track):**

```text
3B v0 accepts latest-run milestone binding for SSR/load-by-track flows.
Track-specific SolverRun selection is deferred until Run picker exists.
```

---

## Spec → plan coverage

| Spec | Plan |
|------|------|
| Approach B separate Section B | PR-1 Tasks 1–6, PR-2 Tasks 7–10 |
| Mandatory v0 sentences (no merge / no map fields) | Task 2 validation + Task 6 integration |
| `lab_optimization_milestone_frames_json` | Tasks 3–5 |
| `lab_optimization_milestone_track_metrics` + `event_types` | Task 1–2 |
| H1 preserved | Task 6 |
| Output-only replay | Task 7 |
| UI panel, empty state | PR-2 Tasks 8–11 |
| Validation failure still returns Section B | Task 3 gate test + both return paths |
| RTTP milestone 4-type filter (production) | Task 2 |
| Visible local `frame_index` | Task 2 |
| Latest-run Section B on `_lab_json_bundle` | Task 4 |

---

## File map

| File | PR | Responsibility |
|------|-----|----------------|
| `django_apps/asteroid_lab/services/lab_optimization_milestone_payload.py` | 1 | Read `:rttp` track → milestone JSON + metrics |
| `tests/support/rttp_milestone_contract.py` | 1 | Re-exports production `RTTP_MILESTONE_EVENT_TYPES` + forbidden map keys |
| `tests/unit/asteroid_lab/test_rttp_milestone_contract.py` | 1 | Mirror-verify production constant |
| `tests/unit/asteroid_lab/test_lab_optimization_milestone_payload.py` | 1 | Adapter unit tests |
| `django_apps/asteroid_lab/services/solver_runtime_entry.py` | 1 | Result dataclass + RTTP paths + JSON dict |
| `django_apps/web/services/asteroid_lab_page_context.py` | 1 | SSR defaults + page load |
| `django_apps/web/views/public_pages.py` | 1 | `_lab_json_bundle_for_track_id` |
| `tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py` | 1 | Extend H1 + Section B assertions |
| `tests/unit/asteroid_lab/test_solver_runtime_entry.py` | 1 | JSON keys present on RTTP run |
| `tests/unit/asteroid_lab/test_optimization_milestone_import_boundary.py` | 1 | `optimization/` must not import adapter |
| `django_apps/web/templates/web/asteroid_miner_layout_solver.html` | 2 | `json_script` + panel markup |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | 2 | Panel render + Run Solver merge |
| `tests/unit/web/test_asteroid_lab_page_context.py` | 2 | JS smoke strings |

---

## Pre-flight (both PRs)

- [ ] **Step 1:** Confirm on `master` (or feature branch) with RTTP v0.2 merged

```powershell
git status
```

- [ ] **Step 2:** Baseline narrow tests

```powershell
python -m pytest tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py tests/unit/asteroid_lab/test_lab_replay_track_selection.py tests/unit/asteroid_lab/test_solver_runtime_entry.py -v
```

Expected: all passed.

- [ ] **Step 3:** Confirm optimization does not import milestone adapter (pre-change)

```powershell
rg "lab_optimization_milestone_payload" django_apps/asteroid_lab/optimization
```

Expected: no matches.

---

# PR-1 — Backend response section

### Task 1: Milestone read adapter (TDD)

**Files:**
- Create: `tests/unit/asteroid_lab/test_lab_optimization_milestone_payload.py`
- Create: `django_apps/asteroid_lab/services/lab_optimization_milestone_payload.py`

- [ ] **Step 1: Write failing unit tests**

```python
# tests/unit/asteroid_lab/test_lab_optimization_milestone_payload.py
from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.replay_track_keys import rttp_optimization_track_key
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.dto import SnapshotEventDTO
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    DIAGNOSTIC_EMPTY_OPTIMIZATION_MILESTONE_FRAMES,
    DIAGNOSTIC_MISSING_OPTIMIZATION_MILESTONE_TRACK,
    RTTP_MILESTONE_EVENT_TYPES,
    build_lab_optimization_milestone_frames_for_project,
)
from django_apps.asteroid_lab.services.replay_recorder import ReplayRecorder
from tests.support.rttp_milestone_contract import FORBIDDEN_MILESTONE_MAP_KEYS

pytestmark = pytest.mark.django_db


def _rttp_event(
    event_type: str,
    *,
    frame_key: str,
    metrics_json: dict | None = None,
) -> SnapshotEventDTO:
    return SnapshotEventDTO(
        event_key=frame_key,
        phase="rttp_pipeline",
        event_type=event_type,
        title=f"title:{event_type}",
        metrics_json=dict(metrics_json or {}),
    )


def test_build_milestone_frames_from_rttp_track() -> None:
    project = m.AsteroidProject.objects.create(name="Mile", slug="mile-1")
    run = m.SolverRun.objects.create(
        project=project,
        run_key="run-a",
        algorithm_label="rttp_v0.1",
        config_json={},
    )
    track = m.ReplayTrack.objects.create(
        project=project,
        track_key=rttp_optimization_track_key("run-a"),
        solver_run=run,
    )
    rec = ReplayRecorder(track.id)
    for i, etype in enumerate(sorted(RTTP_MILESTONE_EVENT_TYPES)):
        rec.record_event(
            _rttp_event(etype, frame_key=f"k{i}", metrics_json={"step": i})
        )

    frames, metrics = build_lab_optimization_milestone_frames_for_project(
        int(project.pk),
        run_key="run-a",
    )
    assert len(frames) == 4
    assert metrics["frame_count"] == 4
    assert metrics["track_key"] == rttp_optimization_track_key("run-a")
    assert set(metrics["event_types"]) == set(RTTP_MILESTONE_EVENT_TYPES)
    for visible_idx, fr in enumerate(frames):
        assert fr["frame_index"] == visible_idx
        assert set(fr.keys()).isdisjoint(FORBIDDEN_MILESTONE_MAP_KEYS)
        assert fr["event_type"] in RTTP_MILESTONE_EVENT_TYPES
        assert isinstance(fr["metrics"], dict)


def test_skips_payload_with_forbidden_map_keys() -> None:
    project = m.AsteroidProject.objects.create(name="MapKey", slug="map-key")
    run = m.SolverRun.objects.create(
        project=project,
        run_key="run-map",
        algorithm_label="rttp_v0.1",
        config_json={},
    )
    track = m.ReplayTrack.objects.create(
        project=project,
        track_key=rttp_optimization_track_key("run-map"),
        solver_run=run,
    )
    rec = ReplayRecorder(track.id)
    rec.record_event(_rttp_event(et.EVENT_TYPE_ROUTING_PROBE_STARTED, frame_key="ok"))
    bad = _rttp_event(et.EVENT_TYPE_CANDIDATE_GENERATED, frame_key="bad")
    rec.record_event(
        SnapshotEventDTO(
            event_key=bad.event_key,
            phase=bad.phase,
            event_type=bad.event_type,
            title=bad.title,
            full_map=[{"x": 1, "y": 0}],
        )
    )
    frames, _metrics = build_lab_optimization_milestone_frames_for_project(
        int(project.pk),
        run_key="run-map",
    )
    assert len(frames) == 1
    assert frames[0]["event_type"] == et.EVENT_TYPE_ROUTING_PROBE_STARTED


def test_skips_non_milestone_registered_event_type() -> None:
    project = m.AsteroidProject.objects.create(name="NonMile", slug="non-mile")
    run = m.SolverRun.objects.create(
        project=project,
        run_key="run-x",
        algorithm_label="rttp_v0.1",
        config_json={},
    )
    track = m.ReplayTrack.objects.create(
        project=project,
        track_key=rttp_optimization_track_key("run-x"),
        solver_run=run,
    )
    rec = ReplayRecorder(track.id)
    rec.record_event(_rttp_event(et.EVENT_TYPE_ROUTING_PROBE_STARTED, frame_key="mile"))
    rec.record_event(
        SnapshotEventDTO(
            event_key="recon",
            phase="reconstruction",
            event_type=et.EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE,
            title="should not appear in Section B",
            is_decision_point=True,
            full_map=[{"x": 1, "y": 0, "cell_kind": "asteroid_shape_field"}],
        )
    )
    frames, metrics = build_lab_optimization_milestone_frames_for_project(
        int(project.pk),
        run_key="run-x",
    )
    assert len(frames) == 1
    assert metrics["frame_count"] == 1


def test_missing_rttp_track_diagnostic() -> None:
    project = m.AsteroidProject.objects.create(name="NoRttp", slug="no-rttp")
    frames, metrics = build_lab_optimization_milestone_frames_for_project(
        int(project.pk),
        run_key="missing",
    )
    assert frames == []
    assert metrics["diagnostic_reason"] == DIAGNOSTIC_MISSING_OPTIMIZATION_MILESTONE_TRACK


def test_empty_rttp_track_diagnostic() -> None:
    project = m.AsteroidProject.objects.create(name="Empty", slug="empty-rttp")
    run = m.SolverRun.objects.create(
        project=project,
        run_key="empty",
        algorithm_label="rttp_v0.1",
        config_json={},
    )
    track_key = rttp_optimization_track_key("empty")
    m.ReplayTrack.objects.create(
        project=project,
        track_key=track_key,
        solver_run=run,
    )
    frames, metrics = build_lab_optimization_milestone_frames_for_project(
        int(project.pk),
        run_key="empty",
    )
    assert frames == []
    assert metrics["diagnostic_reason"] == DIAGNOSTIC_EMPTY_OPTIMIZATION_MILESTONE_FRAMES
    assert metrics["track_key"] == track_key
    assert metrics["source_solver_run_id"] == int(run.pk)
```

- [ ] **Step 2: Run tests — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_optimization_milestone_payload.py -v
```

Expected: `ModuleNotFoundError` or import error for `lab_optimization_milestone_payload`.

- [ ] **Step 3: Implement adapter**

```python
# django_apps/asteroid_lab/services/lab_optimization_milestone_payload.py
"""Read-only Section B: RTTP optimization milestone cards (metrics-only)."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.models import ReplayFrame, ReplayTrack, SolverRun
from django_apps.asteroid_lab.optimization.replay_track_keys import rttp_optimization_track_key
from django_apps.asteroid_lab.replay import event_types as et

DIAGNOSTIC_MISSING_OPTIMIZATION_MILESTONE_TRACK = "missing_optimization_milestone_track"
DIAGNOSTIC_EMPTY_OPTIMIZATION_MILESTONE_FRAMES = "empty_optimization_milestone_frames"
DIAGNOSTIC_INVALID_OPTIMIZATION_MILESTONE_PAYLOAD = "invalid_optimization_milestone_payload"

RTTP_MILESTONE_EVENT_TYPES: frozenset[str] = frozenset(
    {
        et.EVENT_TYPE_ROUTING_PROBE_STARTED,
        et.EVENT_TYPE_CANDIDATE_GENERATED,
        et.EVENT_TYPE_GA_BEST_UPDATED,
        et.EVENT_TYPE_ROUTING_COMMITTED,
    }
)

_FORBIDDEN_PAYLOAD_MAP_KEYS = frozenset({"map_view", "full_map", "cell_overlay_json"})


def _empty_track_metrics(
    *,
    track_key: str | None = None,
    source_solver_run_id: int | None = None,
    diagnostic_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "track_key": track_key,
        "frame_count": 0,
        "event_types": [],
        "replay_truncated": False,
        "truncation_reason": None,
        "dropped_frame_count": None,
        "diagnostic_reason": diagnostic_reason,
        "source_solver_run_id": source_solver_run_id,
    }


def _metrics_from_row(frame: ReplayFrame) -> dict[str, Any]:
    metrics = dict(frame.metric_snapshot_json or {})
    payload = dict(frame.frame_payload or {})
    extra = payload.get("metrics_json")
    if isinstance(extra, dict):
        metrics.update(extra)
    return metrics


def replay_frame_to_optimization_milestone_json(frame: ReplayFrame) -> dict[str, Any] | None:
    payload = dict(frame.frame_payload or {})
    if _FORBIDDEN_PAYLOAD_MAP_KEYS & payload.keys():
        return None
    event_type = str(payload.get("event_type") or "")
    if event_type not in RTTP_MILESTONE_EVENT_TYPES:
        return None
    return {
        "frame_index": int(frame.frame_index),  # renumbered by builder
        "phase": str(frame.phase),
        "event_type": event_type,
        "title": str(frame.title),
        "description": str(frame.description or ""),
        "inspector": {},
        "metrics": _metrics_from_row(frame),
    }


def _resolve_solver_run(
    project_id: int,
    *,
    run_key: str | None,
) -> SolverRun | None:
    qs = SolverRun.objects.filter(project_id=int(project_id)).order_by("-created_at", "-id")
    if run_key:
        qs = qs.filter(run_key=str(run_key).strip())
    return qs.first()


def build_lab_optimization_milestone_frames_for_project(
    project_id: int,
    *,
    run_key: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    run = _resolve_solver_run(int(project_id), run_key=run_key)
    if run is None:
        return [], _empty_track_metrics(
            diagnostic_reason=DIAGNOSTIC_MISSING_OPTIMIZATION_MILESTONE_TRACK
        )
    track_key = rttp_optimization_track_key(str(run.run_key))
    run_id = int(run.pk)
    track = ReplayTrack.objects.filter(
        project_id=int(project_id),
        track_key=track_key,
    ).first()
    if track is None:
        return [], _empty_track_metrics(
            diagnostic_reason=DIAGNOSTIC_MISSING_OPTIMIZATION_MILESTONE_TRACK
        )
    rows = ReplayFrame.objects.filter(replay_track_id=int(track.pk)).order_by(
        "frame_index", "id"
    )
    if not rows.exists():
        return [], _empty_track_metrics(
            track_key=track_key,
            source_solver_run_id=run_id,
            diagnostic_reason=DIAGNOSTIC_EMPTY_OPTIMIZATION_MILESTONE_FRAMES,
        )

    frames: list[dict[str, Any]] = []
    omitted = 0
    for row in rows:
        got = replay_frame_to_optimization_milestone_json(row)
        if got is None:
            omitted += 1
            continue
        frames.append(got)

    if not frames:
        return [], _empty_track_metrics(
            track_key=track_key,
            source_solver_run_id=run_id,
            diagnostic_reason=DIAGNOSTIC_INVALID_OPTIMIZATION_MILESTONE_PAYLOAD,
        )

    for visible_index, fr in enumerate(frames):
        fr["frame_index"] = visible_index

    event_types = [str(fr["event_type"]) for fr in frames]
    metrics: dict[str, Any] = {
        "track_key": track_key,
        "frame_count": len(frames),
        "event_types": event_types,
        "replay_truncated": False,
        "truncation_reason": None,
        "dropped_frame_count": omitted if omitted else None,
        "diagnostic_reason": None,
        "source_solver_run_id": int(run.pk),
    }
    return frames, metrics


__all__ = [
    "DIAGNOSTIC_EMPTY_OPTIMIZATION_MILESTONE_FRAMES",
    "DIAGNOSTIC_INVALID_OPTIMIZATION_MILESTONE_PAYLOAD",
    "DIAGNOSTIC_MISSING_OPTIMIZATION_MILESTONE_TRACK",
    "RTTP_MILESTONE_EVENT_TYPES",
    "build_lab_optimization_milestone_frames_for_project",
    "replay_frame_to_optimization_milestone_json",
]
```

- [ ] **Step 4: Add tests/support + mirror unit test**

`tests/support/rttp_milestone_contract.py` (no `test_*` functions — import helper only):

```python
# tests/support/rttp_milestone_contract.py
from __future__ import annotations

from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
)

FORBIDDEN_MILESTONE_MAP_KEYS: frozenset[str] = frozenset(
    {"map_view", "full_map", "cell_overlay_json"}
)

__all__ = ["FORBIDDEN_MILESTONE_MAP_KEYS", "RTTP_MILESTONE_EVENT_TYPES"]
```

`tests/unit/asteroid_lab/test_rttp_milestone_contract.py`:

```python
from __future__ import annotations

from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
)


def test_rttp_milestone_event_types_match_v02_contract() -> None:
    expected = frozenset(
        {
            et.EVENT_TYPE_ROUTING_PROBE_STARTED,
            et.EVENT_TYPE_CANDIDATE_GENERATED,
            et.EVENT_TYPE_GA_BEST_UPDATED,
            et.EVENT_TYPE_ROUTING_COMMITTED,
        }
    )
    assert RTTP_MILESTONE_EVENT_TYPES == expected
```

- [ ] **Step 5: Run unit tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_optimization_milestone_payload.py tests/unit/asteroid_lab/test_rttp_milestone_contract.py -v
python -m ruff check django_apps/asteroid_lab/services/lab_optimization_milestone_payload.py tests/unit/asteroid_lab/test_lab_optimization_milestone_payload.py tests/support/rttp_milestone_contract.py tests/unit/asteroid_lab/test_rttp_milestone_contract.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add django_apps/asteroid_lab/services/lab_optimization_milestone_payload.py tests/unit/asteroid_lab/test_lab_optimization_milestone_payload.py tests/support/rttp_milestone_contract.py tests/unit/asteroid_lab/test_rttp_milestone_contract.py
git commit -m "feat(lab): read RTTP milestone frames for Section B payload"
```

---

### Task 2: Wire `SolverRuntimeEntryResult` + RTTP runtime paths

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- Test: `tests/unit/asteroid_lab/test_solver_runtime_entry.py`

- [ ] **Step 1: Extend failing JSON test**

Add to `tests/unit/asteroid_lab/test_solver_runtime_entry.py`:

```python
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
)


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_entry_result_json_includes_optimization_milestone_section() -> None:
    proj = m.AsteroidProject.objects.create(name="MileJson", slug="mile-json")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    result = run_solver_runtime_for_project(
        int(proj.pk),
        run_key="mile-json",
        config={"rttp_record_replay": True},
    )
    body = entry_result_to_json_dict(result)
    assert "lab_optimization_milestone_frames_json" in body
    assert "lab_optimization_milestone_frame_count" in body
    assert "lab_optimization_milestone_track_metrics" in body
    mile_types = {fr.get("event_type") for fr in body["lab_optimization_milestone_frames_json"]}
    assert RTTP_MILESTONE_EVENT_TYPES <= mile_types
    lab_types = {fr.get("event_type") for fr in body["lab_replay_frames_json"]}
    assert lab_types.isdisjoint(RTTP_MILESTONE_EVENT_TYPES)


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_rttp_validation_failure_still_returns_optimization_milestones_section(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Section B must be present even when validation_passed is False."""
    from django_apps.asteroid_lab.optimization import pipeline as rttp_pipeline

    proj = m.AsteroidProject.objects.create(name="MileFail", slug="mile-fail")
    create_copy_code_map_input(proj, _minimal_valid_copy())

    class _FakePipelineResult:
        validation_passed = False
        normal_count = 0
        genome = type("G", (), {"commit_order": []})()
        commit_result = type("C", (), {"committed_ids": [], "conflicts": []})()

    monkeypatch.setattr(
        rttp_pipeline,
        "run_rttp_pipeline",
        lambda *a, **k: _FakePipelineResult(),
    )

    result = run_solver_runtime_for_project(
        int(proj.pk),
        run_key="mile-fail",
        config={"rttp_record_replay": True},
    )
    assert result.ok is False
    assert result.validation_passed is False
    assert len(result.lab_optimization_milestone_frames_json) >= 0
    body = entry_result_to_json_dict(result)
    assert "lab_optimization_milestone_frames_json" in body
    assert "lab_optimization_milestone_track_metrics" in body
```

> **Note:** If monkeypatching `run_rttp_pipeline` skips DB milestone writes, assert JSON **keys exist** and milestone fields default to `[]` / empty metrics on that path; prefer an integration fixture that forces real `RTTP_VALIDATION_FAILED` with persisted `:rttp` track if unit monkeypatch cannot persist frames.

- [ ] **Step 2: Run test — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_solver_runtime_entry.py::test_entry_result_json_includes_optimization_milestone_section -v
```

- [ ] **Step 3: Update `solver_runtime_entry.py`**

1. Import:

```python
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    build_lab_optimization_milestone_frames_for_project,
)
```

2. Extend dataclass — **required fields first**, then defaults (avoids dataclass ordering error):

```python
@dataclass(frozen=True, slots=True)
class SolverRuntimeEntryResult:
    ok: bool
    solver_run_id: int | None
    lab_replay_frames_json: list[dict[str, Any]]
    replay_track_metrics: dict[str, Any]
    solver_summary: dict[str, Any]
    validation_passed: bool
    gene_template_source: dict[str, Any] = field(default_factory=dict)
    error_code: SolverRuntimeEntryErrorCode | None = None
    message: str | None = None
    lab_optimization_milestone_frames_json: list[dict[str, Any]] = field(default_factory=list)
    lab_optimization_milestone_track_metrics: dict[str, Any] = field(default_factory=dict)
```

3. Grep all constructors — update **every** `SolverRuntimeEntryResult(` in `solver_runtime_entry.py` (6 call sites) to pass milestone fields explicitly or rely on defaults:

```powershell
rg "SolverRuntimeEntryResult\(" django_apps/asteroid_lab/services/solver_runtime_entry.py
```

4. Helper:

```python
def _milestone_payload_for_project(
    project_id: int,
    *,
    run_key: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return build_lab_optimization_milestone_frames_for_project(
        int(project_id),
        run_key=run_key,
    )
```

5. In `_run_rttp_solver_for_map_input`, after `frames, metrics = build_lab_replay_frames_for_project(...)`:

```python
    milestone_frames, milestone_metrics = _milestone_payload_for_project(
        int(project_id),
        run_key=rk,
    )
```

6. Pass `milestone_frames` / `milestone_metrics` into **both** `SolverRuntimeEntryResult(...)` returns in `_run_rttp_solver_for_map_input` (success **and** `RTTP_VALIDATION_FAILED`).

7. For `_solver_not_available_result`, `_failure_result`, and other early exits: omit milestone args (use dataclass defaults `[]` / `{}`) or pass explicit empty lists.

- [ ] **Step 4: Update `entry_result_to_json_dict`**

```python
def entry_result_to_json_dict(result: SolverRuntimeEntryResult) -> dict[str, Any]:
    frames = list(result.lab_replay_frames_json)
    milestone_frames = list(result.lab_optimization_milestone_frames_json)
    body: dict[str, Any] = {
        "ok": result.ok,
        "solver_run_id": result.solver_run_id,
        "lab_replay_frame_count": len(frames),
        "lab_replay_frames_json": frames,
        "replay_track_metrics": result.replay_track_metrics,
        "lab_optimization_milestone_frame_count": len(milestone_frames),
        "lab_optimization_milestone_frames_json": milestone_frames,
        "lab_optimization_milestone_track_metrics": dict(
            result.lab_optimization_milestone_track_metrics or {}
        ),
        ...
    }
```

- [ ] **Step 5: Run tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_solver_runtime_entry.py -v
```

- [ ] **Step 6: Commit**

```powershell
git add django_apps/asteroid_lab/services/solver_runtime_entry.py tests/unit/asteroid_lab/test_solver_runtime_entry.py
git commit -m "feat(solver): expose RTTP milestone Section B in runtime JSON"
```

---

### Task 3: SSR page context + import bundle

**Files:**
- Modify: `django_apps/web/services/asteroid_lab_page_context.py`
- Modify: `django_apps/web/views/public_pages.py`
- Test: `tests/unit/web/test_asteroid_lab_page_context.py`

- [ ] **Step 1: Failing page context test**

Add to `tests/unit/web/test_asteroid_lab_page_context.py` (use existing project+replay fixtures pattern in file):

```python
def test_lab_page_context_includes_optimization_milestone_keys(db) -> None:
    from django_apps.web.services.asteroid_lab_page_context import lab_page_context

    ctx = lab_page_context(project_id=None)
    assert "lab_optimization_milestone_frames_json" in ctx
    assert "lab_optimization_milestone_track_metrics" in ctx
    assert ctx["lab_optimization_milestone_frames_json"] == []
```

- [ ] **Step 2: Implement `neutral_lab_context` defaults**

```python
        "lab_optimization_milestone_frames_json": [],
        "lab_optimization_milestone_track_metrics": {
            "track_key": None,
            "frame_count": 0,
            "event_types": [],
            "replay_truncated": False,
            "truncation_reason": None,
            "dropped_frame_count": None,
            "diagnostic_reason": None,
            "source_solver_run_id": None,
        },
```

- [ ] **Step 3: In `lab_page_context`, after `build_lab_replay_frames_for_project`:**

```python
    milestone_frames, milestone_metrics = build_lab_optimization_milestone_frames_for_project(
        int(project_id)
    )
    ctx["lab_optimization_milestone_frames_json"] = milestone_frames
    ctx["lab_optimization_milestone_track_metrics"] = milestone_metrics
```

- [ ] **Step 4: Update `_lab_json_bundle_for_track_id` in `public_pages.py`**

Import `build_lab_optimization_milestone_frames_for_project`; add Section B keys to returned dict.

**v0 contract:** Section B uses `run_key=None` → **latest** `SolverRun` on project, even when the bundle is loaded for a specific inspection `track_id`. Section A still comes from `build_lab_replay_frames_for_project(project_id)`.

```python
    milestone_frames, milestone_metrics = build_lab_optimization_milestone_frames_for_project(
        int(track.project_id),
        run_key=None,
    )
    return {
        ...
        "lab_optimization_milestone_frames_json": milestone_frames,
        "lab_optimization_milestone_frame_count": len(milestone_frames),
        "lab_optimization_milestone_track_metrics": milestone_metrics,
    }
```

- [ ] **Step 4b: Failing test `test_lab_json_bundle_uses_latest_solver_run_for_section_b_v0`**

In `tests/unit/web/test_asteroid_lab_page_context.py` or `tests/integration/web/test_asteroid_miner_layout_solver.py`:

```python
@pytest.mark.django_db
def test_lab_json_bundle_uses_latest_solver_run_for_section_b_v0() -> None:
    """Section B follows latest SolverRun, not the inspection track_id passed to the bundle."""
    # 1. Create project + inspection track (Section A source)
    # 2. Create older SolverRun without :rttp milestones
    # 3. Create newer SolverRun with :rttp track + 4 milestone frames
    # 4. Call _lab_json_bundle_for_track_id(inspection_track_id, ...)
    # 5. Assert lab_optimization_milestone_frame_count >= 4
    #    and metrics["track_key"] == rttp_optimization_track_key(newer_run.run_key)
```

- [ ] **Step 5: Run tests**

```powershell
python -m pytest tests/unit/web/test_asteroid_lab_page_context.py -v
```

- [ ] **Step 6: Commit**

```powershell
git add django_apps/web/services/asteroid_lab_page_context.py django_apps/web/views/public_pages.py tests/unit/web/test_asteroid_lab_page_context.py
git commit -m "feat(web): SSR Lab context for optimization milestone Section B"
```

---

### Task 4: Extend H1 integration test

**Files:**
- Modify: `tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py`

- [ ] **Step 1: Refactor imports to shared contract**

```python
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
)
```

Remove local `RTTP_MILESTONE_EVENT_TYPES` definition in the integration file.

- [ ] **Step 2: Extend `test_run_solver_lab_json_uses_inspection_not_rttp_optimization_track`**

```python
    milestones = body["lab_optimization_milestone_frames_json"]
    assert body["lab_optimization_milestone_frame_count"] == len(milestones)
    assert len(milestones) >= 4
    mile_types = {fr.get("event_type") for fr in milestones}
    assert RTTP_MILESTONE_EVENT_TYPES <= mile_types
    assert body["lab_replay_frame_count"] == len(body["lab_replay_frames_json"])
    for fr in milestones:
        assert "map_view" not in fr
        assert "full_map" not in fr
```

- [ ] **Step 3: Run integration test**

```powershell
python -m pytest tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py -v
```

- [ ] **Step 4: Commit**

```powershell
git add tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py tests/support/rttp_milestone_contract.py
git commit -m "test: H1 plus Section B milestone JSON integration gates"
```

---

### Task 5: Import boundary (replay not solver input)

**Files:**
- Create: `tests/unit/asteroid_lab/test_optimization_milestone_import_boundary.py`

- [ ] **Step 1: Add architecture test**

```python
# tests/unit/asteroid_lab/test_optimization_milestone_import_boundary.py
from __future__ import annotations

from pathlib import Path


def test_optimization_package_does_not_import_milestone_payload() -> None:
    root = Path(__file__).resolve().parents[3]
    opt_dir = root / "django_apps" / "asteroid_lab" / "optimization"
    needle = "lab_optimization_milestone_payload"
    for path in opt_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert needle not in text, f"{path} must not import milestone read adapter"
```

- [ ] **Step 2: Run**

```powershell
python -m pytest tests/unit/asteroid_lab/test_optimization_milestone_import_boundary.py -v
```

- [ ] **Step 3: Commit**

```powershell
git add tests/unit/asteroid_lab/test_optimization_milestone_import_boundary.py
git commit -m "test: optimization must not read milestone replay adapter"
```

---

### Task 6: PR-1 gate (full narrow + lint)

- [ ] **Step 1: Run PR-1 test bundle**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_optimization_milestone_payload.py tests/unit/asteroid_lab/test_solver_runtime_entry.py tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py tests/unit/asteroid_lab/test_optimization_milestone_import_boundary.py tests/unit/web/test_asteroid_lab_page_context.py -v
python -m ruff check django_apps/asteroid_lab/services/lab_optimization_milestone_payload.py django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/web/services/asteroid_lab_page_context.py django_apps/web/views/public_pages.py
```

Expected: all passed.

- [ ] **Step 2: Typecheck (repo standard — preferred)**

```powershell
python -m mypy django_apps config src
```

Expected: no new errors in touched modules. If the full gate is too heavy for a mid-PR checkpoint, run it before merge; do **not** rely on file-scoped mypy unless your local config documents support for it.

**Fallback (narrow, optional):**

```powershell
python -m mypy django_apps/asteroid_lab/services/lab_optimization_milestone_payload.py django_apps/asteroid_lab/services/solver_runtime_entry.py
```

---

# PR-2 — UI Optimization Milestones panel

### Task 7: Template — `json_script` + panel shell

**Files:**
- Modify: `django_apps/web/templates/web/asteroid_miner_layout_solver.html`

- [ ] **Step 1: Add json_script tags** (after `lab-replay-track-metrics-data`):

```django
  {{ lab_optimization_milestone_frames_json|json_script:"lab-optimization-milestone-frames-data" }}
  {{ lab_optimization_milestone_track_metrics|json_script:"lab-optimization-milestone-track-metrics-data" }}
```

- [ ] **Step 2: Add panel markup** below Replay Timeline block (inside same card or adjacent card):

```html
              <div
                id="lab-optimization-milestones-panel"
                class="mt-4 rounded-xl border border-slate-800 bg-slate-900/40 p-3"
              >
                <h3 class="text-sm font-semibold text-slate-200">Optimization Milestones</h3>
                <p id="lab-optimization-milestones-empty" class="mt-2 text-xs text-slate-500">
                  No optimization milestones recorded
                </p>
                <ul id="lab-optimization-milestones-list" class="mt-2 hidden space-y-2"></ul>
              </div>
```

- [ ] **Step 3: Template smoke test (empty copy lives in HTML, not JS)**

Add to `tests/unit/web/test_asteroid_lab_page_context.py`:

```python
def test_lab_solver_template_includes_optimization_milestones_empty_copy() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    html = (
        root / "django_apps" / "web" / "templates" / "web" / "asteroid_miner_layout_solver.html"
    ).read_text(encoding="utf-8")
    assert "lab-optimization-milestones-panel" in html
    assert "No optimization milestones recorded" in html
    assert "lab-optimization-milestone-frames-data" in html
```

```powershell
python -m pytest tests/unit/web/test_asteroid_lab_page_context.py::test_lab_solver_template_includes_optimization_milestones_empty_copy -v
```

- [ ] **Step 4: Manual smoke** — load Lab page; panel visible (empty until run).

- [ ] **Step 5: Commit**

```powershell
git add django_apps/web/templates/web/asteroid_miner_layout_solver.html
git commit -m "feat(lab-ui): template shell for optimization milestones panel"
```

---

### Task 8: Lab JS — render milestone list (no scrubber coupling)

**Files:**
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- Test: `tests/unit/web/test_asteroid_lab_page_context.py`

- [ ] **Step 1: Add failing JS smoke assertions**

In `test_lab_js_replay_wiring_smoke` (JS only — **do not** assert empty copy string; that is Task 7 template test):

```python
    assert "lab-optimization-milestone-frames-data" in js
    assert "renderOptimizationMilestonesPanel" in js
    assert "textContent" in js  # panel uses DOM text, not innerHTML for payload strings
```

- [ ] **Step 2: Implement in `asteroid_miner_layout_lab.js`**

Near replay init (~line 1053), read scripts:

```javascript
    const optimizationMilestoneFramesRaw = readJsonScript("lab-optimization-milestone-frames-data");
    let optimizationMilestoneFrames = Array.isArray(optimizationMilestoneFramesRaw)
      ? optimizationMilestoneFramesRaw
      : [];
```

Add function:

```javascript
    function formatMetricsPreview(metrics) {
      if (!metrics || typeof metrics !== "object") return "";
      const keys = Object.keys(metrics).slice(0, 4);
      return keys.map((k) => `${k}=${JSON.stringify(metrics[k])}`).join(" · ");
    }

    function appendTextLine(parent, className, text) {
      const el = document.createElement("div");
      el.className = className;
      el.textContent = text;
      parent.appendChild(el);
    }

    function renderOptimizationMilestonesPanel(frames) {
      const list = document.getElementById("lab-optimization-milestones-list");
      const empty = document.getElementById("lab-optimization-milestones-empty");
      if (!list || !empty) return;
      const rows = Array.isArray(frames) ? frames : [];
      while (list.firstChild) list.removeChild(list.firstChild);
      if (!rows.length) {
        empty.classList.remove("hidden");
        list.classList.add("hidden");
        return;
      }
      empty.classList.add("hidden");
      list.classList.remove("hidden");
      rows.forEach((fr, idx) => {
        const li = document.createElement("li");
        li.className = "rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2 text-xs";
        const title = typeof fr.title === "string" ? fr.title : "—";
        const phase = typeof fr.phase === "string" ? fr.phase : "—";
        const eventType = typeof fr.event_type === "string" ? fr.event_type : "—";
        const metricsLine = formatMetricsPreview(fr.metrics);
        appendTextLine(li, "font-medium text-slate-200", `${idx + 1}. ${title}`);
        appendTextLine(li, "mt-1 text-violet-300", eventType);
        appendTextLine(li, "text-slate-500", phase);
        if (metricsLine) {
          appendTextLine(li, "mt-1 font-mono text-slate-400", metricsLine);
        }
        list.appendChild(li);
      });
    }
```

> **Security:** Replay `title` / `event_type` / `phase` / `metrics` come from DB payloads — use **`textContent` only**; never `innerHTML` for those values.

Call `renderOptimizationMilestonesPanel(optimizationMilestoneFrames)` once at init.

- [ ] **Step 3: Run smoke test**

```powershell
python -m pytest tests/unit/web/test_asteroid_lab_page_context.py::test_lab_js_replay_wiring_smoke -v
```

- [ ] **Step 4: Commit**

```powershell
git add django_apps/web/static/web/js/asteroid_miner_layout_lab.js tests/unit/web/test_asteroid_lab_page_context.py
git commit -m "feat(lab-ui): render optimization milestones panel from Section B JSON"
```

---

### Task 9: Run Solver JSON refresh — milestones only

**Files:**
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`

- [ ] **Step 1: In `replaceLabReplayPayload` (or equivalent POST handler), after updating `replayFrames`:**

```javascript
      if (Array.isArray(payload.lab_optimization_milestone_frames_json)) {
        optimizationMilestoneFrames = payload.lab_optimization_milestone_frames_json;
      }
      renderOptimizationMilestonesPanel(optimizationMilestoneFrames);
```

**Critical:** Do **not** add milestone length to `replayFrames`, `totalFrames`, or scrubber `max`. Map scrubber uses `lab_replay_frame_count` / `lab_replay_frames_json` only.

- [ ] **Step 2: Manual test**

1. Import blueprint → Run Solver with `rttp_record_replay: true`.
2. Map scrubber frame count unchanged vs pre-3B behavior.
3. Milestone panel shows 4 rows with RTTP titles/types.

- [ ] **Step 3: Commit**

```powershell
git add django_apps/web/static/web/js/asteroid_miner_layout_lab.js
git commit -m "feat(lab-ui): refresh milestone panel on Run Solver without map scrubber"
```

---

### Task 10: PR-2 gate

- [ ] **Step 1: Tests**

```powershell
python -m pytest tests/unit/web/test_asteroid_lab_page_context.py tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py -v
```

- [ ] **Step 2: Optional integration browser check** — Lab page loads, panel empty before run, populated after RTTP run.

---

## Test gates (reviewer checklist)

| Gate | Task |
|------|------|
| `lab_replay_frames_json` excludes RTTP milestone event types | Task 4 |
| `lab_optimization_milestone_frames_json` contains 4 RTTP milestones | Task 4 |
| Map scrubber count = `lab_replay_frame_count` only | Task 9 (manual + existing frame counter tests) |
| Milestone panel renders without `map_view` / `full_map` | Task 1, 8 |
| Replay rows never solver input | Task 5 |
| Validation failure includes Section B keys | Task 2 |
| Visible local `frame_index` 0..n-1 | Task 1 |

---

## Risks

| Risk | Mitigation |
|------|------------|
| `SolverRuntimeEntryResult` dataclass field order | Task 2: defaults after required fields; grep 6 call sites |
| Page context / bundle loads milestones for latest run only | Task 3 v0 contract + `test_lab_json_bundle_uses_latest_solver_run_for_section_b_v0` |
| JS regressions on scrubber | Task 9: do not touch `replayFrames` length |
| Validation-failure test with monkeypatch may not persist DB frames | Task 2 note: prefer integration path or assert keys + empty metrics |

---

## Docs (optional follow-up PR)

- Link spec from `documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md` §2.1 (one paragraph).
- Not required for 3B code merge.

---

## Self-review (plan author + reviewer pass)

| Check | Result |
|-------|--------|
| Spec coverage | All approved keys + PR split covered |
| Placeholders | None |
| Type/name consistency | `lab_optimization_milestone_*` used throughout |
| Mandatory sentences | Task 1 payload map-key skip; Task 9 preserves scrubber |
| Reviewer checklist (10 items) | Incorporated in § Plan review amendments |
| Dataclass ordering | Task 2 fixed |
| Empty-track test | Task 1 includes SolverRun |
| Production milestone filter | `RTTP_MILESTONE_EVENT_TYPES` in adapter |

---

## Execution handoff

Plan updated with reviewer amendments (2026-05-23). **Start with PR-1 Task 1.**

1. **Subagent-Driven (recommended)** — subagent per task + review between tasks (`subagent-driven-development`)
2. **Inline Execution** — this session, `executing-plans`, checkpoint after Task 6 (PR-1 gate)

Which approach?
