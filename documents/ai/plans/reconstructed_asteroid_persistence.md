# Reconstructed asteroid DB persistence

**상태**: ACTIVE (full_map only — 4 fields)  
**관련 코드**: [`reconstruction/display_map.py`](../../django_apps/asteroid_lab/reconstruction/display_map.py), [`reconstructed_map_persist_builder.py`](../../django_apps/asteroid_lab/services/reconstructed_map_persist_builder.py), [`reconstructed_asteroid_service.py`](../../django_apps/asteroid_lab/services/reconstructed_asteroid_service.py), [`models.py`](../../django_apps/asteroid_lab/models.py)

## 저장 계약

`ReconstructedAsteroidMap` 행당 **원본 1쌍 + full_map 1쌍**만 유지한다.

| | Copy string | JSON |
|---|-------------|------|
| 원본 | `original_copy_code` | `original_decoded_json` (persist 시점 `AsteroidMapInput` 스냅샷) |
| 복원 full_map | `copy_code` (`SHAPEZ2-4-…$`, lab encode) | `decoded_json` (replay `reconstruction_complete`와 동일 병합 topology) |

## full_map 정본

- **merged cells**: `merge_reconstruction_display_cells(structural, recon.cells)` — replay `reconstruction_complete`와 동일.
- **BP.Entries / copy_code**: merged 전체 (structural + recon overlay). `encode_reconstructed_copy_string` (lab).
- **meta**: `_asteroid_lab_reconstruction.full_map_server_bbox` = merged server bbox.
- **섬 스탬프**: `stamp_islands_uniform`은 `unknown` 벽을 칠하지 않음 (field/topology_fill만).
- **금지**: replay `visible_cells`, `to_game_paste_island_root`, `encode_official_copy_string`, `cells_for_field_export`로 Entries 축소.
- `ReconstructedAsteroidEntry`, `export_json`, `rebuilt_copy_code`, `summary_json`, `reconstruction_json` — **미사용·삭제**.

## 저장 경계

`persist_reconstructed_asteroid_map(recon, cleanup=…)` — reconstruction + cleanup DTO만. replay ORM 읽기 금지. env 플래그 없이 즉시 ORM 저장.

## 검증

- `test_reconstruction_replay_merge.py`
- `test_persistence_does_not_read_replay_frames.py`
- `test_reconstructed_asteroid_persist.py`
- `test_reconstruction_persist_full_map_bbox.py`
