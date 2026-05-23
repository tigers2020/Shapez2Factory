---
status: CANON
owner: asteroid-lab
last_reviewed: 2026-05-23
language: ko
related_docs:
  - asteroid_lab_mining_installation/04_installation_guide.md
  - asteroid_lab_mining_installation/03_db_cross_reference.md
---

# 섬 추출기 기본 블루프린트 (Balance / Omni / Fluid)

Shapez 2 **섬(Island) 블루프린트**로 붙여넣는 추출기는 종류별로 내부 `B.Entries` 구성이 다르다. Lab·테스트·Admin에서 동일 문자열을 쓰려면 아래 **코드 카탈로그**와 **DB 시드**를 정본으로 삼는다.

## 인게임 변형 (요약)

| 변형 | `variant_key` | 최상위 `T` | 역할 |
|------|---------------|------------|------|
| 벨런스 추출기 | `shape_balance` | `Layout_ShapeMiner` | 12개 라인에 도형을 균등 분배 |
| 옴니 추출기 | `shape_omni` | `Layout_ShapeMiner` | 조각 도형을 본 형태로 복원·출력 |
| 유체 추출기 | `fluid_default` | `Layout_FluidMiner` | 펌프 기반 유체 추출 (단일 버전) |

도형 추출기는 **겉의 `Layout_*` 타입이 같아도** nested building이 다르다. Lab `cell_classifier`는 최상위 `Layout_ShapeMiner`만 보므로, balance/omni 구분은 **내부 지문** 또는 게임 메타데이터로 한다.

## 코드 정본

| 경로 | 내용 |
|------|------|
| `django_apps/asteroid_lab/catalog/island_extractor_defaults.py` | `ISLAND_EXTRACTOR_DEFAULTS`, `SHAPEZ2-4-` copy 문자열, `inner_entry_fingerprint()` |
| `django_apps/asteroid_lab/catalog/__init__.py` | 공개 re-export |

애플리케이션 코드는 DB 없이도 `ISLAND_EXTRACTOR_DEFAULTS` / `default_record()`로 copy 문자열을 읽을 수 있다.

## DB 정본

| 모델 | 용도 |
|------|------|
| `asteroid_lab.IslandExtractorBlueprint` | Admin·browse·시드된 copy_code + `inner_fingerprint` |

시드 (idempotent):

```powershell
python manage.py seed_island_extractor_blueprints
```

`--dry-run`으로 upsert 대상만 확인한다.

## 회귀 지문

`inner_entry_fingerprint(copy_code)` = nested `B.Entries`의 `T` 빈도를 JSON 정렬 후 SHA-256.

테스트: `tests/unit/asteroid_lab/test_island_extractor_blueprint_defaults.py`

- balance vs omni 지문 불일치
- balance의 `BeltPortSenderInternalVariant` 수 > omni
- fluid의 `PumpDefaultInternalVariant` == 16

## Blueprint vs Asteroid Lab miner

| 계층 | 식별 |
|------|------|
| 섬 붙여넣기 (이 문서) | `Layout_ShapeMiner` / `Layout_FluidMiner` + nested factory |
| 소행성 맵 최적화 | `GeneTemplate`, `Layout_*MinerExtension` 필드 타일 — [`04_installation_guide.md`](04_installation_guide.md) |

[`03_db_cross_reference.md`](03_db_cross_reference.md) § Blueprint `Layout_*` vs DB 참고.
