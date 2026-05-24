# Reconstructed asteroid DB persistence

**Status**: ACTIVE (full_map only — 4 fields)  
**Related code**: [`reconstruction/display_map.py`](../../django_apps/asteroid_lab/reconstruction/display_map.py), [`reconstructed_map_persist_builder.py`](../../django_apps/asteroid_lab/services/reconstructed_map_persist_builder.py), [`reconstructed_asteroid_service.py`](../../django_apps/asteroid_lab/services/reconstructed_asteroid_service.py), [`models.py`](../../django_apps/asteroid_lab/models.py)

## Persistence contract

Each `ReconstructedAsteroidMap` row keeps **one original pair + one full_map pair** only.

| | Copy string | JSON |
|---|-------------|------|
| Original | `original_copy_code` | `original_decoded_json` (`AsteroidMapInput` snapshot at persist time) |
| Reconstructed full_map | `copy_code` (`SHAPEZ2-4-…$`, lab encode) | `decoded_json` (same merge topology as replay `reconstruction_complete`) |

## full_map canon

- **merged cells**: `merge_reconstruction_display_cells(structural, recon.cells)` — same merge topology as replay `reconstruction_final` / synthetic `step4_10_asteroid_map_complete`.
- **BP.Entries / copy_code**: full merged (structural + recon overlay). `encode_reconstructed_copy_string` (lab).
- **meta (write)**: `_asteroid_lab_reconstruction.full_map_island_bbox` = merged island-local extent (`island_bbox_from_cells` on merged cells). New exports do not use `full_map_server_bbox`.
- **meta (read)**: `full_map_island_bbox_from_decoded_json` (`snapshots/island_bbox.py`) — (1) meta `full_map_island_bbox` first, (2) ignore legacy `full_map_server_bbox`, (3) if no meta, `BP.Entries` X/Y extent fallback.
- **Island stamp**: `stamp_islands_uniform` does not paint `unknown` walls (field/topology_fill only).
- **Forbidden**: shrink Entries via replay `visible_cells`, `to_game_paste_island_root`, `encode_official_copy_string`, `cells_for_field_export`.
- `ReconstructedAsteroidEntry`, `export_json`, `rebuilt_copy_code`, `summary_json`, `reconstruction_json` — **unused · removed**.

## Persistence boundary

`persist_reconstructed_asteroid_map(recon, cleanup=…)` — reconstruction + cleanup DTO only. No replay ORM reads. Immediate ORM persist without env flags.

## Verification

Narrow gate (replay · topology · island_bbox read-compat, no RTTP):

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
```

Included modules:

- `test_reconstruction_replay_merge.py` — `reconstruction_final` merge, `step4_10` parity
- `test_persistence_does_not_read_replay_frames.py`
- `test_reconstructed_asteroid_persist.py`
- `test_reconstruction_persist_full_map_bbox.py`
- `test_island_bbox.py` — meta / legacy server ignore / BP fallback
- `test_reconstruction_fixture_contract.py`, `test_replay_snapshot_contract.py`
