# PR-X Plan

## Classification

`bug fix` | `refactor` | `contract change` | `performance` | `docs`

## Position

```text
Position: [Contract Auditor | Test Engineer | Implementer | …]
Mission: [one sentence]
Authority:
  - You may: …
  - You must not: …
Primary lens: [contract | testing | django | solver | …]
```

## Current behavior

What the code does today (evidence: test, spec, or audit note).

## Target behavior

What must change.

## Contract

- Invariant 1
- Invariant 2
- Forbidden behavior

## Non-goals

## Files expected to change

| Action | Path | Why |
|--------|------|-----|
| | | |

## Steps

1. Audit current behavior (read-only)
2. Add acceptance tests from spec (if behavior change)
3. Minimal implementation
4. Run focused gates
5. Update docs if public contract changed

## Acceptance criteria

- [ ] …
- [ ] No unrelated files changed
- [ ] No synthetic/fallback behavior introduced unless spec allows

## Stop conditions

- Public contract conflict discovered
- Scope grows beyond this PR purpose
- Existing invariant violation
- Missing CANON spec for contract change

## Verification

```bash
python -m pytest <narrow path>
python -m ruff check <paths>
```

PR-ready full gate: see [`AGENTS.md`](../../../AGENTS.md).
