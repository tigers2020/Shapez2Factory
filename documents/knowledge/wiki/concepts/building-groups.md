---
title: Building Groups
created: 2026-06-11
updated: 2026-06-11
type: concept
tags: [buildings, game-data-analysis]
sources: [raw/analysis/building_groups/00_summary.md, documents/game_data/building_groups.json]
confidence: high
---

# Building Groups

## Source
`documents/game_data/building_groups.json` — 13 MB. Manifest SHA256 `c39e4b...`. Unity runtime_reflection v2 export.

## 구조
- **Array of 67 building definition groups** — player-facing buildable families
- 각 요소: `stable_id` (64-char hex PK), `source_guid`, `definition_snapshot`, `simulation_parameters`
- `source_type_name`: 항상 `BuildingDefinitionGroup`
- 최대 nesting depth: ~8+ under `definition_snapshot`

## 멤버 분포

| Partitions | Count | 키 |
|---------|-----|---|
| Building groups | 67 | `source_guid` / `definition_snapshot.Id.Id` |
| Embedded members | 131 total | `definition_snapshot.Definitions[]` |
| — Full variants | 97 | `Definitions[i].Id.Name` present |
| — Cycle placeholders | 34 | `$cycle`만 있음 |
| Transport groups | 12 | `IsTransportBuilding: true` |

## Definitions 크기 분포 (per group)
| Members | Groups |
|---------|--------|
| 1 | 37 |
| 2 | 23 |
| 3 | 1 |
| 4 | 2 |
| 8 | 3 |
| 13 | 1 |

## 교차 참조
| 파일 | 관계 |
|------|------|
| `buildings.json` | 67/67 same `source_guid`; identical snapshots |
| `building_variants.json` | 97 embedded by `Id.Name`; 34 `$cycle` aliases |
| `research_unlocks.json` | 모든 67 `source_guid` 파일 텍스트 등장 |
| `toolbar_entries.json` | 57/67 source_guid 매칭 |

## Cross-references
- [[building-definitions]] — parent group definition
- [[building-variants]] — members via Definitions[]
- [[research-unlocks]] — 67 group guids unlock tree에서 등장
- [[game-data-manifest]] — dump provenance
