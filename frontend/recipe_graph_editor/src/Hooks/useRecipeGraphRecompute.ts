import type { Dispatch, SetStateAction } from "react";
import { useCallback, useState } from "react";

import type { Edge, Node } from "@xyflow/react";

import { setGlobalStatus } from "../GraphEditor/globalStatus";
import { mergeSilentPreviewFromServer } from "../RecipeGraph/mergeSilentPreviewFromServer";
import { postRecipeGraphRecompute, type RecipeGraphRecomputeResponse } from "../RecipeGraph/api";
import { buildReactFlowSnapshot } from "../EditorFoundation/reactFlowSnapshot";
import { ensurePainterTargetHandlesOnEdges } from "../RecipeConnection";
import { enrichNodesWithCatalogIcons } from "../Operation/nodeCatalogMerge";
import { applyValidationIssuesToNodes } from "../EditorFoundation/validationIssuesNodes";

/** Ref holder (avoids deprecated `MutableRefObject` in Sonar ruleset). */
type RefBox<T> = { current: T };

type ApplyMeta = { commit: boolean; silent?: boolean };

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

  const applyRecomputeJson = useCallback(
    (json: RecipeGraphRecomputeResponse, meta: ApplyMeta) => {
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
    async (nodeList: Node[], edgeList: Edge[]) => {
      if (!recomputeUrl || !recipeId) {
        return;
      }
      try {
        const rf = buildReactFlowSnapshot(nodeList, edgeList);
        const json = await postRecipeGraphRecompute(recomputeUrl, { react_flow: rf });
        applyRecomputeJson(json, { commit: false, silent: true });
      } catch {
        // Keep local wiring; user can use Dry-run for an error message.
      }
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
