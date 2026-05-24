# Asteroid Lab — Runtime Replay Wiring Plan

Role: Asteroid Lab Runtime Replay Wiring Architect

**Document status:** ACTIVE. **Product replay North Star (2026-05-19):** [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md) — dual-track deprecated; dual-track paragraphs in §1·§9 of this document are pre-migration snapshots. §12 **Sequence 12F·12G·12H** implemented (2026-05-17). **Sequence 12I** has **HUD vocabulary hardening** draft only in §12; implementation in separate PR. **Sequence 12J** (POST `optimization_replay_attach` dedicated HUD line) implemented via Lab template·`asteroid_miner_layout_lab.js`·tests·§12J doc (2026-05-17). **Sequence 12K** (POST attach `diagnostic` scalar·`evolution_failed` stage observation) implemented via §12K·code·tests (2026-05-17). **Sequence 12L** (raw↔dense forbidden at optimization boundary·AST) reflected 2026-05-17. **PR-F (2026-05):** replay/Lab is island-local `(x,y)` only; `server_coords`·`server_xy_params` **removed**. Other sequences are for design·boundary fixation.  
**Scope:** Only how to safely connect optimization replay to Lab persistence·UI read paths.  
**Forbidden:** This document alone does **not** change **solver·replay event semantics·DTO·test-only fixture parser behavior**. Actual wiring implementation proceeds in separate PR·after approval.

> **FIXTURE ENVELOPE SCHEMA ≠ RUNTIME PERSISTENCE SCHEMA**  
> Test golden envelope (`replay_summary.replay_truncated` + top-level `truncation_reason`) and runtime persist (frame list + frame `metrics` aggregation) are **different schemas**. On implementation, top-level persist of `payload["truncation_reason"]` is **forbidden** — §6.1 canonical.

---

## 1. Purpose

What is fixed so far is the **output contract**. The next runtime work exposes existing optimization replay **output** to persistence·UI read paths while fixing boundaries so replay does not leak as **solver input**.

This document's purpose:

```text
- what to store where
- what and how UI reads
- what remains output-only forever
- product replay converges to single replay timeline (Phase 9; dual-track deprecated)
```

is fixed in documentation before implementation. **Product replay canonical:** [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md).

---

## 2. Current contracts

The following are **already fixed by implementation·tests**.

| Contract | Location·means (summary) |
|------|------------------|
| Optimization JSON golden v0 | `tests/fixtures/shapez_asteroid/optimization/` |
| Optimization fixture JSON parser | `tests/unit/shapez_asteroid/fixtures/optimization_json.py` |
| Replay-track JSON golden v0 | `tests/fixtures/shapez_asteroid/replay/` |
| Replay JSON parser (fixture envelope) | `tests/unit/shapez_asteroid/fixtures/replay_json.py` |
| Long replay stitching JSON v0 | `tests/fixtures/shapez_asteroid/replay_long/` |
| `replay_truncated` / `truncation_reason` (fixture envelope pair) | golden + `replay_json` contract |
| `commit.survivability_summary` replay frame | aligned with domain events·regression tests |
| Lab / Optimization **dual-track** replay policy | **Deprecated** → replay timeline ([`asteroid_lab_09_replay_timeline`](asteroid_lab_09_replay_timeline.md)) |

**Important:** Fixture parsers·golden JSON above are **contract·regression only**. Do not attach same parser/envelope to solver input path in production.

### 2.1 Runtime pieces already present (code baseline, 2026-05-21)

- **Composition·payload:** `django_apps.asteroid_lab.services.lab_replay_timeline_payload.build_lab_replay_frames_for_project` — Lab `ReplayTrack` + solver runtime segment → single timeline frames + track `metrics`.
- **RTTP v0.2 + 3B-S (2026-05-23):** Pipeline milestones persist on **`{run_key}:rttp`** (`rttp_optimization_track_key`); `get_latest_lab_replay_track_for_project` **excludes** `rttp-*` / `:rttp` tracks. **`lab_replay_frames_json`** composes inspection/reconstruction + **interleaved full-snapshot RTTP frames** via `lab_rttp_snapshot_compose` (canonical `rttp.*` event types; no `inherited_snapshot`). See [`2026-05-23-rttp-v0.2-replay-parity-design.md`](../../docs/superpowers/specs/2026-05-23-rttp-v0.2-replay-parity-design.md) § H2 and [`2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md`](../../docs/superpowers/specs/2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md).
- **UI:** `django_apps.web.services.asteroid_lab_page_context` + `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` — **`updateReplayTruncationHud`** displays track `metrics.replay_truncated` / `metrics.truncation_reason` / `diagnostic_reason` (display-only).
- **Track `metrics`:** `_track_metrics_from_serialized_frames` — `replay_truncated` is frame OR; `truncation_reason`·`dropped_frame_count` read from **last frame** `metrics` (§6.1).
- **Deprecated (dual-track):** `build_optimization_replay_track_payload`, `renderOptimizationReplayHud`, `#lab-optimization-replay-status` — removed·unused; do not reference in new code.

### 2.2 Fixture envelope vs runtime persist shape

| Item | Golden long replay (`replay_long/`) | Current persist + UI |
|------|-----------------------------------|---------------------|
| `schema_version` | envelope top-level | **absent** in persist (frame list only) |
| `replay_summary` / `replay_event_sequence` | explicit in envelope | **recomputed** by `build_lab_replay_frames_for_project` |
| `truncation_reason` | envelope top-level (pair contract) | **After 12F v0:** frame `metrics` → track `metrics.truncation_reason` aggregation (§6.1 below) |

This table separates **test envelope ≠ runtime persist** to prevent mistakenly treating fixture parser as production parser.

---

## 3. Runtime boundary

Fix the following **explicitly**.

```text
Optimization replay is output-only.
Persisted replay must never be used by solver, candidate generation, route probe,
evolutionary search, incremental commit, or validation.
```

### 3.1 One-way data flow

```text
Optimization run / post-inspection
  → (memory) OptimizationReplayFrame sequence
  → (storage) SolverRun.config_json["optimization_replay_frames"]  # output only
  → (read) deserialize → build track → Lab context["optimization_replay"]
  → (display) metadata·overlay observation UI
```

### 3.2 Layer responsibilities

| Layer | Responsibility |
|--------|------|
| `shapez_asteroid.optimization` | events·frame DTO·serialization dict (business rules) |
| `asteroid_lab` | merge output storage into `SolverRun`, import boundary |
| `web` (page context) | read-only adapter: empty track + `metrics.optimization_replay_diagnostic_reason` on deserialize failure (12G, metadata only) |
| test fixture parser | regression canonical only; production dependency **not recommended** |

### 3.3 Sequence 12L — Server coordinate boundary (optimization input)

```text
After OptimizationInput (and candidate·route·evolution·replay recording using same coordinates), use Server X/Y only.
raw blueprint X/Y·dense conversion only at decode/import·cleanup/reconstruction boundary.
django_apps.shapez_asteroid.optimization package and asteroid_lab_post_inspection_evolution.py:
`server_coords` bridge **removed** (PR-F). replay/web use `ReplayProjectionContext` island identity only.
copy JSON `X==0` valid in island-local; lab world map has no `x==0` column — do not confuse frames.
```

---

## 4. Persistence target

### 4.1 Key names (match code canonical)

**Keys used by current implementation (no rename):**

```text
SolverRun.config_json["optimization_replay_frames"]
```

Constant: `django_apps.shapez_asteroid.optimization.optimization_ui_payload.SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY` (`"optimization_replay_frames"`).

**Not added in 12F v0:** Unless a separate envelope is introduced, **do not add** sibling keys below (implementers must not add arbitrarily).

```text
optimization_replay_schema_version   # not introduced in v0
optimization_replay_truncated       # not introduced as sibling in v0
optimization_replay_truncation_reason # not introduced as sibling in v0
```

Truncation·schema handled only via **frame list + track metrics** model in §6·§7. Envelope·schema sibling·extra keys reviewed only in **separate migration / compatibility PR**.

### 4.2 **12F v0 decision (schema_version)**

Unless a separate envelope is introduced, do **not** add `optimization_replay_schema_version` sibling key. v0 runtime guard validates existing `optimization_replay_frames` list via `deserialize_optimization_replay_frames_from_json`. Envelope or schema sibling introduction handled only in **separate migration/compatibility PR**.

---

## 5. Write path

```text
Run / Lab inspection flow
→ inspection·Lab replay success (existing pipeline)
→ bounded optimization run
→ optimization replay frames produced (memory)
→ JSON-safe serialization·only if 12F v0 guard passes
→ attach output payload only to config_json["optimization_replay_frames"]
```

Replay data does **not** flow back to the solver.

---

## 6. Read path

```text
page context / UI payload builder
→ read optimization_replay_frames from config_json
→ deserialize + (after 12F) additional shape/pair validation
→ expose optimization_replay track to template·json_script
→ UI displays metadata/overlay only per dual-track policy
```

### 6.1 `replay_truncated` and `truncation_reason` (**12F v0 decision**)

**Do not store `truncation_reason` as `SolverRun.config_json` sibling.**

- **Publish:** On frames indicating truncation, set `replay_truncated: true` and `truncation_reason: <non-empty string>` **together** in `metrics`.
- **Aggregate:** `_track_metrics_from_serialized_frames` (`lab_replay_timeline_payload.py`) lifts from frame `metrics` to **`metrics.truncation_reason`**. When `replay_truncated == true`, reason·`dropped_frame_count` canonical from **last frame** `metrics` (code L204–212).
- **v1 alternative:** `config_json` sibling is design deferral; revisit only in separate doc/PR if needed.

**Track `metrics` pair contract (common basis for UI·guard):**

```text
track.metrics.replay_truncated == false  →  track.metrics.truncation_reason absent
track.metrics.replay_truncated == true   →  track.metrics.truncation_reason is non-empty string
```

UI uses `replay_truncated` for truncation badge, `truncation_reason` for detail·tooltip only; **does not change replay event semantics.**

### 6.2 Relationship to fixture envelope pair

- **Test golden:** `replay_summary.replay_truncated` + top-level `truncation_reason` (regression).
- **Runtime:** persist is frame list only; pair aligned via **frame `metrics` → track `metrics`**.

---

## 7. Malformed payload policy

Required behavior:

```text
Malformed optimization replay payload must not crash Lab page.
Malformed payload must be dropped or replaced by empty replay payload.
A diagnostic reason should be exposed for UI/debug.
Solver result must remain unchanged.
```

### 7.1 Diagnostic reason codes (**12G v0 implementation values**)

Read-only·metadata-only. Constant key: `django_apps.asteroid_lab.services.optimization_ui_payload.OPTIMIZATION_REPLAY_DIAGNOSTIC_REASON_METRIC_KEY` → track `metrics` field name **`optimization_replay_diagnostic_reason`**.

```text
missing_optimization_replay          # no optimization_replay_frames key in any SolverRun.config_json
empty_optimization_replay_frames     # key present but list empty ([])
invalid_optimization_replay_payload  # all frames skipped due to unknown event_type or shape mismatch
```

> **Read path (lenient)**: Uses `deserialize_optimization_replay_frames_lenient` — frames with unknown `event_type` are **individually skipped** and counted in `omitted_frame_count` metric. Sets `invalid_optimization_replay_payload` diagnostic only when entire track is empty. Strict validation (`validate_optimization_replay_frame_list_payload`) remains on **write (persist) path** only.

When some valid frames are skipped, track `metrics` adds `omitted_frame_count` (int).

On normal deserialize this field is **absent**. Does not participate in solver·replay semantics·ordering·aggregation.

### 7.2 UI exposure (12G / 12H)

- **12G:** Sets §7.1 string in `metrics.optimization_replay_diagnostic_reason` only when falling to empty track. **Does not participate in replay semantics·frame order.**
- **12H:** Lab template·`asteroid_miner_layout_lab.js` expose `replay_truncated` / `truncation_reason` / `optimization_replay_diagnostic_reason` as **display-only HUD** (`#lab-optimization-replay-status`, etc.). No sync·retry·payload mutation; on Run Solver JSON update client `replaceOptimizationReplayPayload` redraws HUD.

---

## 8. Truncation contract

- **Fixture:** `replay_json` — `replay_summary.replay_truncated` + top-level `truncation_reason`.
- **Runtime track:** §6.1 `track.metrics` pair.
- **No semantic change:** HUD is observation only; does not change commit/route/evolution semantics.

---

## 9. Dual-track UI policy — **Deprecated historical**

> **Do not apply to implementation·review·test design.** Product canonical: [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md).

<details>
<summary>Deprecated historical: Dual-track UI policy (expand)</summary>

```text
Lab replay owns map rendering.
Optimization replay owns optimization metadata/overlay observation.
No implicit index sync.
No implicit event-order sync.
Optimization replay controls must not mutate Lab currentFrameIndex
unless an explicit sync mode is introduced later (out of scope for v0).
```

</details>

---

## 10. Schema policy

**Document v0 (persist):**

```text
No separate optimization_replay_schema_version key.
deserialize_optimization_replay_frames_from_json + 12F v0 shape/truncation guard is center of structure validation.
```

**When envelope introduced later (separate PR):**

```text
optimization_replay_schema_version = 1  # example
unknown version → empty payload + diagnostic; no silent coercion
```

---

## 11. Explicit non-goals

```text
- No production solver input from replay
- No replay-driven optimization
- No implicit Lab/Optimization frame sync
- No UI sync mode (v0)
- No database migration unless existing config_json is insufficient
- No JSON fixture parser reuse as production parser unless explicitly reviewed
- No route/commit/evolution algorithm changes
- 12F-v0: no schema envelope / schema sibling / byte-size cap (12H adds **truncation·diagnostic HUD** display-only; semantics·sync unchanged)
```

---

## 12. Implementation sequence

### Sequence 12F — Persist frame-list guard v0

**Implementation status (v0, 2026-05-17): complete**

- **Guard·deserialize:** `validate_optimization_replay_frame_list_payload` and frame `metrics` truncation pair validation in `deserialize_optimization_replay_frames_from_json` in `django_apps.shapez_asteroid.optimization.optimization_ui_payload` (`replay_truncated == true` → non-empty `truncation_reason` in same `metrics`).
- **Track aggregation:** `build_optimization_replay_track_payload` sets `metrics.truncation_reason` only when `replay_truncated == true`; value is **first** non-empty reason in frame order (or `"unknown"` on in-memory inconsistency — persist path filtered on deserialize).
- **Write:** `persist_optimization_replay_frames_to_solver_run` skips save on guard failure after serialization. `attach_optimization_replay_frames_after_successful_replay_build` skips with `invalid_replay_payload` reason.
- **Recorder:** `OptimizationReplayRecorder` records `truncation_reason` together on cell·frame limit truncation (`max_replay_cells_per_frame`, `max_replay_frames`).
- **Scope maintained:** **No** `optimization_replay_schema_version` / `optimization_replay_truncated` / `optimization_replay_truncation_reason` **sibling**; **no** envelope·byte cap·migration; **12H** adds display-only HUD only (aligned with §11·§12).
- **12G preview:** Single diagnostic string such as `optimization_replay_diagnostic_reason` on read failure is 12G; 12F covers shape·truncation pair·track reason aggregation only.

**Tests (added·updated):** `tests/unit/shapez_asteroid/test_optimization_ui_payload.py` (guard·aggregation·deserialize), `tests/unit/shapez_asteroid/test_solver_optimization_replay_import_boundary.py` (solver package string non-reference), `tests/unit/asteroid_lab/test_optimization_replay_persist.py` (persist/attach/page empty track), Recorder assertion updates `test_optimization_replay.py`·`test_optimization_replay_skeleton.py`.

**Scope:**

- Keep `optimization_replay_frames` as sole optimization replay persist key.
- **List shape** validation before attach/read.
- Reject broken frame dicts.
- Require **continuous** `frame_index` (0..n-1).
- Allow only known `OptimizationReplayEventType` values for `event_type`.
- **Frame `metrics` truncation pair:** Frames with `metrics.replay_truncated == true` must have non-empty `truncation_reason` in **same frame** `metrics`. If aggregated `track.metrics` violates §6.1 pair, fix as **persist reject** or **empty track on read** (choose in implementation PR·lock with tests).
- On read path malformed → expose **empty optimization replay payload**.

**Out of scope (not in 12F-v0):**

```text
- schema envelope
- optimization_replay_schema_version sibling
- config_json truncation sibling keys
- DB migration
- payload byte-size cap
- excessive global dict key whitelist extension (follow-up PR if needed)
```

(Display-only **truncation·diagnostic HUD** introduced in **12H** via `asteroid_miner_layout_solver.html` / `asteroid_miner_layout_lab.js`; no replay semantics·Lab sync.)

### Sequence 12G — UI payload read adapter

**Implementation status (v0, 2026-05-17): complete**

- page context reads persisted frames (shape·truncation pair already fixed by `deserialize`/`validate` in 12F).
- On failure: empty payload + §7.2 diagnostic string (`optimization_replay_diagnostic_reason`, etc. — **12G implementation scope**).
- `metrics.truncation_reason` exposure per §6.1 (track aggregation complete in 12F).

### Sequence 12H — Truncation / diagnostic metadata HUD

**Implementation status (PR8 unified, 2026-05-19): partial**

- **Unified timeline:** Product replay is `lab_replay_frames_json` single track. dual-track `lab-optimization-replay-data` / `replaceOptimizationReplayPayload` / `renderOptimizationReplayHud` **unused**.
- **Template SSR:** `lab-replay-truncation-hud` (truncation·`diagnostic_reason`·`optimization_replay_diagnostic_reason`), `lab-optimization-replay-attach` (12J, POST attach only).
- **Client:** `updateReplayTruncationHud` · `renderOptimizationReplayAttachHud` · `replaceLabReplayPayload` update metrics/attach.
- **Forbidden (maintain):** Lab ↔ optimization implicit frame sync, metadata interaction (retry·repair), no solver·replay semantic changes.

### Sequence 12I — Optimization replay HUD vocabulary hardening (draft)

**Goal:** Separate **display strings·codes** on optimization replay HUD into **3 axes** `status` / `reason` / `diagnostic` so SSR·client re-injection (`replaceOptimizationReplayPayload`)·Python diagnostic contract do not mix. **Implementation not in this sequence scope** — this section fixes documentation canonical only.

**Non-goals (forbidden in 12I):** **Sync mode introduction** between Lab map replay and optimization overlay, **render/ownership changes** to `renderOptimizationReplayHud`·overlay pipeline, **frame index·event order tight coupling** for "full display" of observation overlay. Overlay **completeness** recorded only via **observation·metrics·manual QA** after implementation; this sequence does **not** reflect results in **documentation·test expectations** (no sync/render responsibility change).

#### 12I.1 3-axis definition (status / reason / diagnostic)

| Axis | Meaning (display·contract) | Source (approx.) | Notes |
|----|------------------|------------|------|
| **status** | User-facing summary: "track loaded normally / empty / truncated", etc. | **Derived** from track `metrics` `frame_count`, `replay_truncated`, empty vs non-empty payload, etc. | **Does not 1:1 map to solver·replay semantics.** HUD label only. |
| **reason** | **Domain reason** for truncation (e.g. `truncation_reason`, recorder limits) | frame `metrics` → track `metrics` aggregation (§6.1) | On §6.1 pair violation **read path → empty + diagnostic** (§7). |
| **diagnostic** | **Read adapter failure codes** for deserialize·shape·unsupported `event_type`, etc. | `metrics.optimization_replay_diagnostic_reason` and attach reason on **write skip** (12I.3 below) | **Metadata only**; does not participate in frame order·event interpretation (aligned with §7.1·12G). |

Three axes are **non-interchangeable**. UI must align **naming rules** identically in JS·SSR·Python so one axis string is not reused as another axis label.

#### 12I.2 JS `enum`/const mapping (draft)

- **Principle:** Place **display constant table** in `asteroid_miner_layout_lab.js` (and Lab-only bundle). Do not scatter string literals across template·HUD branches.
- **Minimum structure:** (1) **diagnostic codes** — fix same string set as §7.1 as `OPTIMIZATION_REPLAY_DIAGNOSTIC_*` or single object map. (2) **truncation / status badges** — bundle `replay_truncated`·`truncation_reason` display labels·tooltip keys as const.
- **i18n:** v0 may use fixed Korean/English strings but separate **code values (diagnostic)** from **display strings** so follow-up i18n PR swaps map only.
- **Forbidden:** Branches linking diagnostic strings to Lab replay index or map step (implicit sync, conflicts with §9·12H non-goals).

#### 12I.3 `optimization_replay_attach.reason` mapping (draft)

- **Scope:** Map **internal reason codes** left on guard failure·skip in **persist/attach write path** (document·log·optional meta) to **page-exposed** `optimization_replay_diagnostic_reason` in a **table**.
- **Principle:** attach reason is **operations·debug·regression test** first; need not expose verbatim to HUD. When exposed, use only codes already in §7.1 or **add new codes to §7.1 table first** then fix with JS const (prevent string drift).
- **Documentation deliverable (before implementation PR):** Recommended **mapping table** "attach reason → (optional) diagnostic → HUD display yes/no" under this section (single copy-pasteable table).

#### 12I.4 Malformed payload matrix (draft)

Below is **read path** matrix. Columns: input condition / expected track / `optimization_replay_diagnostic_reason` / `replay_truncated`·`truncation_reason` / page non-destructive. Implementation PR attaches **unit test name** per row.

| # | Input condition (config_json `optimization_replay_frames`) | Expected track | diagnostic (when present) | truncation axis | Notes |
|---|--------------------------------------------------------|-----------|------------------------|-----------------|------|
| M1 | key absent | empty | `missing_optimization_replay` | default false/absent per §6.1 pair | §7.1 |
| M2 | `[]` | empty | `empty_optimization_replay_frames` | same | |
| M3 | not a list·broken frame dict·discontinuous `frame_index`, etc. | empty | `invalid_optimization_replay_payload` | same | |
| M4 | `replay_truncated` and `truncation_reason` pair broken | empty | `invalid_truncation_contract` | blocked before aggregation | |
| M5 | unknown `event_type` | empty | `unsupported_or_unknown_event_type` | same | |
| M6 | (follow-up) envelope·`optimization_replay_schema_version` mismatch | empty | separate code (§10) | separate PR extends §7.1 | 12I **reserves row only**; code strings fixed with envelope PR |
| M7 | (follow-up) byte limit exceeded | empty or policy choice | follow-up | follow-up | linked to §14 open decision |

**Note:** M1–M5 code strings must match **§7.1 implementation values**. Matrix is **contract table**; update §7·§12I·tests together on implementation change.

#### 12I.5 Verification chain: persist → deserialize → `replaceOptimizationReplayPayload` → HUD preservation (draft)

- **Intent:** Regression that **same diagnostic·truncation·status display** persists whether read once after save or client calls `replaceOptimizationReplayPayload` on **Run Solver JSON update**.
- **Recommended test layers:**
  1. **Python:** persist fixture or inject `SolverRun.config_json` → `deserialize_optimization_replay_frames_from_json` + `build_optimization_replay_track_payload` → expected `metrics` snapshot.
  2. **Django page context:** extend existing `test_page_context_malformed_optimization_replay_does_not_crash` — HTML contains expected strings in **diagnostic·truncation placeholders** (SSR).
  3. **JS (optional·minimal):** after `replaceOptimizationReplayPayload`, HUD nodes remain and same normalize path — one unit or integration per **frontend build policy**.
- **Preservation definition:** "Preservation" is **display strings·visibility**, not to be confused with **frame count·event content** changing on JSON update. When optimization track is **intentionally emptied**, HUD matching empty state is normal.

#### 12I.6 Overlay completeness·sync (observation only)

- **Completeness:** "All cells/all events drawn on overlay" recorded only as **observation metrics** (log, screenshot, manual checklist). 12I does **not** document as **PASS/FAIL gate**.
- **Forbidden reconfirmation:** Frame index sync, matching Lab `currentFrameIndex` to optimization step, overlay layer ownership transfer, expanding `renderOptimizationReplayHud` responsibility — **all out of scope**. If issues appear, separate **bug report·sequence**.

**Implementation scope summary:** Bundle 3-axis vocabulary·JS const·attach↔diagnostic mapping table·M1–M7 matrix·chain tests in **one PR or consecutive 12I sub-PRs**; each PR must not violate §3 output-only·§11 non-goals. (§9 dual-track is historical — see replay timeline canonical.)

### Sequence 12J — Optimization replay attach HUD (POST write channel, separate line)

**Implementation status (2026-05-17): complete**

- **Goal:** Expose `Accept: application/json` POST response `optimization_replay_attach` `{ attached, reason }` on Optimization Replay panel as **`#lab-optimization-replay-attach`** single line only, **not mixed** with read diagnostic (`metrics.optimization_replay_diagnostic_reason`).
- **Display rules (client):** `formatOptimizationReplayAttachHudLine` — `attached === true` and `reason === "attached"` → `Attach: attached`; `attached === false` → `Attach: skipped (<reason>)` (`unknown` if no `reason`); missing meta·non-object·non-boolean `attached` → `Attach: —`.
- **Render:** `renderOptimizationReplayHud(track)` updates status / truncation / diagnostic **as before**, then updates attach line from cached POST value (`optimizationReplayAttachHudRaw`). Calling `replaceOptimizationReplayPayload` alone does not change attach cache so **last POST attach display persists** (write observation axis separated from read track swap).
- **`renderOptimizationReplayAttachHud(raw)`:** Called only from POST handling path; updates cache then redraws full HUD via `renderOptimizationReplayHud(optimizationReplayTrack)`.
- **Out of scope (maintain):** No solver·GA·`optimization_replay_persist` behavior change; no read diagnostic meaning change; **do not merge** attach reason into `optimization_replay_diagnostic_reason`; no payload compression·Lab/Optimization implicit sync·overlay lifecycle change.
- **Relation to 12I.6:** 12I.6 "expand `renderOptimizationReplayHud` responsibility" non-goal targets **overlay·Lab index sync·render ownership transfer**. 12J adds **POST attach meta single line (write observation)** only.

### Sequence 12K — POST attach scalar diagnostics (`evolution_failed` stage)

**Implementation status (2026-05-17): complete**

- **Goal:** Keep **existing vocabulary** for `optimization_replay_attach.reason` (especially `evolution_failed`·`empty_candidate_pool`, etc.) while distinguishing failure cause only via scalar **`optimization_replay_attach.diagnostic`**. **Read axis** `metrics.optimization_replay_diagnostic_reason` (persist scan·deserialize) and **write axis** attach diagnostic remain **separated** (12J invariant).
- **Fields:** `stage`, candidate·recorder counts, `best_genome_present`, `evolution_convergence_reason`, (reserved) commit/validation scalars, `error_type` / short `error_message` — **no frame arrays·paths·full traceback·large maps**. Allowed `stage` values fixed by code constant `OPTIMIZATION_REPLAY_ATTACH_DIAGNOSTIC_STAGES`.
- **Path:** Exception mapping via stage variables in `django_apps/web/services/asteroid_lab_post_inspection_evolution.py`; `optimization_replay_persist.attach_optimization_replay_frames_after_successful_replay_build` merges stages such as `replay_serialization` / `attach_persist` on attach failure. Expose `diagnostic.stage` in `public_pages` JSON·INFO log (additional HUD line **non-goal**).
- **Out of scope (maintain):** No solver·GA·candidate generation·incremental commit·validation **semantic changes**; no Lab/optimization replay sync·overlay·payload compression.
- **Tests (regression):** 12K cases in `tests/unit/asteroid_lab/test_optimization_replay_persist.py` (`evolution_search` exception with candidate pool fixed via test helper), `test_post_json_attach_diagnostic_does_not_overwrite_read_diagnostic` in `tests/integration/web/test_asteroid_miner_layout_solver.py`, etc.

---

## 13. Test plan — 12F implementation PR acceptance criteria

Names below are **recommended for implementation PR to add·match**.

**Persist / schema (extend when envelope introduced):**

- `test_persisted_optimization_replay_schema_version_required` (envelope PR)
- `test_persisted_optimization_replay_rejects_unsupported_schema`

**Shape / read:**

- `test_persisted_optimization_replay_invalid_shape_falls_back_empty`
- `test_persisted_optimization_replay_truncation_contract` (frame metrics + track metrics pair)

**Page context:**

- `test_page_context_reads_persisted_optimization_replay`
- `test_page_context_malformed_optimization_replay_does_not_crash`

**Boundary:**

- `test_ui_payload_preserves_dual_track_no_sync` (historical name — replace with single timeline·output-only boundary test on unified migration)
- `test_solver_does_not_read_persisted_replay` (fix "no reverse import/call" via static search or architecture test)

**Regression:** maintain `test_optimization_replay_persist.py`, `test_replay_fixture_json_contract.py`, `test_long_replay_fixture_contract.py`.

---

## 14. Remaining open decisions

1. **Payload byte-size cap:** **Out of 12F-v0 scope**; timing·limit value follow-up.
2. **Multiple SolverRun:** Whether UI needs previous run selection beyond "show latest only".
3. **Envelope·`optimization_replay_schema_version`:** Only in separate migration/compatibility PR.

~~`truncation_reason` sibling vs metrics~~ → **v0 fixed as metrics aggregation (§6.1).**

---

## 15. Acceptance criteria (for this document)

- This document exists with §3 boundary·§11 non-goals explicit.
- 12F-v0 scope·out of scope fixed in §12.
- output-only invariant repeated in §3·§11.
- **Code behavior changes are not included in this document work.**
- Subsequent implementation should proceed in **small PRs** 12F→12G→12H→12I.

---

## 16. Verification (this document work)

- Markdown-only changes.
- No document-only lint script observed — **not run**.

---

## 17. Cross references

- `asteroid_lab_10_development_sequence.md`
- `asteroid_lab_11_future_execution_plan_post_sequence.md`
- `asteroid_lab_09_replay_debug.md`
- Code: `optimization_ui_payload.py`, `optimization_replay_persist.py`, `asteroid_lab_page_context.py`

---

## 18. Summary

| Item | Conclusion |
|------|------|
| Persist | `config_json["optimization_replay_frames"]` only (key name preserved) |
| schema_version | v0 sibling **not introduced**; deserialize + 12F shape guard |
| truncation_reason | **frame metrics → `build` → track.metrics**; first reason canonical; **no** sibling |
| Malformed | empty track + diagnostic string (12G); Lab page non-destructive |
| Dual-track | **Deprecated** → replay timeline ([`asteroid_lab_09_replay_timeline`](asteroid_lab_09_replay_timeline.md)) |
| 12F-v0 | frame list guard only; envelope·HUD·cap·migration **excluded** |
| 12I (draft, not implemented) | §12I: HUD **status / reason / diagnostic** 3 axes·JS const·`optimization_replay_attach.reason`↔diagnostic mapping·malformed matrix (M1–M7)·persist→deserialize→`replaceOptimizationReplayPayload`→HUD **display preservation** tests; overlay completeness·sync/render ownership change **out of scope (observation only)** |
| 12J (complete) | §12J: POST **`optimization_replay_attach` dedicated HUD line** (`Attach: …`); read **`optimization_replay_diagnostic_reason` unchanged**; solver/attach/persist **unchanged** |
| 12K (complete) | §12K: attach **`reason` vocabulary preserved** + **`diagnostic` scalar** (`stage`·counts·short error); read diagnostic separated; solver semantics·sync **unchanged** |

## Sequence 12L coordinate boundary reinforcement (2026-05-17)

- Critical invariant: after decode/import normalization produces Server X/Y, raw coordinates are illegal in algorithm code.
- optimization replay write path is solver output observation layer; input construction uses Server X/Y only.
- post-inspection evolution does not call raw coordinate converters after `build_optimization_input`.
- Island-local `x`/`y` only exposed on replay `map_view`·Lab HUD; `server_*` fields forbidden on UI·wire even in legacy JSON read-compat.
- **Hardening:** `test_coordinate_frame_ast_gate`, `test_import_boundaries`, POST `test_post_json_optimization_input_does_not_raw_convert_server_coords`.
- UI/overlay projection changes out of scope in 12L. If projection boundary issues found, separate UI/export boundary work.
