# PR-CLI-2f — Decode / Cleanup / Reconstruction Pipeline Core Move

**Type:** refactoring (relocation)
**Depends on:** PR-CLI-2e (L3–L6 + stack_runner in core)
**Enables:** PR-CLI-3b (full pure CLI `run` — was previously blocked on this move)
**Branch (suggested):** `feat/asteroid-cli-first-pipeline-move`

---

## Why this PR exists (inserted 2026-05-30, 2nd-review follow-up)

PR-CLI-3b's premise is *"`run` executes decode → cleanup → reconstruction → in-core `stack_runner`
end-to-end with **no Django required**"*. An empirical audit on the post-2e branch
(`feat/asteroid-cli-first-l3-stack-move` @ `af59dc0a`) showed this premise is **not yet satisfiable**:

| Stage | Algorithm body location (today) | Core today |
|-------|----------------------------------|------------|
| decode (`decode_copy_string`) | `django_apps/asteroid_lab/adapters/decode_adapter.py` | port stub only |
| normalize (`normalize_decoded_blueprint`) | `django_apps/asteroid_lab/adapters/normalization.py` | — |
| snapshot (`build_decoded_blueprint_snapshot`) | `django_apps/asteroid_lab/snapshots/decoded_blueprint_snapshot.py` | — |
| cleanup (`deconstruct_snapshot`) | `django_apps/asteroid_lab/cleanup/pipeline.py` | DTO only |
| reconstruction (`run_topology_reconstruction`) | `django_apps/asteroid_lab/reconstruction/pipeline.py` | DTO + `complete_map` merge only |

If PR-CLI-3b tried to assemble the full run from core, `run_stack.py` would have to import
`django_apps.asteroid_lab.*` → **BA-1 violation**. Doing the move *inside* 3b would mix a large
algorithm relocation with CLI run + artifact writer + replay_core in one PR → **BA-2 violation**
(no monolithic move). Therefore the pure-input pipeline move is split into its own PR-CLI-2f and
sequenced **before** 3b. (Decision: architect "C → A", 2026-05-30.)

## Goal

Relocate the **decode + cleanup + reconstruction execution pipeline** (and its pure dependency
closure + DTOs) into pure core (`src/shapez2_factory/**`), so that core can compute
`copy-code / decoded-JSON → cleanup → ReconstructionCompleteMap` with **zero `django_apps` / `django`
import**. Django keeps ORM input loading, persistence, web/replay shaping, and observability sinks
(settings/file I/O) only — via shims that re-export the moved core symbols.

## Behavior contract

- `deconstruct_snapshot` / `run_topology_reconstruction` / `decode_copy_string` /
  `normalize_decoded_blueprint` / `build_decoded_blueprint_snapshot` produce **byte-identical**
  results to post-2e master (pure relocation; no algorithm change).
- Core pipeline emits **no boundary JSONL and reads no settings** itself; observability is delivered
  via an **injected trace/sink Protocol** (default no-op) — Django wires the file/settings sink.
- All existing `tests/unit/asteroid_lab/` decode / cleanup / reconstruction tests stay green through
  the Django shim paths (zero test churn target).
- Purity gate has **zero `django_apps` exceptions** after the move.

## Non-goals

- No algorithm tuning of decode / cleanup / reconstruction.
- No CLI run wiring (that is PR-CLI-3b).
- No capacity-envelope move unless required by 3b's L2 real-planning path — see "Open item" below;
  default is to defer it to 3b.

---

## Move set — CONFIRMED by Step 1 audit (2026-05-30): 15 modules

> **Audit precedent:** mirror PR-CLI-2a/2c/2d — per module confirm zero `django`/ORM/settings import,
> copy to core, replace original with explicit-name shim (never `*`, never redefine). Step 1 confirmed
> **none** of the 15 algorithm bodies import `django`/ORM/settings directly; the only side-effect is
> `boundary_jsonl` (NOT in the move set — see split below).

### DTOs — already core (verify only, NO move)

Step 1 confirmed all decode/snapshot DTOs are **already in core** (moved in PR-CLI-2e):
`RawDecodedBlueprintDTO`, `NormalizedBlueprintDTO`, `DecodedBlueprintSnapshotDTO` →
`src/shapez2_factory/domain/asteroid_lab/service_dtos.py`; `DecodedCellDTO` →
`domain/asteroid_lab/decoded_cell.py`. `django_apps/asteroid_lab/services/dto.py` is already a shim.
**No DTO move in 2f** — Step 2 only re-verifies their presence / shim identity.

### Decode / normalize / snapshot (5)

| From | To | Kind |
|------|-----|------|
| `adapters/decode_adapter.py` (`decode_copy_string`, `AsteroidLabCopyDecodeError`) | `adapters/asteroid_lab/copy_decode_adapter.py` (core) | pure base64/gzip/json |
| `adapters/normalization.py` (`normalize_decoded_blueprint`) | core adapter | pure (→ core `coord_frames`/`copy_json_coords`) |
| `snapshots/decoded_blueprint_snapshot.py` (`build_decoded_blueprint_snapshot`) | `domain/asteroid_lab/snapshots/` (core) | pure after sink split (1 `emit_boundary_jsonl` site) |
| `snapshots/cell_classifier.py` (`classify_blueprint_entry`) | core | **pure stdlib** (no imports beyond `__future__`) — newly added to set |
| `snapshots/copy_json_coords.py` (`entry_island_raw_coord`, `entries_have_explicit_raw_x_zero`) | core | pure (→ core `coord_frames`) — newly added to set |

### Cleanup (1)

| From | To | Kind |
|------|-----|------|
| `cleanup/pipeline.py` (`deconstruct_snapshot`) | `domain/asteroid_lab/cleanup/pipeline.py` | pure after sink split (1 `emit_boundary_jsonl` site) |

### Reconstruction closure (9)

| From | To | Kind |
|------|-----|------|
| `reconstruction/pipeline.py` (`run_topology_reconstruction`, `reconstruct_snapshot`) | `domain/asteroid_lab/reconstruction/pipeline.py` | pure after sink split + `display_map` repoint |
| `reconstruction/confidence.py` (`apply_confidence_to_result`) | core | pure (lazy `complete_map` → already core) |
| `reconstruction/fill.py` | core | pure |
| `reconstruction/flood_fill.py` (`external_reachable`) | core | pure |
| `reconstruction/island.py` (`stamp_islands_uniform`) | core | pure |
| `reconstruction/perimeter_closing.py` (`close_diagonal_leaks`) | core | pure (→ `shell`) |
| `reconstruction/shell.py` (`_strict_bbox_interior_cells`) | core | pure — newly added to set |
| `reconstruction/trace.py` (`ReconstructionTraceCollector`, `ReconstructionTraceEvent`) | core | **pure** (grid + stdlib); trace seam, separate from boundary sink |
| `reconstruction/topology_contract.py` (`build_normalized_reconstruction_topology`, `decode_shapez_copy_string`) | core | pure (→ moved decode/normalize/snapshot) |

> **`reconstruction/pipeline.py` lazy `display_map` import (line ~488) — NOT a blocker.** The two
> helpers it pulls (`replace_miners_with_synthetic_fields`, `replace_extensions_with_synthetic_fields`)
> are **already in core** `domain/asteroid_lab/reconstruction/complete_map_merge.py` (PR-CLI-2c split).
> Action: **repoint the lazy import to `complete_map_merge`** (one-line); the Django viewer
> `reconstruction/display_map.py` stays Django.

> **Already in core from PR-CLI-2c/2e (verify, do NOT re-move):** `cleanup/result`,
> `reconstruction/{evidence,grid,result,acceptance_topology,rim_topology,complete_map,complete_map_merge}`,
> `snapshots/{transport_components,coord_frames,grid_contract}`, `services/dto`→`service_dtos`,
> `decoded_cell`.

### Target core paths (canonical; tests reference these — keep stable through Step 4)

Follow the established flat core convention (PR-CLI-2c moved `coord_frames`/`grid_contract`/
`transport_components` directly under `domain/asteroid_lab/`, not under a `snapshots/` subdir):

```text
src/shapez2_factory/domain/asteroid_lab/copy_decode.py              # decode_copy_string, AsteroidLabCopyDecodeError
src/shapez2_factory/domain/asteroid_lab/normalization.py           # normalize_decoded_blueprint
src/shapez2_factory/domain/asteroid_lab/decoded_blueprint_snapshot.py  # build_decoded_blueprint_snapshot
src/shapez2_factory/domain/asteroid_lab/cell_classifier.py         # classify_blueprint_entry
src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py        # entry_island_raw_coord, entries_have_explicit_raw_x_zero
src/shapez2_factory/domain/asteroid_lab/cleanup/pipeline.py        # deconstruct_snapshot
src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py            # run_topology_reconstruction, reconstruct_snapshot
src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
src/shapez2_factory/domain/asteroid_lab/reconstruction/flood_fill.py
src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py
src/shapez2_factory/domain/asteroid_lab/reconstruction/perimeter_closing.py
src/shapez2_factory/domain/asteroid_lab/reconstruction/shell.py
src/shapez2_factory/domain/asteroid_lab/reconstruction/trace.py
src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
```

> The PR-CLI-3b-referenced `adapters/asteroid_lab/copy_decode_adapter.py` (if kept) becomes a thin
> re-export of `domain/asteroid_lab/copy_decode.py` — decode is pure (no I/O), so the body lives in
> domain; any "adapter" is a thin wrapper. (3b concern, not 2f.)

### BLOCKING split — `observability/boundary_jsonl.py`

`boundary_jsonl.py` lazy-imports `from django.conf import settings` (in `_repo_base_dir`) and performs
env reads + file I/O. It **stays in Django** and **must NOT move to core** (BA-1).

**Step 1 confirmed the side-effect is localized — exactly 3 `emit_boundary_jsonl` call sites** across the
moving modules: `cleanup/pipeline.py:56`, `reconstruction/pipeline.py:127`,
`snapshots/decoded_blueprint_snapshot.py:179` (+ one pure helper `summarize_cell_kind_transitions` used
at `reconstruction/pipeline.py:126` to build the payload). Not widely scattered → an injected sink is
clean. `summarize_cell_kind_transitions` is pure and moves to core (payload built in core; emit happens
in the Django sink).

**Approach (mirror PR-CLI-2e stack_runner "Approach A" — core ignorant):**

- Define a pure **`BoundaryTraceSink` Protocol** (or reuse `ReconstructionTraceCollector` if pure) in
  core; the moved pipelines accept an **injected sink** (default = no-op core sink). Core never reads
  settings, never opens files.
- The Django side keeps `boundary_jsonl.py` (settings + file I/O) and passes a sink adapter that
  forwards to `emit_boundary_jsonl` when `ASTEROID_LAB_BOUNDARY_JSONL` is enabled.
- `reconstruction/trace.py` (`ReconstructionTraceCollector`) — audit: if pure, move to core; it is the
  natural seam for the sink.

**Forbidden in core:** `from django.conf import settings`, `emit_boundary_jsonl` import, any file/dir
path resolution against `BASE_DIR`, any `os.environ` gate that selects a Django path.

### Step acceptance gate

```text
[ ] core decode/cleanup/reconstruction import no django/django_apps/config/settings (purity gate + Django-free subprocess import test)
[ ] boundary observability delivered by injected sink (default no-op); Django sink writes JSONL when enabled; `summarize_cell_kind_transitions` pure in core
[ ] DTOs already in core (verify only); `services/dto.py` shim identity holds — no DTO move
[ ] `reconstruction/pipeline.py` lazy `display_map` import repointed to core `complete_map_merge`
[ ] all 15 original module paths keep explicit-name shims (no `*`, no redefine)
[ ] reconstruction leaf closure fully resolved (no Django sibling left in a core import chain)
[ ] tests/unit/asteroid_lab decode+cleanup+reconstruction suites green unchanged via shims
[ ] purity gate has zero django_apps exceptions
```

---

## Tasks

- [x] **Step 1 (audit):** DONE 2026-05-30 — confirmed 15-module move set (no wildcard), zero direct
  `django`/ORM/settings import in any algorithm body, boundary side-effect localized to 3 emit sites,
  DTOs already core, `display_map` helpers already core. No stop condition triggered. (See chat audit
  report + deltas folded into this doc.)
- [ ] **Step 2 (TDD, tests-first → red):** add the 5 failing tests below (no DTO move — DTOs already
  core, so this step only asserts the *target* core pipeline modules exist + are pure):
  1. `test_pipeline_importable_without_django.py` — subprocess, `DJANGO_SETTINGS_MODULE` unset, import
     core decode/cleanup/reconstruction.
  2. `test_recon_pipeline_no_boundary_jsonl_import.py` — AST gate: core pipeline modules do not import
     `django.conf` / `observability.boundary_jsonl` / `django_apps`.
  3. `test_pipeline_core_parity.py` — core decode→cleanup→recon `complete_map` == Django path.
  4. shim-identity extension — 15 moved modules' key public symbols `is`-identical core↔shim.
  5. Django-free full `decode→cleanup→recon` subprocess (3b prerequisite).
- [ ] **Step 3 (BLOCKING):** introduce core `BoundaryTraceSink` Protocol (default no-op); move pure
  `summarize_cell_kind_transitions` to core; rewire the 3 emit sites to inject the sink; Django sink
  adapter forwards to `emit_boundary_jsonl`. (Greens test 2.)
- [ ] **Step 4 (move):** copy the 15 modules to core; rewrite intra-core imports to core paths; repoint
  `reconstruction/pipeline.py` lazy `display_map` import → core `complete_map_merge`; replace originals
  with explicit-name shims. (Greens tests 1, 4, 5.)
- [ ] **Step 5 (TDD, parity):** green `test_pipeline_core_parity.py` — decode→cleanup→recon on a fixture
  copy code produces a `ReconstructionCompleteMap` identical (field cells / external void / counts)
  to the Django path; Django-free subprocess run of the full pipeline.
- [ ] **Step 6:** full `tests/unit/asteroid_lab/` suite green (parity, zero churn); purity gate +
  import-matrix + shim-identity gates green.
- [ ] **Step 7:** ruff + `mypy src` + black; reconstruction narrow gate
  (`scripts/test_reconstruction_narrow.ps1`).

## Tests / verification

```powershell
python -m pytest tests/unit/asteroid_lab/reconstruction/ tests/unit/asteroid_lab/ -v
python -m pytest tests/unit/shapez2_factory/ tests/unit/architecture/test_shapez2_factory_core_purity.py -v
powershell -File scripts/test_reconstruction_narrow.ps1
python -m ruff check src/shapez2_factory
python -m mypy src
```

> **Worktree env note (from 2e):** worktree runs require `PYTHONPATH=<worktree>/src` because the
> editable install resolves to the main checkout. Confirm CI/editable wiring at merge time.

## Risks

- `invariant:` reconstruction output is terrain SoT, **never** solver/algorithm input — relocation
  must not change this contract.
- `invariant:` core emits no observability side effects; sink injection only (no settings/file I/O).
- `uncertain:` size of the reconstruction leaf closure — Step 1 audit fixes the exact list; keep PR
  scoped to relocation (no algorithm edits) to bound risk.
- `assumption:` `reconstruction/trace.py` is pure enough to host the sink seam; if it carries Django
  coupling, split it like `boundary_jsonl`.
- Merge-conflict risk if the reconstruction track reopens — land fast after audit.

## Open item — RESOLVED by Step 1 audit: out of 2f scope

- **Capacity envelope** (`services/reconstruction_capacity_summary.build_reconstruction_capacity_envelope`)
  and the **game-data port** are **confirmed NOT in the decode→cleanup→reconstruction closure** — they
  are L2 *real-planning* inputs (core `run_layer_02_exterior_transport` needs `capacity_envelope` +
  `throughput_target_percent` + `rules`). **Deferred to PR-CLI-3b** (L2 wiring, not input pipeline).
  If 3b's L2 wiring later needs the envelope builder in core, that is a 3b task, not 2f.

## Done criteria

- decode + cleanup + reconstruction pipeline (+ DTOs + leaf closure) in pure core; observability via
  injected sink; Django shims preserve public surface; parity + Django-free subprocess green; purity
  gate zero `django_apps` exceptions; behavior identical to post-2e master.
