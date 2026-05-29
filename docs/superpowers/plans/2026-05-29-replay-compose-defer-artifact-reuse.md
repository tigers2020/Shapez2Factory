# PR-13C2-lite — Replay Compose Defer + Artifact Reuse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop repeating `build_lab_replay_frames_for_project()` on lazy SSR (cache-hit), run-solver POST, and lab-replay GET (cache-hit) by persisting composed frames + manifest summary on `SolverRun.config_json` with partial JSON reads so SSR never deserializes the ~15 MB frames blob.

**Architecture:** One compose after Layer 02 solve → atomic merge into `config_json` → lazy SSR reads only `lab_replay_manifest_summary` via `KeyTransform`; GET reads only `lab_replay_composed_frames` via `KeyTransform`. Cache schema version invalidates storage; wire `replay_payload_version` unchanged. **Payload shape unchanged** (not 13E).

**Tech Stack:** Django 5.x JSONField + `KeyTransform`, pytest-django, `unittest.mock.patch`, ruff, black, mypy `django_apps config src`, optional `ASTEROID_LAB_PERF_TRACE=1`

**Spec:** [`docs/superpowers/specs/2026-05-29-replay-compose-defer-artifact-reuse-design.md`](../specs/2026-05-29-replay-compose-defer-artifact-reuse-design.md)

**Branch:** `feat/replay-compose-defer-artifact-reuse` (from `feat/lab-request-latency-instrumentation` or `master` after 13D+13L merge)

**Out of scope:** 13E delta · 13G gzip · PR-13F interning · `solver_runs_for_lab_project` query optimization

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `django_apps/asteroid_lab/services/solver_run_config_keys.py` | New config key constants |
| Create | `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py` | Partial load, persist merge, schema version |
| Modify | `django_apps/asteroid_lab/services/solver_runtime_layer02.py` | Compose once + persist; remove duplicate post compose |
| Modify | `django_apps/asteroid_lab/services/solver_runtime_entry.py` | POST body from summary (no frames list required) |
| Modify | `django_apps/asteroid_lab/services/lab_replay_lazy_handle.py` | `build_handle_from_manifest_summary()` |
| Modify | `django_apps/web/services/asteroid_lab_page_context.py` | Lazy cache-hit/miss paths |
| Modify | `django_apps/web/views/public_pages.py` | GET uses partial frame load |
| Modify | `django_apps/asteroid_lab/observability/lab_perf_trace.py` | New cache/byte spans |
| Create | `tests/unit/asteroid_lab/test_lab_replay_persisted_cache.py` | Loader + persist unit tests |
| Create | `tests/integration/web/test_lab_replay_compose_defer.py` | SSR/GET/POST integration |
| Modify | `tests/integration/web/test_lab_replay_ssr_manifest.py` | Seed manifest summary on fixtures |
| Modify | `documents/ai/current_plan.md` | Queue row ACTIVE → CLOSED |
| Modify | `documents/Algorithm/asteroid_lab_13_replay_payload_scalability.md` | Note 13C2-lite |

---

## Task 0: Inventory, branch, patch targets

**Files:** none (read-only)

**Fixed inventory — `build_lab_replay_frames_for_project` call sites (patch these imports):**

| Module | Import path for `patch()` |
|--------|---------------------------|
| `django_apps/web/services/asteroid_lab_page_context.py` | `django_apps.web.services.asteroid_lab_page_context.build_lab_replay_frames_for_project` |
| `django_apps/web/views/public_pages.py` | `django_apps.web.views.public_pages.build_lab_replay_frames_for_project` |
| `django_apps/asteroid_lab/services/solver_runtime_layer02.py` | `django_apps.asteroid_lab.services.solver_runtime_layer02.build_lab_replay_frames_for_project` |
| `django_apps/asteroid_lab/services/solver_runtime_entry.py` | `django_apps.asteroid_lab.services.solver_runtime_entry.build_lab_replay_frames_for_project` |

Also grep before Task 1: `reset_map` / `solver_runtime_entry` error paths may compose without persisting — leave as documented exceptions.

**Compose-count tests (success path):** Patch `django_apps.asteroid_lab.services.solver_runtime_layer02.build_lab_replay_frames_for_project` only — not `solver_runtime_entry` (success path does not call compose there).

**`public_pages` patch:** H2 (`lab_replay` GET) and S1 (`_lab_json_bundle_for_track_id` / reset·import) share the same imported symbol. Keep GET defer tests separate from reset/import bundle tests; do not assert zero compose globally on `public_pages` when reset paths run.

- [ ] **Step 1: Branch**

```powershell
git checkout feat/lab-request-latency-instrumentation
git pull
git checkout -b feat/replay-compose-defer-artifact-reuse
```

- [ ] **Step 2: Baseline**

```powershell
python -m pytest tests/integration/web/test_lab_replay_ssr_manifest.py tests/integration/web/test_asteroid_miner_layout_solver.py -k lazy tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py -v --tb=short
```

Expected: PASS. (`test_lab_replay_lazy_load_endpoint.py` does not exist — use layout solver lazy tests.)

- [ ] **Step 3: Record inventory in commit message body or plan note** (no code).

---

### Task 1: Config keys + persisted cache module (unit TDD)

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_run_config_keys.py`
- Create: `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`
- Create: `tests/unit/asteroid_lab/test_lab_replay_persisted_cache.py`

- [ ] **Step 1: Add constants**

In `solver_run_config_keys.py`:

```python
SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY = "lab_replay_composed_frames"
SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY = "lab_replay_manifest_summary"
```

Export in `__all__`.

- [ ] **Step 2: Write failing tests — manifest summary builder**

```python
from django_apps.asteroid_lab.services.lab_replay_persisted_cache import (
    CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION,
    build_manifest_summary_from_compose,
    is_cache_summary_valid,
)


def test_build_manifest_summary_includes_cache_schema_version() -> None:
    frames = [{"frame_index": 0}, {"frame_index": 1}]
    metrics = {"frame_count": 2, "replay_truncated": False}
    summary = build_manifest_summary_from_compose(frames=frames, metrics=metrics)
    assert summary["lab_replay_cache_schema_version"] == CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION
    assert summary["replay_payload_version"] == 1
    assert summary["frame_count"] == 2
    assert summary["preview_frame_index"] == 1
    assert summary["preview_frame"] == frames[1]
    assert summary["replay_track_metrics"] == metrics


def test_is_cache_summary_valid_rejects_wrong_schema() -> None:
    assert is_cache_summary_valid({"lab_replay_cache_schema_version": 0}) is False
    assert is_cache_summary_valid(
        {"lab_replay_cache_schema_version": CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION, "frame_count": 1}
    ) is True
```

- [ ] **Step 3: Run — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_replay_persisted_cache.py -v --tb=short
```

- [ ] **Step 4: Implement `lab_replay_persisted_cache.py` (minimal)**

```python
from __future__ import annotations

import copy
from typing import Any

from django.db import transaction
from django.db.models.fields.json import KeyTransform

from django_apps.asteroid_lab.models import SolverRun
from django_apps.asteroid_lab.services.lab_replay_lazy_handle import LAB_REPLAY_PAYLOAD_VERSION
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY,
    SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY,
)

CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION = 1


def build_manifest_summary_from_compose(
    *, frames: list[dict[str, Any]], metrics: dict[str, Any]
) -> dict[str, Any]:
    count = len(frames)
    preview_index = max(0, count - 1) if count else 0
    preview = dict(frames[preview_index]) if count else None
    return {
        "replay_payload_version": LAB_REPLAY_PAYLOAD_VERSION,
        "lab_replay_cache_schema_version": CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION,
        "frame_count": count,
        "preview_frame_index": preview_index,
        "preview_frame": preview,
        "replay_track_metrics": dict(metrics),
    }


def is_cache_summary_valid(summary: dict[str, Any] | None) -> bool:
    if not summary or not isinstance(summary, dict):
        return False
    return int(summary.get("lab_replay_cache_schema_version", -1)) == CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION


def load_manifest_summary_for_run_id(run_id: int) -> dict[str, Any] | None:
    key = SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY
    raw = (
        SolverRun.objects.filter(pk=int(run_id))
        .values_list(KeyTransform(key, "config_json"), flat=True)
        .first()
    )
    return dict(raw) if isinstance(raw, dict) else None


def load_composed_frames_for_run_id(run_id: int) -> list[dict[str, Any]] | None:
    key = SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY
    raw = (
        SolverRun.objects.filter(pk=int(run_id))
        .values_list(KeyTransform(key, "config_json"), flat=True)
        .first()
    )
    if not isinstance(raw, list) or not raw:
        return None
    return [dict(x) for x in raw if isinstance(x, dict)]


@transaction.atomic
def persist_composed_replay_for_run_id(
    run_id: int,
    *,
    frames: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> None:
    summary = build_manifest_summary_from_compose(frames=frames, metrics=metrics)
    run = SolverRun.objects.select_for_update().get(pk=int(run_id))
    config = copy.deepcopy(dict(run.config_json or {}))
    config[SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY] = frames
    config[SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY] = summary
    run.config_json = config
    run.save(update_fields=["config_json"])
```

Adjust imports/types per ruff/mypy.

- [ ] **Step 5: Run unit tests — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_replay_persisted_cache.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/services/lab_replay_persisted_cache.py django_apps/asteroid_lab/services/solver_run_config_keys.py
```

- [ ] **Step 6: Test persist preserves unrelated config keys**

Add test: seed run with `config_json={"solver_runtime_replay_frames": [{"x": 1}], "solver_summary": {"a": 1}}`, persist cache, reload run, assert both old keys still present.

---

### Task 2: Lazy handle from summary (unit)

**Files:**
- Modify: `django_apps/asteroid_lab/services/lab_replay_lazy_handle.py`
- Modify: `tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py`

- [ ] **Step 1: Failing test `test_build_handle_from_manifest_summary`**

- [ ] **Step 2: Implement**

```python
def build_lab_replay_lazy_handle_from_summary(
    *,
    project_slug: str,
    solver_run_id: int | None,
    manifest_summary: dict[str, Any],
) -> LabReplayLazyHandle:
    mode = lab_replay_payload_mode()
    count = int(manifest_summary.get("frame_count", 0))
    preview_index = int(manifest_summary.get("preview_frame_index", 0))
    preview_raw = manifest_summary.get("preview_frame")
    preview = dict(preview_raw) if isinstance(preview_raw, dict) else None
    fetch_url = None
    if mode == "lazy" and solver_run_id is not None and project_slug and count > 0:
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
        replay_payload_version=int(manifest_summary.get("replay_payload_version", 1)),
    )
```

- [ ] **Step 3: pytest + ruff PASS**

---

### Task 3: Layer 02 — compose once, persist, remove duplicate compose

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_runtime_layer02.py`
- Modify: `django_apps/asteroid_lab/observability/lab_perf_trace.py` (span rename)

- [ ] **Step 1: Failing integration test** (create skeleton in `tests/integration/web/test_lab_replay_compose_defer.py`):

`test_run_solver_persists_composed_cache` — run solver on fixture project, assert `load_composed_frames_for_run_id(run_id)` non-empty and `load_manifest_summary_for_run_id` valid.

Patch compose at **`django_apps.asteroid_lab.services.solver_runtime_layer02.build_lab_replay_frames_for_project`**; expect call count **1** per POST.

- [ ] **Step 2: Replace `post_replay_compose_ms` block**

```python
from django_apps.asteroid_lab.observability.lab_perf_trace import perf_span, record_perf_ms
from django_apps.asteroid_lab.services.lab_replay_persisted_cache import persist_composed_replay_for_run_id

with perf_span("replay_compose_once_ms"):
    frames, metrics = build_lab_replay_frames_for_project(pid, solver_run_id=run_id)
    persist_composed_replay_for_run_id(run_id, frames=frames, metrics=metrics)
```

Remove separate `post_replay_compose_ms` span (or alias record for one release — prefer rename only).

- [ ] **Step 3: Run targeted test**

```powershell
python -m pytest tests/integration/web/test_lab_replay_compose_defer.py::test_run_solver_persists_composed_cache -v --tb=short
```

- [ ] **Step 4: ruff on `solver_runtime_layer02.py`**

---

### Task 4: POST response from summary (no second compose)

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`

- [ ] **Step 1:** After Layer 02 returns, `entry_result_to_json_dict` should build lazy handle via `build_lab_replay_lazy_handle_from_summary` when `solver_run_id` set and summary load succeeds — **without** requiring full `frames` in `SolverRuntimeEntryResult` for lazy mode (may pass empty `lab_replay_frames_json` list if summary loaded).

- [ ] **Step 2:** Test `test_run_solver_lazy_response_uses_manifest_without_recompose` — patch compose at **`django_apps.asteroid_lab.services.solver_runtime_layer02.build_lab_replay_frames_for_project`** only; expect call count **1** per successful POST; do not patch `solver_runtime_entry` for success-path compose counts.

---

### Task 5: `lab_page_context` lazy SSR (cache-hit + miss Policy A)

**Files:**
- Modify: `django_apps/web/services/asteroid_lab_page_context.py`
- Modify: `tests/integration/web/test_lab_replay_ssr_manifest.py`
- Modify: `tests/integration/web/test_lab_replay_compose_defer.py`

- [ ] **Step 1: Failing `test_project_page_lazy_ssr_does_not_call_full_replay_composer`**

Patch: `django_apps.web.services.asteroid_lab_page_context.build_lab_replay_frames_for_project`

Fixture: SolverRun with valid `lab_replay_manifest_summary` (use `persist_composed_replay_for_run_id` in test setup). Expect compose **not** called.

- [ ] **Step 2: Failing `test_project_page_lazy_ssr_does_not_load_composed_frames_blob`**

Patch `load_composed_frames_for_run_id` to raise `AssertionError("composed frames loaded")`. Page GET must still 200 and include manifest.

- [ ] **Step 3: Implement lazy branch**

```text
if mode == "lazy":
    summary = load_manifest_summary_for_run_id(solver_run_id) if solver_run_id else None
    if is_cache_summary_valid(summary):
        handle = build_lab_replay_lazy_handle_from_summary(...)
        ctx["lab_replay_manifest_json"] = lab_replay_manifest_json_dict(
            handle=handle,
            replay_track_metrics=summary["replay_track_metrics"],
        )
        # set ui fields from summary — no build_lab_replay_frames_for_project
    else:
        with perf_span("replay_cache_miss_compose_ms"):
            frames, metrics = build_lab_replay_frames_for_project(...)
            if solver_run_id:
                persist_composed_replay_for_run_id(...)
        # build manifest from compose result (existing handle path)
```

- [ ] **Step 4: Update existing 13D manifest tests** to seed summary via `persist_composed_replay_for_run_id` instead of relying on compose during page render.

- [ ] **Step 5: pytest**

```powershell
python -m pytest tests/integration/web/test_lab_replay_ssr_manifest.py tests/integration/web/test_lab_replay_compose_defer.py -k "lazy or cache" -v --tb=short
```

---

### Task 6: Lab replay GET — partial frame load + fallback

**Files:**
- Modify: `django_apps/web/views/public_pages.py`

- [ ] **Step 1: Tests**

- `test_lab_replay_get_uses_persisted_artifact_when_available` — patch composer in `public_pages`; expect 0 calls.
- `test_lab_replay_get_falls_back_to_compose_without_artifact` — old run; expect 1 call.
- `test_lazy_get_semantic_equivalence_persisted_vs_compose` — compare JSON keys/frame_count.

- [ ] **Step 2: Implement GET**

```python
with perf_span("replay_cache_load_ms"):
    frames = load_composed_frames_for_run_id(int(run.pk))
    summary = load_manifest_summary_for_run_id(int(run.pk))
if frames is not None and is_cache_summary_valid(summary):
    metrics = dict(summary["replay_track_metrics"])
    record replay_cache_json_decode_ms / lab_replay_cache_frames_bytes
else:
    with perf_span("replay_cache_miss_compose_ms"):
        frames, metrics = build_lab_replay_frames_for_project(...)
        persist_composed_replay_for_run_id(...)
```

- [ ] **Step 3: pytest lazy load endpoint + new tests**

```powershell
python -m pytest tests/integration/web/test_asteroid_miner_layout_solver.py -k lazy tests/integration/web/test_lab_replay_compose_defer.py -v --tb=short
```

---

### Task 7: Perf trace bytes + manual verification

**Files:**
- Modify: `django_apps/asteroid_lab/observability/lab_perf_trace.py`
- Modify: `docs/superpowers/specs/2026-05-29-lab-request-latency-instrumentation-design.md` (optional one-line cross-ref)

- [ ] **Step 1:** Add `record_perf_meta` keys: `lab_replay_cache_frames_bytes`, `lab_replay_manifest_summary_bytes`, spans per spec §4.9.

- [ ] **Step 2:** Manual trace on `rttp-core-recovery-test-map`:

```powershell
$env:ASTEROID_LAB_PERF_TRACE="1"
$env:ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy"
```

Second page load (cache warm): `build_lab_replay_frames_for_project_ms` absent; `lab_replay_manifest_summary_bytes` small.

---

### Task 8: Docs + narrow gate

- [ ] **Step 1:** Update `documents/ai/current_plan.md` — 13C2-lite row.

- [ ] **Step 2:** Note in `asteroid_lab_13_replay_payload_scalability.md` Strategy table: compose defer (13C2-lite) between 13D and 13E.

- [ ] **Step 3: Iteration gate**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_replay_persisted_cache.py tests/integration/web/test_lab_replay_compose_defer.py tests/integration/web/test_lab_replay_ssr_manifest.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/services/lab_replay_persisted_cache.py django_apps/web/services/asteroid_lab_page_context.py django_apps/web/views/public_pages.py django_apps/asteroid_lab/services/solver_runtime_layer02.py
```

- [ ] **Step 4: Full gate before PR** (per AGENTS.md): `powershell -File scripts/test_full.ps1`, mypy, black.

---

## Plan self-review (spec coverage)

| Spec § | Task |
|--------|------|
| §4.7 no SSR frames deserialize | Task 1 `KeyTransform` loaders; Task 5 blob test |
| §4.8 atomic merge | Task 1 persist test; Task 3 |
| §4.9 perf bytes | Task 7 |
| §4.10 cache-miss Policy A | Task 5 miss test + implementation |
| Cache schema version | Task 1 |
| PATCH call sites | Task 0 table |
| Exit criteria cache-hit | Tasks 5–6 tests |

No TBD placeholders remain in task steps above.

---

## Execution handoff

**Plan saved to** `docs/superpowers/plans/2026-05-29-replay-compose-defer-artifact-reuse.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — run tasks in this session with executing-plans checkpoints  

Which approach do you want?
