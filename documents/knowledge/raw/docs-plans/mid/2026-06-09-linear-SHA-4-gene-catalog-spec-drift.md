# Plan: SHA-4 - GeneCatalogSnapshot spec drift vs GeneticSampleSeedSnapshot

## Source

- Linear issue: https://linear.app/zkaufman/issue/SHA-4
- Priority: Mid
- Labels: test, question, docs, solver, spec
- Status at planning time: Todo

## Problem

Normative Layer 03 spec defines `GeneCatalogSnapshot`, schema version `gene_catalog_v1`, and skip reasons `MISSING_GENE_CATALOG` / `INVALID_GENE_CATALOG`, but runtime uses `GeneticSampleSeedSnapshot`, `genetic_sample_seed_v1`, and different `Layer03SkipReason` enum values. Published spec and implementation cannot both be authoritative.

## Scope

- Resolve spec vs implementation naming drift for L3 gene-catalog boundary.
- Align DTO, skip reasons, CLI flag docs, and tests to a single chosen authority.
- Add schema round-trip test for canonical contract.

## Non-goals

- Changing gene sampling semantics or throughput validation rules.
- L4 `GeneCatalogSnapshot` references (separate deferred work).
- Runtime solver behavior beyond contract naming alignment.

## Implementation Plan

1. **Human decision gate:** Choose authority path before coding:
   - **(A) Rename implementation to match spec:** `GeneticSampleSeedSnapshot` → `GeneCatalogSnapshot`, schema `gene_catalog_v1`, skip reasons `MISSING_GENE_CATALOG` / `INVALID_GENE_CATALOG`.
   - **(B) Amend spec to canonize implementation:** Update normative L3 spec and plans to `GeneticSampleSeedSnapshot`, `genetic_sample_seed_v1`, and current skip reason enums.
2. Apply chosen path across adapter, contracts, runner gate, CLI docs, and tests in one PR.
3. Update `src/shapez2_factory/adapters/asteroid_lab/genetic_sample_seed_snapshot.py` (or rename to `gene_catalog_snapshot.py` per path A).
4. Align `Layer03SkipReason` in `application/asteroid_lab/layers/contracts/candidates.py` and `run.py:73-90` gates.
5. Update `docs/superpowers/specs/2026-05-31-layer-03-rim-placement-v2-design.md` §G/M to match chosen authority.
6. Fix unit tests: `test_layer_03_gene_catalog_gate.py`, `test_genetic_sample_catalog_snapshot.py`.
7. Confirm no mixed skip-reason strings in replay/metrics output.

## Files / Areas Likely Affected

- `src/shapez2_factory/adapters/asteroid_lab/genetic_sample_seed_snapshot.py`
- `src/shapez2_factory/application/asteroid_lab/layers/contracts/candidates.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/run.py`
- `docs/superpowers/specs/2026-05-31-layer-03-rim-placement-v2-design.md`
- `tests/unit/asteroid_lab/test_layer_03_gene_catalog_gate.py`
- `tests/unit/asteroid_lab/test_genetic_sample_catalog_snapshot.py`
- CLI docs referencing `--gene-catalog` / `input/gene_catalog.json`

## Tests / Validation

- `pytest tests/unit/asteroid_lab/test_layer_03_gene_catalog_gate.py tests/unit/asteroid_lab/test_genetic_sample_catalog_snapshot.py -q`
- `python manage.py check`
- `ruff check .`

## Acceptance Criteria

- [ ] Single canonical DTO name and `schema_version` agreed and documented in normative L3 spec
- [ ] `Layer03SkipReason` skip-reason enums match chosen contract (no mixed spec/impl names)
- [ ] Adapter, runner gate, and CLI docs use canonical naming
- [ ] Unit tests assert canonical enum values and DTO round-trip
- [ ] Targeted pytest suite passes

## Risks

- **Blocked on human authority decision** between rename-impl (A) vs amend-spec (B).
- Wide rename touches adapter, contracts, tests, docs, and possibly CLI artifact paths.
- Downstream consumers referencing old names may break if migration alias not documented.

## Human Review Required

- yes
- reason: Contract authority decision required (rename implementation vs amend spec); product scope and naming convention change affecting published spec and CLI surface.

## Automation Notes

Generated from Linear Todo issue by planning automation.

Issue carries `question` label — implementation must not proceed until authority path (A or B) is chosen.
