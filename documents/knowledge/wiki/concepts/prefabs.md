---
title: Prefabs Registry
created: 2026-06-11
updated: 2026-06-11
type: concept
tags: [buildings, game-data-analysis]
sources: [raw/analysis/prefabs/00_summary.md, documents/game_data/prefabs.json]
confidence: high
---

# Prefabs Registry

## Source
`documents/game_data/prefabs.json` — 225 KB. Manifest SHA256 `c73e36...`. Unity runtime_reflection v2 export.

## 구조
- **Array of 764 prefab content records** — visual/mesh/transport prefab 레지스트리
- 각 요소: `stable_id` (64-char hex, 764 unique PK), `source_type_name`, `source_guid`, `source_path`, `display_name_key`, `prefab_path`
- `source_type_name`: 항상 `UnityEngine.Object` — 도메인 엔티티 이름 아님
- `prefab_path == source_path == display_name_key` (100% 일치)

## 주요 객체 그룹
| Prefix/패턴 | 대략 수량 | 역할 |
|-------------|----------|------|
| `Wire*` | 140 | 와이어 트랜스포트 시각화 |
| `Pipe*` | 68 | 유체 파이프 시각화 |
| `LogicGate*` | 43 | 로직 빌딩 меш |
| `Lift*` | 31 | 리프트 변종 |
| `*LOD*` | 521 | 레벨-오브-디테일 meshes |
| `*BakedMesh*` | 275 | 베이킹(mesh representations) |

## 교차 참조
| 파일 | 관계 |
|------|------|
| `asset_references.json` | 764개 `asset_type: prefab` rows; `ref_stable_id` 전체 매칭 |
| `building_variants.json` | 131 변종 — mesh LOD 이름의 약한 문자열 중복 |
| `materials.json` / `sprites.json` | 형제 콘텐츠 레지스트리 |

## Cross-references
- [[building-varients]] — 131 variants와의 mesh 경계 명확히 필요
- [[game-data-manifest]] — dump provenance 및 무결성 기준
