---
title: Research Unlocks (Island Progression)
created: 2026-06-11
updated: 2026-06-11
type: concept
tags: [game-data-analysis, research]
sources: [raw/analysis/research_unlocks/00_summary.md]
confidence: high
---

# Research Unlocks

## Source
`documents/game_data/research_unlocks.json` — SHA256 in manifest. Unity runtime_reflection dump.

## Structure
- Island progression tree / research unlock definitions
- 253 `ShapeHash` references → all resolve to [[shape-data-model]] catalog
- Defines which shapes become available at each island/tech level

## Cross-References
- [[shape-data-model]]: ShapeHash values ⊆ full shape catalog
- [[island-mechanics]]: island progression gates unlock new research slots
