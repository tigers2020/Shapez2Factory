# Pre-Pass3 low-ROI bundle prune (P2)

## Goal

Immediately after Pass2 scan completes and before premerge Pass3 loop entry, remove miner bundles that failed the existing **P1 coarse ROI gate** (`_placement_p1_roi_gate_ok`, `roi_pass_key="pass2"`) to reduce long-distance routing load.

## Behavior

- Candidates: extractors that failed the gate only.
- Sort: ascending `_bundle_placement_roi_score` (lowest first). Fix transport keys for marginal/ROI calculation to snapshot at prune start.
- Cap: `MAX_PREPASS3_PRUNE_BUNDLES`.
- Removal: reuse `_demolish_extractor_bundle`.
- Rollback: `MiningLayoutGridRollback.capture` before prune. After each removal, check trunk connectivity **from anchor** (`flood_fill_component(anchor, transport_only) == transport_only`, `transport_only = set(transport_cells) | {anchor}`). Shapez grid cardinal neighbors are asymmetric, so use this check instead of `transport_is_connected` (arbitrary set start). On failure, `restore_into` full state and stop.
- Trace: `prepass3_low_roi_bundle_removed` (optional), `prepass3_low_roi_prune_summary`.

## Notes

- Post-placement extension count uses only extension and fluid_extension tiles from `buildings` / `extension_parents`.
- Plan file [`zero_extension_placement_gate_2026-05-09.md`](zero_extension_placement_gate_2026-05-09.md) P2 defers to this document as canonical.
