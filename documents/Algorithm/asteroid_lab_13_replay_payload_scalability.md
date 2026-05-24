# Sequence 13 — Replay Payload Scalability Roadmap

**Role:** Canonical roadmap for the **unified replay payload** scaling track (product uses a single timeline; Lab/optimization attribution labels are historical labels from 13A·13B measurement).  
**Scope:** Documentation only. **Code, response contract, and JS loading changes after 13C require explicit approval** in a separate implementation phase.

**Related canonical docs and evidence:**

- Measurement, field numbers, 13A·13B detail: [`asteroid_lab_09_replay_debug.md`](asteroid_lab_09_replay_debug.md) (historical) · product replay canonical: [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md)
- Development sequence context: [`asteroid_lab_10_development_sequence.md`](asteroid_lab_10_development_sequence.md)
- Post-sequence priorities: [`asteroid_lab_11_future_execution_plan_post_sequence.md`](asteroid_lab_11_future_execution_plan_post_sequence.md)

---

## Purpose

Sequence 13 is the **scaling track** for when **Lab replay timeline** frame payloads grow large enough to break **POST JSON** and **DevTools observability** (response body cache eviction, etc.).

- **Replay semantics** are preserved.
- **Replay / debug artifacts** remain **output-only**.

---

## Current Evidence

- **HAR-based:** A single POST response JSON grew to **~22.6MB** in at least one observed case.
- Chrome DevTools and similar tools may trigger **response body eviction** (body removed from inspector cache).

**13A:** Introduced deterministic top-level JSON **section size attribution**.  
**13B:** Added **Lab replay–specific** attribution, `largest_lab_frames`, and **redundancy** measurement.

---

## Completed Work

| Phase | Content |
|------|------|
| **13A** | Deterministic JSON section measurement (`measure_json_sections`, etc.), optimization replay **hard cap** regression, HAR and evidence documentation |
| **13B** | Lab replay attribution, `full_map` / cell count / redundancy analysis, top-frame ranking; **13B measurement snapshot:** Lab replay was not capped by optimization limits (`MAX_OPTIMIZATION_*`) — **historical observation**. Product limits: Lab `MAX_UNIFIED_LAB_*`, optimization `MAX_OPTIMIZATION_*` ([`replay_limits.py`](../../django_apps/asteroid_lab/replay/replay_limits.py), [`asteroid_lab_09_replay_timeline`](asteroid_lab_09_replay_timeline.md)) |

**Transition to implementation:** The above covers **measurement, design, and regression keys** only. **POST body reduction, lazy-load, delta, and other runtime behavior changes are after 13C** and require **separate approval**.

---

## Strategy role split (inline / lazy-load / delta / interning / compression)

These are **not substitutes for one another**; responsibilities differ.

| Strategy | Role | Semantics |
|------|------|--------|
| **Inline full replay** | Current: full Lab frames in POST response | Baseline; equivalence proof required on change |
| **Lazy-load endpoint (13C)** | POST carries **summary · preview · fetch handle** only; full Lab replay via **on-demand GET**, etc. | Frame **content identical**; only transport path split |
| **Delta replay (13E)** | Reduces serialization **representation** only; client/server **reconstruction rules** documented | **Serialization optimization**, not **semantic change** |
| **Cell interning / dictionary encoding (13F)** | **Reference · dictionary encoding** for repeated cell payloads | Cell detail lookup and frame rendering **equivalence** preserved |
| **HTTP compression (13G)** | gzip/Brotli etc. at **transport layer** | JSON body meaning identical; **does not replace semantic payload work** |

---

## Non-negotiable Invariants

```text
Replay is output-only.
One unified product replay timeline (dual-track policy deprecated 2026-05-19).
Every frame must remain 2D-renderable (map_view) when payload shape changes.
No solver / algorithm reads replay payload.
Replay semantic equivalence must be preserved.
No large golden JSON unless explicitly approved.
UI uses a single timeline controller unless a dedicated migration sequence opens.
```

**Forbidden before implementation approval (including this document phase):**

- **Code implementation** (no 13C UI · endpoint · contract changes)
- **Preemptive response contract changes**
- **Preemptive JS replay loading changes**
- **Delta compression · encoding core implementation**
- **Solver / replay semantics changes**
- **13C implementation** — do not start without **explicit human approval**

---

## Sequence 13C — Full Lab Replay Lazy-load Endpoint

**Environment variables:** Before implementation and approval, do **not** put any env name such as `ASTEROID_LAB_REPLAY_JSON_DELIVERY` in `.env`. Register canonical names only in [`environment.md`](../ai/manuals/environment.md) with the implementation PR.

**Preferred first implementation:** Reduce POST response size without changing **replay frame semantics**.

- POST response: **summary · preview · fetch handle** (e.g. token · URL · resource id — exact format fixed in approved design).
- **Full Lab replay** fetched via **separate request** when needed.
- Frames returned by the **full replay endpoint** must be **semantically identical** to historical inline `lab_replay_frames_json`.

**Semantic risk:** Ensure fetch path · cache · permissions · CSRF · errors on **partial load** do not corrupt UI state.

---

## Sequence 13D — UI Lazy-load Integration

- UI loads when the **replay controller needs the full Lab replay**.
- Expose **loading / error states**.
- Maintain **single replay timeline controller** ([`asteroid_lab_09_replay_timeline`](asteroid_lab_09_replay_timeline.md); dual-track deprecated).
- **Inline mode fallback** allowed during migration.

**Semantic risk:** If two sources (inline vs fetch) both claim **authority**, drift occurs; one explicit source priority is required.

---

## Sequence 13E — Delta Replay Prototype

- Explore **after lazy-load is insufficient**.
- Must include **frame reconstruction equivalence** tests.
- Delta format is **serialization optimization**; **semantic change forbidden**.

**Semantic risk:** Reconstruction bugs · frame order · `full_map`/`diff` interpretation mismatch.

---

## Sequence 13F — Cell Interning / Dictionary Encoding

- Review after **redundancy measurement (13B)** shows sufficient gain.
- Preserve **cell detail lookup** and **frame rendering equivalence**.

**Semantic risk:** Intern key resolution failure → silent truncation or wrong cell display.

---

## Sequence 13G — Transport Compression / Server Response Policy

- Verify **gzip / Brotli** behavior and response headers.
- **Transport layer** optimization; **does not replace 13C–13F semantic payload design**.

**Semantic risk:** Low (byte-identical decode then existing JSON pipeline). **Observability risk:** DevTools may display compressed bodies differently.

---

## Deferred / Not Now

Revisit only when **13C–13G are insufficient**.

```text
Binary replay format
WebSocket streaming
Replay database chunking
Object-store artifact downloads
Full replay pagination (splitting large single artifacts, etc.)
```

---

## Required Test Strategy

Verification to fix at implementation phase (summary):

```text
full endpoint replay == previous inline replay (semantic equivalence)
same frame_count
same frame_index order
same frame_key / event metadata
same full_map / diff semantics
cell detail lookup compatibility: Lab ORM frames expose ``inspector.replay_frame_id`` (persisted ``ReplayFrame.pk``); optimization-only frames use client ``map_view`` lookup (no ORM row)
equipment bundle highlight: unified wire includes ``cell_overlay_json.equipment_bundles`` when present (Lab passthrough or optimization rebuild from ``map_view``)
no algorithm reads replay payload
lazy-load failure: explicit UI error; current replay state must not be corrupted
```

**Recommended test command (post-implementation · regression):**

```text
python -m pytest tests/integration/web/test_asteroid_miner_layout_solver.py -k "payload or replay or json_size"
```

---

## Sequence 13 Exit Criteria

```text
POST response no longer carries unnecessary full Lab replay payload by default
full replay remains fetchable and semantically equivalent
large response DevTools eviction is avoided for normal Run Solver flow
replay / debug remains output-only
```

---

## Document History

| Date | Content |
|------|------|
| 2026-05-17 | Sequence 13 roadmap canonical first fixed (13A·13B completion summary, 13C–13G, invariants · forbidden · tests · exit criteria) |
