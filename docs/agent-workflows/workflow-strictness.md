# Workflow Strictness

Canon: `AGENTS.md` § Workflow strictness. Routers: `workflow.mdc`, `git-worktree.mdc`, `graphify.mdc`, `ops-recovery.mdc`.

## Principle

```text
Do not weaken safety rules globally.
Classify risk first, then apply matching gate intensity.
Scope boundaries and verification evidence apply in every mode.
```

## Modes

| Mode | When | Contract | Git | Code search | Validation |
|------|------|----------|-----|-------------|------------|
| **Read-only** | Q&A, explanation, structure | none | not required | graphify for architecture only | none |
| **Tiny** | typo, copy, comment, clear 1-file fix | 3-line (below) | clean preferred; dirty OK if disjoint + logged | skip graphify when exact file/line/stacktrace | touched-file / targeted |
| **Normal** | feature, bug, docs contract change | full + ICE | clean unless user scoped | graphify for cross-module | tier 2–3 by slice |
| **High-risk** | solver, replay, validation, routing, DTO, migrations | full SDD | clean worktree | graphify + stale check | tier 3+; golden when applicable |
| **Ops / recovery** | git, PR, CI, plan-run state | recovery scope only | dirty inventory OK | N/A | state verification |

### Auto-upgrade to High-risk

Treat as **High-risk** when touching any of:

- solver layers, routing, replay, validation logic
- DTO / schema / artifact contracts
- migrations
- golden / optimization loop
- branch / plan-run automation skills

When unsure, default **Normal** — not Tiny.

## Tiny contract (3-line)

```text
Problem:
Change:
Validation:
```

Example:

```text
Problem: button label typo
Change: "Runing" → "Running"
Validation: grep or targeted frontend test
```

No ICE, plan, or full acceptance doc required. Still report changed files and verification evidence.

## Dirty worktree exceptions

| Mode | Dirty tree |
|------|------------|
| Read-only | allowed (no edits) |
| Tiny | allowed when user explicit **and** edit paths do not overlap dirty files |
| Normal / High-risk | BLOCKED unless user scoped paths |
| Ops / recovery | inventory OK; whitelist edits only |

When dirty edit is allowed, log in the report:

```text
DIRTY_ALLOWED_REASON:
- user explicitly requested
- touched files do not overlap dirty paths
- recovery-mode whitelist only
```

## Graphify

- **Use first:** architectural or unknown-location work (Normal/High-risk).
- **Skip:** exact file, function, or stacktrace given; Read-only answer after direct read; `GRAPH_STALE` (hint only).

## Minimum validation by mode

See `validation-routine.md` § Strictness mapping. PR push always tier 4.

## One-line summary

```text
Classify risk → apply matching gates → keep scope and evidence → STOP
```
