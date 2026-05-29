# PR-13F — Lab Page TTFB Breakdown + Shell-Only SSR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `project_page` TTFB explainable in one `lab_perf.jsonl` line and remove provably unnecessary SSR-heavy reads (full `config_json` per run, replay frame prefetch) without changing `lab-runs-data` wire shape or reducing runs limit below 10.

**Architecture:** Extend 13L perf collector with SQL wrapper + `json_script` byte map on `project_page`; refactor `solver_runs_for_lab_project` to `.values()` + `KeyTransform(solver_summary)` only; add `get_latest_lab_replay_track_shell_for_project` (annotate `Count`, no prefetch) for `lab_page_context`. **Approach 1 — Fix + explain.** Lazy runs API / slim DTO v2 → **13H only.**

**Tech Stack:** Django 5.2+ (`KeyTransform`, `connection.execute_wrapper`), pytest-django, `CaptureQueriesContext`, `unittest.mock.patch`, ruff, black, mypy `django_apps config src`

**Spec:** [`docs/superpowers/specs/2026-05-29-lab-page-ttfb-breakdown-shell-only-design.md`](../specs/2026-05-29-lab-page-ttfb-breakdown-shell-only-design.md)

**Branch:** `feat/lab-page-ttfb-breakdown-shell-only` (from current `master` or active replay perf branch)

**Out of scope:** 13G gzip · 13E delta · 13H lazy runs API · runs limit &lt; 10 · `page_shell_cache_hit` implementation (meta stays `false`) · solver/runtime changes

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `django_apps/asteroid_lab/observability/lab_perf_trace.py` | SQL execute wrapper; `record_json_script_bytes`; export helpers |
| Modify | `django_apps/asteroid_lab/services/solver_run_lab_summary.py` | Partial-read `solver_runs_for_lab_project`; keep `lab_run_summary_from_orm` for non-page callers |
| Modify | `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py` | `get_latest_lab_replay_track_shell_for_project` |
| Modify | `django_apps/web/services/asteroid_lab_page_context.py` | Shell track; `runs_*` spans; cache-hit meta |
| Modify | `django_apps/web/views/public_pages.py` | `template_render_ms`; json_script sizing; SQL wrapper scope |
| Create | `tests/integration/web/test_lab_page_shell_perf.py` | **RED-first** shell regression tests |
| Modify | `tests/unit/asteroid_lab/test_lab_perf_trace.py` | 13F JSONL keys |
| Modify | `tests/unit/asteroid_lab/test_solver_run_lab_summary.py` | Partial-read unit test |
| Modify | `documents/ai/current_plan.md` | 13F row ACTIVE → CLOSED when done |
| Modify | `documents/ai/manuals/environment.md` | Note 13F perf keys (optional one paragraph) |

---

## Task 0: Branch and baseline

**Files:** none (read-only)

- [ ] **Step 1: Branch**

```powershell
git checkout master
git pull
git checkout -b feat/lab-page-ttfb-breakdown-shell-only
```

- [ ] **Step 2: Baseline (must be green before RED tests)**

```powershell
python -m pytest tests/integration/web/test_lab_replay_compose_defer.py tests/integration/web/test_lab_replay_ssr_manifest.py tests/unit/asteroid_lab/test_lab_perf_trace.py tests/unit/asteroid_lab/test_solver_run_lab_summary.py -v --tb=short
```

Expected: PASS.

- [ ] **Step 3: Confirm env for manual perf (later)**

```powershell
$env:ASTEROID_LAB_PERF_TRACE="1"
$env:ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy"
```

---

## Task 1: RED — runs list must not use full `config_json` path

**Files:**
- Create: `tests/integration/web/test_lab_page_shell_perf.py`
- Modify: `tests/unit/asteroid_lab/test_solver_run_lab_summary.py`

**Reviewer requirement:** RED test **first** — sentinel proves page path does not materialize full `config_json` / composed frames blob.

- [ ] **Step 1: Write failing unit test — `lab_run_summary_from_orm` not used by runs list**

Add to `tests/unit/asteroid_lab/test_solver_run_lab_summary.py`:

```python
from unittest.mock import patch

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)
from django_apps.asteroid_lab.services.solver_run_lab_summary import (
    lab_run_summary_from_orm,
    solver_runs_for_lab_project,
)


@pytest.mark.django_db
def test_solver_runs_for_lab_project_never_calls_lab_run_summary_from_orm(
    asteroid_project_factory,
) -> None:
    project = asteroid_project_factory()
    run = m.SolverRun.objects.create(
        project=project,
        status=m.SolverRun.RunStatus.COMPLETED,
        config_json={
            SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY: {
                "validation_passed": True,
                "confirmed_count": 1,
                "issue_codes": [],
                "issue_details": [],
            },
            SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY: [{"frame_index": 0, "sentinel": "X" * 5000}],
        },
    )
    with patch(
        "django_apps.asteroid_lab.services.solver_run_lab_summary.lab_run_summary_from_orm",
        side_effect=AssertionError("full config_json ORM path forbidden on runs list"),
    ) as from_orm_mock:
        runs = solver_runs_for_lab_project(int(project.pk), limit=10)
    from_orm_mock.assert_not_called()
    assert len(runs) == 1
    assert runs[0]["id"] == str(run.pk)
    assert runs[0]["validation_passed"] is True
```

- [ ] **Step 2: Run test — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_solver_run_lab_summary.py::test_solver_runs_for_lab_project_never_calls_lab_run_summary_from_orm -v --tb=short
```

Expected: **FAIL** — `AssertionError: full config_json ORM path forbidden` (current code calls `lab_run_summary_from_orm` per row).

- [ ] **Step 3: Write failing integration test — page GET + composed-frames sentinel**

Create `tests/integration/web/test_lab_page_shell_perf.py` (reuse helpers from `test_lab_replay_compose_defer.py` — `_client_run_solver`, fixtures):

```python
"""13F — project page shell must not materialize full config_json or ReplayFrame rows."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.test import Client, override_settings
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)
from django_apps.asteroid_lab.services.solver_run_lab_summary import lab_run_summary_from_orm

pytestmark = pytest.mark.django_db

_FROM_ORM_PATCH = (
    "django_apps.asteroid_lab.services.solver_run_lab_summary.lab_run_summary_from_orm"
)


@pytest.fixture(scope="module", autouse=True)
def _require_game_data(imported_game_data_batch_module):
    return imported_game_data_batch_module


def _inject_composed_frames_sentinel(run: m.SolverRun) -> None:
    config = dict(run.config_json or {})
    config[SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY] = [
        {"frame_index": i, "blob": "Z" * 8000} for i in range(200)
    ]
    if SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY not in config:
        config[SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY] = {
            "validation_passed": True,
            "confirmed_count": 0,
            "issue_codes": [],
            "issue_details": [],
        }
    run.config_json = config
    run.save(update_fields=["config_json"])


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_project_page_runs_path_forbids_lab_run_summary_from_orm(client: Client) -> None:
    from tests.integration.web.test_lab_replay_compose_defer import _client_run_solver

    slug, run_id, _proj = _client_run_solver(client)
    run = m.SolverRun.objects.get(pk=run_id)
    _inject_composed_frames_sentinel(run)
    with patch(_FROM_ORM_PATCH, side_effect=AssertionError("page runs path must not load full config_json")):
        resp = client.get(reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug}))
    assert resp.status_code == 200
```

- [ ] **Step 4: Run integration test — expect FAIL**

```powershell
python -m pytest tests/integration/web/test_lab_page_shell_perf.py::test_project_page_runs_path_forbids_lab_run_summary_from_orm -v --tb=short
```

Expected: **FAIL** with `page runs path must not load full config_json`.

---

## Task 2: GREEN — partial-read `solver_runs_for_lab_project`

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_run_lab_summary.py`

- [ ] **Step 1: Implement partial read (limit=10 unchanged)**

Replace body of `solver_runs_for_lab_project`:

```python
from django.db.models.fields.json import KeyTransform

from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)


def _ui_status_from_run_status(status: str) -> str:
    if status == m.SolverRun.RunStatus.COMPLETED:
        return "completed"
    if status == m.SolverRun.RunStatus.PARTIAL:
        return "partial"
    if status == m.SolverRun.RunStatus.FAILED:
        return "failed"
    return str(status)


def solver_runs_for_lab_project(project_id: int, *, limit: int = 10) -> list[dict[str, Any]]:
    """Latest solver runs for one project (newest first). Partial config_json read only."""

    summary_key = SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY
    rows = (
        m.SolverRun.objects.filter(project_id=int(project_id))
        .order_by("-created_at", "-id")[: int(limit)]
        .values(
            "pk",
            "status",
            KeyTransform(summary_key, "config_json"),
        )
    )
    out: list[dict[str, Any]] = []
    for row in rows:
        raw_summary = row.get(summary_key)
        summary = dict(raw_summary) if isinstance(raw_summary, dict) else {}
        out.append(
            lab_run_summary_from_solver_summary(
                run_id=int(row["pk"]),
                status=_ui_status_from_run_status(str(row["status"])),
                solver_summary=summary,
            )
        )
    return out
```

Keep `lab_run_summary_from_orm` unchanged for any other callers (grep before commit).

- [ ] **Step 2: Re-run Task 1 tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_solver_run_lab_summary.py::test_solver_runs_for_lab_project_never_calls_lab_run_summary_from_orm tests/integration/web/test_lab_page_shell_perf.py::test_project_page_runs_path_forbids_lab_run_summary_from_orm -v --tb=short
```

Expected: PASS.

- [ ] **Step 3: Run existing summary tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_solver_run_lab_summary.py -v --tb=short
```

Expected: PASS (including `test_solver_runs_for_lab_project_orders_newest_first`).

---

## Task 3: RED — track shell must not evaluate `ReplayFrame` queryset

**Files:**
- Modify: `tests/integration/web/test_lab_page_shell_perf.py`

**Reviewer requirement:** Forbid not only `prefetch_related("frames")` but **zero `ReplayFrame` queryset row evaluation** on page path (COUNT subquery via annotate is OK).

- [ ] **Step 1: Write failing test — no ReplayFrame row fetch**

Add to `test_lab_page_shell_perf.py`:

```python
from django.apps import apps
from django.test.utils import CaptureQueriesContext
from django.db import connection

from django_apps.asteroid_lab.models import ReplayFrame
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    get_latest_lab_replay_track_for_project,
)


@pytest.mark.django_db
def test_track_shell_helper_issues_no_replayframe_row_select(asteroid_project_factory) -> None:
    from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
        get_latest_lab_replay_track_shell_for_project,
    )

    project = asteroid_project_factory()
    with CaptureQueriesContext(connection) as ctx:
        get_latest_lab_replay_track_shell_for_project(int(project.pk))
    frame_table = ReplayFrame._meta.db_table
    for captured in ctx.captured_queries:
        sql = captured["sql"].lower()
        if frame_table.lower() in sql and "select" in sql:
            assert "count(" in sql or "count (*" in sql.replace("_", " "), (
                f"ReplayFrame row SELECT forbidden, got: {captured['sql']}"
            )


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_project_page_shell_does_not_prefetch_replay_frames(client: Client) -> None:
    from tests.integration.web.test_lab_replay_compose_defer import _client_run_solver

    slug, _run_id, proj = _client_run_solver(client)
    frame_table = ReplayFrame._meta.db_table
    with CaptureQueriesContext(connection) as ctx:
        resp = client.get(reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug}))
    assert resp.status_code == 200
    for captured in ctx.captured_queries:
        sql = captured["sql"].lower()
        if frame_table.lower() in sql and "select" in sql:
            assert "count(" in sql, f"ReplayFrame row SELECT on page GET: {captured['sql']}"
```

- [ ] **Step 2: Run shell helper test — expect FAIL**

```powershell
python -m pytest tests/integration/web/test_lab_page_shell_perf.py::test_track_shell_helper_issues_no_replayframe_row_select -v --tb=short
```

Expected: **FAIL** — `ImportError` or `AttributeError` (`get_latest_lab_replay_track_shell_for_project` missing) **or** FAIL on SQL assertion if mistakenly calling old helper.

- [ ] **Step 3: Run page GET test — expect FAIL**

```powershell
python -m pytest tests/integration/web/test_lab_page_shell_perf.py::test_project_page_shell_does_not_prefetch_replay_frames -v --tb=short
```

Expected: **FAIL** — page path still prefetches frame rows (SELECT without COUNT).

---

## Task 4: GREEN — track shell helper + wire `lab_page_context`

**Files:**
- Modify: `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py`
- Modify: `django_apps/web/services/asteroid_lab_page_context.py`

- [ ] **Step 1: Add dataclass / TypedDict and shell helper**

In `lab_replay_timeline_payload.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LabReplayTrackShell:
    id: int
    track_key: str
    frame_count: int


def get_latest_lab_replay_track_shell_for_project(project_id: int) -> LabReplayTrackShell | None:
    row = (
        ReplayTrack.objects.filter(project_id=int(project_id))
        .exclude(
            Q(track_key__startswith=RTTP_TRACK_KEY_PREFIX)
            | Q(track_key__endswith=RTTP_OPTIMIZATION_TRACK_SUFFIX)
        )
        .annotate(_frame_count=Count("frames"))
        .filter(_frame_count__gt=0)
        .order_by("-created_at", "-id")
        .values("pk", "track_key", "_frame_count")
        .first()
    )
    if not row:
        return None
    return LabReplayTrackShell(
        id=int(row["pk"]),
        track_key=str(row["track_key"]),
        frame_count=int(row["_frame_count"]),
    )
```

Export in `__all__`. **Do not** change `get_latest_lab_replay_track_for_project` (compose / GET paths).

- [ ] **Step 2: Switch `lab_page_context` to shell helper**

In `asteroid_lab_page_context.py`:

- Import `get_latest_lab_replay_track_shell_for_project`, `LabReplayTrackShell`.
- Replace `get_latest_lab_replay_track_for_project` with shell helper inside `perf_span("track_lookup_ms")` (rename span from `get_latest_lab_replay_track_ms` or record both for backward compat — prefer **`track_lookup_ms`** per spec).
- Set `ctx["lab_replay_track_id"]` / `lab_replay_track_key` from shell.
- Wrap `solver_runs_for_lab_project` with nested spans: `runs_query_ms` + `runs_materialize_ms` (or single outer `solver_runs_for_lab_project_ms` plus inner keys — implementation choice: **split** inside `solver_run_lab_summary` via optional perf callbacks or inline in page context before/after call).
- After runs built: `record_perf_meta(runs_json_bytes=serialized_json_utf8_bytes(runs))`.
- Lazy branch: `record_perf_meta(replay_manifest_cache_hit=..., page_shell_cache_hit=False)`.

- [ ] **Step 3: Re-run Task 3 tests**

```powershell
python -m pytest tests/integration/web/test_lab_page_shell_perf.py -v --tb=short
```

Expected: PASS.

- [ ] **Step 4: 13C2-lite regression**

```powershell
python -m pytest tests/integration/web/test_lab_replay_compose_defer.py -k "project_page_lazy" -v --tb=short
```

Expected: PASS (compose still skipped on cache-hit).

---

## Task 5: Perf trace — SQL wrapper + json_script sizing

**Files:**
- Modify: `django_apps/asteroid_lab/observability/lab_perf_trace.py`
- Modify: `django_apps/web/views/public_pages.py`

- [ ] **Step 1: SQL execute wrapper (trace-active only)**

In `lab_perf_trace.py`, add context manager used by `lab_perf_trace_request`:

```python
@contextmanager
def perf_sql_trace() -> Iterator[None]:
    if _active is None:
        yield
        return
    from django.db import connection

    count = 0
    total_ms = 0.0
    largest_ms = 0.0

    def wrapper(execute, sql, params, many, context):
        nonlocal count, total_ms, largest_ms
        t0 = time.monotonic()
        try:
            return execute(sql, params, many, context)
        finally:
            elapsed = (time.monotonic() - t0) * 1000.0
            count += 1
            total_ms += elapsed
            if elapsed > largest_ms:
                largest_ms = elapsed

    with connection.execute_wrapper(wrapper):
        yield
    record_perf_meta(
        sql_query_count=count,
        sql_total_ms=total_ms,
        largest_query_ms=largest_ms,
    )
```

Nest inside `lab_perf_trace_request` when enabled.

- [ ] **Step 2: `record_json_script_bytes` helper**

```python
_LAB_JSON_SCRIPT_CONTEXT_KEYS: dict[str, str] = {
    "lab-cell-overlay-matrix-data": "lab_cell_overlay_matrix",
    "lab-runs-data": "runs",
    "lab-ui-initial-state": "lab_ui_initial",
    "lab-replay-frames-data": "lab_replay_frames_json",
    "lab-replay-track-metrics-data": "replay_track_metrics",
    "lab-replay-manifest-data": "lab_replay_manifest_json",
    "lab-identifier-sprite-paths-data": "lab_identifier_sprite_paths",
}


def measure_lab_json_script_bytes(page_ctx: dict[str, Any]) -> None:
    by_id: dict[str, int] = {}
    total = 0
    for script_id, ctx_key in _LAB_JSON_SCRIPT_CONTEXT_KEYS.items():
        nbytes = serialized_json_utf8_bytes(page_ctx.get(ctx_key))
        by_id[script_id] = nbytes
        total += nbytes
    record_perf_meta(json_script_bytes_by_id=by_id, json_script_bytes_total=total)
```

- [ ] **Step 3: Wire `asteroid_miner_layout_project`**

```python
with lab_perf_trace_request(request_kind="project_page", project_slug=str(project.slug)):
    with perf_sql_trace():
        with perf_span("lab_page_context_ms"):
            page_ctx = _asteroid_miner_lab_page_context(blueprint_code, project=project)
        measure_lab_json_script_bytes(page_ctx)
        record_perf_meta(
            frame_count=int(page_ctx.get("total_frames") or 0),
            has_replay_frames=bool(page_ctx.get("has_replay_frames")),
            track_frames_loaded_count=0,
            track_frames_prefetched=False,
            page_shell_cache_hit=False,
        )
        with perf_span("template_render_ms"):
            response = render(request, "web/asteroid_miner_layout_solver.html", page_ctx)
        record_perf_meta(html_bytes=len(response.content))
        return response
```

Ensure `replay_manifest_cache_hit` is set inside `lab_page_context` (lazy path).

- [ ] **Step 4: Unit test — 13F keys present**

Extend `tests/unit/asteroid_lab/test_lab_perf_trace.py`:

```python
@override_settings(ASTEROID_LAB_PERF_TRACE=True)
def test_lab_perf_trace_project_page_emits_13f_keys(perf_log_path: Path) -> None:
    from django_apps.asteroid_lab.observability.lab_perf_trace import (
        measure_lab_json_script_bytes,
        perf_sql_trace,
    )

    with lab_perf_trace_request(request_kind="project_page", project_slug="demo"):
        with perf_sql_trace():
            with perf_span("template_render_ms"):
                measure_lab_json_script_bytes({"runs": [], "lab_ui_initial": {}})
            record_perf_meta(
                track_frames_loaded_count=0,
                track_frames_prefetched=False,
                replay_manifest_cache_hit=False,
                page_shell_cache_hit=False,
            )
    record = json.loads(perf_log_path.read_text(encoding="utf-8").strip().splitlines()[-1])
    for key in (
        "template_render_ms",
        "sql_query_count",
        "json_script_bytes_total",
        "json_script_bytes_by_id",
        "track_frames_loaded_count",
        "page_shell_cache_hit",
    ):
        assert key in record
    assert record["track_frames_loaded_count"] == 0
    assert record["page_shell_cache_hit"] is False
```

- [ ] **Step 5: Run perf unit tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_perf_trace.py -v --tb=short
```

Expected: PASS.

---

## Task 6: Iteration gate + manual perf verification

**Files:** none (commands only)

- [ ] **Step 1: Narrow pytest gate**

```powershell
python -m pytest tests/integration/web/test_lab_page_shell_perf.py tests/integration/web/test_lab_replay_compose_defer.py tests/unit/asteroid_lab/test_lab_perf_trace.py tests/unit/asteroid_lab/test_solver_run_lab_summary.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/observability/lab_perf_trace.py django_apps/asteroid_lab/services/solver_run_lab_summary.py django_apps/asteroid_lab/services/lab_replay_timeline_payload.py django_apps/web/services/asteroid_lab_page_context.py django_apps/web/views/public_pages.py tests/integration/web/test_lab_page_shell_perf.py
```

- [ ] **Step 2: Manual perf — warm cache-hit line**

1. Run solver once on reference slug (e.g. `rttp-core-recovery-test-map`).
2. Second GET project page.
3. Read last line of `var/log/asteroid_lab_perf/lab_perf.jsonl`.

**Check:**

| Field | Expectation |
|-------|-------------|
| `build_lab_replay_frames_for_project_ms` | absent on cache-hit |
| `replay_manifest_cache_hit` | `true` |
| `page_shell_cache_hit` | `false` |
| `track_frames_loaded_count` | `0` |
| `runs_json_bytes` + `json_script_bytes_by_id` | present |
| `total_ms` | soft &lt; 1000; if not, some phase/meta &gt; 250 |

- [ ] **Step 3: HTML size**

Confirm `html_bytes` &lt; 500_000 and `len(runs)` in rendered JSON still up to 10 (grep `lab-runs-data` in response or trust SSR tests).

---

## Task 7: Docs and full gate

**Files:**
- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/specs/2026-05-29-lab-page-ttfb-breakdown-shell-only-design.md` — set **Status: Implemented** when done

- [ ] **Step 1: `current_plan.md`** — 13F row note + CLOSED date when merged.

- [ ] **Step 2: Full gate (pre-PR)**

```powershell
powershell -File scripts/test_full.ps1
python -m ruff check .
python -m mypy django_apps config src
python -m black --check .
```

- [ ] **Step 3: Commit** (only when user requests)

```text
perf(web): 13F project page TTFB breakdown and shell-only SSR reads
```

---

## Plan self-review (spec coverage)

| Spec § | Task |
|--------|------|
| §4 Page shell contract | Tasks 2, 4 |
| §5 Forbidden SSR reads | Tasks 1–4 RED/GREEN |
| §6 Instrumentation | Task 5 |
| §7 Remediation | Tasks 2, 4 |
| §8 AC — instrumentation | Task 5–6 |
| §8 AC — shell remediation | Tasks 1–4 |
| §8 AC — runs limit 10 | Task 2 (`limit=10`); no test changing limit |
| §8 AC — run-count shortcut forbidden | Task 1 RED + explicit AC in tests |
| §8 AC — compose cache-hit | Task 4 step 4 |
| §9 Non-goals | Header out-of-scope |
| §10 Follow-up 13H | Header only |
| Reviewer: RED sentinel first | **Task 1 before Task 2** |
| Reviewer: ReplayFrame eval 0 | **Task 3 before Task 4** |

No TBD placeholders in task steps.

---

## Execution handoff

**Plan saved to** `docs/superpowers/plans/2026-05-29-lab-page-ttfb-breakdown-shell-only.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — run tasks in this session with executing-plans checkpoints  

Which approach do you want?
