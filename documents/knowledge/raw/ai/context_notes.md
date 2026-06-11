# Context notes

## Asteroid Lab: replay cell detail lookup (2026-05-18)

- `replay_frame_cell_lookup`: merge all `full_map` at same coords; on miss fallback to `cell_overlay_json`; synthesize `lab_empty` for empty cells inside `bbox` (`_lab_synthetic`). Not solver input.

## Asteroid Lab: equipment bundle outline (2026-05-16)

- Extractor · extension 4-way BFS in `build_equipment_bundles` at `django_apps/asteroid_lab/snapshots/equipment_bundles.py`; replay `cell_overlay_json.equipment_bundles` + Lab JS border pass after `full_map` render. Not solver input.

## STEP4 `no_route_exhausted` sample (2026-05-12)

- Representative samples · per-question summary Markdown from NDJSON by `routing_failures` criterion are **not kept in repo**. If needed, find `documents/debug/step4_no_route_exhausted_sample_report_2026-05-12.md` in **git history**.
- Extraction script (non-production): `scripts/debug/extract_step4_no_route_exhausted_samples.py`
