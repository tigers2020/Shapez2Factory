# Hermes Handoff Formats

Canon: `.cursor/rules/01-hermes-handoff-format.mdc`.

Validation commands: read from `AGENTS.md` § Validation. Do not invent generic validation commands.

## PLAN_TO_SKILL_REQUEST

After Plan Mode, before implementation.

```md
[PLAN_TO_SKILL_REQUEST]

## Task goal
...

## Cursor plan
...

## Current project context
- Framework:
- Relevant files:
- Existing behavior:
- Expected behavior:
- Related AGENTS.md / .cursor rules:
- Existing skills checked:

## Technical uncertainty
...

## Research needed
- Current standard:
- Better algorithm:
- Better library/tool:
- Security concerns:
- Performance concerns:
- Django-specific concerns:

## Constraints
...

## Desired Hermes output
Research current standards and project context; suggest a development skill.
Do not simply APPROVE or BLOCK.

Return:
1. Research summary
2. Recommended implementation direction
3. Rejected alternatives
4. Project-specific SKILL.md draft (save as draft per skill-trust-boundary.md)
5. Implementation checklist for Cursor
6. Validation checklist (from AGENTS.md § Validation)
7. Open risks
```

## SKILL_APPLICATION_SUMMARY

After Cursor applies an approved skill and implements.

```md
[SKILL_APPLICATION_SUMMARY]

## Skill used
...

## Implementation summary
...

## Files changed
- ...

## Tests / validation run
- ...

## What worked well
- ...

## Where the skill was unclear
- ...

## Deviations from the skill
- ...

## Suggested skill improvements
- ...
```

## SKILL_IMPROVEMENT_REQUEST

When implementation shows the skill should be updated.

```md
[SKILL_IMPROVEMENT_REQUEST]

## Original skill
...

## Problem found during implementation
...

## Evidence
- ...

## Requested improvement
Please update the skill so future Cursor tasks avoid this issue.
```

## Hermes response: SKILL_SUGGESTION

```md
[SKILL_SUGGESTION]

## Research summary
- ...

## Recommended direction
- ...

## Why this fits shapez2Factory
- ...

## Rejected alternatives
- ...

## Skill name
...

## SKILL.md draft

Separate fenced block with frontmatter (`name`, `description`) and sections: Purpose, When to use, Inputs required, Implementation checklist, Validation checklist (AGENTS.md § Validation only), Anti-patterns.

## Cursor implementation checklist
- ...

## Validation checklist
- (from AGENTS.md § Validation only)

## Risks / assumptions
- ...

## Follow-up research needed
- ...
```

Draft path: `docs/agent-skills/drafts/`. See `skill-trust-boundary.md`.

## SKILL.md draft example (nested in SKILL_SUGGESTION)

```md
---
name: example-task-skill
description: Use when …
---

# Purpose
…

# When to use
…

# Inputs required
…

# Implementation checklist
- …

# Validation checklist
- (commands from AGENTS.md § Validation only)

# Anti-patterns
- …
```
