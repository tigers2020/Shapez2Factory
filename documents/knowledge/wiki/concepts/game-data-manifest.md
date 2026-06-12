---
title: Game Data Manifest
created: 2026-06-11
updated: 2026-06-12
type: concept
tags: [game-data-dump, game-data-analysis]
sources: [raw/game-data-docs/manifest.md, documents/game_data/manifest.json]
confidence: high
---

# Game Data Manifest

## Source
`documents/game_data/manifest.json` — 24 KB. Unity dump 메타데이터의 단일 소스 오브 트루스.

## 구조
- **Root object**: 10 keys (`assembly_hashes`, `dump_mod_version`, `dump_schema_version`, `dump_timestamp_utc`, `file_hashes`, `game_version`, `incomplete_sections`, `source_method`, `unity_version`, `warnings`)
- `file_hashes`: 각 game_data JSON 파일의 SHA256 해시 — import 무결성 검증 기준
- `assembly_hashes`: Unity DLL 어셈블리 sha256 맵 (~68개 엔트) — 게임 빌드 버전 추론 사용
- `game_version`:Dump 대상 Shapezi 2.14

## 게임 데이터 덤프 프로퍼티

## 신뢰도 해시
모든 game_data JSON은 manifest SHA256이 일치해야 유효. 변경 감지 기준: dump_schema_version, incomplete_sections — translations 등 일부 섹션 미완성 상태임.

## Glossary count anchors (`file_hashes`)

Wiki entity counts (67 groups, 131 variants, 1,170 shapes, etc.) are valid **only** for the manifest generation they were analyzed against. On reimport, re-verify:

| Wiki concept | game_data file | Manifest field |
|---|---|---|
| [[building-groups]] / [[building-definitions]] | `building_groups.json`, `buildings.json` | `file_hashes` entry |
| [[building-variants]] | `building_variants.json` | `file_hashes` entry |
| [[shape-data-model]] | `shapes.json` | `file_hashes` entry |
| [[prefabs]] | `prefabs.json` | `file_hashes` entry |
| [[transport-system]] | `belts_pipes_transport.json` | `file_hashes` entry |

If hash drifts, update wiki counts from fresh `raw/analysis/*/00_summary.md` — do not assume stale numbers.

## Cross-references
- [[shape-data-model]] — shapes.json의 manifest hash 참고
- [[building-definitions]] — buildings.json 메타데이터 출처
- [[transport-system]] — belts_pipes_transport.json dumps
