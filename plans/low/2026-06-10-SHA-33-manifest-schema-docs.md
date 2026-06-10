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

# Plan: Document manifest.error_code semantics for stack failures

## Source Issue

- Linear: SHA-33 (Low slice)
- Status at planning time: In Progress
- Priority: Low

## Problem

Manifest schema documentation does not clearly state that `error_code` must be set when the stack fails but the artifact is still finalized (`ARTIFACT_WRITTEN`, exit 20). Operators and ingest authors may assume `error_code=null` means success.

## Scope

Update artifact design spec / manifest schema docs to document `error_code` population on stack failure and ingest FAILED mapping.

## Non-goals

- Changing manifest `schema_version`.
- Translating KO strings or UI copy.
- Full exit-code table rewrite (SHA-7).

## Implementation Plan

1. Locate canonical manifest spec (grep `error_code` in `docs/superpowers/` and `documents/Algorithm/`).
2. Add subsection: when `run_success=false` / `failed_layer_slug` set, CLI must write non-null `error_code` (e.g. `stack_unavailable`); ingest maps non-null `error_code` to FAILED.
3. Cross-link SHA-33 High implementation and SHA-7 exit-code table when aligned.
4. No code changes unless doc references stale behavior after High plan merges.

## Files / Areas Likely Affected

- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-3a-artifact-shell.md` (or current artifact spec)
- `src/shapez2_factory/adapters/asteroid_lab/artifact_manifest.py` (docstring only, optional)

## Validation Plan

- lint: N/A (docs only)
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: Doc accurately reflects post-SHA-33 behavior

## Acceptance Criteria

- [ ] Matches the source issue spec (Low priority breakdown item).
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Docs must not claim behavior until SHA-33 High is merged — coordinate doc PR timing.
