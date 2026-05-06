import { useCallback, useState } from "react";

import type { Node } from "@xyflow/react";

export function useRecipeGraphSelection() {
  const [selectedNodeIds, setSelectedNodeIds] = useState<string[]>([]);

  const handleSelectionChange = useCallback((params: { nodes: Node[] }) => {
    setSelectedNodeIds(params.nodes.map((n) => n.id));
  }, []);

  return { selectedNodeIds, handleSelectionChange };
}
