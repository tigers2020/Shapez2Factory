import { initGraphViewport } from "./graph_viewport.js?v=20260508-pinned-layout";
import { renderSelectedNodeDetail } from "./graph_detail.js?v=20260504-modal";
import { renderSolverGraph } from "./graph_markup.js?v=20260504-grid-pinned";
import { setStepsHtml } from "./dom_utils.js?v=20260502-graph-ui-2";

/** Shared `Promise#catch` handler so deep listeners stay shallow. */
function swallowPromiseRejection() {
  /* intentionally empty */
}

function initGraphPreviewFallbacks(canvas) {
  const maxPreviewRetries = 3;

  canvas.querySelectorAll("[data-graph-preview-image]").forEach((img) => {
    const fallback = img.parentElement?.querySelector("[data-graph-preview-fallback]");
    if (!fallback) {
      return;
    }

    const showFallback = () => {
      img.classList.add("hidden");
      fallback.classList.remove("hidden");
    };

    const baseSrc = img.getAttribute("src") || "";
    let attemptIndex = 0;
    let retryTimerId;

    const previewRetryDelayMs = (attemptZeroBased) => 200 * 2 ** attemptZeroBased;

    const onError = () => {
      if (retryTimerId !== undefined) {
        globalThis.clearTimeout(retryTimerId);
        retryTimerId = undefined;
      }
      if (attemptIndex < maxPreviewRetries) {
        const delayMs = previewRetryDelayMs(attemptIndex);
        attemptIndex += 1;
        retryTimerId = globalThis.setTimeout(() => {
          retryTimerId = undefined;
          const sep = baseSrc.includes("?") ? "&" : "?";
          img.src = `${baseSrc}${sep}_sgPvRetry=${attemptIndex}`;
        }, delayMs);
        return;
      }
      showFallback();
    };

    img.addEventListener("error", onError);
    if (img.complete && typeof img.naturalWidth === "number" && img.naturalWidth === 0) {
      onError();
    }
  });
}

function dismissStaffNodeContextMenu() {
  const existing = document.getElementById("macro-staff-graph-ctx-menu");
  if (existing) {
    existing.remove();
  }
}

/**
 * @param {number} clientX
 * @param {number} clientY
 * @param {{ id: string, label: string }[]} items
 * @param {(id: string) => void} onPick
 */
function showStaffNodeContextMenu(clientX, clientY, items, onPick) {
  dismissStaffNodeContextMenu();
  const menu = document.createElement("div");
  menu.id = "macro-staff-graph-ctx-menu";
  menu.className =
    "fixed z-[200] min-w-[10rem] rounded-lg border border-slate-600 bg-slate-900 py-1 text-sm shadow-xl";
  menu.style.left = `${Math.min(clientX, globalThis.innerWidth - 16)}px`;
  menu.style.top = `${Math.min(clientY, globalThis.innerHeight - 16)}px`;
  menu.setAttribute("role", "menu");
  for (const item of items) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className =
      "block w-full px-3 py-2 text-left text-slate-100 hover:bg-slate-800 focus-visible:bg-slate-800 focus-visible:outline-none";
    btn.textContent = item.label;
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      dismissStaffNodeContextMenu();
      onPick(item.id);
    });
    menu.appendChild(btn);
  }
  document.body.appendChild(menu);
  const onDoc = (e) => {
    if (menu.contains(/** @type {Node} */ (e.target))) {
      return;
    }
    dismissStaffNodeContextMenu();
    document.removeEventListener("pointerdown", onDoc, true);
  };
  setTimeout(() => {
    document.addEventListener("pointerdown", onDoc, true);
  }, 0);
}

/**
 * @typedef {{ from: string, to: string, kind: string, slot?: string }} RecipeWireEdgeDraft
 * @typedef {(edge: RecipeWireEdgeDraft) => void | Promise<void>} RecipeWireConnectHandler
 * @typedef {(edge: RecipeWireEdgeDraft) => void | Promise<void>} RecipeWireDeleteHandler
 * @typedef {(nodeId: string) => void} GraphNodeSelectHandler
 * @typedef {(args: { nodeId: string, x: number, y: number }) => void | Promise<void>} RecipeNodeDragCommitHandler
 * @typedef {{ kind: "shape" } | { kind: "operation", operation: string }} RecipeCanvasDropPayload
 * @typedef {(args: RecipeCanvasDropPayload & { graphX: number, graphY: number }) => void | Promise<void>} RecipeCanvasDropHandler
 */

/**
 * Palette drag-drop: convert viewport client coords to graph space using viewport pan/zoom.
 *
 * @param {HTMLElement} canvas
 * @param {RecipeCanvasDropHandler} onDrop
 */
function initRecipeCanvasDrop(canvas, onDrop) {
  const viewport = canvas.querySelector("[data-graph-viewport]");
  if (!viewport || typeof onDrop !== "function") {
    return;
  }
  viewport.addEventListener("dragover", (e) => {
    e.preventDefault();
    try {
      e.dataTransfer.dropEffect = "copy";
    } catch {
      /* ignore */
    }
  });
  viewport.addEventListener("drop", (e) => {
    e.preventDefault();
    let raw = e.dataTransfer.getData("application/x-macro-palette");
    if (!raw) {
      raw = e.dataTransfer.getData("text/plain");
    }
    if (!raw) {
      return;
    }
    let payload;
    try {
      payload = JSON.parse(raw);
    } catch {
      return;
    }
    if (!payload || typeof payload !== "object" || !payload.kind) {
      return;
    }
    const st = viewport._graphTransform;
    if (!st) {
      return;
    }
    const rect = viewport.getBoundingClientRect();
    const cx = e.clientX - rect.left;
    const cy = e.clientY - rect.top;
    const gx = (cx - st.x) / st.scale;
    const gy = (cy - st.y) / st.scale;
    void Promise.resolve(
      onDrop(
        /** @type {RecipeCanvasDropPayload & { graphX: number, graphY: number }} */ ({
          ...payload,
          graphX: gx,
          graphY: gy,
        }),
      ),
    ).catch(swallowPromiseRejection);
  });
}

/**
 * @param {HTMLElement} canvas
 * @param {{ _displayedGraph?: { nodes?: { id: string, kind: string }[] } }}} panel
 * @param {RecipeWireConnectHandler} onConnect
 */
function initRecipeGraphPortWire(canvas, panel, onConnect) {
  const viewport = canvas.querySelector("[data-graph-viewport]");
  if (!viewport) {
    return;
  }

  const readSpec = (el) => {
    const port = el?.closest?.("[data-graph-port]");
    if (!port) {
      return null;
    }
    const owner = port.dataset.graphPortOwner;
    const flow = port.dataset.graphPortFlow;
    if (!owner || (flow !== "in" && flow !== "out")) {
      return null;
    }
    const raw = port.dataset.graphPortIndex;
    const parsed = raw === undefined || raw === "" ? 0 : Number(raw);
    const index = Number.isFinite(parsed) ? parsed : 0;
    const graph = panel._displayedGraph;
    const node = (graph?.nodes || []).find((n) => n.id === owner);
    if (!node) {
      return null;
    }
    return { owner, flow, index, nodeKind: node.kind, el: port };
  };

  const normalizeWire = (a, b) => {
    const aOut = a.flow === "out";
    const bIn = b.flow === "in";
    const bOut = b.flow === "out";
    const aIn = a.flow === "in";
    if (aOut && bIn) {
      return [a, b];
    }
    if (bOut && aIn) {
      return [b, a];
    }
    return null;
  };

  /** @param {{ owner: string, nodeKind: string, index: number }} outP @param {{ owner: string, nodeKind: string, index: number }} inP */
  const edgeDraft = (outP, inP) => {
    if (outP.owner === inP.owner) {
      return null;
    }
    if (outP.nodeKind === "shape" && inP.nodeKind === "operation") {
      /** @type {RecipeWireEdgeDraft} */
      const edge = { from: outP.owner, to: inP.owner, kind: "input" };
      if (inP.index > 0) {
        edge.slot = String(inP.index);
      }
      return edge;
    }
    if (outP.nodeKind === "operation" && inP.nodeKind === "shape") {
      /** @type {RecipeWireEdgeDraft} */
      const edge = { from: outP.owner, to: inP.owner, kind: "output" };
      if (outP.index > 0) {
        edge.slot = String(outP.index);
      }
      return edge;
    }
    return null;
  };

  canvas.addEventListener("pointerdown", (event) => {
    const port = event.target.closest("[data-graph-port]");
    if (!port) {
      return;
    }
    event.preventDefault();
    const startSpec = readSpec(port);
    if (!startSpec) {
      return;
    }

    const overlay = document.createElement("div");
    overlay.className = "pointer-events-none absolute inset-0 z-[34]";
    overlay.dataset.graphWireOverlay = "1";
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "absolute inset-0 h-full w-full overflow-visible");
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("stroke", "rgba(52, 211, 153, 0.9)");
    line.setAttribute("stroke-width", "2");
    line.setAttribute("stroke-linecap", "round");
    svg.appendChild(line);
    overlay.appendChild(svg);
    viewport.appendChild(overlay);

    const startClientX = event.clientX;
    const startClientY = event.clientY;
    let moved = false;

    const setLineTo = (clientX, clientY) => {
      const vr = viewport.getBoundingClientRect();
      const pr = port.getBoundingClientRect();
      const x1 = pr.left + pr.width / 2 - vr.left;
      const y1 = pr.top + pr.height / 2 - vr.top;
      const x2 = clientX - vr.left;
      const y2 = clientY - vr.top;
      line.setAttribute("x1", String(x1));
      line.setAttribute("y1", String(y1));
      line.setAttribute("x2", String(x2));
      line.setAttribute("y2", String(y2));
    };

    setLineTo(event.clientX, event.clientY);

    const onMove = (ev) => {
      ev.preventDefault();
      if (Math.hypot(ev.clientX - startClientX, ev.clientY - startClientY) > 4) {
        moved = true;
      }
      setLineTo(ev.clientX, ev.clientY);
    };

    const cleanup = () => {
      document.removeEventListener("pointermove", onMove, true);
      document.removeEventListener("pointerup", onUp, true);
      document.removeEventListener("pointercancel", onUp, true);
      document.removeEventListener("keydown", onKey, true);
      overlay.remove();
    };

    const onKey = (ev) => {
      if (ev.key === "Escape") {
        cleanup();
      }
    };

    const onUp = (ev) => {
      cleanup();
      if (!moved) {
        return;
      }
      const endSpec = readSpec(document.elementFromPoint(ev.clientX, ev.clientY));
      if (!endSpec) {
        return;
      }
      const ends = normalizeWire(startSpec, endSpec);
      if (!ends) {
        return;
      }
      const edge = edgeDraft(ends[0], ends[1]);
      if (!edge) {
        return;
      }
      void Promise.resolve(onConnect(edge)).catch(swallowPromiseRejection);
    };

    document.addEventListener("pointermove", onMove, { capture: true, passive: false });
    document.addEventListener("pointerup", onUp, { capture: true });
    document.addEventListener("pointercancel", onUp, { capture: true });
    document.addEventListener("keydown", onKey, { capture: true });
  });
}

/**
 * Staff/macro: pointer-hit on rendered wires removes matching graph_document edge.
 *
 * @param {HTMLElement} canvas
 * @param {{ _displayedGraph?: { edges?: unknown[] } }} panel
 * @param {RecipeWireDeleteHandler} onDelete
 */
function initRecipeGraphWireDelete(canvas, panel, onDelete) {
  if (typeof onDelete !== "function") {
    return;
  }
  const viewport = canvas.querySelector("[data-graph-viewport]");
  if (!viewport) {
    return;
  }
  viewport.addEventListener("pointerdown", (event) => {
    const hit = event.target.closest("[data-graph-edge-hit]");
    if (!hit) {
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    const from = hit.dataset.graphEdgeFrom || "";
    const to = hit.dataset.graphEdgeTo || "";
    const kind = hit.dataset.graphEdgeKind || "";
    /** @type {RecipeWireEdgeDraft} */
    const draft = { from, to, kind };
    const sl = hit.dataset.graphEdgeSlot;
    if (sl != null && sl !== "") {
      draft.slot = sl;
    }
    void Promise.resolve(onDelete(draft)).catch(swallowPromiseRejection);
  });
}

/**
 * @param {HTMLElement} canvas
 * @param {{ _displayedGraph?: { nodes?: { id: string, kind: string, x?: number, y?: number }[] } }}} panel
 * @param {RecipeNodeDragCommitHandler} onCommit
 */
function initRecipeGraphNodeDrag(canvas, panel, onCommit) {
  if (typeof onCommit !== "function") {
    return;
  }
  const viewport = canvas.querySelector("[data-graph-viewport]");
  if (!viewport) {
    return;
  }

  canvas.querySelectorAll("[data-graph-node-id]").forEach((nodeEl) => {
    nodeEl.addEventListener("pointerdown", (event) => {
      if (event.target.closest("[data-graph-port]")) {
        return;
      }
      if (event.pointerType === "mouse" && event.button !== 0) {
        return;
      }
      const graph = panel._displayedGraph;
      const nodeId = nodeEl.dataset.graphNodeId;
      const node = graph?.nodes?.find((n) => n.id === nodeId);
      if (!node || typeof node.x !== "number" || typeof node.y !== "number") {
        return;
      }
      const state = viewport._graphTransform;
      if (!state) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();

      const startClientX = event.clientX;
      const startClientY = event.clientY;
      const scale = state.scale || 1;
      const startRawX = Number(node.x);
      const startRawY = Number(node.y);
      const startLeft = Number.parseFloat(nodeEl.style.left || "0");
      const startTop = Number.parseFloat(nodeEl.style.top || "0");
      let moved = false;

      nodeEl.setPointerCapture(event.pointerId);
      const prevZ = nodeEl.style.zIndex;
      const prevCursor = nodeEl.style.cursor;
      nodeEl.style.zIndex = "40";
      nodeEl.style.cursor = "grabbing";

      const onMove = (ev) => {
        ev.preventDefault();
        const dx = (ev.clientX - startClientX) / scale;
        const dy = (ev.clientY - startClientY) / scale;
        if (Math.hypot(dx, dy) > 2) {
          moved = true;
        }
        nodeEl.style.left = `${startLeft + dx}px`;
        nodeEl.style.top = `${startTop + dy}px`;
      };

      const cleanup = () => {
        document.removeEventListener("pointermove", onMove, true);
        document.removeEventListener("pointerup", onUp, true);
        document.removeEventListener("pointercancel", onUp, true);
        nodeEl.style.zIndex = prevZ;
        nodeEl.style.cursor = prevCursor;
      };

      const onUp = (ev) => {
        cleanup();
        try {
          nodeEl.releasePointerCapture(ev.pointerId);
        } catch {
          /* ignore */
        }
        if (!moved) {
          return;
        }
        panel._suppressNextNodeClick = true;
        const dx = (ev.clientX - startClientX) / scale;
        const dy = (ev.clientY - startClientY) / scale;
        const newRawX = startRawX + dx;
        const newRawY = startRawY + dy;
        void Promise.resolve(onCommit({ nodeId, x: newRawX, y: newRawY })).catch(
          swallowPromiseRejection,
        );
      };

      document.addEventListener("pointermove", onMove, { capture: true, passive: false });
      document.addEventListener("pointerup", onUp, { capture: true });
      document.addEventListener("pointercancel", onUp, { capture: true });
    });
  });
}

/**
 * @param {HTMLElement} panel
 * @param {{ nodes?: unknown[], edges?: unknown[] }} graph
 * @param {{
 *   recipeWireConnect?: RecipeWireConnectHandler
 *   recipeWireDelete?: RecipeWireDeleteHandler
 *   onGraphNodeSelect?: GraphNodeSelectHandler
 *   recipeNodeDragCommit?: RecipeNodeDragCommitHandler
 *   recipeCanvasDrop?: RecipeCanvasDropHandler
 *   staffNodeModalUi?: boolean
 *   staffOpenNodeDetailModal?: (nodeId: string) => void | Promise<void>
 *   staffOpenNodeEditModal?: (nodeId: string) => void
 * } | null | undefined} [options]
 */
export async function mountGraph(panel, graph, options) {
  const canvas = panel.querySelector("[data-solver-graph-canvas]");
  if (!canvas) {
    return;
  }
  panel._displayedGraph = graph;

  const edgeHits = typeof options?.recipeWireDelete === "function";
  setStepsHtml(
    canvas,
    renderSolverGraph(graph, edgeHits ? { includeEdgeHitForDelete: true } : undefined),
  );
  initGraphPreviewFallbacks(canvas);
  initGraphViewport(canvas);

  const dropHandler = options?.recipeCanvasDrop;
  if (typeof dropHandler === "function") {
    initRecipeCanvasDrop(canvas, dropHandler);
  }

  const selectNode = (nodeId) => {
    panel._selectedGraphNodeId = nodeId;
    for (const el of canvas.querySelectorAll("[data-graph-node-id]")) {
      const on = el.dataset.graphNodeId === nodeId;
      el.classList.toggle("ring-2", on);
      el.classList.toggle("ring-inset", on);
      el.classList.toggle("ring-cyan-200", on);
    }
    if (!options?.staffNodeModalUi) {
      renderSelectedNodeDetail(panel, graph, nodeId);
    }
    if (typeof options?.onGraphNodeSelect === "function") {
      options.onGraphNodeSelect(nodeId);
    }
  };

  canvas.querySelectorAll("[data-graph-node-id]").forEach((nodeEl) => {
    nodeEl.addEventListener("click", (event) => {
      if (event.target.closest("[data-graph-port]")) {
        return;
      }
      if (panel._suppressNextNodeClick) {
        panel._suppressNextNodeClick = false;
        event.preventDefault();
        event.stopPropagation();
        return;
      }
      selectNode(nodeEl.dataset.graphNodeId);
    });
    const body = nodeEl.querySelector("[data-graph-node-body]");
    const keyTarget = body || nodeEl;
    keyTarget.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectNode(nodeEl.dataset.graphNodeId);
      }
    });
  });

  const staffDetail = options?.staffOpenNodeDetailModal;
  const staffEdit = options?.staffOpenNodeEditModal;
  if (
    options?.staffNodeModalUi &&
    (typeof staffDetail === "function" || typeof staffEdit === "function")
  ) {
    canvas.querySelectorAll("[data-graph-node-id]").forEach((nodeEl) => {
      nodeEl.addEventListener(
        "contextmenu",
        (e) => {
          if (e.target.closest("[data-graph-port]")) {
            return;
          }
          e.preventDefault();
          e.stopPropagation();
          const nid = nodeEl.dataset.graphNodeId;
          if (!nid) {
            return;
          }
          const items = [];
          if (typeof staffDetail === "function") {
            items.push({ id: "details", label: globalThis.shapezUiT("Node info") });
          }
          if (typeof staffEdit === "function") {
            items.push({ id: "edit", label: globalThis.shapezUiT("Edit node") });
          }
          if (items.length === 0) {
            return;
          }
          showStaffNodeContextMenu(e.clientX, e.clientY, items, (actionId) => {
            selectNode(nid);
            if (actionId === "details" && typeof staffDetail === "function") {
              void Promise.resolve(staffDetail(nid)).catch(swallowPromiseRejection);
            }
            if (actionId === "edit" && typeof staffEdit === "function") {
              staffEdit(nid);
            }
          });
        },
        true,
      );
      nodeEl.addEventListener(
        "dblclick",
        (e) => {
          if (e.target.closest("[data-graph-port]")) {
            return;
          }
          e.preventDefault();
          e.stopPropagation();
          const nid = nodeEl.dataset.graphNodeId;
          if (!nid || typeof staffEdit !== "function") {
            return;
          }
          selectNode(nid);
          staffEdit(nid);
        },
        true,
      );
    });
  }

  const wireHandler = options?.recipeWireConnect;
  if (typeof wireHandler === "function") {
    initRecipeGraphPortWire(canvas, panel, wireHandler);
  }

  const dragHandler = options?.recipeNodeDragCommit;
  if (typeof dragHandler === "function") {
    initRecipeGraphNodeDrag(canvas, panel, dragHandler);
  }

  const deleteHandler = options?.recipeWireDelete;
  if (typeof deleteHandler === "function") {
    initRecipeGraphWireDelete(canvas, panel, deleteHandler);
  }

  const selectedNodeId = resolveSelectedNodeId(graph, panel._selectedGraphNodeId);
  const targetNode = (graph.nodes || []).find(
    (node) => node.kind === "shape" && node.role === "target",
  );
  const firstNode = selectedNodeId
    ? (graph.nodes || []).find((node) => node.id === selectedNodeId)
    : targetNode || (graph.nodes || [])[0];
  if (firstNode) {
    selectNode(firstNode.id);
  }

  panel._selectDisplayedGraphNode = selectNode;
}

function resolveSelectedNodeId(graph, selectedNodeId) {
  if (!selectedNodeId) {
    return null;
  }
  const exact = (graph.nodes || []).find((node) => node.id === selectedNodeId);
  if (exact) {
    return exact.id;
  }
  return null;
}
