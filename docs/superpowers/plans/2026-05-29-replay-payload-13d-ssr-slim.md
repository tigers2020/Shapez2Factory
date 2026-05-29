# PR-13D-SSR — Manifest-only SSR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove full `lab_replay_frames_json` from the project page HTML document; embed a single `lab-replay-manifest-data` script (preview + metrics + lazy fetch URL) and reuse the 13C frontend lazy loader.

**Architecture:** `lab_page_context()` still calls `build_lab_replay_frames_for_project()` once for preview/metrics but omits the full array from template context when `ASTEROID_LAB_REPLAY_PAYLOAD_MODE=lazy`. Template branches on `lab_replay_ssr_delivery`. JS `init()` reads manifest first (same state as POST lazy). Inline SSR rollback only when settings mode is `inline`.

**Tech Stack:** Django 5.x, pytest-django, vanilla JS (`asteroid_miner_layout_lab.js`), ruff, black, mypy `django_apps config src`

**Spec:** [`docs/superpowers/specs/2026-05-29-replay-payload-network-optimization-design.md`](../specs/2026-05-29-replay-payload-network-optimization-design.md)

**Branch:** `feat/replay-payload-13d-ssr-slim` (worktree recommended)

**Out of scope:** `reset_map` JSON inline slimming, 13G gzip, 13E delta, Run Solver POST changes, 13UI-guard

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `documents/Algorithm/asteroid_lab_13_replay_payload_scalability.md` | Note 13D-SSR approved + link spec |
| Modify | `documents/ai/current_plan.md` | ACTIVE queue row for 13D-SSR |
| Modify | `django_apps/asteroid_lab/services/lab_replay_lazy_handle.py` | `lab_replay_manifest_json_dict()` |
| Modify | `django_apps/web/services/asteroid_lab_page_context.py` | Manifest context; no full frames in lazy SSR |
| Modify | `django_apps/web/templates/web/asteroid_miner_layout_solver.html` | Conditional manifest vs inline scripts |
| Modify | `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | SSR manifest bootstrap in `init()` |
| Create | `tests/integration/web/test_lab_replay_ssr_manifest.py` | SSR size + script + bulk-frame guards |
| Modify | `tests/integration/web/test_asteroid_miner_layout_solver.py` | Update legacy assertion for manifest script |
| Modify | `tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py` | Unit test for manifest dict helper |

---

### Task 0: Branch, baseline, and inventory

**Files:** none

**Inventory (fixed before Task 1):**

- `solver_runs_for_lab_project()` returns `list[dict]` from `lab_run_summary_from_orm`; run id key is **`"id"`** (string), e.g. `"295"`. Use `int(runs[0]["id"])`, not `.pk`.
- Inline SSR rollback **keeps** `lab-replay-track-metrics-data` — `init()` reads it for `updateReplayTruncationHud`; lazy mode uses `manifest.replay_track_metrics` only.
- Helper: `_solver_run_id_from_lab_summary(run: dict | None) -> int | None` in `asteroid_lab_page_context.py`.

- [ ] **Step 1: Create branch**

```powershell
git checkout master
git pull
git checkout -b feat/replay-payload-13d-ssr-slim
```

- [ ] **Step 2: Baseline tests**

```powershell
python -m pytest tests/integration/web/test_asteroid_miner_layout_solver.py tests/integration/web/test_lab_replay_lazy_load_endpoint.py tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py -v --tb=short
```

Expected: PASS (13C lazy POST/GET still green before SSR edits).

---

### Task 1: Manifest dict helper (unit TDD)

**Files:**
- Modify: `django_apps/asteroid_lab/services/lab_replay_lazy_handle.py`
- Modify: `tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py`

- [ ] **Step 1: Write failing test**

Add to `tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py`:

```python
from django_apps.asteroid_lab.services.lab_replay_lazy_handle import (
    build_lab_replay_lazy_handle,
    lab_replay_manifest_json_dict,
)


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_lab_replay_manifest_json_dict_includes_metrics() -> None:
    frames = [{"frame_index": 0, "title": "a"}, {"frame_index": 1, "title": "b"}]
    handle = build_lab_replay_lazy_handle(
        mode="lazy",
        frames=frames,
        project_slug="demo-slug",
        solver_run_id=99,
    )
    metrics = {"frame_count": 2, "replay_truncated": False}
    manifest = lab_replay_manifest_json_dict(handle=handle, replay_track_metrics=metrics)
    assert manifest["mode"] == "lazy"
    assert manifest["frame_count"] == 2
    assert manifest["preview_frame_index"] == 1
    assert manifest["preview_frame"] == frames[1]
    assert manifest["fetch_url"] == "/asteroid-miner-layout/p/demo-slug/solver-runs/99/lab-replay/"
    assert manifest["replay_track_metrics"] == metrics
```

- [ ] **Step 2: Run test — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py::test_lab_replay_manifest_json_dict_includes_metrics -v --tb=short
```

Expected: FAIL — `lab_replay_manifest_json_dict` not defined.

- [ ] **Step 3: Implement helper**

Add to `django_apps/asteroid_lab/services/lab_replay_lazy_handle.py`:

```python
def lab_replay_manifest_json_dict(
    *,
    handle: LabReplayLazyHandle,
    replay_track_metrics: dict[str, Any],
) -> dict[str, Any]:
    preview = handle.preview_frame
    return {
        "mode": handle.mode,
        "frame_count": int(handle.frame_count),
        "preview_frame_index": int(handle.preview_frame_index),
        "preview_frame": dict(preview) if preview is not None else None,
        "fetch_url": handle.fetch_url,
        "replay_payload_version": int(handle.replay_payload_version),
        "replay_track_metrics": dict(replay_track_metrics),
    }
```

Update `__all__` to export `lab_replay_manifest_json_dict`.

- [ ] **Step 4: Run test — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py -v --tb=short
```

- [ ] **Step 5: Commit**

```powershell
git add django_apps/asteroid_lab/services/lab_replay_lazy_handle.py tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py
git commit -m "feat(asteroid_lab): add lab_replay_manifest_json_dict for SSR embed"
```

---

### Task 2: SSR integration tests (red)

**Files:**
- Create: `tests/integration/web/test_lab_replay_ssr_manifest.py`

- [ ] **Step 1: Create failing integration tests**

Create `tests/integration/web/test_lab_replay_ssr_manifest.py`:

```python
"""SSR manifest-only replay embed (Sequence 13D-SSR)."""

from __future__ import annotations

import json
import random

import pytest
from django.test import Client, override_settings
from django.urls import reverse

from django_apps.asteroid_lab import models as m

pytestmark = pytest.mark.django_db

# Calibrate after first green run on CI fixture (same policy as LAB_REPLAY_LAZY_POST_MAX_BYTES).
LAB_REPLAY_SSR_DOCUMENT_MAX_BYTES = 512_000
# Single preview frame + manifest metadata; not 80+ timeline frames.
LAB_REPLAY_SSR_MAX_FRAME_INDEX_MARKERS = 24


def _unique_valid_copy() -> str:
    import base64
    import gzip

    root = {
        "V": random.randint(1, 10_000_000),
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
            ],
        },
    }
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    b64 = base64.b64encode(gzip.compress(text)).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


def _project_page_html(client: Client, copy_code: str) -> tuple[str, m.AsteroidProject]:
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    resp = client.post(create_url, {"copy_code": copy_code}, follow=True)
    assert resp.status_code == 200
    proj = m.AsteroidProject.objects.get()
    # Run solver once so latest run + composed replay exist (matches real UI).
    run_url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": proj.slug})
    run_resp = client.post(run_url, HTTP_ACCEPT="application/json")
    assert run_resp.status_code == 200
    page = client.get(reverse("web:asteroid-miner-layout-project", kwargs={"slug": proj.slug}))
    assert page.status_code == 200
    return page.content.decode(), proj


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_project_page_lazy_ssr_has_manifest_not_frames_script(client: Client) -> None:
    html, _proj = _project_page_html(client, _unique_valid_copy())
    assert 'id="lab-replay-manifest-data"' in html
    assert 'id="lab-replay-frames-data"' not in html
    assert 'id="lab-initial-replay-frame-data"' not in html
    assert 'id="lab-replay-track-metrics-data"' not in html


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_project_page_lazy_ssr_document_bytes_under_cap(client: Client) -> None:
    html, _proj = _project_page_html(client, _unique_valid_copy())
    assert len(html.encode("utf-8")) <= LAB_REPLAY_SSR_DOCUMENT_MAX_BYTES


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_project_page_lazy_ssr_no_bulk_timeline_markers(client: Client) -> None:
    html, _proj = _project_page_html(client, _unique_valid_copy())
    assert html.count('"frame_index"') <= LAB_REPLAY_SSR_MAX_FRAME_INDEX_MARKERS


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_ssr_manifest_fetch_url_matches_latest_run(client: Client) -> None:
    html, proj = _project_page_html(client, _unique_valid_copy())
    latest_run = m.SolverRun.objects.filter(project_id=proj.pk).order_by("-id").first()
    assert latest_run is not None
    marker = 'id="lab-replay-manifest-data"'
    start = html.index(marker)
    end = html.index("</script>", start)
    blob = html[start:end]
    assert f"/solver-runs/{latest_run.pk}/lab-replay/" in blob


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="inline")
def test_project_page_inline_ssr_still_has_frames_script(client: Client) -> None:
    html, _proj = _project_page_html(client, _unique_valid_copy())
    assert 'id="lab-replay-frames-data"' in html
    assert 'id="lab-replay-manifest-data"' not in html
```

- [ ] **Step 2: Run tests — expect FAIL**

```powershell
python -m pytest tests/integration/web/test_lab_replay_ssr_manifest.py -v --tb=short
```

Expected: FAIL on manifest script / byte cap / missing project URL name.

- [ ] **Step 3: Fix project URL if needed**

Project page URL name is `web:asteroid-miner-layout-project` (see `django_apps/web/urls.py`).

---

### Task 3: `lab_page_context()` manifest delivery

**Files:**
- Modify: `django_apps/web/services/asteroid_lab_page_context.py`

- [ ] **Step 1: Implement lazy SSR context**

At top of `asteroid_lab_page_context.py`, add imports:

```python
from django_apps.asteroid_lab.services.lab_replay_lazy_handle import (
    build_lab_replay_lazy_handle,
    lab_replay_manifest_json_dict,
    lab_replay_payload_mode,
)
```

In `neutral_lab_context()`, add keys:

```python
"lab_replay_ssr_delivery": "manifest",  # or "inline"
"lab_replay_manifest_json": {},
```

Replace the body of `lab_page_context()` after `frames_json, track_metrics = build_lab_replay_frames_for_project(...)`:

```python
    mode = lab_replay_payload_mode()
    ctx["lab_replay_ssr_delivery"] = mode
    solver_run_id = _solver_run_id_from_lab_summary(runs[0] if runs else None)

    if mode == "inline":
        first = frames_json[0]
        n = len(frames_json)
        first_idx = int(first.get("frame_index", 0))
        ctx.update(
            {
                "total_frames": n,
                "initial_frame": first_idx,
                "initial_replay_phase": str(first.get("phase") or "—"),
                "lab_replay_frames_json": frames_json,
                "lab_initial_replay_frame_json": {},
                "has_replay_frames": True,
                "replay_track_metrics": track_metrics,
                "lab_replay_manifest_json": {},
            }
        )
    else:
        handle = build_lab_replay_lazy_handle(
            mode="lazy",
            frames=frames_json,
            project_slug=str(project_slug),
            solver_run_id=solver_run_id,
        )
        ctx["lab_replay_manifest_json"] = lab_replay_manifest_json_dict(
            handle=handle,
            replay_track_metrics=track_metrics,
        )
        ctx["lab_replay_frames_json"] = []
        ctx["lab_initial_replay_frame_json"] = {}
        ctx["has_replay_frames"] = handle.frame_count > 0
        ctx["total_frames"] = handle.frame_count
        ctx["replay_track_metrics"] = track_metrics
        preview = handle.preview_frame or {}
        ctx["initial_frame"] = int(preview.get("frame_index", 0))
        ctx["initial_replay_phase"] = str(preview.get("phase") or "—")
```

- [ ] **Step 2: Pass `project_slug` into `lab_page_context`**

Change signature:

```python
def lab_page_context(*, project_id: int | None = None, project_slug: str = "") -> dict[str, Any]:
```

Update `_asteroid_miner_lab_page_context` in `public_pages.py`:

```python
ctx = lab_page_context(
    project_id=int(project.pk) if project is not None else None,
    project_slug=str(project.slug) if project is not None else "",
)
```

Use `project_slug` when building `build_lab_replay_lazy_handle`.

- [ ] **Step 3: Run integration tests**

```powershell
python -m pytest tests/integration/web/test_lab_replay_ssr_manifest.py -v --tb=short
```

Still expect template failures until Task 4.

- [ ] **Step 4: Commit**

```powershell
git add django_apps/web/services/asteroid_lab_page_context.py django_apps/web/views/public_pages.py
git commit -m "feat(web): build SSR lab replay manifest in lab_page_context"
```

---

### Task 4: Template conditional scripts

**Files:**
- Modify: `django_apps/web/templates/web/asteroid_miner_layout_solver.html`

- [ ] **Step 1: Replace json_script block**

Remove lines 12–14 and insert:

```django
  {% if lab_replay_ssr_delivery == "inline" %}
  {{ lab_replay_frames_json|json_script:"lab-replay-frames-data" }}
  {{ replay_track_metrics|json_script:"lab-replay-track-metrics-data" }}
  {% else %}
  {{ lab_replay_manifest_json|json_script:"lab-replay-manifest-data" }}
  {% endif %}
```

Do **not** render `lab-initial-replay-frame-data` in either mode. Lazy: metrics only inside manifest. Inline: keep separate `lab-replay-track-metrics-data` for truncation HUD.

- [ ] **Step 2: Run integration tests**

```powershell
python -m pytest tests/integration/web/test_lab_replay_ssr_manifest.py -v --tb=short
```

Expected: PASS (or calibrate `LAB_REPLAY_SSR_DOCUMENT_MAX_BYTES` if still over cap — record measured bytes in comment).

- [ ] **Step 3: Commit**

```powershell
git add django_apps/web/templates/web/asteroid_miner_layout_solver.html
git commit -m "feat(web): SSR manifest-only replay embed (13D-SSR)"
```

---

### Task 5: Frontend `init()` manifest bootstrap

**Files:**
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`

- [ ] **Step 1: Add bootstrap helper inside `init()`**

Replace the block that reads `lab-replay-frames-data` / `lab-replay-track-metrics-data` (approx. lines 1922–1936) with:

```javascript
    const manifestRaw = readJsonScript("lab-replay-manifest-data");
    let replayFrames = [];
    let replayTrackMetrics = {};
    const labReplayLoadState = {
      mode: "inline",
      status: "idle",
      frameCount: 0,
      fetchUrl: null,
      errorMessage: null,
      loadPromise: null,
    };

    if (manifestRaw && manifestRaw.mode === "lazy") {
      labReplayLoadState.mode = "lazy";
      labReplayLoadState.frameCount = Number(manifestRaw.frame_count) || 0;
      labReplayLoadState.fetchUrl =
        typeof manifestRaw.fetch_url === "string" ? manifestRaw.fetch_url : null;
      if (manifestRaw.replay_track_metrics && typeof manifestRaw.replay_track_metrics === "object") {
        replayTrackMetrics = manifestRaw.replay_track_metrics;
      }
      const preview =
        manifestRaw.preview_frame && typeof manifestRaw.preview_frame === "object"
          ? manifestRaw.preview_frame
          : null;
      replayFrames = preview ? [preview] : [];
      if (!labReplayLoadState.fetchUrl) {
        labReplayLoadState.status = "idle";
      }
    } else {
      const replayFramesRaw = readJsonScript("lab-replay-frames-data");
      replayFrames = Array.isArray(replayFramesRaw) ? replayFramesRaw : [];
      const trackMetricsRaw = readJsonScript("lab-replay-track-metrics-data");
      replayTrackMetrics =
        trackMetricsRaw && typeof trackMetricsRaw === "object" ? trackMetricsRaw : {};
    }
    let hasServerReplay = replayFrames.length > 0;
```

Remove the duplicate `const labReplayLoadState = { ... }` declaration that followed the old reads.

- [ ] **Step 2: Align `replaceLabReplayPayload` metrics source**

In lazy branch, prefer `payload.lab_replay.replay_track_metrics` then `payload.replay_track_metrics` (POST may use top-level key). Manifest SSR only uses `init()` path.

- [ ] **Step 3: Manual smoke**

```powershell
python manage.py runserver 8080
```

Open project page → Network: document should be ≪ 1 MB (not ~16 MB). Scrub timeline → single `lab-replay/` GET.

- [ ] **Step 4: Commit**

```powershell
git add django_apps/web/static/web/js/asteroid_miner_layout_lab.js
git commit -m "feat(web): bootstrap lab replay from SSR manifest"
```

---

### Task 6: Fix existing tests + docs

**Files:**
- Modify: `tests/integration/web/test_asteroid_miner_layout_solver.py`
- Modify: `documents/Algorithm/asteroid_lab_13_replay_payload_scalability.md`
- Modify: `documents/ai/current_plan.md`

- [ ] **Step 1: Update `test_asteroid_miner_layout_post_copy_prg_shows_in_project_page`**

Change assertion:

```python
    content = response.content.decode()
    assert 'id="lab-replay-manifest-data"' in content
    assert 'id="lab-replay-frames-data"' not in content
```

- [ ] **Step 2: Docs queue**

Add to `documents/ai/current_plan.md`:

```markdown
**ACTIVE — Sequence 13D-SSR — Replay manifest SSR** — Project page embeds `lab-replay-manifest-data` only (no full frames script). Spec: [`2026-05-29-replay-payload-network-optimization-design.md`](../../docs/superpowers/specs/2026-05-29-replay-payload-network-optimization-design.md) · plan: [`2026-05-29-replay-payload-13d-ssr-slim.md`](../../docs/superpowers/plans/2026-05-29-replay-payload-13d-ssr-slim.md).
```

In `asteroid_lab_13_replay_payload_scalability.md`, under **Sequence 13D-SSR**, mark approved and link spec.

- [ ] **Step 3: Full narrow gate**

```powershell
python -m pytest tests/integration/web/test_lab_replay_ssr_manifest.py tests/integration/web/test_asteroid_miner_layout_solver.py tests/integration/web/test_lab_replay_lazy_load_endpoint.py tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/services/lab_replay_lazy_handle.py django_apps/web/services/asteroid_lab_page_context.py tests/integration/web/test_lab_replay_ssr_manifest.py
```

- [ ] **Step 4: Commit**

```powershell
git add tests/integration/web/test_asteroid_miner_layout_solver.py documents/Algorithm/asteroid_lab_13_replay_payload_scalability.md documents/ai/current_plan.md
git commit -m "test(docs): SSR manifest regression and 13D queue entry"
```

---

## Plan self-review (spec coverage)

| Spec requirement | Task |
|------------------|------|
| Amendment 1 — remove frames script (not empty) | Task 4 |
| Amendment 2 — no `lab-initial-replay-frame-data` | Task 4 |
| Amendment 3 — metrics inside manifest | Task 1, 3, 5 |
| Amendment 4 — `fetch_url: null` JS state | Task 5 |
| Amendment 5 — inline SSR only via settings | Task 3, 4, tests |
| Amendment 6 — byte cap + bulk-frame guard | Task 2 |
| Reuse 13C GET loader | Task 5 (no change to `ensureLabReplayFramesLoaded`) |
| Edge cases table | Task 3 (`solver_run_id` / empty frames) |

No placeholders remain in task steps.

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-29-replay-payload-13d-ssr-slim.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — run tasks in this session with executing-plans checkpoints  

**Which approach?**

Follow-on plans (after 13D merges): [`2026-05-29-replay-payload-13g-compression.md`](2026-05-29-replay-payload-13g-compression.md)
