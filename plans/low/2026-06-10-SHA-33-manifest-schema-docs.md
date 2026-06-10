---
linear_issue: SHA-33
title: Stack-failure artifacts write manifest.error_code=null; Django ingest indexes COMPLETED
priority: Low
labels:
  - bug
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Manifest error_code documentation

## Source Issue

- Linear: SHA-33
- Status at planning time: Todo
- Priority: Low

## Problem

Manifest schema documentation does not clearly state when `error_code` is populated on stack failure vs success.

## Scope

- Update manifest schema / artifact design docs to document `error_code` population on stack failure.

## Non-goals

- Changing manifest DTO fields.
- CLI implementation (High plan).

## Implementation Plan

1. After High plan merges, locate manifest schema docs and artifact design spec.
2. Document: `error_code` is non-null when stack fails with `STACK_UNAVAILABLE` / `failed_layer_slug`.
3. Cross-link SHA-7 exit-code table and SHA-10 regression coverage.
4. No code changes unless doc references stale behavior.

## Files / Areas Likely Affected

- `documents/` or `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/` (manifest schema docs)
- `tests/unit/shapez2_factory/test_manifest_dto.py` (docstring cross-ref only if needed)

## Validation Plan

- lint: N/A (docs only)
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: Doc review against implemented behavior.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on High plan finalizing error_code contract.
