---
title: Shapez2 Factory Planner — Knowledge Schema
created: 2026-06-11
updated: 2026-06-11
type: schema
tags: [meta]
---

# Wiki Schema

## Domain
Shapez2 Factory Planner 프로젝트의 종합 지식 베이스:
- 게임 도메인 (shape algebra, operations, buildings, transport, fluids)
- Game data 덤프 분석 (Unity 리플렉션 추출 결과)
- Solver/astroid lab 아키텍처 및 알고리즘 설계 결정
- Agent 워크플로우, governance, PR 계획 문서

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `transformer-architecture.md`)
- Every wiki page starts with YAML frontmatter (see below)
- Use `[[wikilinks]]` to link between pages (minimum 2 outbound links per page)
- When updating a page, always bump the `updated` date
-Every new page must be added to `index.md` under the correct section
- Every action must be appended to `log.md`
- **Provenance markers:** On pages that synthesize 3+ sources, append `^[raw/articles/source-file.md]`
  at the end of paragraphs whose claims come from a specific source.

## Frontmatter
```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary
tags: [from taxonomy below]
sources: [raw/articles/source-name.md]
confidence: high | medium | low
contested: true
contradictions: [other-page-slug]
---
```

## Tag Taxonomy
- **Game domain:** shape-algebra, operations, buildings, transport, fluids, crystals, island, items, materials, research
- **Data:** game-data-dump, game-data-analysis, schema-reconstruction
- **Solver/Algo:** solver, asteroid-lab, gene-seed, golden-loop, optimization, routing
- **Agent/Governance:** agent-workflow, pr-plan, adr, governance, testing
- **Meta:** comparison, timeline, architecture

Rule: every tag on a page must appear in this taxonomy. If a new tag is needed, add it here first.

## Page Thresholds
- **Create a page** when an entity/concept appears in 2+ sources OR is central to one source
- **Add to existing page** when a source mentions something already covered
- **DON'T create a page** for passing mentions, minor details
- **Split a page** when it exceeds ~200 lines
- **Archive a page** when superseded — move to `_archive/`, remove from index

## Update Policy
When new information conflicts with existing content:
1. Check dates — newer sources supersede older ones
2. If contradictory, note both positions with dates and sources
3. Mark contradiction in frontmatter: `contradictions: [page-name]`
4. Flag for user review in lint report
