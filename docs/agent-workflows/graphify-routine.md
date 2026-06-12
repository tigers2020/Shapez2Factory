# Graphify routine

Use the project knowledge graph before expensive codebase exploration.

## Artifacts

| Path | Use |
|------|-----|
| `graphify-out/graph.json` | Query, path, explain (preferred) |
| `graphify-out/GRAPH_REPORT.md` | God nodes, communities, inferred-edge audit |
| `graphify-out/graph.html` | Browser viz (community meta if >5k nodes) |
| `graphify-out/obsidian/` | Local-only Obsidian export (`graphify --obsidian`); gitignored — open **this** folder, not `graphify-out/` root |

Current scope built: `django_apps` + `src`. Freshness: `built_at_commit` in `graph.json` vs `git rev-parse --short HEAD`.

## Code Search Routing — Graphify First

When `graphify-out/graph.json` exists, repository exploration **must** start from Graphify documentation and Graphify commands before using SemanticSearch, Grep, or direct file reads.

### Required order

1. Read the local Graphify guidance first:
   - `AGENTS.md` § Tool Routing
   - `.cursor/rules/graphify.mdc`
   - `docs/agent-workflows/graphify-routine.md` (this file)

2. Run broad graph navigation:

   ```bash
   graphify query "<question>"
   ```

3. For module coupling or dependency questions:

   ```bash
   graphify path "<source/module>" "<target/module>"
   ```

4. For concept ownership or neighboring modules:

   ```bash
   graphify explain "<concept>"
   ```

5. If steps 2–4 are insufficient, inspect `graphify-out/GRAPH_REPORT.md` (god nodes, surprises — not full dump).

6. Use Grep, SemanticSearch, or direct file reads only after Graphify has identified candidate files/modules, or when an explicit exception applies.

Chat: attach `/graphify` skill or ask agent to run the skill pipeline on a path.

### Grep / SemanticSearch exceptions

Grep, SemanticSearch, or direct reads are allowed first only when:

- The user provides an exact file, function, class, symbol, or stack trace.
- Graphify data is missing, stale, or does not contain the needed area.
- The task is a single-file bug fix with a known location.
- Graphify result is `EXTRACTED` and grep is only used to confirm imports, calls, or exact symbol usage.

### Staleness rule

If code changed after the graph was built, update the graph before relying on it:

```bash
graphify update src
graphify update django_apps
```

Do not treat `graphify-out/graph.json` as current if its build commit (see `GRAPH_REPORT.md` § Graph Freshness) is older than the code under investigation. Compare with `git rev-parse HEAD`.

### Anti-pattern

Do not start broad repository exploration with SemanticSearch, Grep, or opening random likely files when a valid `graphify-out/graph.json` exists.

**Graphify is the map. Grep is the microscope.**

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
