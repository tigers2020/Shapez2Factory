---
linear_issue: SHA-44
title: CI never runs build:css; committed app.css can drift from Tailwind source
priority: Low
labels:
  - ui
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Related frontend drift gates (deferred)

## Source Issue

- Linear: SHA-44
- Status at planning time: Todo
- Priority: Low (deferred items)

## Problem

Multiple committed frontend artifacts lack CI freshness gates. SHA-44 addresses CSS only.

## Scope

Track cross-issue dependencies only.

## Non-goals

- Implementing SHA-35, SHA-40, SHA-42 in this card

## Implementation Plan

1. Note SHA-35 (graph-layout), SHA-40 (recipe graph editor), SHA-42 (locale) as parallel tracks.
2. Consider unified CI pattern after two+ gates land (see SHA-35 low plan).

## Files / Areas Likely Affected

- TBD

## Validation Plan

- N/A

## Acceptance Criteria

- [ ] Remaining risks documented per SHA-44 spec.

## Risks / Open Questions

- Pytest substring guards in `test_asteroid_lab_ui_strings.py` are partial, not systemic.
