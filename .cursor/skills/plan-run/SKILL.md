---
name: plan-run
description: >-
  Linear plan queue executor for shapez2Factory. Scans plans/{high,mid,low},
  picks one eligible plan, runs it in an isolated worktree via executing-plans,
  validates, updates Linear, opens PR, and babysits when ≥5 open PRs on master.
  Invoke via /plan-run (default: auto) | pick |
  run [SHA-XX] | skip [SHA-XX] | ship | babysit | auto [SHA-XX] [--merge] |
  status | recover | clear. Use status only with explicit /plan-run status.
disable-model-invocation: true
---

# /plan-run — Linear plan queue

Execute approved plans from the repo plan queue. One plan per run.

- **Manual subcommands** — confirm at pick and ship; see [Manual confirmation semantics](#manual-confirmation-semantics).
- **`auto`** — default headless mode; chains phases without re-prompting; see [Auto mode](#plan-run-auto).

Canon: [`AGENTS.md`](../../../AGENTS.md) · [`.cursor/rules/agent_scope.mdc`](../../rules/agent_scope.mdc) · [`.cursor/rules/git-worktree.mdc`](../../rules/git-worktree.mdc)

Plan queue root: **`plans/high/` · `plans/mid/` · `plans/low/`** only — **not** `docs/plans/`.

Default branch: **`master`**.

State file (session handoff): `var/plan-run/active.md` (gitignored via `var/`).

---

## Commands

| Command | Purpose |
|---------|---------|
| `/plan-run pick` | Read-only: propose next eligible plan; no edits |
| `/plan-run run [SHA-XX]` | Worktree + implement + validate; stop before PR |
| `/plan-run skip [SHA-XX]` | Mark no-code plan skipped (user confirmed) |
| `/plan-run ship` | Push branch + `gh pr create` (user confirmed) |
| `/plan-run babysit` | Batch triage when ≥5 open PRs on `master`; merge only on user confirm |
| `/plan-run auto [SHA-XX] [--merge]` | Chain pick → run → commit → ship → babysit (when batch gate passes) |
| `/plan-run auto resume [--merge]` | Continue `active.md` from current phase |
| `/plan-run status` | Report `active.md`, worktrees, open PR |
| `/plan-run recover` | Inspect stale `active.md`; classify resumable state |
| `/plan-run clear` | Mark run cleared; does not delete worktree or branch |

### Default invocation

| Input | Action |
|-------|--------|
| `/plan-run` alone | Headless **`auto`** — see routing below |
| `/plan-run status` | Read-only status report only |

**`/plan-run` alone (no subcommand)** — same consent as `/plan-run auto` / `auto resume`:

1. If `active.md` has `status: active` and run is resumable (`phase` / `last_successful_phase` < `merged`, including `failed`) **and** not babysit-deferred at `pr-open` → **`auto resume`**.
2. If `last_successful_phase: pr-open` and open PRs on `master` **< 5** ([babysit batch gate](#babysit-batch-gate-5-open-prs)) → fresh **`auto`** (next plan; [mutex exception](#active-run-mutex)).
3. Else if no active run, or `status: cleared` / `achieved` → fresh **`auto`**.
4. Dirty root before fresh `auto` → `/clean-root auto` then retry.

**Never** default to `status`. Status is explicit: **`/plan-run status`** only.

**Aliases:** `auto --merge`, `auto merge`, `auto --through-merge` enable merge phase. `auto --allow-linear-offline` permits auto when Linear MCP unavailable (use sparingly).

---

## Manual confirmation semantics

What each command **counts as** user confirmation:

| Command | Confirms | Does **not** confirm |
|---------|----------|----------------------|
| `/plan-run` (alone) | same as `/plan-run auto` or `auto resume` per [default invocation](#default-invocation) | merge (needs `--merge`) |
| `/plan-run status` | nothing (read-only) | all mutating phases |
| `/plan-run pick` | nothing (read-only) | worktree, Linear, commit, PR, merge |
| `/plan-run run SHA-XX` | worktree create, plan `in_progress`, Linear → In Progress (or Linear offline if user confirmed) | commit, push, PR, merge |
| `/plan-run skip SHA-XX` | plan `skipped`, Linear comment only | worktree, commit, PR, merge |
| `/plan-run ship` | commit (if needed), push, PR, Linear → In Review | merge |
| `/plan-run babysit` | in-scope CI/review fixes | merge (unless user also says merge) |
| `/plan-run auto` | commit, push, PR, Linear; babysit only when [batch gate](#babysit-batch-gate-5-open-prs) passes | merge (needs `--merge`) |
| `/plan-run auto --merge` | merge when [merge gate](#merge-gate---merge-only) passes | — |

Do **not** re-ask for Linear In Progress when user already invoked `/plan-run run SHA-XX`.

---

## Global guards

### Dirty main worktree guard

Applies to commands that may **edit root-tracked files**:

- `run`
- `auto` (fresh start)
- `skip` (edits plan frontmatter in root)
- `ship` when committing from root (worktree commits OK when cwd is worktree)
- merge cleanup touching root checkout

Does **not** block:

- `pick` (read-only)
- `status`, `clear`, `recover`
- `babysit` read-only inspection (`gh pr view`, `gh pr checks`, comment triage without root edits)
- `auto resume` when the next phase edits **only inside the worktree** (verify cwd)

If dirty root blocks a command:

```text
BLOCKED: dirty main worktree · tried: git status --short · next: /clean-root auto then retry
```

Run **`/clean-root auto`** (or `/clean-root plan` first) before `run`, fresh `auto`, or `skip`. See [`.cursor/skills/clean-root/SKILL.md`](../clean-root/SKILL.md).

Read-only commands may report dirty root as **info**, not as a hard stop.

### Active run mutex

If `active.md` has `status: active`:

- **allowed:** `status`, `recover`, `clear`, `ship`, `babysit`, `auto resume`, `skip` (only when user confirms abandoning current run first)
- **refused:** fresh `pick`, `run`, `auto` (without `resume`)

Use `/plan-run recover` before `/plan-run clear` when unsure whether worktree/PR still exist.

**Babysit batch gate exception:** When `last_successful_phase` is `pr-open`, open PR count on `master` is **< 5**, and babysit was deferred — fresh `pick`, `run`, and `auto` (without `resume`) are **allowed** so the queue can ship more PRs before batch babysit.

### Babysit batch gate (≥5 open PRs)

Do **not** enter babysit / `ci-green` until **≥ 5** open PRs target `master`.

**Count open PRs:**

```bash
gh pr list --state open --base master --json number
```

Use the JSON array length. Report as `open_prs_on_master: N`.

| Command | When open PRs < 5 | When open PRs ≥ 5 |
|---------|-------------------|-------------------|
| `/plan-run babysit` | **Defer** — report count; do not triage or merge | Run **`babysit`** on deferred PRs (start with `active.md` `pr_url` when set, then other open plan-run PRs) |
| `/plan-run auto` / `auto resume` at `ci-green` | **Stop at `pr-open`** — checkpoint ok + babysit deferred | Continue babysit → `ci-green` |
| `/plan-run ship` (manual) | After PR open: suggest next plan, not babysit | May suggest `/plan-run babysit` |
| `/plan-run status` | Always report `open_prs_on_master` vs threshold | Same |

**Defer output (babysit batch gate):**

```text
Summary
- Issue: SHA-XX · phase: pr-open
- Open PRs on master: N / 5 (babysit deferred)

Next
- /plan-run pick  (ship more plans)
- /plan-run run SHA-YY
- /plan-run babysit  (when N ≥ 5)
```

Do not treat babysit deferral as `failed`. Keep `last_successful_phase: pr-open`.

### Hermes

- Do **not** invoke Hermes unless plan frontmatter has `hermes: required`.
- If the first otherwise eligible plan has `hermes: required` and Hermes is unavailable:
  - **manual `pick`:** `BLOCKED:` — report the plan; do **not** silently choose a lower-priority plan
  - **auto:** `BLOCKED:` at pick; do not continue
  - **exception:** user explicitly says to skip Hermes-blocked plans → skip that plan only and continue scan
- If `hermes: required` mid-run and Hermes unavailable: `BLOCKED:` and ask user.

### Linear unavailable

When Linear MCP is not connected or query fails:

| Command | Behavior |
|---------|----------|
| `pick` | Report Linear state **unknown** for candidate; still propose plan from file queue |
| `run` | Continue only if user confirms **Linear offline mode** in this message |
| `skip` | Update plan file; skip Linear comment |
| `ship`, `babysit` | `BLOCKED:` unless user confirms Linear offline mode |
| `auto` | `BLOCKED:` unless `--allow-linear-offline` is in the message |
| `status`, `recover` | Continue; report Linear unknown |

`--allow-linear-offline` does not bypass dirty guard, mutex, or merge gate.

**Forbidden flag combination:** `--allow-linear-offline` and `--merge` together → **`BLOCKED:`** immediately. Linear must be available before auto merge. With offline mode, auto may open PR but must stop at `pr-open` (or `ci-green` only when [babysit batch gate](#babysit-batch-gate-5-open-prs) passes).

### Auto forbidden (manual subcommands only)

For `pick`, `run`, `skip`, `ship`, `babysit`, `status`, `recover`, `clear`: no commit, push, PR, merge, or Linear write beyond what [Manual confirmation semantics](#manual-confirmation-semantics) allows.

**`auto` / `auto resume` override** commit/push/PR/Linear for chained phases. Merge only with `--merge`.

### Stale Linear claim

Linear issue is **In Progress** (or started) but execution never began — common after `todo-plan-automation` moved issues without creating a worktree.

**Detect `stale-linear-claim`** when **all** true for a plan's `linear_issue`:

- Linear status is In Progress / started (not Todo, Backlog, Done, Canceled)
- no `active.md` for that issue (or no `active.md` at all)
- no worktree under `.worktrees/auto-<issue>-*` or `.worktrees/auto-<ISSUE>-*`
- no open PR whose branch/title/body references that issue
- plan frontmatter `status` is `planned` or `in_progress`

| Command | Behavior |
|---------|----------|
| `pick` | Do **not** silently skip. Report first queue-order match as **`stale-linear-claim`** (not eligible by default). Do not fall through to lower-priority plans unless user says to skip stale claims. |
| `recover` | Scan `plans/{high,mid,low}` + Linear MCP; list all `stale-linear-claim` issues with suggested next steps. |
| `run SHA-XX` | **Allowed** when dirty root is clean — attaches real `active.md` + worktree to an orphan Linear claim. Do not move Linear back to Todo unless user abandons. |
| `auto` (fresh) | Same as pick — report stale claim; do not auto-run until user confirms `/plan-run run SHA-XX` or skip-stale policy. |

**Pick output when blocked by stale claim:**

```text
Summary
- Blocked: SHA-XX · stale-linear-claim
- Plan: plans/<tier>/<file>.md
- Linear: In Progress (no active.md, no worktree, no PR)

Next
- /plan-run run SHA-XX
- or move SHA-XX back to Todo in Linear if abandoning
```

---

## `active.md` schema

Full state file written at claim time; update after every phase transition:

```yaml
status: active | achieved | cleared | failed
mode: manual | auto
auto_merge: false
linear_issue: SHA-XX
plan_path: plans/high/2026-06-10-SHA-12-....md
phase: picked | claimed | worktree_ready | running | implemented | committed | pr-open | ci-green | merged | failed
worktree: .worktrees/auto-SHA-12-<slug>
branch: auto/SHA-12-<slug>
started_at: <ISO8601>
last_successful_phase: <phase>
failure_phase: <phase or empty>
failure_reason: <text or empty>
remote_pushed: false
commit_sha: <sha or empty>
pr_url: <url or empty>
linear_previous_state: <state or empty>
linear_current_state: <state or empty>
linear_offline: false
```

On any failure after external side effects:

1. Set `failure_phase`, `failure_reason`, `last_successful_phase`.
2. Never delete worktree automatically after commit or push.
3. Report recovery:

```text
Recovery: /plan-run auto resume | /plan-run babysit | /plan-run recover | /plan-run clear
```

---

## Plan frontmatter contract

```yaml
linear_issue: SHA-12
title: ...
priority: High | Mid | Low
labels: [...]
status: planned | in_progress | done | skipped
created_by: todo-plan-automation
hermes: required   # optional; only when Hermes handoff mandatory
depends_on:      # optional; source of truth for prerequisites
  - SHA-10
  - SHA-11
```

Matching key: **`linear_issue`** → Linear identifier (e.g. `SHA-12`).

### Dependency resolution

**Source of truth (in order):**

1. frontmatter **`depends_on`** — list of `linear_issue` ids; every listed issue must be Done/Merged before pick/run
2. body text (`Depends on High`, `Depends on Mid`, links to other plans) — **advisory only**; use when `depends_on` absent; report ambiguity to user rather than guessing

---

## `/plan-run pick`

Read-only. Propose **one** plan; wait for user confirm before `run`.

### Selection algorithm

1. `git fetch origin` (best effort).
2. Scan tiers: `plans/high/*.md` → `plans/mid/*.md` → `plans/low/*.md`.
3. Within each tier: sort by filename ascending (date prefix).
4. For each plan in tier order, evaluate skip vs **stale-linear-claim** vs eligible:
   - frontmatter `status` is not `planned` → skip (unless `in_progress` with real active run — use `recover`)
   - Linear In Progress + [stale-linear-claim signals](#stale-linear-claim) → **report as blocked stale claim**; stop scan (do not pick lower priority unless user said skip stale claims)
   - Linear issue not in Todo / Backlog / planned-equivalent — if Linear MCP unavailable, report state unknown (see [Linear unavailable](#linear-unavailable)); do not treat as skip
   - body contains `Human Review Required` with `yes` (case-insensitive)
   - body contains `No code action required` → suggest `/plan-run skip SHA-XX`
   - any id in frontmatter **`depends_on`** not Done/Merged (Linear MCP or plan `status: done` in `plans/done/`)
   - body dependency text only when `depends_on` absent — if ambiguous, `BLOCKED:` and ask user
   - same `linear_issue` has open PR or active worktree under `.worktrees/auto-*` (and not stale-linear-claim)
5. First **eligible** (Todo/Backlog + not skipped) plan wins.
6. If that plan has `hermes: required` and Hermes is unavailable → **`BLOCKED:`** (do not fall through to lower-priority plans unless user said to skip Hermes-blocked plans).

### Pick output (caveman)

```text
Summary
- Candidate: SHA-XX · <title>
- Plan: plans/<tier>/<file>.md
- Priority: High|Mid|Low
- Depends: none | blocked on SHA-YY

Next
Confirm: /plan-run run SHA-XX
```

Do not edit files during `pick`.

---

## `/plan-run skip [SHA-XX]`

Mark a no-code or intentionally skipped queued plan.

**Requires:** explicit user confirmation in the message (e.g. `/plan-run skip SHA-XX`).

### Steps

1. Find matching plan by `linear_issue` under `plans/**`.
2. Verify frontmatter `status` is `planned` or `in_progress`.
3. Set frontmatter `status: skipped`.
4. If Linear MCP available, add comment: `Skipped by /plan-run: <reason from plan or user>.`
5. Do **not** create worktree, branch, commit, push, PR, or merge.

If `active.md` is `status: active` for a **different** issue, warn and require user confirm to abandon that run first.

**Do not use `skip` to abandon a failed implementation.** Use `/plan-run recover` first, then `/plan-run clear` if abandoning the active run.

### Output

```text
Summary
- Issue: SHA-XX
- Plan: <path>
- Status: skipped
```

---

## `/plan-run run [SHA-XX]`

Implement one plan in an isolated worktree. Stops after validation — **no PR**.

Invoking `/plan-run run SHA-XX` confirms:

- worktree creation
- plan frontmatter `in_progress`

If Linear is already In Progress (**stale-linear-claim**), do not re-move Linear — create `active.md` + worktree to attach execution state.

If Linear MCP is **available** and issue is Todo/Backlog, it also confirms Linear → In Progress (do not re-prompt).

If Linear MCP is **unavailable**, continue only when the message explicitly confirms **Linear offline mode** (e.g. `run SHA-XX linear offline`). Set `linear_offline: true` in `active.md`; skip Linear writes until MCP returns.

### 1. Resolve plan

- If `SHA-XX` given: find matching `linear_issue` under `plans/**`.
- Else: use last `pick` candidate; if none, run pick algorithm — user must confirm via `run`.

### 2. Claim state

Write `active.md` ([schema above](#activemd-schema)) with `mode: manual`, `phase: claimed`.

Update plan frontmatter `status: in_progress`.

Linear: when MCP available — move to **In Progress** only if not already In Progress; label `plan-run:claimed` if team uses labels. Record `linear_previous_state` / `linear_current_state`. When offline mode, skip Linear writes and note in report.

### 3. Worktree (`using-git-worktrees`)

- Directory: `.worktrees/` (must pass `git check-ignore .worktrees`).
- Branch: `auto/SHA-XX-<short-slug-from-title>` off `origin/master`.
- Baseline: `powershell -File scripts/test_fast.ps1` — on fail, remove worktree, set `phase: failed`, `BLOCKED:`.
- Solver touch: `PYTHONPATH=<worktree>/src` when plan targets `src/shapez2_factory/`.
- Set `phase: worktree_ready`, `last_successful_phase: worktree_ready`.

All edits only inside the worktree path.

### 4. Execute

1. Read the single plan file end-to-end.
2. Paste [`execution-scope-contract.md`](../../../documents/ai/templates/execution-scope-contract.md) short block; fill tasks from **Implementation Plan**.
3. Follow superpowers **`executing-plans`**: implement listed tasks only.
4. Domain ambiguous → **`grill-me-shapez2`** (read-only) before edits.
5. CLI touch → **`cli-boundary`**.

### 5. Validate

Run plan **Tests / Validation** or **Validation Plan**, then minimum:

```bash
python manage.py check
ruff check .
mypy django_apps config src
powershell -File scripts/test_fast.ps1
```

On failure: one in-scope fix loop; then `phase: failed`, record `failure_phase` / `failure_reason`, `BLOCKED:`.

### 6. Stop boundary

- Final report with **`STOPPED_AT_APPROVED_SCOPE`**.
- Update `phase: implemented`, `last_successful_phase: implemented`.
- Suggest `/plan-run ship` — do **not** push or open PR.

Optional: commit when user explicitly requests (`git-workflow`).

---

## `/plan-run ship`

Push branch and open PR. Requires `active.md` phase `implemented` (or user names branch/PR).

**Requires:** `/plan-run ship` in this message (confirmation).

### Steps

1. In worktree: ensure commits exist; **commit if needed** (see staging rules below).
2. `git push -u origin <branch>` — set `remote_pushed: true`.
3. Record `commit_sha` from `git rev-parse HEAD`.
4. `gh pr create --base master --title "..." --body` with plan summary + test checklist — **skip if `pr_url` already set** (resume path).
5. Linear → **In Review**; label `plan-run:pr-opened` (or skip Linear write in offline mode).
6. Update `active.md`: `phase: pr-open`, `pr_url`, `last_successful_phase: pr-open`.
7. Count open PRs on `master` ([babysit batch gate](#babysit-batch-gate-5-open-prs)). If **< 5**, report babysit deferred and suggest next plan — do **not** invoke babysit.

### Commit if needed (staging rules)

- Stage **only** files changed inside the active worktree for this plan.
- Stage **only** paths required by the selected plan scope.
- **Manual `ship`:** show `git status --short` before commit; **abort** if unrelated files are present.
- **`auto` ship:** emit `git status --short` in checkpoint; abort if files outside plan scope appear.

On push failure: set `failure_phase: pr-open`, record actual `remote_pushed` value, report recovery via `auto resume` or manual push.

Follow superpowers **`finishing-a-development-branch`** Option 2 only.

---

## `/plan-run babysit`

Batch PR triage — run only when [babysit batch gate](#babysit-batch-gate-5-open-prs) passes (**≥ 5** open PRs on `master`).

### Preflight

1. `gh pr list --state open --base master --json number,url,headRefName,title`
2. If count **< 5** → **defer** (see batch gate defer output). Do not triage.
3. If count **≥ 5** → proceed.

Use Cursor **`babysit`** skill. Start with PR from `active.md` when `pr_url` set; then other open plan-run PRs (`auto/SHA-*` branches) in PR number order unless user names a URL.

- Resolve merge conflicts preserving plan intent.
- Triage Bugbot / review — fix only valid in-scope issues.
- Fix CI failures in PR scope only; do not weaken CI/workflows.

Read-only inspection (`gh pr view`, checks) is allowed even when root worktree is dirty.

**Merge only if** user explicitly says merge AND [merge gate](#merge-gate---merge-only) passes.

### On merge

1. Linear → **Done**; label `plan-run:merged`.
2. Plan `status: done`; move to `plans/done/<original-filename>`.
3. `git worktree remove <worktree>`; delete local branch when safe.
4. `active.md` → `status: achieved`, `phase: merged`, `last_successful_phase: merged`.

---

## `/plan-run status`

Read and report (never blocked by dirty root):

- `var/plan-run/active.md`
- `git worktree list` (`.worktrees/auto-*`)
- `gh pr view` when `pr_url` set
- `open_prs_on_master` vs babysit batch gate (≥5)
- Linear issue state when MCP available
- dirty root as info if present

---

## `/plan-run recover`

Inspect stale or interrupted runs (never blocked by dirty root).

### Steps

1. Read `active.md` if present.
2. If `active.md` **missing**: scan open PRs on `master` (`gh pr list --state open --base master --json number,url,headRefName,title`); match `auto/SHA-*` branches to `plans/**` `linear_issue`; note worktrees (`git worktree list`). Use this to classify PR-open runs lost to accidental state deletion.
3. **Scan stale Linear claims:** walk `plans/{high,mid,low}` in pick order; for each `planned`/`in_progress` plan, query Linear; apply [stale-linear-claim](#stale-linear-claim) detection. List all matches.
4. If `active.md` present (or reconstructed from step 2), verify:
   - worktree path exists (`git worktree list`)
   - branch exists locally/remotely
   - PR open if `pr_url` set (`gh pr view`)
   - Linear state if MCP available
5. Classify:

| Class | Meaning | Suggested next |
|-------|---------|----------------|
| `stale-linear-claim` | Linear In Progress; no active.md/worktree/PR | `/plan-run run SHA-XX` or Todo in Linear |
| `resumable` | worktree + branch OK; phase < merged | `/plan-run auto resume` |
| `active-pr-open` | active.md + worktree + open PR; CI pending or green | `/plan-run babysit` when ≥5 open PRs, else monitor |
| `active-pr-open-ci-red` | active.md + worktree + open PR; required CI failing | fix in worktree + push; `/plan-run babysit` when ≥5 open PRs |
| `stale-active-no-worktree` | active.md but worktree missing | `/plan-run clear` then `/plan-run run SHA-XX` or abandon |
| `stale-active-pr-open` | open PR exists but active.md/worktree incomplete or missing | reconstruct via PR scan; then `/plan-run babysit` when ≥5 open PRs |
| `manual-cleanup-required` | branch/PR/worktree mismatch | report paths; user decides |

**Classify PR-open runs:** when `active.md` + worktree + `pr_url` all verify, use `active-pr-open` or `active-pr-open-ci-red` (check `gh pr checks` / required CI). Reserve `stale-active-pr-open` for PR without complete session state.

Do not auto-clear or auto-delete anything.

---

## `/plan-run clear`

Set `active.md` `status: cleared`. Does not remove worktree, branch, or PR.

**Prefer `/plan-run recover` first** when active lock may be stale.

---

## `/plan-run auto`

Chains phases **in order**. After each phase: update `active.md`, emit checkpoint, continue — **no re-prompt**.

Invoking `/plan-run auto` = consent for commit, push, PR, Linear; babysit only when [batch gate](#babysit-batch-gate-5-open-prs) passes. Merge requires `--merge`.

### Syntax

```text
/plan-run auto
/plan-run auto SHA-12
/plan-run auto --merge
/plan-run auto SHA-12 --merge
/plan-run auto resume
/plan-run auto resume --merge
/plan-run auto --allow-linear-offline
/plan-run auto SHA-12 --allow-linear-offline
```

**Forbidden:** `--merge` with `--allow-linear-offline` in the same message.

Set `mode: auto`, `auto_merge: true|false`, `linear_offline: true|false` at start. If both merge and offline flags detected → `BLOCKED:` before any phase.

### Phase machine

Execute from first incomplete phase per `active.md`.

| Step | Phase key | Action | On fail |
|------|-----------|--------|---------|
| 1 | `picked` | [Selection algorithm](#selection-algorithm) | `BLOCKED:` no eligible plan |
| 2 | `claimed` | Write `active.md`; plan `in_progress`; Linear In Progress | `BLOCKED:` |
| 3 | `worktree_ready` | [Worktree setup](#3-worktree-using-git-worktrees) | remove worktree; `failed` |
| 4 | `implemented` | [Execute + validate](#4-execute) | `failed`; record side effects |
| 5 | `committed` | Commit plan scope; set `commit_sha` | `failed`; keep worktree |
| 6 | `pr-open` | [Ship steps](#steps); set `remote_pushed`, `pr_url` | `failed`; record push/PR state |
| 7 | `ci-green` | If open PRs on `master` **≥ 5**: `babysit` until checks green or blocked. If **< 5**: stop at `pr-open` (babysit deferred, not failed) | stop; `failure_phase: ci-green` only after babysit started |
| 8 | `merged` | **Only if `--merge`:** merge + [cleanup](#on-merge) | stop at `ci-green` |

**Resume (normal):** enter at the phase **after** `last_successful_phase`. `auto resume` never re-picks unless `phase` is missing.

**Resume from `phase: failed`:**

- Resume from **`failure_phase`** (not from scratch).
- Preserve all confirmed external side effects:
  - if `commit_sha` exists and worktree `HEAD` unchanged → do **not** recommit
  - if `remote_pushed: true` → do **not** force-push unless explicitly required to fix CI
  - if `pr_url` exists → do **not** create a second PR; continue babysit/merge on existing PR
- After successful retry, clear `failure_phase` / `failure_reason`; update `last_successful_phase`.

### Checkpoint format

```text
[plan-run auto] phase=<key> issue=SHA-XX ok | BLOCKED
```

### Auto-specific rules

1. **No re-prompt** between phases.
2. **Commit before ship** — always phase `committed`.
3. **Human Review Required: yes** — exclude at pick; never auto-run.
4. **Validation retry** — one in-scope fix loop per command; then `failed`.
5. **Babysit batch gate** — do not start `ci-green` / babysit until **≥ 5** open PRs on `master`; stop at `pr-open` with defer report (not `failed`).
6. **Babysit rounds** — max **10** rounds once batch gate passes; then `BLOCKED: babysit round limit`.
7. **Hermes** — first eligible plan `hermes: required` without Hermes → `BLOCKED:` (unless user skipped Hermes-blocked plans).
8. **Linear** — without MCP, `BLOCKED:` unless `--allow-linear-offline`; offline auto stops at `pr-open` or deferred `ci-green` (no merge).
9. **Flag conflict** — `--allow-linear-offline` + `--merge` → `BLOCKED:` before start.
10. **Long plans** — stop at `failed` or complete validation; continue via `auto resume` after `/goal`.

### Merge gate (`--merge` only)

Requires Linear MCP available (`linear_offline` must be false). Merge only when **all** true:

- required CI checks green
- no unresolved `CHANGES_REQUESTED`
- no merge conflicts
- plan `Human Review Required` is not `yes`

Else stop at `ci-green`; report blockers.

### Failure handling (auto)

On any phase failure after external side effects:

1. Update `failure_phase`, `failure_reason`, `last_successful_phase`.
2. Set `remote_pushed`, `commit_sha`, `pr_url` accurately — never assume.
3. Never auto-delete worktree after commit or push.
4. Report:

```text
BLOCKED: <what> · tried: <steps> · next: /plan-run auto resume | /plan-run babysit | /plan-run recover
```

### Auto vs manual

| Action | Manual | `auto` |
|--------|--------|--------|
| Pick confirm | required | skipped |
| Worktree + Linear In Progress | `/run SHA-XX` | automatic |
| Commit | user ask | automatic |
| Push / PR | `/ship` | automatic |
| Babysit | when ≥5 open PRs | when batch gate passes |
| Linear writes | per semantics | automatic |
| Merge | user ask | `--merge` + gates |

---

## Long plans + `/goal`

```text
/plan-run auto SHA-6
/goal <plan validation condition> or stop after N turns
/plan-run auto resume
/plan-run auto resume --merge
```

Manual: `/plan-run run SHA-6` → `/goal` → `/plan-run ship` → (repeat until ≥5 open PRs) → `/plan-run babysit`.

---

## Skills map

| Phase | Skill |
|-------|--------|
| Root clean before run/auto | **`clean-root`** |
| Queue workflow | **`plan-run`** |
| Chained execution | **`plan-run auto`** |
| Stale lock inspection | **`plan-run recover`** |
| Harness checklist | `shapez2-workflow` |
| Worktree | superpowers `using-git-worktrees` |
| Implement | superpowers `executing-plans` |
| Domain grill | `grill-me-shapez2` |
| Commit/push | `git-workflow` |
| PR completion | superpowers `finishing-a-development-branch` |
| PR batch triage (≥5 open PRs) | `babysit` |
| Pre-merge | `quality-check` |

---

## Failure report

```text
BLOCKED: <what> · tried: <steps> · next: <one recovery command>
```

Keep worktree after commit/push unless user asks to remove.
