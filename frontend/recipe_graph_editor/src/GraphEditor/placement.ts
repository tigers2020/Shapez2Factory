import {
  RECIPE_PALETTE_GRID_CELL_HEIGHT,
  RECIPE_PALETTE_GRID_CELL_WIDTH,
  RECIPE_PALETTE_GRID_COLUMNS,
  RECIPE_PALETTE_GRID_ORIGIN_X,
  RECIPE_PALETTE_GRID_ORIGIN_Y,
} from "../EditorFoundation/constants";

export function newGraphNodeId(prefix: string): string {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

export function paletteGridPosition(index: number): { x: number; y: number } {
  const col = index % RECIPE_PALETTE_GRID_COLUMNS;
  const row = Math.floor(index / RECIPE_PALETTE_GRID_COLUMNS);
  return {
    x: RECIPE_PALETTE_GRID_ORIGIN_X + col * RECIPE_PALETTE_GRID_CELL_WIDTH,
    y: RECIPE_PALETTE_GRID_ORIGIN_Y + row * RECIPE_PALETTE_GRID_CELL_HEIGHT,
  };
}
