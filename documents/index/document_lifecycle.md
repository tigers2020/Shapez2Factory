# Document Lifecycle Policy

This repository keeps current documents only. Archive, superseded, obsolete, and
outdated documents are deleted instead of retained in a local archive tree.

## Status Enum

| Status | Meaning | Default Context Included |
|---|---|---|
| `CANON` | Current system contract | Yes |
| `ACTIVE` | Current work plan or checklist | As needed |
| `RESEARCH` | Current evidence for open work, not a contract | As needed |
| `REPORT` | Current execution observation, not a contract | As needed |

## Reading Priority

1. `AGENTS.md`, `.cursor/rules/`, and `documents/ai/manuals/`
2. [`documents/index/document_inventory.md`](document_inventory.md)
3. Current `CANON` documents
4. The task's `ACTIVE` plan
5. Required current `RESEARCH` or `REPORT`

## Operational Rules

- Delete outdated documents once they are no longer current authority.
- Do not create archive or quarantine document trees.
- Do not leave competing specs on the same topic unattended.
- Promote finalized decisions into `CANON` docs or accepted ADRs.
- Remove links to deleted plans, specs, reports, and tests in the same cleanup.
