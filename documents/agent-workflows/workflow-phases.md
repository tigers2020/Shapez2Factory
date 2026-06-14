# Workflow Phases

Canon: `AGENTS.md` § Workflow & DOX. Routers: `workflow-phases.mdc`, `dox-framework.mdc`. DOX detail: `dox-framework.md`.

Matt-style **align → slice → AFK implement → fresh review** mapped onto Shapez2 **risk-tier SDD**. Detail source: `documents/knowledge/wiki/concepts/vibe-coding-agentic-engineering-2026.md`.

## Workflow + DOX

Phases and DOX are one pipeline — not parallel checklists.

| Phase | Workflow | DOX | Kanban |
|-------|----------|-----|--------|
| Align | shared intent; `grill-me-shapez2` when ambiguous | read root `AGENTS.md`; skim child `AGENTS.md` for likely touch paths | find/create card; `status: align` |
| Contract | ICE / contract-brief; authority split (process vs domain) | walk DOX chain for every path in scope; nearest doc = local contract | `status: contract` |
| Slice | vertical slice plan; reject horizontal unless infra-only | confirm subtree `AGENTS.md` covers slice boundaries | `status: slice` |
| Implement | code + tests; closed-world (`agent_scope.mdc`) | **re-read** nearest `AGENTS.md` before each edit batch | `status: implement`; append **Progress** |
| Verify | validation tier; fresh-context review when Normal+ | **DOX pass**: update owning `AGENTS.md` if contracts changed; else note unchanged | `status: verify` → `done` |
| Stop | `STOPPED_AT_APPROVED_SCOPE` | top-level index: root `AGENTS.md` § Child DOX Index only | archive card |

**By strictness mode:**

| Mode | DOX |
|------|-----|
| Read-only | read chain; no edits; no DOX pass |
| Tiny | read chain for touched path; DOX pass; doc update only if contract changed |
| Normal / High-risk | full table above |
| Ops / recovery | read chain; edits on recovery whitelist only (`ops-recovery.mdc`) |

## Phase map

| Phase | HITL / AFK | Artifact | Shapez2 tool |
|-------|------------|----------|--------------|
| Align | HITL | shared design concept | `grill-me-shapez2` |
| Contract | HITL | ICE / contract-brief | `documents/ai/templates/contract-brief.md` |
| Slice | HITL | vertical slice plan | `pr-plan.md`, plan frontmatter |
| Implement | AFK when eligible | code + tests | plan-run / manual |
| Verify | mixed | validation evidence | `validation-routine.md` |
| Stop | — | final report | `STOPPED_AT_APPROVED_SCOPE` |

## HITL vs AFK

**Human-in-the-loop** work cannot be delegated to `plan-run auto` or `/goal`:

- ambiguous feature intent
- contract creation or amendment
- slice shape review (horizontal vs vertical)
- merge approval
- taste, UX, or domain judgment

**AFK-eligible** only when all are explicit:

- contract and acceptance criteria
- stop condition
- closed-world task list (`agent_scope.mdc`)
- `afk_eligible: true` in plan frontmatter (when using plan-run)

High-risk (solver, replay, DTO, migrations): default **HITL** for contract and slice review even if `afk_eligible: true`.

## Vertical slice (tracer bullet)

**One PR purpose** ≠ **vertical slice**. A vertical slice is the smallest change that still produces **end-to-end runnable feedback**.

### Good (Shapez2 examples)

- One field: DTO → serializer → adapter → UI read path → test
- One replay frame contract: schema + producer + consumer test
- One lab API: view + service boundary + integration test

### Bad (rewrite unless infra-only)

- DTO types only
- Serializer only
- JS display only without wire authority check
- Schema migration without runnable consumer

### Infra-only exception

User must explicitly scope horizontal work (e.g. "migration scaffold only, no behavior change"). Mark `slice_type: horizontal` or `ops` in plan frontmatter.

## Fresh-context review

After implementation in the same session, context quality degrades (smart-zone decay). For Normal+:

1. New chat or review subagent (`quality-check`, Bugbot per `bugbot-policy.mdc`)
2. Re-read contract and acceptance — do not trust implementer summary alone
3. Inspect full diff
4. Run smallest relevant validation tier (`validation-routine.md`)

## plan-run frontmatter (doc contract)

Extend standard frontmatter:

```yaml
slice_type: vertical | horizontal | ops
afk_eligible: true | false
blocked_by: []          # linear_issue ids; prefer depends_on when merged
contract_authority:
  - path/to/canon-or-spec
acceptance:
  - command: "pytest …"
    expected: "…"
stop_condition: "…"
```

| Field | Meaning |
|-------|---------|
| `slice_type: vertical` | end-to-end feedback in this plan |
| `slice_type: horizontal` | infra-only; user must have said so |
| `afk_eligible: true` | safe for `plan-run auto` when contract complete |
| `blocked_by` | advisory DAG; `depends_on` remains pick authority |
| `contract_authority` | prevents stale plan overriding canon |

`plan-run auto` requires: `afk_eligible: true`, clean worktree, explicit acceptance and stop.

## Plan authority lifecycle

See `plan-lifecycle.md`. Summary:

```text
active plan = execution authority
closed plan = audit trail only
canon/spec/ADR = durable authority
code/tests = implementation evidence
agent memory = never authority
```

## References

- DOX hierarchy: `dox-framework.md` · `dox-framework.mdc`
- Kanban columns (`.devtool/`): `.devtool/README.md` · `kanban.settings.json` · `scripts/sync-kanban-settings.ps1`
- Kanban WIP tracking: `kanban-tracking.md` · `kanban-tracking.mdc`
- `documents/ai/templates/contract-brief.md`, `pr-plan.md`, `execution-scope-contract.md`
- `documents/knowledge/raw/ai/manuals/cursor_usage.md` (context hygiene)
- Raw workshop: `documents/knowledge/raw/Full Walkthrough Workflow for AI coding.md`
