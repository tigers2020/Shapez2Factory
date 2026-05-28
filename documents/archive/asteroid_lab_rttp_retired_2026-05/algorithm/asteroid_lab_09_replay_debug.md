# Phase 9 — Replay and Debug Artifact (DEPRECATED)

> **Product canonical for this document has moved to [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md).**  
> The dual-track, HUD-only optimization replay, and separate optimization controller policies below are **obsolete**. Do **not** apply them in implementation, review, or test design.

---

## Deprecated policy (summary)

```text
Deprecated:
The previous dual-track Lab replay / Optimization replay policy is obsolete.
The product replay model is now a single Lab replay timeline.
Optimization events must be projected into 2D map frames, not displayed as HUD-only metadata.
```

| Deprecated statement | New canonical |
|-----------|---------|
| Lab replay authoritative; Optimization metadata only | One Lab Replay Timeline |
| Run Solver does not change Lab timeline | Full lifecycle appends to the same timeline |
| Lab frame index ↔ Optimization frame index linking forbidden | **One** global monotonic `frame_index` |
| 11A/11B optional overlay | 9C–9E core map projection and render pipeline |

**New North Star:** [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md)

---

## Historical archive (dual-track original)

<details>
<summary>Frontend Dual-track Replay Policy (deprecated — expand)</summary>

The frontend treated **Lab replay** and **Optimization replay** as **dual-track**.

- Lab: `lab_replay_frames_json` — map render authority
- Optimization: metadata only (through 10E); optional overlay in 11B
- `no implicit index sync` between Lab and Optimization frame indices
- Separate `optimizationReplayFrameIndex`

**→ All deprecated due to product goal change.** Details: unified canonical document 「Deprecated」 section.

</details>

---

## Historical archive (instrumentation and scale — still referenceable)

Sequence **13A·13B** instrumentation, HAR, `measure_json_sections`, Lab `full_map` uncapped gap, etc. remain valid as **payload research evidence**. However, invariant wording **「maintain dual-track」** is **replaced** by the replay timeline canonical.

- **13 roadmap canonical:** [`asteroid_lab_13_replay_payload_scalability.md`](asteroid_lab_13_replay_payload_scalability.md)
- **13A·13B detail (this file's git history or archive):** HAR ~22.6MB, `MAX_REPLAY_FRAMES`/`MAX_REPLAY_CELLS_PER_FRAME`, Lab vs optimization attribution

**Invariants to update in the 13 series (2026-05-19):**

```text
Replay is output-only.                    # retained
One unified product replay timeline.      # replaces dual-track
No solver reads replay payload.           # retained
```

---

## Migration pointers

| Previous concept | New location |
|-----------|---------|
| `OptimizationReplayFrame` | `ReplayTimelineFrame` + `ReplayMapView` |
| `OptimizationReplayEventType` | `ReplayEventType` (value strings may remain compatible) |
| Sequence 11A projection | Sequence **9C** |
| Sequence 11B overlay layer | Sequence **9E** (single map; overlay via `map_view.overlay_cells`) |
| Phase 9 invariants and tests | unified canonical 「Invariants」「Test Plan」 |

---

## Links

- **Canonical:** [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md)
- **Development sequence:** [`asteroid_lab_10_development_sequence.md`](asteroid_lab_10_development_sequence.md)
- **Runtime wiring:** [`asteroid_lab_12_runtime_replay_wiring.md`](asteroid_lab_12_runtime_replay_wiring.md)
