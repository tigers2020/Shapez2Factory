# Execution scope contract (paste at top of plan-run prompts)

Copy the block below into the Cursor prompt when executing an approved plan. Replace task and validation placeholders.

```text
EXECUTION SCOPE CONTRACT

You are executing ONLY the approved tasks listed below.

Approved tasks:
- A: …
- B: …
- C: …
- D: …

Hard stop:
After D is complete, run only the validation commands listed in this prompt or the plan, produce the final report, and stop.

Forbidden:
- Do not create or execute D-1, D-2, D-3, or any additional subtask.
- Do not continue to "next", "follow-up", "cleanup", "refactor", "optimization", or "future phase".
- Do not implement anything listed as deferred work.
- Do not modify files outside the approved task scope.
- Do not expand the plan.

If additional issues are discovered:
- Record them under "Deferred Work".
- Do not fix them.
- Do not create tasks for them.
- Do not continue executing them.

Final response must include:
STOPPED_AT_APPROVED_SCOPE
```

## Short version

```text
Execute the approved plan exactly as written.

Hard boundary: tasks A, B, C, and D are the full scope.

After D:
1. Run only the listed validation commands.
2. Produce the final report.
3. Stop.

Do not create or execute D-1, D-2, follow-up, cleanup, refactor, optimization, or future-phase tasks.

If you discover extra work, list it under "Deferred Work" only. Do not implement it.

Final response must include:
STOPPED_AT_APPROVED_SCOPE
```

Authority: `AGENTS.md` § Agent Scope; `.cursor/rules/agent_scope.mdc`.
