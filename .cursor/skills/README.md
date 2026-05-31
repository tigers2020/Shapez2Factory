# Skills Index

Cursor project skills — open when task matches; not read every turn.

## Active skills

| Skill | Path | Purpose |
|---|---|---|
| bug-fix | `bug-fix/SKILL.md` | Minimal fix from failure log + regression test |
| write-tests | `write-tests/SKILL.md` | Contract/failing/regression tests (often PR-3 scope) |
| doc-update | `doc-update/SKILL.md` | Sync docs/ADR when public contract changes |
| quality-check | `quality-check/SKILL.md` | REVIEW ONLY — contract/scope audit on diff |
| cli-boundary | `cli-boundary/SKILL.md` | Thin CLI adapter — import/serialization/exit/determinism |

## Workflow alignment

- **PR-3 (tests only):** `write-tests` · no production edits unless user expands scope
- **Pre-merge review:** `quality-check` · `cli-boundary` when CLI touched
- **Post-contract-change:** `doc-update`

Templates: [`documents/ai/templates/`](../documents/ai/templates/) · Workflow: [`AGENTS.md`](../../AGENTS.md)

## Inactive (phase 3+)

| Skill | Gate |
|---|---|
| feature-add | golden or acceptance test minimum |
| refactor | characterization or golden diff |

## Adding a skill

1. CANON spec or research doc first.
2. Short `SKILL.md`; details in `references/`.
3. Declare **Position · Authority · Acceptance** in skill body.
4. Register here.
