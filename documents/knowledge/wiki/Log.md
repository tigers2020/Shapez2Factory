# Knowledge Log

Append-only chronological record. Newest entries at the bottom.

## [2026-06-11] bootstrap | Initial knowledge layer

- Created `documents/knowledge/` (raw / wiki / outputs)
- Added `Index.md`, `Processed.md`, append-only `Log.md`
- Added `docs/agent-workflows/dream-sequence.md`
- Linked from `AGENTS.md`; workflow in `.cursor/skills/llm-wiki/`

## [2026-06-11] update | Index 복구 — concepts 7개 페이지 등록

- `Index.md`: concepts 섹션에 7개 페이지 추가 (shape, building, transport, fluid, materials, items, research)
- Empty Sources 섹션 제거 → Comparisons, Queries 섹션으로 대체
- Total pages: 7, Last updated: 2026-06-11

## [2026-06-11] lint | Full health check — 12 issues found

### HIGH (7): Broken wikilinks to non-existent concept pages
- `asteroid-lab-algorithm`, `building-groups`, `building-variants`, `game-data-manifest`,
  `island-mechanics`, `prefabs`, `transport-capacity` — 위키 초기 상태, source ingest 필요

### MEDIUM (4): Cross-reference 부족
- orphan: `materials-data-model` (inbound 링크 0)
- few_refs (<2 outbound to existing pages): `building-definitions`(0), `research-unlocks`(1), `transport-system`(1)

### LOW (1): Bad tag
- `'research'` 태그가 taxonomy 미등록 — SCHEMA.md에 추가하거나 페이지 frontmatter 수정 필요

### PASS: Index completeness(7/7), Frontmatter(validation OK), Page size(최대 41줄)

## [2026-06-11] ingest | 2026 vibe coding + MCP web research

- **Input:** User `/llm-wiki` + web search (15 URLs)
- **Raw:** `raw/2026-06-11-vibe-coding-mcp-web-research.md` (SHA256 `1c924409…c98d1`)
- **Wiki:** `concepts/vibe-coding-agentic-engineering-2026.md`, `concepts/mcp-servers-cursor-2026.md`
- **Index:** +2 concepts, +2 queries, Sources table
- **Uncertainty:** Cursor tool limits / marketplace dates marked unverified in wiki

## [2026-06-11] dream-sequence | Wiki refresh + typing/graphify ingest

- **Input:** `/llm-wiki update`; session handoff (Phase 0/1/#280, Phase 4/#283, graphify guidance)
- **Scan:** `raw/general_workflow_and_skill.md` present (untracked) — skipped as duplicate generic Cursor content
- **Orphans fixed:** Index now lists `building-groups`, `prefabs`, `game-data-manifest` (pages existed, Index lagged)
- **Wiki created:**
  - `concepts/asteroid-lab-algorithm.md` — L2–L5 hub; fixes broken wikilink from [[transport-system]]
  - `concepts/asteroid-lab-wire-typing.md` — wire boundary + mypy rollout status
  - `concepts/graphify-architecture-map.md` — scoped updates, GRAPH_STALE, module-level granularity
- **Index:** 9 → 15 concept rows; +2 queries; canon Sources table; Open questions for missing analysis pages
- **Processed:** +4 ledger rows (3 ingested, 1 skipped)
- **Uncertainty:** graphify node/edge counts marked inference; Phase 2+ typing deferred per design spec
- **Remaining:** `building-variants`, `island-mechanics`, `transport-capacity` — raw exists, wiki deferred

## [2026-06-11] policy | Graphify `_private` granularity canon

- **Input:** architect advisory — default exclude `_internal`; Level 2/3 selective include
- **Canon:** `docs/agent-workflows/graphify-routine.md` § Granularity policy
- **Wiki:** `graphify-architecture-map.md` expanded (include/exclude tables, cutoff)
- **Filters:** `.graphifyignore` + `tests/**`; header points to routine
- **Uncertainty:** graphify tool has no per-symbol `_` toggle yet — policy is agent scope discipline
