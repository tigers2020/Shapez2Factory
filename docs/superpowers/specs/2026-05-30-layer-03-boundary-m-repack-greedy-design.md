# Layer 03 Boundary-M Repack Greedy (m3e_01) — Normative Design

**Status:** ACTIVE (authored in boundary-m-repack PR-B)
**Date:** 2026-05-30
**Owner:** Layer 03 rim greedy placement (`django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/`)
**Plan set:** [`../plans/2026-05-30-layer-03-boundary-m-repack-greedy/README.md`](../plans/2026-05-30-layer-03-boundary-m-repack-greedy/README.md)
**Gates PR-CLI-2e:** [`../plans/2026-05-30-asteroid-lab-cli-first/pr-cli-2e-l3-gated-move.md`](../plans/2026-05-30-asteroid-lab-cli-first/pr-cli-2e-l3-gated-move.md)
**Invariants:** [`.cursor/rules/asteroid-lab-invariants.mdc`](../../../.cursor/rules/asteroid-lab-invariants.mdc)

This document is the single source of truth for the boundary-M repack greedy contract. PR-CLI-2e
(L3–L6 + `stack_runner` relocation) is a pure relocation that MUST preserve the behavior fixed here.

---

## Goal

PR-B is an **algorithm enhancement** (not a relocation, not a pure formalization): maximize asteroid
mining yield by placing the highest-yield canonical bundle **`m3e_01` (miner + 3 extensions)** along
the outer rim, degrading gracefully where the field is too shallow, while keeping all mining/extension
equipment strictly on the field and using the exterior void only for output stub + transport route.

## Work classification

`contract change` + `implementation change` (algorithm enhancement). Tests authored first (red), then
implementation turned them green; see [Acceptance matrix](#acceptance-matrix).

---

## Behavior contract (normative)

| ID | Rule |
|----|------|
| C1 | M extractor **and** E extensions never sit in exterior void. All equipment cells ⊆ `field_cells`. |
| C2 | The miner anchor is an outer-rim field cell adjacent to external void (rim anchor `void_dirs`). |
| C2-1 | The `m3e_01` footprint reaches up to **4 field cells inward** (miner at depth 0 + extensions at depth 1..3). |
| C3 | `belt`/`pipe` (the M output stub + route path) MAY be installed in the external void. |
| C4 | The route probe MUST NOT fail solely because no belt is preinstalled. |
| C5 | A transport route MAY cross field cells, but field is **lower priority** than void: `step_cost` field = `FIELD_ROUTE_COST` (25) vs void = `EXTERIOR_ROUTE_COST` (1). Committed equipment is a hard blocker (`step_cost = None`). |
| C6 | Greedy-committed placements MUST surface in append / provisional overlay / post-summary metrics / replay segment. |
| C7 | The algorithm runs in **Layer 3** (`layer_03_rim_greedy_placement`). **Layer 4 remains disabled** (`Layer04DisabledResult.superseded()`). |
| C8 | This PR does not touch PR-CLI-2e / core relocation. |

## Bundle layout (m3e_01)

- Lab raw grid convention (`cardinal_map`): north decreases `y`. Output direction delta
  `CARDINAL_DIR_DELTA[output_dir]` points from the anchor toward the void.
- Miner occupies the anchor (depth 0). Extensions form a **straight inward chain** opposite the void
  normal: extension at depth `k` = `anchor - k * delta(output_dir)`, for `k = 1..extension_count`.
- The M output stub is `anchor + delta(output_dir)` (one void cell on the void side).
- **Decoded topology of `m3e_01` is a linear inward chain** (`branch_count == 0`), confirmed by audit
  against `miner_seed_constants` / `miner_seed_intrinsic_difficulty` and
  `tests/unit/asteroid_lab/test_miner_seed_intrinsic_difficulty.py::test_linear_m3e_01_tier_four`.
  This PR therefore defines the canonical L3 `m3e_01` footprint as a straight inward chain.

### Degradation (3 → 2 → 1)

- Degradation is handled **inside the layout** (`layout_seed_at_anchor`), not via separately-named
  fallback seeds. Extensions are appended inward until the first non-field cell, then truncated.
- The committed placement records the **actual** extension count as `len(extension_cells)` — no new
  contract field is added; intent (`seed_id = "m3e_01"`) and actual placement are separate.
- If zero extensions fit inward (1-deep stub-only rim), the layout rejects cleanly with
  `RimGreedyRejectReason.FOOTPRINT_OUT_OF_FIELD`.

```text
seed intent     = m3e_01 (miner + up to 3 extensions)
actual placement = miner + min(3, inward_field_depth) extensions
```

## Seed catalog + priority

- `DEFAULT_GREEDY_SEEDS = (GreedyMinerSeed("m3e_01", intrinsic_priority_rank=1, miner_count=1, extension_count=3),)`.
- Yield preference ("install the larger bundle first") is provided by the existing sort tiebreak
  `-extension_count` in `sort_seeds_by_priority`; with a single default seed, inter-seed ordering is
  moot and degradation is internal.
- **Known follow-up (out of PR-B scope):** `GreedyMinerSeed.intrinsic_priority_rank` sorts with
  `-rank` (higher value first), which is the inverse of the canonical `intrinsic_priority_score`
  ("lower score = higher priority", m3e_01 = score 211 / rank 1). With one default seed this does not
  affect behavior; unifying the rank/score convention is deferred to a separate PR.

## Replay multi-extension rotation (regression)

Replay resolves each extension's rotation against its **chain parent**, not the miner:

```text
ext1 → miner, ext2 → ext1, ext3 → ext2
```

`layer03_rim_greedy_segment._parent_coord_for_extension` returns `extension + delta(output_dir)`
(always a 4-neighbor), so `placement_extension_rotation` resolves for chained extensions. Before this
fix, ext2/ext3 fell back to the (non-adjacent) anchor and raised `ValueError`. A straight inward chain
shares one extension rotation. Regression:
`tests/unit/asteroid_lab/replay/test_layer03_rim_greedy_segment.py::test_m3e_chain_extension_rotations_resolve_without_error`.

---

## Acceptance matrix

Tests: `tests/unit/asteroid_lab/layers/test_layer_03_boundary_m_repack_acceptance.py`
(fixtures: `tests/unit/asteroid_lab/layers/fixtures/layer_03_deep_rim_map.py`).

| Contract | Test |
|----------|------|
| C2-1 / C1 / C3 layout | `test_m3e_layout_places_three_extensions_inward`, `test_m3e_extensions_and_miner_stay_in_field`, `test_m3e_output_stub_is_external_void`, `test_m3e_footprint_depth_at_most_four` |
| Degrade 3→2, 3→1 | `test_m3e_degrades_to_two_extensions_when_inward_field_is_short`, `test_m3e_degrades_to_one_extension_when_inward_field_is_short` |
| C1/C6 run-level | `test_run_commits_m3e_bundle_with_three_extensions`, `test_committed_placements_appear_in_overlay_and_metrics` |
| C4 route w/o preinstalled belt | `test_route_probe_succeeds_without_preinstalled_transport` |
| Actual extension_count after degrade | `test_committed_placement_records_actual_extension_count_after_degrade` |
| Yield preference | `test_greedy_prefers_larger_bundle_to_maximize_yield` |
| Default seed | `test_default_seed_catalog_is_m3e_01_with_three_extensions` |
| C5 field route costed / hard blocker | `test_field_route_is_allowed_but_costed_higher_than_void` |
| C7 runs in L3 / L4 disabled | `test_algorithm_runs_in_layer_3`, `test_layer4_remains_disabled` |
| Replay chained-extension rotation | `test_m3e_chain_extension_rotations_resolve_without_error` (replay file) |

---

## Verification

**Gate A (Lab gate):**

```powershell
python -m pytest tests/unit/asteroid_lab/layers/ -v
```

Result: passed.

**Additional replay regression:**

```powershell
python -m pytest tests/unit/asteroid_lab/replay/ -v
```

Result: passed.

**Combined local check:**

```powershell
python -m pytest tests/unit/asteroid_lab/layers/ tests/unit/asteroid_lab/replay/
```

Result: 173 passed, 2 warnings.

**Lint / format:**

```powershell
python -m ruff check <changed L3/replay/test modules>   # passed
python -m black --check <changed test/fixture modules>  # passed
```

**Type check:**

```powershell
python -m mypy <changed L3 + replay modules>
```

Result: Success, 13 files. Note: repo-wide `mypy django_apps config src` is NOT claimed here; the
project has a pre-existing repo-wide mypy baseline (see CLI-first checklist PR-CLI-2d note). Run it
separately under the PR full gate if/when publishing.

**Gate C smoke (evidence only).** `ASTEROID_LAB_LAYER_02_SOLVER_ENABLED = True` is already the default;
the run-solver path (`run_layer02_solver_for_project`) DOES run L3 (the settings comment "L3–L5 not run"
is stale). No deterministic project fixture slug exists (only gene/pattern seeders), and incidental
local-DB slugs are forbidden, so the manual `run_solver --slug` DB smoke is recorded **not reproducible**.
Deterministic Gate-C-equivalent evidence is used instead — fixture-based runtime tests that drive the
full run-solver L3 path with the m3e_01 default:

```powershell
python -m pytest tests/unit/asteroid_lab/test_solver_runtime_entry_layer02.py tests/unit/asteroid_lab/test_run_solver_management_command.py tests/unit/asteroid_lab/test_lab_replay_timeline_layer03_runtime.py -v
```

Result: 7 passed. Evidence only; MUST NOT be reused as solver/algorithm input. See plan checklist
[Phase 6](../plans/2026-05-30-layer-03-boundary-m-repack-greedy/checklist.md).

---

## Files

| Path | Role |
|------|------|
| `layers/layer_03_rim_greedy_placement/seed_orient.py` | `layout_seed_at_anchor(extension_count)` + inward chain + degrade |
| `layers/layer_03_rim_greedy_placement/greedy_seed.py` | `DEFAULT_GREEDY_SEEDS` = single `m3e_01` (ext3) |
| `layers/layer_03_rim_greedy_placement/greedy_pass1.py` | pass `seed.extension_count` to layout; full footprint reservation |
| `layers/layer_03_rim_greedy_placement/greedy_pass2.py` | re-derive committed layout with `seed.extension_count` |
| `replay/layer03_rim_greedy_segment.py` | chain-parent extension rotation (`_parent_coord_for_extension`) |
| `tests/unit/asteroid_lab/layers/test_layer_03_boundary_m_repack_acceptance.py` | acceptance locks |
| `tests/unit/asteroid_lab/layers/fixtures/layer_03_deep_rim_map.py` | deep/shallow rim fixtures |
| `tests/unit/asteroid_lab/replay/test_layer03_rim_greedy_segment.py` | m3e chain rotation regression |

## Risks

- `uncertain:` seed rank/score convention mismatch (documented above); no behavioral impact with the
  single default seed; unify in a follow-up PR.
- `assumption:` straight inward chain ⇒ all extensions share one rotation, so computing rotation
  against a parent-as-miner is geometrically correct (covered by the replay regression test).
- Branched `m3e_01` topology is excluded by audit; if a future canonical pattern is branched, this
  contract must be revised before reuse.
