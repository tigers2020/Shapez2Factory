import { describe, expect, it } from "vitest";

import { operationChangeGroupId, paletteCategoryForOperation } from "../src/Operation/paletteGroups";

describe("operationChangeGroupId", () => {
  it("groups painter with color_mixer and crystal_generator", () => {
    expect(operationChangeGroupId("painter")).toBe("COLOR");
    expect(operationChangeGroupId("color_mixer")).toBe("COLOR");
    expect(operationChangeGroupId("crystal_generator")).toBe("COLOR");
  });

  it("returns null for unknown operations (modal shows full catalog)", () => {
    expect(operationChangeGroupId("")).toBeNull();
    expect(operationChangeGroupId("not_an_op")).toBeNull();
  });
});

describe("paletteCategoryForOperation", () => {
  it("maps unknown values to FLOW (palette fallback)", () => {
    expect(paletteCategoryForOperation("")).toBe("FLOW");
    expect(paletteCategoryForOperation("not_an_op")).toBe("FLOW");
  });
});
