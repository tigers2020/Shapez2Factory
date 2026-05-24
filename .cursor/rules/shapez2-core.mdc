---
description: "shapez2 Factory Planner standing rules: Caveman 6 sections · gates · validation · Forbidden shortcuts"
alwaysApply: true
---

# shapez2 Factory Planner — Core Rules

Canonical manuals: [`AGENTS.md`](mdc:AGENTS.md) · [`documents/ai/manuals/cursor_usage.md`](mdc:documents/ai/manuals/cursor_usage.md) · [`documents/ai/manuals/testing.md`](mdc:documents/ai/manuals/testing.md)

---

## Work classification (required at start)

Classify before starting changes (one or more): **contract change** · **implementation change** · **refactoring** · **documentation change** · **regression fix** · **UI change**

| Classification | Test · documentation order |
|------|-----------------|
| Contract change | Tests · related docs **first** |
| Regression fix | Reproduction test **first** |
| Implementation change | Start with the narrowest unit tests |
| Refactoring | Existing tests suffice if behavior is unchanged; update tests when contracts change |
| Documentation change | pytest not required; if code contracts change, plan in the Tests section |
| UI change | DOM · serialization · JS or fixture regression first |

---

## Validation gates (Dual Gate)

### Iteration (during implementation — red-green)

```bash
python -m pytest <narrow path>      # -q / --quiet / --tb=no forbidden
python -m ruff check <paths>        # after green
```

**Forbidden pytest output-suppression flags**: `-q`, `--quiet`, `--tb=no`, `-p no:terminal` — errors become undetectable.

### PR / merge / CI (Full Gate)

```bash
python -m ruff check .
python -m black --check .
python -m mypy django_apps config src
python -m pytest
```

PR full gate: `mypy django_apps config src` ([AGENTS.md](mdc:AGENTS.md)).

---

## Caveman 6-section output (required at close)

**Closing without 6 sections = incomplete.** Exceptions: Plan mode body · user explicitly requests 「detailed explanation」 · `documents/` file body.

```
## Summary
## Files
## Contracts
## Tests
## Risks
## Next
```

| Section | Content |
|----|------|
| Summary | 1–3 bullets; state work classification |
| Files | `path — why` |
| Contracts | Invariants · DTO · schema changes; reason for adding or skipping tests |
| Tests | `cmd — pass\|fail\|skipped — note` |
| Risks | Regression · `uncertain:` · `assumption:` |
| Next | What follows; use 「complete」 only when finished |

Details: [`cursor_usage.md` §17](mdc:documents/ai/manuals/cursor_usage.md)

---

## Forbidden Shortcuts (absolutely forbidden)

- Making green by deleting or weakening tests only.
- Using replay · artifact · metrics as solver · algorithm **inputs**.
- Multiple `route_domain` patches (`RouteDomainSnapshotBuilder` is the sole owner).
- Repair logic in validation (read-only asserts only).
- Using candidate order as commit order; using candidate reachable as final commit proof.
- Raw↔server re-conversion inside optimization.
- **Free-form strings** for `failure_reason` · `event_type` · `issue_code`, etc. (update enum/const and tests together).
- Proceeding with implementation before plan approval.
- Declaring completion without validation.
- Renames that change **only a leading underscore** (`func`↔`_func`, `name`↔`_name`, same import alias) — forbidden for style · lint · “private/public cleanup” purposes. **Exception**: only when the user explicitly requests a rename, or an approved contract · spec requires the new name.

Full list: [`testing.md § Forbidden shortcuts`](mdc:documents/ai/manuals/testing.md)

---

## Layer boundaries

- `domain` — no I/O · UI · DB · external API calls.
- `application` — no concrete adapter imports.
- `adapters` — no business policy.
- Do not put business rules in views or templates.

Details: [architecture.mdc](mdc:.cursor/rules/architecture.mdc)

---

## Persona policy

Persona 3-stage ([`persona-dialogue.mdc`](mdc:.cursor/rules/persona-dialogue.mdc)) applies only at [`protocols/README.md`](mdc:protocols/README.md) **stage 5 (implementation)**. Do not apply to Plan · documentation-only · review-only work.

---

## BLOCKED format

Stop when validation commands are missing · domain rules conflict · regression lacks baseline tests · high-risk change:

```
BLOCKED:
- missing context:
- risky change:
- recommended next step:
```
