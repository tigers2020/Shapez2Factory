---
linear_issue: SHA-51
title: shape_part_sprite_manifest lists DB rows without verifying PNG exists on storage
priority: High
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Omit manifest entries without backing PNG on storage

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: High

## Problem

`shape_part_sprite_manifest` returns every ORM row with `image.url` without verifying the PNG exists on storage. Recipe graph editor gets 404s and blank tiles with no server signal.

## Scope

Filter manifest to servable sprites only (DB row + storage file present).

## Non-goals

- Auto-rebaking during manifest requests.
- Sprite key format changes.
- Client retry logic.

## Implementation Plan

1. Read `shape_part_sprite_manifest` in `staff_shared.py` (~76–84).
2. Before adding entry, check `row.image.name` non-empty and `row.image.storage.exists(row.image.name)`.
3. Omit rows failing check.
4. Manual: manifest with deleted PNG omits key.

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`

## Validation Plan

- tests: mid/low plans
- manual: recipe graph editor tile load

## Acceptance Criteria

- [ ] Manifest omits rows without backing PNG.

## Risks / Open Questions

- Storage backend must support `exists()` in test (use default file storage mock).
