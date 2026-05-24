# Archive: completed plan & research pairs (`completed-implementation/`)

**1:1 execution plan and research pairs** formerly under `documents/plans/` and `documents/research/` that appear reflected in the codebase, reorganized into **stem folders by topic**. Active, backlog, and design-only documents remain in parent [`../../plans/`](../plans/) and [`../../research/`](../research/).

## Layout rules

| Item | Description |
|------|------|
| Path | `by-stem/<stem>/plan_<stem>.md`, with `research_<stem>.md` in the same folder when present |
| Stem | Identifier from filename minus `plan_` prefix and `.md` suffix (e.g. `planner_service_split_2026-05-01`) |
| Relative links | On move, repo-root paths adjusted to `../../../../../django_apps/...` (three levels deeper vs `documents/plans/`) |
| Exceptions left active | Multi-phase roadmaps, standalone horizontal layout plans, future DTO design, etc.: `factory_throughput`, `solver_graph_horizontal_layout_2026-05-01`, `solve_progress_rendering_2026-05-01` |

## Relationship to session archives

- [`../2026-05-completed/README.md`](../2026-05-completed/README.md): copies bundled for **specific dated sessions** (Recipe Graph Editor, Python cleanup, etc.).
- This directory: archive reorganized by **filename stem** for plan/research pairs. Older plans such as `dead_code_cleanup_2026-05-01` may overlap topic-wise with the `2026-05-04` canonical in session archive; prefer code and latest plans as execution authority.

## Reproducing / additional moves

Initial bulk move was done from repo root via `python scripts/archive_completed_plans.py`. Adjust `EXCLUDE_STEMS` in the script and rerun (fails if files already moved; check Git state before rerun).

## Parent index

- [`../../README.md`](../../README.md) — full `documents/` map
- [`../README.md`](../README.md) — `archive/` subdirectory summary

## 2026-05-12 check

- `by-stem/` currently holds 26 stem folders archived as implementation-complete.
- Asteroid mining layout plans, research, and algorithm specs after 2026-05-09 remain active documents. Move here only after completion is judged.
