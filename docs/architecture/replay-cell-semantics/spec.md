# Replay cell semantics — spec

Kanban: `.devtool/features/replay-cell-semantics-2026-06-12.md`

## Scope

Asteroid Lab replay cell semantics: overlay wire read/write, `EffectiveCellView` merge, serialized-frame lookup, Lab UI client fast-path.

## Non-goals

- Artifact ingest boundary
- Game-data snapshot provenance
- Step 4 unless explicitly approved

## Contract decisions

| Question | Decision |
|----------|----------|
| Client POST-only? | Step 4+ only. Steps 1–3: keep JS fast-path + server POST |
| Shared overlay keys? | Registry concept in Step 4; harvest hidden in resolver until then |
| Remove flat lookup? | After Step 3 only (grep-clean first) |
| read vs write transport | **Do not merge.** Read: tolerant (`normalize_project_transport_kind`). Write: strict (`profile_to_output_transport_kind`) |

## Invariants

- Normalized read transport ∈ `{none, space_belt, space_pipe}` on wire surfaces
- Legacy tokens (`shape_belt`, etc.) accepted on **read** only; never emitted on write
- `replay_cell_semantics.py` — pure read policy; no frame/merge/serialization
- JS mirror (`lab_effective_cell_view.js`) unchanged until Step 4+

## Epic acceptance

- [x] Step 1: resolver → `django_apps/asteroid_lab/replay/replay_frame_cell_resolver.py`
- [x] Step 2: `replay_cell_semantics.py`
- [x] Step 3: wire tests; remove flat shim + `replay_frame_cell_lookup.py`
- [ ] Step 4 (optional): server-canonical compare; overlay bucket registry

## Frozen (Steps 1–3)

No client/server path unification. No overlay bucket registry. No merging read/write normalizers.
