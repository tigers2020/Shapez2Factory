# PR-CLI-3b — Full Pure CLI `run` (decode → stack → artifacts)

**Type:** implementation change
**Depends on:** PR-CLI-2e (L3–L6 + stack_runner in core) **AND** PR-CLI-3a
**Enables:** PR-CLI-4
**Branch (suggested):** `feat/asteroid-cli-first-full-run`

---

## Goal

Complete the pure CLI: `run` now executes decode → cleanup → reconstruction → in-core `stack_runner`
end-to-end with **no Django required**, writing the full atomic artifact directory including
`replay_core.jsonl`. This is only valid after PR-CLI-2e, when stack_runner + L3–L6 live in core.

> **Structural amendment (2026-05-30):** "Full pure CLI run" was separated from the artifact shell and
> re-pointed to depend on **PR-CLI-2e** (not 2d), so the "No Django required" claim is actually true.

## Behavior contract

- `run` performs the full stack in-core; no `django_apps` import path is reachable.
- Emits `manifest.json`, `input/*`, `output/stack_result.json`, `output/layer01_complete_map.json`,
  `output/replay_core.jsonl`, `output/solver_summary.json` via atomic writer (BA-5).
- `replay_core.jsonl` deterministic, output-only, monotonic `frame_index` (BA-4 + guard B).
- Exit codes per CLI-0 / BA-7 mapping; snapshot fail-closed per BA-8.
- BA-9: `run` emits stderr start/end one-liners (from 3a amend `cli_console`); `--verbose` adds per-layer `layer_done` lines ([`obs-console-log.md`](obs-console-log.md)).

## Non-goals

- No Django integration (PR-CLI-4).
- No web-ready replay payload (viewer-only, never core).

---

## File map

| Action | Path | Why |
|--------|------|-----|
| Implement | `src/shapez2_factory/application/asteroid_lab/run_stack.py` | real `RunStackUseCase` (replaces 3a stub) |
| Create | `src/shapez2_factory/application/asteroid_lab/replay_core.py` | core JSONL replay emitter (deterministic) |
| Create | `src/shapez2_factory/adapters/asteroid_lab/copy_decode_adapter.py` | pure decode wrap |
| Modify | `src/shapez2_factory/interfaces/cli/asteroid_solve.py` | `run` now executes full stack; `--verbose` (BA-9) |
| Modify | in-core stack / `run_stack.py` | optional `layer_done` via `cli_console` when verbose |
| Create | `tests/unit/shapez2_factory/test_cli_run_artifact.py` | full round-trip |
| Create | `tests/unit/shapez2_factory/test_cli_exit_codes.py` | BA-7 mapping |
| Create | `tests/unit/shapez2_factory/test_replay_core_monotonic.py` | guard B |
| Create | `tests/unit/architecture/test_replay_core_no_django_replay.py` | guard E |
| Create | `tests/fixtures/asteroid_lab/copy_code_min.txt` | deterministic input |

---

## Guards (architect-required)

### Guard B — replay frame monotonicity + streaming

```text
test_replay_core_rejects_non_monotonic_frame_index
```

- `replay_core.jsonl`: header line first; frames strictly increasing `frame_index`.
- Emitter writes line-by-line (stream-friendly); never builds one giant in-memory JSON blob.

### Guard D — replay JSONL streaming-only policy (carried to viewer PRs)

```text
replay_core.jsonl is stream-read.
Django must NOT inline full replay JSON into SSR page.  (enforced in PR-CLI-5)
```

Stated here so the artifact is produced stream-friendly from day one.

### Guard E — `replay_core.py` no legacy replay import (architect-required, 2026-05-30)

`replay_core.py` reuses the **core portion** of the former
[`replay/solver_runtime_assembler.py`](../../../../django_apps/asteroid_lab/replay/solver_runtime_assembler.py).
The direction is correct, but an accidental import of the Django replay/services/web packages would break
BA-1. Add a dedicated AST gate (in addition to the global purity gate):

```text
test_replay_core_does_not_import_django_replay
```

Forbidden import prefixes from `src/shapez2_factory/application/asteroid_lab/replay_core.py` (and siblings):

```text
django_apps.asteroid_lab.replay
django_apps.asteroid_lab.services
django_apps.web
```

> Move only the pure event-construction helpers into core; leave timeline enrichment / wire shaping in Django.

---

## CLI surface (full)

```text
python -m shapez2_factory.interfaces.cli.asteroid_solve run \
  --copy-file <path> | --decoded-json <path> \
  --snapshot <game_data_snapshot.json> \
  [--expected-snapshot-hash sha256:...] \
  --artifact-root var/runs --run-key <key> \
  [--throughput-target-percent 80] [--budget-ms 60000] [--replace-existing] [--verbose]
```

## Tasks

- [ ] **Step 1 (TDD):** `test_cli_run_artifact.py` — run on fixture; final dir only after success; manifest hashes valid; all output files present; JSONL parses per line.
- [ ] **Step 2:** Implement `run_stack` use case (decode/cleanup/recon/in-core stack_runner + JSON snapshot adapter).
- [ ] **Step 3:** Implement `replay_core` emitter; pull core event construction from former
  [`replay/solver_runtime_assembler.py`](../../../../django_apps/asteroid_lab/replay/solver_runtime_assembler.py) core portion; leave Django enrichment behind.
- [ ] **Step 4 (TDD):** `test_replay_core_monotonic.py` (guard B) + `test_cli_exit_codes.py` (BA-7) + `test_replay_core_no_django_replay.py` (guard E).
- [ ] **Step 5 (BA-9):** `--verbose`; `layer_done` stderr lines from stack when verbose; assert no verbose lines without flag (`capsys`).
- [ ] **Step 6:** ruff + mypy + purity gate.

## Tests / verification

```powershell
python -m shapez2_factory.interfaces.cli.asteroid_solve run --copy-file tests/fixtures/asteroid_lab/copy_code_min.txt --snapshot tests/fixtures/asteroid_lab/game_data_snapshot_min.json --artifact-root var/runs --run-key local-test
python -m pytest tests/unit/shapez2_factory/test_cli_run_artifact.py tests/unit/shapez2_factory/test_cli_exit_codes.py tests/unit/shapez2_factory/test_replay_core_monotonic.py -v
python -m mypy src
```

## Risks

- `invariant:` replay frames output-only; never read back as algorithm input.
- `invariant:` single replay timeline; global monotonic `frame_index`.
- Determinism: sort dict iteration; no unseeded `random`/`uuid4` in core emit.
- Hard dependency on PR-CLI-2e — do not start until stack_runner is in core.

## Done criteria

- Full pure CLI produces valid atomic artifact dir incl. streaming JSONL replay; exit codes mapped; no Django reachable; tests green.
