---
name: cli-boundary
description: >-
  CLI Boundary Architect rules for the Asteroid Lab / Shapez2 Factory project.
  Treat every CLI entrypoint as a thin execution adapter, never a solver/domain/
  replay layer. Use when creating, modifying, or reviewing a CLI command,
  management command, or other solver-execution entrypoint, or when checking CLI
  import boundaries, serialization contracts, exit codes, or determinism.
disable-model-invocation: false
metadata:
  owner: project
  risk: medium
  requires_validation: true
---

# CLI Development Rules Skill

## Purpose

Use this skill whenever creating, modifying, or reviewing a CLI entrypoint for the Asteroid Lab / Shapez2 Factory project.

The CLI must be treated as a thin execution boundary, not as a place for solver logic, Django coupling, replay interpretation, or ad-hoc orchestration.

## Related project sources

Read only when the changed paths touch them:

- Global gates and forbidden shortcuts: [AGENTS.md](../../../AGENTS.md), [shapez2-core.mdc](../../rules/shapez2-core.mdc)
- Layer boundaries: [architecture.mdc](../../rules/architecture.mdc)
- Asteroid Lab invariants: [asteroid-lab-invariants.mdc](../../rules/asteroid-lab-invariants.mdc)
- Testing gates: [testing.md](../../../documents/ai/manuals/testing.md)

---

## Required Role

Role: CLI Boundary Architect

---

## Mandatory Rules

### 1. CLI is an adapter, not a solver layer

The CLI may:

- parse arguments
- load input files or copy strings
- call an approved application service
- print or write deterministic output
- return explicit exit codes

The CLI must not:

- implement solver logic directly
- mutate domain state outside approved services
- read replay frames as algorithm input
- infer topology from UI artifacts
- silently call Django ORM from core logic

---

### 2. Core logic must stay import-clean

CLI-facing code must preserve import boundaries.

Allowed direction:

```text
CLI
→ application service
→ core/domain layer
→ pure solver/reconstruction/validation modules
```

Forbidden direction:

```text
core/domain → CLI
core/domain → Django view
core/domain → replay UI
core/domain → ORM model
core/domain → solver_summary artifact
```

If Django setup is required, isolate it in the CLI adapter or application boundary, never inside domain modules.

---

### 3. Replay and artifacts are output-only

The following are debug/output artifacts only:

```text
NDJSON
ReplayFrame
solver_summary
lab metrics
timeline payload
UI overlay
artifact JSONL
```

They must not become source-of-truth inputs for solver, reconstruction, routing, placement, validation, or commit logic.

---

### 4. Every CLI command must have an explicit contract

Each CLI command must define:

```text
command name
input format
output format
exit codes
failure modes
side effects
determinism guarantees
```

Minimum command contract template:

```md
## CLI Contract

Command:
Input:
Output:
Writes:
Exit codes:
Deterministic:
Requires Django:
Allowed imports:
Forbidden imports:
Failure behavior:
Verification command:
```

---

### 5. Fail closed, never guess

CLI must fail closed on missing required data.

Do not:

- synthesize missing catalog data
- invent fallback topology
- silently use stale replay data
- continue after invalid DTO schema
- convert unknown failure into success

Use explicit failure codes or enums.

Recommended examples:

```text
MISSING_INPUT
INVALID_COPY_STRING
INVALID_RECONSTRUCTION_COMPLETE_MAP
MISSING_GENE_CATALOG
INVALID_GENE_CATALOG
MISSING_EVTC_ROW
LAYER_FAILED_CLOSED
VALIDATION_FAILED
```

---

### 6. Deterministic output required

CLI output must be stable for the same input.

Required:

- stable sorting
- stable JSON key ordering where practical
- no timestamp in deterministic artifacts unless explicitly marked metadata
- no random seed unless passed explicitly
- no environment-dependent path leakage in golden outputs

Use, where relevant:

```text
--seed
--output
--format json|jsonl|summary
--strict
--dry-run
```

---

### 7. Streaming must be explicit

Long-running solver CLI may stream progress, but streaming output must be contract-separated.

Allowed:

```text
stdout: user-readable progress
stderr: diagnostics
--jsonl: machine-readable events
--output: final artifact
```

Do not mix progress logs into final JSON output.

For machine mode:

```text
one JSON object per line
event_type required
schema_version required
run_id optional but stable if provided
```

---

### 8. Validation is read-only

Validation CLI commands must only assert.

Validation must not:

- create new routes
- repair topology
- mutate layout
- regenerate candidates
- normalize failed state into passing state

Validation may:

- load complete map
- load candidate/commit result
- check invariants
- emit issue codes
- return non-zero exit code

---

### 9. Tests are mandatory before implementation is considered done

Every CLI command requires at least:

```text
unit test for parser / argument contract
unit test for success path
unit test for fail-closed path
snapshot or golden test for output format
import-boundary test if command touches core/domain
```

Recommended gate:

```powershell
python -m pytest <targeted tests> -v
python -m ruff check <touched paths>
python -m mypy <touched packages>
```

If formatter is part of the repo gate:

```powershell
python -m black --check <touched paths>
```

Do not use pytest output-suppression flags (`-q`, `--quiet`, `--tb=no`, `-p no:terminal`).

---

### 10. CLI implementation workflow

Do not jump directly to implementation.

Required flow:

```text
1. Brainstorm command contract
2. Write spec or amend existing spec
3. Write implementation plan
4. Add RED tests
5. Implement minimum GREEN
6. Refactor
7. Run targeted gates
8. Update docs / command help
9. Report exact files and commands run
```

For agentic execution, use:

```text
superpowers:subagent-driven-development
```

or:

```text
superpowers:executing-plans
```

Task plans must use checkbox syntax.

---

## CLI Review Checklist

Before approving a CLI PR, verify:

```text
[ ] CLI is adapter-only
[ ] domain/core imports do not depend on CLI/Django/UI/replay
[ ] input/output schema documented
[ ] explicit exit codes exist
[ ] fail-closed behavior tested
[ ] deterministic output tested
[ ] no replay/solver_summary used as algorithm input
[ ] no synthetic missing domain data
[ ] validation is read-only
[ ] targeted pytest passed
[ ] ruff passed
[ ] mypy passed where applicable
[ ] docs/help updated
```

---

## Stop Conditions

Stop and request architectural review if:

```text
CLI needs to import a Django model inside a core module
CLI needs replay data as solver input
CLI command mutates state during validation
missing catalog/game data is being synthesized
output differs across identical runs
command requires broad refactor outside planned scope
```

---

## Final Response Format

When reporting CLI work, use:

```md
Role: CLI Boundary Architect

## Classification
CLI change / contract change / refactoring / test-only / docs-only

## Summary
- ...

## Files Changed
| Path | Why |
|---|---|

## Verification
\`\`\`powershell
...
\`\`\`

## Boundary Check
- CLI adapter only:
- Replay-as-input avoided:
- Django/core boundary:
- Determinism:
- Fail-closed behavior:

## Status
DONE / BLOCKED / PARTIAL
```

---

## Core constraints (always enforce)

```text
1. CLI is adapter-only
2. core/domain does not import Django · UI · Replay
3. Replay / solver_summary / NDJSON are output-only
4. Every CLI command is fail-closed + deterministic + tested
```
