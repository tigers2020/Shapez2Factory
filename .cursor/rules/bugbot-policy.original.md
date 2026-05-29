---
description: When to invoke Cursor Bugbot on pull requests (selective, not default).
globs:
alwaysApply: false
---

# Bugbot policy

Use Cursor Bugbot **selectively** — not on every PR and not as a default checklist item.

## Invoke when

- High-risk change (contracts, solver invariants, authority/doc routing)
- Large diff or cross-cutting refactor
- User explicitly requests Bugbot review
- Uncertain regression surface after merge

## Skip when

- Docs-only PR with no runtime path change
- Narrow test or style fix with green CI
- User asked to skip automated review

## Agent rule

Do not add "run Bugbot" to PR templates or completion checklists by default. Mention Bugbot only when one of the invoke criteria applies.
