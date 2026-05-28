# Reconstruction Max Throughput & Lab UI (PR-2a) — Design Spec

**Date:** 2026-05-25 (UI B-scope amendment: 2026-05-24)  
**Status:** Approved — architecture + Lab UI (B) + localization  
**Depends on:** PR-1 `MiningExtractionRule` + `mining_extraction_rules` helpers (merged or in flight)  
**Follow-ups:** PR-2b `actual_committed_output_per_min` · PR-2c throughput budget correctness

**Parent:** [`2026-05-24-mining-extraction-rule-design.md`](2026-05-24-mining-extraction-rule-design.md)

---

## Problem

Lab UI shows placeholder stat cards (`Best score`, `Extractors`, `Belt groups`, …) and maps `score` / `miners` / `placed` to `confirmed_count` (RTTP commit). Users cannot see:

1. Whether **reconstruction** succeeded (quality, mineable footprint).
2. **Theoretical max throughput** from reconstructed terrain vs RTTP committed placement.

We need reconstruction authority and RTTP authority **visually separated**, with Korean UI via project gettext.

## Non-goals (PR-2a)

- `actual_committed_output_per_min` computation (PR-2b)
- Rewriting `capacity_goals` or `throughput_budget_satisfied` (PR-2c)
- RTTP commit / validation / replay-as-input changes
- Fluid pipe bottleneck modeling
- Route-feasible platform placement proof (v0 = terrain upper bound)
- Full Lab dashboard redesign (Evolution / replay timeline overhaul — deferred)
- `topology_signature` fingerprint for reconstruction (v0 omit; PR-2a.1 optional)

Placeholder flags (`capacity_satisfied`, `throughput_budget_satisfied`, …) stay as-is in PR-2a.

## Two metrics (must never mix)

| Field | Meaning |
|-------|---------|
| `reconstruction_max_throughput_per_min` (shape headline) | Terrain-based **theoretical** max from `ReconstructionResult` + `MiningExtractionRule` |
| `actual_committed_output_per_min` | RTTP route-confirmed production (PR-2b; UI shows `pending_pr_2b`) |

---

## Authority split (Lab UI B)

```text
Top cards 1–4  → reconstruction + capacity (terrain upper bound)
Top card 5     → RTTP committed only
Detail A–B     → reconstruction observability + capacity
Detail C       → RTTP / validation (existing issue rows retained)
```

### Mandatory disclaimer (localized)

English msgids (see Localization); Korean via `locale/ko`:

| Msgid | KO (reference) |
|-------|----------------|
| `Theoretical max = reconstructed terrain upper bound` | `이론 최대치 = 복원된 소행성 지형 기준 상한` |
| `Committed = route-confirmed solver result` | `실제 확정 = 외부 trunk 검증된 solver 결과` |

Show once above top cards (compact) and at top of Detail section C.

---

## CANON rates (from L1b)

| Resource | `mini_unit_output_per_min` | `max_mini_units` (extensions 0..3) | `max_output_per_miner` |
|----------|---------------------------|-------------------------------------|-------------------------|
| shape | 30 shapes/min | 16 | 480 shapes/min |
| fluid | 300 L/min | 16 | 4800 L/min |

```text
max_throughput_per_min(resource) =
    capacity_upper_bound_platform_count * output_per_min(rule, 4)
```

**v0 platform count — SUPERSEDED (2026-05-25):** See [`2026-05-25-reconstruction-field-cell-capacity-contract-design.md`](2026-05-25-reconstruction-field-cell-capacity-contract-design.md). Platform count = **asteroid field cell count** (shape/fluid `cell_kind` only); ×4 per cell; `confirmed_cells` mask not used for cap/placement/mineable SoT.

---

## Backend: `reconstruction_capacity_summary.py`

**Path:** `django_apps/asteroid_lab/services/reconstruction_capacity_summary.py`

```python
def build_reconstruction_capacity_summary(
    *,
    recon: ReconstructionResult,
    resource_kind: str,
) -> dict[str, Any]:
    ...
```

**Inputs only:** `ReconstructionResult` + `get_active_rule` / `max_output_per_miner` from `game_data.services.mining_extraction_rules`.

**Forbidden inputs:** replay frames, existing `solver_summary`, CLR/reflection.

**Per-resource row (decimals as strings in JSON):**

```json
{
  "resource_kind": "shape",
  "capacity_upper_bound_platform_count": 142,
  "mini_unit_output_per_min": "30.0000",
  "max_mini_units_per_miner": 16,
  "max_output_per_miner": "480.0000",
  "max_throughput_per_min": "68160.0000",
  "output_unit": "shapes_per_min",
  "source_kind": "CANON_MANUAL",
  "authority": "MiningExtractionRule"
}
```

**Persisted envelope:**

```json
"reconstruction_capacity": {
  "capacity_basis": "terrain_upper_bound",
  "by_resource": {
    "shape": { "...": "..." },
    "fluid": { "...": "..." }
  }
}
```

---

## Backend: `reconstruction_observability` snapshot

At solver wire time, copy metrics from `reconstruction_step_from_result` (do not re-read replay in Lab):

```json
"reconstruction_observability": {
  "cell_count": 156,
  "confirmed_cell_count": 142,
  "ambiguous_cell_count": 8,
  "external_void_cell_count": 6,
  "quality_tier": "CONFIDENT_RECONSTRUCTION",
  "confidence_score": "0.940",
  "inferred_shell_cell_count": 0
}
```

Optional keys from `recon.summary_json` may be merged when present and JSON-serializable.

---

## `build_rttp_solver_summary` extension

**File:** `django_apps/asteroid_lab/optimization/rttp_solver_summary.py`

```python
reconstruction_capacity_summary: Mapping[str, Any] | None = None,
reconstruction_observability: Mapping[str, Any] | None = None,
```

When provided:

```python
summary["reconstruction_capacity"] = dict(reconstruction_capacity_summary)
summary["reconstruction_observability"] = dict(reconstruction_observability)
```

When `None`, omit keys (backward compatible).

**Wire site:** `solver_runtime_entry.py` after reconstruction, before commit. Do not read replay.

---

## Lab DTO (`solver_run_lab_summary.py`)

Nested sections for template + JS (replace flat placeholder keys `score`/`belts`/`pipes` used for fake GA cards):

```python
{
  "reconstruction": {
    "cell_count": int | "—",
    "confirmed_cell_count": int | "—",
    "ambiguous_cell_count": int | "—",
    "external_void_cell_count": int | "—",
    "quality_tier": str | "—",
    "confidence_score": str | "—",
    "quality_tier_short": str | "—",  # e.g. HIGH from CONFIDENT_RECONSTRUCTION
  },
  "capacity": {
    "shape_max_throughput_per_min": str | "—",
    "fluid_max_throughput_per_min": str | "—",
    "shape_output_unit": str | "—",
    "fluid_output_unit": str | "—",
    "reconstruction_max_throughput_per_min": str | "—",  # alias: shape headline
    "platform_upper_bound": int | "—",
    "capacity_basis": str | "—",
    "extraction_rule_source": str | "—",
  },
  "rttp": {
    "confirmed_count": int | "—",
    "validation_passed": bool,
    "actual_committed_output_per_min": None,
    "actual_output_status": "pending_pr_2b" | "available",
    "candidate_count": int | "—",  # when present in solver_summary
    "commit_order_preview": str | "—",  # first id or truncated join
  },
  # Retain existing validation/issue/algorithm_steps keys at top level for HUD
}
```

Legacy runs without new keys: section fields → `_PLACEHOLDER` (`"—"`), `actual_output_status` → `pending_pr_2b`.

---

## Lab UI — top 5 cards

**Files:** `django_apps/web/templates/web/asteroid_miner_layout_solver.html`, `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`

| # | English msgid (label) | Primary value | Subtitle msgid |
|---|----------------------|---------------|----------------|
| 1 | `Theoretical Max` | `capacity.shape_max_throughput_per_min` + unit | `terrain upper bound (shape)` |
| 2 | `Resource Capacity` | `Belt {shape} / Fluid {fluid}` formatted | `from reconstructed terrain` |
| 3 | `Mineable Footprint` | `{confirmed} / {cell}` | `confirmed cells` |
| 4 | `Reconstruction Quality` | `{tier_short} · {confidence}` | `quality / confidence` |
| 5 | `RTTP Committed` | `{confirmed_count}` + `placement(s)` | `actual output pending` until PR-2b |

Remove permanently: `Best score`, `fitness weighted`, `Extensions`, `Belt groups`, `Fluid groups`, hardcoded `5 miners each` / `4 miners each`.

Card DOM ids (stable for JS): `lab-card-theoretical-max`, `lab-card-resource-capacity`, `lab-card-footprint`, `lab-card-reconstruction-quality`, `lab-card-rttp-committed`.

On run select, JS updates card bodies from `run.reconstruction` / `run.capacity` / `run.rttp` (same shape as SSR).

---

## Lab UI — Selected Run Detail

Replace bottom `—` placeholder panel with three sub-panels:

### A. Reconstruction Summary

Fields from `reconstruction` DTO (labels via `{% trans %}`).

### B. Capacity Summary

`by_resource` shape/fluid throughput, `platform_upper_bound`, `extraction_rule_source`, `capacity_basis`.

### C. RTTP Result

`rttp` section + existing validation/issue rows (relocate misleading `Fitness` / `Belt-equivalent groups` labels to RTTP naming or hide when `—`).

---

## Lab UI — Evolution Runs list (minimal)

Do not restructure list layout. Replace 3-column subtitle:

```text
{shape_max}/min theor. | {confirmed} committed | {quality_tier_short}
```

Use `shapezUiT()` for unit suffixes. Do not show `score` as run headline metric.

---

## Localization (required in PR-2a)

**Policy:** English **msgids** everywhere; Korean product strings via `locale/ko` and `scripts/build_locale_ko.py` `KO` dict. Matches `solver.html` / `ui_locale.js` pattern; Asteroid Lab currently hardcoded English — PR-2a migrates **new and touched** Lab copy only (scope: stat cards, disclaimers, detail panels A–C, evolution list strings, JS dynamic fragments).

### Template

- `{% load i18n %}` on Lab template (if not already via base).
- All new visible labels: `{% trans "..." %}` or `{% blocktrans %}` with variables for numbers only.

### JavaScript

- Dynamic strings: `shapezUiT("...")` from `ui_locale.js` (requires `javascript-catalog` — already in `base.html`).
- Do not embed Korean literals in `.js` files.

### Locale build

After adding msgids:

```powershell
python scripts/build_locale_ko.py
python scripts/build_locale_ko.py --strict   # when touching public_pages strict paths
```

Add every new msgid to `KO` in `scripts/build_locale_ko.py` with Korean copy (cards, subtitles, disclaimers, panel headings, `pending_pr_2b`, `placement(s)`, `validation failed`, evolution list fragments).

### Language activation

Uses existing Django `LANGUAGE_CODE` / `html lang` — no new language switcher in PR-2a.

### Numeric formatting

Locale-aware **number** grouping optional v0; units and labels must be translated. Values stay canonical strings from backend (`"68160.0000"` → display trim in JS/template).

---

## PR split (mining extraction arc)

| PR | Delivers |
|----|----------|
| PR-1 | `MiningExtractionRule`, seed, helpers, admin |
| **PR-2a** | Capacity builder + observability snapshot + nested Lab DTO + localized UI (B) |
| PR-2b | `actual_committed_output_per_min`; card 5 subtitle → committed rate |
| PR-2c | User `throughput_target_percent` 10–80; `target_throughput_per_min`; real `throughput_budget_satisfied` — [`2026-05-24-throughput-target-percent-pr2c-design.md`](2026-05-24-throughput-target-percent-pr2c-design.md) |

---

## Tests (required)

| Module | Cases |
|--------|-------|
| `test_reconstruction_capacity_summary.py` | rule 30×16; platform count; decimal strings; shape+fluid rows; no solver_summary input |
| `test_rttp_solver_summary.py` | includes `reconstruction_capacity` / `reconstruction_observability` when provided |
| `test_solver_run_lab_summary.py` | nested `reconstruction` / `capacity` / `rttp`; legacy placeholder; `actual_output_status` |
| `test_asteroid_lab_ui_strings.py` (or template lint) | forbidden placeholder substrings absent from template |
| `test_build_locale_ko_strict.py` | if new `_("...")` added to strict Python paths |

Regression: Lab template must not contain `Best score`, `fitness weighted`, `5 miners each`.

---

## Validation (narrow)

```powershell
python -m pytest tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py -v --tb=short
python -m pytest tests/unit/asteroid_lab/test_solver_run_lab_summary.py -v --tb=short
python -m pytest tests/unit/asteroid_lab/test_rttp_solver_summary.py -v --tb=short
python scripts/build_locale_ko.py
python -m ruff check django_apps/asteroid_lab/services/reconstruction_capacity_summary.py django_apps/asteroid_lab/optimization/rttp_solver_summary.py django_apps/asteroid_lab/services/solver_run_lab_summary.py django_apps/web/
```

---

## Forbidden shortcuts

- Replay or prior `solver_summary` as computation input
- Treating reconstruction max as `confirmed_throughput` or `throughput_budget_satisfied`
- Summing shape + fluid throughput into one number on card 1
- Korean hardcoded in JS without `shapezUiT` / gettext
- Changing validation_passed / commit order / capacity_goals in PR-2a
