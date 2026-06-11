# Macro multilayer tile preview enablement (2026-05-06)

## Goal

When macro recipe graph multilayer shape `preview_scene.cells` includes `layer_index > 0`, relax `canComposeTileScene` so client tile sprite composition (`ShapePartSpriteTileLayers`) does not fall back.

## Scope

- In scope: `canComposeTileScene` in `frontend/recipe_graph_editor/src/ShapeSprite/compose.ts`, related unit tests.
- Out of scope: Stage track UI, solver inventory · placement limits.

## Implementation summary

- Forbid duplicate `(layer_index, quadrant_index)` pairs only.
- `quadrant_index` 0–3, `layer_index` 0–3 (aligned with max 4 layers per pattern).
- Cell count cap 16.

## Verification

- `cd frontend/recipe_graph_editor && npm run test && npm run build`

## Approval

Proceed per requester implementation directive (this document is gate record only).
