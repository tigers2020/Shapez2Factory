---
name: grill-me-shapez2
description: >-
  Adversarial pre-spec review for Asteroid Lab / Shapez2 solver plans. One question
  at a time with recommended answers and risk class. Checks CANON invariants before
  implementation. REVIEW ONLY — no production edits. Use when the user runs
  /grill-me-shapez2, says "grill this plan", stress-tests an algorithm/DTO/Layer
  design, or scope is large/ambiguous before contract brief or spec amendment.
disable-model-invocation: true
metadata:
  owner: project
  risk: low
  mode: review-only
---

# /grill-me-shapez2 — Adversarial plan review (pre-spec gate)

## Position

| Field | Value |
|---|---|
| **Position** | Workflow Architect — adversarial plan reviewer |
| **Mission** | Stress-test a plan or design until decision dependencies are explicit and implementation risk is classified |
| **Authority** | Read codebase · CANON specs · ADRs · rules · ask user **one question at a time** |
| **Must not** | Edit production code · write specs/ADRs unless user explicitly asks after session · start implementation · weaken tests to force green |
| **Acceptance** | Final deliverable: decision table · unresolved blockers · PR split · hard test gates · likely files — within **≤8 questions** |
| **Stop** | Plan **approve** / **reject** / **amend** verdict reached, or user stops |

## When to use

**Use** before spec amendment or PR plan when:

- Algorithm or Layer responsibility is branching (e.g. Layer 3 shape/fluid split, clean-slate vs reuse)
- DTO / replay / contract boundaries move
- Agent plan feels optimistic or scope is multi-PR
- Test-weakening risk is visible

**Skip** for: approved CANON-only implementation · clear regression with reproducer · rename/lint/format · tasks under ~5 minutes.

## Relationship to other skills

| Skill | Role |
|---|---|
| **grill-me-shapez2** (this) | Pre-spec adversarial Q&A; project invariant checklist |
| **grill-with-docs** (global) | Same interview style + inline `CONTEXT.md` / ADR updates |
| **quality-check** | Post-diff merge-gate review |
| **shapez2-workflow** | Full SDD checklist |

Preferred pipeline:

```text
grill-me-shapez2 → spec/contract brief → pr-plan → acceptance tests → implementation → quality-check → gate
```

**Not:**

```text
grill-me-shapez2 → agent edits files immediately
```

## Session rules

1. **One question at a time** — wait for user answer (or explicit "use your recommendation") before the next.
2. **Max 8 questions** — if more branches remain, batch into "deferred" in the final table.
3. For each question provide:
   - **Why it matters** (dependency or invariant at stake)
   - **Recommended answer** (agent judgment)
   - **Risk**: `BLOCKER` · `HIGH` · `MEDIUM` · `LOW`
4. If the answer exists in repo docs or code, **explore first** — do not ask the user to repeat CANON.
5. **Read-only** for this skill unless the user expands scope to doc/spec writes.

## Invariant checklist (always cross-check)

Full table: [references/invariants-checklist.md](references/invariants-checklist.md) · rule: [asteroid-lab-invariants.mdc](../../rules/asteroid-lab-invariants.mdc)

Summary — challenge any plan that violates or blurs:

- **SDD**: CANON spec / contract brief before behavior change; acceptance tests from spec; one PR · one purpose
- **Layer 3/4**: follow active clean-slate / reset CANON — superseded greedy Layer 3/4 docs are not authority
- **Decontamination**: retired RTTP/MEG paths stay retired; no revive from deleted tests or old plans
- **Coordinates**: island-local copy JSON; `CoordFrame.ISLAND_RAW` solver default; no dense server-coords bridge
- **Replay / artifacts**: debug/output only — **never** solver or algorithm input; single replay timeline
- **ReconstructionCompleteMap**: terrain/capacity SoT at pipeline boundaries
- **Route domain**: `RouteDomainSnapshotBuilder` sole owner; commit-time re-probe; candidate reachable ≠ commit proof
- **Validation**: read-only asserts — no repair in validation
- **M extractor**: outer-rim anchor where CANON applies
- **Void belt/pipe**: exterior installation CANON where relevant
- **Enums**: no free-form `failure_reason` / `event_type` / `issue_code` strings
- **Tests**: no synthetic tests that only force green; no forbidden pytest quiet flags

## Question selection (priority order)

Walk the design tree — highest dependency first:

1. Goal · non-goals · rollback if wrong
2. Contract / DTO / schema boundaries
3. Layer ownership and what is explicitly **out of scope**
4. Invariant conflicts with existing CANON or code
5. Test gates and what must fail on HEAD before production
6. PR split (one purpose per PR)
7. Files and modules likely touched
8. Residual `uncertain:` / human approval needed

## Final deliverable (required)

End every session with:

### 1. Verdict

One of: **approve** · **reject** · **amend** (with one-line rationale).

### 2. Decision table

| # | Decision | Choice | Risk | Status |
|---|----------|--------|------|--------|
| 1 | … | … | BLOCKER/HIGH/MEDIUM/LOW | resolved / deferred |

### 3. Unresolved blockers

List `BLOCKER` items still open; link missing CANON or human approval.

### 4. Recommended PR split

```text
PR-N: <one purpose> — <acceptance hint>
```

### 5. Hard test gates

Concrete `pytest` paths or test names that must pass and must not be weakened.

### 6. Likely files

Paths only — no drive-by scope.

## Communication

Follow [AGENTS.md](../../../AGENTS.md): chat **Korean caveman**; tables and deliverables **English**.

## References

- [invariants-checklist.md](references/invariants-checklist.md)
- [AGENTS.md](../../../AGENTS.md) · [START_HERE.md](../../../documents/ai/START_HERE.md)
- [asteroid-lab-invariants.mdc](../../rules/asteroid-lab-invariants.mdc)
- [workflow.mdc](../../rules/workflow.mdc) · [protocols/README.md](../../../protocols/README.md)
