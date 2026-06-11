---
name: golden-fixture-optimization-loop
description: >-
  Runs one Golden Fixture Optimization cycle: preflight, baseline run, diagnosis,
  single-hypothesis patch, verification, cycle report, PR, and merge only when
  merge gates pass. Golden map is eval oracle only — never solver input. Use when
  the user says golden loop, golden fixture optimization, optimization cycle,
  run a cycle, continue the golden loop, or /golden-fixture-optimization-loop.
disable-model-invocation: true # procedural skill only; external agent performs reasoning
metadata:
  owner: project
  risk: high
  requires_validation: true
---

# Golden Fixture Optimization Loop

**Role:** Golden Fixture Loop Skill Architect

**Position:** One reproducible optimization cycle from baseline through a recorded decision; merge only when merge gates pass.

**Authority:** [`AGENTS.md`](../../../AGENTS.md) · [`shapez2-core.mdc`](../../rules/shapez2-core.mdc) · [`git-worktree.mdc`](../../rules/git-worktree.mdc) · canonical baseline reports below

**Invoke:** `/golden-fixture-optimization-loop` · `@golden-fixture-optimization-loop`

**Canonical baseline reports (not interchangeable):**

- Invalid MVP baseline (`valid=false`, `l5_failed_sources:60`): [`2026-06-09-golden-loop-baseline.md`](../../../docs/superpowers/reports/2026-06-09-golden-loop-baseline.md)
- Later valid baseline after PR-7–10 (`valid=true`): [`2026-06-09-golden-loop-valid-baseline.md`](../../../docs/superpowers/reports/2026-06-09-golden-loop-valid-baseline.md) — **valid solver output**, not the starting MVP state

---

## One cycle (definition)

```text
baseline 돌리고
→ 진단하고
→ 고치고
→ 성공|실패 기록
→ PR
→ merge (merge gates 통과 시만)
```

**1 cycle** = baseline → diagnosis → patch → verification → report → PR.

Merge is part of the cycle **only when merge gates pass**. If gates fail, close or leave PR unmerged and record **FAILED** or **REVERTED**.

**Not a cycle:** `scripts/run_golden_loop.py` alone — that is the **baseline / verification run** inside a cycle.

**Core rule:** One cycle tests exactly **one dominant hypothesis**. Do not combine unrelated solver, scorer, fixture, or replay changes.

---

## Cycle completion rule

A cycle **always** completes with a recorded decision (**SUCCESS** | **PARTIAL** | **FAILED** | **REVERTED**).

Merge is allowed only when all merge gates pass.

If merge gates fail:

- do not force merge
- mark the cycle **FAILED** or **PARTIAL**
- leave PR open, close PR, or revert according to the decision table
- record the reason in the cycle report

---

## Resume / idempotency

If a cycle is interrupted:

1. Find latest `docs/superpowers/reports/*golden-loop-cycle-*.md`.
2. Inspect current branch, open PRs, and artifact archive under `var/experiments/golden_loop/archive/`.
3. Check whether baseline, patch, verification, PR, or merge is the last completed step.
4. Resume from the **first incomplete** step.
5. Do not rerun destructive setup.
6. **Never overwrite** previous before/after artifacts — archive or create a new `cycle-N` directory/report.
7. If state is ambiguous, **stop** and report the ambiguity instead of patching.

---

## Preflight gate

Before starting a cycle:

```text
- git status clean 확인
- 현재 branch 확인
- master/main 최신화
- open PR / active worktree / active plan-run 확인
- artifact archive (see below) before patching
- protected ignored path 삭제 금지
```

Commands:

```bash
git status --short
git branch --show-current
git fetch origin
git worktree list
gh pr list --state open --limit 10
```

**Never run by default:** `git clean -fdX` or any destructive ignored cleanup. Preview only if user explicitly requests.

**DO NOT delete:**

```text
- var/plan-run/**
- .worktrees/**
- plans/**
- var/experiments/golden_loop/archive/**
```

Dirty worktree → stop per [`git-worktree.mdc`](../../rules/git-worktree.mdc). Use isolated branch or worktree for the cycle.

---

## Artifact archive

Before patching, snapshot current golden loop artifacts:

```text
var/experiments/golden_loop/archive/cycle-N-before/
var/experiments/golden_loop/archive/cycle-N-after/
```

Copy when present (do not overwrite an existing archive — bump `N` or use timestamp suffix):

```text
runs.jsonl
best_config.json
diagnostics.json
best_result.shapez.txt
```

After verification, copy the post-patch baseline run into `cycle-N-after/`.

---

## Baseline contract

Canonical baseline command:

```bash
python scripts/run_golden_loop.py --throughput-targets 80 --write-best-copy
python scripts/summarize_golden_loop_diagnostics.py
```

Default config grid when only `80` is passed: `throughput_target_percent=80`, `budget_ms=60000`, `speed_tier=1` (see `golden_valid_baseline.py`).

**Required baseline artifacts** (under `var/experiments/golden_loop/` unless `--out-dir`):

| Artifact | Purpose |
| --- | --- |
| `runs.jsonl` | Per-grid-cell run records |
| `best_config.json` | Best valid (or best any) record |
| `diagnostics.json` | Failure pattern histogram |
| `best_result.shapez.txt` | Present only when `valid=true` and `--write-best-copy` |

Also capture: branch, commit SHA, command, config grid, score breakdown, validity, top failure pattern.

**Oracle rule (hard):**

```text
Golden fixture/golden_summary/golden blueprint must never be used as solver input.
They are oracle/eval only.
```

Solver input: `empty.shapez.txt`, frozen `genetic_sample_seeds.json`, `game_data_snapshot_min.json`. Golden map is **eval oracle only**.

---

## Diagnosis

Classify the **dominant** failure into **one** bucket before patching:

| Bucket | Examples |
| --- | --- |
| invalidity gate failure | hard validity failed |
| failed source count | `l5_failed_sources:N` |
| route commit failure | `stack_failed_layer:layer_06_*` |
| route island / orphan | `route_island_count`, `orphan_count` |
| transport kind mismatch | `transport_kind_mismatch` |
| output stub mismatch | stub placement / kind |
| connector / root selection | L4/L5 connector choice |
| source ordering conflict | tie-break / priority |
| corridor blocked by L4/L5 | L4 interior / routeable gap |
| budget / time limit | timeout, `remaining_budget_ms_zero` |
| scorer / evaluator issue | metric or threshold change needed |
| artifact / export issue | missing `best_result.shapez.txt` |

**Priority when `l5_failed_sources:N` dominates:** split into **per-failed-source reason histogram** before broad heuristic tuning. Prefer instrumentation cycle first.

Full taxonomy: [reference.md](reference.md#diagnosis-taxonomy)

---

## Patch scope

**Allowed per cycle:**

- small instrumentation PR
- one solver behavior knob
- one bug fix
- one regression test group
- one cycle report update
- adding diagnostic fields / reason codes used only for reporting
- adding non-scoring metrics

**Forbidden per cycle:**

- broad solver rewrite
- fixture contract change without separate spec
- changing golden oracle
- changing **evaluator thresholds** and **solver behavior** in the same PR
- using replay / diagnostic output as solver input

**Examples:**

```text
Good: L5 failed-source reason code · one tie-breaker · one stub bug
Bad:  L3 priority + L4 fill + L5 cost + UI replay in one PR
```

---

## Verification

1. Targeted pytest for touched paths.
2. Re-run baseline command (same grid as cycle start unless hypothesis requires otherwise).
3. Compare before/after metrics (see [reference.md](reference.md#metric-comparison)).
4. `diagnostics.json` failure_patterns diff — diagnostics must not get **less specific**.
5. Archive post-patch artifacts to `cycle-N-after/`.

**Project gates** (when merging): `AGENTS.md` § Validation — at minimum `powershell -File scripts/test_fast.ps1` for cycle PR; full gate before merge to master.

---

## Decision

| Outcome | Criteria |
| --- | --- |
| **SUCCESS** | `valid=true`, tests pass, PR diff matches hypothesis — **closure success** only |
| **PARTIAL** | `valid=false` and (dominant failure count **decreases** or diagnostics **strictly improve**) — never SUCCESS |
| **FAILED** | no improvement, regression, missing diagnostics, or tests fail |
| **REVERTED** | patch removed after negative result |

```text
dominant failure count decrease → PARTIAL only (never SUCCESS).
valid=true → SUCCESS (closure success).
valid=false + failure 감소/diagnostics 개선 → PARTIAL.
```

**PARTIAL may open PR only when:**

- dominant failure count decreased, **or**
- diagnostics became strictly more specific, **or**
- observability improved without solver behavior regression

**PARTIAL must not merge** if it only changes behavior and validity/diagnostics did not improve.

Failed **solver behavior** changes must **not** merge unless they improve observability only. Failed diagnostic-only reports **may** be committed.

---

## Report (required)

Each cycle writes:

`docs/superpowers/reports/YYYY-MM-DD-golden-loop-cycle-N.md`

Template: [reference.md](reference.md#cycle-report-template)

---

## PR and merge gate

**Create PR** when the cycle produced a clean, reviewable change per the **PARTIAL** rules above or **SUCCESS**.

PR body must include: hypothesis, baseline summary, changed files, verification commands, before/after metrics, decision.

**Inspect PR before merge:**

```bash
gh pr checks <PR_NUMBER>
gh pr view <PR_NUMBER> --json mergeStateStatus,reviewDecision,statusCheckRollup
```

**Merge only if:**

- CI green (`gh pr checks` all pass)
- golden loop verification attached or linked in report
- cycle report committed or linked
- diff matches stated hypothesis
- no protected workflow state deleted
- no unrelated dirty files

**After CI green (user-approved merge only):**

```bash
gh pr merge <PR_NUMBER> --squash --delete-branch
git checkout master
git pull --ff-only
```

CI red → fix CI-only issues on same branch **or** mark cycle **FAILED** and leave PR unmerged/closed.

**Do not** merge failed solver behavior changes (observability-only exception above).

---

## Rollback

If cycle worsens validity or hides diagnostics:

```text
- do not stack more changes
- revert last commit or close PR as failed experiment
- record failure reason in cycle report
```

---

## Workflow alignment

Map to Superpowers-style steps:

```text
Spec (hypothesis) → Plan (one change) → Execute → Review → Verification → Finish Branch (PR / merge if gates pass)
```

Contract/PR scope when cycle touches public contracts: [`AGENTS.md`](../../../AGENTS.md) · [`workflow.mdc`](../../rules/workflow.mdc).

---

## First-cycle guidance (current canon)

When baseline shows undifferentiated `l5_failed_sources:N`, the **first** cycle target is reason histogram instrumentation — not broad L3/L4/L5 tuning.

Historical starting point (invalid MVP): [`2026-06-09-golden-loop-baseline.md`](../../../docs/superpowers/reports/2026-06-09-golden-loop-baseline.md) (`valid=false`, no `best_result.shapez.txt`).

---

## Cycle checklist

Copy and track:

```text
- [ ] Preflight: clean tree, branch, no protected path delete
- [ ] Baseline run + summarize + archive/cycle-N-before
- [ ] One dominant failure bucket + one hypothesis
- [ ] Smallest patch; evaluator thresholds ≠ solver in same PR
- [ ] Targeted pytest + baseline re-run + archive/cycle-N-after
- [ ] Before/after metrics + diagnostics diff
- [ ] Decision: SUCCESS | PARTIAL | FAILED | REVERTED
- [ ] Cycle report committed
- [ ] PR opened only if PARTIAL/SUCCESS rules met
- [ ] gh pr checks green → merge; else FAILED / leave unmerged
```

---

## Terminology

| Term | Meaning |
| --- | --- |
| **cycle** | baseline → diagnose → patch → verify → report → PR → merge **if gates pass** |
| **baseline run** | one `run_golden_loop.py` invocation |
| **grid cell** | one `(throughput%, budget_ms, speed_tier)` solver+eval pair inside a baseline run |
