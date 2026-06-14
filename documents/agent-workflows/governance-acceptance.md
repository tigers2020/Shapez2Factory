# Agent Governance Acceptance

Run after governance rule changes:

```powershell
powershell -File scripts/check_governance.ps1
```

## Checklist

- [ ] root `AGENTS.md` target ~75 lines, max 120 before split
- [ ] nested `AGENTS.md` max 150 (module-local rules); split past 150
- [ ] every `.cursor/rules/**/*.mdc` <= 75 lines (thin routers)
- [ ] `root.mdc` routes `workflow.mdc`, `agent_scope.mdc`, and `ops-recovery.mdc`
- [ ] `AGENTS.md` separates process vs domain authority
- [ ] `documents/agent-workflows/dox-framework.md` exists; `dox-framework.mdc` routes to it
- [ ] `workflow-phases.md` § Workflow + DOX integrates phases, DOX, and kanban
- [ ] top-level Child DOX Index lives only in root `AGENTS.md` § Child DOX Index (no duplicate table in `dox-framework.md`)
- [ ] protected paths documented: `var/plan-run/**`, `.worktrees/**`, `plans/**`
- [ ] `documents/agent-workflows/workflow-strictness.md` exists; `AGENTS.md` § Workflow strictness routes to it
- [ ] handoff docs defer validation to `AGENTS.md` § Validation
