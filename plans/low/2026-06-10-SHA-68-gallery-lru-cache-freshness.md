---
linear_issue: SHA-68
title: Gallery image listing cached with lru_cache; new static files invisible until process restart
priority: Low
labels:
  - bug
  - ui
  - priority:low
status: planned
created_by: todo-plan-automation
---

# Plan: Gallery static image listing freshness (SHA-68)

## Source Issue

- Linear: SHA-68
- Status at planning time: Todo
- Priority: Low

## Problem

The `/gallery/` view discovers screenshot and factory-template images via `_list_web_static_images`, which is wrapped in `@lru_cache(maxsize=8)`. The filesystem scan result is cached for the lifetime of each Django worker process. After the first gallery request, adding or removing files under `django_apps/web/static/web/img/screenshots/` or `django_apps/web/static/web/img/factory-templates/` does not change the rendered gallery until the worker restarts.

## Scope

- Remove or bound the process-lifetime cache on `_list_web_static_images` so gallery inventory reflects the current filesystem without worker restart.
- Add a regression test proving listing freshness across consecutive calls.
- Add a brief docstring or operator note only if intentional production caching is retained.

## Non-goals

- Changing gallery viewer JS navigation (`gallery-viewer.js`).
- CI wiring for gallery assets.
- Subdirectory recursion or CDN integration.

## Implementation Plan

1. **Remove `@lru_cache` (preferred path).**
   - In `django_apps/web/views/public_pages.py`, delete the `@lru_cache(maxsize=8)` decorator from `_list_web_static_images` (lines 105–106).
   - Remove `from functools import lru_cache` if no other symbol in the file uses it.
   - Keep the function body unchanged: flat scan of `static_root / "web" / "img" / subdir`, allowed extensions `{.png, .jpg, .jpeg, .webp, .gif}`, sorted paths relative to `django_apps/web/static/`.

2. **Alternative only if perf review blocks removal** (not expected for two small flat dirs):
   - Gate cache behind `not settings.DEBUG`, or invalidate on parent folder mtime.
   - If any cache remains in production, add a one-line docstring on `_list_web_static_images` stating that deploy/worker restart refreshes the listing.

3. **Add unit regression test for listing freshness.**
   - Create `tests/unit/web/test_gallery_static_listing.py`.
   - Use `tmp_path` to build a minimal static tree: `{base}/django_apps/web/static/web/img/screenshots/`.
   - Patch `settings.BASE_DIR` to `tmp_path` via `@override_settings(BASE_DIR=tmp_path)` (or `monkeypatch.setattr` on `django.conf.settings.BASE_DIR`).
   - Seed `first.png`, call `public_pages._list_web_static_images("screenshots")`, assert `first.png` path is present.
   - Add `second.png` to the same folder without clearing any cache, call again, assert both paths appear.
   - If `@lru_cache` is retained during refactor, the test must fail before fix and pass after; with decorator removed, no `cache_clear()` is needed in the test.

4. **Optional integration smoke extension (only if unit test is insufficient).**
   - Existing `tests/integration/web/test_web_smoke.py` gallery tests assert markup only; do not broaden scope unless unit isolation is blocked.

5. **Commit in two steps (TDD-friendly).**
   - Commit 1: failing freshness test (if implementing test-first).
   - Commit 2: remove cache + green test.

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py` — `_list_web_static_images`, `gallery` view (caller only; no logic change expected)
- `tests/unit/web/test_gallery_static_listing.py` — new regression test
- `django_apps/web/templates/web/gallery.html` — read-only reference; no edits expected
- `django_apps/web/static/web/js/gallery-viewer.js` — non-goal; no edits
- `tests/integration/web/test_web_smoke.py` — existing smoke; no required change

## Validation Plan

- lint: `ruff check django_apps/web/views/public_pages.py tests/unit/web/test_gallery_static_listing.py`
- typecheck: `mypy django_apps/web/views/public_pages.py tests/unit/web/test_gallery_static_listing.py`
- tests: `pytest tests/unit/web/test_gallery_static_listing.py -v`
- build: not applicable
- manual verification: start dev server, open `/gallery/`, add a `.png` under `django_apps/web/static/web/img/screenshots/`, refresh page — new image appears without process restart

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- **Perf:** Removing cache adds two small directory scans per gallery request; acceptable for informational page with flat dirs.
- **Production:** Static assets normally ship with deploy restarts; low user impact if cache were kept, but dev/long-lived workers benefit from fix.
- **Related issue SHA-25:** Unrelated gallery markup test naming; do not conflate with this fix.
