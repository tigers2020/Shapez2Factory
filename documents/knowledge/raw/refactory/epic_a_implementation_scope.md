# Epic A — Implementation Scope (Implementation Boundary)

**Role:** Fix allowed·forbidden·canonical rationale in one place so Epic A **implementation PR** scope does not drift.  
**Prerequisites:** [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) (§4.3 vs code audit·A/B/Info), [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md) (B-only fixed table).  
**Updated:** 2026-05-12 — scope tracker draft after PR #7 (MVP exception documentation).

**Operations:** While **A-classified rows are 0** per §5.3, do **not** open Epic A **code-only PRs** (maintain control-flow **doc·governance** phase only). Open implementation PR only after **A rows are agreed and documented** in [epic_a_active_rows.md](./epic_a_active_rows.md).

---

## Fixed Classification (Decision Principle)

| Status | Meaning |
|------|------|
| **A** | Implementation **normalization** target (code·contract·test change allowed) |
| **B** | **Intentional MVP behavior** — only rows in [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md). "Differs from canonical ≠ fix immediately" is **not** the default for B. |
| **Info** | Already aligned·observation only — **do not target rows** in this Epic A implementation. |

**Drift question:** "Is this drift?" → read mini-audit §5·exception table first. **If in B**, answer axis is "fixed as MVP exception".

---

## Allowed (In Scope)

- **A-classified rows only** — only items fixed as **A** in [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) §5.4 and related plan ([02_pipeline_recovery_control_flow.md](./02_pipeline_recovery_control_flow.md)) are code change targets.
- **Current PR A row list** — [epic_a_active_rows.md](./epic_a_active_rows.md) (§5.3 snapshot; when A is 0, do not force canonical recovery in code).

---

## Forbidden (Out of Scope)

- **B-classified rows** — triggers·paths in [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md). If needed, **link only** in comments·contract tests; no behavior change (reclassification needs separate review·doc update).
- **Info rows** — same as exception doc header: `post_reclaim_pass3_connectivity_break`, `reclaim_incremental_failure`, etc. **Info** classification is outside this Epic A implementation scope.
- **Routing heuristics** — outside Epic A (separate Epic·plan).
- **Pass3 scoring** — same.
- **Reclaim thresholds** — same.
- **Corridor lifecycle** — Epic C territory; no change in this scope.
- **Replay / event schema** — Epic D·trace layer; no change in this scope.

---

## Canonical Authority (Canonical·Audit)

| Document | Purpose |
|------|------|
| [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) **§5** | **Audit canonical** for §4.3 table·Expected·PR classification (A/B/Info) |
| [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md) | **B-only** single source of truth |
| `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` §4.3 | Algorithm canonical (original per mini-audit §5.1 links) |

---

## Implementation PR Checklist (Summary)

- [ ] Change target **directly corresponds** to an **A** row?
- [ ] Did not accidentally modify **B / Info / Forbidden** list above?
- [ ] If canonical·mini-audit changed, left issue to **re-copy** §5·update exception table **Revisit**?
