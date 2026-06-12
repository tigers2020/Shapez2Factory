# AGENTS.md

## Mission
shapez2 Factory Planner governance: short rules, strict contracts, small safe changes, fast verification, no stale-doc authority.

## Authority split

**AGENTS.md controls HOW to work. Spec/ADR controls WHAT is true.**

| Kind | Order |
|------|-------|
| **Process** | user > `AGENTS.md` > `.cursor/rules/*.mdc` > skills > agent assumptions |
| **Domain** | user > current canon/spec/ADR > game_data/contracts > code evidence > older docs > agent memory |

Process and domain authority do not override each other across category.

## Session phases (Normal+)

```text
align → contract → slice → implement → verify → STOPPED_AT_APPROVED_SCOPE
```

HITL: ambiguous alignment, contract changes, slice review, merge/taste decisions. AFK: implement/verify only when scope, acceptance, and stop are explicit. Ambiguous features: `grill-me-shapez2` before planning. Detail: `docs/agent-workflows/workflow-phases.md`.

## Kanban tracking (Normal+)

Link each feature/task chat to one card in `.devtool/features/`. On start and each phase change: update `status` + append **Progress** (what doing, evidence). Before unrelated work: if a WIP card exists, emit `LEFTOVER_WIP:` with unfinished acceptance — do not silently abandon; user must park (`blocked`/`backlog` + note) or finish. Read-only/Tiny: optional. Detail: `kanban-tracking.mdc`, `docs/agent-workflows/kanban-tracking.md`.

## Context hygiene

Prefer new session/subagent over compact when reasoning degrades. Keep always-on rules small; exploration via graphify/subagents. Detail: `documents/knowledge/raw/ai/manuals/cursor_usage.md`.

## Task routing

| Kind | Path |
|------|------|
| Question / read-only | domain canon + code; graphify only for cross-module architecture |
| Docs-only | contract clear → edit → no runtime claims |
| Regression | repro → minimal fix → regression gate |
| Implementation | ICE → contract → plan → acceptance → small change → gate |
| Alignment / ambiguous feature | `grill-me-shapez2` → contract → vertical slice review |
| Slice planning | reject horizontal phase plans unless explicitly infra-only |
| Review after implementation | new session/subagent → `quality-check` / Bugbot policy |
| Ops / recovery | git/PR/CI/state inventory → safe recovery → verify → STOP (`ops-recovery.mdc`) |

**ICE:** Intent · Context · Expectations — three layers, not full spec (Normal / High-risk).

## Workflow strictness

Classify risk **first** — do not apply full gates to every request. Detail: `docs/agent-workflows/workflow-strictness.md`.

| Mode | When | Gates |
|------|------|-------|
| Read-only | Q&A, code reading | no clean git or validation |
| Tiny | typo, copy, 1-file localized fix | 3-line contract; touched-file checks |
| Normal | feature, bug, docs contract | default workflow below |
| High-risk | solver, replay, validation, DTO, migrations | full SDD + strict tiers |
| Ops / recovery | git, PR, CI, plan-run | `ops-recovery.mdc` |

All modes: scope boundaries + verification evidence when claiming done.

## Default workflow

Applies to **Normal** and **High-risk** (Tiny uses 3-line contract; Read-only skips edits).

```text
Classify strictness → authority split → matching gates → evidence → STOPPED_AT_APPROVED_SCOPE
```

1. **Authority:** split process vs domain (`Authority split` above).
2. **Code search:** graphify for architecture / unknown location — skip exact file/function/stacktrace or `GRAPH_STALE` (`graphify.mdc`).
3. **Contract:** full contract before production edit; Tiny: Problem / Change / Validation only (`workflow.mdc`).
4. **Git:** Normal/High-risk: clean tree; Tiny: disjoint dirty OK with `DIRTY_ALLOWED_REASON`; Ops: recovery whitelist (`git-worktree.mdc`).
5. **Scope:** closed-world (`agent_scope.mdc`). Stop: `STOPPED_AT_APPROVED_SCOPE`.
6. **Verify:** command + exit code + summary; tier matches strictness (`validation-routine.md`).
7. **Delivery:** one PR-sized purpose; no commit/push/PR unless user asks.

Read when domain authority missing: `structure.md` → `documents/knowledge/wiki/Index.md` → canon/spec → code/tests. Wiki maintenance: `docs/agent-workflows/dream-sequence.md`.

## Shapez2

Solver/Asteroid Lab: domain authority wins. Glob match → `asteroid-lab-invariants.mdc`. Cross-module boundaries → `graphify.mdc` when graph exists.

## SDD / Testing

Tests verify contracts, not agent guesses. Acceptance: Given/When/Then, regression, golden, invariant, schema, API. No weak tests; never relax or skip to force green. Regression: failing repro before fix unless impossible. Solver/replay: preserve invariants in rules and canon.

## Validation

```bash
python manage.py check
powershell -File scripts/test_fast.ps1
ruff check .
mypy django_apps config src
black --check .
```

When to run: `docs/agent-workflows/validation-routine.md`. PR/full: `scripts/test_full.ps1`. Solver smoke: `python manage.py run_solver --slug <slug>`.

## Communication

English for work. Korean summary, compressed (`caveman.mdc`).

## Scope / Permissions

Allowed: source, tests, docs, governance. Ask before `.env`, secrets, CI/deploy, security config, large delete/rename. Do not invent commands, tools, MCP behavior, or unverified pass claims.

## Governance

Root `AGENTS.md` target ~75 lines; split before 120. Nested `AGENTS.md` ≤150. `.cursor/rules/*.mdc` ≤75; detail in `docs/agent-workflows/`. WARN non-blocking. Check: `scripts/check_governance.ps1`.

When blocked: `BLOCKED:` + context, risk, fixes tried, next step.
