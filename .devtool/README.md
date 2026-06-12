# .devtool — Kanban features board

Agent-native feature cards for [Kanban Markdown](https://marketplace.visualstudio.com/items?itemName=LachyFS.kanban-markdown) (`kanban-markdown.open`).

## Columns ↔ workflow phases

Maps to `AGENTS.md` § Session phases and `docs/agent-workflows/workflow-phases.md`:

| Column `id` | Phase | HITL / AFK | Typical action |
|-------------|-------|------------|----------------|
| `backlog` | intake | — | raw idea, not triaged |
| `align` | align | HITL | `grill-me-shapez2` |
| `contract` | contract | HITL | ICE / `contract-brief.md` |
| `slice` | slice | HITL | vertical slice review |
| `implement` | implement | AFK when eligible | code + tests / `plan-run` |
| `verify` | verify | mixed | fresh review + validation |
| `blocked` | — | HITL | `BLOCKED:` — needs human decision |
| `done` | stop | — | `STOPPED_AT_APPROVED_SCOPE`; archived under `features/done/` |

New cards default to `backlog`. Keep `done` as column id (extension archives to `features/done/`).

## Workspace settings

Canonical config: [`kanban.settings.json`](kanban.settings.json).

Apply to Cursor/VS Code (`.vscode/settings.json` is gitignored):

```bash
powershell -File scripts/sync-kanban-settings.ps1
```

Or merge `kanban.settings.json` keys manually under **Settings → Workspace → Kanban Markdown**.

## Card format

See extension readme. Features live in `features/*.md` (`status` frontmatter = column `id`).

Agents (Normal+): link each task/chat to one card; update `status` + **Progress** on phase changes. Pivot without finishing → `LEFTOVER_WIP:` warning. See `docs/agent-workflows/kanban-tracking.md`.
