import { describe, expect, it } from "vitest";

import { fluidShapeCodeFromInk, inkFromFluidShapeCode } from "../src/EditorFoundation/fluidSourceUi";

describe("fluidSourceUi", () => {
  it("fluidShapeCodeFromInk uses ink-only tokens (no shape letter)", () => {
    expect(fluidShapeCodeFromInk("r")).toBe("-r-r-r-r");
    expect(fluidShapeCodeFromInk("g")).toBe("-g-g-g-g");
    expect(fluidShapeCodeFromInk("b")).toBe("-b-b-b-b");
  });

  it("inkFromFluidShapeCode parses color- alias, -ink layers, legacy C+ink", () => {
    expect(inkFromFluidShapeCode("color-r")).toBe("r");
    expect(inkFromFluidShapeCode("-g-g-g-g")).toBe("g");
  });
});
