---
status: ARCHIVED
do_not_use_as_authority: true
archived_reason: pre-RTTP plan snapshot; see documents/Algorithm/ and docs/superpowers/specs/
superseded_by:
  - documents/ai/current_plan.md
  - docs/superpowers/specs/2026-05-22-rttp-hybrid-c-layout-design.md
---

# Asteroid Lab — Runtime Replay Wiring Plan


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md`](../../Algorithm/asteroid_lab_12_runtime_replay_wiring.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

Role: Asteroid Lab Runtime Replay Wiring Architect

**Document status:** ACTIVE. §12 **Sequence 12F·12G·12H** are implemented (2026-05-17). **Sequence 12I** has only a **HUD vocabulary hardening** draft in §12; implementation proceeds in a separate PR. **Sequence 12J** (POST `optimization_replay_attach` dedicated HUD line) is implemented via Lab template, `asteroid_miner_layout_lab.js`, tests, and §12J documentation (2026-05-17). **Sequence 12K** (POST attach `diagnostic` scalar and `evolution_failed` stage observation) is implemented via §12K, code, and tests (2026-05-17). **Sequence 12L** (optimization boundary AST) 2026-05-17. **PR-F:** island-local replay; `server_coords` bridge **deleted**. Other sequences are for design and boundary fixation only.  
**Scope:** Covers only how to safely wire optimization replay into Lab persistence and UI read paths.  
**Prohibited:** This document alone does **not** change **solver, replay event semantics, DTO, or test-only fixture parser behavior**. Actual wiring implementation proceeds after separate PR and approval.

> **FIXTURE ENVELOPE SCHEMA ≠ RUNTIME PERSISTENCE SCHEMA** — golden top-level `truncation_reason` is regression-only; runtime uses frame `metrics` → track `metrics` ([`asteroid_lab_12_runtime_replay_wiring.md`](../../Algorithm/asteroid_lab_12_runtime_replay_wiring.md) Algorithm canonical §6.1).

---

## 1. Purpose

What is fixed so far is the **output contract**. The next runtime work is to expose existing optimization replay **output** through persistence and UI read paths, while fixing boundaries so replay does not leak as **solver input**.

Purpose of this document:

```text
- What to store where
- What the UI reads and how
- What remains output-only forever
- Whether to implicitly merge Lab replay track and Optimization replay track
```

Fixed in documentation before implementation.

---

## 2. Current contracts

The following are **already fixed by implementation and tests**.

| Contract | Location / means (summary) |
|------|------------------|
| Optimization JSON golden v0 | `tests/fixtures/shapez_asteroid/optimization/` |
| Optimization fixture JSON parser | `tests/unit/shapez_asteroid/fixtures/optimization_json.py` |
| Replay-track JSON golden v0 | `tests/fixtures/shapez_asteroid/replay/` |
| Replay JSON parser (fixture envelope) | `tests/unit/shapez_asteroid/fixtures/replay_json.py` |
| Long replay stitching JSON v0 | `tests/fixtures/shapez_asteroid/replay_long/` |
| `replay_truncated` / `truncation_reason` (fixture envelope pair) | golden + `replay_json` contract |
| `commit.survivability_summary` replay frame | aligned with domain events and regression tests |
| Lab / Optimization **dual-track** replay policy | Lab map track vs optimization observation track separation |

**Important:** The above fixture parsers and golden JSON are **contract and regression only**. Do not attach the same parser/envelope to solver input paths in production.

### 2.1 Pieces already present at runtime (code baseline, 2026-05-21)

- **Composition:** `lab_replay_timeline_payload.build_lab_replay_frames_for_project`
- **UI:** `updateReplayTruncationHud` — track `metrics.replay_truncated` / `truncation_reason`
- **Deprecated:** `build_optimization_replay_track_payload`, `renderOptimizationReplayHud`

### 2.2 Fixture envelope vs runtime persist shape

| Item | Golden long replay (`replay_long/`) | Current persist + UI |
|------|-----------------------------------|---------------------|
| `schema_version` | envelope top-level | **absent** from persist (frame list only) |
| `replay_summary` / `replay_event_sequence` | explicit in envelope | UI **recomputes** via `build_optimization_replay_track_payload` |
| `truncation_reason` | envelope top-level (pair contract) | **After 12F v0:** frame `metrics` → track `metrics.truncation_reason` aggregation (see §6.1 below) |

This table separates **test envelope ≠ runtime persist** to prevent mistakenly treating fixture parsers as production parsers.

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
  → (persist) SolverRun.config_json["optimization_replay_frames"]  # output only
  → (read) deserialize → build track → Lab context["optimization_replay"]
  → (display) metadata and overlay observation UI
```

### 3.2 Layer responsibilities

| Layer | Responsibility |
|--------|------|
| `shapez_asteroid.optimization` | events, frame DTO, serialization dict (business rules) |
| `asteroid_lab` | merge and persist output on `SolverRun`, import boundary |
| `web` (page context) | read-only adapter: on deserialize failure, empty track + `metrics.optimization_replay_diagnostic_reason` (12G, metadata only) |
| test fixture parser | regression canonical only; production dependency **not recommended** |

### 3.3 Sequence 12L — Island-local coord boundary

```text
After OptimizationInput, only `CoordFrame.ISLAND_RAW` island `(x, y)` (PR-F).
raw blueprint X/Y and dense conversion run only at decode/import, cleanup, and reconstruction boundaries.
django_apps.shapez_asteroid.optimization package and asteroid_lab_post_inspection_evolution.py:
Dense coord bridge module **deleted** (PR-F). AST: `test_coordinate_frame_ast_gate.py`.
copy JSON ``X==0`` is valid in island-local; lab world map has no ``x==0`` column — do not mix frame contexts.
```

---

## 4. Persistence target

### 4.1 Key names (aligned with code canonical)

**Keys used by current implementation (names unchanged):**

```text
SolverRun.config_json["optimization_replay_frames"]
```

Constant: `django_apps.shapez_asteroid.optimization.optimization_ui_payload.SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY` (`"optimization_replay_frames"`).

**Not added in 12F v0:** unless a separate envelope is introduced, do **not** add the sibling keys below (implementers must not add arbitrarily).

```text
optimization_replay_schema_version   # not introduced in v0
optimization_replay_truncated       # not introduced as sibling in v0
optimization_replay_truncation_reason # not introduced as sibling in v0
```

Truncation and schema are handled only via **frame list + track metrics** model in §6·§7. Envelope, schema sibling, and additional keys are reviewed only in a **separate migration / compatibility PR**.

### 4.2 **12F v0 decision (schema_version)**

Unless a separate envelope is introduced, do **not** add `optimization_replay_schema_version` sibling key. v0 runtime guard validates the existing `optimization_replay_frames` list via `deserialize_optimization_replay_frames_from_json`. Envelope or schema sibling introduction is handled only in a **separate migration/compatibility PR**.

---

## 5. Write path

```text
Run / Lab inspection flow
→ inspection and Lab replay success (existing pipeline)
→ bounded optimization run
→ produce optimization replay frames (memory)
→ JSON-safe serialization and attach to config_json["optimization_replay_frames"] only when 12F v0 guard passes
```

Replay data does **not** flow back to the solver.

---

## 6. Read path

```text
page context / UI payload builder
→ read optimization_replay_frames from config_json
→ deserialize + (after 12F) additional shape/pair validation
→ expose optimization_replay track to template and json_script
→ UI displays metadata/overlay only per dual-track policy
```

### 6.1 `replay_truncated` and `truncation_reason` (**12F v0 decision**)

**Do not store `truncation_reason` as a `SolverRun.config_json` sibling.**

- **Emit:** on frames indicating truncation, put `replay_truncated: true` and `truncation_reason: <non-empty string>` together in `metrics`.
- **Aggregate:** `_track_metrics_from_serialized_frames` lifts **`metrics.truncation_reason`**. When `replay_truncated == true`, reason is canonical from **last frame** `metrics` (Algorithm §6.1).
- **v1 alternative:** `config_json` sibling is reserved in design; revisit only in separate documentation/PR if needed.

**Track `metrics` pair contract (common baseline for UI and guards):**

```text
track.metrics.replay_truncated == false  →  track.metrics.truncation_reason absent
track.metrics.replay_truncated == true   →  track.metrics.truncation_reason is non-empty string
```

UI uses `replay_truncated` for truncation badge and `truncation_reason` for detail/tooltip only; **does not change replay event semantics.**

### 6.2 Relationship to fixture envelope pair

- **Test golden:** `replay_summary.replay_truncated` + top-level `truncation_reason` (regression).
- **Runtime:** persist is frame list only; pair is aligned via **frame `metrics` → track `metrics`**.

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

Read-only, metadata-only. Constant key: `django_apps.shapez_asteroid.optimization.optimization_ui_payload.OPTIMIZATION_REPLAY_DIAGNOSTIC_REASON_METRIC_KEY` → track `metrics` field name **`optimization_replay_diagnostic_reason`**.

```text
missing_optimization_replay          # no optimization_replay_frames key in any SolverRun.config_json
empty_optimization_replay_frames     # key exists but list is empty ([])
invalid_optimization_replay_payload  # not a list, broken frame dict/shape, coords, non-contiguous frame_index, etc. (unknown event_type excluded)
invalid_truncation_contract          # replay_truncated set but truncation_reason pair broken
unsupported_or_unknown_event_type    # unknown event_type string
```

On successful deserialize this field is **absent**. It does not participate in solver, replay semantics, ordering, or aggregation.

### 7.2 UI exposure (12G / 12H)

- **12G:** only when falling back to empty track, put §7.1 string in `metrics.optimization_replay_diagnostic_reason`. **Does not participate in replay semantics or frame order.**
- **12H:** Lab template and `asteroid_miner_layout_lab.js` expose `replay_truncated` / `truncation_reason` / `optimization_replay_diagnostic_reason` as **display-only HUD** (`#lab-optimization-replay-status`, etc.). No sync, retry, or payload mutation; on Run Solver JSON refresh, client `replaceOptimizationReplayPayload` redraws HUD.

---

## 8. Truncation contract

- **Fixture:** `replay_json` — `replay_summary.replay_truncated` + top-level `truncation_reason`.
- **Runtime track:** `track.metrics` pair from §6.1.
- **No semantic change:** HUD is observation only; does not change commit/route/evolution semantics.

---

## 9. Dual-track UI policy

```text
Lab replay owns map rendering.
Optimization replay owns optimization metadata/overlay observation.
No implicit index sync.
No implicit event-order sync.
Optimization replay controls must not mutate Lab currentFrameIndex
unless an explicit sync mode is introduced later (out of scope for v0).
```

---

## 10. Schema policy

**Documented v0 (persist):**

```text
No separate optimization_replay_schema_version key.
deserialize_optimization_replay_frames_from_json + 12F v0 shape/truncation guards are the structural validation center.
```

**When envelope is introduced later (separate PR):**

```text
optimization_replay_schema_version = 1  # example
unknown version → empty payload + diagnostic; silent coercion forbidden
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
- 12F-v0 does not introduce schema envelope / schema sibling / byte-size cap (12H adds **truncation and diagnostic HUD** only; semantics and sync unchanged)
```

---

## 12. Implementation sequence

### Sequence 12F — Persist frame-list guard v0

**Implementation status (v0, 2026-05-17): complete**

- **Guard and deserialize:** `validate_optimization_replay_frame_list_payload` and frame `metrics` truncation pair validation in `deserialize_optimization_replay_frames_from_json` (`replay_truncated == true` → non-empty `truncation_reason` in same `metrics`) in `django_apps.shapez_asteroid.optimization.optimization_ui_payload`.
- **Track aggregation:** `build_optimization_replay_track_payload` puts `metrics.truncation_reason` only when `replay_truncated == true`; value is **first** non-empty reason in frame order (or `"unknown"` on in-memory inconsistency — persist path filtered at deserialize).
- **Write:** `persist_optimization_replay_frames_to_solver_run` skips save on guard failure after serialization. `attach_optimization_replay_frames_after_successful_replay_build` skips with `invalid_replay_payload` reason.
- **Recorder:** `OptimizationReplayRecorder` records `truncation_reason` together on cell and frame limit truncation (`max_replay_cells_per_frame`, `max_replay_frames`).
- **Scope maintained:** **no** `optimization_replay_schema_version` / `optimization_replay_truncated` / `optimization_replay_truncation_reason` **sibling**; **no** envelope, byte cap, or migration; **12H** adds display-only HUD only (aligned with §11·§12).
- **12G preview:** single diagnostic string such as `optimization_replay_diagnostic_reason` on read failure is 12G; 12F covers shape, truncation pair, and track reason aggregation only.

**Tests (added/updated):** `tests/unit/shapez_asteroid/test_optimization_ui_payload.py` (guard, aggregation, deserialize), `tests/unit/shapez_asteroid/test_solver_optimization_replay_import_boundary.py` (solver package string non-reference), `tests/unit/asteroid_lab/test_optimization_replay_persist.py` (persist/attach/page empty track), Recorder assertions in `test_optimization_replay.py` and `test_optimization_replay_skeleton.py`.

**Scope:**

- Keep `optimization_replay_frames` as the only optimization replay persist key.
- **List shape** validation before attach/read.
- Reject broken frame dicts.
- Require **contiguous** `frame_index` (0..n-1).
- Allow only known `OptimizationReplayEventType` values for `event_type`.
- **Frame `metrics` truncation pair:** frames with `metrics.replay_truncated == true` must have non-empty `truncation_reason` in **same frame** `metrics`. If aggregated `track.metrics` does not satisfy §6.1 pair, fix to either **persist rejection** or **empty track on read** (implementation PR chooses one and locks with tests).
- On read path, malformed payload exposes **empty optimization replay payload**.

**Out of scope (not done in 12F-v0):**

```text
- schema envelope
- optimization_replay_schema_version sibling
- config_json truncation sibling keys
- DB migration
- payload byte-size cap
- excessive global dict key whitelist expansion (follow-up PR if needed)
```

(Display-only **truncation and diagnostic HUD** introduced in **12H** via `asteroid_miner_layout_solver.html` / `asteroid_miner_layout_lab.js`; no replay semantics or Lab sync.)

### Sequence 12G — UI payload read adapter

**Implementation status (v0, 2026-05-17): complete**

- page context reads persisted frames (12F fixes shape and truncation pair via `deserialize`/`validate`).
- On failure, empty payload + §7.2 diagnostic string (`optimization_replay_diagnostic_reason`, etc. — **12G implementation scope**).
- `metrics.truncation_reason` exposure follows §6.1 (12F track aggregation complete).

### Sequence 12H — Truncation / diagnostic metadata HUD

**Implementation status (v0, 2026-05-17): complete**

- **Template SSR:** `asteroid_miner_layout_solver.html` — `lab-optimization-replay-status` / `lab-optimization-replay-truncation` / `lab-optimization-replay-diagnostic` / `lab-optimization-replay-attach` (12J, default `Attach: —`; display-only; Lab replay index and frame order unchanged).
- **Client:** `renderOptimizationReplayHud(track)` — `normalizeOptimizationReplayTrack` passes `truncation_reason` and `optimization_replay_diagnostic_reason` to metrics; HUD re-renders on `replaceOptimizationReplayPayload` path.
- **Prohibited (maintained):** Lab ↔ optimization implicit frame sync, metadata interaction (retry/repair), no solver or replay semantic changes.

### Sequence 12I — Optimization replay HUD vocabulary hardening (draft)

**Goal:** Separate **display strings and codes** on the optimization replay HUD into **status / reason / diagnostic** **3 axes** so SSR, client re-injection (`replaceOptimizationReplayPayload`), and Python diagnostic contracts do not mix. **Implementation is not included in this sequence scope** — this section fixes documentation canonical only.

**Non-goals (prohibited in 12I):** **sync mode** between Lab map replay and optimization overlay, **render/ownership changes** to `renderOptimizationReplayHud` and overlay pipeline, **frame index and event order tight coupling** to make observation overlay "fully displayed". Overlay **completeness** is recorded only via **observation, metrics, and manual QA** after implementation; this sequence does **not** reflect those results in **documentation or test expectations** (no sync/render responsibility change).

#### 12I.1 3-axis definition (status / reason / diagnostic)

| Axis | Meaning (display and contract) | Source (summary) | Notes |
|----|------------------|------------|------|
| **status** | User-facing summary such as "track loaded normally / empty / truncated" | **Derived** from track `metrics` `frame_count`, `replay_truncated`, empty vs non-empty payload, etc. | **Does not 1:1 map to solver or replay semantics.** HUD label only. |
| **reason** | **Domain reason** for truncation (e.g. `truncation_reason`, recorder limits) | frame `metrics` → track `metrics` aggregation (§6.1) | On §6.1 pair violation, **read path is empty + diagnostic** (§7). |
| **diagnostic** | **Read adapter failure codes** for deserialize, shape, unsupported `event_type`, etc. | `metrics.optimization_replay_diagnostic_reason` and attach reason on **write skip** (12I.3 below) | **Metadata only**; does not participate in frame order or event interpretation (aligned with §7.1·12G). |

The three axes are **not interchangeable**. UI must align **naming rules** across JS, SSR, and Python so one axis string is not reused as another axis label.

#### 12I.2 JS `enum`/const mapping (draft)

- **Principle:** put **display constant tables** in `asteroid_miner_layout_lab.js` (and Lab-only bundle). Do not scatter string literals across template and HUD branches.
- **Minimum structure:** (1) **diagnostic codes** — fix same string set as §7.1 as `OPTIMIZATION_REPLAY_DIAGNOSTIC_*` or single object map. (2) **truncation / status badges** — bundle `replay_truncated` and `truncation_reason` display labels and tooltip keys as const.
- **i18n:** v0 may use fixed Korean/English strings, but separate **code values (diagnostic)** from **display strings** so follow-up i18n PR can swap maps only.
- **Prohibited:** branches that tie diagnostic strings to Lab replay index or map step (implicit sync; conflicts with §9·12H non-goals).

#### 12I.3 `optimization_replay_attach.reason` mapping (draft)

- **Scope:** map **internal reason codes** left on persist/attach **write path** when guard fails or skip occurs (e.g. `attach_optimization_replay_frames_after_successful_replay_build`) and **page-exposed** `optimization_replay_diagnostic_reason` in a **table**.
- **Principle:** attach reason is **operations, debug, and regression test** first; need not be exposed verbatim on HUD. When exposed, use only codes already in §7.1, or **add new codes to §7.1 table first** then fix with JS const (prevent string drift).
- **Documentation deliverable (before implementation PR):** recommended to put "attach reason → (optional) diagnostic → HUD display yes/no" **mapping table** under this section (one copy-paste-ready table for implementation).

#### 12I.4 Malformed payload matrix (draft)

Below is a **read path** matrix. Columns: input condition / expected track / `optimization_replay_diagnostic_reason` / `replay_truncated`·`truncation_reason` / page non-crash. Implementation PR attaches **one unit test name per row**.

| # | Input condition (config_json `optimization_replay_frames`) | Expected track | diagnostic (when present) | truncation axis | Notes |
|---|--------------------------------------------------------|-----------|------------------------|-----------------|------|
| M1 | key absent | empty | `missing_optimization_replay` | pair §6.1 default false/absent | §7.1 |
| M2 | `[]` | empty | `empty_optimization_replay_frames` | same | |
| M3 | not a list, broken frame dict, non-contiguous `frame_index`, etc. | empty | `invalid_optimization_replay_payload` | same | |
| M4 | `replay_truncated` and `truncation_reason` pair broken | empty | `invalid_truncation_contract` | blocked before aggregation | |
| M5 | unknown `event_type` | empty | `unsupported_or_unknown_event_type` | same | |
| M6 | (follow-up) envelope / `optimization_replay_schema_version` mismatch | empty | separate code (§10) | separate PR extends §7.1 | 12I **reserves row only**; code strings fixed with envelope PR |
| M7 | (follow-up) byte limit exceeded | empty or policy choice | follow-up | follow-up | linked to §14 open decision |

**Note:** M1–M5 code strings must match **§7.1 implementation values**. Matrix is a **contract table**; on implementation change, update §7·§12I·tests together.

#### 12I.5 Verification chain: persist → deserialize → `replaceOptimizationReplayPayload` → HUD preservation (draft)

- **Intent:** regression that **same diagnostic, truncation, and status display** holds both right after persist read and when client runs `replaceOptimizationReplayPayload` on Run Solver JSON refresh.
- **Recommended test layers:**
  1. **Python:** persist fixture or inject `SolverRun.config_json` → `deserialize_optimization_replay_frames_from_json` + `build_optimization_replay_track_payload` → expected `metrics` snapshot.
  2. **Django page context:** extend existing `test_page_context_malformed_optimization_replay_does_not_crash` — HTML contains expected strings in **diagnostic and truncation placeholders** (SSR).
  3. **JS (optional, minimal):** after `replaceOptimizationReplayPayload`, HUD nodes remain and same normalize path runs — one unit or integration case per **frontend build policy**.
- **Preservation definition:** "preservation" is **display strings and visibility**, not confused with frame count or event content changing on JSON refresh. When optimization track is **intentionally emptied**, HUD matching empty state is correct.

#### 12I.6 Overlay completeness and sync (observation only)

- **Completeness:** "whether all cells/all events are drawn on overlay" is recorded only as **observation metrics** (log, screenshot, manual checklist). 12I does **not** document this as a **PASS/FAIL gate**.
- **Prohibited reconfirmation:** frame index sync, aligning Lab `currentFrameIndex` with optimization step, overlay layer ownership transfer, expanding `renderOptimizationReplayHud` responsibility — **all out of scope**. If issues appear, split to **bug report or separate sequence**.

**Implementation scope summary:** bundle 3-axis vocabulary, JS const, attach↔diagnostic mapping table, M1–M7 matrix, and chain tests in **one PR or consecutive 12I sub-PRs**; each PR must not violate §3 output-only, §9 dual-track, §11 non-goals.

### Sequence 12J — Optimization replay attach HUD (POST write channel, separate line)

**Implementation status (2026-05-17): complete**

- **Goal:** expose POST response `optimization_replay_attach` `{ attached, reason }` on **`#lab-optimization-replay-attach`** one line in Optimization Replay panel only, **without mixing with read diagnostic** (`metrics.optimization_replay_diagnostic_reason`).
- **Display rules (client):** `formatOptimizationReplayAttachHudLine` — `attached === true` and `reason === "attached"` → `Attach: attached`; `attached === false` → `Attach: skipped (<reason>)` (`unknown` if no `reason`); missing meta, non-object, or non-boolean `attached` → `Attach: —`.
- **Render:** `renderOptimizationReplayHud(track)` updates status / truncation / diagnostic **as before**, then updates attach line from cached POST value (`optimizationReplayAttachHudRaw`). When only `replaceOptimizationReplayPayload` is called, attach cache is unchanged so **last POST attach display is preserved** (read track replacement and write observation axes separated).
- **`renderOptimizationReplayAttachHud(raw)`:** called only on POST handling path; updates cache then redraws full HUD via `renderOptimizationReplayHud(optimizationReplayTrack)`.
- **Out of scope (maintained):** no solver, GA, or `optimization_replay_persist` behavior change; no read diagnostic semantic change; do **not merge** attach reason into `optimization_replay_diagnostic_reason`; no payload compression, Lab/Optimization implicit sync, or overlay lifecycle change.
- **Relation to 12I.6:** 12I.6 "expanding `renderOptimizationReplayHud` responsibility" out of scope refers to **overlay, Lab index sync, and render ownership transfer**. 12J adds **POST attach meta one line (write observation)** only.

### Sequence 12K — POST attach scalar diagnostics (`evolution_failed` stage)

**Implementation status (2026-05-17): complete**

- **Goal:** keep `optimization_replay_attach.reason` **existing vocabulary** (especially `evolution_failed`, `empty_candidate_pool`, etc.) while distinguishing failure cause only via scalar **`optimization_replay_attach.diagnostic`**. **Read axis** `metrics.optimization_replay_diagnostic_reason` (persist scan, deserialize) and **write axis** attach diagnostic remain **separated** (12J invariant).
- **Fields:** `stage`, candidate and recorder counts, `best_genome_present`, `evolution_convergence_reason`, (reserved) commit/validation scalars, `error_type` / short `error_message` — **no frame arrays, paths, full traceback, or large maps**. Allowed `stage` values fixed by code constant `OPTIMIZATION_REPLAY_ATTACH_DIAGNOSTIC_STAGES`.
- **Path:** exception mapping via stage variables in `django_apps/web/services/asteroid_lab_post_inspection_evolution.py`; on attach failure `optimization_replay_persist.attach_optimization_replay_frames_after_successful_replay_build` merges stages such as `replay_serialization` / `attach_persist`. Expose `diagnostic.stage` in `public_pages` JSON and INFO log (additional HUD line **not a goal**).
- **Out of scope (maintained):** no solver, GA, candidate generation, incremental commit, or validation **semantic change**; no Lab/optimization replay sync, overlay, or payload compression.
- **Tests (regression):** 12K-specific cases in `tests/unit/asteroid_lab/test_optimization_replay_persist.py` (`evolution_search` exception with candidate pool fixed via test helper), `tests/integration/web/test_asteroid_miner_layout_solver.py` `test_post_json_attach_diagnostic_does_not_overwrite_read_diagnostic`, etc.

---

## 13. Test plan — 12F implementation PR acceptance criteria

Names below are **recommended for addition and alignment in implementation PR**.

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

- `test_ui_payload_preserves_dual_track_no_sync`
- `test_solver_does_not_read_persisted_replay` (fix "no reverse import/call" via static search or architecture test)

**Regression:** maintain `test_optimization_replay_persist.py`, `test_replay_fixture_json_contract.py`, `test_long_replay_fixture_contract.py`.

---

## 14. Remaining open decisions

1. **Payload byte-size cap:** **out of 12F-v0 scope**; timing and limit value are follow-up.
2. **Multiple SolverRun:** whether UI needs run selection beyond "show latest only".
3. **Envelope and `optimization_replay_schema_version`:** only in separate migration/compatibility PR.

~~`truncation_reason` sibling vs metrics~~ → **v0 fixed on metrics aggregation (§6.1).**

---

## 15. Acceptance criteria (this document itself)

- This document exists and §3 boundary and §11 non-goals are explicit.
- 12F-v0 scope and out-of-scope fixed in §12.
- output-only invariant repeated in §3·§11.
- **Code behavior changes are not included in this document work.**
- Subsequent implementation must proceed in **small PRs** in order 12F→12G→12H→12I.

---

## 16. Verification (this document work)

- Markdown-only changes.
- No document-only lint script observed; **not run**.

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
| Persist | `config_json["optimization_replay_frames"]` only (key name unchanged) |
| schema_version | v0 sibling **not introduced**; deserialize + 12F shape guard |
| truncation_reason | **frame metrics → `build` → track.metrics**; first reason canonical; **no** sibling |
| Malformed | empty track + diagnostic string (12G); Lab page non-crash |
| Dual-track | Lab map authority vs optimization observation; no implicit sync |
| 12F-v0 | frame list guard only; envelope, HUD, cap, migration **excluded** |
| 12I (draft, not implemented) | §12I: HUD **status / reason / diagnostic** 3 axes, JS const, `optimization_replay_attach.reason`↔diagnostic mapping, malformed matrix (M1–M7), persist→deserialize→`replaceOptimizationReplayPayload`→HUD **display preservation** tests; overlay completeness and sync/render ownership change **out of scope (observation only)** |
| 12J (implemented) | §12J: POST **`optimization_replay_attach` dedicated HUD line** (`Attach: …`); read **`optimization_replay_diagnostic_reason` unchanged**; solver/attach/persist **unchanged** |
| 12K (implemented) | §12K: attach **`reason` vocabulary maintained** + **`diagnostic` scalar** (`stage`, counts, short errors); separated from read diagnostic; solver semantics and sync **unchanged** |
## Sequence 12L coordinate boundary hardening (2026-05-17)

- Critical invariant: after decode/normalize to island grid, raw coordinates are illegal in algorithm code.
- optimization replay write path is solver output observation layer; input uses island-local coords only.
- post-inspection evolution does not call raw coordinate converters after `build_optimization_input`.
- copy JSON `X`/`Y`; forbidden re-conversion: dense bridge (removed PR-F) class conversions allowed only at import/decode and final display/export projection boundaries.
- copy JSON `X==0` remains valid coordinate in replay/route/evolution diagnostics.
- **12L-hardening:** `test_import_boundaries`, `test_coordinate_frame_ast_gate`; POST `test_post_json_optimization_input_does_not_raw_convert_server_coords` (legacy name).
- UI/overlay projection changes are out of scope in 12L. If projection boundary issues are found, split to separate UI/export boundary work.
