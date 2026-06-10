# LOOP_ISSUE — Agent Work Loop Automation

**Role:** Automation Architect  
**Status:** Spec / implementation backlog (not yet implemented)  
**Trigger model:** Human-triggered automation — not a fully autonomous daemon

> Cursor automation: paste sections below as implementation tasks.  
> Do **not** build a daemon first — person starts the loop; risky/ambiguous changes stop and report.

---

## Repo context

| Item | Value |
|------|-------|
| Repo | `shapez2Factory` (Python/Django) |
| Canonical validation | `AGENTS.md` § Validation |
| Linear team | **Shapez2Factory** (`team_id: 3e7df740-a09e-4fa1-bc8c-43d4bbb47ddb`) |
| Linear project | **shapez2factory** (create in Linear if missing at implementation time) |
| Linear API key | env `LINEAR_API_KEY` — never hardcode |

**Existing Linear team labels (2026-06-09):** `auto:impl-blocked`, `auto:verify-done`, `auto:research-done`, `auto:spec-brainstorming` only.  
Phase 2 requires `bug`, `feature`, `ui`, `docs`, `test`, `infra`, `refactor`, `performance`, `security`, `database`, `question`, `blocked`, `risk`, `automation`, `agent-loop` — create manually or set `create_missing_labels: true` per repo policy.

---

## Goal

Turn `AGENTS.md` + `.cursor/rules` AI work loop into runnable **Agent Loop Automation**.

```text
요구사항 확인
→ 구현
→ 검증 실행
→ 실패 분석
→ 안전한 수정
→ 재검증
→ 문서/계약 대조
→ 증거 보고
→ 완료 또는 사람 호출
```

**Output principle (Phase 2):** Unresolved findings → **individual Linear issue cards** on team **Shapez2Factory**, project **shapez2factory**. Final markdown report = **Linear issue index only**.

---

# Phase 1 — Loop skeleton + validation report

## 1. File structure

```text
.agent-loop/
  config.yaml              # loop + validation + linear settings
  state.json               # latest run state (generated)
  reports/                 # execution reports (generated)
  logs/                    # validation logs (generated)

scripts/
  agent_loop.ps1           # Windows entrypoint
  agent_loop.py            # orchestrator (no external LLM call)

.cursor/rules/
  agent-loop-automation.mdc  # thin router (<= 75 lines)
```

Merge with existing paths — do not duplicate.

## 2. `.agent-loop/config.yaml`

Use repo-canonical validation (`AGENTS.md` § Validation). **Not** npm defaults.

```yaml
version: 1

loop:
  max_iterations: 5
  stop_on_first_hard_gate_failure: false
  require_final_report: true
  require_clean_worktree_before_start: false

scope:
  allow_auto_fix:
    - lint
    - format
    - typecheck
    - obvious_test_failure
    - missing_test_for_changed_behavior
    - simple_doc_drift
    - import_cleanup
    - naming_cleanup

  require_human_review:
    - database_schema_change
    - data_loss_migration
    - auth_policy_change
    - permission_change
    - payment_logic
    - security_sensitive_change
    - secret_or_token_change
    - product_requirement_change
    - feature_scope_expansion
    - large_refactor
    - architecture_boundary_change
    - ux_intent_change

validation:
  commands:
    - name: django_check
      command: "python manage.py check"
      required: true

    - name: test_fast
      command: "powershell -File scripts/test_fast.ps1"
      required: true

    - name: ruff
      command: "ruff check ."
      required: true

    - name: mypy
      command: "mypy django_apps config src"
      required: true

    - name: black
      command: "black --check ."
      required: true

report:
  include:
    - changed_files
    - validation_commands
    - validation_results
    - failure_analysis
    - fixes_applied
    - contract_check
    - risks
    - human_review_items
```

**Rules:**

- Missing/unavailable commands → `skipped: command not available`; do **not** crash.
- `agent_loop.py` loads commands from `config.yaml`, not hardcoded npm.

## 3. `scripts/agent_loop.ps1`

```powershell
param(
    [string]$Task = "",
    [int]$MaxIterations = 5
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $RepoRoot

Write-Host "Agent Loop Automation"
Write-Host "Repo: $RepoRoot"

if ($Task -eq "") {
    Write-Host "ERROR: Missing task description."
    Write-Host "Usage:"
    Write-Host "  ./scripts/agent_loop.ps1 -Task 'Implement X and validate against spec'"
    exit 1
}

python ./scripts/agent_loop.py `
    --task "$Task" `
    --max-iterations $MaxIterations
```

## 4. `scripts/agent_loop.py` — minimum behavior

Orchestrator only — **does not call an LLM**. Manages state, validation, findings, reports, Linear issue creation (Phase 2) for Cursor/agent to follow.

1. Load `.agent-loop/config.yaml`
2. Persist task input
3. Run iterations (up to `max_iterations`)
4. Run validation commands; save logs under `.agent-loop/logs/`
5. Classify failures; record hard-gate results
6. Detect human-review boundaries from changed paths / config
7. Build findings (Phase 2)
8. Create Linear issues for unresolved findings (Phase 2)
9. Write final markdown report under `.agent-loop/reports/`
10. Update `.agent-loop/state.json`

### Skeleton

```python
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOOP_DIR = ROOT / ".agent-loop"
REPORT_DIR = LOOP_DIR / "reports"
LOG_DIR = LOOP_DIR / "logs"
STATE_FILE = LOOP_DIR / "state.json"


@dataclass
class ValidationResult:
    name: str
    command: str
    exit_code: int | None
    status: str
    log_file: str | None


def run_command(name: str, command: str) -> ValidationResult:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{name}.log"

    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        log_path.write_text(completed.stdout or "", encoding="utf-8")

        return ValidationResult(
            name=name,
            command=command,
            exit_code=completed.returncode,
            status="passed" if completed.returncode == 0 else "failed",
            log_file=str(log_path.relative_to(ROOT)),
        )

    except FileNotFoundError:
        return ValidationResult(
            name=name,
            command=command,
            exit_code=None,
            status="skipped_command_not_found",
            log_file=None,
        )


def get_changed_files() -> list[str]:
    completed = subprocess.run(
        "git status --short",
        cwd=ROOT,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def write_state(state: dict) -> None:
    LOOP_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def write_report(task: str, results: list[ValidationResult]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = REPORT_DIR / f"agent-loop-report-{timestamp}.md"
    changed_files = get_changed_files()

    lines = [
        "# Agent Loop Report",
        "",
        f"- Time: {timestamp}",
        f"- Task: {task}",
        "",
        "## Changed Files",
        "",
    ]
    if changed_files:
        lines.extend(f"- `{item}`" for item in changed_files)
    else:
        lines.append("- No changed files detected.")

    lines.extend(["", "## Validation Results", ""])
    for result in results:
        lines.extend([
            f"### {result.name}",
            "",
            f"- Command: `{result.command}`",
            f"- Status: `{result.status}`",
            f"- Exit code: `{result.exit_code}`",
            f"- Log: `{result.log_file}`",
            "",
        ])

    failed = [r for r in results if r.status == "failed"]
    lines.extend(["## Loop Decision", ""])
    if failed:
        lines.extend([
            "Status: partial",
            "",
            "Failed validation exists. Do not claim completion until resolved or explicitly accepted.",
            "",
            "## Required Follow-up",
            "",
        ])
        lines.extend(f"- Inspect `{r.log_file}` for `{r.name}` failure." for r in failed)
    else:
        lines.extend([
            "Status: validation-passed",
            "",
            "All configured validation commands passed or were skipped (command unavailable).",
        ])

    lines.extend([
        "",
        "## Human Review Boundary",
        "",
        "Confirm manually if task involved database schema, migrations, auth, permissions, security, payment, product scope, architecture, or UX intent changes.",
        "",
    ])
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def load_validation_commands() -> list[tuple[str, str]]:
    # TODO Phase 1: load from .agent-loop/config.yaml
    return [
        ("django_check", "python manage.py check"),
        ("test_fast", "powershell -File scripts/test_fast.ps1"),
        ("ruff", "ruff check ."),
        ("mypy", "mypy django_apps config src"),
        ("black", "black --check ."),
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--max-iterations", type=int, default=5)
    args = parser.parse_args()

    results: list[ValidationResult] = []
    state = {
        "task": args.task,
        "started_at": datetime.now().isoformat(),
        "status": "running",
        "max_iterations": args.max_iterations,
    }
    write_state(state)

    for name, command in load_validation_commands():
        results.append(run_command(name, command))

    report_path = write_report(args.task, results)
    state.update({
        "status": "completed_with_failures" if any(r.status == "failed" for r in results) else "completed",
        "finished_at": datetime.now().isoformat(),
        "report": str(report_path.relative_to(ROOT)),
        "results": [asdict(r) for r in results],
    })
    write_state(state)
    print(f"Agent loop report written: {report_path}")
    return 1 if any(r.status == "failed" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**`run_command` rules:** never log `LINEAR_API_KEY` or other secrets.

## 5. `.cursor/rules/agent-loop-automation.mdc`

Thin router (`alwaysApply: true`, ≤ 75 lines). Detail in `docs/agent-workflows/agent-loop-automation.md` if line limit exceeded.

```md
---
description: Use the agent loop automation for non-trivial implementation tasks.
alwaysApply: true
---

# Agent Loop Automation Rule

For non-trivial implementation work, operate as a loop, not a one-shot editor.

## Required Loop

1. Read relevant docs/spec/task files.
2. Implement requested scope only.
3. Run applicable validation.
4. Analyze failures.
5. Apply safe fixes.
6. Re-run validation.
7. Check against docs/spec/task.
8. Produce evidence report (+ Linear issues when Phase 2 enabled).

## Entry Point

`scripts/agent_loop.ps1`, `scripts/agent_loop.py`, `.agent-loop/`  
Reports: `.agent-loop/reports/`

## Safe Fixes

lint, format, type errors, obvious test failures, missing tests for changed behavior, simple doc drift, import/naming cleanup.

## Stop Before Changing

DB schema, data-loss migrations, auth, permissions, payment, security-sensitive code, secrets, product scope, large refactors, architecture boundaries, UX intent.

## Completion Claim

Only with changed files, validation commands/results, failures, risks, human-review items, and (Phase 2) Linear issue index.
```

## 6. `AGENTS.md` addition

Add **Agent Loop Automation** (keep file ≤ 75 lines — link to `docs/agent-workflows/agent-loop-automation.md` if needed):

```md
## Agent Loop Automation

For non-trivial work, use repository loop automation instead of a single prompt-response cycle.

Paths: `.agent-loop/`, `scripts/agent_loop.ps1`, `scripts/agent_loop.py`

Enforces: requirement re-check, scoped implementation, validation, failure analysis, safe auto-fix, re-validation, evidence report, human escalation.

Run: `./scripts/agent_loop.ps1 -Task "Implement the requested feature and validate against the relevant spec"`

Completion: not complete merely because code was edited. Report `partial` or `blocked` when validation fails.
```

## Phase 1 acceptance criteria

- [ ] `.agent-loop/config.yaml` with repo validation commands
- [ ] `scripts/agent_loop.ps1`
- [ ] `scripts/agent_loop.py` (loads `config.yaml`)
- [ ] `.cursor/rules/agent-loop-automation.mdc`
- [ ] `AGENTS.md` references loop (within governance limits)
- [ ] `./scripts/agent_loop.ps1 -Task "Smoke test the agent loop automation"` runs on Windows
- [ ] Report under `.agent-loop/reports/agent-loop-report-*.md`
- [ ] Failed validations visible; missing commands → skipped, not crash

## Phase 1 non-goals

- GitHub PR auto-merge / CI auto-push
- DB migration auto-fix
- auth/security/payment auto-change
- External LLM API / autonomous daemon / file watcher
- Cursor-external MCP/ACP runtime

---

# Phase 2 — Linear issue cards (report = index only)

Reference: [Linear API and Webhooks](https://linear.app/docs/api-and-webhooks)

## Goal change

| Before | After |
|--------|-------|
| One long report as follow-up source | One **Linear issue per actionable finding** |
| Human re-triages report | Report = index + links to Linear cards |

**Target:** team **Shapez2Factory**, project **shapez2factory**.

## `.agent-loop/config.yaml` — add `linear` section

```yaml
linear:
  enabled: true
  create_issues: true
  dry_run: false

  api_key_env: "LINEAR_API_KEY"   # never hardcode

  team_key: "Shapez2Factory"      # Linear team name/key
  team_id: "3e7df740-a09e-4fa1-bc8c-43d4bbb47ddb"
  project_name: "shapez2factory"  # attach issues to this project

  issue_source_label: "agent-loop"
  create_missing_labels: false    # true only if repo policy allows auto-create

  labels:
    bug: "bug"
    feature: "feature"
    ui: "ui"
    docs: "docs"
    test: "test"
    infra: "infra"
    refactor: "refactor"
    performance: "performance"
    security: "security"
    database: "database"
    question: "question"
    blocked: "blocked"
    risk: "risk"
    automation: "automation"
```

**Token / label rules:**

- No `LINEAR_API_KEY` → `linear_skipped_missing_token`; loop continues
- Missing label → `missing_label`; no auto-create unless `create_missing_labels: true`
- API errors → `linear_issue_creation_failed` finding; loop does not hard-fail
- Idempotent: same fingerprint must not create duplicate open issues

## Finding model

```python
@dataclass
class LoopFinding:
    title: str
    category: str       # bug|feature|ui|docs|test|infra|refactor|performance|security|database|question|blocked|risk|automation
    severity: str       # critical|high|medium|low|info
    summary: str
    evidence: list[str]
    suggested_action: str
    source: str
    labels: list[str]
    blocking: bool
```

## One Linear issue each

- Failed validation
- Unresolved bug
- Missing test scope
- docs/spec/task mismatch
- UI/UX confirmation
- Performance regression
- security/auth/permission risk
- DB/schema/migration risk
- blocked/question needing human judgment

## Not a Linear issue

- Auto-fixed lint/format now passing
- Raw logs
- Duplicate findings
- Unsupported speculation

Auto-fixed → report section **Resolved Automatically** only.

## Label mapping

| Category | Required label |
|----------|----------------|
| bug | bug |
| feature | feature |
| ui | ui |
| docs | docs |
| test | test |
| infra | infra |
| refactor | refactor |
| performance | performance |
| security | security |
| database | database |
| question | question |
| blocked | blocked |
| risk | risk |
| automation | automation |

Extra: validation fail → `bug` and/or `test`; CI/script → `infra`; user-visible → `ui`; DB → `database`; auth/token → `security`; human judgment → `question`/`blocked`; loop tooling → `automation`. Always add `agent-loop` via `issue_source_label`.

## Issue title

```text
[category] concise problem statement
```

Example: `[bug] mypy fails in django_apps shapez2 preview hook`

## Issue description template

```md
## Summary

Brief problem summary.

## Evidence

- Command:
- Log:
- Files:
- Spec/task:

## Suggested Action

Concrete next step.

## Severity

critical | high | medium | low | info

## Blocking

yes | no

## Source

Generated by Agent Loop Automation.

## Run Context

- Loop report:
- Iteration:
- Timestamp:

agent-loop-fingerprint: <hash>
```

## Idempotency

**Fingerprint:** `category + title + source + related file + failed command`

1. Search open Linear issues (team Shapez2Factory) for matching fingerprint in description
2. Found → link as `reused`
3. Not found → `created`

## `agent_loop.py` — Linear functions

```text
load_linear_config()
resolve_linear_team()          # Shapez2Factory
resolve_linear_project()       # shapez2factory
resolve_linear_labels()
find_existing_issue_by_fingerprint()
create_linear_issue()
create_issues_for_findings()
```

## Final report format (Phase 2)

```md
# Agent Loop Report

## Status

complete | partial | blocked

## Summary

- Changed files:
- Validation:
- Findings:
- Linear issues created:
- Linear issues reused:
- Linear issue creation failures:

## Linear Issues

| Category | Severity | Status | Linear Issue | Title |
|---|---|---|---|---|
| bug | high | created | SHA-123 | [bug] mypy fails in ... |

## Resolved Automatically

- ...

## Not Uploaded to Linear

Items intentionally not issue-worthy.

## Risks

- ...

## Human Review Required

- ...
```

**Invariant:** unresolved work lives in Linear (team Shapez2Factory / project shapez2factory), not in report body.

## Cursor rule addition (Phase 2)

Add to `agent-loop-automation.mdc` or linked doc:

```md
## Linear Issue Output Rule

Unresolved findings → individual Linear issue cards on team Shapez2Factory, project shapez2factory.

One issue per: failed validation, missing test, unresolved bug, UI/UX issue, docs/spec mismatch, performance issue, security risk, database/migration risk, blocked human decision.

Labels: bug, feature, ui, docs, test, infra, refactor, performance, security, database, question, blocked, risk, automation, agent-loop.

Final markdown report summarizes Linear issues and links only. Linear is the source of follow-up work.
```

## Phase 2 acceptance criteria

- [ ] `linear` section in `config.yaml` (Shapez2Factory + shapez2factory)
- [ ] `LoopFinding` + validation-failure → finding
- [ ] Category/severity/label classification
- [ ] Linear client + label resolution
- [ ] Fingerprint deduplication
- [ ] Linear failures in report
- [ ] Report = Linear issue index
- [ ] Cursor rule updated

## Phase 2 non-goals

- Linear auto-close / auto-assign
- Forced workflow changes / bulk label creation
- PR auto-merge / unlimited CI push
- Auto-fix security/database / human-judgment issues

---

## Implementation order

1. Phase 1: config, ps1, py, cursor rule, AGENTS.md pointer
2. Smoke: `./scripts/agent_loop.ps1 -Task "Smoke test the agent loop automation"`
3. Bootstrap Linear labels on team Shapez2Factory (or enable `create_missing_labels`)
4. Create Linear project `shapez2factory` if absent
5. Phase 2: findings, Linear client, fingerprint, report as index
6. Runbook in `docs/agent-workflows/agent-loop-automation.md` if routers exceed 75 lines

---

## Final report template (implementing agent)

```text
Status: complete | partial | blocked

Changed:
- ...

Automation added/updated:
- ...

Validation:
- command: ...
  result: ...

Linear:
- created: N
- reused: N
- skipped: N
- failed: N

Created/Reused issues:
- SHA-123 [bug] ...
- SHA-124 [test] ...

Generated report:
- .agent-loop/reports/...

Risks:
- ...

Needs human review:
- ...
```

---

## References

- `AGENTS.md` § Validation
- `docs/agent-workflows/validation-routine.md`
- `.cursor/rules/agent_scope.mdc`
- [Linear API and Webhooks](https://linear.app/docs/api-and-webhooks)
