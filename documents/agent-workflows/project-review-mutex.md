# Project Review Run Mutex

Periodic project review automation uses a global mutex so concurrent cron or manual runs cannot overlap, re-review the same modules, or file duplicate Linear issues.

**Holder card:** [SHA-67](https://linear.app/zkaufman/issue/SHA-67/automation-project-review-run-mutex-via-dedicated-linear-holder-card) — infrastructure only. Review runs add/remove the lock label here; they must not triage or implement product work from this card.

**Parallel pattern:** Backlog triage uses `auto:backlog-triage-running` on its holder card (see SHA-63/65 verification cards). Project review uses `auto:project-review-running` on SHA-67 only.

**Run history examples:** [daily-project-inspection-log.md](./daily-project-inspection-log.md)

---

## Hard concurrency rules (non-negotiable)

1. **One run = one review pass** — do not drain multiple areas in a loop beyond the single rotation pick for this invocation.
2. **Global mutex** — before work, `list_issues` on team Shapez2Factory with label `auto:project-review-running`. If any issue was `updatedAt` within the last **45 minutes**, exit immediately. Report `Status: blocked`, reason `concurrent-run`.
3. **Per-run lock** — immediately after the gate passes, add label `auto:project-review-running` to **SHA-67 only** (preserve all existing labels on SHA-67).
4. **`finally` cleanup** — always remove `auto:project-review-running` from SHA-67 when the run ends (success, skip, or failure). Never leave the label stuck.
5. **Skip `reviewing`** — during review scans and duplicate checks, skip Linear issues labeled `reviewing`.

Set Cursor Automation **concurrency = 1** if the UI exposes it. Use **either** the built-in Linear trigger **or** `scripts/linear_cursor_webhook_bridge.py` — not both.

---

## Run sequence

1. Global mutex gate (see above).
2. Add `auto:project-review-running` to SHA-67.
3. Read `.agent-loop/reviewed-areas.md` before picking an area.
4. Pick one unreviewed area; run inspection; file findings to Linear (skip issues labeled `reviewing`).
5. Append a dated entry to `.agent-loop/reviewed-areas.md` after a successful pass (path/module, skipped areas, findings filed, notes).
6. In `finally`: remove `auto:project-review-running` from SHA-67.
7. On failure before `finally`, comment on SHA-67 with the failure reason.

---

## Memory file contract

File: `.agent-loop/reviewed-areas.md`

- **Before each run:** read the full file to avoid duplicate filings.
- **After each successful pass:** append a section matching existing format (`## YYYY-MM-DD HH:MM`, Reviewed area, Skipped, Findings, Notes).
- **Skip convention:** issues labeled `reviewing` are in-flight elsewhere; do not file duplicate cards for them.

---

## Stale lock recovery

The 45-minute window is time-based. If a run crashes before `finally`, the label may remain on SHA-67 until:

- the window expires, or
- an operator manually removes `auto:project-review-running` from SHA-67.

Document manual recovery in run comments when a failure prevents `finally` cleanup.

---

## Final run report

Every project review automation run must end with:

```text
Status: complete | partial | blocked

Trigger: project-review cron | manual

Mutex holder: SHA-67
Lock label: auto:project-review-running (added/removed)

Reviewed area: <path/module>
Findings filed: SHA-NN, ...
Memory updated: yes | no

Blocked/skipped: <reason>
Failures: ...
```

Align report wording with backlog triage and todo-plan automation reports where possible.
