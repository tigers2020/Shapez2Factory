# Skills Index

Invoke **only** when rules below match. Not default workflow — see [`AGENTS.md`](../../AGENTS.md).

## Invocation rules

1. **Slash command present** → invoke matching skill.
2. **No slash** → core workflow unless exactly one skill matches task class.
3. **Multiple candidates** → do not stack; pick one or `BLOCKED:` with routing note.
4. **Never auto-stack** `/plan-run`, `/clean-root`, `/clean-repo-commit`, `/bug-fix`, `/quality-check` on the same turn.

| Skill | Invoke | Purpose |
|---|---|---|
| `bug-fix` | `/bug-fix` | Fix + regression tests, or tests-only mode |
| `quality-check` | `/quality-check` | Diff review or pre-spec plan review |
| `grill-me-shapez2` | `/grill-me-shapez2` | HITL alignment before contract (read-only) |
| `doc-update` | `/doc-update` | Sync docs/ADR after contract change |
| `cli-boundary` | CLI touch | Thin adapter rules for management commands |
| `plan-run` | `/plan-run` | Linear plan queue automation |
| `clean-root` | `/clean-root` | Safe root cleanup before plan-run (stash-based) |
| `clean-repo-commit` | `/clean-repo-commit` | Review, validate, commit completed work; no stash/delete/reset |
| `goal` | `/goal` | Autonomous loop until completion condition |
| `golden-fixture-optimization-loop` | `/golden-fixture-optimization-loop` | One golden solver optimization cycle |
| `fallow` | `/fallow` | JS/TS static health audit |
| `llm-wiki` | `/llm-wiki` | `documents/knowledge/` ingest + maintenance |
| `improve-codebase-architecture` | `/improve-codebase-architecture` | Review-only deep-module proposals (Ousterhout); no code without approval |

## Adding a skill

1. CANON or runbook first.
2. Short `SKILL.md`; detail in `references/`.
3. Register here — do not add to `AGENTS.md` unless user asks.
