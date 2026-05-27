# Environment Variable Policy

Collects **classification · names · defaults** for environment variables used locally · in deployment. Not an implementation contract (CANON).

## File layering

| File | Git | Role |
|------|-----|------|
| `.env.example` | tracked | **Minimal runtime** template for secrets · DB mode · OAuth, etc. |
| `.env.debug.example` | tracked | **Optional** template for observability · debug · preview noop, etc. |
| `.env` | ignored | Developer local (copy) |
| `.env.debug` | ignored | Overlays on `.env` (`override=True` in `config/settings.py`) |

Load order: `.env` → `.env.debug` (when present).

## Classification

| Class | Description | Examples |
|--------|------|-----|
| **runtime** | Infrastructure · data paths needed locally/deployment | `DATABASE_URL`, `DJANGO_USE_SQLITE`, `SHAPEZ_BASEDATA_ROOT` |
| **feature** | Product behavior toggles (code has readers) | `ASTEROID_LAB_REPLAY_PAYLOAD_MODE` |
| **infra** | Graph PNG preview · cache, etc. | `SOLVER_GRAPH_PREVIEW_*` |
| **debug** | Do not put in default `.env` | `ASTEROID_LAB_BOUNDARY_JSONL`, `SHAPEZ_COPY_DEBUG_DIR` |
| **unused** | Names left only in `.env` — **not referenced in code, delete** | `SHAPEZ_MINING_*`, `ASTEROID_LAB_REPLAY_JSON_DELIVERY`, etc. |

## Boolean notation

- **Docs · example files**: use only `0` / `1`.
- **Parsers**: some modules allow `true`, `yes`, `on` for backward compatibility (`DJANGO_USE_SQLITE`, `ASTEROID_LAB_BOUNDARY_JSONL`, etc.). Prefer `0`/`1` for new keys.

## Reader locations

| Key | Default | Reading module |
|----|--------|-----------|
| `DJANGO_USE_SQLITE` | off | `config/settings.py` |
| `DATABASE_URL` | sqlite `db.sqlite3` | `config/settings.py` + dj_database_url |
| `SHAPEZ_BASEDATA_ROOT` | `documents/shapez_2_data/basedata-v1137` | `config/settings.py` |
| `SOLVER_GRAPH_PREVIEW_RENDERER` | `playwright_png` | `config/shapez_runtime_flags.py` |
| `SOLVER_GRAPH_PREVIEW_STORAGE` | `filesystem` | `config/shapez_runtime_flags.py` |
| `SOLVER_GRAPH_PREVIEW_CACHE_DIR` | `<BASE_DIR>/.graph_preview_cache` | `config/shapez_runtime_flags.py` |
| `ASTEROID_LAB_RUNTIME_GENE_TEMPLATES_PATH` | `tests/fixtures/asteroid_lab/gene_templates` | `config/settings.py` |
| `ASTEROID_LAB_MINERS_PER_ROUTE_OUT` | `12` | `config/settings.py` (shape belt goals per-route bundle budget) |
| `ASTEROID_LAB_REPLAY_PAYLOAD_MODE` | `lazy` | `config/settings.py` — `inline` keeps full POST `lab_replay_frames_json`; `lazy` omits inline array (Sequence 13C) |
| `ASTEROID_LAB_BOUNDARY_JSONL` | off | `django_apps/asteroid_lab/observability/boundary_jsonl.py` |
| `ASTEROID_LAB_BOUNDARY_JSONL_DIR` | `var/asteroid_boundary_logs` | same |
| `ASTEROID_LAB_SOLVER_SUMMARY_STACK_LOG` | on (`1`) | `django_apps/asteroid_lab/observability/solver_summary_stack_log.py` |
| `ASTEROID_LAB_SOLVER_SUMMARY_STACK_LOG_DIR` | `var/log/solver_summary_stack` | same |
| `ASTEROID_LAB_SOLVER_SUMMARY_STACK_MAX` | `5` | same (max stack entries per file, 1–20) |
| `SHAPEZ_COPY_DEBUG_DIR` | off (empty string) | `config/shapez_runtime_flags.py` (no consumer code — reserved dump path) |

OAuth · Support URL, etc.: see `config/settings.py`.

## Forbidden · caution

1. **Phantom flag**: do not put names in `.env` / `.env.example` that have no `os.environ.get` in code.
2. **Pre-implementation env**: before approval · implementation (e.g. Sequence 13C lazy replay), do not pre-add names like `ASTEROID_LAB_REPLAY_*`. On implementation, register the canonical name in this doc and `settings` in one place.
3. **Alias duplication**: do not enable the same feature with two names (`ENABLE_*` / `LAB_*`). If there is no reader, mark “no env” in docs too.
4. **Solver pass flags**: `SHAPEZ_MINING_PASS*` etc. have no readers in the current codebase. Remove legacy `.env` entries.
5. **Secrets**: `.env` only. Do not put credentials in Markdown · commits.

## Unimplemented features and docs

- **11B optimization overlay**: no env flag. On implementation, separate design · update this doc.
- **13C lazy Lab replay**: `ASTEROID_LAB_REPLAY_PAYLOAD_MODE` registered (default `lazy`). See [`asteroid_lab_13_replay_payload_scalability.md`](../../Algorithm/asteroid_lab_13_replay_payload_scalability.md).

## Related manuals

- Django run: [`django.md`](django.md)
- Cloud VM · preview noop: [`cursor_usage.md`](cursor_usage.md)
- Test gates: [`testing.md`](testing.md)
