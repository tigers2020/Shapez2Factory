# Manual: Refactor · Cleanup

## Goal

Change no behavior, or change only the behavior requested.

## Principles ([`.cursor/rules/shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc))

- Do not touch files unrelated to the request.
- Remove unused imports · variables only from your own changes. **Do not delete existing dead code without a request.**
- Do not add speculation · out-of-scope abstractions · “impossible scenario” defensive code.

## Broad rewrites

Do not perform broad rewrites without explicit request · plan · approval ([`AGENTS.md`](../../../AGENTS.md)).

## Deletion

Do not delete legacy modules without proof they are unused.

## Verification

Pass [`testing.md`](testing.md) Contract-first SDD · dual gate, or document why not run. Behavior-preserving refactors do not require new tests.

## Related

- PR · scope-level **comprehensive review** (architecture · security · performance · style parallel audit, then integrated report): [`.cursor/skills/quality-check/SKILL.md`](../../../.cursor/skills/quality-check/SKILL.md) (`@quality-check`)
