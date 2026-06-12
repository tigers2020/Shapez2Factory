---
name: grill-me-shapez2
description: >-
  HITL adversarial alignment for ambiguous Shapez2 features: interview until
  contract and vertical slice are clear. Read-only — no edits, no implement.
  Use when domain/contract is ambiguous, solver/replay/DTO/wire/UI semantics
  are unclear, or the request would produce a broad plan before alignment.
disable-model-invocation: true
---

# grill-me-shapez2

Pre-spec **HITL alignment** skill. **Do not edit files. Do not implement. Do not open a PR.**

Canon: `AGENTS.md` · `workflow-phases.mdc` · `shapez2-domain.mdc` · `graphify.mdc`

## Purpose

Reach a **shared design concept** before planning. Output is not an implementation plan.

Deliver:

- clarified intent
- domain assumptions
- rejected options
- contract candidates
- vertical slice candidates
- blockers that prevent AFK work

## When to use

Use for:

- ambiguous feature requests
- solver / replay / DTO / wire changes without a clear contract
- UI behavior tied to Shapez2 domain semantics
- requests that would jump straight to a multi-phase plan

Skip for:

- Tiny fixes (typo, rename, clear regression with repro)
- approved implementation plan with explicit contract
- ops/recovery (`ops-recovery.mdc`)

## Context order

1. `AGENTS.md`
2. Relevant `.cursor/rules/*.mdc`
3. If `graphify-out/graph.json` exists: `graphify query` / `path` / `explain` before wide grep (`graphify.mdc`)
4. Read only files needed for better questions

## Interview rules

- One question at a time
- Each question: **why it matters**, **recommended answer**, **risk if different**
- Stop when contract is clear enough for a vertical slice, a human decision is required, or scope must split
- Default max **8 questions** unless user asks to continue

## Question branches (when relevant)

**Domain:** invariant? canon/spec/ADR owner? gameplay vs UI projection vs replay wire?

**Boundary:** Python runtime · DTO · serializer/adapter · JS view · artifact · docs?

**Compatibility:** legacy wire? degraded artifact? read-only vs write vs round-trip?

**Testing:** smallest runnable validation? unit / integration / replay / JS?

**Slice:** first vertical slice? end-to-end path? independently reviewable? AFK-eligible?

## Output format

```md
## Alignment Result

### Decision
- …

### Contract candidate
- Authority:
- Boundary:
- In-scope:
- Out-of-scope:
- Compatibility:
- Acceptance:

### Vertical slice candidate
- slice_type: vertical | horizontal | ops
- afk_eligible: true | false
- blocked_by: []
- Files likely involved:
- Smallest validation:

### Rejected options
- …

### Remaining blockers
- …

### Recommendation
Proceed to contract / slice / stop.
```

## Hard stops

Stop with `BLOCKED:` or `STOPPED_AT_ALIGNMENT_SCOPE` when:

- authority is unclear
- behavior conflicts with canon
- first slice is horizontal but not explicitly infra-only
- acceptance cannot be validated
- solver/replay/wire boundaries crossed without explicit contract

Conflict with approved skill or canon: escalate to user (`skill-trust-boundary.md`).
