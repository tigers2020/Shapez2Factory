# Manual: Testing · Verification

**Canonical detail** for SDD, contracts, and gates. Routing and work classification summaries are in [`AGENTS.md`](../../../AGENTS.md) · [`.cursor/rules/workflow.mdc`](../../../.cursor/rules/workflow.mdc) (**Contract-first SDD**).

## pytest (default: changed scope only)

- **Default:** Run only tests directly tied to the code or modules you touched this session. Example: the matching module under `tests/unit/...` next to the changed file, or `pytest path/to/test_file.py` / `pytest tests/unit/some_package/`.
- **Full suite** (`python -m pytest`, everything from repo root): only when **strictly needed** — PR, merge, CI, broad regression ([Quality gate sequence](#quality-gate-sequence) PR full gate).
- Use markers and scopes per the **Scoped execution** table below.

```bash
# Example: single working directory
python -m pytest tests/unit/asteroid_lab/test_example.py

# Full (PR / merge / CI)
python -m pytest
```

### pytest output rules (required)

**Do not use pytest output-suppression flags when running pytest.** (Same as [`AGENTS.md`](../../../AGENTS.md))

| Forbidden flag | Reason |
|---|---|
| `-q` / `--quiet` | Hides failure detail; errors are easy to miss |
| `--tb=no` | Removes traceback; debugging is impossible |
| `--no-header` | Loses context when used alone |
| `-p no:terminal` | Suppresses all output |

Allowed: `-v`, `-s`, `--tb=short` (default), `--tb=long`, `-x`, `--maxfail=N`.

Local scripts (`scripts/test_fast.ps1`, etc.), CI, and agent narrow/full gates all follow the rules above.

---

## Development Mode: Contract-first SDD

**Default flow (SDD — not TDD):** Lock **CANON spec / contract + acceptance criteria** first → derive **focused tests** from acceptance → **minimal implementation** → pass gates. Do not default to “implement first → test later” or “test-first without spec.”

**This is not classic test-driven design (TDD).** Tests **verify** spec acceptance; they do not replace spec. **This is not aggressive line-coverage testing.** Test only **contracts that are expensive to rediscover after they break**.

At work start, classify per [`AGENTS.md`](../../../AGENTS.md) (one or more): `contract change` · `implementation change` · `refactoring` · `documentation change` · `regression fix`.

---

## When to write or update tests

When you change any of the following, map **acceptance criteria from spec**, then add or update **focused tests** before production (unless docs-only contract).

1. **Public behavior**: API response shape, function output contracts, CLI, user-visible UI behavior, persisted data shape, serialization/deserialization formats.
2. **Domain contracts**: DTO fields, **enum / StrEnum / constants**, state transitions, ownership/lifetime rules, validation, allowed/forbidden states.
3. **Data conversion**: coordinate conversion (`raw` ↔ Server X/Y), normalization, parsing, encoding/decoding, import/export boundaries, schema migration, DB mapping.
4. **Control-flow branches**: success/failure, accept/reject, commit/rollback, retry/skip/fallback, error classification, guards/gates/permissions.
5. **Persistence and external boundaries**: DB, file output, POST/GET payloads, background jobs, **replay payload**, **validation results**, artifact/log/metrics/NDJSON contracts.
6. **Bug fixes**: add a reproducing **regression test** before the fix (if impossible or unrealistic, state why in Caveman **Tests/Risks**).
7. **Recently fragile areas**: narrow corridor, route starvation, replay, coordinate boundary, UI replay sync, etc. — at least one test for the relevant **invariant**.

**Priority when external contracts change** (update tests and enums together):

- DTO · enum · serialization
- coordinate conversion · `route_domain` · candidate pool
- replay payload · validation `issue_code` / `failure_reason` / `event_type`

---

## When not to add new tests

The following usually **do not warrant new tests by default**; existing tests and validation commands may suffice.

- Format-only, comment-only, log-message-only, or pure visual tweaks (CSS color/spacing, etc.).
- Non-behavior renames of private symbols.
- Internal refactors or dead-code removal where **behavior contracts are unchanged** (existing tests are enough).
- Fixture cleanup with **no production behavior change**.

If **behavior contracts change**, test updates are mandatory.

---

## Required SDD workflow

1. After classifying the work, confirm **CANON spec / contract brief** and list **acceptance criteria**.
2. Add the **narrowest acceptance test(s)** that encode those criteria (new behavior may fail until implementation).
3. Make **only that test path** green with `pytest` via minimal production change.
4. Repeat before widening scope.
5. Do **not** start with one large integration test without spec slices. Integration/E2E only when the same invariant cannot be proven at unit level.

---

## Domain invariants that must be test-protected

### Asteroid Lab (solver / optimization)

Semantic canon: `documents/Algorithm/asteroid_lab_*.md` · [ADR-003](../../adr/ADR-003-final-validation-assertion-gate.md). For glob work, see [`.cursor/rules/asteroid-lab-invariants.mdc`](../../../.cursor/rules/asteroid-lab-invariants.mdc).

| Invariant | Canon | Representative tests / planned names |
|-----------|-------|----------------------------------------|
| Replay / NDJSON / artifact / metrics **output-only** — **forbidden as solver/algorithm input** | current replay code and tests | `test_lab_page_context_*` |
| Candidate: **no placement commit**; generate → local geometry → immediate route probe → reachable only in normal pool | [`asteroid_lab_03_candidate_generator.md`](../../Algorithm/asteroid_lab_03_candidate_generator.md) | generator-adjacent unit; Phase checklist |
| Incremental commit: **commit-time latest `route_domain` re-probe**; candidate-phase reachable ≠ final proof | [`asteroid_lab_07_incremental_commit.md`](../../Algorithm/asteroid_lab_07_incremental_commit.md) | `test_incremental_commit_reprobes_latest_route_domain` (documented) |
| Validation: **read-only assert**; **no** route/placement/topology **repair** | [`asteroid_lab_08_validation.md`](../../Algorithm/asteroid_lab_08_validation.md), ADR-003 | validation read-only checklist · pytest |
| Lab replay timeline; global monotonic `frame_index`; every frame **2D map_view**; single play/scrubber | current replay code and tests | `test_lab_js_replay_wiring_smoke`; `test_lab_page_context_*` |
| `failure_reason` · `event_type` · `issue_code` etc. are **enum/const** — no free-form strings | Phase DTO docs | `test_invalid_event_type_rejected`; replay contract tests |
| Same seed **deterministic** (+ tie-break) | evolution docs | explicit tests where needed |
| **Regression fixture** — add at bug recurrence | this manual | `tests/fixtures/asteroid_lab/`; corridor · starvation · replay · coord · UI sync first |
| Replay truncation schema | current replay code and tests | `test_lab_replay_timeline_payload.py`, `test_timeline_composer.py` |
| **Fitness vs commit survivability** — predictive penalties vs observed metrics; observed → solver input **forbidden** | [`asteroid_lab_05_genome_fitness.md`](../../Algorithm/asteroid_lab_05_genome_fitness.md) | `test_fitness_contracts.py` |

**Unimplemented** invariant tests listed in the table are in scope for a later **implementation PR**. This document only fixes requirements and what must be protected.

### shapez_solver · Graph

- Keep **demand summary · source quantity · target output · materialized nodes · visual labels · operation nodes** distinct ([`shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc) Solver/Graph).
- Operation output → operation **direct adjacency forbidden**; route through intermediate shape nodes.

---

## Test selection strategy

### Minimum set for meaningful changes

(1) happy path (2) one important failure path (3) one invariant or edge case. Avoid multiple tests proving the same contract.

### Layer choice

- Pure logic → **unit**
- Orchestration → **service/use case**
- Cross-boundary → **integration**
- **E2E** only when lower layers cannot prove the contract

Do not add slow integration tests when a unit test can prove the same invariant.

### Regression · fixtures

Per bug fix: **what went wrong**, **which invariant broke**, **which test prevents recurrence**. If contract coverage was empty, place the test near the **contract owner** (domain · serialization · boundary).

Add **regression fixtures** at recurrence time. Priority: narrow corridor, route starvation, replay payload, coordinate boundary, UI replay sync.

### Reuse existing tests

Before adding, search for tests that already verify the same contract. **Extend** if found; add a new case only when none exists. Avoid names tied to implementation details.

### Test names

Name by **behavior · invariant**.

- Good: `test_rejects_invalid_payload_without_crashing`, `test_commit_failure_does_not_mutate_confirmed_state`
- Bad: `test_helper_line_42`, `test_new_code_path`

---

## Quality gate sequence

### Iteration (local spec-gated)

**Default** during agent work and implementation. Spec/acceptance mapped → narrow `pytest` green → narrow lint if needed.

```bash
python -m pytest <narrow path>   # -q / --quiet / --tb=no forbidden
# after green
python -m ruff check <paths>   # or .
python -m mypy <paths>         # optional
python -m black <paths>        # local format fix allowed
```

### PR / merge / CI (full gate)

At close, merge, and CI, run **full** verification. Order:

```bash
python -m ruff check .
python -m black --check .
python -m mypy src
python -m pytest
```

- Local format fixes: `black .` allowed.
- Record `black --check .` results in PR and Caveman **Tests**.
- From Phase 2: extend `mypy src` → `mypy django_apps config src` (single AGENTS.md change).

[`shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc) · [`protocols/README.md`](../../../protocols/README.md) · harness skills align with this **dual-mode** sequence.

---

## Agent behavior rules

- Before starting, classify scope as **contract / implementation / refactor / documentation / regression** ([`AGENTS.md`](../../../AGENTS.md)).
- **Contract change** → spec amendment → acceptance tests and related docs first.
- **Regression fix** → spec slice or bug note → repro test first.
- **Implementation change** → spec-linked acceptance tests first.
- **UI change** → DOM · serialization · JS behavior or fixture regression first.
- **Documentation only** → pytest not required; if docs change **code contracts**, note test plan in Caveman **Contracts/Tests**.
- Close with Caveman 6 sections only ([`shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc)); **Contracts** states invariants and why tests were added/skipped; **Tests** lists commands and results.
- For same-seed deterministic areas, lock **tie-break** in tests too.

---

## Forbidden shortcuts

**Forbidden** for agents and PRs:

- Making green by **deleting or weakening tests only** — if deleted/weakened, document reason and **replacement invariant**.
- Reading replay · artifact · metrics · NDJSON as **solver / algorithm input**.
- Patching `route_domain` in multiple places — keep **`RouteDomainSnapshotBuilder` as sole owner**.
- **Repair** in validation (route creation, placement/topology mutation).
- Using candidate enumeration · rim scan order as **`Gene.commit_order` / commit order**.
- Using candidate-phase reachable as **final commit proof** (commit-time re-probe required).
- **Raw ↔ server coordinate re-conversion** in the algorithm layer after `OptimizationInput`.
- Adding **free-form strings** for `failure_reason` · `event_type` · `issue_code` — update **enum/const + tests** together.
- **Implicit sync** between Lab replay frame index and Optimization replay frame index.
- Starting SDD with “one big test” and no spec/acceptance mapping.
- **TDD-only:** test-first design without CANON spec or acceptance criteria.
- **Output suppression** in pytest (`-q`, `--quiet`, `--tb=no`, `-p no:terminal`) — misses failures/tracebacks.
- Renames that change **only a leading underscore** (`func`↔`_func`, `name`↔`_name`) — forbidden for style · lint · private/public cleanup unrelated to behavior/contracts. Exception: explicit user rename or approved contract change.

---

## PR / commit checklist

Use together with [`documents/ai/checklist.md`](../checklist.md).

- [ ] State work classification (contract · implementation · refactor · documentation · regression) in Caveman **Summary** or **Contracts**.
- [ ] Add/update tests for contract · invariant · regression changes (or state skip reason).
- [ ] Confirm no forbidden shortcuts apply.
- [ ] Iteration: narrow `pytest` green.
- [ ] PR/merge: [full gate](#pr--merge--ci-full-gate) or skip reason in **Tests/Risks**.
- [ ] For Asteroid Lab, follow [`asteroid-lab-invariants.mdc`](../../../.cursor/rules/asteroid-lab-invariants.mdc) table.

**Before close (implementation PR)** — if any of the following apply, confirm focused tests (state exception reason in **Tests**):

- Public behavior · serialization · branches/gates · external boundaries · bug fix · fragile path.

---

## Scoped execution

| Method | Example |
|------|-----|
| Marker | `-m unit`, `-m integration`, `-m shapez_solver`, `-m shapez_core`, `-m web`, `-m api`, `-m asteroid_lab` |
| Combination | `-m "unit and shapez_core"` |
| Path | `python -m pytest tests/unit/shapez_solver/` · `python -m pytest tests/unit/asteroid_lab/` |
| Single file · name filter | `python -m pytest tests/unit/shapez_solver/test_bar.py` · `python -m pytest -k "substring"` |
| Parallel full | `python -m pytest -n auto --dist loadscope` |
| Fast unit | `python -m pytest -m "unit and not slow" -n auto --dist loadscope` |
| slow only | `python -m pytest -m slow -n auto --dist loadscope` |

When only production modules changed, default to passing the **existing** test module or directory path that verifies that behavior.

PR · CI full gate `python -m pytest` may use `-n auto --dist loadscope` parallelism. Local iteration defaults to narrow path or `unit and not slow`.

Marker definitions: `pytest.ini`. Path-based auto-markers: `tests/conftest.py`.

**Auto `slow`:** tests using expensive fixtures such as `imported_game_data_batch` · `exhaustive_genes_*`, or heavy modules like `test_macro_recipe_staff_catalog.py`, get `slow` at collection (`tests/conftest.py`). Local iteration default: `-m "unit and not slow"` + `-n auto --dist loadscope`.

### Local scripts (recommended)

| Script | Purpose |
|----------|------|
| `powershell -File scripts/test_fast.ps1` | **Daily SDD iteration** — `unit and not slow`, parallel |
| `powershell -File scripts/test_slow.ps1` | Slow contracts · import · exhaustive |
| `powershell -File scripts/test_full.ps1` | Before PR — full pytest |

Agent iteration default: changed narrow path → `test_fast.ps1`. PR/CI: full gate (`test_full.ps1` or AGENTS.md order).

### game_data unit fixture (Tier B)

- Full ORM seed: `game_data_backup/game_data_dump.json` via `loaddata` (`tests/unit/game_data/fixtures.py`).
- Pinned `ImportBatch.manifest_self_hash` in `tests/unit/game_data/_dump_expectations.py` — update together when regenerating dump.
- Missing dump: `pytest.fail` when `CI` or `REQUIRE_GAME_DATA_DUMP=1`; otherwise `pytest.skip`.
- Tier A (`import_game_data` / `--verify` / dump regen): [game_data_tier_a_release_gate.md](../../../docs/runbooks/game_data_tier_a_release_gate.md) — **not** `test_fast`.
- Slice importer tests: `tests/fixtures/game_data/*.json` only (not `documents/game_data/`).

CI runs as **parallel jobs**: `test-fast`, `test-integration` (`.github/workflows/ci.yml`). `test-slow` (`scripts/test_slow.ps1`) is **local / pre-PR only** — excluded from CI matrix.

## Recipe Graph editor (Vitest)

Wire · input arity · carrier alignment verified against Python via shared fixtures.

```bash
npm --prefix frontend/recipe_graph_editor test
```

Fixtures: `tests/fixtures/recipe_connection_rule_scenarios.json` · Python: `tests/unit/shapez_solver/test_recipe_connection_rule_fixture_alignment.py`

## Lint · type · format

Local fixes:

```bash
ruff check .
mypy src
black .
```

PR · CI verification follows [Quality gate sequence](#quality-gate-sequence) PR full gate.

## Locale (`ko`)

To reflect gettext msgids in templates and designated Python paths, run `python scripts/build_locale_ko.py` from repo root. In PR/CI, `python scripts/build_locale_ko.py --strict` verifies every literal `_("...")` in `django_apps/web/views/public_pages.py` exists in `KO` inside `scripts/build_locale_ko.py` (`tests/unit/test_build_locale_ko_strict.py`).

## Completion reporting

Agent and PR descriptions use **Caveman 6 sections only** per [`AGENTS.md`](../../../AGENTS.md) · [`.cursor/rules/shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc). **Do not report completion without all 6 sections.**

| Caveman section | Include |
|------------|-------------|
| **Summary** | Change summary · work classification |
| **Files** | Changed files · why |
| **Contracts** | Contracts · invariants; why tests were added/skipped |
| **Tests** | narrow/full `pytest` · `ruff` · `mypy` · `black`/`black --check` — pass/fail/skipped |
| **Risks** | Unrun commands · remaining risk |
| **Next** | Follow-up; use “complete” only here |

Exceptions: Plan mode body · user-requested detailed explanation · `documents/` file body. Details: [`cursor_usage.md`](cursor_usage.md) §17.
