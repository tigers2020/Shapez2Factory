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

**One card per feature thread** — not per chat, sub-step, or review pass.

| Do | Don't |
|----|-------|
| Reuse the same card for Step 1 → Step 2 → Step 3 of one epic | Create `feature-r2`, `step-2-only`, or session-sibling cards |
| Append **Progress** bullets as each slice lands | Mark `done` after a sub-step when epic Acceptance still open |
| Move `status` to the current phase of the **whole thread** | Archive to `features/done/` until full Acceptance met (optional steps may stay open with note) |
| Mark `done` + archive only when scoped Acceptance is complete | Split history across multiple done cards for the same title/epic |

Sub-step completion → update Acceptance checkboxes + Progress line; keep card in `implement`/`verify` until the thread stops.

| Event | Card action |
|-------|-------------|
| Task/chat starts (any mode) | Link **existing** thread card or create **one** new card; set `status` to current phase |
| Sub-step / slice completes | Append **Progress**; tick Acceptance; **do not** set `done` if more Acceptance remains |
| Work advances (phase change) | Move `status`; append **Progress** bullet |
| Blocked | `status: blocked`; note blocker + tried fixes |
| Full Acceptance + validation | `verify` → `done`; archive to `features/done/` |
| User pivots away | `LEFTOVER_WIP` warning unless user parks card |

## Progress log format

Append to card body (markdown below frontmatter):

```markdown
## Progress

- 2026-06-12 — **implement** — wired DTO field X; next: serializer test
- 2026-06-12 — **verify** — pytest path/to/test.py exit 0
```

Update frontmatter `modified` when editing.

## Artifacts (architecture / improve-codebase-architecture)

When using `/improve-codebase-architecture`, persist review content under `documents/architecture/<thread-slug>/` and link from the card **Artifacts** table:

| File | Phase |
|------|-------|
| `report.md` | Review complete |
| `spec.md` | Contract locked |
| `plan.md` | Implementation approved |

See `documents/architecture/README.md` and `.cursor/skills/improve-codebase-architecture/SKILL.md`. Card holds links + Acceptance; artifact files hold long-form content.

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

## No mode exceptions

Read-only, Tiny, ops/recovery, architecture review, and one-line Q&A all require a card at session start. Trivial work still gets a card (minimal Scope/Acceptance OK).

## Settings

Workspace columns: `.devtool/kanban.settings.json` → `scripts/sync-kanban-settings.ps1`.
