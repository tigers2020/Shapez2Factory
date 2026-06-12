---
title: Graphify Architecture Map (Operating Notes)
created: 2026-06-11
updated: 2026-06-11
type: concept
tags: [architecture, agent-workflow]
sources: [.cursor/rules/graphify.mdc, graphify-out/graph.json]
confidence: medium
---

# Graphify Architecture Map

**Canon for workflow:** `.cursor/rules/graphify.mdc`, `docs/agent-workflows/graphify-routine.md`. Wiki = operating summary.

## Artifacts

| Path | Use |
|------|-----|
| `graphify-out/graph.json` | Query / path / explain |
| `graphify-out/GRAPH_REPORT.md` | God nodes, communities |
| `graphify-out/graph.html` | Browser viz — **skipped when nodes > 5000** |

Compare `built_at_commit` in `graph.json` to `git rev-parse --short HEAD`. Mismatch → `GRAPH_STALE` (hint only).

## Scope (inference)

- Primary targets: `django_apps/`, `src/` architecture
- `.graphifyignore` excludes migrations, static assets, caches
- **Module/converter-level granularity is enough** — tracking every internal function adds noise without contract value
- Prefer scoped updates: `graphify update django_apps/asteroid_lab/replay` after replay edits

## Last known rebuild (source)

- Commit: `cc33840a` (`inference` from session handoff)
- ~5160 nodes, 8593 edges after incremental AST update
- Full-repo update pruned ghost nodes from deleted paths

## Agent read order

1. `graphify query` / `path` / `explain`
2. `GRAPH_REPORT.md` (sections only)
3. Grep/read on graph-identified candidates — skip wide grep when graph is fresh

## Cross-References

- [[asteroid-lab-wire-typing]]: replay package boundary for scoped graphify
- [[asteroid-lab-algorithm]]: layer modules in `src/`
