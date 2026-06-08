# Agent Governance Acceptance

Run after governance rule changes:

```powershell
powershell -File scripts/check_governance.ps1
```

## Checklist

- [ ] `AGENTS.md` <= 75 lines
- [ ] every `.cursor/rules/**/*.mdc` <= 75 lines
- [ ] `agent_scope.mdc` has Hermes handoff exception
- [ ] Shapez2 pipeline defined in `docs/agent-workflows/hermes-skill-suggestion.md`
- [ ] grill/Hermes conflict → surface to user (same doc)
- [ ] `root.mdc` routes Hermes workflow and handoff routers
- [ ] `hermes-handoff.md` has full `SKILL_SUGGESTION` contract
- [ ] `skill-trust-boundary.md` defines draft vs approved paths
- [ ] handoff docs defer validation to `AGENTS.md` § Validation
- [ ] markers present: `PLAN_TO_SKILL_REQUEST`, `SKILL_SUGGESTION`, `SKILL_APPLICATION_SUMMARY`

## Rule conflict scenarios

| Scenario | Expected behavior |
|----------|-------------------|
| User: "implement X" only | Hermes handoff allowed as prep, not extra impl scope (`agent_scope.mdc`) |
| User: "skip Hermes" | Skip Hermes workflow |
| grill reject, Hermes suggests proceed | Surface conflict; no silent choice |
| Unreviewed SKILL_SUGGESTION | Draft only; no implementation guide |
