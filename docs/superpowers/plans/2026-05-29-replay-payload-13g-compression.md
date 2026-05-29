# PR-13G — GZip Transport Compression Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable Django `GZipMiddleware` so large JSON responses (especially `GET …/lab-replay/`) are compressed when the client accepts `gzip`, without changing JSON semantics.

**Architecture:** Insert `django.middleware.gzip.GZipMiddleware` after `WhiteNoiseMiddleware` and before `SessionMiddleware` in `config/settings.py`. Add integration tests that set `HTTP_ACCEPT_ENCODING=gzip` and assert `Content-Encoding` plus decoded JSON equivalence.

**Tech Stack:** Django 5.x, pytest-django, ruff, mypy `django_apps config src`

**Spec:** [`docs/superpowers/specs/2026-05-29-replay-payload-network-optimization-design.md`](../specs/2026-05-29-replay-payload-network-optimization-design.md)

**Prerequisite:** PR-13D-SSR merged (optional but recommended — smaller HTML baseline)

**Branch:** `feat/replay-payload-13g-compression`

---

## File map

| Action | Path |
|--------|------|
| Modify | `config/settings.py` |
| Create | `tests/integration/web/test_lab_replay_gzip_compression.py` |
| Modify | `documents/ai/manuals/environment.md` | Note gzip is always on (no env flag) |

---

### Task 1: Failing gzip tests

**Files:**
- Create: `tests/integration/web/test_lab_replay_gzip_compression.py`

- [ ] **Step 1: Write tests**

```python
"""GZip transport for lab-replay GET (Sequence 13G)."""

from __future__ import annotations

import gzip
import json

import pytest
from django.test import Client
from django.urls import reverse

from tests.integration.web.test_asteroid_miner_layout_solver import _unique_valid_copy

pytestmark = pytest.mark.django_db


def _lab_replay_url(client: Client) -> str:
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    resp = client.post(create_url, {"copy_code": _unique_valid_copy()}, follow=True)
    assert resp.status_code == 200
    slug = resp.wsgi_request.path.split("/p/")[1].split("/")[0]
    run_url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
    run_body = json.loads(client.post(run_url, HTTP_ACCEPT="application/json").content)
    run_id = run_body["solver_run_id"]
    return reverse(
        "web:asteroid-miner-layout-project-solver-run-lab-replay",
        kwargs={"slug": slug, "run_id": int(run_id)},
    )


def test_lab_replay_get_content_encoding_gzip(client: Client) -> None:
    url = _lab_replay_url(client)
    resp = client.get(url, HTTP_ACCEPT_ENCODING="gzip")
    assert resp.status_code == 200
    assert resp.get("Content-Encoding") == "gzip"
    raw = resp.content
    decoded = gzip.decompress(raw)
    data = json.loads(decoded.decode("utf-8"))
    assert isinstance(data.get("frames"), list)
    assert data.get("frame_count") == len(data["frames"])


def test_lab_replay_get_without_gzip_accept_still_json(client: Client) -> None:
    url = _lab_replay_url(client)
    resp = client.get(url)
    assert resp.status_code == 200
    assert resp.get("Content-Encoding") in (None, "")
    data = json.loads(resp.content.decode("utf-8"))
    assert "frames" in data
```

- [ ] **Step 2: Run — expect FAIL**

```powershell
python -m pytest tests/integration/web/test_lab_replay_gzip_compression.py -v --tb=short
```

Expected: FAIL — no `Content-Encoding: gzip`.

---

### Task 2: Enable middleware

**Files:**
- Modify: `config/settings.py`

- [ ] **Step 1: Insert middleware**

Change `MIDDLEWARE` to:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

- [ ] **Step 2: Run tests — expect PASS**

```powershell
python -m pytest tests/integration/web/test_lab_replay_gzip_compression.py -v --tb=short
```

If `Content-Encoding` still missing, confirm response body length ≥ 200 bytes (Django minimum). Fixture with few frames may be small — use project with run-solver + full replay or lower threshold test only when `len(content) >= 200`.

- [ ] **Step 3: Commit**

```powershell
git add config/settings.py tests/integration/web/test_lab_replay_gzip_compression.py
git commit -m "feat(config): enable GZipMiddleware for lab replay responses"
```

---

### Task 3: Docs + gate

- [ ] **Step 1:** Add note to `documents/ai/manuals/environment.md` — gzip enabled globally via middleware (no env var).

- [ ] **Step 2:**

```powershell
python -m pytest tests/integration/web/test_lab_replay_gzip_compression.py -v --tb=short
python -m ruff check config/settings.py tests/integration/web/test_lab_replay_gzip_compression.py
```

- [ ] **Step 3: Commit docs**

```powershell
git add documents/ai/manuals/environment.md
git commit -m "docs: note GZipMiddleware for replay transport (13G)"
```

---

## Plan self-review

| Spec §13G | Task |
|-----------|------|
| GZipMiddleware order | Task 2 |
| lab-replay GET gzip | Task 1 |
| Semantic unchanged | Task 1 decode assert |
| No gzip client OK | Task 1 second test |

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-29-replay-payload-13g-compression.md`. Run **after** 13D-SSR or in parallel on separate branch.
