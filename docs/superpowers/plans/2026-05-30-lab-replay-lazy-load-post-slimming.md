# Lab Replay Lazy-load & POST Slimming — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Slim Run Solver POST JSON by omitting inline `lab_replay_frames_json`, return a preview + lazy fetch handle, and serve full run-scoped replay via GET.

**Architecture:** Extend `build_lab_replay_frames_for_project(project_id, solver_run_id=...)` for run-scoped selection (A-1). POST still composes frames internally but omits the array when `ASTEROID_LAB_REPLAY_PAYLOAD_MODE=lazy`. GET reuses the same builder. Frontend `replaceLabReplayPayload` gains lazy mode; full fetch deferred until timeline interaction.

**Tech Stack:** Django 5.x, pytest-django, vanilla JS (`asteroid_miner_layout_lab.js`), ruff, black, mypy `django_apps config src`

**Spec:** [`docs/superpowers/specs/2026-05-30-lab-replay-lazy-load-post-slimming-design.md`](../specs/2026-05-30-lab-replay-lazy-load-post-slimming-design.md)

**Branch:** `feat/lab-replay-lazy-load-post-slimming` (worktree recommended)

**Out of scope:** SSR `json_script` slimming (13D-SSR), frontend decode, delta/interning, solver algorithm changes

**Plan status:** APPROVED (2026-05-30). Mandatory: run-scoped builder (not auth-only `run_id`); terminology sync in `asteroid_lab_13`.

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `documents/Algorithm/asteroid_lab_13_replay_payload_scalability.md` | Terminology + 13C approval (Task 1) |
| Modify | `documents/ai/current_plan.md` | ACTIVE queue entry (Task 1) |
| Modify | `documents/ai/manuals/environment.md` | Register `ASTEROID_LAB_REPLAY_PAYLOAD_MODE` (Task 5) |
| Modify | `config/settings.py` | Setting default `lazy` |
| Modify | `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py` | Run-scoped builder |
| Create | `django_apps/asteroid_lab/services/lab_replay_lazy_handle.py` | DTO + handle builder |
| Modify | `django_apps/asteroid_lab/services/solver_runtime_entry.py` | Pass `solver_run_id`; slim dict helper |
| Modify | `django_apps/web/urls.py` | GET lab-replay route |
| Modify | `django_apps/web/views/public_pages.py` | GET view + lazy POST wiring |
| Modify | `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | Lazy-load controller |
| Create | `tests/unit/asteroid_lab/test_lab_replay_run_scoped_builder.py` | Run-scoped compose unit tests |
| Create | `tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py` | DTO / handle builder tests |
| Modify | `tests/integration/web/test_asteroid_miner_layout_solver.py` | POST lazy + size attribution |
| Create | `tests/integration/web/test_lab_replay_lazy_load_endpoint.py` | GET endpoint + equivalence |

---

### Task 0: Branch and baseline

**Files:** none

- [ ] **Step 1: Create branch**

```powershell
git checkout master
git pull
git checkout -b feat/lab-replay-lazy-load-post-slimming
```

- [ ] **Step 2: Baseline narrow tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_replay_timeline_payload.py tests/integration/web/test_asteroid_miner_layout_solver.py -v --tb=short
```

Expected: PASS (existing replay + Run Solver integration before edits).

---

### Task 1: Docs queue entry (PR-13C-1)

**Files:**
- Modify: `documents/ai/current_plan.md`
- Verify: `docs/superpowers/specs/2026-05-30-lab-replay-lazy-load-post-slimming-design.md` (already approved)
- Verify: `documents/Algorithm/asteroid_lab_13_replay_payload_scalability.md` (terminology synced)

- [ ] **Step 1: Add ACTIVE row to `current_plan.md` under Next focus**

Insert after the first `**NEXT:**` block:

```markdown
**ACTIVE — Sequence 13C — Lab replay lazy-load (POST slimming)** — Run Solver POST omits inline `lab_replay_frames_json`; preview + GET `/p/<slug>/solver-runs/<run_id>/lab-replay/`. SSR slimming deferred (13D-SSR). Spec: [`2026-05-30-lab-replay-lazy-load-post-slimming-design.md`](../../docs/superpowers/specs/2026-05-30-lab-replay-lazy-load-post-slimming-design.md) · plan: [`2026-05-30-lab-replay-lazy-load-post-slimming.md`](../../docs/superpowers/plans/2026-05-30-lab-replay-lazy-load-post-slimming.md). **NEXT: Task 2** run-scoped builder.
```

- [ ] **Step 2: Commit docs-only (optional separate PR-13C-1 or fold into Task 2 commit)**

```powershell
git add documents/ai/current_plan.md docs/superpowers/specs/2026-05-30-lab-replay-lazy-load-post-slimming-design.md documents/Algorithm/asteroid_lab_13_replay_payload_scalability.md docs/superpowers/plans/2026-05-30-lab-replay-lazy-load-post-slimming.md
git commit -m "docs: approve Sequence 13C lab replay lazy-load spec and plan"
```

---

### Task 2: Run-scoped replay builder (TDD)

**Files:**
- Modify: `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py`
- Create: `tests/unit/asteroid_lab/test_lab_replay_run_scoped_builder.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/asteroid_lab/test_lab_replay_run_scoped_builder.py`:

```python
"""Run-scoped product replay timeline (Sequence 13C A-1)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.replay_track_keys import rttp_optimization_track_key
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.dto import SnapshotEventDTO
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    build_lab_replay_frames_for_project,
)
from django_apps.asteroid_lab.services.replay_recorder import ReplayRecorder
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY,
)

pytestmark = pytest.mark.django_db


def _recon_event() -> SnapshotEventDTO:
    return SnapshotEventDTO(
        event_key="recon-complete",
        phase="reconstruction",
        event_type=et.EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE,
        title="Reconstruction complete",
        is_decision_point=True,
        full_map=[{"x": 1, "y": 0, "cell_kind": "asteroid_shape_field"}],
    )


def _runtime_frame_dict(*, frame_index: int, tag: str) -> dict:
    return {
        "frame_index": frame_index,
        "frame_key": f"runtime-{tag}",
        "phase": "solver_runtime",
        "event_type": "solver.runtime.segment",
        "title": f"Runtime {tag}",
        "description": "",
        "map_view": {"full_cells": [], "overlay_cells": [], "cell_delta": []},
        "metrics": {"replay_truncated": False},
        "inspector": {"runtime_tag": tag},
    }


def test_build_lab_replay_frames_for_run_uses_that_runs_config_json_not_latest() -> None:
    project = m.AsteroidProject.objects.create(name="RunScope", slug="run-scope")
    inspection_run = m.SolverRun.objects.create(
        project=project,
        run_key="inspection",
        algorithm_label="inspection_only",
        config_json={},
    )
    inspection_track = m.ReplayTrack.objects.create(
        project=project,
        track_key="inspection",
        solver_run=inspection_run,
    )
    ReplayRecorder(inspection_track.id).record_event(_recon_event())

    older_run = m.SolverRun.objects.create(
        project=project,
        run_key="rttp-old",
        algorithm_label="rttp_v0.1",
        config_json={
            SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY: [
                _runtime_frame_dict(frame_index=10, tag="old"),
            ],
        },
    )
    m.ReplayTrack.objects.create(
        project=project,
        track_key=rttp_optimization_track_key("rttp-old"),
        solver_run=older_run,
    )

    newer_run = m.SolverRun.objects.create(
        project=project,
        run_key="rttp-new",
        algorithm_label="rttp_v0.1",
        config_json={
            SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY: [
                _runtime_frame_dict(frame_index=10, tag="new"),
            ],
        },
    )
    m.ReplayTrack.objects.create(
        project=project,
        track_key=rttp_optimization_track_key("rttp-new"),
        solver_run=newer_run,
    )

    latest_frames, _ = build_lab_replay_frames_for_project(int(project.pk))
    old_frames, _ = build_lab_replay_frames_for_project(
        int(project.pk),
        solver_run_id=int(older_run.pk),
    )
    new_frames, _ = build_lab_replay_frames_for_project(
        int(project.pk),
        solver_run_id=int(newer_run.pk),
    )

    latest_tags = {
        str((fr.get("inspector") or {}).get("runtime_tag"))
        for fr in latest_frames
        if isinstance(fr, dict)
    }
    old_tags = {
        str((fr.get("inspector") or {}).get("runtime_tag"))
        for fr in old_frames
        if isinstance(fr, dict)
    }
    new_tags = {
        str((fr.get("inspector") or {}).get("runtime_tag"))
        for fr in new_frames
        if isinstance(fr, dict)
    }

    assert "new" in latest_tags
    assert "old" in old_tags
    assert "new" not in old_tags
    assert old_frames != new_frames


def test_build_lab_replay_frames_unknown_run_id_returns_empty() -> None:
    project = m.AsteroidProject.objects.create(name="NoRun", slug="no-run")
    frames, metrics = build_lab_replay_frames_for_project(
        int(project.pk),
        solver_run_id=999_999,
    )
    assert frames == []
    assert metrics["frame_count"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_replay_run_scoped_builder.py -v --tb=short
```

Expected: FAIL (`TypeError: build_lab_replay_frames_for_project() got an unexpected keyword argument 'solver_run_id'` or assertion on tags).

- [ ] **Step 3: Implement run-scoped builder**

In `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py`:

1. Add helper:

```python
def _solver_runtime_timeline_frames_for_run(run: SolverRun) -> tuple[ReplayTimelineFrame, ...]:
    config = dict(run.config_json or {})
    raw = config.get(SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY)
    if not isinstance(raw, list) or not raw:
        return ()
    out: list[ReplayTimelineFrame] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            out.append(replay_timeline_frame_from_json_dict(item))
        except Exception:  # noqa: BLE001
            continue
    return tuple(out)
```

2. Refactor existing `_solver_runtime_timeline_frames_for_project` to call latest run then `_solver_runtime_timeline_frames_for_run`.

3. Change signature:

```python
def build_lab_replay_frames_for_project(
    project_id: int,
    *,
    solver_run_id: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pid = int(project_id)
    run: SolverRun | None = None
    if solver_run_id is not None:
        run = SolverRun.objects.filter(pk=int(solver_run_id), project_id=pid).first()
        if run is None:
            return [], _track_metrics_from_serialized_frames([], diagnostic_reason=DIAGNOSTIC_NO_REPLAY_FRAMES)

    lab_frames = _lab_timeline_frames_for_project(pid)
    if run is not None:
        runtime_frames = _solver_runtime_timeline_frames_for_run(run)
        rttp_rows = load_rttp_compose_rows_for_project(pid, run_key=str(run.run_key))
    else:
        runtime_frames = _solver_runtime_timeline_frames_for_project(pid)
        rttp_rows = load_rttp_compose_rows_for_project(pid)

    combined = compose_replay_timeline(
        lab_frames=(*lab_frames, *runtime_frames),
        max_frames=replay_limits.MAX_LAB_REPLAY_TIMELINE_FRAMES,
    )
    serialized = [replay_timeline_frame_to_json_dict(fr) for fr in combined]
    serialized = interleave_rttp_snapshot_frames(serialized, rttp_rows)
    serialized, frozen_rim_wire = enrich_lab_timeline_frames_with_terrain_rim(serialized)
    diagnostic = _lab_replay_diagnostic_reason(pid, composed_count=len(serialized))
    metrics = _track_metrics_from_serialized_frames(serialized, diagnostic_reason=diagnostic)
    if frozen_rim_wire is not None:
        metrics["frozen_terrain_rim_highlight"] = frozen_rim_wire
    return serialized, metrics
```

4. Export `_solver_runtime_timeline_frames_for_run` in `__all__` if tests need it (optional).

- [ ] **Step 4: Run tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_replay_run_scoped_builder.py tests/unit/asteroid_lab/test_lab_replay_timeline_payload.py -v --tb=short
```

Expected: PASS

- [ ] **Step 5: Wire solver runtime entry to run-scoped compose**

In `django_apps/asteroid_lab/services/solver_runtime_entry.py`, replace:

```python
frames, metrics = build_lab_replay_frames_for_project(int(project_id))
```

with:

```python
frames, metrics = build_lab_replay_frames_for_project(
    int(project_id),
    solver_run_id=int(run_id),
)
```

(Apply at every post-persist compose site inside `_run_rttp_solver_for_map_input`.)

- [ ] **Step 6: Commit**

```powershell
git add django_apps/asteroid_lab/services/lab_replay_timeline_payload.py django_apps/asteroid_lab/services/solver_runtime_entry.py tests/unit/asteroid_lab/test_lab_replay_run_scoped_builder.py
git commit -m "feat: add run-scoped lab replay timeline builder for lazy-load"
```

---

### Task 3: LabReplayLazyHandle DTO + settings flag (TDD)

**Files:**
- Create: `django_apps/asteroid_lab/services/lab_replay_lazy_handle.py`
- Modify: `config/settings.py`
- Create: `tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py`:

```python
from __future__ import annotations

from django.test import override_settings

from django_apps.asteroid_lab.services.lab_replay_lazy_handle import (
    LAB_REPLAY_PAYLOAD_VERSION,
    build_lab_replay_lazy_handle,
    lab_replay_payload_mode,
)


def test_lab_replay_payload_mode_defaults_lazy() -> None:
    with override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy"):
        assert lab_replay_payload_mode() == "lazy"


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="inline")
def test_build_handle_inline_mode() -> None:
    handle = build_lab_replay_lazy_handle(
        mode="inline",
        frames=[{"frame_index": 0}, {"frame_index": 1}],
        project_slug="demo",
        solver_run_id=42,
    )
    assert handle.mode == "inline"
    assert handle.frame_count == 2
    assert handle.fetch_url is None


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_build_handle_lazy_preview_is_last_frame() -> None:
    frames = [
        {"frame_index": 0, "title": "first"},
        {"frame_index": 1, "title": "last"},
    ]
    handle = build_lab_replay_lazy_handle(
        mode="lazy",
        frames=frames,
        project_slug="demo-slug",
        solver_run_id=99,
    )
    assert handle.mode == "lazy"
    assert handle.frame_count == 2
    assert handle.preview_frame_index == 1
    assert handle.preview_frame == frames[1]
    assert handle.replay_payload_version == LAB_REPLAY_PAYLOAD_VERSION
    assert handle.fetch_url == "/asteroid-miner-layout/p/demo-slug/solver-runs/99/lab-replay/"
```

- [ ] **Step 2: Run test — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py -v --tb=short
```

- [ ] **Step 3: Implement DTO module**

Create `django_apps/asteroid_lab/services/lab_replay_lazy_handle.py`:

```python
"""Lab replay lazy-load handle DTO (Sequence 13C transport contract)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

from django.conf import settings
from django.urls import reverse

LAB_REPLAY_PAYLOAD_VERSION = 1
LabReplayPayloadMode = Literal["inline", "lazy"]


@dataclass(frozen=True)
class LabReplayLazyHandle:
    mode: LabReplayPayloadMode
    frame_count: int
    preview_frame_index: int
    preview_frame: Mapping[str, Any] | None
    fetch_url: str | None
    replay_payload_version: int


def lab_replay_payload_mode() -> LabReplayPayloadMode:
    raw = str(getattr(settings, "ASTEROID_LAB_REPLAY_PAYLOAD_MODE", "lazy")).strip().lower()
    return "inline" if raw == "inline" else "lazy"


def build_lab_replay_lazy_handle(
    *,
    mode: LabReplayPayloadMode,
    frames: list[dict[str, Any]],
    project_slug: str,
    solver_run_id: int | None,
) -> LabReplayLazyHandle:
    count = len(frames)
    preview_index = max(0, count - 1) if count else 0
    preview = dict(frames[preview_index]) if count else None
    fetch_url: str | None = None
    if mode == "lazy" and solver_run_id is not None and project_slug:
        fetch_url = reverse(
            "web:asteroid-miner-layout-project-solver-run-lab-replay",
            kwargs={"slug": str(project_slug), "run_id": int(solver_run_id)},
        )
    return LabReplayLazyHandle(
        mode=mode,
        frame_count=count,
        preview_frame_index=preview_index,
        preview_frame=preview,
        fetch_url=fetch_url,
        replay_payload_version=LAB_REPLAY_PAYLOAD_VERSION,
    )


__all__ = [
    "LAB_REPLAY_PAYLOAD_VERSION",
    "LabReplayLazyHandle",
    "LabReplayPayloadMode",
    "build_lab_replay_lazy_handle",
    "lab_replay_payload_mode",
]
```

Add to `config/settings.py` near other `ASTEROID_LAB_*` keys:

```python
ASTEROID_LAB_REPLAY_PAYLOAD_MODE = os.environ.get(
    "ASTEROID_LAB_REPLAY_PAYLOAD_MODE",
    "lazy",
).strip().lower()
if ASTEROID_LAB_REPLAY_PAYLOAD_MODE not in ("inline", "lazy"):
    ASTEROID_LAB_REPLAY_PAYLOAD_MODE = "lazy"
```

- [ ] **Step 4: Run tests — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py -v --tb=short
```

- [ ] **Step 5: Commit**

```powershell
git add django_apps/asteroid_lab/services/lab_replay_lazy_handle.py config/settings.py tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py
git commit -m "feat: add LabReplayLazyHandle DTO and payload mode setting"
```

---

### Task 4: POST slim `entry_result_to_json_dict` (TDD)

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- Modify: `tests/integration/web/test_asteroid_miner_layout_solver.py`

- [ ] **Step 1: Write failing integration tests**

Append to `tests/integration/web/test_asteroid_miner_layout_solver.py`:

```python
from django.test import override_settings

from tests.support.measure_json_sections import measure_json_sections


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_post_run_solver_lazy_mode_omits_inline_lab_replay_frames(client: Client) -> None:
    copy_code = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    create_resp = client.post(
        create_url,
        {"copy_code": copy_code, "Accept": "application/json"},
        HTTP_ACCEPT="application/json",
    )
    data = json.loads(create_resp.content.decode())
    slug = data["project_slug"]
    run_url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
    run_resp = client.post(run_url, HTTP_ACCEPT="application/json")
    body = json.loads(run_resp.content.decode())
    assert body.get("ok") is True
    assert "lab_replay_frames_json" not in body
    lab_replay = body.get("lab_replay") or {}
    assert lab_replay.get("mode") == "lazy"
    assert lab_replay.get("frame_count", 0) >= 1
    assert lab_replay.get("preview_frame") is not None
    assert lab_replay.get("fetch_url")


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="inline")
def test_post_run_solver_inline_mode_still_includes_lab_replay_frames(client: Client) -> None:
    copy_code = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    create_resp = client.post(
        create_url,
        {"copy_code": copy_code},
        HTTP_ACCEPT="application/json",
    )
    data = json.loads(create_resp.content.decode())
    slug = data["project_slug"]
    run_url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
    run_resp = client.post(run_url, HTTP_ACCEPT="application/json")
    body = json.loads(run_resp.content.decode())
    assert isinstance(body.get("lab_replay_frames_json"), list)
    assert len(body["lab_replay_frames_json"]) >= 1
```

- [ ] **Step 2: Run tests — expect FAIL**

```powershell
python -m pytest tests/integration/web/test_asteroid_miner_layout_solver.py -k "lazy_mode or inline_mode_still" -v --tb=short
```

- [ ] **Step 3: Implement slim dict**

Update `entry_result_to_json_dict` in `solver_runtime_entry.py`:

```python
from django_apps.asteroid_lab.services.lab_replay_lazy_handle import (
    build_lab_replay_lazy_handle,
    lab_replay_payload_mode,
)

def entry_result_to_json_dict(
    result: SolverRuntimeEntryResult,
    *,
    project_slug: str | None = None,
) -> dict[str, Any]:
    frames = list(result.lab_replay_frames_json)
    milestone_frames = list(result.lab_optimization_milestone_frames_json)
    mode = lab_replay_payload_mode()
    body: dict[str, Any] = {
        "ok": result.ok,
        "solver_run_id": result.solver_run_id,
        "lab_replay_frame_count": len(frames),
        "replay_track_metrics": result.replay_track_metrics,
        "lab_optimization_milestone_frame_count": len(milestone_frames),
        "lab_optimization_milestone_frames_json": milestone_frames,
        "lab_optimization_milestone_track_metrics": _normalize_milestone_track_metrics(
            result.lab_optimization_milestone_track_metrics
        ),
        "solver_summary": dict(result.solver_summary),
        "validation_passed": result.validation_passed,
        "validation_issue_codes": list(result.solver_summary.get("issue_codes") or []),
        "validation_issue_details": list(result.solver_summary.get("issue_details") or []),
        "gene_template_source": dict(result.gene_template_source),
    }
    handle = build_lab_replay_lazy_handle(
        mode=mode,
        frames=frames,
        project_slug=str(project_slug or ""),
        solver_run_id=result.solver_run_id,
    )
    if mode == "lazy":
        body["lab_replay"] = {
            "mode": handle.mode,
            "frame_count": handle.frame_count,
            "preview_frame_index": handle.preview_frame_index,
            "preview_frame": handle.preview_frame,
            "fetch_url": handle.fetch_url,
            "replay_payload_version": handle.replay_payload_version,
        }
        body["metrics"] = {
            "post_payload_slimmed": True,
            "lab_replay_inline_omitted": True,
            "lab_replay_frame_count": handle.frame_count,
        }
    else:
        body["lab_replay_frames_json"] = frames
    # ... rest unchanged (error_code, message, run_summary)
    return body
```

Update `asteroid_miner_layout_project_run_solver` in `public_pages.py`:

```python
body = entry_result_to_json_dict(result, project_slug=str(project.slug))
```

- [ ] **Step 4: Run tests — expect PASS**

```powershell
python -m pytest tests/integration/web/test_asteroid_miner_layout_solver.py -k "lazy_mode or inline_mode_still" -v --tb=short
```

- [ ] **Step 5: Commit**

```powershell
git add django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/web/views/public_pages.py tests/integration/web/test_asteroid_miner_layout_solver.py
git commit -m "feat: slim Run Solver POST response in lazy replay payload mode"
```

---

### Task 5: GET lab-replay endpoint (TDD)

**Files:**
- Modify: `django_apps/web/urls.py`
- Modify: `django_apps/web/views/public_pages.py`
- Create: `tests/integration/web/test_lab_replay_lazy_load_endpoint.py`

- [ ] **Step 1: Write failing endpoint tests**

Create `tests/integration/web/test_lab_replay_lazy_load_endpoint.py`:

```python
import json

import pytest
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _create_project_and_run(client: Client) -> tuple[str, int]:
    from tests.integration.web.test_asteroid_miner_layout_solver import (
        _unique_valid_copy,
    )

    copy_code = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    create_resp = client.post(create_url, {"copy_code": copy_code}, HTTP_ACCEPT="application/json")
    data = json.loads(create_resp.content.decode())
    slug = str(data["project_slug"])
    run_url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
    run_resp = client.post(run_url, HTTP_ACCEPT="application/json")
    body = json.loads(run_resp.content.decode())
    return slug, int(body["solver_run_id"])


def test_lab_replay_get_returns_frames_for_run(client: Client) -> None:
    slug, run_id = _create_project_and_run(client)
    url = reverse(
        "web:asteroid-miner-layout-project-solver-run-lab-replay",
        kwargs={"slug": slug, "run_id": run_id},
    )
    resp = client.get(url, HTTP_ACCEPT="application/json")
    assert resp.status_code == 200
    payload = json.loads(resp.content.decode())
    assert payload["run_id"] == run_id
    assert payload["frame_count"] == len(payload["frames"])
    assert payload["frame_count"] >= 1


def test_lab_replay_get_unknown_run_returns_404(client: Client) -> None:
    slug, _run_id = _create_project_and_run(client)
    url = reverse(
        "web:asteroid-miner-layout-project-solver-run-lab-replay",
        kwargs={"slug": slug, "run_id": 9_999_999},
    )
    resp = client.get(url, HTTP_ACCEPT="application/json")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run — expect FAIL** (404 route not found)

```powershell
python -m pytest tests/integration/web/test_lab_replay_lazy_load_endpoint.py -v --tb=short
```

- [ ] **Step 3: Add URL + view**

In `django_apps/web/urls.py`:

```python
path(
    "asteroid-miner-layout/p/<slug:slug>/solver-runs/<int:run_id>/lab-replay/",
    views.asteroid_miner_layout_project_solver_run_lab_replay,
    name="asteroid-miner-layout-project-solver-run-lab-replay",
),
```

In `django_apps/web/views/public_pages.py`:

```python
from django.views.decorators.http import require_GET

@require_GET
def asteroid_miner_layout_project_solver_run_lab_replay(
    request: HttpRequest,
    slug: str,
    run_id: int,
) -> JsonResponse:
    project = AsteroidProject.objects.filter(slug=slug).first()
    if project is None:
        return JsonResponse({"ok": False, "error": "project_not_found"}, status=404)
    run = SolverRun.objects.filter(pk=int(run_id), project_id=int(project.pk)).first()
    if run is None:
        return JsonResponse({"ok": False, "error": "solver_run_not_found"}, status=404)
    frames, metrics = build_lab_replay_frames_for_project(
        int(project.pk),
        solver_run_id=int(run.pk),
    )
    return JsonResponse(
        {
            "schema_version": 1,
            "run_id": int(run.pk),
            "project_slug": str(project.slug),
            "frame_count": len(frames),
            "frames": frames,
            "replay_track_metrics": metrics,
            "metrics": {
                "source": "lazy_load",
                "semantic_equivalent_to_inline": True,
            },
        }
    )
```

- [ ] **Step 4: Run endpoint tests — PASS**

```powershell
python -m pytest tests/integration/web/test_lab_replay_lazy_load_endpoint.py -v --tb=short
```

- [ ] **Step 5: Commit**

```powershell
git add django_apps/web/urls.py django_apps/web/views/public_pages.py tests/integration/web/test_lab_replay_lazy_load_endpoint.py
git commit -m "feat: add GET lab-replay endpoint with run-scoped frames"
```

---

### Task 6: Semantic equivalence + run isolation integration test

**Files:**
- Modify: `tests/integration/web/test_lab_replay_lazy_load_endpoint.py`

- [ ] **Step 1: Add equivalence test**

Append to `test_lab_replay_lazy_load_endpoint.py`:

```python
from django.test import override_settings


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="inline")
def test_lab_replay_get_matches_inline_post_for_same_run(client: Client) -> None:
    from tests.integration.web.test_asteroid_miner_layout_solver import _unique_valid_copy

    copy_code = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    create_resp = client.post(create_url, {"copy_code": copy_code}, HTTP_ACCEPT="application/json")
    data = json.loads(create_resp.content.decode())
    slug = str(data["project_slug"])
    run_url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
    post_body = json.loads(client.post(run_url, HTTP_ACCEPT="application/json").content.decode())
    run_id = int(post_body["solver_run_id"])
    inline_frames = list(post_body["lab_replay_frames_json"])

    get_url = reverse(
        "web:asteroid-miner-layout-project-solver-run-lab-replay",
        kwargs={"slug": slug, "run_id": run_id},
    )
    get_body = json.loads(client.get(get_url, HTTP_ACCEPT="application/json").content.decode())
    assert get_body["frames"] == inline_frames
```

- [ ] **Step 2: Run — PASS**

```powershell
python -m pytest tests/integration/web/test_lab_replay_lazy_load_endpoint.py -v --tb=short
```

- [ ] **Step 3: Commit**

```powershell
git add tests/integration/web/test_lab_replay_lazy_load_endpoint.py
git commit -m "test: assert GET lab-replay matches inline POST frames for run"
```

---

### Task 7: Payload size regression gate (TDD)

**Files:**
- Modify: `tests/integration/web/test_asteroid_miner_layout_solver.py`
- Modify: `tests/support/measure_json_sections.py` (only if helper gap found)

- [ ] **Step 1: Measure fixture and add named constant**

In `tests/integration/web/test_asteroid_miner_layout_solver.py` add:

```python
# Measured on 2026-05-30 with _unique_valid_copy() Run Solver fixture (update if fixture changes).
LAB_REPLAY_LAZY_POST_MAX_BYTES = 512_000  # replace after first measurement run
```

Add test:

```python
@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="inline")
def test_measure_inline_post_bytes_for_fixture(client: Client) -> None:
    """Record inline baseline; run once to calibrate LAB_REPLAY_LAZY_POST_MAX_BYTES."""
    copy_code = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    create_resp = client.post(create_url, {"copy_code": copy_code}, HTTP_ACCEPT="application/json")
    slug = json.loads(create_resp.content.decode())["project_slug"]
    run_url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
    inline_body = json.loads(client.post(run_url, HTTP_ACCEPT="application/json").content.decode())
    sections = measure_json_sections(inline_body)
    inline_bytes = int(sections["total_bytes"])
    assert inline_bytes > 0


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_post_projects_json_size_attribution_and_lazy_post_under_cap(client: Client) -> None:
    copy_code = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    create_resp = client.post(create_url, {"copy_code": copy_code}, HTTP_ACCEPT="application/json")
    slug = json.loads(create_resp.content.decode())["project_slug"]
    run_url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
    lazy_body = json.loads(client.post(run_url, HTTP_ACCEPT="application/json").content.decode())
    sections = measure_json_sections(lazy_body)
    assert "lab_replay_frames_json" not in lazy_body
    assert sections.get("lab_replay_frames_json_bytes", 0) == 0
    assert int(sections["total_bytes"]) <= LAB_REPLAY_LAZY_POST_MAX_BYTES
```

- [ ] **Step 2: Run measurement test; set constant**

```powershell
python -m pytest tests/integration/web/test_asteroid_miner_layout_solver.py::test_measure_inline_post_bytes_for_fixture -v --tb=short
```

Update `LAB_REPLAY_LAZY_POST_MAX_BYTES` to `max(measured_lazy_bytes * 2, 512_000)` or 10% of measured inline, whichever is larger (headroom for CI).

- [ ] **Step 3: Run size gate — PASS**

```powershell
python -m pytest tests/integration/web/test_asteroid_miner_layout_solver.py -k "json_size or lazy_mode" -v --tb=short
```

- [ ] **Step 4: Commit**

```powershell
git add tests/integration/web/test_asteroid_miner_layout_solver.py
git commit -m "test: add lazy POST payload size regression gate"
```

---

### Task 8: Frontend lazy-load controller (minimal 13C)

**Files:**
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`

- [ ] **Step 1: Add load state near replay globals**

After `replayFrames` / `hasServerReplay` declarations, add:

```javascript
const labReplayLoadState = {
  mode: "inline",
  status: "idle",
  frameCount: 0,
  fetchUrl: null,
  errorMessage: null,
  loadPromise: null,
};

function renderLabReplayLoadStatus() {
  const el = document.getElementById("lab-replay-load-status");
  if (!el) return;
  if (labReplayLoadState.mode !== "lazy") {
    el.textContent = "";
    return;
  }
  if (labReplayLoadState.status === "loading") {
    el.textContent = "Replay: loading…";
  } else if (labReplayLoadState.status === "loaded") {
    el.textContent = "Replay: loaded " + String(labReplayLoadState.frameCount) + " frames";
  } else if (labReplayLoadState.status === "error") {
    el.textContent = "Replay: failed to load — retry";
  } else {
    el.textContent = "Replay: preview only";
  }
}

function applyLoadedLabReplayPayload(payload) {
  if (!payload || !Array.isArray(payload.frames)) return;
  const prevIndex = replayArrayIndex;
  replayFrames = payload.frames;
  hasServerReplay = replayFrames.length > 0;
  replayCleanup();
  replayCleanup = initializeServerReplaySurface(replayFrames);
  replayArrayIndex = Math.min(prevIndex, Math.max(0, replayFrames.length - 1));
  labReplayLoadState.status = "loaded";
  labReplayLoadState.frameCount = replayFrames.length;
  renderLabReplayLoadStatus();
  applyFrame();
}

function ensureLabReplayFramesLoaded(reason) {
  if (labReplayLoadState.mode !== "lazy" || labReplayLoadState.status === "loaded") {
    return Promise.resolve();
  }
  if (!labReplayLoadState.fetchUrl) {
    return Promise.resolve();
  }
  if (labReplayLoadState.loadPromise) {
    return labReplayLoadState.loadPromise;
  }
  labReplayLoadState.status = "loading";
  renderLabReplayLoadStatus();
  labReplayLoadState.loadPromise = fetch(labReplayLoadState.fetchUrl, {
    credentials: "same-origin",
    headers: { Accept: "application/json" },
  })
    .then(function (res) {
      return res.json().then(function (data) {
        return { ok: res.ok, data: data };
      });
    })
    .then(function (bundle) {
      if (!bundle.ok || !bundle.data || !Array.isArray(bundle.data.frames)) {
        throw new Error("lab_replay_load_failed");
      }
      applyLoadedLabReplayPayload(bundle.data);
    })
    .catch(function () {
      labReplayLoadState.status = "error";
      labReplayLoadState.errorMessage = "load_failed";
      renderLabReplayLoadStatus();
    })
    .finally(function () {
      labReplayLoadState.loadPromise = null;
    });
  return labReplayLoadState.loadPromise;
}
```

- [ ] **Step 2: Extend `replaceLabReplayPayload`**

At start of frame handling (replace block that sets `replayFrames = next`):

```javascript
const lazy = payload.lab_replay;
if (lazy && lazy.mode === "lazy") {
  labReplayLoadState.mode = "lazy";
  labReplayLoadState.status = "idle";
  labReplayLoadState.frameCount = Number(lazy.frame_count) || 0;
  labReplayLoadState.fetchUrl = typeof lazy.fetch_url === "string" ? lazy.fetch_url : null;
  labReplayLoadState.errorMessage = null;
  const preview = lazy.preview_frame && typeof lazy.preview_frame === "object" ? lazy.preview_frame : null;
  replayFrames = preview ? [preview] : [];
  hasServerReplay = replayFrames.length > 0;
  if (!hasServerReplay) {
    window.location.assign(redirectTo || window.location.href);
    return;
  }
  replayCleanup();
  replayCleanup = initializeServerReplaySurface(replayFrames);
  replayArrayIndex = 0;
  setPlaying(false);
  renderLabReplayLoadStatus();
  applyFrame();
  return;
}
```

Keep existing inline path unchanged below.

- [ ] **Step 3: Gate timeline interactions**

Wrap play/scrub handlers to call `ensureLabReplayFramesLoaded` first, e.g. in play button click and scrub `input` handler:

```javascript
ensureLabReplayFramesLoaded("play").then(function () {
  if (labReplayLoadState.status === "error") return;
  /* existing play logic */
});
```

- [ ] **Step 4: Add HUD element to template (minimal)**

In `django_apps/web/templates/web/asteroid_miner_layout_solver.html` near replay controls, add:

```html
<div id="lab-replay-load-status" class="text-xs text-muted"></div>
```

- [ ] **Step 5: Manual smoke**

Run dev server, create project, Run Solver, confirm preview renders and scrub triggers network GET to `lab-replay/`.

- [ ] **Step 6: Commit**

```powershell
git add django_apps/web/static/web/js/asteroid_miner_layout_lab.js django_apps/web/templates/web/asteroid_miner_layout_solver.html
git commit -m "feat: lazy-load lab replay frames on timeline interaction"
```

---

### Task 9: environment.md + full gate

**Files:**
- Modify: `documents/ai/manuals/environment.md`

- [ ] **Step 1: Register env key**

Add row:

```markdown
| `ASTEROID_LAB_REPLAY_PAYLOAD_MODE` | `lazy` | `config/settings.py` — `inline` keeps full POST `lab_replay_frames_json`; `lazy` omits inline array (Sequence 13C) |
```

- [ ] **Step 2: Full narrow gate**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_replay_run_scoped_builder.py tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py tests/integration/web/test_lab_replay_lazy_load_endpoint.py tests/integration/web/test_asteroid_miner_layout_solver.py -k "lab_replay or lazy or json_size or replay" -v --tb=short
python -m ruff check django_apps/asteroid_lab/services/lab_replay_timeline_payload.py django_apps/asteroid_lab/services/lab_replay_lazy_handle.py django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/web/views/public_pages.py
python -m mypy django_apps/asteroid_lab/services/lab_replay_timeline_payload.py django_apps/asteroid_lab/services/lab_replay_lazy_handle.py django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/web/views/public_pages.py
```

Expected: PASS

- [ ] **Step 3: Mark plan item in current_plan when merged**

Update `documents/ai/current_plan.md` Sequence 13C row to **CLOSED** with date after PR merge.

- [ ] **Step 4: Commit**

```powershell
git add documents/ai/manuals/environment.md
git commit -m "docs: register ASTEROID_LAB_REPLAY_PAYLOAD_MODE in environment manual"
```

---

## Spec coverage self-review

| Spec requirement | Task |
|------------------|------|
| Option C POST-only slim | Tasks 4, 7, 8 |
| A-1 run-scoped builder | Task 2 |
| GET endpoint | Task 5 |
| Semantic equivalence | Task 6 |
| Inline fallback | Tasks 3, 4 |
| Preview = last frame | Task 3 |
| Payload size gate | Task 7 |
| Terminology sync | Task 1 |
| Transport-only note (POST still composes) | Documented in spec; no defer-compose in 13C |
| Milestone HUD unchanged | No task (unchanged wire) |
| SSR deferred | Out of scope |
| environment.md registration | Task 9 |

## Placeholder scan

No TBD steps. Size constant requires one measurement run in Task 7 Step 2 (explicit command provided).

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-30-lab-replay-lazy-load-post-slimming.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
