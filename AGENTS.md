# AGENTS.md

## Mission

shapez2 Factory Planner governance: short rules, strict contracts, small safe changes, fast verification, no stale-doc authority.

## DOX framework

DOX is the performant `AGENTS.md` hierarchy. Follow DOX across any edit.

### Core Contract

- `AGENTS.md` files are binding work contracts for their subtrees.
- Work products, source materials, instructions, records, assets, and durable docs must stay understandable from the nearest applicable `AGENTS.md` plus every parent above it.

### Read Before Editing

1. Read root `AGENTS.md`.
2. Identify every file or folder you expect to touch.
3. Walk from repository root to each target path.
4. Read every `AGENTS.md` found along each route.
5. If a parent lists a child `AGENTS.md` whose scope contains the path, read that child and continue from there.
6. Nearest `AGENTS.md` = local contract; parents = repo-wide rules.
7. Conflicts: closer doc controls local details; no child may weaken DOX.

Re-read the applicable DOX chain in the current session before editing. Do not rely on memory.

### Update After Editing

Every meaningful change requires a DOX pass before done. Update the closest owning `AGENTS.md` when a change affects purpose, scope, ownership, structure, contracts, workflows, I/O, permissions, artifacts, user preferences, or index contents. Update parents when parent-level structure or child index changes; update children when parent changes alter local rules. Remove stale text immediately. Small non-contract edits may leave docs unchanged, but the DOX pass still must happen.

### Hierarchy

- Root `AGENTS.md` = DOX rail: project-wide rules and Child DOX Index.
- Child `AGENTS.md` files own domain-specific instructions and their own Child DOX Index.
- Closer doc = more specific and practical.

Default child section order: Purpose · Ownership · Local Contracts · Work Guidance · Verification · Child DOX Index.

### Style

Concise, current, operational. Stable contracts only — not diary entries. Broad rules in parents; concrete details in children. Delete stale notes; trim obvious repetition.

### Closeout

Re-check changed paths against the DOX chain · update nearest owning docs and affected parents/children · refresh Child DOX Index · remove contradictions · run verification when relevant · report docs intentionally left unchanged and why.

## Authority split

**AGENTS.md controls HOW to work. Spec/ADR controls WHAT is true.**

| Kind | Order |
|------|-------|
| **Process** | user > `AGENTS.md` > `.cursor/rules/*.mdc` > skills > agent assumptions |
| **Domain** | user > current canon/spec/ADR > game_data/contracts > code evidence > older docs > agent memory |

Process and domain authority do not override each other across category.

## Child DOX Index

| Child `AGENTS.md` | Owns |
|-------------------|------|
| [`docs/AGENTS.md`](docs/AGENTS.md) | Session phases, kanban, workflow strictness, default workflow, validation, communication, delivery safety |
| [`django_apps/AGENTS.md`](django_apps/AGENTS.md) | Django apps layer (`shapez_core`, `shapez_solver`, `asteroid_lab`, `game_data`, `web`) |
| [`src/AGENTS.md`](src/AGENTS.md) | Hexagonal solver core, CLI boundary, SDD/testing for `shapez2_factory` |
| [`documents/AGENTS.md`](documents/AGENTS.md) | Canonical documents, plans, research, knowledge base |
| [`.cursor/AGENTS.md`](.cursor/AGENTS.md) | Cursor rules and skills |
| [`tests/AGENTS.md`](tests/AGENTS.md) | Test layout, golden, architecture boundary tests |
| [`frontend/AGENTS.md`](frontend/AGENTS.md) | Recipe graph editor, graph layout, Tailwind CSS source |

Path map SoT (not DOX): [`structure.md`](structure.md).

## Workflow (summary)

Normal+ pipeline: `align → contract → slice → implement → verify → STOPPED_AT_APPROVED_SCOPE`. Classify strictness first. Every task/chat: one kanban card in `.devtool/features/`. Full workflow, validation commands, delivery safety modes: [`docs/AGENTS.md`](docs/AGENTS.md).

## Shapez2 (summary)

Solver/Asteroid Lab domain authority wins. Glob match → `asteroid-lab-invariants.mdc`. Cross-module boundaries → `graphify.mdc` when graph exists. Detail: [`src/AGENTS.md`](src/AGENTS.md), [`django_apps/AGENTS.md`](django_apps/AGENTS.md).

## Scope / Permissions

Allowed: source, tests, docs, governance. Ask before `.env`, secrets, CI/deploy, security config, large delete/rename. Do not invent commands, tools, MCP behavior, or unverified pass claims.

## Validation

```bash
python manage.py check
powershell -File scripts/test_fast.ps1
mypy django_apps config src
```

Tiers and full commands: [`docs/AGENTS.md`](docs/AGENTS.md) § Verification.

## Governance

Root `AGENTS.md` target ~75 lines, max 120 before split. Nested `AGENTS.md` ≤150. `.cursor/rules/*.mdc` ≤75; detail in `docs/agent-workflows/`. Check: `scripts/check_governance.ps1`.

When blocked: `BLOCKED:` + context, risk, fixes tried, next step.

## User Preferences

Durable behavior changes: record here or in the relevant child `AGENTS.md`.
