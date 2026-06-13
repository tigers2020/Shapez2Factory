---
id: "workflow-safety-modes-2026-06-12"
status: "done"
priority: "high"
assignee: null
epic: null
dueDate: null
created: "2026-06-12T00:00:00.000Z"
modified: "2026-06-12T18:00:00.000Z"
completedAt: null
labels: ["governance", "workflow-safety"]
order: "a0"
---
# Workflow safety modes (delivery policy)

## Scope

Codify Workflow Safety Architect decision: stop PR-first default; modes 0–3; git destructive ops forbidden unless explicit; protected paths expanded; Step N slice naming.

Non-goals: product code changes; replay Step 2+ implementation.

## Acceptance

- [x] `.cursor/rules/workflow-safety.mdc` always-on router
- [x] `docs/agent-workflows/workflow-safety.md` detail
- [x] `AGENTS.md`, `root.mdc`, `git-worktree.mdc`, `ops-recovery*` aligned
- [x] replay card: PR1–PR4 → Step 1–4 terminology
- [x] governance check passes (`check_governance.ps1` exit 0)

## Progress

- 2026-06-12 — **align** — user Workflow Safety Architect verdict: PR-first overkill; 4 delivery modes; git safety defaults
- 2026-06-12 — **implement** — workflow-safety router + detail doc; cross-link ops/git/AGENTS
- 2026-06-12 — **verify** — governance check passed; replay card PR→Step terminology
- 2026-06-12 — **implement** — reviewer hardening: dirty root=user state; scope-outside STOP; all git clean; checkout Mode 0–1 ban; graphify-out hybrid
