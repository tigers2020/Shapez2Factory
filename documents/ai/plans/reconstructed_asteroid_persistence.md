# Reconstructed asteroid DB persistence

**상태**: ACTIVE (구현 반영)  
**관련 코드**: [`django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py`](../../django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py), [`django_apps/asteroid_lab/services/reconstructed_asteroid_service.py`](../../django_apps/asteroid_lab/services/reconstructed_asteroid_service.py), [`django_apps/asteroid_lab/models.py`](../../django_apps/asteroid_lab/models.py) `ReconstructedAsteroidMap`

## 목적

topology reconstruction **완성 소행성**을 ORM에 저장한다. 게임 identifier에 asteroid 전용 `T`가 없으므로 `Layout_*MinerExtension`으로 encode하고, load 시 `asteroid_*_field`로 역매핑한다.

## 양방향 식별자

| 방향 | 랩 `cell_kind` | `BP.Entries[*].T` |
|------|----------------|-------------------|
| 저장 | `asteroid_shape_field` | `Layout_ShapeMinerExtension` |
| 저장 | `asteroid_fluid_field` | `Layout_FluidMinerExtension` |
| 불러오기 | `asteroid_shape_field` | `Layout_ShapeMinerExtension` |
| 불러오기 | `asteroid_fluid_field` | `Layout_FluidMinerExtension` |

문서/UI: AsteroidShapeField / AsteroidFluidField. 코드: `asteroid_shape_field` / `asteroid_fluid_field`.

**일반 `classify_blueprint_entry`로 reconstructed island를 로드하지 않는다** — 전용 `load_reconstruction_cells_from_*` 만 사용.

## encrypt · json

- `copy_code`: `SHAPEZ2-4-{base64(gzip(JSON))}$` (`$` 포함 저장, decode 시 strip/removesuffix)
- `decoded_json`: 동일 root + `_asteroid_lab_reconstruction` 메타 + `server_*` (attach 후)

내부 JSON 예: `V: 1137`, `BP.$type: Island`, `BP.Icon` Platforms + RuRuRuRu.

## 이력

`ReconstructedAsteroidMap`: `(map_input, run_key)` unique — inspection 파이프라인과 동일 `run_key`; `force=True` 시 suffix로 새 행.

## 검증

- `tests/unit/asteroid_lab/test_reconstruction_blueprint_export.py` — encode/import roundtrip
- `tests/unit/asteroid_lab/test_reconstructed_asteroid_persist.py` — pipeline persist

## 금지

- reconstruction topology 알고리즘 변경
- solver가 ORM 행을 알고리즘 입력으로 읽기
- `encode_official_copy_string` (miner-anchor dense export)
