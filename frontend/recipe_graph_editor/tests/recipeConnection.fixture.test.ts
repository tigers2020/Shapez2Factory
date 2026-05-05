import { strict as assert } from "node:assert";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import type { Edge, Node } from "@xyflow/react";
import { describe, it } from "vitest";

import { getEffectiveOperationInputArity } from "../src/operationArity";
import { expectedInputCarriers, sortedInputEdgesToOperation } from "../src/recipeConnection";

const __dirname = dirname(fileURLToPath(import.meta.url));
const fixturePath = join(__dirname, "../../../tests/fixtures/recipe_connection_rule_scenarios.json");

type ScenarioFile = {
  required_input_and_carriers: Array<{
    id: string;
    op_type: string;
    op_node: Record<string, unknown>;
    required_input_count: number;
    expected_carriers: string[];
  }>;
  input_edge_sort: Array<{
    id: string;
    operation_id: string;
    shape_nodes: Array<{ id: string; kind: string }>;
    input_edges: Array<{ from: string; to: string; slot?: string | null }>;
    expected_from_order: string[];
  }>;
};

const scenarios: ScenarioFile = JSON.parse(readFileSync(fixturePath, "utf8")) as ScenarioFile;

describe("recipe_connection_rule_scenarios.json (TS vs Python contract)", () => {
  it("required_input_count and expected_input_carriers match fixture", () => {
    for (const row of scenarios.required_input_and_carriers) {
      const op = row.op_type.trim();
      const d = row.op_node;
      const gotCount = getEffectiveOperationInputArity(op, d);
      assert.equal(gotCount, row.required_input_count, row.id);
      const paint = typeof d.paint_color === "string" ? d.paint_color : undefined;
      const crystal = typeof d.crystal_color === "string" ? d.crystal_color : undefined;
      const gotCarriers = expectedInputCarriers(op, paint, crystal);
      assert.deepStrictEqual(gotCarriers, row.expected_carriers, row.id);
    }
  });

  it("sortedInputEdgesToOperation matches fixture", () => {
    for (const row of scenarios.input_edge_sort) {
      const opId = row.operation_id;
      const nodes: Node[] = row.shape_nodes.map((n) => ({
        id: n.id,
        type: n.kind === "shape" ? "shape" : "default",
        position: { x: 0, y: 0 },
        data: {},
      }));
      const edges: Edge[] = row.input_edges.map((e, i) => {
        const data: Record<string, unknown> = { domainKind: "input" };
        if (e.slot != null && e.slot !== "") {
          data.slot = e.slot;
        }
        return {
          id: `e${i}`,
          source: e.from,
          target: e.to,
          type: "recipe",
          data,
        };
      });
      const sorted = sortedInputEdgesToOperation(edges, nodes, opId);
      assert.deepStrictEqual(
        sorted.map((x) => x.source),
        row.expected_from_order,
        row.id,
      );
    }
  });
});
