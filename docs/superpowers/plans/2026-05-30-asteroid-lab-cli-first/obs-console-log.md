# Cross-cutting — CLI / run-solver console observability (BA-9)

**Type:** observability contract (output-only; not solver input)
**Normative spec:** [`../../specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`](../../specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md) §11
**Lands in:** PR-CLI-3a (amend) · PR-CLI-3b · PR-CLI-4

---

## Goal

Developers see **one access-log-style line per CLI invocation** (start + end) on **stderr**, in the same
terminal as `runserver`, without replacing existing file JSONL observability (`var/log/…`).

Surfaces in scope:

| Surface | When |
|---------|------|
| Pure CLI | `python -m shapez2_factory.interfaces.cli.asteroid_solve …` |
| HTTP `POST …/run-solver/` | `in_process` today; `runserver` terminal |
| Django `subprocess` mode | PR-CLI-4: child stderr **teed** to parent TTY **and** `logs/subprocess.log` |

**Out of scope:** `python manage.py run_solver` parity (not required for BA-9).

---

## Frozen behavior

### Default (always when console logging enabled)

- **One line at start**, **one line at end** per invocation.
- Fields (omit nulls): `surface`, `command`, `slug` (HTTP only), `run_key`, `exit` / `error_code`,
  `elapsed_ms`, `solver_run_id`, `ok`.
- Format (Django dev-server friendly):

```text
[30/May/2026 15:29:29] asteroid_cli run start surface=http_run_solver slug=rttp-core-recovery-test-map
[30/May/2026 15:29:41] asteroid_cli run end surface=http_run_solver slug=rttp-core-recovery-test-map exit=0 elapsed_ms=12045 solver_run_id=379 ok=true
```

- Written to **`sys.stderr`** only (never mixed into artifact payloads or JSON API bodies).
- **Not algorithm input** — same class as `lab_perf_trace` / layer-stack JSONL.

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

Document in [`config/settings.py`](../../../../config/settings.py) when implemented (PR-CLI-4).

---

## PR landing map

| PR | Deliverable |
|----|-------------|
| **PR-CLI-3a (amend)** | `cli_console.py`; `validate-artifact` + `run` stub start/end lines; `test_cli_console.py`; extend `test_validate_artifact.py` (`capsys`) |
| **PR-CLI-3b** | `--verbose` on `run`; `layer_done` lines from in-core stack; do not duplicate `var/log/asteroid_lab_layer_stack` JSONL |
| **PR-CLI-4** | `cli_invoke_trace` on `_run_solver_post_traced`; verbose hooks in `solver_runtime_layer02`; `subprocess_stream_tee` + runner wiring; amend BA-7 snippet in [`pr-cli-4-django-subprocess-ingest.md`](pr-cli-4-django-subprocess-ingest.md) |

---

## Tests (by landing PR)

```text
test_cli_console.py              — formatter + env gates (3a amend)
test_validate_artifact.py        — capsys: start/end stderr lines (3a amend)
test_cli_invoke_trace.py         — HTTP wrap emits start/end (4)
test_subprocess_stream_tee.py    — bytes in log file AND captured parent stderr (4)
```

---

## Non-goals

- Replacing `ASTEROID_LAB_PERF_TRACE` JSONL or `asteroid_lab_layer_stack` file logs
- Logging secrets from POST bodies or snapshot file contents
- `manage.py run_solver` console parity

## Risks

- **Production noise:** default console on; set `ASTEROID_LAB_CLI_CONSOLE_LOG=0` under WSGI.
- **Duplicate lines under subprocess:** parent `run end` + child layer lines — acceptable (different semantics).
- **Windows encoding:** tee preserves bytes; CLI text boundaries use UTF-8 at emit sites.

## Done criteria (cross-PR)

- [ ] Spec §11 + README BA-9 row published
- [ ] Pure CLI: every `validate-artifact` / `run` prints start+end on stderr when enabled
- [ ] HTTP in-process: `runserver` shows start+end around `run_solver_runtime_for_project`
- [ ] Subprocess: child output visible in parent terminal and in `logs/subprocess.log`
- [ ] Verbose layer lines only under `--verbose` / `DEBUG` / `cli_verbose` / env
