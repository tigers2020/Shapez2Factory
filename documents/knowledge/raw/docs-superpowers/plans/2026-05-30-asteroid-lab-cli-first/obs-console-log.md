# Cross-cutting - CLI / run-solver console observability (BA-9)

**Type:** observability contract (output-only; not solver input)
**Normative spec:** [`../../specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`](../../specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md) section 11
**Lands in:** PR-CLI-3a (amend), PR-CLI-3b, PR-CLI-4, management CLI amend

---

## Goal

Developers see **one access-log-style line per CLI invocation** (start + end) on **stderr**, in the same
terminal as `runserver`, without replacing existing file JSONL observability (`var/log/...`).

Surfaces in scope:

| Surface | When |
|---------|------|
| Pure CLI | `python -m shapez2_factory.interfaces.cli.asteroid_solve ...` |
| Django management CLI | `python manage.py run_solver --slug <slug>` |
| HTTP `POST ...run-solver/` | `subprocess_only`; `runserver` terminal plus subprocess tee/log |
| Django `subprocess` mode | PR-CLI-4: child stderr **teed** to parent TTY **and** `logs/subprocess.log` |

**Out of scope:** replacing command stdout summaries or `--json` payloads with console logs.

---

## Frozen behavior

### Default (always when console logging enabled)

- **One line at start**, **one line at end** per invocation.
- Fields (omit nulls): `surface`, `command`, `slug`, `run_key`, `exit` / `error_code`,
  `elapsed_ms`, `solver_run_id`, `ok`.
- Format (Django dev-server friendly):

```text
[30/May/2026 15:29:29] asteroid_cli run start surface=http_run_solver slug=rttp-core-recovery-test-map
[30/May/2026 15:29:41] asteroid_cli run end surface=http_run_solver slug=rttp-core-recovery-test-map exit=0 elapsed_ms=12045 solver_run_id=379 ok=true
```

- Written to **`sys.stderr`** only (never mixed into artifact payloads or JSON API bodies).
- **Not algorithm input** - same class as `lab_perf_trace` / layer-stack JSONL.

### Verbose (opt-in only)

- Extra lines per completed solver layer (`layer_done`, `layer_slug`, `elapsed_ms`).
- Enabled when **any** of:
  - CLI `--verbose`
  - `ASTEROID_LAB_CLI_VERBOSE=1`
  - Django `DEBUG=True`
  - HTTP JSON body `cli_verbose: true` (optional; no UI requirement)

### Subprocess tee (PR-CLI-4, amends BA-7)

- Replace `capture_output=True`-only with **`Popen` + stream tee**:
  - Append every child stdout/stderr chunk to `<artifact>/logs/subprocess.log`
  - Mirror the same bytes to **parent** `sys.stderr` when parent stderr is a TTY
- Child CLI MUST emit BA-9 lines on its own stderr so tee reproduces them under `runserver`.
- Disable parent tee only via `ASTEROID_LAB_CLI_SUBPROCESS_TEE=0` (artifact log remains canonical).

---

## BA-1 placement

| Module | Package | Rule |
|--------|---------|------|
| `cli_console.py` | `src/shapez2_factory/adapters/asteroid_lab/` | stdlib only; `emit_cli_line(event, **fields)` |
| `cli_invoke_trace.py` | `django_apps/asteroid_lab/observability/` | wraps HTTP in-process path; imports core `cli_console` |
| `subprocess_stream_tee.py` | `django_apps/asteroid_lab/services/` | Django-only; BA-7 runner uses it |

Core MUST NOT import Django. Django MAY import core formatter.

---

## Settings / env

| Name | Default | Meaning |
|------|---------|---------|
| `ASTEROID_LAB_CLI_CONSOLE_LOG` | on (`1`) unless `0`/`false`/`no` | Master switch for stderr one-liners |
| `ASTEROID_LAB_CLI_VERBOSE` | off | Force verbose layer lines |
| `ASTEROID_LAB_CLI_SUBPROCESS_TEE` | on when stderr is TTY | Parent mirrors child streams (PR-CLI-4) |

Documented in [`config/settings.py`](../../../../config/settings.py): `ASTEROID_LAB_CLI_CONSOLE_LOG`,
`ASTEROID_LAB_CLI_VERBOSE`, `ASTEROID_LAB_CLI_SUBPROCESS_TEE` (pure CLI reads env directly for console/verbose).

---

## PR landing map

| PR | Deliverable |
|----|-------------|
| **PR-CLI-3a (amend)** | `cli_console.py`; `validate-artifact` + `run` stub start/end lines; `test_cli_console.py`; extend `test_validate_artifact.py` (`capsys`) |
| **PR-CLI-3b** | `--verbose` on `run`; `layer_done` lines from in-core stack; do not duplicate `var/log/asteroid_lab_layer_stack` JSONL |
| **HTTP in-process amend** | `cli_invoke_trace` on `_run_solver_post_traced`; start/end lines land before PR-CLI-4 subprocess mode |
| **PR-CLI-4** | core CLI verbose hooks; `subprocess_stream_tee` + runner wiring; amend BA-7 snippet in [`pr-cli-4-django-subprocess-ingest.md`](pr-cli-4-django-subprocess-ingest.md) |
| **Management CLI amend** | `run_solver` emits start/end stderr one-liners via the same pure `cli_console` formatter; stdout summaries and `--json` output stay unchanged |

---

## Tests (by landing PR)

```text
test_cli_console.py                       formatter + env gates (3a amend)
test_validate_artifact.py                 capsys: start/end stderr lines (3a amend)
test_run_solver_management_command.py     management command start/end stderr lines
test_asteroid_run_solver_cli_trace.py     HTTP subprocess-only run-solver start/end stderr lines
test_cli_invoke_trace.py                  HTTP wrap emits start/end (4)
test_subprocess_stream_tee.py             bytes in log file AND captured parent stderr (4)
```

---

## Non-goals

- Replacing `ASTEROID_LAB_PERF_TRACE` JSONL or `asteroid_lab_layer_stack` file logs
- Logging secrets from POST bodies or snapshot file contents
- Replacing management command stdout / JSON output with access-log lines

## Risks

- **Production noise:** default console on; set `ASTEROID_LAB_CLI_CONSOLE_LOG=0` under WSGI.
- **Duplicate lines under subprocess:** parent `run end` + child layer lines - acceptable (different semantics).
- **Windows encoding:** tee preserves bytes; CLI text boundaries use UTF-8 at emit sites.

## Done criteria (cross-PR)

- [x] Spec section 11 + README BA-9 row published
- [x] Pure CLI: every `validate-artifact` / `run` prints start+end on stderr when enabled
- [x] Django management CLI: `run_solver` prints start+end on stderr when enabled
- [x] HTTP request path: `runserver` shows start+end around subprocess-only `run_solver_runtime_for_project`
- [x] Subprocess: child output visible in parent terminal and in `logs/subprocess.log` (Popen tee implemented in PR-CLI-4 runner; HTTP/management opt-in wiring and end-to-end fixture run are in)
- [x] Verbose layer lines only under `--verbose` / `DEBUG` / `cli_verbose` / env
