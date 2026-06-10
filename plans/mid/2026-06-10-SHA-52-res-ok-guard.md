---
linear_issue: SHA-52
title: quick_solver_preview leaves stale GLTF viewers when shape-preview API returns ok:false
priority: Mid
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Guard fetch response before JSON parse

## Source Issue

- Linear: SHA-52
- Priority: Mid

## Scope

Consider checking `res.ok` before trusting JSON in `runPreview`.

## Implementation Plan

1. After `fetch`, if `!res.ok`, clear viewers and show error (align with network path).
2. Only parse JSON when response OK or known 200+error-body contract documented.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/quick_solver_preview.js`

## Acceptance Criteria

- [ ] Non-2xx responses clear viewers.

## Risks / Open Questions

- API returns 200 with `ok:false` for parse errors — both paths needed.
