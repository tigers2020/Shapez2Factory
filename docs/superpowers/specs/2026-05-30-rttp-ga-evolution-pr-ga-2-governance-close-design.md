# RTTP GA Evolution PR-GA-2 — Governance Close Design

**Date:** 2026-05-30  
**Status:** CLOSED — PR-GA-2 merged ([#97](https://github.com/tigers2020/Shapez2Factory/pull/97) `e43e197b`, 2026-05-30)  
**Owner:** RTTP Release Governance / asteroid-lab Layer 3 (selection)  
**Scope:** **A only** — PR-GA-2 safe close (no new feature track, no macro unpause, no post-merge v0.1 selection)  
**Parent design:** [`2026-05-29-rttp-ga-evolution-design.md`](2026-05-29-rttp-ga-evolution-design.md) §5  
**Executable plan:** [`../plans/2026-05-29-rttp-ga-evolution-pr-ga-2.md`](../plans/2026-05-29-rttp-ga-evolution-pr-ga-2.md) Tasks 7–9  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)

**Approval record (2026-05-30):**

1. Shadow-enabled ops smoke remains **optional diagnostic**, not a hard gate.  
2. N3 baseline count decrease blocks merge **only if unexplained** (document intentional skip/delete in PR body).  
3. CLOSED governance docs are applied **after squash merge** with PR number and merge SHA (do not mark `current_plan` CLOSED on the feature branch pre-merge).  
4. **Ops addendum:** CC-3 split into **CC-3A** (selection-path smoke — PR-GA-2 merge blocker) and **CC-3B** (throughput-budget passing smoke — product gate, not PR-GA-2 blocker when greedy/evolution fail identically for pre-existing `throughput_target_shortfall`).

---

## §1 — Close criteria

PR-GA-2 is **CLOSED** only when **all** blocks below are satisfied. Any missing item keeps the track **WIP**.

| ID | Criterion | Evidence |
|----|-----------|----------|
| **CC-1** | Squash-merge to `master` | PR number + merge SHA |
| **CC-2** | Implementation plan Tasks 0–8 PASS | Local/CI logs; N3 count note (§2) |
| **CC-3A** | Selection-path ops smoke PASS on canon slug (§3) | `solver_run_id` + readback; greedy baseline parity (§3.2) |
| **CC-3B** | Throughput-budget passing smoke | **Deferred** — product/track issue; not PR-GA-2 merge blocker when §3.3 applies |
| **CC-4** | Default runtime unchanged | Empty/`greedy_regret` config → same class as pre–PR-GA-2; N3 unexplained decrease absent |
| **CC-5** | Forbidden boundaries hold | Arch + standing gates (§2) |
| **CC-6** | Task 9 governance on `master` **after merge** | `current_plan`, design spec status, roadmap B7/Axis A (§5) |

### Normative invariants (CC-5)

```text
selection.mode changes genome selection authority only.

It must not:
- generate candidates
- run route probe inside GA / genome_fitness / ga_evolution_shadow
- bypass incremental_commit
- mutate validation_passed or perform validation repair
- read replay / solver_summary / NDJSON as algorithm input
- change macro_only pipeline selection (select_macro_genome; CLI rejects macro_only + evolution)
```

**Final route proof:** `incremental_commit` with latest `route_domain` re-probe per candidate (unchanged).

**CC-3A (PR-GA-2 selection-path smoke)** — merge blocker. See §3.1–§3.3.

**CC-3B (throughput-budget passing smoke)** — standing product validation; **not** a PR-GA-2 merge blocker when greedy and evolution share the same pre-existing `throughput_target_shortfall` and CC-3A passes (§3.3).

**CC-3A does not require** `ga_evolution_shadow.enabled=true` on the real-map run (§3).

---

## §2 — Verification matrix

Attach this table to the PR **Test plan**. Forbidden pytest flags: `-q`, `--quiet`, `--tb=no`, `-p no:terminal`.

| Tier | Command / owner | Scope | Merge blocker? |
|------|-----------------|-------|----------------|
| **N1** | `python -m pytest tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py tests/unit/asteroid_lab/test_ga_evolution_shadow.py -v --tb=short` | Mapper, primary path, dual shadow, frozen default | **Yes** |
| **N2** | `python -m pytest tests/unit/architecture/test_ga_evolution_no_probe_route.py -v --tb=short` | No `probe_route` in GA modules | **Yes** |
| **N3** | `python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short` | RTTP regression (excl. macro real-map E2E) | **Yes** (see baseline rule) |
| **S1** | `powershell -File scripts/test_capacity_sot.ps1` | Capacity C-GATE / complete-map SoT | **Yes** |
| **S2** | `powershell -File scripts/test_reconstruction_narrow.ps1` | Reconstruction replay/topology (no `test_rttp_replay_*`) | **Yes** |
| **S3** | `powershell -File scripts/test_optimization_contamination.ps1` | PR-B optimization import canon | **Yes** |
| **F** | `powershell -File scripts/test_full.ps1` → `python -m ruff check .` → `python -m mypy django_apps config src` → `python -m black --check .` | Full gate per AGENTS.md | **Yes** |
| **O-A** | `python manage.py run_solver --slug copy-import-495e552c --selection-mode evolution --no-replay` + greedy baseline (§3) | Selection-path ops (CC-3A) | **Yes** |
| **O-B** | Canon slug `validation_passed=true` + `issue_codes=[]` | Throughput-budget product smoke (CC-3B) | **No** for PR-GA-2 when §3.3 applies |
| **CI** | GitHub `ci` + `rttp-lab-macro-smoke` | Default-config regression | **Yes** |

**N1 ruff narrow (PR diff):**

```powershell
python -m ruff check django_apps/asteroid_lab/contracts/selection_mode.py django_apps/asteroid_lab/contracts/ga_evolution_shadow.py django_apps/asteroid_lab/optimization/selection/primary_genome.py django_apps/asteroid_lab/optimization/selection/ga_evolution_shadow.py django_apps/asteroid_lab/optimization/pipeline.py django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/asteroid_lab/management/commands/run_solver.py tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py
```

### N3 baseline rule (amendment 2)

Record **Task 0** N3 passed count in the PR description before implementation merge.

```text
N3 count < Task 0 baseline blocks merge ONLY when the decrease is unexplained.

Intentional test skip, delete, or rename must be documented in the PR body with reason.
A raw count alone is not a merge blocker when the delta is explained.
```

### BLOCKED (stop close)

- Canon slug `copy-import-495e552c` missing (Task 0 shell check).  
- Unexplained N3 decrease vs Task 0 baseline.  
- Tier F or CI red.  
- **CC-3A** fails: evolution run missing `selection.mode=evolution`, wrong `genome_selection` metrics, extra `issue_codes` vs greedy baseline, or no persisted `SolverRun` readback.  
- **Not** blocked solely by `validation_passed=false` / `throughput_target_shortfall` when §3.3 parity holds (CC-3B deferred).

---

## §3 — Runtime smoke contract

**Canonical ops path:** `--selection-mode evolution` (not generic `--config-json-path`; parent design §5 corrected at close).

PR-GA-2 close separates **selection-path smoke (CC-3A)** from **throughput-budget passing smoke (CC-3B)**. Lowering quality bar is forbidden; gates are **split by evidence type**, not removed.

### §3.1 CC-3A — Selection-path smoke (PR-GA-2 merge blocker)

**Commands:**

```powershell
python manage.py run_solver --slug copy-import-495e552c --selection-mode evolution --no-replay
python manage.py run_solver --slug copy-import-495e552c --no-replay
```

**Readback (use recorded `solver_run_id` from evolution run, not “latest” if ambiguous):**

```powershell
python manage.py shell -c "
from django_apps.asteroid_lab import models as m
run = m.SolverRun.objects.get(pk=<EVOLUTION_RUN_ID>)
ss = (run.config_json or {}).get('solver_summary') or {}
steps = ss.get('algorithm_steps') or []
sel = next(s for s in steps if s.get('step_id')=='rttp.genome_selection')
commit = next((s for s in steps if s.get('step_id')=='rttp.commit'), None)
sel_idx = next(i for i,s in enumerate(steps) if s.get('step_id')=='rttp.genome_selection')
commit_idx = next((i for i,s in enumerate(steps) if s.get('step_id')=='rttp.commit'), None)
print('solver_run_id', run.pk)
print('selection', (run.config_json or {}).get('selection'))
print('sel_mode', sel.get('metrics', {}).get('selection_mode'))
print('genome_selection_before_commit', sel_idx < commit_idx if commit_idx is not None else False)
print('issue_codes', ss.get('issue_codes'))
print('validation_passed', ss.get('validation_passed'))
"
```

| Check | Evolution run | Greedy baseline run |
|-------|---------------|---------------------|
| `SolverRun` persisted | Required | Required |
| `config_json.selection.mode` | `"evolution"` | absent or `"greedy_regret"` |
| `rttp.genome_selection.metrics.selection_mode` | `"evolution"` | `"greedy_regret"` |
| `genome_selection` before `rttp.commit` | true | true |
| Extra `issue_codes` vs greedy | **none** (same set) | — |

**Exit code policy (known non-pass-capable slug):**

```text
Exit code 0 is required for pass-capable ops slugs (historical B-CS2 / E5 class).

For copy-import-495e552c after Capacity C-GATE (reconstruction_max inflation), the slug may
no longer satisfy throughput_target_percent at any allowed percent (10–80). CLI exit code 1
from throughput validation is expected and does NOT fail CC-3A when §3.3 parity holds.

Authority for CC-3A: persisted SolverRun + readback parity, not validation_passed alone.
```

### §3.2 Optional diagnostic — shadow enabled

```text
Shadow readback is optional unless the PR changes shadow runtime behavior.

ga_evolution_shadow.enabled defaults false; PR-GA-2 core is evolution primary, not shadow execution.
Shadow dual-mode is covered by N1 (test_ga_evolution_shadow.py).
CLI --selection-mode evolution may auto-enable shadow for diagnostics; not required for CC-3A.
```

When ops intentionally enables shadow (`ga_evolution_shadow.enabled=true` via config), expect:

- `primary_selection_mode == "evolution"` in shadow metrics when step present.  
- Title **"GA evolution shadow (greedy baseline)"** when evolution is primary.

Absence of `rttp.ga_evolution_shadow` step on a default-config real-map run is **not** a close failure.

### §3.3 CC-3B — Throughput-budget smoke (product gate; PR-GA-2 non-blocker when parity)

```text
Throughput-budget passing smoke remains required for release-quality product validation,
but it is NOT evidence against PR-GA-2 selection correctness when ALL hold:

1. Greedy (default) and evolution runs share the same issue_codes set.
2. Failure includes throughput_target_shortfall (post C-GATE reconstruction_max / target policy).
3. config_json.selection.mode=evolution and genome_selection metrics record evolution on the evolution run.
4. N1/N2/N3/S/F/CI tiers pass (no PR-GA-2-specific regression).
```

**Recorded evidence (2026-05-30, local):**

| `solver_run_id` | `selection.mode` | `genome_selection.selection_mode` | `issue_codes` | `reconstruction_max` (informative) |
|-----------------|------------------|-----------------------------------|---------------|-------------------------------------|
| 102 | `evolution` | `evolution` | `rttp_validation_failed`, `throughput_target_shortfall` | 75360 |
| 103 | (default greedy) | `greedy_regret` | same as 102 | 75360 |

Historical reference: run 76 (`validation_passed=true` at 10% target) used `reconstruction_max` 15360 — pre–complete-map SoT class.

**CC-3B follow-up (separate track):** throughput target floor vs complete-map `reconstruction_max`, or canon ops slug refresh — **not** PR-GA-2 scope (§6).

### Recommended regression line (PR body)

```powershell
python manage.py run_solver --slug copy-import-495e552c --no-replay
```

→ No `selection.mode=evolution`; greedy default + PR-GA-1 shadow contract unchanged.

### CLI guard

`--macro-only` + `--selection-mode evolution` must fail fast (`test_run_solver_macro_only_and_selection_mode_evolution_raises`).

---

## §4 — Regression risks

| Risk | Signal | Mitigation |
|------|--------|------------|
| Default becomes evolution | CI / default slug | `RttpPipelineConfig.selection_mode` default `greedy_regret`; `test_default_pipeline_matches_explicit_greedy_mode` |
| Shadow steals commit authority | Commit spy | `test_observe_only_false_does_not_switch_commit_authority` |
| Evolution bypasses commit | Step order / spy | `test_incremental_commit_receives_evolution_genome_when_mode_evolution` |
| GA calls route probe | N2 | `test_ga_evolution_no_probe_route` |
| Macro path polluted | Pipeline + CLI | `test_macro_path_unchanged_by_selection_mode_evolution`; CLI raise |
| Dual-mode shadow confusion | N1 + optional ops | Evolution primary → shadow runs greedy baseline; greedy primary → shadow runs GA |
| PR-GA-1 shadow regression | N1 | Full `test_ga_evolution_shadow.py` |
| Runtime cost spike | CI duration | `ga_evolution_shadow.enabled` default **false** |
| Fitness uses commit output | S1 | C-GATE unchanged; no `CommitResult` in `genome_fitness` |

**Pre-merge manual (30s):** PR diff — `incremental_commit(` in normal path still receives single `primary_genome` from `select_primary_genome`.

---

## §5 — Governance updates (Task 9)

**Timing (amendment 3):**

```text
code + tests + local gates on feat/rttp-ga-evolution-pr-ga-2
→ open PR (current_plan stays ACTIVE with PR-GA-2; no CLOSED without merge SHA)
→ CI green
→ squash merge to master
→ master follow-up commit: CLOSED rows + roadmap + design spec status (CC-6)
```

Do **not** mark `current_plan` PR-GA-2 **CLOSED** on the feature branch before merge SHA exists.

### 5.1 `documents/ai/current_plan.md` (post-merge)

Replace ACTIVE PR-GA-2 block with:

```text
**CLOSED (YYYY-MM-DD):** RTTP GA evolution **PR-GA-2** — config-gated selection.mode (evolution primary) — PR #NN (`<merge-sha>`).
Plan: docs/superpowers/plans/2026-05-29-rttp-ga-evolution-pr-ga-2.md
Governance close: docs/superpowers/specs/2026-05-30-rttp-ga-evolution-pr-ga-2-governance-close-design.md
```

**Next focus** (one line only):

```text
v0.1 next track selection — new spec + ACTIVE row (macro child-pool fixture OR explicit defer).
```

Keep **BLOCKED** macro child-pool text; do not unpause macro.

### 5.2 `docs/superpowers/specs/2026-05-29-rttp-ga-evolution-design.md`

```text
**Status:** PR-GA-1 CLOSED (#95 `5b7ead43`); PR-GA-2 CLOSED (#NN, YYYY-MM-DD)
```

§5 ops smoke: canonical `--selection-mode evolution` (remove stale `--config-json-path`-only wording if present).

### 5.3 `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`

- **Axis A — Open next:** PR-GA-2 CLOSED (#NN); catalog arc remains CLOSED; next = macro child-pool fixture spec (new spec + ACTIVE).  
- **B7 Step 7:** greedy default ✅; bounded evolution primary ✅ (PR-GA-2); macro/full GA ⏸ (new spec).

### 5.4 Parent plan

[`2026-05-29-rttp-ga-evolution.md`](../plans/2026-05-29-rttp-ga-evolution.md) Appendix A → link PR-GA-2 plan as **CLOSED**.

### 5.5 PR body (required)

- Summary: fail-closed `selection.mode`; default `greedy_regret` unchanged.  
- Test plan: §2 matrix + N3 baseline note.  
- Ops CC-3A: `solver_run_id` 102 / 103 parity table (§3.3); note exit code 1 + CC-3B deferred.  
- Non-scope: §6.

---

## §6 — Explicit non-scope

Not in PR-GA-2 close PR or this governance doc:

| Item | Reason |
|------|--------|
| Macro child-pool fixture spec | BLOCKED; separate spec |
| v0.1 next track selection (post-merge brainstorming) | After CC-6 |
| Lab UI `selection.mode` | Separate UI track |
| Default `ga_evolution_shadow.enabled=true` | Runtime/CI cost |
| Macro pipeline GA | Parent design §3 |
| Survivability / commit metrics → fitness | Phase 5; forbidden solver input |
| LNS / deferred retry behavior change | Selection-only PR |
| New replay event types | Metrics JSON only |
| Generic `--config-json-path` loader | Plan out of scope |
| Macro unpause / unskip macro tests | Fixture spec first |
| Marking `current_plan` CLOSED pre-merge | No merge SHA |
| Fixing canon slug throughput budget (CC-3B) | Separate product spec |

---

## §7 — Close runbook (executing-plans handoff)

```text
1. Task 8: N1 → N2 → N3 (record count; explain delta) → S1–S3 → F
2. Task 7: CC-3A selection-path smoke + readback; CC-3B deferred if §3.3 → PR create
3. CI green
4. Squash merge
5. Task 9: governance on master (CC-6) — separate docs commit acceptable
6. B brainstorming (next track) — separate session
```

**Next skill after this spec:** `executing-plans` on [`2026-05-29-rttp-ga-evolution-pr-ga-2.md`](../plans/2026-05-29-rttp-ga-evolution-pr-ga-2.md) Tasks 7–9 only (implementation Tasks 0–6 assumed complete on branch).

---

## Spec self-review

| Check | Result |
|-------|--------|
| Placeholder scan | No TBD in normative sections |
| Internal consistency | CC-3A selection-path vs CC-3B throughput split; shadow optional |
| Scope | Close governance only; no implementation steps duplicated from plan |
| Ambiguity | N3 baseline = unexplained decrease only; governance post-merge only |

---

## References

- [`2026-05-29-rttp-ga-evolution-design.md`](2026-05-29-rttp-ga-evolution-design.md)  
- [`2026-05-29-rttp-ga-evolution-pr-ga-2.md`](../plans/2026-05-29-rttp-ga-evolution-pr-ga-2.md)  
- [`2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md)  
- [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)
