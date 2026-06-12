---
title: Graphify Architecture Map (Operating Notes)
created: 2026-06-11
updated: 2026-06-12
type: concept
tags: [architecture, agent-workflow]
sources: [.cursor/rules/graphify.mdc, docs/agent-workflows/graphify-routine.md, graphify-out/graph.json]
confidence: high
---

# Graphify Architecture Map

**Canon:** `docs/agent-workflows/graphify-routine.md` § Granularity policy. Wiki = retrieval summary.

## Default answer

**No** — do not track every `_internal` / `_private` function repo-wide. Large graphs (>5k nodes) skip `graph.html` and produce Obsidian noise (`__init__.py_N`).

`graphify-out/` is **not** globally junk. **Track** `graph.json`, `GRAPH_REPORT.md`, `manifest.json` (portable). **Ignore / safe clean:** `cost.json`, `cache/`, `.graphify_detect.json`, dated snapshots, wrong-CWD `*/graphify-out/`, generated `obsidian/` export, `.obsidian/` machine state. Navigation graph ≠ source of truth for domain contracts.

```text
graphify is a navigation graph, not a complete call graph
```

## Three graph levels

| Level | Include | `_private` | Purpose |
|-------|---------|------------|---------|
| 1 — default exploration | module, class, public function | exclude | "Where should I look?" |
| 2 — solver/replay precision | `django_apps/asteroid_lab/replay/**`, `src/shapez2_factory/**` | selective | "Where does contract drift happen?" |
| 3 — bug trace (temporary) | one failing package | include around failure | "What is the real call chain?" |

## Include `_` when (source)

| Signal | Why |
|--------|-----|
| routing / replay / serializer core helper | contract hidden inside |
| shared `_helper` used by multiple public APIs | coupling |
| cross-module import of `_name` | not truly private |
| validation / invariant / boundary assert | design rules |
| bug-prone internal transform | debug value |

Examples: `_effective_cell_to_wire_parts`, `_classify_transport_component`, `_assert_overlay_wire_contract`.

## Exclude `_` when (source)

| Signal | Why |
|--------|-----|
| one-off formatting / sort keys | noise |
| UI event glue | low architecture signal |
| test fixture builder internals | test graph explosion |
| trivial dict coercion | edge spam |
| nested local functions | no structure signal |
| migrations / generated dumps | graph blow-up |

Examples: `_format_label`, `_sort_key`, `_parse_int_or_none`.

## Cutoff rule

```text
public API explains architecture     → exclude _
_ owns contract/invariant/wire/route → include
glue / formatting / one-off            → exclude
```

## Artifacts & freshness

| Path | Use |
|------|-----|
| `graphify-out/graph.json` | query / path / explain |
| `graphify-out/GRAPH_REPORT.md` | god nodes, communities |
| `graphify-out/graph.html` | skipped when nodes > 5000 |

`built_at_commit` vs `git rev-parse --short HEAD` → `GRAPH_STALE` if mismatch.

## Repo filters

`.graphifyignore`: migrations, static/vendor, images, `graphify-out/**`, `tests/**` (fixture noise).

Prefer scoped update: `graphify update django_apps/asteroid_lab/replay`.

## Cross-References

- [[asteroid-lab-wire-typing]]: Level 2 precision target
- [[asteroid-lab-algorithm]]: `src/` layer modules
