# Skill Trust Boundary

Hermes-generated skills are **drafts**, not operational instructions, until human review.

## Storage

| Location | Role |
|----------|------|
| `docs/agent-skills/drafts/` | Hermes-proposed skill drafts; **no auto-apply** |
| `docs/agent-skills/approved/` | Human-reviewed project skills Cursor may follow |
| `~/.hermes/skills/` | Hermes global/personal skills; **do not commit unreviewed copies to repo** |

## Flow

```text
Hermes SKILL_SUGGESTION → save under docs/agent-skills/drafts/
→ human review
→ move or copy to docs/agent-skills/approved/ (or existing .cursor/skills/ with review)
→ only then use as Cursor implementation guide
```

## Rules

- Do not copy unreviewed Hermes output directly into `~/.hermes/skills/` or `.cursor/skills/`.
- Do not treat draft skills as alwaysApply rules or committed governance.
- `SKILL.md` frontmatter (`name`, `description`) affects skill discovery — keep purpose, scope, and prohibitions explicit.
- Reject or revise drafts that broaden scope, weaken tests, or bypass `AGENTS.md` / canon specs.

## Conflict with grill-me-shapez2

If an approved skill conflicts with grill verdict or canon spec: stop and escalate to user; do not implement silently.
