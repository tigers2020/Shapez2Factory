# RTTP Pass-Capable Slug Certification (Track B)

**Date:** 2026-05-30  
**Status:** **CLOSED (2026-05-30)** — Track B Task 4 complete; registered slug `rttp-cert-candidate-tiny-passable-v2`  
**Owner:** RTTP Release / Optimization Architect  
**Track:** **B** — designate at least one **pass_capable** slug for T3 milestone ops under v0.1 RTTP  
**Parent:** [`2026-05-30-rttp-ops-authority-tier-design.md`](2026-05-30-rttp-ops-authority-tier-design.md) §6–§9 Track **B**  
**Predecessors (CLOSED):**

- Ops tier taxonomy — [`2026-05-30-rttp-ops-authority-tier-design.md`](2026-05-30-rttp-ops-authority-tier-design.md)
- T2 diagnostic policy — [`2026-05-30-rttp-throughput-policy-t2-diagnostic-canon-design.md`](2026-05-30-rttp-throughput-policy-t2-diagnostic-canon-design.md) (D-PR)
- FL-06 T1b layout — [`2026-05-30-rttp-fl06-output-stub-route-reservation-alignment-design.md`](2026-05-30-rttp-fl06-output-stub-route-reservation-alignment-design.md)
- B-CS2 ops smoke (historical T3 framing) — [`2026-05-24-b-cs2-trunk-ops-smoke-design.md`](2026-05-24-b-cs2-trunk-ops-smoke-design.md)

**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)  
**Roadmap:** [`2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md)

**User decision (2026-05-30):** Proceed with **Track B** before Track A. Do not promote `copy-import-495e552c` to pass-capable or mask T2 shortfall on that slug.

---

## §1 — Purpose

RTTP v0.1 pipeline closure (Axis B milestones, standing pytest) is **not** the same as **product success on every real Lab map**. The diagnostic canon `copy-import-495e552c` is intentionally authoritative for **T0 / T1a / T1b stress** and **expected T2 shortfall**, but it must **not** be the sole slug used to claim **T3 full-ops-pass**.

**Goal:**

```text
Register slug classes (diagnostic_canon | pass_capable | unknown).
Certify at least one pass_capable slug where the same v0.1 algorithm
(T0 + T1b + T2 + validation_passed) passes on documented default config.
Persist evidence (solver_run_id + tier readback) in current_plan / roadmap.
```

This track delivers a **healthy-slug baseline** for milestone ops, CI optional smoke, and merge policy — without changing throughput formulas, validation rules, or diagnostic canon semantics.

**North-star invariant (unchanged):**

```text
Everything is provisional until connected to exterior trunk.
Candidate-time reachable is NOT commit success proof.
```

---

## §2 — Non-goals (Track B v1)

| Item | Follow-up |
|------|-----------|
| Restore T2/T3 on `copy-import-495e552c` | Track **A** (explicit product approval) |
| Lower `reconstruction_max`, change PR-2c target formula, or cap targets | Forbidden; Track D deferred Approach 3 |
| Weaken `validation_passed`, layout asserts, or catalog fail-closed | Forbidden (Track E closed) |
| Promote diagnostic canon to `pass_capable` | Forbidden |
| Force PASS via `diagnostic_expected_shortfall` or policy-only fields | Forbidden |
| Full GA, macro unpause, evolution-only “fix” for throughput | PAUSE / new spec |
| Using replay / prior `solver_summary` / NDJSON as **algorithm input** | Forbidden (global) |
| Scanning every slug on every PR by default | Optional CI; v1 = registry + manual/batch scan command |
| New pipeline metrics (`reprobe_count`, etc.) | Out of scope unless separate spec |

---

## §3 — Slug classes

Normative registry lives in `django_apps/asteroid_lab/contracts/rttp_ops_policy.py` (extend D-PR module). **No free-form** `rttp_ops_slug_class` values in tests or persistence.

### `diagnostic_canon`

| Field | Value |
|-------|--------|
| Slug(s) v1 | `copy-import-495e552c` only (`RTTP_DIAGNOSTIC_CANON_SLUG`) |
| Role | T0 selection-path; T1a/T1b commit stress; **expected** T2 shortfall after complete-map class |
| T3 | **Never** pass-capable; `t3_blocked_reason` may be `t2_not_pass_capable_on_diagnostic_canon` when T2 fails |
| Merge policy | T3 FAIL here is **not** a regression gate for unrelated PRs (ops tier §8) |

### `pass_capable`

| Field | Rule |
|-------|------|
| Count v1 | **≥ 1** registered slug |
| Role | T3 milestone ops (B-CS2 successor, E-series class smokes) |
| Registration | Explicit list + certification evidence row; not inferred from a single lucky run without re-run |
| T2 on pass_capable | `throughput_budget_satisfied == true`; `t2_policy_status == satisfied`; `diagnostic_expected_shortfall == false` |
| Mutual exclusion | A slug MUST NOT be both `diagnostic_canon` and `pass_capable` |

### `unknown`

| Field | Rule |
|-------|------|
| Default | Any slug not in either registry |
| T2 policy | `shortfall` when budget false (not `expected_diagnostic_shortfall`) |
| T3 ops | Do not claim milestone T3 until certified and registered |
| Scan outcome | Candidate may become `pass_capable` after certification procedure (§5–§6) |

### Classification precedence

```text
if slug in RTTP_PASS_CAPABLE_SLUGS:
    rttp_ops_slug_class = pass_capable
elif slug == RTTP_DIAGNOSTIC_CANON_SLUG:
    rttp_ops_slug_class = diagnostic_canon
else:
    rttp_ops_slug_class = unknown
```

`classify_t2_policy` MUST use final `rttp_ops_slug_class` (pass_capable shortfall is never “expected diagnostic”).

---

## §4 — T3 certification rule

A slug is **certified pass_capable** when **all** criteria hold on **certification config** (§5) in a **recorded** ops run.

### Tier requirements (normative)

| ID | Tier | Criterion | Readback |
|----|------|-----------|----------|
| B-T3-1 | T3 shell | CLI exit code `0` | `manage.py run_solver` |
| B-T3-2 | T3 summary | `solver_summary.validation_passed == true` | `config_json.solver_summary` |
| B-T3-3 | T3 issues | `solver_summary.issue_codes == []` | same |
| B-T3-4 | T1b | `rttp.commit` step `passed == true` | pipeline steps |
| B-T3-5 | T1a | `confirmed_count > 0`; `rttp.commit` exists | summary + step metrics |
| B-T3-6 | T2 | `throughput_budget_satisfied == true` | summary |
| B-T3-7 | T2 issues | `throughput_target_shortfall` **not** in `issue_codes` | summary |
| B-T3-8 | T2 policy | `t2_policy_status == satisfied` | summary |
| B-T3-9 | Diagnostic flag | `diagnostic_expected_shortfall == false` | summary |
| B-T3-10 | Slug class | `rttp_ops_slug_class == pass_capable` | summary (after registry wire-up) |
| B-T3-11 | T0 (when in scope) | Default greedy: no `selection.mode=evolution` required for v1 certification unless spec amendment | config_json |
| B-T3-12 | Evidence | `solver_run_id`, slug, date, git SHA (branch) in evidence artifact | §6 |

**Dependency (ops tier, unchanged):**

```text
T3  ⇒  T0 + T1b + T2
T1b ⇒  T1a
```

**Pure evaluator (implementation):** `evaluate_t3_certification(*, slug, solver_summary, pipeline_steps) -> T3CertificationResult` in contracts layer — read-only over persisted outputs; no solver invocation inside evaluator.

### Failure taxonomy (scan / cert reports)

| `cert_status` token | Meaning |
|---------------------|---------|
| `certified_pass` | All B-T3-* satisfied |
| `fail_t1b` | Layout / `rttp.commit.passed` false |
| `fail_t2` | Throughput budget false |
| `fail_t3_shell` | `validation_passed` false or non-empty `issue_codes` |
| `fail_runtime` | Exception / RTTP disabled / missing map |
| `skipped_diagnostic` | Slug is diagnostic canon (never cert candidate) |
| `skipped_no_map` | Project missing map input |

---

## §5 — Scan policy

### Objectives

1. Discover **candidate** slugs from the Lab database (not from replay artifacts).
2. Run **full** RTTP v0.1 path per slug (reconstruction → candidates → probe → selection → commit → validation).
3. Rank candidates by **cert_status**; register the **first** stable `certified_pass` slug for v1 (additional slugs optional).

### Candidate universe (v1)

| Source | Include | Exclude |
|--------|---------|---------|
| `AsteroidProject` with non-empty map input | All slugs | `copy-import-495e552c` (always `skipped_diagnostic`) |
| Fixtures / copy-code files | Out of scan DB command | Use direct `run_solver --slug` if imported as project |
| Macro-only | Exclude when `macro_only_mode` would be required | Macro track PAUSE |

**Default ordering:** slug ascending (deterministic). Optional `--limit N` for dev.

### Certification config (B-CS2 class)

Matches historical B-CS2 / E-series smokes unless a follow-up spec narrows flags:

```text
ASTEROID_LAB_RTTP_ENABLED = True
macro_only_mode = false
selection.mode = greedy (default; no --selection-mode evolution for v1 cert)
throughput_target_percent = project/Lab default (document per slug if non-10)
--no-replay recommended for batch scan (output still from solver_summary)
```

**Forbidden during scan/cert:**

```text
- reconstruction_max manipulation
- throughput formula changes
- validation repair
- treating candidate_count or normal_count alone as PASS
```

### Scan command (v1 deliverable)

**Preferred:** `python manage.py scan_rttp_slug_certification`  
**Acceptable:** `scripts/scan_rttp_pass_capable_slugs.ps1` wrapping sequential `run_solver` + JSON report

| Flag | Purpose |
|------|---------|
| `--slug <s>` | Single slug (dev) |
| `--all` | All eligible projects |
| `--limit N` | Cap batch size |
| `--no-replay` | Default true for scan |
| `--output <path>` | Write evidence JSON (§6) |
| `--dry-run` | List slugs only |

Scan MUST call the same runtime entry as HTTP/CLI (`run_solver_runtime_for_project`), not a shortened pipeline.

### Stability rule (registration)

A slug is registered in `RTTP_PASS_CAPABLE_SLUGS` only after:

1. One `certified_pass` scan row recorded in evidence JSON, **and**
2. One **confirmation** re-run within 7 days (same config) still `certified_pass`, **or**
3. Product owner waives confirmation in PR body (exception; document in `current_plan`).

---

## §6 — Evidence schema

### File location

```text
docs/superpowers/reports/YYYY-MM-DD-rttp-pass-capable-slug-certification.json
```

Optional human summary: same basename `.md` (ops table only; not algorithm input).

### JSON shape (version 1)

```json
{
  "schema_version": 1,
  "scan_date": "2026-05-30",
  "git_ref": "<branch-or-sha>",
  "certification_config": {
    "macro_only_mode": false,
    "selection_mode": "greedy",
    "throughput_target_percent": 10,
    "no_replay": true
  },
  "diagnostic_canon_slug": "copy-import-495e552c",
  "registered_pass_capable_slugs": [],
  "rows": [
    {
      "slug": "example-slug",
      "cert_status": "fail_t2",
      "solver_run_id": 111,
      "validation_passed": false,
      "issue_codes": ["throughput_target_shortfall"],
      "throughput_budget_satisfied": false,
      "t2_policy_status": "shortfall",
      "rttp_ops_slug_class": "unknown",
      "confirmed_count": 12,
      "rttp_commit_passed": true
    }
  ],
  "first_certified_slug": null,
  "confirmation_run": null
}
```

### `current_plan.md` evidence row (required on close)

```markdown
**CLOSED (2026-05-30):** Track B pass-capable slug — `rttp-cert-candidate-tiny-passable-v2` — cert `solver_run_id` 151, confirm 153; borderline T2 pass (actual=target=480); reports: task4-confirm-v2.json, task4-limit30.json
```

**Registered (Task 4):**

```python
RTTP_PASS_CAPABLE_SLUGS = frozenset({"rttp-cert-candidate-tiny-passable-v2"})
```

**Risk (retained):** borderline pass — zero margin on 80% target; fixture slug is SoT (not live crop builder `solver_run_id=136`).

---

## §7 — Lab / CLI display policy

Extends Track D §6; does not change exit-code contract.

| `rttp_ops_slug_class` | Lab / CLI behavior |
|-----------------------|-------------------|
| `diagnostic_canon` | Show diagnostic T2 copy when `diagnostic_expected_shortfall`; never “T3 healthy” badge |
| `pass_capable` | Show “T3 reference slug” when last run `certified_pass`; T2 shortfall = real regression language |
| `unknown` | Neutral copy; T2 shortfall = investigate (not “expected diagnostic”) |

**HUD / summary fields (additive):**

| Field | When |
|-------|------|
| `rttp_ops_slug_class` | Every RTTP run with policy fields |
| `t3_certification_eligible` | `pass_capable` slug + run passed B-T3-2..B-T3-9 |
| `ops_tier_summary` | Optional compact string: `T0:pass,T1b:pass,T2:fail,...` (tokens in contracts) |

**CLI `run_solver`:** After summary block, one line when `rttp_ops_slug_class == pass_capable` and certified: `ops_slug: pass_capable (T3 reference)`.

---

## §8 — Tests

### Unit (required)

| Module | Covers |
|--------|--------|
| `test_rttp_ops_slug_classification.py` | Registry precedence; diagnostic vs pass_capable mutual exclusion |
| `test_rttp_t3_certification_evaluator.py` | `evaluate_t3_certification` on fixture summaries (pass / fail_t1b / fail_t2) |
| Extend `test_rttp_throughput_policy_diagnostic.py` | pass_capable slug → `shortfall` not `expected_diagnostic_shortfall` |

### Integration (optional v1)

| Module | Covers |
|--------|--------|
| `test_scan_rttp_slug_certification_command.py` | Dry-run lists slugs; mocks runtime for one row |

### Standing gates (unchanged)

```powershell
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v
powershell -File scripts/test_optimization_contamination.ps1
```

### Architecture

- No free-form `cert_status`, `rttp_ops_slug_class`, or `issue_codes` in tests.
- `evaluate_t3_certification` MUST NOT import optimization pipeline adapters (contracts + summary dict only).

---

## §9 — Rollout

```text
1. D-PR #99 merge (T2 policy + rttp_ops_slug_class unknown/diagnostic)
2. B-GOV: approve this spec + plan; current_plan ACTIVE row
3. B-PR: registry + evaluator + scan command + tests
4. Batch scan → pick first stable certified_pass slug
5. Register RTTP_PASS_CAPABLE_SLUGS + confirmation re-run
6. Wire classify_t2_policy / summary for pass_capable class
7. Lab/CLI display (§7)
8. Close: evidence JSON + current_plan + roadmap “Open next” → Track A optional / macro PAUSE unchanged
```

**Merge blocker (after B-PR):**

| PR class | Evidence |
|----------|----------|
| Milestone T3 / B-CS2 successor | **pass_capable** slug + B-T3-* on PR branch |
| Selection-only | Diagnostic canon T0 still sufficient |
| Track B implementation | Unit tests + at least one registered pass_capable slug |

---

## §10 — Risks

| Risk | Mitigation |
|------|------------|
| No slug in DB passes T3 on v0.1 | Document scan null result; open Track A or import simpler map; do not weaken cert criteria |
| False positive from one lucky run | Confirmation re-run + stability rule (§5) |
| pass_capable slug regresses on `master` | Optional weekly CI smoke on registered slug only; not full DB scan |
| Confusing pass_capable with “algorithm fixed” on diagnostic canon | Lab copy + slug class badge (§7) |
| Scan duration on large DB | `--limit`, `--slug`, off-peak batch |
| `unknown` slug shortfall blocks PRs | Merge policy: only **registered** pass_capable required for T3 claims |

---

## §11 — Acceptance criteria

### B-GOV (docs)

- [x] User approved Track B direction (2026-05-30)
- [ ] This spec on disk; `current_plan.md` ACTIVE row points here
- [x] Roadmap “Open next” references Track B CLOSED (2026-05-30)

### B-PR (implementation)

- [x] `RTTP_PASS_CAPABLE_SLUGS` + `classify_rttp_ops_slug(slug)` in `rttp_ops_policy.py` (2026-05-30)
- [ ] `evaluate_t3_certification` + tests
- [ ] Scan command or script + one evidence JSON under `docs/superpowers/reports/`
- [ ] ≥ 1 slug registered; confirmation run recorded
- [ ] `classify_t2_policy` uses pass_capable class (no expected diagnostic shortfall on pass_capable)
- [ ] Lab/CLI display per §7
- [ ] Forbidden shortcuts checklist passed (no formula/validation weakening)

---

## §12 — Verification

**After registration:**

```powershell
python manage.py run_solver --slug <pass_capable_slug> --no-replay
python -m pytest tests/unit/asteroid_lab/test_rttp_ops_slug_classification.py tests/unit/asteroid_lab/test_rttp_t3_certification_evaluator.py -v
```

**Diagnostic control (must still shortfall):**

```powershell
python manage.py run_solver --slug copy-import-495e552c --no-replay
```

Expect: `t2_policy_status == expected_diagnostic_shortfall`; not registered as pass_capable.

---

## References

- [`2026-05-30-rttp-ops-authority-tier-design.md`](2026-05-30-rttp-ops-authority-tier-design.md)
- [`2026-05-30-rttp-throughput-policy-t2-diagnostic-canon-design.md`](2026-05-30-rttp-throughput-policy-t2-diagnostic-canon-design.md)
- [`2026-05-24-b-cs2-trunk-ops-smoke-design.md`](2026-05-24-b-cs2-trunk-ops-smoke-design.md)
- [`2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md)
- [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)
