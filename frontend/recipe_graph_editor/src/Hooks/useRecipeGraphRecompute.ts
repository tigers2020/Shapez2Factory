import type { Dispatch, SetStateAction } from "react";
import { useCallback, useEffect, useRef, useState } from "react";

import type { Edge, Node } from "@xyflow/react";

import { macroGraphDebug } from "../EditorFoundation/macroGraphDebug";
import { applyValidationIssuesToNodes } from "../EditorFoundation/validationIssuesNodes";
import { buildReactFlowSnapshot } from "../EditorFoundation/reactFlowSnapshot";
import { setGlobalStatus } from "../GraphEditor/globalStatus";
import { enrichNodesWithCatalogIcons } from "../Operation/nodeCatalogMerge";
import { ensurePainterTargetHandlesOnEdges } from "../RecipeConnection";
import { mergeSilentPreviewFromServer } from "../RecipeGraph/mergeSilentPreviewFromServer";
import { postRecipeGraphRecompute, type RecipeGraphRecomputeResponse } from "../RecipeGraph/api";

/** Ref holder (avoids deprecated `MutableRefObject` in Sonar ruleset). */
type RefBox<T> = { current: T };

const SILENT_RECOMPUTE_DEBOUNCE_MS = 400;

type ApplyMeta = { commit: boolean; silent?: boolean };

function summarizeShapeNodeForDebug(n: Node): Record<string, unknown> | null {
  const nodeType = String(n.type ?? "");
  if (nodeType !== "shape" && nodeType !== "intermediate" && nodeType !== "output") {
    return null;
  }
  const raw = n.data;
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    return null;
  }
  const code = typeof raw["shape_code"] === "string" ? raw["shape_code"] : "";
  const ps = raw["preview_scene"];
  let previewNorm = "";
  if (ps !== null && ps !== undefined && typeof ps === "object" && !Array.isArray(ps)) {
    const nc = Reflect.get(ps, "normalized_code");
    if (typeof nc === "string") {
      previewNorm = nc;
    }
  }
  return {
    id: n.id,
    type: nodeType,
    shape_code: code,
    preview_normalized: previewNorm,
    has_preview_scene: Boolean(ps && typeof ps === "object"),
  };
}

function logShapeNodesSummary(tag: string, nodes: Node[] | undefined): void {
  if (!nodes?.length) {
    macroGraphDebug(tag, "no nodes");
    return;
  }
  const shapes: Record<string, unknown>[] = [];
  for (const n of nodes) {
    const row = summarizeShapeNodeForDebug(n);
    if (row) {
      shapes.push(row);
    }
  }
  macroGraphDebug(tag, { shapeNodeCount: shapes.length, shapes });
}

export function useRecipeGraphRecompute(options: {
  recipeId: number;
  recomputeUrl: string;
  nodesRef: RefBox<Node[]>;
  edgesRef: RefBox<Edge[]>;
  setNodes: Dispatch<SetStateAction<Node[]>>;
  setEdges: Dispatch<SetStateAction<Edge[]>>;
  catalogIconByOpRef: RefBox<Map<string, string>>;
}) {
  const {
    recipeId,
    recomputeUrl,
    nodesRef,
    edgesRef,
    setNodes,
    setEdges,
    catalogIconByOpRef,
  } = options;

  const [busy, setBusy] = useState(false);
  const [validationOk, setValidationOk] = useState<boolean | null>(null);
  const [footerHint, setFooterHint] = useState("");

  const silentDebounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const silentAbortRef = useRef<AbortController | null>(null);
  const silentLatestGraphRef = useRef<{ nodes: Node[]; edges: Edge[] } | null>(null);

  useEffect(
    () => () => {
      if (silentDebounceTimerRef.current !== null) {
        clearTimeout(silentDebounceTimerRef.current);
        silentDebounceTimerRef.current = null;
      }
      silentAbortRef.current?.abort();
      silentAbortRef.current = null;
    },
    [],
  );

  const applyRecomputeJson = useCallback(
    (json: RecipeGraphRecomputeResponse, meta: ApplyMeta) => {
      macroGraphDebug("recompute apply", {
        silent: Boolean(meta.silent),
        commit: meta.commit,
        warnings: json.warnings,
        validationOk: json.validation?.ok,
      });
      logShapeNodesSummary("recompute server react_flow.nodes (incoming)", json.react_flow?.nodes as Node[] | undefined);
      if (meta.silent) {
        setNodes((current) => {
          const withIssues = applyValidationIssuesToNodes(current, json.validation?.issues);
          const withPreview = mergeSilentPreviewFromServer(
            withIssues,
            json.react_flow?.nodes as Node[] | undefined,
          );
          return enrichNodesWithCatalogIcons(withPreview, catalogIconByOpRef.current);
        });
        const vok = json.validation?.ok;
        setValidationOk(typeof vok === "boolean" ? vok : null);
        return;
      }

      if (json.react_flow?.nodes && Array.isArray(json.react_flow.edges)) {
        const serverNodes = json.react_flow.nodes as Node[];
        const rawEdges = json.react_flow.edges as Edge[];
        const issues = json.validation?.issues;

        const withVal = applyValidationIssuesToNodes(serverNodes, issues);
        setNodes(enrichNodesWithCatalogIcons(withVal, catalogIconByOpRef.current));
        const nextEdges = ensurePainterTargetHandlesOnEdges(withVal, rawEdges).map((e) => ({
          ...e,
          type: e.type ?? "recipe",
        }));
        setEdges(nextEdges);
      }
      const vok = json.validation?.ok;
      setValidationOk(typeof vok === "boolean" ? vok : null);
      const issues = json.validation?.issues;
      const issueCount = Array.isArray(issues) ? issues.length : 0;
      let nextFooterHint: string;
      if (!meta.commit) {
        nextFooterHint = `Dry-run · ${issueCount} validation note(s)`;
      } else if (json.steps_synced) {
        nextFooterHint = "Saved · steps synced";
      } else {
        nextFooterHint = "Saved (steps not synced)";
      }
      setFooterHint(nextFooterHint);
      setGlobalStatus(
        meta.commit ? "Recompute & save complete." : "Dry-run complete. Review validation.",
        false,
      );
    },
    [catalogIconByOpRef, setEdges, setNodes],
  );

  const silentDryRunFromGraph = useCallback(
    (nodeList: Node[], edgeList: Edge[]) => {
      if (!recomputeUrl || !recipeId) {
        return;
      }
      silentLatestGraphRef.current = { nodes: nodeList, edges: edgeList };
      if (silentDebounceTimerRef.current !== null) {
        clearTimeout(silentDebounceTimerRef.current);
      }
      silentDebounceTimerRef.current = setTimeout(() => {
        silentDebounceTimerRef.current = null;
        const latest = silentLatestGraphRef.current;
        if (!latest) {
          return;
        }
        silentAbortRef.current?.abort();
        const ac = new AbortController();
        silentAbortRef.current = ac;
        void (async () => {
          try {
            const rf = buildReactFlowSnapshot(latest.nodes, latest.edges);
            const json = await postRecipeGraphRecompute(
              recomputeUrl,
              { react_flow: rf },
              { signal: ac.signal },
            );
            if (ac.signal.aborted) {
              return;
            }
            applyRecomputeJson(json, { commit: false, silent: true });
          } catch {
            if (!ac.signal.aborted) {
              // Keep local wiring; user can use Dry-run for an error message.
            }
          }
        })();
      }, SILENT_RECOMPUTE_DEBOUNCE_MS);
    },
    [applyRecomputeJson, recipeId, recomputeUrl],
  );

  const runRecompute = useCallback(
    async (commit: boolean) => {
      if (!recomputeUrl) {
        setGlobalStatus("Missing recompute API URL in bootstrap.", true);
        return;
      }
      if (!recipeId) {
        setGlobalStatus("Missing recipe id.", true);
        return;
      }
      setBusy(true);
      setGlobalStatus(commit ? "Saving…" : "Recomputing…", false);
      try {
        const rf = buildReactFlowSnapshot(nodesRef.current, edgesRef.current);
        const payload: Record<string, unknown> = { react_flow: rf };
        if (commit) {
          payload.commit = true;
        }
        const json = await postRecipeGraphRecompute(recomputeUrl, payload);
        applyRecomputeJson(json, { commit });
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Request failed";
        setGlobalStatus(msg, true);
        setFooterHint("");
      } finally {
        setBusy(false);
      }
    },
    [applyRecomputeJson, edgesRef, nodesRef, recipeId, recomputeUrl],
  );

  const onDryRun = useCallback(() => {
    void runRecompute(false);
  }, [runRecompute]);

  const onSave = useCallback(() => {
    void runRecompute(true);
  }, [runRecompute]);

  return {
    busy,
    validationOk,
    footerHint,
    silentDryRunFromGraph,
    runRecompute,
    onDryRun,
    onSave,
  };
}
