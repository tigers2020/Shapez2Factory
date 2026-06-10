# Graphify routine

Use the project knowledge graph before expensive codebase exploration.

## Artifacts

| Path | Use |
|------|-----|
| `graphify-out/graph.json` | Query, path, explain (preferred) |
| `graphify-out/GRAPH_REPORT.md` | God nodes, communities, inferred-edge audit |
| `graphify-out/graph.html` | Browser viz (skip if >5k nodes) |

Current scope built: `django_apps` + `src` (see `graphify-out/cost.json` runs).

## When to use graphify first

- Architecture, coupling, boundary, or SoT questions
- Cross-package paths (domain ↔ django_apps ↔ replay ↔ layers)
- Unfamiliar subsystem onboarding
- Trace reports (e.g. hub DTOs, god nodes)
- Before broad `grep` / multi-file read on >3 modules

## When graphify is optional

- User named exact file/function
- Single-file bug with stack trace
- Graph missing and task is one-line fix

## Agent commands (in order)

1. `graphify query "<question>"` — neighborhood / BFS context
2. `graphify path "A" "B"` — shortest coupling path
3. `graphify explain "Concept"` — one node + neighbors
4. Read `GRAPH_REPORT.md` sections only if 1–3 are insufficient

Chat: attach `/graphify` skill or ask agent to run the skill pipeline on a path.

## Rebuild / update

```powershell
# Full rebuild (subfolder recommended)
/graphify django_apps
/graphify src

# Code-only incremental (no LLM)
graphify update django_apps
graphify update src
```

Large corpus (>200 files or >2M words): subfolder only unless user confirms full repo.

## Honesty

- Tag **EXTRACTED** (AST/import) vs **INFERRED** (semantic) edges separately.
- Do not refactor from inferred edges alone — confirm with imports/calls/tests.
- `service_dtos` barrel imports often inflate inferred `uses` edges.

## Cursor skill

Skill: `graphify` (`.cursor/skills` or user attach). Rule router: `.cursor/rules/graphify.mdc`.
