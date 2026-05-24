# AI Work Hub (`documents/ai`)

Root [`AGENTS.md`](../../AGENTS.md) holds **short rules + manual routing** only; detailed procedures and domain notes live here and in [`manuals/`](manuals/).

Full `documents/` folder map, archive, and plan-research pairs: [`../README.md`](../README.md).

Per project convention, Markdown body text in this directory is written in **English**.

## Files

| File | Purpose |
|------|---------|
| [`current_plan.md`](current_plan.md) | Goals, scope, and forbidden items for this session/task |
| [`context_notes.md`](context_notes.md) | Assumptions, decisions, related issues and path links |
| [`checklist.md`](checklist.md) | Step-by-step completion checks and quality gates |
| [`manuals/cursor_usage.md`](manuals/cursor_usage.md) | Cursor and agent workflow summary |
| [`.cursor/rules/shapez2-core.mdc`](../../.cursor/rules/shapez2-core.mdc) | Always-on rules and Caveman 6 sections (§17 [`cursor_usage.md`](manuals/cursor_usage.md)) |

Mapping to harness engineering four elements and the 10-stage pipeline: see canonical [`protocols/README.md`](../../protocols/README.md).

## Manuals

[`manuals/`](manuals/) — open **only the chapters needed** for the task type (do not read everything every time).

| Manual | Purpose |
|--------|---------|
| [`manuals/testing.md`](manuals/testing.md) | **Contract-first TDD** · invariant · dual gate · PR checklist · **pytest output rules** (`-q` forbidden) — canonical |
| [`manuals/cursor_usage.md`](manuals/cursor_usage.md) | Cursor, context, and agent-native engineering |
| [`manuals/django.md`](manuals/django.md) § References | External Django references (DEV Cursor rules, django-rules) — for `django` work |
| [`manuals/cursor_slim_setup.md`](manuals/cursor_slim_setup.md) | MCP, plugins, and User Rules slim setup guide |

## Runbooks

[`runbooks/`](runbooks/) — repeatable development procedures.

| Runbook | Purpose |
|---------|---------|
| [`runbooks/dev_commands.md`](runbooks/dev_commands.md) | Quick reference for pytest, runserver, pycache, and build commands |

See also: [`AGENTS.md`](../../AGENTS.md) Manual Routing — task-type manual routing table.
