---
name: clean-repo-commit
description: >-
  Clean the repository by reviewing, grouping, validating, and committing
  completed necessary work without hiding dirty state via delete, stash, or
  reset. Use when the user asks to clean up the repo, commit completed work,
  make the working tree clean, fix dirty root from completed local work,
  prepare a branch for PR without leaving dirty files, or commit necessary
  work that has already been done. Do not use for throwing away changes,
  stash-based workflows, branch surgery, force reset, conflict recovery, or
  deleting files merely to make Git clean.
disable-model-invocation: true
---

# clean-repo-commit

Purpose: Clean the repository by reviewing, grouping, validating, and committing completed necessary work. This skill must not hide dirty state by deleting files, stashing work, resetting changes, or opening a PR while the worktree is still dirty.

The intended outcome is:

```text
necessary completed work → committed
unnecessary local noise → explicitly reported
ambiguous work → not touched, reported, and blocked if still dirty
```

## Trigger

Use this skill when the user asks to:

* clean up the repo
* commit completed work
* make the working tree clean
* fix dirty root caused by completed local work
* prepare a branch for PR without leaving dirty files
* commit necessary work that has already been done

Do not use this skill for:

* throwing away changes
* stash-based workflows
* branch surgery
* force reset
* conflict recovery
* deleting files merely to make Git clean

## Core Rule

A clean repo is achieved by committing reviewed, necessary work.

Do not make the repo appear clean by discarding, hiding, stashing, or deleting changes.

## Hard Prohibitions

Do not run:

```bash
git reset --hard
git clean -fd
git clean -fdx
git checkout -- .
git restore .
git restore --staged .
git stash
git stash push
rm -rf <path>
del /s <path>
```

Do not remove, discard, hide, or stash changes unless the user explicitly asks for that exact action.

Do not open or update a PR while the worktree contains unreviewed dirty state.

Do not claim the repo is clean without running:

```bash
git status --short
```

## Protected Branch Guard

Treat these as protected branch names unless project rules say otherwise:

```text
main
master
release
release/*
production
prod
stable
deploy
```

If currently on a protected branch, do not commit directly unless the user explicitly requested committing on that branch.

Run:

```bash
git branch --show-current
```

If the branch is protected, stop and report the branch.

## Preflight

Run:

```bash
git status --short
git branch --show-current
git log --oneline -5
```

Stop immediately if any of these are true:

* not inside a Git repository
* detached HEAD
* merge conflict
* rebase conflict
* cherry-pick conflict
* protected branch without explicit user approval

Detect conflict state with:

```bash
git status
git diff --name-only --diff-filter=U
```

## Dirty State Inventory

Run:

```bash
git status --short
git diff --stat
git diff --name-only
git ls-files --others --exclude-standard
```

Classify every dirty path before staging anything.

## Classification Rules

### 1. Necessary completed work

Definition: A source, test, config, documentation, migration, or project artifact change that directly belongs to the completed task.

Examples:

```text
M  src/replay/effective_cell_wire.py
M  tests/unit/replay/test_effective_cell_wire.py
M  docs/agent-workflows/graphify-routine.md
A  .cursor/skills/clean-repo-commit/SKILL.md
M  pyproject.toml
```

Action:

* Review diff.
* Validate.
* Stage explicitly.
* Commit.

### 2. Required generated artifact

Definition: A generated or machine-updated file that is required for the committed work to reproduce, build, test, or deploy correctly.

Examples:

```text
M  uv.lock
M  package-lock.json
M  pnpm-lock.yaml
M  schema.graphql
M  prisma/migrations/<timestamp>_<name>/migration.sql
M  alembic/versions/<revision>.py
M  snapshots/api_contract.snap
```

Required artifact heuristics:

Commit it only when at least one is true:

* project normally commits this file type
* source change updates dependency or schema state
* tests fail without it
* docs or project policy says it is canonical
* file is already tracked and changed by an accepted generator command

Do not commit it when:

* it is untracked and no policy says it belongs in Git
* it is a local cache
* it is build output not normally committed
* it contains machine-specific absolute paths
* it contains timestamps only and no semantic change

Action:

* Inspect diff.
* Confirm it is expected.
* Validate if practical.
* Stage explicitly.

### 3. Local noise

Definition: Local-only files that should not be committed and do not represent completed work.

Examples:

```text
?? .DS_Store
?? Thumbs.db
?? .pytest_cache/
?? .mypy_cache/
?? node_modules/
?? .venv/
?? logs/debug.log
?? tmp/
?? scratch.txt
?? graphify-out/
?? playwright-report/
?? test-results/
```

Action:

* Do not delete.
* Do not stash.
* Do not stage.
* Report as local noise.
* Consider `.gitignore` only if the file pattern is clearly recurring project noise.

### 4. Ambiguous dirty state

Definition: A file that could be user work, unrelated work, generated output, or accidental modification, and cannot be safely classified from path and diff.

Examples:

```text
?? notes.md
?? output/manual_patch.json
M  src/large_unrelated_module.py
M  docs/random_design.md
?? export.zip
?? screenshot.png
D  unknown_file.py
```

Action:

* Do not stage.
* Do not delete.
* Do not restore.
* Stop if ambiguity blocks clean status.
* Report exact file and why it is ambiguous.

### 5. Sensitive files

Definition: Files or diffs that may contain secrets, credentials, private keys, tokens, personal data, or deployment credentials.

Examples:

```text
?? .env
?? .env.local
?? id_rsa
?? *.pem
?? service-account.json
M  settings.py
M  config/secrets.yml
```

Also scan diffs for strings like:

```text
API_KEY
SECRET
TOKEN
PASSWORD
PRIVATE KEY
AWS_ACCESS_KEY
OPENAI_API_KEY
GITHUB_TOKEN
```

Action:

* Do not stage.
* Do not commit.
* Stop and report.
* Do not print secret values in the final report.

## Deleted File Handling

`git status --short` may show deleted files:

```text
D  path/to/file.py
```

Deleted files are not automatically necessary work.

Classify deletions separately:

| Deletion type        | Heuristic                                                                            | Action                        |
| -------------------- | ------------------------------------------------------------------------------------ | ----------------------------- |
| Intentional deletion | File removal matches task, docs, tests, import cleanup, or explicit user request     | Stage deletion explicitly     |
| Generated deletion   | Removed generated artifact is known obsolete and project normally tracks its removal | Stage only after validation   |
| Suspicious deletion  | File is unrelated, important, or not explained by task                               | Do not stage; stop and report |
| Unknown deletion     | No clear reason for removal                                                          | Do not stage; stop and report |

Review deletion context with:

```bash
git diff -- <path>
git log --oneline -- <path>
git grep "<deleted symbol or filename>"
```

To stage an intentional already-deleted tracked file:

```bash
git add -u -- <path>
```

Do not run broad restore commands to undo deletions. If a deletion is suspicious, stop and report it.

## Diff Review

For tracked files:

```bash
git diff -- <path>
```

For deleted files:

```bash
git diff -- <path>
git log --oneline -- <path>
```

For untracked text files:

```bash
sed -n '1,160p' <path>
```

On Windows PowerShell:

```powershell
Get-Content <path> -TotalCount 160
```

For untracked binary files, do not stage unless the path and project policy clearly identify it as a required artifact.

## Staging Policy

Stage explicitly.

Allowed:

```bash
git add -- <file>
git add -u -- <deleted-or-modified-file>
git add -- <dir>/<specific-file>
```

Disallowed:

```bash
git add .
git add -A
git add -u
```

Exception: path-scoped directory staging is allowed only when every file under that directory has already been listed, classified, and reviewed.

Allowed example:

```bash
git add -- .cursor/skills/clean-repo-commit/SKILL.md
```

Risky example, avoid unless every file under the directory was reviewed:

```bash
git add -- docs/
```

Before committing, always run:

```bash
git diff --cached --stat
git diff --cached
```

The staged diff must contain only intended work.

## Validation Policy

Run the smallest meaningful validation available.

### Validation discovery order

Check for documented commands in:

```text
README.md
AGENTS.md
CONTRIBUTING.md
Makefile
pyproject.toml
package.json
tox.ini
noxfile.py
justfile
Taskfile.yml
```

### Validation ladder

Use the first applicable tier, then expand only if needed.

| Situation                         | Validation                                                   |
| --------------------------------- | ------------------------------------------------------------ |
| Docs-only change                  | markdown lint if available; otherwise no test required       |
| Skill/prompt/workflow-only change | project governance check if available; otherwise diff review |
| Python source change              | targeted pytest, then mypy/ruff if configured                |
| JS/TS source change               | targeted test, then typecheck/lint if configured             |
| Config/dependency change          | relevant build/import check                                  |
| Migration/schema change           | migration/schema validation command if available             |
| No obvious target                 | run syntax/import/lightweight checks before full suite       |
| No documented validation          | run `git diff --check` and report validation gap             |

Always run:

```bash
git diff --check
```

unless the project explicitly uses whitespace-sensitive generated files where this would be misleading.

Do not run the full suite by default. Use full suite only when:

* targeted validation is unavailable
* the change affects broad shared contracts
* project policy requires it
* prior targeted validation indicates wider risk

If validation fails:

| Failure cause             | Action                                                                |
| ------------------------- | --------------------------------------------------------------------- |
| Caused by current diff    | Fix before commit                                                     |
| Existing baseline failure | Commit only if current diff is valid; report baseline failure clearly |
| Environment/tool missing  | Report exact missing tool; use next best validation                   |
| No validation available   | Report `validation gap`                                               |

## `.gitignore` Policy

Do not edit `.gitignore` automatically for every local noise file.

Add or update `.gitignore` only when all are true:

* the file pattern is recurring local/generated noise
* the pattern is project-wide, not user-specific
* the ignore rule will not hide source, tests, docs, fixtures, lockfiles, migrations, or required artifacts
* the `.gitignore` change itself is reviewed and committed as necessary work

Examples usually safe to ignore:

```text
.pytest_cache/
.mypy_cache/
.ruff_cache/
playwright-report/
test-results/
.DS_Store
Thumbs.db
```

Examples usually unsafe to ignore without explicit project policy:

```text
uv.lock
package-lock.json
pnpm-lock.yaml
schema.graphql
migrations/
dist/
build/
fixtures/
snapshots/
```

## Commit Grouping

Prefer one commit when all changes belong to one completed task.

Use multiple commits when there are separate scopes:

```text
implementation
tests
docs
generated contract artifact
workflow/skill update
```

Do not mix unrelated work into one commit.

Commit message rules:

* Use imperative mood.
* Use a narrow scope.
* Describe the contract or behavior changed.
* Avoid vague messages like `cleanup`, `fix stuff`, or `changes`.

Examples:

```bash
git commit -m "chore(agent): add clean repo commit skill"
git commit -m "fix(replay): stabilize effective cell wire typing"
git commit -m "docs(workflow): clarify dirty root handling"
```

## Commit Loop

Repeat until no necessary completed work remains unstaged.

Loop:

```text
inventory
classify
review
validate
stage explicitly
review staged diff
commit
status check
```

After every commit:

```bash
git status --short
git log --oneline -3
```

If more necessary work remains, repeat.

If only local noise remains, report it.

If ambiguous or sensitive files remain, stop and report.

## PR Gate

A PR may be opened or updated only after the commit loop finishes and remaining dirty state is either empty or explicitly classified as untracked local noise.

Never open a PR with ambiguous, sensitive, or necessary uncommitted work remaining.

## Stop Conditions

Stop immediately if any of these are found:

* secrets or credentials in diff
* merge/rebase/cherry-pick conflict
* detached HEAD
* protected branch without explicit approval
* suspicious deleted file
* ambiguous untracked source file
* unknown binary file
* large generated artifact without clear purpose
* validation failure caused by current diff
* staged content does not match intended work
* repo cannot be made clean without deleting, stashing, resetting, or restoring files

## Final Report Format

Use this exact structure.

```text
Final Report

Branch:
- <branch>

Committed:
- <commit sha> <message>
- <commit sha> <message>

Validation:
- <command> → <result>
- <command> → <result>

Reviewed and intentionally excluded:
- <path> — <classification> — <reason>

Remaining dirty state:
- clean
```

If dirty state remains:

```text
Remaining dirty state:
- <path> — <classification> — <reason not touched>
```

If blocked:

```text
BLOCKED

Reason:
- <specific reason>

Reviewed:
- <path> — <classification> — <finding>

Remaining dirty state:
- <path> — <classification> — <reason not touched>

Next safe action:
- <specific next step>
```

Do not omit the remaining dirty state section.

## Success Criteria

This skill succeeds only when:

* necessary completed work is committed
* no destructive cleanup was used
* no stash was created
* no unrelated dirty state was hidden
* deleted files were explicitly reviewed before staging
* staged files were explicit and reviewed
* validation was run or a validation gap was reported
* final `git status --short` is clean, or remaining dirty files are classified and reported
* no PR is opened from unreviewed dirty state

## Related skills

| Skill | When |
|-------|------|
| `clean-root` | Stash-based root prep before `/plan-run`; never substitutes for commit-first cleanup |
| `ops-recovery` | Git/worktree recovery, not commit review |

Do not stack `clean-repo-commit` with `clean-root` on the same turn.
