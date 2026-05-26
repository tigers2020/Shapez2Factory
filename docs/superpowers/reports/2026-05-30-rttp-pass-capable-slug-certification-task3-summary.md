# Track B Task 3 — Pass-capable slug scan evidence (2026-05-30)

**Status:** **Track B CLOSED (complete, 2026-05-30)** — PR [#101](https://github.com/tigers2020/Shapez2Factory/pull/101)  
**Registry:** `RTTP_PASS_CAPABLE_SLUGS` = `{rttp-cert-candidate-tiny-passable-v2}`  
**Borderline pass:** `actual_committed=480` == `throughput_target_min=480` (non-vacuous; 5 shape fields)  
**Post-merge confirm (local):** [`post-merge-confirm-v2.json`](2026-05-30-rttp-pass-capable-slug-certification-post-merge-confirm-v2.json) — `solver_run_id` **174**

## Artifacts

| File | Purpose |
|------|---------|
| [`2026-05-30-rttp-pass-capable-slug-certification-scan-limit20.json`](2026-05-30-rttp-pass-capable-slug-certification-scan-limit20.json) | Initial DB scan (`--limit 20`, diagnostic excluded) |
| [`2026-05-30-rttp-pass-capable-slug-certification-rescan-limit30.json`](2026-05-30-rttp-pass-capable-slug-certification-rescan-limit30.json) | Post-import rescan (`--limit 30`, 7 candidates) |
| [`2026-05-30-rttp-pass-capable-slug-certification-diagnostic-canon.json`](2026-05-30-rttp-pass-capable-slug-certification-diagnostic-canon.json) | Diagnostic sanity (`skipped_diagnostic`, no runtime) |
| Per-slug reports | `rescan-recon-l0.json`, `rescan-recon-l1.json`, `rescan-minimal.json`, `rescan-tiny-island.json`, `rescan-minimal-fluid.json` |

**Import helper (dev DB):** `scripts/dev_import_rttp_cert_candidate.py` (`--variant`, `--replace`).

## Scan summary (limit 30, after candidate imports)

| Metric | Value |
|--------|-------|
| `candidate_count` | **7** (5 imported cert candidates + 2 legacy ops-smoke slugs) |
| `certified_pass_count` | **0** |
| `blocked_count` | 7 |
| `fail_runtime` | **0** |

### Per-slug results (latest `solver_run_id` from limit-30 scan)

| Slug | `solver_run_id` | `cert_status` | Tier notes |
|------|-----------------|---------------|------------|
| `ops-smoke-c-mixed-transport` | 118 | `fail_t1b` | Vacuous T2 (`reconstruction_max=0`, target 0); **no commits**; `rttp_validation_failed` |
| `ops-smoke-c-scan` | 119 | `fail_t2` | T1b pass; `throughput_target_shortfall` (actual 1200 vs target 294720) |
| `rttp-cert-candidate-minimal` | 120 | `fail_t1b` | Synthetic 2-cell island; validation failed |
| `rttp-cert-candidate-minimal-fluid` | 121 | `fail_t1b` | Single fluid miner; validation failed |
| `rttp-cert-candidate-recon-l0` | 122 | `fail_t2` | T1b pass; actual 2760 vs target 55968 |
| `rttp-cert-candidate-recon-l1` | 123 | `fail_t2` | T1b pass (canon hole map); same throughput gap as L0 |
| `rttp-cert-candidate-tiny-island` | 124 | `fail_t1b` | Fluid miner + extension; validation failed |

**Best partial candidate:** `rttp-cert-candidate-recon-l0` / `recon-l1` — T0/T1a/T1b pass; blocked on **T2 throughput** only (~5% utilization vs 80% default target).

## Initial scan (limit 20, pre-import)

| Metric | Value |
|--------|-------|
| `candidate_count` | 2 |
| `certified_pass_count` | **0** |

See limit-20 JSON for `ops-smoke-c-*` baseline.

## Diagnostic canon sanity

| Slug | `cert_status` | `solver_run_id` | Runtime |
|------|---------------|-----------------|---------|
| `copy-import-495e552c` | `skipped_diagnostic` | `null` | **Not executed** (contract OK) |

## Judgment (Task 3 rules)

- **`certified_pass_count == 0`** after importing simple Lab maps → **Track B remains BLOCKED**.
- Do **not** weaken T3 criteria, lower `throughput_target_percent` for cert, or promote `copy-import-495e552c`.
- **Do not** treat vacuous T2 (`reconstruction_max=0`) as pass_capable evidence.
- **Next options:** (1) **Track A** — throughput recovery on a T1b-pass slug (`recon-l0` / `ops-smoke-c-scan`) with product approval; (2) new map + solver placement work until `actual_committed` ≥ 80% of `reconstruction_max`; (3) curated ops fixture designed for T2 pass (not yet in repo).

## Track B-3F (2026-05-30) — tiny pass-capable fixture

**Design:** [`2026-05-30-rttp-tiny-passable-ops-fixture-design.md`](../specs/2026-05-30-rttp-tiny-passable-ops-fixture-design.md)

### 3F-1 — `reconstruction_max` root cause (recon-l0/l1)

| Metric | recon-l0/l1 |
|--------|----------------|
| `shape_field_cell_count` | **583** |
| `reconstruction_max` | **69_960**/min (583 × 120 per field cell) |
| `target_80%` | **55_968** |
| Runtime `actual_committed` | **2_760** (~4.9% utilization) |

Large inferred field envelope + partial v0.1 commits → T2 impossible without throughput recovery or smaller cert map.

### 3F-2/3 — `tiny-passable-l0` v0

| Metric | `rttp-cert-candidate-tiny-passable-l0` |
|--------|--------------------------------------|
| `shape_field_cell_count` | **4** (non-vacuous) |
| `reconstruction_max` | **480** |
| `target_80%` | **384** |
| Scan `cert_status` | **`fail_t1b`** (0 commits; `rttp_validation_failed`) |
| Report | [`rescan-tiny-passable-l0.json`](2026-05-30-rttp-pass-capable-slug-certification-rescan-tiny-passable-l0.json) |

**Split:** Capacity band correct; **commit/validation shell not closed** on full runtime.

### 3F-v1 — `tiny-passable-v1` (recon-l0 cluster crop)

| Metric | Value |
|--------|-------|
| `shape_field_cell_count` | 12 |
| `reconstruction_max` | 1_440 |
| `target_80%` | 1_152 |
| `actual_committed` | 360 (3 commits) |
| `cert_status` | **`fail_t2`** (T0/T1a/T1b **PASS**) |

Report: [`rescan-tiny-passable-v1.json`](2026-05-30-rttp-pass-capable-slug-certification-rescan-tiny-passable-v1.json) · design: [`2026-05-30-rttp-tiny-passable-ops-fixture-design.md`](../specs/2026-05-30-rttp-tiny-passable-ops-fixture-design.md)

### 3F-v2 — `tiny-passable-v2` (v1 bbox crop, `max_fields=5`)

| Metric | Value |
|--------|-------|
| `shape_field_cell_count` | **5** |
| `reconstruction_max` | **600**/min |
| `target_80%` | **480** |
| `actual_committed` | **480** (4 commits @ 120/min) |
| T0/T1a/T1b/T2/T3 | **PASS** |
| `cert_status` | **`certified_pass`** |
| `solver_run_id` | 151 (confirmation re-run also `certified_pass_count=1`) |

**Builder:** `scripts/build_tiny_passable_v2_crop_from_recon.py` (delegates to v1 bbox crop; `run_id=136`; `max_fields=5`).  
**Report:** [`rescan-tiny-passable-v2.json`](2026-05-30-rttp-pass-capable-slug-certification-rescan-tiny-passable-v2.json)  
**Fixture:** [`tests/fixtures/asteroid_lab/rttp_tiny_passable_v2.code`](../../../tests/fixtures/asteroid_lab/rttp_tiny_passable_v2.code)

**Note:** `max_fields=4` fails T1b (0 commits); `max_fields=5` is the minimum bbox crop that closes T1b **and** T2 on non-vacuous capacity.

### 3F judgment

v2 achieves **`certified_pass`** on default 80% throughput policy (borderline: zero margin on T2).

## Task 4 — CLOSED (2026-05-30)

| Step | Evidence |
|------|----------|
| Registry | [`rttp_ops_policy.py`](../../../django_apps/asteroid_lab/contracts/rttp_ops_policy.py) — `RTTP_PASS_CAPABLE_SLUGS` |
| Unit tests | 32 passed (classification, T3 evaluator, T2 policy, scan command) |
| Post-registry confirm | [`task4-confirm-v2.json`](2026-05-30-rttp-pass-capable-slug-certification-task4-confirm-v2.json) — `slug_class=pass_capable`, `solver_run_id` 153 |
| limit-30 rescan | [`task4-limit30.json`](2026-05-30-rttp-pass-capable-slug-certification-task4-limit30.json) — `certified_pass_count=4` (includes v2) |
| Pre-registry cert | [`rescan-tiny-passable-v2.json`](2026-05-30-rttp-pass-capable-slug-certification-rescan-tiny-passable-v2.json) — `solver_run_id` 151 |
| Post-merge confirm | [`post-merge-confirm-v2.json`](2026-05-30-rttp-pass-capable-slug-certification-post-merge-confirm-v2.json) — `solver_run_id` **174** |
| DB cleanup | Removed 9× `rttp-cert-probe-mf*` ephemeral projects (sweep artifacts) |
