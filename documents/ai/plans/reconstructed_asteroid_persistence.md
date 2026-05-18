# Reconstructed asteroid DB persistence

**상태**: ACTIVE (v2 — layered JSON + entries)  
**관련 코드**: [`reconstruction_blueprint_export.py`](../../django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py), [`reconstructed_map_persist_builder.py`](../../django_apps/asteroid_lab/services/reconstructed_map_persist_builder.py), [`reconstructed_asteroid_service.py`](../../django_apps/asteroid_lab/services/reconstructed_asteroid_service.py), [`models.py`](../../django_apps/asteroid_lab/models.py)

## 레이어

| 저장소 | 역할 |
|--------|------|
| `AsteroidMapInput` | paste 직후 `copy_code` + `decoded_json` (server 좌표·summary) |
| `ReconstructedAsteroidMap` | reconstruction 완료 후 lab/export/reconstruction JSON + 앵커 |
| `ReconstructedAsteroidEntry` | 행 단위 `kind`/`source` + `payload` (원본 `T` 보존) |

## JSON 분리

| 필드 | 허용 | 금지 |
|------|------|------|
| `decoded_json` | `server_*`, `_asteroid_lab_*` | — |
| `reconstruction_json` | 셀 메타·evidence | solver 입력 |
| `export_json` | 게임 `BP.Entries` | `server_*`, `_asteroid_lab_*` |

`rebuilt_copy_code` = `encode_official_copy_string(to_game_paste_island_root(…))` + `$` (게임 붙여넣기용; 원본 문자열 복사 금지). `recon.cells`가 비면 `source_decoded_json`에서 import fallback. `copy_code` 컬럼은 dual-write.

## 앵커

1. `cleanup.removed_building_cells` 중 miner / miner_extension  
2. fallback: 원본 `BP.Entries`의 `Layout_*Miner`  
3. last: dense min + `summary_json.anchor_fallback`

belt/pipe는 앵커·asteroid evidence 아님.

## Entry unique

`(map, server_x, server_y, kind, source)` — 좌표 단독 unique 금지.

## 저장 경계

`persist_reconstructed_asteroid_map(recon, cleanup=…)` — reconstruction 결과만. replay frame 읽기 금지.

## 덮어쓰기 · `updated_at`

- `AsteroidMapInput.updated_at`, `ReconstructedAsteroidMap.updated_at` — 재저장 시 자동 갱신.
- `upsert_map_input_for_project` / `refresh_map_input_from_copy_code` — 동일 digest 입력 행 overwrite.
- `build_initial_replay_for_map_input(..., overwrite=True)` — 동일 `run_key`로 replay·복원 맵 in-place 교체 (`force`는 새 run_key).
- `refresh_reconstructed_map_for_map_input` — reconstruction만 다시 돌려 동일 `(map_input, run_key)` 행 update.

## 검증

- `test_create_copy_code_map_input_populates_decoded_json.py`
- `test_reconstructed_map_export_layers.py`
- `test_reconstructed_anchor_selection.py`
- `test_persistence_does_not_read_replay_frames.py`
- `test_reconstructed_asteroid_persist.py`
