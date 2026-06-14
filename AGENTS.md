# AGENTS.md

## Mission

shapez2 Factory Planner governance: short rules, strict contracts, small safe changes, fast verification, no stale-doc authority.

## Authority split

**AGENTS.md controls HOW to work. Spec/ADR controls WHAT is true.**

| Kind | Order |
|------|-------|
| **Process** | user > `AGENTS.md` > `.cursor/rules/*.mdc` > skills > agent assumptions |
| **Domain** | user > current canon/spec/ADR > game_data/contracts > code evidence > older docs > agent memory |

Process and domain authority do not override each other across category.

## Workflow & DOX

```text
align → contract → slice → implement → verify → STOPPED_AT_APPROVED_SCOPE
```

**Phases** = what to do (HITL/AFK, contract, scope). **DOX** = which `AGENTS.md` chain to read before edits and update at verify when contracts change. **Kanban** = one feature-thread card per task/chat. Integrated map: [`documents/agent-workflows/workflow-phases.md`](documents/agent-workflows/workflow-phases.md) § Workflow + DOX. DOX detail: [`documents/agent-workflows/dox-framework.md`](documents/agent-workflows/dox-framework.md) · `dox-framework.mdc`.

## Task routing & workflow

Classify strictness first; match gates to mode (Read-only / Tiny / Normal / High-risk / Ops). Default workflow applies to Normal and High-risk.

Detail: [`documents/AGENTS.md`](documents/AGENTS.md) · [`documents/agent-workflows/workflow-strictness.md`](documents/agent-workflows/workflow-strictness.md).

## Shapez2

Solver/Asteroid Lab: domain authority wins. Glob match → `asteroid-lab-invariants.mdc`. Cross-module → `graphify.mdc`. Detail: [`src/AGENTS.md`](src/AGENTS.md), [`django_apps/AGENTS.md`](django_apps/AGENTS.md).

## Validation

```bash
python manage.py check
powershell -File scripts/test_fast.ps1
ruff check .
mypy django_apps config src
black --check .
```

When: [`documents/agent-workflows/validation-routine.md`](documents/agent-workflows/validation-routine.md). PR/full: `scripts/test_full.ps1`. Solver smoke: `python manage.py run_solver --slug <slug>`.

## Communication

English for work. Korean summary, compressed (`caveman.mdc`).

## Scope / Permissions

Allowed: source, tests, docs, governance. Ask before `.env`, secrets, CI/deploy, security config, large delete/rename. Closed-world scope: `agent_scope.mdc`. Delivery safety: `workflow-safety.mdc`.

## Governance

Root target ~75 lines; max 120 before split. Nested `AGENTS.md` ≤150. `.cursor/rules/*.mdc` ≤75. Repository map SoT: [`structure.md`](structure.md). Detail: [`documents/agent-workflows/governance-acceptance.md`](documents/agent-workflows/governance-acceptance.md). Check: `scripts/check_governance.ps1`.

When blocked: `BLOCKED:` + context, risk, fixes tried, next step.

## Child DOX Index

**Canonical SoT** for top-level children — edit here only; do not duplicate this table elsewhere.

| Child | Scope |
|-------|-------|
| [`documents/AGENTS.md`](documents/AGENTS.md) | Documents tree: workflow, AI manuals, templates, wiki, plans, architecture, superpowers |
| [`django_apps/AGENTS.md`](django_apps/AGENTS.md) | Django runtime apps |
| [`src/AGENTS.md`](src/AGENTS.md) | Solver core (hexagonal, Django-free) |
| [`tests/AGENTS.md`](tests/AGENTS.md) | Test layout and contracts |
| [`frontend/AGENTS.md`](frontend/AGENTS.md) | Client-side source |
| [`.cursor/AGENTS.md`](.cursor/AGENTS.md) | Rules and skills |
