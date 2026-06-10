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

# Plan: Manifest schema documentation for stack-failure error_code

## Source Issue

- Linear: SHA-33 (Low priority breakdown item)
- Status at planning time: In Progress
- Priority: Low

## Problem

Manifest schema documentation does not clearly state that `error_code` must be set when the stack fails but the artifact is still finalized (`ARTIFACT_WRITTEN`, exit 20). The exit-code mapping table in the artifact design spec lists legacy codes and omits `STACK_UNAVAILABLE` (20).

## Scope

- Update artifact design spec to document stack-failure `error_code` semantics.
- Cross-link ingest FAILED indexing rule (`error_code` or `solver_summary.run_success`).
- Note relationship to CLI `ExitCode.STACK_UNAVAILABLE` without changing enum values.

## Non-goals

- Full exit-code table rewrite (SHA-7).
- Changing runtime behavior (covered by high plan).

## Implementation Plan

1. **Update artifact design spec**
   - File: `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`
   - In manifest `error_code` field comment (§2): clarify non-null on stack failure.
   - In exit-code mapping table (§6): add row for exit 20 → `stack_unavailable` (or chosen constant from high plan).

2. **Document ingest status rule**
   - Add note in spec §4 or ingest section: Django ingest marks FAILED when `manifest.error_code` is set OR `solver_summary.run_success` is false.

3. **Cross-link related issues**
   - Reference SHA-45 (sync ingest), SHA-8 (CLI exit test), SHA-10 (ingest error_code regression).

4. **Verify docs-only**
   - No code changes; `scripts/check_governance.ps1` if spec line counts matter (WARN is non-blocking).

## Files / Areas Likely Affected

- `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`
- TBD: `docs/agent-workflows/daily-project-inspection-log.md` (optional cross-link if already mentions SHA-33)

## Validation Plan

- lint: N/A (docs only)
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: Read updated spec sections for internal consistency with implemented high plan

## Acceptance Criteria

- [ ] Matches the source issue spec (low breakdown: docs polish).
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Docs must match actual `error_code` string chosen in high plan implementation — update after code lands or draft with placeholder and fix in same PR.
- SHA-7 may supersede exit-code table; keep this slice minimal to avoid conflicting with SHA-7 scope.
