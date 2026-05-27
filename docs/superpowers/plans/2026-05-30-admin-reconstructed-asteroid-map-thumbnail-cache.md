# Admin Reconstructed Asteroid Map Thumbnail Cache — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `ReconstructedAsteroidMap` changelist dense HTML mini-maps with cached WebP/PNG thumbnails so list render cost is O(page rows), not O(page rows × W×H).

**Architecture:** Pure `admin_map_list_thumbnail` raster module (Pillow color-blocks, optional `cairosvg` enhancement) + `reconstructed_map_thumbnail_service` sync (hash/version invalidation, `QuerySet.update` metadata, no recursive save) + model `ImageField` + admin changelist `<img>` with JSON defer on changelist only.

**Tech Stack:** Django 5.x, Pillow 11+, optional `cairosvg`, pytest-django, ruff, black, mypy `django_apps config src`

**Spec:** [`docs/superpowers/specs/2026-05-30-admin-reconstructed-asteroid-map-thumbnail-cache-design.md`](../specs/2026-05-30-admin-reconstructed-asteroid-map-thumbnail-cache-design.md)

**Branch:** `feat/admin-reconstructed-map-thumbnail-cache` (worktree recommended)

**Out of scope:** `GeneticSample` admin, detail `mini_map_preview` replacement, JPG, solver/replay consumption of thumbnails

**Plan status:** APPROVED AFTER BLOCKER FIXES (2026-05-30). Mandatory patches in Tasks 1, 4, 5:
1. `QuerySet.update(admin_list_thumbnail=thumbnail_name, ...)` after `FileField.save(..., save=False)`
2. `sync_admin_list_thumbnail` catches thumbnail render/storage errors; never fails primary persist
3. Crop window clamped to tight bbox `max_x`/`max_y`

**Execution:** Subagent-Driven recommended (Tasks 1–2 renderer → 3–5 model/service/persist → 6–7 admin/command).

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `django_apps/asteroid_lab/admin_map_list_thumbnail.py` | Constants, canonical hash, bbox cap, Pillow raster |
| Create | `django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py` | Sync/clear/regen; `update_fields` persistence |
| Modify | `django_apps/asteroid_lab/models.py` | Thumbnail + metadata fields |
| Create | `django_apps/asteroid_lab/migrations/00XX_reconstructed_map_admin_thumbnail.py` | Schema |
| Modify | `django_apps/asteroid_lab/services/reconstructed_asteroid_service.py` | Call thumbnail sync after persist |
| Modify | `django_apps/asteroid_lab/admin.py` | Changelist img, defer, actions |
| Create | `django_apps/asteroid_lab/management/commands/regenerate_reconstructed_map_thumbnails.py` | Backfill CLI |
| Create | `tests/unit/asteroid_lab/test_admin_map_list_thumbnail.py` | Hash, raster, cap unit tests |
| Create | `tests/unit/asteroid_lab/test_reconstructed_map_thumbnail_service.py` | Sync/skip/clear |
| Create | `tests/unit/asteroid_lab/test_reconstructed_map_admin_changelist.py` | Changelist HTML + defer |
| Modify | `tests/unit/asteroid_lab/test_reconstructed_asteroid_persist.py` | Thumbnail created on persist |
| Modify | `documents/ai/lab_map_rendering_contract.md` | Admin list thumbnail vs HTML minimap note |

---

### Task 0: Branch and baseline

**Files:** none

- [ ] **Step 1: Create branch**

```powershell
git checkout master
git pull
git checkout -b feat/admin-reconstructed-map-thumbnail-cache
```

- [ ] **Step 2: Baseline narrow tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_genetic_sample_mini_map.py tests/unit/asteroid_lab/test_reconstructed_asteroid_persist.py -v --tb=short
```

Expected: PASS (existing behavior before edits).

---

### Task 1: Canonical hash and constants (TDD)

**Files:**
- Create: `django_apps/asteroid_lab/admin_map_list_thumbnail.py`
- Create: `tests/unit/asteroid_lab/test_admin_map_list_thumbnail.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/asteroid_lab/test_admin_map_list_thumbnail.py`:

```python
"""Admin list thumbnail — hash, bbox cap, raster bytes."""

from __future__ import annotations

from django_apps.asteroid_lab.admin_map_list_thumbnail import (
    ADMIN_LIST_THUMBNAIL_RENDERER_VERSION,
    canonical_decoded_json_hash,
    compute_list_thumbnail_window,
)


def test_canonical_hash_stable_key_order() -> None:
    a = {"BP": {"Entries": []}, "V": 1}
    b = {"V": 1, "BP": {"Entries": []}}
    assert canonical_decoded_json_hash(a) == canonical_decoded_json_hash(b)


def test_canonical_hash_changes_when_entries_change() -> None:
    base = {"V": 1, "BP": {"Entries": [{"X": 1, "Y": 1, "T": "SpaceBelt_Forward", "R": 0}]}}
    other = {"V": 1, "BP": {"Entries": [{"X": 2, "Y": 1, "T": "SpaceBelt_Forward", "R": 0}]}}
    assert canonical_decoded_json_hash(base) != canonical_decoded_json_hash(other)


def test_compute_window_caps_at_48_and_sets_truncated() -> None:
    entries = [{"X": x, "Y": 0, "T": "SpaceBelt_Forward", "R": 0} for x in range(1, 80)]
    decoded = {"V": 1, "BP": {"$type": "Island", "Entries": entries}}
    win = compute_list_thumbnail_window(decoded)
    assert win is not None
    assert win.grid_w <= 48
    assert win.truncated is True


def test_compute_window_crop_stays_inside_tight_bbox() -> None:
    entries = [{"X": x, "Y": 1, "T": "SpaceBelt_Forward", "R": 0} for x in range(1, 80)]
    decoded = {"V": 1, "BP": {"$type": "Island", "Entries": entries}}
    win = compute_list_thumbnail_window(decoded)
    assert win is not None
    assert win.min_x >= 1
    assert win.min_x + win.grid_w - 1 <= 79
    assert win.min_y >= 1
    assert win.min_y + win.grid_h - 1 <= 1


def test_renderer_version_is_non_empty() -> None:
    assert ADMIN_LIST_THUMBNAIL_RENDERER_VERSION
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
python -m pytest tests/unit/asteroid_lab/test_admin_map_list_thumbnail.py -v --tb=short
```

Expected: FAIL (`ModuleNotFoundError` or missing attributes).

- [ ] **Step 3: Implement minimal module**

Create `django_apps/asteroid_lab/admin_map_list_thumbnail.py`:

```python
"""Raster admin changelist thumbnails for reconstructed maps (display-only)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
    build_decoded_blueprint_snapshot,
)

ADMIN_LIST_THUMBNAIL_RENDERER_VERSION = "1"
ADMIN_LIST_THUMBNAIL_MAX_GRID = 48
ADMIN_LIST_THUMBNAIL_MAX_EDGE_PX = 256

_CELL_KIND_FILL: dict[str, tuple[int, int, int]] = {
    "space_belt": (51, 65, 85),
    "space_pipe": (14, 165, 233),
    "shape_miner": (245, 158, 11),
    "shape_miner_extension": (217, 119, 6),
    "fluid_miner": (56, 189, 248),
    "fluid_miner_extension": (2, 132, 199),
    "unknown": (100, 116, 139),
}
_BG_RGB = (15, 23, 42)


def canonical_decoded_json_hash(decoded_json: dict[str, Any]) -> str:
    payload = json.dumps(decoded_json, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ListThumbnailWindow:
    min_x: int
    min_y: int
    grid_w: int
    grid_h: int
    truncated: bool
    cell_count: int


def compute_list_thumbnail_window(decoded_json: dict[str, Any]) -> ListThumbnailWindow | None:
    if not decoded_json or not isinstance(decoded_json.get("BP"), dict):
        return None
    snap = build_decoded_blueprint_snapshot(decoded_json)
    bbox = snap.bbox_json
    if not bbox or int(bbox.get("width", 0)) < 1 or int(bbox.get("height", 0)) < 1:
        return None
    bbox_min_x = int(bbox["min_x"])
    bbox_min_y = int(bbox["min_y"])
    bbox_max_x = int(bbox["max_x"])
    bbox_max_y = int(bbox["max_y"])
    min_x = bbox_min_x
    min_y = bbox_min_y
    w = int(bbox["width"])
    h = int(bbox["height"])
    truncated = w > ADMIN_LIST_THUMBNAIL_MAX_GRID or h > ADMIN_LIST_THUMBNAIL_MAX_GRID
    if truncated:
        cap = ADMIN_LIST_THUMBNAIL_MAX_GRID
        cx = sum(c.x for c in snap.cells) // max(len(snap.cells), 1)
        cy = sum(c.y for c in snap.cells) // max(len(snap.cells), 1)
        min_x = max(bbox_min_x, min(cx - cap // 2, bbox_max_x - cap + 1))
        min_y = max(bbox_min_y, min(cy - cap // 2, bbox_max_y - cap + 1))
        w = min(cap, bbox_max_x - min_x + 1)
        h = min(cap, bbox_max_y - min_y + 1)
    return ListThumbnailWindow(
        min_x=min_x,
        min_y=min_y,
        grid_w=w,
        grid_h=h,
        truncated=truncated,
        cell_count=len(snap.cells),
    )
```

(Add `render_list_thumbnail_png_bytes` in Task 2.)

- [ ] **Step 4: Run tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_admin_map_list_thumbnail.py -v --tb=short
```

Expected: PASS for hash/window tests.

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/admin_map_list_thumbnail.py tests/unit/asteroid_lab/test_admin_map_list_thumbnail.py
git commit -m "feat(asteroid_lab): add admin list thumbnail hash and bbox window"
```

---

### Task 2: Color-block raster (TDD)

**Files:**
- Modify: `django_apps/asteroid_lab/admin_map_list_thumbnail.py`
- Modify: `tests/unit/asteroid_lab/test_admin_map_list_thumbnail.py`

- [ ] **Step 1: Add failing raster test**

Append to `tests/unit/asteroid_lab/test_admin_map_list_thumbnail.py`:

```python
from django_apps.asteroid_lab.admin_map_list_thumbnail import render_list_thumbnail_image_bytes


def test_render_list_thumbnail_returns_webp_or_png_bytes() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 1, "T": "SpaceBelt_Forward", "R": 0},
                {"X": 2, "Y": 1, "T": "Layout_ShapeMiner", "R": 0},
            ],
        },
    }
    data, ext = render_list_thumbnail_image_bytes(decoded)
    assert ext in ("webp", "png")
    assert len(data) > 64
```

- [ ] **Step 2: Run test — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_admin_map_list_thumbnail.py::test_render_list_thumbnail_returns_webp_or_png_bytes -v --tb=short
```

- [ ] **Step 3: Implement raster**

Add to `admin_map_list_thumbnail.py`:

```python
from io import BytesIO

from django_apps.asteroid_lab.services.dto import DecodedCellDTO


def _fill_for_cell(cell: DecodedCellDTO) -> tuple[int, int, int]:
    if cell.cell_kind in _CELL_KIND_FILL:
        return _CELL_KIND_FILL[cell.cell_kind]
    t = (cell.tile_type or "").strip()
    if t.startswith("SpaceBelt"):
        return _CELL_KIND_FILL["space_belt"]
    if t.startswith("SpacePipe"):
        return _CELL_KIND_FILL["space_pipe"]
    return _CELL_KIND_FILL["unknown"]


def render_list_thumbnail_image_bytes(
    decoded_json: dict[str, Any],
) -> tuple[bytes, str]:
    """Return (image_bytes, extension) where extension is webp or png."""

    from PIL import Image  # noqa: PLC0415

    win = compute_list_thumbnail_window(decoded_json)
    if win is None:
        msg = "decoded_json not drawable for list thumbnail"
        raise ValueError(msg)
    snap = build_decoded_blueprint_snapshot(decoded_json)
    cell_px = max(
        4,
        min(
            32,
            ADMIN_LIST_THUMBNAIL_MAX_EDGE_PX // max(win.grid_w, win.grid_h),
        ),
    )
    gap = 1
    img_w = win.grid_w * cell_px + (win.grid_w - 1) * gap
    img_h = win.grid_h * cell_px + (win.grid_h - 1) * gap
    img = Image.new("RGB", (img_w, img_h), _BG_RGB)
    by_xy: dict[tuple[int, int], DecodedCellDTO] = {
        (c.x, c.y): c for c in snap.cells
    }
    for gy in range(win.grid_h):
        for gx in range(win.grid_w):
            x = win.min_x + gx
            y = win.min_y + gy
            cell = by_xy.get((x, y))
            if cell is None:
                continue
            left = gx * (cell_px + gap)
            top = (win.grid_h - 1 - gy) * (cell_px + gap)
            color = _fill_for_cell(cell)
            for px in range(left, left + cell_px):
                for py in range(top, top + cell_px):
                    img.putpixel((px, py), color)
    buf = BytesIO()
    try:
        img.save(buf, format="WEBP", lossless=True)
        return buf.getvalue(), "webp"
    except OSError:
        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue(), "png"
```

Optional enhancement (same task, non-blocking): try `cairosvg` inside a helper; on any error, keep color-block path above.

- [ ] **Step 4: Run tests — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_admin_map_list_thumbnail.py -v --tb=short
```

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/admin_map_list_thumbnail.py tests/unit/asteroid_lab/test_admin_map_list_thumbnail.py
git commit -m "feat(asteroid_lab): render admin list thumbnail color-block raster"
```

---

### Task 3: Model fields and migration

**Files:**
- Modify: `django_apps/asteroid_lab/models.py`
- Create: migration via `makemigrations`

- [ ] **Step 1: Add fields to `ReconstructedAsteroidMap`**

After `decoded_json` field in `models.py`:

```python
    admin_list_thumbnail = models.ImageField(
        upload_to="reconstructed_maps/list/%Y/%m/",
        blank=True,
        verbose_name="Admin changelist thumbnail",
    )
    admin_list_thumbnail_hash = models.CharField(max_length=64, blank=True)
    admin_list_thumbnail_renderer_version = models.CharField(max_length=16, blank=True)
    admin_list_thumbnail_cell_count = models.PositiveIntegerField(default=0)
    admin_list_thumbnail_grid_w = models.PositiveSmallIntegerField(default=0)
    admin_list_thumbnail_grid_h = models.PositiveSmallIntegerField(default=0)
    admin_list_thumbnail_truncated = models.BooleanField(default=False)
```

- [ ] **Step 2: Create migration**

```powershell
python manage.py makemigrations asteroid_lab --name reconstructed_map_admin_thumbnail
```

- [ ] **Step 3: Apply migration locally**

```powershell
python manage.py migrate asteroid_lab
```

- [ ] **Step 4: Commit**

```bash
git add django_apps/asteroid_lab/models.py django_apps/asteroid_lab/migrations/
git commit -m "feat(asteroid_lab): add admin list thumbnail fields on ReconstructedAsteroidMap"
```

---

### Task 4: Thumbnail sync service (TDD)

**Files:**
- Create: `django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py`
- Create: `tests/unit/asteroid_lab/test_reconstructed_map_thumbnail_service.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/asteroid_lab/test_reconstructed_map_thumbnail_service.py`:

```python
"""Thumbnail sync — hash skip, regen, clear, failure containment."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.admin_map_list_thumbnail import (
    ADMIN_LIST_THUMBNAIL_RENDERER_VERSION,
    canonical_decoded_json_hash,
)
from django_apps.asteroid_lab.services.reconstructed_map_thumbnail_service import (
    clear_admin_list_thumbnail,
    sync_admin_list_thumbnail,
)


@pytest.fixture
def reconstructed_row(db: None) -> m.ReconstructedAsteroidMap:
    proj = m.AsteroidProject.objects.create(name="ThumbProj", slug="thumb-proj")
    inp = m.AsteroidMapInput.objects.create(
        project=proj,
        copy_code="",
        source_kind=m.AsteroidMapInput.SourceKind.COPY_CODE,
    )
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [{"X": 1, "Y": 1, "T": "SpaceBelt_Forward", "R": 0}],
        },
    }
    return m.ReconstructedAsteroidMap.objects.create(
        map_input=inp,
        project=proj,
        run_key="rk-thumb",
        decoded_json=decoded,
    )


@pytest.mark.django_db
def test_sync_creates_thumbnail_and_db_path(reconstructed_row: m.ReconstructedAsteroidMap) -> None:
    assert sync_admin_list_thumbnail(reconstructed_row) is True
    reconstructed_row.refresh_from_db()
    assert reconstructed_row.admin_list_thumbnail.name
    assert reconstructed_row.admin_list_thumbnail_hash == canonical_decoded_json_hash(
        dict(reconstructed_row.decoded_json)
    )
    assert reconstructed_row.admin_list_thumbnail_renderer_version == (
        ADMIN_LIST_THUMBNAIL_RENDERER_VERSION
    )


@pytest.mark.django_db
def test_sync_skips_when_hash_and_version_match(reconstructed_row: m.ReconstructedAsteroidMap) -> None:
    sync_admin_list_thumbnail(reconstructed_row)
    reconstructed_row.refresh_from_db()
    name_before = reconstructed_row.admin_list_thumbnail.name
    assert sync_admin_list_thumbnail(reconstructed_row) is False
    reconstructed_row.refresh_from_db()
    assert reconstructed_row.admin_list_thumbnail.name == name_before


@pytest.mark.django_db
def test_sync_with_force_regenerates(reconstructed_row: m.ReconstructedAsteroidMap) -> None:
    sync_admin_list_thumbnail(reconstructed_row)
    reconstructed_row.refresh_from_db()
    assert sync_admin_list_thumbnail(reconstructed_row, force=True) is True
    reconstructed_row.refresh_from_db()
    assert reconstructed_row.admin_list_thumbnail.name
    assert reconstructed_row.admin_list_thumbnail_hash


@pytest.mark.django_db
def test_clear_removes_thumbnail_fields(reconstructed_row: m.ReconstructedAsteroidMap) -> None:
    sync_admin_list_thumbnail(reconstructed_row)
    clear_admin_list_thumbnail(int(reconstructed_row.pk))
    reconstructed_row.refresh_from_db()
    assert not reconstructed_row.admin_list_thumbnail
    assert reconstructed_row.admin_list_thumbnail_hash == ""


@pytest.mark.django_db
def test_sync_render_failure_clears_and_does_not_raise(
    reconstructed_row: m.ReconstructedAsteroidMap,
) -> None:
    with patch(
        "django_apps.asteroid_lab.services.reconstructed_map_thumbnail_service.render_list_thumbnail_image_bytes",
        side_effect=ValueError("render failed"),
    ):
        assert sync_admin_list_thumbnail(reconstructed_row) is True
    reconstructed_row.refresh_from_db()
    assert not reconstructed_row.admin_list_thumbnail
```

- [ ] **Step 2: Run tests — FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_reconstructed_map_thumbnail_service.py -v --tb=short
```

- [ ] **Step 3: Implement service**

Create `django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py`:

```python
"""Admin changelist thumbnails for ReconstructedAsteroidMap (display-only)."""

from __future__ import annotations

import logging

from django.core.files.base import ContentFile

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.admin_map_list_thumbnail import (
    ADMIN_LIST_THUMBNAIL_RENDERER_VERSION,
    canonical_decoded_json_hash,
    compute_list_thumbnail_window,
    render_list_thumbnail_image_bytes,
)

logger = logging.getLogger(__name__)

_THUMBNAIL_ERRORS: tuple[type[BaseException], ...] = (ValueError, OSError)


def _try_import_pil_errors() -> tuple[type[BaseException], ...]:
    try:
        from PIL import UnidentifiedImageError  # noqa: PLC0415

        return _THUMBNAIL_ERRORS + (UnidentifiedImageError,)
    except ImportError:
        return _THUMBNAIL_ERRORS


def clear_admin_list_thumbnail(pk: int) -> None:
    row = m.ReconstructedAsteroidMap.objects.filter(pk=int(pk)).first()
    if row is None:
        return
    if row.admin_list_thumbnail:
        row.admin_list_thumbnail.delete(save=False)
    m.ReconstructedAsteroidMap.objects.filter(pk=int(pk)).update(
        admin_list_thumbnail="",
        admin_list_thumbnail_hash="",
        admin_list_thumbnail_renderer_version="",
        admin_list_thumbnail_cell_count=0,
        admin_list_thumbnail_grid_w=0,
        admin_list_thumbnail_grid_h=0,
        admin_list_thumbnail_truncated=False,
    )


def _persist_thumbnail_metadata(
    *,
    pk: int,
    thumbnail_name: str,
    new_hash: str,
    win: object,
) -> None:
    m.ReconstructedAsteroidMap.objects.filter(pk=int(pk)).update(
        admin_list_thumbnail=thumbnail_name,
        admin_list_thumbnail_hash=new_hash,
        admin_list_thumbnail_renderer_version=ADMIN_LIST_THUMBNAIL_RENDERER_VERSION,
        admin_list_thumbnail_cell_count=win.cell_count,
        admin_list_thumbnail_grid_w=win.grid_w,
        admin_list_thumbnail_grid_h=win.grid_h,
        admin_list_thumbnail_truncated=win.truncated,
    )


def sync_admin_list_thumbnail(
    row: m.ReconstructedAsteroidMap,
    *,
    force: bool = False,
) -> bool:
    """Generate thumbnail when hash/version mismatch. Never raises to callers."""

    decoded = dict(row.decoded_json or {})
    new_hash = canonical_decoded_json_hash(decoded) if decoded else ""
    if (
        not force
        and row.admin_list_thumbnail
        and row.admin_list_thumbnail_hash == new_hash
        and row.admin_list_thumbnail_renderer_version == ADMIN_LIST_THUMBNAIL_RENDERER_VERSION
    ):
        return False
    if not decoded:
        clear_admin_list_thumbnail(int(row.pk))
        return True
    win = compute_list_thumbnail_window(decoded)
    if win is None:
        clear_admin_list_thumbnail(int(row.pk))
        return True
    try:
        data, ext = render_list_thumbnail_image_bytes(decoded)
        name = f"recon_map_{row.pk}_{new_hash[:12]}.{ext}"
        row.admin_list_thumbnail.save(name, ContentFile(data), save=False)
        thumbnail_name = row.admin_list_thumbnail.name
        if not thumbnail_name:
            raise OSError("thumbnail save produced empty name")
        _persist_thumbnail_metadata(pk=int(row.pk), thumbnail_name=thumbnail_name, new_hash=new_hash, win=win)
    except _try_import_pil_errors() as exc:
        logger.warning(
            "Failed admin list thumbnail for ReconstructedAsteroidMap pk=%s: %s",
            row.pk,
            exc,
            exc_info=True,
        )
        clear_admin_list_thumbnail(int(row.pk))
    return True
```

**Blocker fixes embodied:** (1) `admin_list_thumbnail=thumbnail_name` in `update`; (2) thumbnail errors → log + clear, no raise; (3) no `row.save()` — recursion-safe.

- [ ] **Step 4: Run tests — PASS**

- [ ] **Step 4: Run tests — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_reconstructed_map_thumbnail_service.py -v --tb=short
```

- [ ] **Step 5: Commit**

---

### Task 5: Wire persist hook

**Files:**
- Modify: `django_apps/asteroid_lab/services/reconstructed_asteroid_service.py`
- Modify: `tests/unit/asteroid_lab/test_reconstructed_asteroid_persist.py`

- [ ] **Step 1: Add failing assertion to persist test**

After existing persist assertion, add:

```python
    row.refresh_from_db()
    assert row.admin_list_thumbnail
    assert row.admin_list_thumbnail_hash
```

- [ ] **Step 2: Run test — FAIL**

- [ ] **Step 3: Call sync at end of `persist_reconstructed_asteroid_map`**

```python
from django_apps.asteroid_lab.services.reconstructed_map_thumbnail_service import (
    sync_admin_list_thumbnail,
)

    # after update_or_create + optional row.save(...)
    row = m.ReconstructedAsteroidMap.objects.get(pk=int(row.pk))
    sync_admin_list_thumbnail(row)  # must not raise — persist succeeds even if thumbnail fails
    return int(row.pk)
```

Use fresh DB row so `decoded_json` is loaded. Add persist test: patch `render_list_thumbnail_image_bytes` to raise; assert `persist_reconstructed_asteroid_map` still returns pk and row exists with empty thumbnail.

- [ ] **Step 4: Run persist + thumbnail tests — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_reconstructed_asteroid_persist.py tests/unit/asteroid_lab/test_reconstructed_map_thumbnail_service.py -v --tb=short
```

- [ ] **Step 5: Commit**

---

### Task 6: Admin changelist + actions

**Files:**
- Modify: `django_apps/asteroid_lab/admin.py`
- Create: `tests/unit/asteroid_lab/test_reconstructed_map_admin_changelist.py`

- [ ] **Step 1: Write failing admin tests**

Create `tests/unit/asteroid_lab/test_reconstructed_map_admin_changelist.py` using project `admin_client` + `staff_user` fixtures (see other `django_apps` admin tests). Include:

```python
@pytest.mark.django_db
def test_changelist_uses_img_not_mini_map_grid(admin_client, staff_user, reconstructed_row):
  sync_admin_list_thumbnail(reconstructed_row)
  url = reverse("admin:asteroid_lab_reconstructedasteroidmap_changelist")
  admin_client.force_login(staff_user)
  resp = admin_client.get(url)
  assert resp.status_code == 200
  assert b"genetic-sample-mini-map-cell" not in resp.content
  assert b"<img" in resp.content


@pytest.mark.django_db
def test_admin_regenerate_action_smoke(admin_client, staff_user, reconstructed_row):
  reconstructed_row.admin_list_thumbnail_hash = ""
  reconstructed_row.save(update_fields=["admin_list_thumbnail_hash"])
  changelist = reverse("admin:asteroid_lab_reconstructedasteroidmap_changelist")
  admin_client.force_login(staff_user)
  resp = admin_client.post(
      changelist,
      {
          "action": "regenerate_admin_list_thumbnails",
          "select_across": "0",
          "_selected_action": [str(reconstructed_row.pk)],
      },
  )
  assert resp.status_code == 302
  reconstructed_row.refresh_from_db()
  assert reconstructed_row.admin_list_thumbnail.name


@pytest.mark.django_db
def test_admin_clear_action_smoke(admin_client, staff_user, reconstructed_row):
  sync_admin_list_thumbnail(reconstructed_row)
  changelist = reverse("admin:asteroid_lab_reconstructedasteroidmap_changelist")
  admin_client.force_login(staff_user)
  resp = admin_client.post(
      changelist,
      {
          "action": "clear_admin_list_thumbnails",
          "select_across": "0",
          "_selected_action": [str(reconstructed_row.pk)],
      },
  )
  assert resp.status_code == 302
  reconstructed_row.refresh_from_db()
  assert not reconstructed_row.admin_list_thumbnail.name
```

- [ ] **Step 2: Implement admin changes**

In `ReconstructedAsteroidMapAdmin`:

```python
    actions = ["regenerate_admin_list_thumbnails", "clear_admin_list_thumbnails"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.resolver_match and request.resolver_match.url_name.endswith("_changelist"):
            return qs.defer("decoded_json", "original_decoded_json")
        return qs

    @admin.display(description="맵")
    def mini_map_list(self, obj: m.ReconstructedAsteroidMap) -> SafeString | str:
        if obj.admin_list_thumbnail:
            truncated = " …" if obj.admin_list_thumbnail_truncated else ""
            return format_html(
                '<img src="{}" alt="" width="120" height="120" loading="lazy" '
                'style="object-fit:contain;background:#020617;border-radius:6px;" />'
                '<span style="font-size:10px;color:#94a3b8;">{} cells{}</span>',
                obj.admin_list_thumbnail.url,
                obj.admin_list_thumbnail_cell_count,
                truncated,
            )
        return format_html(
            '<span style="color:#64748b;font-size:11px;">no thumbnail</span>'
        )
```

Actions:

```python
    @admin.action(description="Regenerate admin list thumbnails")
    def regenerate_admin_list_thumbnails(self, request, queryset):
        qs = queryset.select_related().only(
            "pk", "decoded_json", "admin_list_thumbnail", "admin_list_thumbnail_hash",
            "admin_list_thumbnail_renderer_version",
        )
        for row in qs.iterator():
            sync_admin_list_thumbnail(row, force=True)

    @admin.action(description="Clear admin list thumbnails")
    def clear_admin_list_thumbnails(self, request, queryset):
        for pk in queryset.values_list("pk", flat=True):
            clear_admin_list_thumbnail(int(pk))
```

**Leave `mini_map_preview` unchanged** (still `genetic_sample_mini_map_html`).

- [ ] **Step 3: Run admin test — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_reconstructed_map_admin_changelist.py -v --tb=short
```

- [ ] **Step 4: Commit**

---

### Task 7: Management command

**Files:**
- Create: `django_apps/asteroid_lab/management/commands/regenerate_reconstructed_map_thumbnails.py`

- [ ] **Step 1: Implement command**

```python
class Command(BaseCommand):
    help = "Regenerate admin_list_thumbnail for ReconstructedAsteroidMap rows."

    def add_arguments(self, parser):
        parser.add_argument("--pk", type=int, action="append", default=[])
        parser.add_argument("--all", action="store_true")
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        qs = m.ReconstructedAsteroidMap.objects.all()
        if options["pk"]:
            qs = qs.filter(pk__in=options["pk"])
        elif not options["all"]:
            raise CommandError("Specify --pk ID or --all")
        qs = qs.only(
            "pk", "decoded_json", "admin_list_thumbnail",
            "admin_list_thumbnail_hash", "admin_list_thumbnail_renderer_version",
        )
        updated = 0
        for row in qs.iterator(chunk_size=50):
            if sync_admin_list_thumbnail(row, force=bool(options["force"])):
                updated += 1
        self.stdout.write(f"Updated {updated} thumbnails.")
```

- [ ] **Step 2: Add command unit test**

Append to `tests/unit/asteroid_lab/test_reconstructed_map_thumbnail_service.py` (or `test_reconstructed_map_admin_changelist.py`):

```python
from django.core.management import call_command


@pytest.mark.django_db
def test_regenerate_command_by_pk(reconstructed_row: m.ReconstructedAsteroidMap) -> None:
    clear_admin_list_thumbnail(int(reconstructed_row.pk))
    call_command(
        "regenerate_reconstructed_map_thumbnails",
        pk=[int(reconstructed_row.pk)],
        force=True,
    )
    reconstructed_row.refresh_from_db()
    assert reconstructed_row.admin_list_thumbnail.name
```

- [ ] **Step 3: Smoke run**

```powershell
python manage.py regenerate_reconstructed_map_thumbnails --pk <ID> --force
```

Expected: completes without traceback.

- [ ] **Step 4: Commit**

---

### Task 8: Docs, contract note, full gate

**Files:**
- Modify: `documents/ai/lab_map_rendering_contract.md` (short § Admin list thumbnail cache)

- [ ] **Step 1: Add contract bullet**

Under “Admin minimap vs Lab replay”:

```markdown
- **Admin reconstructed map changelist**: cached WebP/PNG `admin_list_thumbnail` (tight bbox, capped grid). Not used by solver/replay. Detail form still uses `genetic_sample_mini_map_html`.
```

- [ ] **Step 2: Narrow pytest**

```powershell
python -m pytest tests/unit/asteroid_lab/test_admin_map_list_thumbnail.py tests/unit/asteroid_lab/test_reconstructed_map_thumbnail_service.py tests/unit/asteroid_lab/test_reconstructed_map_admin_changelist.py tests/unit/asteroid_lab/test_reconstructed_asteroid_persist.py -v --tb=short
```

- [ ] **Step 3: Ruff + mypy**

```powershell
python -m ruff check django_apps/asteroid_lab/admin_map_list_thumbnail.py django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py django_apps/asteroid_lab/admin.py
python -m mypy django_apps config src
```

- [ ] **Step 4: Commit docs**

```bash
git add documents/ai/lab_map_rendering_contract.md docs/superpowers/specs/2026-05-30-admin-reconstructed-asteroid-map-thumbnail-cache-design.md docs/superpowers/plans/2026-05-30-admin-reconstructed-asteroid-map-thumbnail-cache.md
git commit -m "docs: admin reconstructed map thumbnail cache spec and contract"
```

---

## Plan self-review (spec coverage)

| Spec requirement | Task |
|------------------|------|
| Approach B changelist only | Task 6 leaves `mini_map_preview` |
| WebP/PNG, no JPG | Task 2 `render_list_thumbnail_image_bytes` |
| Hash + renderer version invalidation | Task 1, 4 |
| No recursive full save | Task 4 `QuerySet.update`; Task 5 single sync call |
| ImageField path in DB | Task 4 `admin_list_thumbnail=thumbnail_name` |
| Thumbnail failure → placeholder, persist OK | Task 4 try/except; Task 5 persist test |
| Tight bbox, not full_map_island_bbox | Task 1 `compute_list_thumbnail_window` |
| Cap 48 + truncated + bbox clamp | Task 1 |
| Color-block primary, cairosvg optional | Task 2 note |
| Changelist defer JSON only | Task 6 `get_queryset` |
| Command/action load decoded_json | Task 6 actions, Task 7 |
| Display-only / not solver input | Spec + no solver imports |
| Admin tests action/command/changelist | Tasks 6–7 (regenerate/clear smoke + `call_command`) |

No TBD placeholders in task steps.

---

## Execution handoff

**Status:** PLAN APPROVED — ready for **Subagent-Driven** execution (Tasks 1–2 → 3–5 → 6–7).

Spec: [`docs/superpowers/specs/2026-05-30-admin-reconstructed-asteroid-map-thumbnail-cache-design.md`](../specs/2026-05-30-admin-reconstructed-asteroid-map-thumbnail-cache-design.md)

Plan: [`docs/superpowers/plans/2026-05-30-admin-reconstructed-asteroid-map-thumbnail-cache.md`](2026-05-30-admin-reconstructed-asteroid-map-thumbnail-cache.md)

Say **「Subagent으로 Task 0부터」** or **「inline으로 구현」** to start implementation.
