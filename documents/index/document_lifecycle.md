# Document Lifecycle Policy

This document fixes the status and reading priority of documents under `documents/`. The goal is to prevent old plans and reports from being read as current implementation contracts, which causes architecture drift.

## Status Enum

| Status | Meaning | Default Context Included |
|------|------|------------------|
| `CANON` | Canonical current system contract. Takes precedence in implementation, verification, and review. | Yes |
| `ACTIVE` | In-progress or pending work plan. After completion, resolve to `CANON`, ADR, `COMPLETED`, or `ARCHIVED`. | As needed |
| `RESEARCH` | Investigation, evidence, ideas. Not a finalized contract. | As needed |
| `REPORT` | Execution reports, log analysis, audit results. Observational output, not spec. | As needed |
| `COMPLETED` | Completed work record. Keeps verification results but is not a living spec. | No |
| `ARCHIVED` | Outdated or archival document. Do not use for current design decisions. | No |
| `SUPERSEDED` | Document replaced by another. Leave `superseded_by` at the top. | No |

### Operational label: QUARANTINE

Inventory may label paths **QUARANTINE** for AI routing. Map to lifecycle `ARCHIVED` or `SUPERSEDED` and set `do_not_use_as_authority: true` in front matter. QUARANTINE docs are historical context only — not implementation authority.

## Reading Priority

1. `AGENTS.md`, `.cursor/rules/`, `documents/ai/manuals/`
2. Status check in [`documents/index/document_inventory.md`](document_inventory.md)
3. `CANON` documents
4. Current task's `ACTIVE` plan
5. Required `RESEARCH` or `REPORT`
6. Read `COMPLETED`, `ARCHIVED`, `SUPERSEDED` for historical reference only.

## Recommended Document Header

When possible, place this meta block at the top of a document.

```yaml
status: ACTIVE
owner: solver-architecture
last_reviewed: 2026-05-15
supersedes: []
superseded_by:
do_not_use_as_authority: false
related_epics: []
```

## Operational Rules

- Do not leave competing specs on the same topic unattended. When a new canonical doc appears, mark the previous one `SUPERSEDED` or `ARCHIVED`.
- `REPORT` and `RESEARCH` do not directly replace canonical wording. Reflect finalized content in `CANON` documents or ADRs.
- Mark completed plans `COMPLETED` or bundle them in an archive index, and remove them from the next-task context.
- Large file moves proceed in a separate plan. Priority cleanup via inventory and archive index updates alone is sufficient.
- `documents/` may be git-ignored in this checkout, so use `git status --ignored` together with direct file reads during verification.
