import { BaseEdge, getBezierPath, type EdgeProps } from "@xyflow/react";
import { memo } from "react";

export const RecipeEdge = memo(function RecipeEdge(props: EdgeProps) {
  const {
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    markerEnd,
    interactionWidth,
    data,
  } = props;
  const [path] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
  });
  const dk =
    data && typeof data === "object" && "domainKind" in data
      ? String((data as { domainKind?: string }).domainKind)
      : "";
  const stroke =
    dk === "delivery"
      ? "rgb(251 146 60)"
      : dk === "output"
        ? "rgb(192 132 252)"
        : "rgb(45 212 191)";
  return (
    <BaseEdge
      id={id}
      interactionWidth={interactionWidth ?? 14}
      markerEnd={markerEnd}
      path={path}
      style={{ stroke, strokeWidth: 1.75 }}
    />
  );
});

export const recipeEdgeTypes = {
  recipe: RecipeEdge,
};
