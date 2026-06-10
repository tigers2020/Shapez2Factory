---
name: plan-run
description: >-
  Linear plan queue executor for shapez2Factory. Scans plans/{high,mid,low},
  picks one eligible plan, runs it in an isolated worktree via executing-plans,
  validates, updates Linear, opens PR, babysits when ≥5 open PRs on master,
  and on merge moves Linear In Review → Done with Korean summary comment per PR.
  Batch babysit: resolve duplicate cards, merge passing PRs first;
  defer infra/out-of-scope failures without blocking the batch.
  Invoke via /plan-run (default: auto) | pick |
  run [SHA-XX] | skip [SHA-XX] | ship | babysit | auto [SHA-XX] [--merge] |
  status | recover | clear | batch-status | clean-batch. Use status only with explicit /plan-run status.
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

Runtime state (gitignored under `var/plan-run/`):

| File | Purpose |
|------|---------|
| `active.md` | Current run session — primary handoff |
| `claims.jsonl` | Append-only claim/event log per issue |
| `batch.md` | Optional batch worktree summary cache |

**Root/master is orchestration only** — no product-code edits on root. Code changes happen in `.worktrees/plan-run-batch` (or legacy dedicated worktrees).

Batch worktree root: `.worktrees/plan-run-batch`

Default worktree mode: **batch worktree reuse**.

Important:

- Reuse the same worktree directory across consecutive plans.
- Do **not** reuse the same branch across plans.
- Each plan still gets its own branch: `auto/SHA-XX-<slug>`.
- Each plan still gets its own commit and PR.
- The batch worktree must be clean before switching to the next plan.

Legacy dedicated worktrees (`.worktrees/auto-SHA-XX-<slug>/`) may still exist from runs started before batch mode; finish those runs in place — do not migrate mid-run.

---

## Commands

| Command | Purpose |
|---------|---------|
| `/plan-run pick` | Read-only: propose next eligible plan; no edits |
| `/plan-run run [SHA-XX]` | Worktree + implement + validate; stop before PR |
| `/plan-run skip [SHA-XX]` | Mark no-code plan skipped (user confirmed) |
| `/plan-run ship` | Push branch + `gh pr create` (user confirmed) |
| `/plan-run babysit [merge]` | Batch triage when ≥5 open PRs on `master`; merge → Linear Done + 한국어 summary per PR |
| `/plan-run auto [SHA-XX] [--merge]` | Chain pick → run → commit → ship → babysit (when batch gate passes) |
| `/plan-run auto resume [--merge]` | Continue `active.md` from current phase |
| `/plan-run status` | Report `active.md`, worktrees, open PR |
| `/plan-run batch-status` | Report batch worktree, current branch, open plan-run PR count |
| `/plan-run clean-batch` | Clean/sync reusable batch worktree after PR pile-up |
| `/plan-run recover` | Inspect stale `active.md`; classify resumable state |
| `/plan-run clear` | Mark run cleared; does not delete worktree or branch |

### Default invocation

Parse subcommand from user message.

| Input | Action |
|-------|--------|
| `/plan-run` alone | Headless **`auto`** — see routing below |
| `/plan-run status` | Read-only status report only |

**`/plan-run` alone (no subcommand)** — same consent as `/plan-run auto` / `auto resume`:

1. **Preflight:** [Runaway PR guard](#runaway-pr-guard) + dirty root guard (fresh auto only — **BLOCKED**, no auto PR/clean-root), active run mutex, [batch PR gate](#batch-pr-gate), open PR scan (`open_plan_run_prs`, `open_prs_on_master`).
2. If `active.md` has `status: active`, run is resumable (`phase` / `last_successful_phase` < `merged`, including `failed`), **and** not babysit-deferred at `pr-open` → route to **`auto resume`**.
3. Else → route to headless fresh **`auto`**.
4. Headless fresh auto may [auto-attach stale Linear claims](#auto-stale-claim-attach) when preflight passes and queue-head is a `stale-linear-claim`.

**Mutex exception:** When `last_successful_phase: pr-open` and open PRs on `master` **< 5**, fresh `auto` is allowed even if `active.md` still references the shipped issue — replace `active.md` with the next plan claim (prior run recoverable via PR scan).

**Never** default to `status`. Status is explicit: **`/plan-run status`** only.

**Blocked headless auto when:** [batch PR gate](#batch-pr-gate) (≥5 open plan-run PRs), unrelated dirty root (fresh auto), conflicting active implementation phase, or [auto stale-claim attach](#auto-stale-claim-attach) preconditions fail.

**Aliases:** `auto --merge`, `auto merge`, `auto --through-merge` enable merge phase. `auto --allow-linear-offline` permits auto when Linear MCP unavailable (use sparingly).

---

## Manual confirmation semantics

What each command **counts as** user confirmation:

| Command | Confirms | Does **not** confirm |
|---------|----------|----------------------|
| `/plan-run` (alone) | same as `/plan-run auto` or `auto resume` per [default invocation](#default-invocation); may [auto-attach stale claims](#auto-stale-claim-attach) | merge (needs `--merge`) |
| `/plan-run status` | nothing (read-only) | all mutating phases |
| `/plan-run batch-status` | nothing (read-only) | all mutating phases |
| `/plan-run clean-batch` | batch worktree sync to master when safe | commit, PR, merge |
| `/plan-run pick` | nothing (read-only) | worktree, Linear, commit, PR, merge |
| `/plan-run run SHA-XX` | worktree create, runtime claim in `var/plan-run/**`, Linear → In Progress (or Linear offline if user confirmed) | commit, push, PR, merge, `plans/**` frontmatter |
| `/plan-run skip SHA-XX` | plan `skipped` + metadata commit, Linear comment only | worktree, commit (product), PR, merge |
| `/plan-run ship` | commit (if needed), push, PR, Linear → In Review; may metadata-commit `plans/**` `in_progress` | merge |
| `/plan-run babysit` | in-scope CI/review fixes; on merge → [Linear merge completion](#linear-merge-completion) per merged PR | merge (unless user also says merge) |
| `/plan-run babysit merge` | [partition](#batch-babysit-partition); duplicate resolve; merge passing PRs + Linear Done/summary; defer infra-blocked | — |
| `/plan-run auto` | commit, push, PR, Linear; [auto stale-claim attach](#auto-stale-claim-attach); babysit only when [babysit batch gate](#babysit-batch-gate-5-open-prs) passes | merge (needs `--merge`) |
| `/plan-run auto --merge` | merge when [merge gate](#merge-gate---merge-only) passes | — |

Do **not** re-ask for Linear In Progress when user already invoked `/plan-run run SHA-XX`.

---

## Global guards

### Runaway PR guard

**Dirty root is an automation stop gate — not a trigger to open a PR.**

This automation must **never** create a GitHub PR solely to fix root dirty state, workflow rules, or `clean-root` behavior.

If the root worktree is dirty before starting implementation:

1. **Stop immediately** — no branch, no PR, no product commit on root.
2. Do **not** run `/clean-root auto` unless the **operator** explicitly requested it in the same message.
3. Do **not** run `git clean -fdX` or delete `var/plan-run/**`, `.worktrees/**`, `plans/**`.
4. Do **not** commit workflow-state changes unless the operator explicitly asked (or a single [automation-safety PR](#automation-safety-pr) exception applies).

Report:

```text
BLOCKED: dirty root worktree
Dirty files:
- <path> · <class A|B|C|E>
Next:
- operator must commit, stash, or discard manually
- /clean-root plan (read-only preview)
- operator may run /clean-root auto — not automatic
```

**Forbidden loop:**

```text
dirty root → clean-root auto → commit → branch → PR   # STOP
```

#### Automation-safety PR (only exception)

A **single** explicitly operator-requested PR may patch automation rules (skills, prompts, guards).

Requirements:

- Title must contain `automation-safety`
- Scope: `.cursor/skills/**`, `documents/prompt/**`, governance only — **no** product code
- Do **not** open another automation-safety PR while one is already open
- Never use automation-safety to bypass dirty root on unrelated implementation work

### Dirty main worktree guard

Applies to commands that may **leave root tracked files dirty without an immediate metadata commit**:

- `skip` (edits `plans/**` — must [metadata-commit](#metadata-commit) in same command)
- `ship` when performing [plan metadata commit](#plan-metadata-lifecycle) on root
- merge cleanup touching root checkout (`plans/done/` move)
- fresh `auto` when unrelated tracked edits remain (skill patches, stale `plans/**` without commit)

Does **not** block (runtime state only — no tracked root edits):

- `run` (writes `var/plan-run/**` only)
- `auto resume` when next phase edits **only inside the worktree** or `var/plan-run/**`
- `pick`, `status`, `batch-status`, `clear`, `recover`
- `babysit` read-only inspection (`gh pr view`, `gh pr checks`, comment triage without root edits)

**Skill patches** (`.cursor/skills/**`) during workflow development are a separate dirty source — operator must commit/stash before fresh `auto`; do **not** auto-chain `/clean-root` or open a PR. See [Runaway PR guard](#runaway-pr-guard).

If dirty root blocks a command:

```text
BLOCKED: dirty root worktree
Dirty files:
- <list from git status --short>
Next:
- operator intervention (commit | stash | discard)
- /clean-root plan (read-only)
- /clean-root auto only if operator explicitly requests it
```

Do **not** auto-invoke `/clean-root auto`, create a branch, or open a PR to clear the gate. See [`.cursor/skills/clean-root/SKILL.md`](../clean-root/SKILL.md).

Read-only commands may report dirty root as **info**, not as a hard stop.

### Root mutation policy

During `/plan-run run` and early auto phases, **do not edit tracked root files** except an explicit [metadata commit](#metadata-commit).

Runtime execution state goes to ignored files only:

- `var/plan-run/active.md`
- `var/plan-run/claims.jsonl`
- `var/plan-run/batch.md`

**Delayed `plans/**` frontmatter** — change tracked plan files only at:

| Phase | Allowed frontmatter change |
|-------|----------------------------|
| `run` / `claimed` | **none** — record `status_shadow: in_progress` in `active.md` + append `claims.jsonl` |
| `ship` / `pr-open` | may set `status: in_progress` + metadata commit on root |
| `merge` | set `status: done`, move to `plans/done/` + metadata commit |
| `skip` | set `status: skipped` + metadata commit in same command |

**Never leave `plans/**` dirty after a phase transition.** Either do not touch frontmatter yet, or metadata-commit immediately.

Product code commits happen only inside the active worktree branch — never on root `master` except plan metadata commits above.

### Plan metadata lifecycle

**At claim (`run` / auto `claimed`):**

1. Write `active.md` with `status_shadow: in_progress`.
2. Append to `claims.jsonl`:

```json
{"ts":"<ISO8601>","linear_issue":"SHA-XX","plan_path":"plans/...","event":"claimed","phase":"claimed"}
```

3. Do **not** modify `plans/**` frontmatter.

**At ship (`pr-open`):**

1. Optionally sync frontmatter: `status: in_progress` (if still `planned`).
2. [Metadata-commit](#metadata-commit) on root when frontmatter changed.

**At merge:**

1. [Linear merge completion](#linear-merge-completion) — In Review → Done + summary comment.
2. Set frontmatter `status: done`.
3. `git mv` plan file to `plans/done/<original-filename>`.
4. Metadata-commit on root.

**At skip:**

1. Set frontmatter `status: skipped`.
2. Metadata-commit in the same command.

### Metadata commit

When plan-run changes tracked `plans/**` files:

```bash
git add plans/<tier>/<file>.md
# or: git add plans/done/<file>.md after merge move
git commit -m "chore(plan-run): <action> SHA-XX"
```

Examples:

- `chore(plan-run): mark SHA-18 in_progress`
- `chore(plan-run): skip SHA-10`
- `chore(plan-run): done SHA-12`

Do not mix product-code files into metadata commits.

### Linear lifecycle (plan-run)

| Phase | Linear state | Write |
|-------|--------------|-------|
| `claimed` / `run` | **In Progress** | `save_issue` `state`; label `plan-run:claimed` if team uses labels |
| `pr-open` / `ship` | **In Review** | `save_issue` `state`; label `plan-run:pr-opened`; optional PR link via `links` |
| `merged` / babysit merge | **Done** | [Linear merge completion](#linear-merge-completion) — status + summary comment |

Linear MCP required for merge (`babysit merge`, `auto --merge`). `--allow-linear-offline` forbids merge.

**Batch babysit (≥5 open PRs):** when merging multiple plan-run PRs in one session, run [Linear merge completion](#linear-merge-completion) for **each** merged PR — not only the `active.md` issue. A merged PR with Linear still In Review is incomplete work.

### Linear comment language

All **`save_comment`** bodies for plan-run (merge, duplicate, deferred, skip) → **Korean** prose.

Keep as-is (do not translate):

- issue ids (`SHA-XX`), PR `#` / URL, branch names, paths, commit SHAs, check names, footer markers (`plan-run:merged`, `plan-run:duplicate`, `plan-run:deferred`, `plan-run:skipped`)

**`### 요약`** bullets: concrete behavior/files in Korean — not generic "PR 머지됨".

**Idempotency:** match footer marker + same PR number/URL — not English heading text.

### Linear merge completion

Required **immediately after** each plan-run PR merge (`gh pr merge` succeeds). Applies to `/plan-run babysit` with user merge consent, `auto --merge`, and manual merge during batch cleanup.

**Requires Linear MCP** (`linear_offline` must be false).

#### 1. Resolve issue

From merged PR (in order):

1. `headRefName` — `auto/SHA-XX-<slug>` → `SHA-XX`
2. PR title/body — `SHA-XX` identifier
3. `plans/{high,mid,low,done}/**` frontmatter `linear_issue` matching branch slug
4. `claims.jsonl` row with matching `pr_url`

If unresolved → `BLOCKED:` report PR; do not mark plan metadata done.

#### 2. Verify Linear state

`get_issue` for `SHA-XX`.

| Current state | Action |
|---------------|--------|
| In Review | proceed |
| In Progress | proceed (ship Linear write missed) |
| Done | skip `save_issue` state; ensure summary comment exists (step 4) |
| Todo / Backlog / Canceled | report drift; ask user — do not auto-Done |

#### 3. Move to Done

```text
save_issue id=SHA-XX state=Done labels+=plan-run:merged
```

Record `linear_previous_state` / `linear_current_state: Done` in `active.md` when that issue is the active run; for other batch merges, append `claims.jsonl` only.

#### 4. Summary comment (required, Korean)

`save_comment` on the issue. **Idempotent:** skip if an existing top-level comment contains `plan-run:merged` and the same PR number/URL.

Body template:

```markdown
## /plan-run 머지 완료

- **PR:** #<number> <pr_url>
- **브랜치:** auto/SHA-XX-<slug>
- **머지 커밋:** <sha> (또는 squash 제목)
- **플랜:** <plan_path or unknown>

### 요약
- <무엇이 반영됐는지 — plan 제목·PR 본문·diff 기준 1–3 bullet, 한국어>
- **검증:** <실행한 검증, 예: test_fast / CI green>

---
plan-run:merged
```

요약은 구체적(동작/파일). "PR 머지됨" 같은 빈 문장 금지.

#### 5. Plan metadata + claims (per issue)

For the resolved `SHA-XX`:

1. [Plan metadata at merge](#plan-metadata-lifecycle) on root (`status: done`, move to `plans/done/`).
2. Append `claims.jsonl`: `{"event":"merged","phase":"merged","pr_url":"..."}`.
3. If this issue matches `active.md` `linear_issue` → `status: achieved`, `phase: merged`.

Repeat steps 1–5 for every PR merged in a batch babysit round before starting the next PR.

#### Batch merge report

```text
Linear merge batch
- #181 SHA-12 → Done + 한국어 요약
- #182 SHA-18 → Done + 한국어 요약 (이미 Done; comment ok)
- #184 SHA-10 → duplicate → SHA-12 (PR closed)
- #186 SHA-13 → deferred (infra-blocked; golden CI out of scope)
- #183 SHA-22 → BLOCKED: issue unresolved
```

### Duplicate card detection

A plan-run card is **`duplicate-card`** when **any** true:

| Signal | Meaning |
|--------|---------|
| Same `linear_issue` has **2+** open plan-run PRs (`auto/SHA-XX-*`) | pick newer/lower PR number as duplicate of oldest open |
| `linear_issue` already **Done** in Linear and another open PR/plan claim exists | superseded run |
| Plan `status: done` in `plans/done/` but open PR or `in_progress` plan duplicate exists | superseded plan file |
| `claims.jsonl` shows `merged` for `SHA-XX` but another open PR for same issue | repeat run |
| Same plan path or same title+`linear_issue` claimed twice with different branches | automation double-fire |
| Linear issue already has `duplicateOf` set | already resolved — skip |

**Not duplicate** (classify separately):

| Signal | Class | Action |
|--------|-------|--------|
| CI red, failures **outside PR diff** (e.g. shared golden baseline) | `infra-blocked` | [defer](#batch-babysit-partition); merge passing PRs first |
| CI red, failures **inside PR diff** | `failed-in-scope` | one babysit fix loop; then defer if still red |
| Linear In Progress + no PR yet + no `active.md` | `stale-linear-claim` | attach, not duplicate |

Scan at: `pick`, `run` (before claim), `babysit` preflight, `recover`.

### Duplicate card resolution

When `duplicate-card` confirmed (babysit merge, `recover`, or explicit user request):

**Canonical issue** = first merged Done, else lowest open PR number, else earliest `claims.jsonl` `claimed` for that `linear_issue`.

For each duplicate `SHA-YY` (non-canonical):

1. **Linear** — `save_issue id=SHA-YY duplicateOf=<canonical> state=Canceled` (or team-equivalent canceled state). Label `plan-run:duplicate` if used.
2. **Comment** on duplicate (Korean):

```markdown
## /plan-run 중복 처리

- **정본 이슈:** SHA-XX
- **사유:** <이미 처리 중 | 두 번째 PR #NNN | 플랜 이미 완료 | #MMM에서 머지됨>
- **조치:** 중복 카드 종료; 정본 이슈에서 작업 계속.

---
plan-run:duplicate
```

3. **GitHub** — close duplicate PR with comment: `/plan-run: #<canonical_pr> 중복으로 종료.`
4. **Plan** — frontmatter `status: skipped`; metadata-commit `chore(plan-run): duplicate SHA-YY → SHA-XX`
5. **claims.jsonl** — `{"event":"duplicate","canonical":"SHA-XX","pr_url":"..."}`

Do **not** delete branches until PR closed. Never mark canonical issue duplicate.

If user did not confirm merge/babysit: report duplicates in `pick` / `recover` only — do not close PRs.

### Batch babysit partition

At `/plan-run babysit` / `ci-green` with ≥5 open PRs, **partition** open plan-run PRs before triage:

```text
1. duplicate-card  → resolve first ([Duplicate card resolution](#duplicate-card-resolution))
2. passing         → merge gate green → merge + Linear Done
3. failed-in-scope → one fix loop → re-check; if still red → deferred
4. infra-blocked   → deferred (comment on Linear; do not block passing merges)
```

**Passing-first rule:** one red PR (active or infra-blocked) must **not** stop merge of green plan-run PRs. Process partition order above.

**Deferred** (not global `failed`):

- `active.md` issue infra-blocked → set `phase: deferred`, `failure_phase: ci-green`, `failure_reason: infra-blocked — <summary>`; clear mutex for next plan when user runs `/plan-run clear` or batch round completes
- Append `claims.jsonl` `{"event":"deferred","reason":"infra-blocked"}`

#### Infra-blocked comment (Linear, Korean)

When CI fails outside PR scope (shared golden, master baseline drift, unrelated workflow):

```markdown
## /plan-run 보류 — infra-blocked

- **PR:** #<number> <url>
- **CI:** <failing check>
- **범위:** PR diff 밖 실패 (<paths>)
- **조치:** passing PR 먼저 babysit 계속; infra는 별도 수정 또는 master green 후 rebase.

---
plan-run:deferred
```

Do **not** auto-`duplicateOf` infra-blocked issues unless they are also `duplicate-card` by table above.

#### Batch babysit report

```text
Batch babysit partition
- passing (2): #181 SHA-12, #182 SHA-18
- duplicate (1): #185 SHA-11 → canonical SHA-10
- infra-blocked (1): #186 SHA-13
- failed-in-scope (0):

Merged: #181, #182
Deferred: #186
Duplicates closed: #185
```

### Runtime claim resolution

Use this (not frontmatter alone) to detect an in-flight plan:

1. `active.md` with `status: active` for that `linear_issue`
2. Latest non-terminal row in `claims.jsonl` for that issue (`event` not `cleared` / `merged` / `skipped`)
3. Open PR whose head branch matches `auto/<issue>-*`
4. Worktree (batch or dedicated) on `auto/<issue>-*` branch with unpushed implementation

Frontmatter `status: in_progress` without any runtime claim above is **stale frontmatter drift** — report in `recover`; do not treat as an active run unless verified.

### Active run mutex

If `active.md` has `status: active`:

- **allowed:** `status`, `batch-status`, `recover`, `clear`, `ship`, `babysit`, `auto resume`, `skip` (only when user confirms abandoning current run first)
- **refused:** fresh `pick`, `run`, `auto` (without `resume`) — except [batch PR gate](#batch-pr-gate) explicit `run SHA-XX` / `auto SHA-XX` with warning when count ≥ 5

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
| `/plan-run babysit` | **Defer** — report count; do not triage or merge | Run **`babysit`** on deferred PRs; on merge run [Linear merge completion](#linear-merge-completion) per PR |
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

### Batch PR gate

Before fresh `/plan-run`, `/plan-run auto`, or `/plan-run run`:

1. Count open plan-run PRs.

A plan-run PR is any open PR where:

- head branch starts with `auto/SHA-`
- or PR has label `plan-run`
- or PR title/body references `/plan-run`

```bash
gh pr list --state open --base master --json number,url,headRefName,title,labels
```

Filter the JSON array by the rules above. Report as `open_plan_run_prs: N`.

2. If open plan-run PR count is **0–4**:

- continue normally

3. If open plan-run PR count is **5 or more**:

- do not silently keep creating PRs
- report cleanup recommendation

```text
BATCH_GATE: open plan-run PRs >= 5 · recommend /plan-run babysit merge (PR cleanup + Linear In Review → Done + summary) before starting more
```

Behavior:

| Command | Behavior when PR count ≥ 5 |
|---------|----------------------------|
| `/plan-run status` | report only |
| `/plan-run batch-status` | report only |
| `/plan-run run SHA-XX` | allowed with warning because user named SHA explicitly |
| `/plan-run auto SHA-XX` | allowed with warning because user named SHA explicitly |
| `/plan-run auto` | BLOCKED; suggest babysit/cleanup |
| `/plan-run` alone | BLOCKED; suggest babysit/cleanup |

This gate blocks headless auto from piling PRs indefinitely. It complements the [babysit batch gate](#babysit-batch-gate-5-open-prs) (when to enter babysit), not replace it.

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
- no worktree under `.worktrees/auto-<issue>-*` or `.worktrees/auto-<ISSUE>-*` (legacy dedicated)
- batch worktree (`.worktrees/plan-run-batch`) is not on `auto/<issue>-*` branch with active implementation for this issue
- no open PR whose branch/title/body references that issue
- plan frontmatter `status` is `planned` or `in_progress` (frontmatter alone does not prove execution started)

| Command | Behavior |
|---------|----------|
| `pick` | Do **not** silently skip. Report first queue-order match as **`stale-linear-claim`**. Do not fall through to lower-priority plans unless user says to skip stale claims. |
| `recover` | Scan `plans/{high,mid,low}` + Linear MCP; list all `stale-linear-claim` issues with suggested next steps. |
| `run SHA-XX` | **Allowed** — attaches `active.md` + worktree to orphan Linear claim. Do not move Linear back to Todo unless user abandons. |
| `auto` (fresh) / `/plan-run` alone | **Auto-attach** when [Auto stale-claim attach](#auto-stale-claim-attach) preconditions pass; else `BLOCKED:` with [headless output](#headless-auto-stale-claim-output). |

**Manual `pick` output when stale claim is queue head (no auto):**

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
phase: preflight | picked | claimed | worktree_ready | running | implemented | committed | pr-open | ci-green | merged | deferred | failed
status_shadow: in_progress

worktree_mode: batch | dedicated
batch_worktree: .worktrees/plan-run-batch
worktree: .worktrees/plan-run-batch
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

batch_open_pr_count: 0
batch_started_at: <ISO8601>
batch_last_cleaned_at: <ISO8601 or empty>
```

For **batch mode** (default for new runs): set `worktree_mode: batch`, `batch_worktree` and `worktree` both `.worktrees/plan-run-batch`.

For **legacy dedicated runs** in progress: set `worktree_mode: dedicated`, `worktree: .worktrees/auto-SHA-XX-<slug>`, omit or leave `batch_worktree` empty.

`status_shadow` mirrors execution state while `plans/**` frontmatter may still read `planned` until [ship metadata commit](#plan-metadata-lifecycle).

### `claims.jsonl` format

Append one JSON object per line (never rewrite the file):

```json
{"ts":"2026-06-10T12:00:00Z","linear_issue":"SHA-XX","plan_path":"plans/...","event":"claimed","phase":"claimed"}
{"ts":"...","linear_issue":"SHA-XX","event":"shipped","phase":"pr-open","pr_url":"https://..."}
{"ts":"...","linear_issue":"SHA-XX","event":"merged","phase":"merged"}
```

Terminal events: `cleared`, `skipped`, `merged`, `duplicate`, `deferred`, `failed` (with `failure_reason` when set).

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

**Authoritative execution state** lives in `var/plan-run/**` ([root mutation policy](#root-mutation-policy)). Frontmatter `status` is the durable queue record — updated at ship/merge/skip only, not at claim.

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
   - frontmatter `status` is `done` or `skipped` → skip
   - frontmatter `status` is `in_progress` → skip **unless** [runtime claim](#runtime-claim-resolution) verifies an active run for another issue path; if `in_progress` with no runtime claim → report **stale frontmatter drift** in pick output (still eligible if Linear Todo/Backlog and no other blockers)
   - frontmatter `status` is not `planned` (and not handled above) → skip (use `recover`)
   - Linear In Progress + [stale-linear-claim signals](#stale-linear-claim) → **report as blocked stale claim**; stop scan (do not pick lower priority unless user said skip stale claims)
   - Linear issue not in Todo / Backlog / planned-equivalent — if Linear MCP unavailable, report state unknown (see [Linear unavailable](#linear-unavailable)); do not treat as skip
   - body contains `Human Review Required` with `yes` (case-insensitive)
   - body contains `No code action required` → suggest `/plan-run skip SHA-XX`
   - any id in frontmatter **`depends_on`** not Done/Merged (Linear MCP or plan `status: done` in `plans/done/`)
   - body dependency text only when `depends_on` absent — if ambiguous, `BLOCKED:` and ask user
   - same `linear_issue` has [runtime claim](#runtime-claim-resolution) (open PR, active worktree, or `active.md`) and not stale-linear-claim
   - [duplicate-card](#duplicate-card-detection) — report; suggest [duplicate resolution](#duplicate-card-resolution) or canonical `/plan-run run SHA-XX`
5. First **eligible** (Todo/Backlog + not skipped, not duplicate) plan wins.
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
2. Verify frontmatter `status` is `planned`, or `in_progress` with no conflicting [runtime claim](#runtime-claim-resolution).
3. Set frontmatter `status: skipped`.
4. [Metadata-commit](#metadata-commit): `chore(plan-run): skip SHA-XX`.
5. Append `claims.jsonl` terminal event `skipped`.
6. If Linear MCP available, add Korean comment:

```markdown
/plan-run 스킵: <plan 또는 사용자 사유, 한국어>

---
plan-run:skipped
```
7. Do **not** create worktree, branch, product commit, push, PR, or merge.

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
- runtime claim in `var/plan-run/**` (`status_shadow: in_progress`)

If Linear is already In Progress (**stale-linear-claim**), do not re-move Linear — create `active.md` + worktree to attach execution state.

If Linear MCP is **available** and issue is Todo/Backlog, it also confirms Linear → In Progress (do not re-prompt).

If Linear MCP is **unavailable**, continue only when the message explicitly confirms **Linear offline mode** (e.g. `run SHA-XX linear offline`). Set `linear_offline: true` in `active.md`; skip Linear writes until MCP returns.

### 1. Resolve plan

- If `SHA-XX` given: find matching `linear_issue` under `plans/**`.
- Else: use last `pick` candidate; if none, run pick algorithm — user must confirm via `run`.

### 2. Claim state

Before claim: [duplicate-card scan](#duplicate-card-detection). If duplicate → `BLOCKED:` report canonical `SHA-XX`; suggest [resolution](#duplicate-card-resolution) unless user explicitly re-runs canonical.

Write `active.md` ([schema above](#activemd-schema)) with `mode: manual`, `phase: claimed`, `status_shadow: in_progress`.

Append claim row to `var/plan-run/claims.jsonl` ([format above](#claimsjsonl-format)).

Do **not** modify `plans/**` frontmatter at claim time.

Linear: when MCP available — move to **In Progress** only if not already In Progress; label `plan-run:claimed` if team uses labels. Record `linear_previous_state` / `linear_current_state`. When offline mode, skip Linear writes and note in report.

### 3. Worktree (`using-git-worktrees`)

Default: use reusable batch worktree.

#### Batch worktree path

```text
.worktrees/plan-run-batch
```

#### Branch

Each plan gets a new branch:

```text
auto/SHA-XX-<short-slug-from-title>
```

Do **not** reuse a branch across plans.

#### Setup

1. Ensure `.worktrees/` is gitignored:

```bash
git check-ignore .worktrees
```

2. If `.worktrees/plan-run-batch` does not exist:

```bash
git fetch origin
git worktree add .worktrees/plan-run-batch origin/master
```

3. If `.worktrees/plan-run-batch` exists:

```bash
cd .worktrees/plan-run-batch
git status --short
```

- If dirty: `BLOCKED:` and suggest `/plan-run clean-batch`.
- If clean: continue.

4. Sync batch worktree to latest master:

```bash
git fetch origin
git switch master || git switch -c master origin/master
git reset --hard origin/master
```

Only allowed when the batch worktree is clean.

5. Create the per-plan branch:

```bash
git switch -c auto/SHA-XX-<slug>
```

6. Baseline:

```bash
powershell -File scripts/test_fast.ps1
```

On baseline fail:

- set `phase: failed`
- do **not** delete batch worktree
- report `BLOCKED: baseline failed`

Write `active.md` with `worktree_mode: batch`, `batch_worktree: .worktrees/plan-run-batch`, `worktree: .worktrees/plan-run-batch`, `branch: auto/SHA-XX-<slug>`.

Solver touch: `PYTHONPATH=<worktree>/src` when plan targets `src/shapez2_factory/`.

Set `phase: worktree_ready`, `last_successful_phase: worktree_ready`.

All implementation edits happen only inside `.worktrees/plan-run-batch`.

#### Legacy dedicated worktree (in-progress runs only)

If `active.md` already records `worktree_mode: dedicated` with path `.worktrees/auto-SHA-XX-<slug>`, continue in that worktree — do not migrate to batch mid-run.

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
7. [Plan metadata at ship](#plan-metadata-lifecycle): if frontmatter still `planned`, set `status: in_progress` and [metadata-commit](#metadata-commit) on root. Append `claims.jsonl` event `shipped`.
8. Count open PRs on `master` ([babysit batch gate](#babysit-batch-gate-5-open-prs)). If **< 5**, report babysit deferred and suggest next plan — do **not** invoke babysit.

### Commit if needed (staging rules)

- Stage **only** files changed inside the active worktree for this plan.
- Stage **only** paths required by the selected plan scope.
- **Manual `ship`:** show `git status --short` before commit; **abort** if unrelated files are present.
- **`auto` ship:** emit `git status --short` in checkpoint; abort if files outside plan scope appear.

On push failure: set `failure_phase: pr-open`, record actual `remote_pushed` value, report recovery via `auto resume` or manual push.

Follow superpowers **`finishing-a-development-branch`** Option 2 only.

### After ship — prepare batch worktree for next plan

After PR is created:

1. Ensure branch was pushed and `pr_url` is recorded.
2. Ensure current branch has no uncommitted changes.
3. Do not delete the batch worktree.
4. Leave batch worktree available for the next plan.

Next plan may reuse:

```text
.worktrees/plan-run-batch
```

but must create a new branch:

```text
auto/SHA-YY-<slug>
```

For **legacy dedicated** runs (`worktree_mode: dedicated`), keep the dedicated worktree until merge/cleanup — do not apply batch reuse rules mid-run.

---

## `/plan-run babysit`

Batch PR triage — run only when [babysit batch gate](#babysit-batch-gate-5-open-prs) passes (**≥ 5** open PRs on `master`).

Primary cleanup path when PR pile hits batch gates: [partition](#batch-babysit-partition) → resolve duplicates → merge **passing** PRs → defer infra/failed without blocking batch.

### Preflight

1. `gh pr list --state open --base master --json number,url,headRefName,title,body,labels`
2. If count **< 5** → **defer** (see batch gate defer output). Do not triage.
3. If count **≥ 5** → proceed.
4. Linear MCP must be available for merge path — else `BLOCKED:` (babysit triage/fix without merge still allowed).
5. [Partition](#batch-babysit-partition) all open plan-run PRs; emit [batch babysit report](#batch-babysit-report).

Use Cursor **`babysit`** skill.

**Order:** duplicates first → **passing** PRs (lowest PR number first) → deferred/failed last. Do **not** start with `active.md` red PR if green plan-run PRs exist.

- Resolve merge conflicts preserving plan intent.
- Triage Bugbot / review — fix only valid in-scope issues.
- Fix CI failures in PR scope only; do not weaken CI/workflows.
- CI red outside PR diff → `infra-blocked` → defer; continue passing merges.

Read-only inspection (`gh pr view`, checks) is allowed even when root worktree is dirty.

**Merge only if** user explicitly says merge AND [merge gate](#merge-gate---merge-only) passes **per PR**. Passing PRs merge even when other plan-run PRs are deferred/duplicate.

### On merge (per PR)

After **each** successful `gh pr merge`:

1. Run [Linear merge completion](#linear-merge-completion) for that PR's `SHA-XX` (In Review → Done + summary comment). **Do not** merge the next PR until Linear step succeeds or is idempotent (already Done + comment).
2. Worktree cleanup when merged issue matches `active.md`:
   - **`worktree_mode: batch`:** do **not** remove `.worktrees/plan-run-batch`; suggest `/plan-run clean-batch` after batch round.
   - **`worktree_mode: dedicated`:** `git worktree remove <worktree>`; delete local branch when safe.
   - `active.md` → `status: achieved`, `phase: merged` only for the active issue.

When multiple PRs merge in one babysit session, emit [batch merge report](#batch-merge-report) + [batch babysit report](#batch-babysit-report). Suggest `/plan-run clean-batch` when batch worktree is on a merged branch.

If only deferred/duplicate remain → checkpoint ok (not global `failed`); suggest `/plan-run recover` or infra fix on master.

---

## `/plan-run batch-status`

Read-only.

Report:

- batch worktree path
- whether batch worktree exists
- current branch in batch worktree
- dirty status of batch worktree
- active.md issue/phase
- open plan-run PR count ([Batch PR gate](#batch-pr-gate))
- list of open plan-run PRs
- cleanup recommendation when count ≥ 5

Output:

```text
Batch Status
- Worktree: .worktrees/plan-run-batch
- Exists: yes|no
- Branch: <branch>
- Dirty: yes|no
- Active: SHA-XX phase=<phase>
- Open plan-run PRs: N

Open PRs
- #181 SHA-12 <state/checks>
- #182 SHA-18 <state/checks>

Next
- /plan-run babysit
- /plan-run clean-batch
- /plan-run run SHA-YY
```

---

## `/plan-run clean-batch`

Clean and resync the reusable batch worktree.

Safe only when:

- no uncommitted changes inside `.worktrees/plan-run-batch`
- current branch has been pushed or has no unique commits
- no active implementation phase is running (`active.md` `status` not `active`, or `phase` ≥ `pr-open`)

Steps:

1. Inspect:

```bash
cd .worktrees/plan-run-batch
git status --short
git branch --show-current
git log --oneline origin/master..HEAD
```

2. If dirty:

```text
BLOCKED: batch worktree dirty · next: commit/stash/inspect inside batch worktree
```

3. If clean and current branch has PR open or was pushed:

```bash
git fetch origin
git switch master || git switch -c master origin/master
git reset --hard origin/master
```

4. Do not delete remote branches.
5. Do not close PRs.
6. Do not delete local branch unless safely merged and user confirms.

Output:

```text
Batch clean complete
- Worktree: .worktrees/plan-run-batch
- Branch: master @ origin/master
- Open plan-run PRs: N
```

Update `active.md` `batch_last_cleaned_at` when present.

---

## `/plan-run status`

Read and report (never blocked by dirty root):

- `var/plan-run/active.md`
- `git worktree list` (`.worktrees/plan-run-batch`, legacy `.worktrees/auto-*`)
- batch worktree branch + dirty state when `worktree_mode: batch`
- open plan-run PR count vs [batch PR gate](#batch-pr-gate)
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
4. **Scan stale Linear In Review:** for merged/closed plan-run PRs (`gh pr list --state merged --limit 20`) and plans still `in_progress`, query Linear; if In Review → classify `stale-linear-in-review`; suggest [Linear merge completion](#linear-merge-completion).
5. **Scan duplicate cards:** same `linear_issue` with multiple open PRs or merged+open overlap → [duplicate-card](#duplicate-card-detection).
6. If `active.md` present (or reconstructed from step 2), verify:
   - worktree path exists (`git worktree list`)
   - branch exists locally/remotely
   - PR open if `pr_url` set (`gh pr view`)
   - Linear state if MCP available
7. Classify:

| Class | Meaning | Suggested next |
|-------|---------|----------------|
| `stale-linear-claim` | Linear In Progress; no active.md/worktree/PR | `/plan-run run SHA-XX` or Todo in Linear |
| `resumable` | worktree + branch OK; phase < merged | `/plan-run auto resume` |
| `active-pr-open` | active.md + worktree + open PR; CI pending or green | `/plan-run babysit` when ≥5 open PRs, else monitor |
| `active-pr-open-ci-red` | active.md + worktree + open PR; required CI failing | fix in worktree + push; `/plan-run babysit` when ≥5 open PRs |
| `stale-active-no-worktree` | active.md but worktree missing | `/plan-run clear` then `/plan-run run SHA-XX` or abandon |
| `stale-active-pr-open` | open PR exists but active.md/worktree incomplete or missing | reconstruct via PR scan; then `/plan-run babysit` when ≥5 open PRs |
| `stale-frontmatter-drift` | frontmatter `in_progress` but no runtime claim | metadata-commit revert or `/plan-run recover` |
| `stale-linear-in-review` | PR merged/closed but Linear still In Review; or plan still `in_progress` | [Linear merge completion](#linear-merge-completion) or manual Done + summary |
| `duplicate-card` | same `SHA-XX` multiple PRs; plan done + open PR; repeat claim | [Duplicate card resolution](#duplicate-card-resolution) |
| `infra-blocked` | CI red, failures outside PR diff (shared golden, etc.) | defer; `/plan-run babysit merge` passing PRs first |
| `manual-cleanup-required` | branch/PR/worktree mismatch | report paths; user decides |

**Classify PR-open runs:** when `active.md` + worktree + `pr_url` all verify, use `active-pr-open` or `active-pr-open-ci-red` (check `gh pr checks` / required CI). Reserve `stale-active-pr-open` for PR without complete session state.

Do not auto-clear or auto-delete anything.

---

## `/plan-run clear`

Set `active.md` `status: cleared`. Append `claims.jsonl` terminal event `cleared`. Does not remove worktree, branch, or PR. Does not revert `plans/**` frontmatter (may still read `planned` if ship metadata never ran).

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
| 0 | `preflight` | Dirty guard (fresh auto), mutex, [batch PR gate](#batch-pr-gate), Linear/GitHub scan | `BLOCKED:` |
| 1 | `picked` | [Selection algorithm](#selection-algorithm); queue-head `stale-linear-claim` may [auto-attach](#auto-stale-claim-attach) | `BLOCKED:` no eligible plan or attach blocked |
| 2 | `claimed` | Write `active.md` + `claims.jsonl`; runtime claim; Linear In Progress if needed; **no** `plans/**` edit | `BLOCKED:` |
| 3 | `worktree_ready` | Batch worktree setup + per-plan branch | remove branch only if no commits; do not delete batch worktree; `failed` |
| 4 | `implemented` | [Execute + validate](#4-execute) | `failed`; record side effects |
| 5 | `committed` | Commit plan scope; set `commit_sha` | `failed`; keep worktree |
| 6 | `pr-open` | [Ship steps](#steps); set `remote_pushed`, `pr_url` | `failed`; record push/PR state |
| 7 | `ci-green` | If open PRs on `master` **≥ 5**: [partition](#batch-babysit-partition) + babysit; merge passing PRs; defer infra/duplicate — **partial success ok**. If **< 5**: stop at `pr-open` (babysit deferred, not failed) | active issue `infra-blocked` → `deferred`, not global `failed` if passing merged |
| 8 | `merged` | **Only if `--merge`:** merge + [Linear merge completion](#linear-merge-completion) per PR | stop at `ci-green` |

**Fresh auto entry:** always run step 0 `preflight` first, then step 1 `picked` (which may auto-attach stale claim and continue through step 6 without re-prompt).

**Resume (normal):** enter at the phase **after** `last_successful_phase`. Skip step 0 unless resuming from `preflight` or after a guard failure. `auto resume` never re-picks unless `phase` is missing.

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

### Auto stale-claim attach

For `/plan-run auto` and `/plan-run` headless auto, a queue-head `stale-linear-claim` may be attached automatically.

A `stale-linear-claim` means **all** true:

- Linear issue is In Progress / started
- plan frontmatter is `planned` or `in_progress`
- no conflicting active run — either no `active.md`, or [mutex exception](#active-run-mutex) allows replacing a babysit-deferred `pr-open` session
- no legacy `.worktrees/auto-<issue>-*` or batch branch on `auto/<issue>-*` for that issue with unpushed work
- no open PR for that issue
- [Runaway PR guard](#runaway-pr-guard) + [dirty root guard](#dirty-main-worktree-guard) pass (fresh auto — operator must clear dirty root; no auto PR)
- [batch PR gate](#batch-pr-gate) passes (open plan-run PRs **< 5**)

When all conditions pass, auto continues **without asking**:

1. Create or update `active.md`.
2. Set `mode: auto`.
3. Set `phase: claimed`, `status_shadow: in_progress`.
4. Append `claims.jsonl` event `claimed`.
5. Record `linear_current_state: In Progress`.
6. Do **not** move Linear again if already In Progress.
7. Continue through batch worktree setup, per-plan branch, implement, validate, commit, push, and PR via the normal auto phase machine.

Do **not** skip stale claims silently to a lower-priority plan.

Do **not** auto-attach when:

- open plan-run PR count is **5 or more**
- another active run exists in a blocking phase (`claimed` through `implemented`) without mutex exception
- an open PR already exists for the same issue
- batch worktree or legacy dedicated worktree for that issue is dirty
- Linear state is not In Progress
- plan has `Human Review Required: yes`
- plan has `hermes: required` and Hermes is unavailable

Failure output:

```text
BLOCKED: stale-linear-claim attach failed · tried: preflight + state scan · next: /plan-run recover
```

### Headless auto stale-claim output

When `/plan-run` alone routes to headless auto and auto-attaches a stale claim:

```text
Routing
/plan-run alone
→ headless auto
→ open plan-run PRs: N / 5
→ queue head: SHA-XX stale-linear-claim
→ auto-attach allowed
→ continue

[plan-run auto] phase=preflight ok
[plan-run auto] phase=claimed issue=SHA-XX ok
```

When auto-attach is blocked:

```text
BLOCKED: stale-linear-claim
Issue: SHA-XX
Reason: <dirty root | open PR exists | batch gate >= 5 | active run exists | hermes required>

Next
- /plan-run recover
- /plan-run run SHA-XX
- /plan-run batch-status
```

### Auto-specific rules

1. **No re-prompt** between phases.
2. **Stale-claim auto-attach** — queue-head stale claims attach automatically when [preconditions](#auto-stale-claim-attach) pass; do not require `/plan-run run SHA-XX` first.
3. **Commit before ship** — always phase `committed`.
4. **Human Review Required: yes** — exclude at pick; never auto-run or auto-attach.
5. **Validation retry** — one in-scope fix loop per command; then `failed`.
6. **Babysit batch gate** — do not start `ci-green` / babysit until **≥ 5** open PRs on `master`; stop at `pr-open` with defer report (not `failed`).
7. **Batch PR gate** — headless `/plan-run` and `/plan-run auto` **BLOCKED** when open plan-run PRs **≥ 5**; explicit `auto SHA-XX` allowed with warning.
8. **Babysit rounds** — max **10** rounds once babysit batch gate passes; then `BLOCKED: babysit round limit`.
9. **Hermes** — first eligible plan `hermes: required` without Hermes → `BLOCKED:` (unless user skipped Hermes-blocked plans).
10. **Linear** — without MCP, `BLOCKED:` unless `--allow-linear-offline`; offline auto stops at `pr-open` or deferred `ci-green` (no merge).
11. **Flag conflict** — `--allow-linear-offline` + `--merge` → `BLOCKED:` before start.
12. **Merge** — never without `--merge` and [merge gate](#merge-gate---merge-only); each merged PR → [Linear merge completion](#linear-merge-completion).
13. **Linear on batch merge** — babysit with ≥5 PRs must Done + **Korean** summary every merged issue, not only `active.md`.
14. **Passing-first** — duplicates resolved, then green PRs merge; infra-blocked/deferred must not block passing merges.
15. **Duplicate cards** — [duplicate-card detection](#duplicate-card-detection) + [resolution](#duplicate-card-resolution); never pick/run duplicate when canonical exists.
16. **Long plans** — stop at `failed` or complete validation; continue via `auto resume` after `/goal`.

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

Manual: `/plan-run run SHA-6` → `/goal` → `/plan-run ship` → (repeat until ≥5 open PRs) → `/plan-run babysit merge` (PR cleanup + Linear Done + summary per PR).

---

## Skills map

| Phase | Skill |
|-------|--------|
| Root clean before run/auto | **`clean-root`** |
| Queue workflow | **`plan-run`** |
| Chained execution | **`plan-run auto`** |
| Stale lock inspection | **`plan-run recover`** |
| Batch worktree hygiene | **`plan-run batch-status`**, **`plan-run clean-batch`** |
| Harness checklist | `shapez2-workflow` |
| Worktree | superpowers `using-git-worktrees` |
| Implement | superpowers `executing-plans` |
| Domain grill | `grill-me-shapez2` |
| Commit/push | `git-workflow` |
| PR completion | superpowers `finishing-a-development-branch` |
| PR batch triage (≥5 open PRs) | `babysit` |
| Linear In Review → Done + 한국어 summary on merge | [Linear merge completion](#linear-merge-completion) · [comment language](#linear-comment-language) |
| Duplicate / passing-first batch | [Batch babysit partition](#batch-babysit-partition) |
| Pre-merge | `quality-check` |

---

## Failure report

```text
BLOCKED: <what> · tried: <steps> · next: <one recovery command>
```

Keep worktree after commit/push unless user asks to remove. For batch mode, never delete `.worktrees/plan-run-batch` — use `/plan-run clean-batch` instead.
