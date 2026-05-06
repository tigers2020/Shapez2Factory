import { describe, expect, it } from "vitest";

import {
  atomicLayerGameCode,
  canComposeTileScene,
  overlayStackScaleFromBottom,
  pedestalSpriteKey,
  quadrantDestRect,
  quadrantOverlayStackTier,
  shapePartSpriteKey,
  sortCellsForStackedOverlay,
} from "../src/shapePartSpriteCompose";

describe("shapePartSpriteCompose", () => {
  it("atomicLayerGameCode matches single-layer game notation", () => {
    expect(atomicLayerGameCode("C", "r", 0)).toBe("Cr------");
    expect(atomicLayerGameCode("W", "b", 2)).toBe("----Wb--");
  });

  it("pedestalSpriteKey matches server pedestal row", () => {
    expect(pedestalSpriteKey("v1")).toBe("pedestal:v1");
  });

  it("shapePartSpriteKey matches server manifest key", () => {
    expect(shapePartSpriteKey({ shape_code: "R", color_code: "r", quadrant_index: 0 }, "v1")).toBe(
      "Rr------:v1",
    );
    expect(shapePartSpriteKey({ shape_code: "W", color_code: "b", quadrant_index: 2 }, "v1")).toBe(
      "----Wb--:v1",
    );
  });

  it("quadrantDestRect packs four quadrants into a square", () => {
    const s = 40;
    expect(quadrantDestRect(1, s)).toEqual({ x: 0, y: 0, w: 20, h: 20 });
    expect(quadrantDestRect(2, s)).toEqual({ x: 20, y: 0, w: 20, h: 20 });
    expect(quadrantDestRect(0, s)).toEqual({ x: 0, y: 20, w: 20, h: 20 });
    expect(quadrantDestRect(3, s)).toEqual({ x: 20, y: 20, w: 20, h: 20 });
  });

  it("sortCellsForStackedOverlay puts SW/SE before NW/NE within a layer", () => {
    expect([0, 1, 2, 3].map(quadrantOverlayStackTier)).toEqual([0, 2, 3, 1]);
    const out = sortCellsForStackedOverlay([
      { quadrant_index: 2, layer_index: 0 },
      { quadrant_index: 0, layer_index: 0 },
      { quadrant_index: 3, layer_index: 0 },
    ]);
    expect(out.map((c) => c.quadrant_index)).toEqual([0, 3, 2]);
  });

  it("overlayStackScaleFromBottom reduces each upper tier by 10%", () => {
    expect(overlayStackScaleFromBottom(0)).toBe(1);
    expect(overlayStackScaleFromBottom(1)).toBeCloseTo(0.9, 6);
    expect(overlayStackScaleFromBottom(2)).toBeCloseTo(0.81, 6);
  });

  it("canComposeTileScene rejects multi-layer or duplicate quadrants", () => {
    expect(
      canComposeTileScene([
        { layer_index: 0, quadrant_index: 0 },
        { layer_index: 1, quadrant_index: 1 },
      ]),
    ).toBe(false);
    expect(
      canComposeTileScene([
        { layer_index: 0, quadrant_index: 0 },
        { layer_index: 0, quadrant_index: 0 },
      ]),
    ).toBe(false);
    expect(canComposeTileScene([{ layer_index: 0, quadrant_index: 0 }])).toBe(true);
  });
});
