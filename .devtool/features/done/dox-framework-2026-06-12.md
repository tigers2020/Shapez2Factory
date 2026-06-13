---
status: done
modified: 2026-06-12
---

# DOX framework integration

## Scope

Add DOX hierarchy contract to root `AGENTS.md`, scan repo, create child `AGENTS.md` files, build Child DOX Index.

## Acceptance

- [x] Root `AGENTS.md` includes DOX framework sections
- [x] Child DOX Index lists all child `AGENTS.md` paths
- [x] Child `AGENTS.md` files exist for durable boundaries
- [x] Root stays ≤120 lines (governance hard max)
- [x] `scripts/check_governance.ps1` passes or WARN only on line target

## Progress

- 2026-06-12: Integrated DOX into root; created 7 child AGENTS.md; updated structure.md DOX references; governance PASS (WARN 93 lines).
