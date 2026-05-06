import { useCallback, useRef, useState } from "react";

import type { Connection, Edge, IsValidConnection, Node } from "@xyflow/react";

import { RECIPE_CONNECTION_WARN_THROTTLE_MS } from "../EditorFoundation/constants";
import { setGlobalStatus } from "../GraphEditor/globalStatus";
import {
  evaluateRecipeConnection,
  normalizeMaterialToPainterConnection,
  wouldConnectAfterRemovals,
} from "../RecipeConnection";

export function useRecipeGraphConnectionFeedback(nodes: Node[], edges: Edge[]) {
  const [connectionFeedback, setConnectionFeedback] = useState("");
  const connInspectorMsgRef = useRef("");
  const warnConnAtMs = useRef(0);

  const clearConnectionInspectorFeedback = useCallback(() => {
    connInspectorMsgRef.current = "";
    setConnectionFeedback("");
  }, []);

  const isValidConnection = useCallback<IsValidConnection>(
    (edge) => {
      if (!edge.source || !edge.target) {
        return false;
      }
      const c: Connection = normalizeMaterialToPainterConnection(nodes, {
        source: edge.source,
        target: edge.target,
        sourceHandle: edge.sourceHandle ?? null,
        targetHandle: edge.targetHandle ?? null,
      });
      const res = evaluateRecipeConnection(nodes, edges, c);
      if (res.ok) {
        clearConnectionInspectorFeedback();
        return true;
      }
      if (wouldConnectAfterRemovals(nodes, edges, c)) {
        clearConnectionInspectorFeedback();
        return true;
      }
      if (res.message !== connInspectorMsgRef.current) {
        connInspectorMsgRef.current = res.message;
        setConnectionFeedback(res.message);
      }
      const now = Date.now();
      if (now - warnConnAtMs.current > RECIPE_CONNECTION_WARN_THROTTLE_MS) {
        warnConnAtMs.current = now;
        setGlobalStatus(res.message, true);
      }
      return false;
    },
    [clearConnectionInspectorFeedback, edges, nodes],
  );

  return {
    connectionFeedback,
    clearConnectionInspectorFeedback,
    isValidConnection,
  };
}
