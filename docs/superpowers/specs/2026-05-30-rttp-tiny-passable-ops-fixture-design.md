# Track B-3F — Tiny Non-Vacuous Pass-Capable Ops Fixture (Design)

**Status:** ACTIVE (2026-05-30) — fixture v0 imported; **certification not achieved**  
**Parent:** [`2026-05-30-rttp-pass-capable-slug-certification-design.md`](2026-05-30-rttp-pass-capable-slug-certification-design.md) (Track B Task 3 BLOCKED)

---

## Problem

Track B scan showed `certified_pass_count = 0`. The closest partial candidate (`rttp-cert-candidate-recon-l0`) passes T0/T1a/T1b but fails T2 because **reconstruction terrain upper bound** dominates throughput target:

```text
shape_field_cell_count ≈ 583
per_cell (4 mini)        = 120 shapes/min
reconstruction_max       ≈ 583 × 120 = 69_960/min
target @ 80%             ≈ 55_968/min
actual_committed         ≈ 2_760/min  (~4.9% utilization)
```

This is not “solver off”; it is **certification map class mismatch** (large inferred field envelope + modest v0.1 commits).

Vacuous T2 (`reconstruction_max = 0`, `throughput_budget_satisfied = true`) is excluded from pass_capable evidence.

---

## Goal (B-3F)

Introduce a **dedicated ops fixture** where:

| Constraint | Target |
|------------|--------|
| `reconstruction_max` | **> 0**, not vacuous |
| Field scale | Small (v0 target: ≤ ~28 shape field cells so 80% target ≤ ~3_450 when per_cell = 120) |
| RTTP v0.1 default path | `validation_passed`, `confirmed_count > 0`, `throughput_budget_satisfied` |
| Slug class | Not diagnostic canon |

---

## Task 3F-1 — recon-l0/l1 `reconstruction_max` root cause

**SoT:** `build_reconstruction_capacity_envelope` → `shape_field_cell_count` on `ReconstructionCompleteMap` (terrain upper bound, not overlay-only count).

| Slug / fixture | `shape_field_cell_count` | `reconstruction_max` (shape) | `target_80%` |
|----------------|--------------------------|------------------------------|--------------|
| `recon-l0` / `recon-l1` | 583 | 69_960 | 55_968 |
| `copy-import-495e552c` | 628 | 75_360 | 60_288 |
| `tiny-passable-l0` (v0) | **4** | **480** | **384** |
| `minimal-fluid` / vacuous | 0 | 0 | 0 |

**Cause:** Full-size reconstruction fixtures infer **hundreds** of `asteroid_shape_field` cells from real asteroid copy topology. RTTP commits a **small fraction** of platform upper bound → T2 shortfall under default 80% target.

---

## Task 3F-2 — Fixture v0: `tiny-passable-l0`

**Artifact:** [`tests/fixtures/asteroid_lab/rttp_tiny_passable_l0.code`](../../../tests/fixtures/asteroid_lab/rttp_tiny_passable_l0.code)  
**Import:** `python scripts/dev_import_rttp_cert_candidate.py --variant tiny-passable-l0 --replace`  
**Lab slug:** `rttp-cert-candidate-tiny-passable-l0`

**Layout intent:**

- 4-cell shape field ring (`UnknownTile_*` evidence → reconstruction)
- `Layout_ProMiner` + exterior `SpaceBelt_Right` trunk
- No diagnostic canon; non-zero capacity band

**Probe (minimal catalog slice):** `scripts/probe_rttp_tiny_passable_maps.py`

---

## Task 3F-3 — Single-slug scan result (full runtime)

**Report:** [`reports/2026-05-30-rttp-pass-capable-slug-certification-rescan-tiny-passable-l0.json`](../reports/2026-05-30-rttp-pass-capable-slug-certification-rescan-tiny-passable-l0.json)

| Field | Value |
|-------|-------|
| `cert_status` | `fail_t1b` |
| `reconstruction_max` (implied) | 480 (`throughput_target_min` = 384 @ 80%) |
| `actual_committed` | 0 |
| `validation_passed` | false |
| `issue_codes` | `rttp_validation_failed`, `throughput_target_shortfall` |

**Judgment:** v0 achieves **correct capacity band** but **does not commit** on full `run_solver` path → not certifiable.

---

## Task 3F-v1 — recon-l0 cluster crop (`tiny-passable-v1`)

**Slug:** `rttp-cert-candidate-tiny-passable-v1`  
**Builder:** `scripts/build_tiny_passable_v1_crop_from_recon.py` (first commit cluster on recon-l0, `max_fields=12`)  
**Fixture:** [`tests/fixtures/asteroid_lab/rttp_tiny_passable_v1.code`](../../../tests/fixtures/asteroid_lab/rttp_tiny_passable_v1.code)

| Metric | v1 crop |
|--------|---------|
| `shape_field_cell_count` | **12** |
| `reconstruction_max` | **1_440**/min |
| `target_80%` | **1_152** |
| `actual_committed` | **360** (3 commits) |
| T0/T1a/T1b | **PASS** |
| T2 | **FAIL** (`throughput_target_shortfall`) |
| `cert_status` | `fail_t2` |

**Split closed:** route-feasible **commit shell** on cropped real-map geometry (non-vacuous). **Throughput tier** still blocked: commit count on small crop (~3) ≪ required (~10) for 12-field 80% target.

**Not used:** narrow-corridor-as-copy (synthetic `OptimizationInput` commits in unit tests do not survive copy→reconstruction→runtime; all 16 genome slots conflicted).

---

## Task 3F-v2 — bbox crop cap (`tiny-passable-v2`)

**Slug:** `rttp-cert-candidate-tiny-passable-v2`  
**Builder:** `scripts/build_tiny_passable_v2_crop_from_recon.py` → v1 bbox crop with `max_fields=5`, anchor run `solver_run_id=136`  
**Fixture:** [`tests/fixtures/asteroid_lab/rttp_tiny_passable_v2.code`](../../../tests/fixtures/asteroid_lab/rttp_tiny_passable_v2.code)

| Metric | v2 |
|--------|-----|
| `shape_field_cell_count` | **5** |
| `reconstruction_max` | **600**/min |
| `target_80%` | **480** |
| `actual_committed` | **480** (4 commits) |
| `cert_status` | **`certified_pass`** |

Report: [`reports/2026-05-30-rttp-pass-capable-slug-certification-rescan-tiny-passable-v2.json`](../reports/2026-05-30-rttp-pass-capable-slug-certification-rescan-tiny-passable-v2.json)

**Sweep (ephemeral, `run_id=136`):** `max_fields=4` → `fail_t1b`; `max_fields=5` → `certified_pass`; `max_fields≥8` → T1b pass but T2 shortfall on same geometry family.

---

## Task 3F-4 — limit-30 rescan

Ready after Task 4 registry adds `rttp-cert-candidate-tiny-passable-v2` to `RTTP_PASS_CAPABLE_SLUGS`.

---

## Fixture hardening backlog

1. ~~Non-vacuous `certified_pass` on tiny crop~~ — closed by v2 (`max_fields=5`).
2. Task 4: registry + limit-30 confirmation per pass-capable slug spec.
3. Track A remains optional for `recon-l0` throughput recovery (large envelope); not required for Track B unblock.

---

## Forbidden (unchanged)

- `RTTP_PASS_CAPABLE_SLUGS` registration without Task 4 confirmation
- Track B CLOSED without `certified_pass`
- Lowering `throughput_target_percent` for certification
- Vacuous `reconstruction_max = 0` as pass evidence

---

## References

- Capacity SoT: `django_apps/asteroid_lab/services/reconstruction_capacity_summary.py`
- Throughput budget: `django_apps/asteroid_lab/services/throughput_target.py`
- Task 3 evidence: [`reports/2026-05-30-rttp-pass-capable-slug-certification-task3-summary.md`](../reports/2026-05-30-rttp-pass-capable-slug-certification-task3-summary.md)
