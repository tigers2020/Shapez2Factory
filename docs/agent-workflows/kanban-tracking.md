# Kanban Tracking

Canon: `AGENTS.md` § Kanban tracking. Router: `.cursor/rules/kanban-tracking.mdc`.

One **kanban card** per feature/task thread in `.devtool/features/`. Extension: Kanban Markdown (`kanban-markdown.open`). Column ids: `.devtool/README.md`.

## Why

Chat context is ephemeral; cards are durable WIP state. Prevents lost progress when switching tasks, skipping steps, or starting a new chat.

## Card lifecycle

```text
backlog → align → contract → slice → implement → verify → done
                              ↘ blocked ↗
```

| Event | Card action |
|-------|-------------|
| Task/chat starts (Normal+) | Link or create card; set `status` to current phase |
| Work advances | Move `status`; append **Progress** bullet |
| Blocked | `status: blocked`; note blocker + tried fixes |
| Validation pass | `verify` → `done`; summary + commands run |
| User pivots away | `LEFTOVER_WIP` warning unless user parks card |

## Progress log format

Append to card body (markdown below frontmatter):

```markdown
## Progress

- 2026-06-12 — **implement** — wired DTO field X; next: serializer test
- 2026-06-12 — **verify** — pytest path/to/test.py exit 0
```

Update frontmatter `modified` when editing.

## Frontmatter (typical)

```yaml
id: "feature-slug-2026-06-12"
status: "implement"
priority: "high"
labels: ["shapez2", "dto"]
```

Optional: link plan `linear_issue: SHA-XX` in body, not as authority over canon.

## LEFTOVER_WIP warning

Emit when **all** apply:

1. A card exists with `status` in `align`, `contract`, `slice`, `implement`, `verify`, or `blocked` (active work).
2. User or agent is about to start **unrelated** work (new feature, different bug, ops tangent).
3. User has not explicitly parked the card (`backlog`/`blocked` with reason) or marked done.

Warning template:

```text
LEFTOVER_WIP:
- card: .devtool/features/<file>.md
- status: implement
- unfinished:
  - acceptance criterion 2 not met
  - validation not run
- action: finish, or tell me to park (blocked/backlog + note)
```

Agent must not proceed with unrelated implementation until user acknowledges — read-only triage is OK.

## Mode exceptions

- **Read-only:** no card required.
- **Tiny:** update linked card if present; do not block on missing card.
- **Ops/recovery:** only when user attached a card or recovery contract names it.

## Settings

Workspace columns: `.devtool/kanban.settings.json` → `scripts/sync-kanban-settings.ps1`.
