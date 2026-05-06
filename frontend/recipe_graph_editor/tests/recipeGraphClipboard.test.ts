import type { Edge, Node } from "@xyflow/react";
import { describe, expect, it } from "vitest";

import {
  buildSubgraphClipboardPayload,
  remapClipboardPayloadForPaste,
  serializeRecipeGraphClipboard,
  tryParseRecipeGraphClipboard,
} from "../src/recipeGraphClipboard";

function nid(prefix: string, i: number): string {
  return `${prefix}-${i}`;
}

describe("recipeGraphClipboard", () => {
  it("serializes and parses round-trip", () => {
    const nodes: Node[] = [
      {
        id: nid("src", 1),
        type: "shape",
        position: { x: 10, y: 20 },
        data: { shape_code: "A", quantity: 1 },
      },
    ];
    const edges: Edge[] = [];
    const payload = buildSubgraphClipboardPayload(new Set([nid("src", 1)]), nodes, edges);
    expect(payload).not.toBeNull();
    const text = serializeRecipeGraphClipboard(payload!);
    const parsed = tryParseRecipeGraphClipboard(text);
    expect(parsed?.nodes).toHaveLength(1);
    expect(parsed?.nodes[0]?.id).toBe(nid("src", 1));
  });

  it("remaps ids on paste", () => {
    let seq = 0;
    const newId = (prefix: string) => `${prefix}-paste-${seq++}`;
    const payload = buildSubgraphClipboardPayload(
      new Set(["op-a"]),
      [
        {
          id: "op-a",
          type: "operation",
          position: { x: 0, y: 0 },
          data: { operation: "rotate_cw" },
        },
      ],
      [],
    );
    expect(payload).not.toBeNull();
    const { nodes, edges } = remapClipboardPayloadForPaste(payload!, newId, (n) => n);
    expect(nodes).toHaveLength(1);
    expect(nodes[0]?.id.startsWith("op-paste-")).toBe(true);
    expect(edges).toHaveLength(0);
  });
});
