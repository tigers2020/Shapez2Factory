---
status: AUDIT
owner: asteroid-lab
last_reviewed: 2026-05-22
language: ko
dump_source: game_data_backup/game_data_dump.json
related_docs:
  - asteroid_lab_mining_installation/00_source_of_truth.md
  - asteroid_lab_mining_installation/01_rule_reconciliation.md
  - docs/domain/asteroid_game_data_snapshot.md
---

# DB 교차 참조 — 채굴기·확장기·운송

고정 import dump 기준 **층 A**(정규화 ORM)와 **층 B**(반영·반구조화 행). 여기 내용이 바뀌면 [`01_rule_reconciliation.md`](01_rule_reconciliation.md) 판정을 갱신한다.

**목록 재생성 명령:**

```powershell
rg "ShapeMiner|FluidMiner|MinerExtension|ExtractorDefault|PumpDefault" game_data_backup/game_data_dump.json
```

## 층 A — `game_data` 정규화 테이블

| 테이블 | miner 관련 키 (이 dump) | 비고 |
|--------|-------------------------|------|
| `game_data.buildingvariant` | `ExtractorDefaultInternalVariant`, `PumpDefaultInternalVariant` | Miner/Extractor/Pump 이름 필터에 걸린 internal variant는 dump에서 2종뿐 |
| `game_data.buildingfootprinttile` | `variant:ExtractorDefaultInternalVariant:tile:0` (x=0,y=0); `variant:PumpDefaultInternalVariant:tile:0` (x=0,y=0) | variant당 타일 1개 |
| `game_data.buildingconnector` | 위 variant에 연결된 2행 | `canonical_id` 접두사 참고 |
| `game_data.buildinggroup` | `ExtractorDefaultVariant`, `PumpDefaultVariant` | internal variant 멤버 그룹 |
| `game_data.buildinggroupmember` | 위 그룹 멤버 | dump 전체 variant 행 131 |
| `game_data.toolbarbuildingplacement` | miner toolbar 노드 참조 placement | dump 합계 78 |
| `game_data.toolbartreenode` | `ExtractorDefaultVariant`, `PumpDefaultVariant`, `ShapeMinerExtractorsGroup`, `ShapeMinerChainsGroup`, `FluidMinerExtractorsGroup`, `FluidMinerChainsGroup` | 섬/toolbar 분류 |
| `game_data.toolbarelement` | miner 노드에 연결된 action (hash id) | `toolbartreenode`와 짝 |
| `game_data.transportbuildingregistry` | belt/pipe transport kind (PR-1 확장) | `AsteroidGameDataSnapshot.transport_registry`와 대조 |

### Blueprint `Layout_*` 이름 vs DB

디코드된 copy code는 `Layout_ShapeMiner`, `Layout_FluidMiner`, `Layout_*MinerExtension` 등을 쓴다 (`django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py`). **이 문자열은 이 dump의 `buildingvariant.internal_name` 행이 아니다.** Lab 최적화 geometry는 `GeneTemplate` + footprint import를 쓰며, raw `Layout_*` 타입 문자열을 그대로 쓰지 않는다.

| 표면 | 식별자 스타일 | 이 dump에 있음? |
|------|---------------|----------------|
| Blueprint 디코드 | `Layout_ShapeMiner`, `Layout_FluidMinerExtension` 등 | 붙여넣기·샘플 경로, variant 테이블 아님 |
| 정규화 DB | `ExtractorDefaultInternalVariant`, `PumpDefaultInternalVariant` 등 | 예 (층 A) |
| Lab 코드 | `GeneTemplate`, `VALID_THROUGHPUT_FACTORS` | 코드만 (층 C) |

## 층 B — 반영·반구조화

| 소스 | miner 관련 `type_name` / 키 (샘플) | 용도 |
|------|-----------------------------------|------|
| `game_data.unknownproperty` | `ShapeMinerMetadata`, `ShapeMinerExtensionMetadata`, `FluidMinerExtensionMetadata`, `*PlacementHelper`, `*SidePanelModuleDataProvider`, `*DynamicDrawer` 등 | 배치·메타데이터 반영 — 아직 스칼라 ORM으로 승격 전 |
| `game_data.clrtyperegistryentry` | simulation CLR 행과 연결 | 중간 신뢰; `simulationsystem` 감사와 짝 |
| `game_data.simulationsystem` | `Miner` / `Extractor` / `Pump` entry id 필터 | 처리량·rate 경로 — `docs/domain/game_data_json_deep/simulation_systems*` 확장 |
| 섬·toolbar JSON 경로 | `ShapeMinerExtractorsGroup`, `FluidMinerChainsGroup`, placer stable_keys | UI 배치 그룹 |

**처리량:** 이 dump의 `buildingvariant`에 `throughput_rate` 단일 컬럼은 없다. 절대 처리량은 [`shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md) (CANON) + `gene_template.VALID_THROUGHPUT_FACTORS` (층 C)가 정본이며, 층 B 경로가 import에 샘플링될 때까지 유지한다.

## 층 C / D 포인터 (여기서 중복 서술 안 함)

| topic | 코드 | 테스트 |
|-------|------|--------|
| 처리량 4/8/12/16 | `django_apps/asteroid_lab/optimization/gene_template.py` | `tests/unit/asteroid_lab/test_gene_template_loader.py::test_gene_template_throughput_factor_matches_extension_count` |
| 확장기 0..3 | `throughput_factor_for_extension_count()` | `tests/unit/asteroid_lab/test_sample_gene_exhaustive.py::test_exhaustive_generator_extension_count_0_to_3` |
| rim-only 앵커 | `candidate_dtos.ExtractorPlacementPolicy.RIM_ONLY` | `test_candidate_generator.py::test_candidate_generator_does_not_commit_placements` |

## `01` 갱신 메모 (PR-1)

| topic | normalized_db_evidence (채움) | reflected_db_evidence (채움) | 판정 메모 |
|-------|------------------------------|-----------------------------|-----------|
| 확장기 max 0..3 | toolbar 그룹 + internal variant 2종; blueprint `Layout_*`는 별도 | `*PlacementHelper`, `*ExtensionMetadata` type_name | keep; `04`에서 Layout vs DB 설명 |
| 처리량 4/8/12/16 | 전용 rate 테이블 없음 | `unknownproperty` 샘플 + 향후 `simulation_systems` 감사 | rate와 B 경로 연결 전까지 `needs-review` |
