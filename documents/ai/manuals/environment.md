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
| **infra** | Graph PNG preview · cache, HTTP gzip (no env — `GZipMiddleware` in `config/settings.py`) | `SOLVER_GRAPH_PREVIEW_*` |
| **debug** | Do not put in default `.env` | `ASTEROID_LAB_BOUNDARY_JSONL`, `ASTEROID_LAB_PERF_TRACE`, `SHAPEZ_COPY_DEBUG_DIR` |
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
| `ASTEROID_LAB_REPLAY_COMPOSE_CACHE_ENABLED` | `1` | `config/settings.py` + `lab_replay_persisted_cache.py` — `0` skips read/write of composed replay on `SolverRun` (always recompose from artifact; debug L3/replay) |
| `ASTEROID_LAB_BOUNDARY_JSONL` | off | `django_apps/asteroid_lab/observability/boundary_jsonl.py` |
| `ASTEROID_LAB_PERF_TRACE` | off | `django_apps/asteroid_lab/observability/lab_perf_trace.py` — JSONL under `var/log/asteroid_lab_perf/` |
| `ASTEROID_LAB_BOUNDARY_JSONL_DIR` | `var/asteroid_boundary_logs` | same |
| `ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_ENABLED` | on (`True` in `config/settings.py`) | `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` |
| `ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_DIR` | `var/log/asteroid_lab_layer_stack` | same |
| `ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_MAX_RUNS` | `5` | same (per-project run dir retention) |

**Layer-stack forensic canonical path** (when post-summary logging is enabled):

```text
var/log/asteroid_lab_layer_stack/projects/{project_slug}/runs/{run_id}/
  manifest.json
  stack_run.jsonl
  layer_01_reconstruction.jsonl … layer_06_commit_validate.jsonl
  layer_04_inner_pattern_fill.jsonl    # canonical L4 inner fill
  layer_05_transport_routing.jsonl     # canonical L5 transport (legacy runs may log deprecated slugs)
  layer_04_selected_placements.jsonl   # rim-bundle forensic (legacy L4 rim placement)
```

Separate optional paths (not merged into layer-stack):

- `var/asteroid_boundary_logs/` — boundary JSONL (`ASTEROID_LAB_BOUNDARY_JSONL`)
- `var/log/asteroid_lab.log` — ambient JSON Lines (`ASTEROID_LAB_FILE_LOG`) — web views + `asteroid_lab.services`
- `var/log/solver.log` — ambient JSON Lines (`ASTEROID_LAB_FILE_LOG`) — `django_apps.shapez_solver`
- `var/log/asteroid_lab_perf/lab_perf.jsonl` — HTTP latency JSONL (`ASTEROID_LAB_PERF_TRACE` only)

**Ambient file log schema** (`asteroid_lab.log`, `solver.log` — one JSON object per line; not layer-stack / perf trace):

| Key | Type | Description |
|-----|------|-------------|
| `ts` | string | ISO8601 UTC timestamp |
| `level` | string | `DEBUG`, `INFO`, `WARNING`, `ERROR`, … |
| `logger` | string | Python logger name |
| `message` | string | Event name or message text |
| `request_id` | string \| null | HTTP correlation ID (null outside request) |
| *(extra)* | any | Non-colliding `logger.*(..., extra={...})` keys promoted to top level |

Filter examples:

```bash
# jq (one request)
jq -c 'select(.request_id=="abcd1234")' var/log/asteroid_lab.log

# grep slug in structured extra
grep '"slug":"abc123"' var/log/solver.log
```

| `ASTEROID_LAB_FILE_LOG` | on (`1`) | `config/settings.py` — `0` disables all ambient file handlers |
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
- **13G gzip transport**: `django.middleware.gzip.GZipMiddleware` after WhiteNoise in `config/settings.py` (no env flag). Large JSON responses (e.g. `GET …/lab-replay/`) compress when `Accept-Encoding: gzip`.

## Related manuals

- Django run: [`django.md`](django.md)
- Cloud VM · preview noop: [`cursor_usage.md`](cursor_usage.md)
- Test gates: [`testing.md`](testing.md)
