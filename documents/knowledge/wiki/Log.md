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
