---
linear_issue: SHA-22
title: Subprocess solver runtime omits gene_template_source provenance despite exporting GeneSeed snapshot
priority: Mid
labels:
  - bug
  - ui
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Wire gene_template_source provenance through subprocess runtime

## Source Issue

- Linear: SHA-22
- Status at planning time: Todo
- Priority: Mid

## Problem

Subprocess runtime exports genetic sample seeds but discards `gene_template_source` provenance. Lab UI `genes:<count>` always empty; `SolverRun.config_json` missing field.

## Scope

Populate `gene_template_source` in subprocess request build, HTTP response, and `config_json` persistence.

## Non-goals

- Do not use provenance as solver algorithm input.
- Do not change CLI snapshot export format.

## Implementation Plan

1. Read `solver_runtime_entry.py`, `runtime_gene_template_source.py`, `solver_run_config_keys.py`.
2. After `build_genetic_sample_seed_snapshot`, derive `GeneTemplateSourceMetadata` from snapshot `entries`.
3. Thread through `_run_subprocess_runtime_for_project` and `enqueue_solver_run_for_project`.
4. Persist in `config_json["gene_template_source"]`; return via `SolverRuntimeEntryResult` / `entry_result_to_json_dict`.
5. Add unit test: GeneSeed rows present → non-empty `gene_count`.
6. Verify `asteroid_miner_layout_lab.js` displays `genes:<count>`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- `django_apps/asteroid_lab/services/runtime_gene_template_source.py`
- `django_apps/asteroid_lab/services/solver_run_config_keys.py`
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`

## Validation Plan

- tests: unit tests under `tests/unit/asteroid_lab/`
- manual verification: Lab status text shows gene count

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Related SHA-28 game_data provenance — coordinate but separate scope.
