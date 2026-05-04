import "@xyflow/react/dist/style.css";
import type { Edge, Node } from "@xyflow/react";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { type CatalogOperationRow, type GraphBootstrap, GraphEditorApp } from "./GraphEditorApp";
import "./index.css";

function readJsonScript(id: string): unknown {
  const el = document.getElementById(id);
  if (!el?.textContent) {
    return null;
  }
  try {
    return JSON.parse(el.textContent);
  } catch {
    return null;
  }
}

function parseReactFlowInitial(raw: unknown): { nodes: Node[]; edges: Edge[] } {
  if (!raw || typeof raw !== "object") {
    return { nodes: [], edges: [] };
  }
  const o = raw as Record<string, unknown>;
  if (!Array.isArray(o.nodes) || !Array.isArray(o.edges)) {
    return { nodes: [], edges: [] };
  }
  return {
    nodes: o.nodes as Node[],
    edges: (o.edges as Edge[]).map((e) => ({
      ...e,
      type: e.type || "recipe",
    })),
  };
}

function parseCatalogOperations(raw: unknown): {
  operations: CatalogOperationRow[];
  engineIds: string[];
} {
  if (!raw || typeof raw !== "object") {
    return { operations: [], engineIds: [] };
  }
  const o = raw as Record<string, unknown>;
  const opsRaw = o.operations;
  const operations: CatalogOperationRow[] = [];
  if (Array.isArray(opsRaw)) {
    for (const row of opsRaw) {
      if (!row || typeof row !== "object") {
        continue;
      }
      const r = row as Record<string, unknown>;
      const value = typeof r.value === "string" ? r.value.trim() : "";
      if (!value) {
        continue;
      }
      operations.push({
        value,
        label: typeof r.label === "string" ? r.label : value,
        icon: typeof r.icon === "string" ? r.icon : "",
      });
    }
  }
  const eng = o.recipe_graph_engine_operations;
  const engineIds = Array.isArray(eng)
    ? eng.filter((x): x is string => typeof x === "string" && x.trim().length > 0)
    : [];
  return { operations, engineIds };
}

const rootEl = document.getElementById("macro-graph-editor-root");
if (!rootEl) {
  console.warn("[recipe-graph-editor] #macro-graph-editor-root missing");
} else {
  const recipe = readJsonScript("macro-graph-initial-recipe") as Record<string, unknown> | null;
  const bootstrap = readJsonScript("macro-graph-bootstrap") as GraphBootstrap | null;
  const catalogRaw = readJsonScript("macro-graph-initial-catalog");
  let { engineIds, operations } = parseCatalogOperations(catalogRaw);
  if (engineIds.length === 0 && operations.length > 0) {
    engineIds = operations.map((o) => o.value);
  }
  const code = typeof recipe?.code === "string" ? recipe.code : "—";
  const name = typeof recipe?.name === "string" ? recipe.name : "";
  const rid = recipe?.id;
  const recipeId =
    typeof rid === "number"
      ? rid
      : typeof rid === "string" && /^\d+$/.test(rid)
        ? parseInt(rid, 10)
        : 0;
  const { edges, nodes } = parseReactFlowInitial(bootstrap?.react_flow_initial ?? null);
  createRoot(rootEl).render(
    <StrictMode>
      <GraphEditorApp
        bootstrap={bootstrap}
        catalogOperations={operations}
        engineOperationIds={engineIds}
        initialEdges={edges}
        initialNodes={nodes}
        recipeCode={code}
        recipeId={recipeId}
        recipeName={name}
      />
    </StrictMode>,
  );
}
