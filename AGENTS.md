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

**Phases** = what to do (HITL/AFK, contract, scope). **DOX** = which `AGENTS.md` chain to read before edits and update at verify when contracts change. **Kanban** = one feature-thread card per task/chat. Integrated map: [`docs/agent-workflows/workflow-phases.md`](docs/agent-workflows/workflow-phases.md) § Workflow + DOX. DOX detail: [`docs/agent-workflows/dox-framework.md`](docs/agent-workflows/dox-framework.md) · `dox-framework.mdc`.

## Task routing & workflow

Classify strictness first; match gates to mode (Read-only / Tiny / Normal / High-risk / Ops). Default workflow applies to Normal and High-risk.

Detail: [`docs/AGENTS.md`](docs/AGENTS.md) · [`docs/agent-workflows/workflow-strictness.md`](docs/agent-workflows/workflow-strictness.md).

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

When: [`docs/agent-workflows/validation-routine.md`](docs/agent-workflows/validation-routine.md). PR/full: `scripts/test_full.ps1`. Solver smoke: `python manage.py run_solver --slug <slug>`.

## Communication

English for work. Korean summary, compressed (`caveman.mdc`).

## Scope / Permissions

Allowed: source, tests, docs, governance. Ask before `.env`, secrets, CI/deploy, security config, large delete/rename. Closed-world scope: `agent_scope.mdc`. Delivery safety: `workflow-safety.mdc`.

## Governance

Root target ~75 lines; max 120 before split. Nested `AGENTS.md` ≤150. `.cursor/rules/*.mdc` ≤75. Repository map SoT: [`structure.md`](structure.md). Detail: [`docs/agent-workflows/governance-acceptance.md`](docs/agent-workflows/governance-acceptance.md). Check: `scripts/check_governance.ps1`.

When blocked: `BLOCKED:` + context, risk, fixes tried, next step.

## Child DOX Index

**Canonical SoT** for top-level children — edit here only; do not duplicate this table elsewhere.

| Child | Scope |
|-------|-------|
| [`docs/AGENTS.md`](docs/AGENTS.md) | Workflow, kanban, validation tiers |
| [`django_apps/AGENTS.md`](django_apps/AGENTS.md) | Django runtime apps |
| [`src/AGENTS.md`](src/AGENTS.md) | Solver core (hexagonal, Django-free) |
| [`tests/AGENTS.md`](tests/AGENTS.md) | Test layout and contracts |
| [`frontend/AGENTS.md`](frontend/AGENTS.md) | Client-side source |
| [`documents/AGENTS.md`](documents/AGENTS.md) | Document authority and wiki |
| [`.cursor/AGENTS.md`](.cursor/AGENTS.md) | Rules and skills |
