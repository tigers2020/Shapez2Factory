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

# Plan: Other frontend bundle drift gates (tracked separately)

## Source Issue

- Linear: SHA-44 (Low priority items)
- Status at planning time: Todo
- Priority: Low

## Problem

Other committed-artifact drift gates (SHA-35 graph-layout, SHA-40 recipe-graph-editor, SHA-42 locale) and pytest substring guards for lab classes remain separate.

## Scope

Track only — no implementation in SHA-44.

## Non-goals

- Unified frontend static-asset CI pattern in this card.

## Implementation Plan

1. No code under SHA-44 Low scope.
2. Follow SHA-35, SHA-40, SHA-42 for respective gates.

## Files / Areas Likely Affected

- TBD per related issues

## Validation Plan

- N/A

## Acceptance Criteria

- [ ] Related issues remain tracked.

## Risks / Open Questions

- Future unified frontend CI job may reduce matrix duplication.
