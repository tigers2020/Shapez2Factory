/**
 * Staff macro recipe graph editor (canvas-primary; graph_document kept in memory).
 */
(function () {
  "use strict";

  function readJsonScript(id) {
    const el = document.getElementById(id);
    if (!el || !el.textContent) {
      return null;
    }
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      console.error("macro graph editor: bad JSON in", id, e);
      return null;
    }
  }

  function getCookie(name) {
    if (!document.cookie) {
      return null;
    }
    const parts = document.cookie.split(";");
    for (let i = 0; i < parts.length; i += 1) {
      const cookie = parts[i].trim();
      if (cookie.startsWith(name + "=")) {
        return decodeURIComponent(cookie.substring(name.length + 1));
      }
    }
    return null;
  }

  const bootstrap = readJsonScript("macro-graph-bootstrap");
  const catalog =
    readJsonScript("macro-graph-initial-catalog") || {
      families: [],
      recipes: [],
      strategy_codes: [],
      operations: [],
      recipe_graph_engine_operations: [],
    };
  const editorRoot = document.getElementById("macro-graph-editor-root");
  const statusEl = document.getElementById("macro-graph-status");

  if (!bootstrap || !editorRoot || !bootstrap.api_recipe_graph_recompute) {
    console.warn("[macro graph editor] init skipped.", {
      hasBootstrap: Boolean(bootstrap),
      hasRoot: Boolean(editorRoot),
      api_recipe_graph_recompute: Boolean(bootstrap && bootstrap.api_recipe_graph_recompute),
    });
    return;
  }

  var EMPTY_GRAPH_DOCUMENT = {
    schema_version: 1,
    nodes: [],
    edges: [],
  };

  function graphRecomputeUrl(recipeId) {
    if (bootstrap.api_recipe_graph_recompute) {
      return bootstrap.api_recipe_graph_recompute;
    }
    return String(bootstrap.api_recipe_graph_recompute_pattern || "").replace(
      "__RECIPE_ID__",
      String(recipeId),
    );
  }

  function setGraphDocument(card, doc) {
    card._graphDocument = doc;
    var ta = card.querySelector(".macro-graph-json");
    if (ta) {
      ta.value = JSON.stringify(doc, null, 2);
    }
  }

  function parseGraphTextarea(card) {
    var ta = card.querySelector(".macro-graph-json");
    if (ta && document.activeElement === ta) {
      return JSON.parse(ta.value || "{}");
    }
    var mem = card._graphDocument;
    if (mem && typeof mem === "object") {
      return mem;
    }
    if (!ta) {
      throw new Error("Graph document is not initialized.");
    }
    return JSON.parse(ta.value || "{}");
  }

  function setGraphValidationList(card, validation) {
    var host = card.querySelector("[data-macro-validation-issues]");
    var insVal = card.querySelector("[data-macro-inspector-validation]");
    if (!validation || !validation.issues || !validation.issues.length) {
      if (host) {
        host.innerHTML = "";
        host.classList.add("hidden");
      }
      if (insVal) {
        insVal.innerHTML =
          '<p class="text-[11px] text-emerald-200/90">No issues in the last recompute.</p>';
      }
      return;
    }
    if (host) {
      host.classList.remove("hidden");
    }
    var ok = validation.ok !== false;
    if (host) {
      host.classList.toggle("text-rose-200", !ok);
      host.classList.toggle("text-amber-100/90", ok);
    }
    if (insVal) {
      insVal.classList.toggle("text-rose-200", !ok);
      insVal.classList.toggle("text-amber-100/90", ok);
    }
    var items = validation.issues
      .map(function (it) {
        var sev = esc(it.severity || "warning");
        var msg = esc(it.message || "");
        return '<li><span class="font-semibold uppercase">' + sev + "</span> — " + msg + "</li>";
      })
      .join("");
    var ul = "<ul class=\"list-disc space-y-1 pl-4\">" + items + "</ul>";
    if (host) {
      host.innerHTML = ul;
    }
    if (insVal) {
      insVal.innerHTML = ul;
    }
  }

  function setGraphWarnings(card, warnings) {
    var w = card.querySelector("[data-macro-graph-warnings]");
    if (!w) {
      return;
    }
    if (!warnings || !warnings.length) {
      w.textContent = "";
      w.classList.add("hidden");
      return;
    }
    w.classList.remove("hidden");
    w.textContent = warnings.join(" · ");
  }

  /** 서버 ``recipe_graph_topology`` 와 동일한 연결 규칙 (와이어 추가 시). */
  function validateEdgeTopologyForAppend(gdoc, edge) {
    var fromId = String(edge.from);
    var toId = String(edge.to);
    var kind = String(edge.kind);
    var byId = {};
    (gdoc.nodes || []).forEach(function (n) {
      if (n && n.id != null) {
        byId[String(n.id)] = n;
      }
    });
    var nf = byId[fromId];
    var nt = byId[toId];
    if (!nf || !nt) {
      return { ok: true };
    }
    if (kind === "input") {
      if (nf.kind !== "shape" || nt.kind !== "operation") {
        return { ok: false, message: "Input wire must be shape → operation." };
      }
    } else if (kind === "output") {
      if (nf.kind !== "operation" || nt.kind !== "shape") {
        return { ok: false, message: "Output wire must be operation → shape." };
      }
      var role = String(nt.role || "intermediate").trim();
      if (role !== "intermediate") {
        return {
          ok: false,
          message: "Operation output must connect to an intermediate shape (not target/source).",
        };
      }
    }
    return { ok: true };
  }

  function tryAppendEdgeToGraphDoc(card, edge) {
    var gdoc;
    try {
      gdoc = parseGraphTextarea(card);
    } catch (e2) {
      return { ok: false, message: "Invalid JSON in graph document: " + (e2.message || e2) };
    }
    if (!gdoc || typeof gdoc !== "object") {
      return { ok: false, message: "Graph document is empty or invalid." };
    }
    var fromId = String(edge.from);
    var toId = String(edge.to);
    var kind = String(edge.kind);
    var slotKey = edge.slot != null && String(edge.slot) !== "" ? String(edge.slot) : "";
    if (!fromId || !toId) {
      return { ok: false, message: "Edge from/to missing." };
    }
    if (kind !== "input" && kind !== "output") {
      return { ok: false, message: "Kind must be input or output." };
    }
    var nodeIds = new Set(
      (gdoc.nodes || []).map(function (n) {
        return String(n.id);
      }),
    );
    if (!nodeIds.has(fromId) || !nodeIds.has(toId)) {
      return { ok: false, message: "From and To must be existing node ids in graph_document.nodes." };
    }
    gdoc.edges = Array.isArray(gdoc.edges) ? gdoc.edges : [];
    var dup = gdoc.edges.some(function (e) {
      return (
        String(e.from) === fromId &&
        String(e.to) === toId &&
        String(e.kind) === kind &&
        String((e && e.slot) || "") === slotKey
      );
    });
    if (dup) {
      return { ok: false, message: "An edge with the same from/to/kind/slot already exists." };
    }
    var newEdge = { from: fromId, to: toId, kind: kind };
    if (slotKey) {
      newEdge.slot = slotKey;
    }
    var topo = validateEdgeTopologyForAppend(gdoc, newEdge);
    if (!topo.ok) {
      return topo;
    }
    gdoc.edges.push(newEdge);
    setGraphDocument(card, gdoc);
    return { ok: true, message: "Edge appended to JSON." };
  }

  function tryRemoveEdgeFromGraphDoc(card, edge) {
    var fromId = String(edge.from);
    var toId = String(edge.to);
    var kind = String(edge.kind);
    var slotKey = edge.slot != null && String(edge.slot) !== "" ? String(edge.slot) : "";
    if (!fromId || !toId) {
      return { ok: false, message: "Edge from/to missing." };
    }
    if (kind !== "input" && kind !== "output") {
      return { ok: false, message: "Kind must be input or output." };
    }
    var gdoc;
    try {
      gdoc = parseGraphTextarea(card);
    } catch (e2) {
      return { ok: false, message: "Invalid JSON in graph document: " + (e2.message || e2) };
    }
    gdoc.edges = Array.isArray(gdoc.edges) ? gdoc.edges : [];
    var before = gdoc.edges.length;
    gdoc.edges = gdoc.edges.filter(function (e) {
      if (!e) {
        return true;
      }
      var match =
        String(e.from) === fromId &&
        String(e.to) === toId &&
        String(e.kind) === kind &&
        String((e && e.slot) || "") === slotKey;
      return !match;
    });
    if (gdoc.edges.length === before) {
      return { ok: false, message: "No matching edge in graph_document.edges." };
    }
    setGraphDocument(card, gdoc);
    return { ok: true, message: "Removed edge (" + kind + ") " + fromId + " → " + toId + "." };
  }

  async function remountVisualGraph(card, graph, wireCtx) {
    var host = card.querySelector("[data-macro-visual-graph-host]");
    if (!host) {
      return;
    }
    host.innerHTML = "";
    var g = graph && typeof graph === "object" ? graph : { nodes: [], edges: [] };
    if (!Array.isArray(g.nodes)) {
      g.nodes = [];
    }
    if (!Array.isArray(g.edges)) {
      g.edges = [];
    }
    var staffCtx = wireCtx && wireCtx.recipeId && wireCtx.card;
    if (g.nodes.length || staffCtx) {
      await initMacroGraphMount(host, g, wireCtx || null);
    } else {
      host.innerHTML =
        '<p class="text-xs text-slate-500">No nodes yet — use the <span class="font-semibold text-slate-400">palette</span> (drag onto the canvas), <span class="font-semibold text-slate-400">Add shape</span> / <span class="font-semibold text-slate-400">Add operation</span>, or open <span class="font-semibold text-slate-400">Advanced: raw JSON</span> below.</p>';
    }
  }

  /** @param {{ showStepsSynced?: boolean }} [opts] */
  function stepsSyncedFragment(data, opts) {
    if (!opts || !opts.showStepsSynced) {
      return "";
    }
    if (!data || data.steps_synced !== true) {
      return " DB steps unchanged (could not derive step list from graph).";
    }
    return " DB steps synced from graph.";
  }

  async function runMacroGraphDryRecompute(card, recipeId, statusOpts) {
    statusOpts = statusOpts || {};
    var doc;
    try {
      doc = parseGraphTextarea(card);
    } catch (e) {
      throw new Error("Invalid JSON in graph document: " + (e.message || e));
    }
    var data = await api(
      "POST",
      graphRecomputeUrl(recipeId),
      {
        graph_document: doc,
        commit: false,
      },
      { signal: statusOpts.signal },
    );
    var ta = card.querySelector(".macro-graph-json");
    var preserveTa =
      Boolean(statusOpts.preserveTextareaIfFocused) &&
      ta &&
      document.activeElement === ta;
    if (!preserveTa) {
      setGraphDocument(card, data.graph_document);
    }
    setGraphWarnings(card, data.warnings);
    setGraphValidationList(card, data.validation);
    await remountVisualGraph(card, data.visual_graph, { recipeId: recipeId, card: card });
    if (!statusOpts || !statusOpts.skipStatus) {
      setStatus(
        (data.validation && data.validation.ok === false) ||
          (data.warnings && data.warnings.length)
          ? "Graph recompute done (see validation / warnings on card)."
          : "Graph recompute preview updated.",
      );
    }
    return data;
  }

  function newUniqueGraphNodeId(prefix, gdoc) {
    var existing = new Set(
      (gdoc.nodes || []).map(function (n) {
        return String((n && n.id) || "");
      }),
    );
    var id;
    var attempt;
    for (attempt = 0; attempt < 64; attempt += 1) {
      id = prefix + Math.random().toString(16).slice(2, 12);
      if (!existing.has(id)) {
        return id;
      }
    }
    id = prefix + String(Date.now());
    if (!existing.has(id)) {
      return id;
    }
    return prefix + Math.random().toString(16).slice(2, 14);
  }

  function suggestNewNodeXY(gdoc) {
    var nodes = Array.isArray(gdoc.nodes) ? gdoc.nodes : [];
    var maxX = 0;
    var sumY = 0;
    var i;
    var n;
    var x;
    var y;
    for (i = 0; i < nodes.length; i += 1) {
      n = nodes[i];
      if (!n || typeof n !== "object") {
        continue;
      }
      x = Number(n.x);
      y = Number(n.y);
      if (!Number.isFinite(x)) {
        x = 0;
      }
      if (!Number.isFinite(y)) {
        y = 0;
      }
      maxX = Math.max(maxX, x);
      sumY += y;
    }
    var avgY = nodes.length ? sumY / nodes.length : 0;
    return { x: maxX + 220, y: avgY };
  }

  function snapGraphCoord(v) {
    var g = 20;
    return Math.round(Number(v) / g) * g;
  }

  function tryAppendShapeNodeToGraphDocAt(card, gx, gy) {
    var gdoc;
    try {
      gdoc = parseGraphTextarea(card);
    } catch (e2) {
      return { ok: false, message: "Invalid JSON in graph document: " + (e2.message || e2) };
    }
    gdoc.nodes = Array.isArray(gdoc.nodes) ? gdoc.nodes : [];
    gdoc.edges = Array.isArray(gdoc.edges) ? gdoc.edges : [];
    var id = newUniqueGraphNodeId("shape_", gdoc);
    var xy =
      Number.isFinite(Number(gx)) && Number.isFinite(Number(gy))
        ? { x: snapGraphCoord(gx), y: snapGraphCoord(gy) }
        : suggestNewNodeXY(gdoc);
    gdoc.nodes.push({
      id: id,
      kind: "shape",
      role: "intermediate",
      shape_code: "",
      quantity: 1,
      x: xy.x,
      y: xy.y,
    });
    setGraphDocument(card, gdoc);
    return { ok: true, message: "Added shape node " + id + "." };
  }

  function tryAppendShapeNodeToGraphDoc(card) {
    var gdoc;
    try {
      gdoc = parseGraphTextarea(card);
    } catch (e2) {
      return { ok: false, message: "Invalid JSON in graph document: " + (e2.message || e2) };
    }
    gdoc.nodes = Array.isArray(gdoc.nodes) ? gdoc.nodes : [];
    gdoc.edges = Array.isArray(gdoc.edges) ? gdoc.edges : [];
    var id = newUniqueGraphNodeId("shape_", gdoc);
    var xy = suggestNewNodeXY(gdoc);
    gdoc.nodes.push({
      id: id,
      kind: "shape",
      role: "intermediate",
      shape_code: "",
      quantity: 1,
      x: xy.x,
      y: xy.y,
    });
    setGraphDocument(card, gdoc);
    return { ok: true, message: "Added shape node " + id + "." };
  }

  function tryAppendOperationNodeToGraphDoc(card, operation) {
    var op = String(operation || "").trim();
    if (!op) {
      return { ok: false, message: "Choose an operation type." };
    }
    var allowed = catalog.recipe_graph_engine_operations || [];
    if (allowed.indexOf(op) === -1) {
      return {
        ok: false,
        message: "Operation must be engine-supported (see catalog recipe_graph_engine_operations).",
      };
    }
    var gdoc;
    try {
      gdoc = parseGraphTextarea(card);
    } catch (e2) {
      return { ok: false, message: "Invalid JSON in graph document: " + (e2.message || e2) };
    }
    gdoc.nodes = Array.isArray(gdoc.nodes) ? gdoc.nodes : [];
    gdoc.edges = Array.isArray(gdoc.edges) ? gdoc.edges : [];
    var id = newUniqueGraphNodeId("op_", gdoc);
    var xy = suggestNewNodeXY(gdoc);
    var node = { id: id, kind: "operation", operation: op, x: xy.x, y: xy.y };
    if (op === "painter") {
      node.paint_color = "r";
    }
    gdoc.nodes.push(node);
    setGraphDocument(card, gdoc);
    return { ok: true, message: "Added operation node " + id + " (" + op + ")." };
  }

  function tryAppendOperationNodeToGraphDocAt(card, operation, gx, gy) {
    var op = String(operation || "").trim();
    if (!op) {
      return { ok: false, message: "Choose an operation type." };
    }
    var allowed = catalog.recipe_graph_engine_operations || [];
    if (allowed.indexOf(op) === -1) {
      return {
        ok: false,
        message: "Operation must be engine-supported (see catalog recipe_graph_engine_operations).",
      };
    }
    var gdoc;
    try {
      gdoc = parseGraphTextarea(card);
    } catch (e2) {
      return { ok: false, message: "Invalid JSON in graph document: " + (e2.message || e2) };
    }
    gdoc.nodes = Array.isArray(gdoc.nodes) ? gdoc.nodes : [];
    gdoc.edges = Array.isArray(gdoc.edges) ? gdoc.edges : [];
    var id = newUniqueGraphNodeId("op_", gdoc);
    var xy =
      Number.isFinite(Number(gx)) && Number.isFinite(Number(gy))
        ? { x: snapGraphCoord(gx), y: snapGraphCoord(gy) }
        : suggestNewNodeXY(gdoc);
    var node = { id: id, kind: "operation", operation: op, x: xy.x, y: xy.y };
    if (op === "painter") {
      node.paint_color = "r";
    }
    gdoc.nodes.push(node);
    setGraphDocument(card, gdoc);
    return { ok: true, message: "Added operation node " + id + " (" + op + ")." };
  }

  function tryRemoveNodeFromGraphDoc(card, nodeId) {
    var nid = String(nodeId || "").trim();
    if (!nid) {
      return { ok: false, message: "Select a node in the preview first." };
    }
    var gdoc;
    try {
      gdoc = parseGraphTextarea(card);
    } catch (e2) {
      return { ok: false, message: "Invalid JSON in graph document: " + (e2.message || e2) };
    }
    gdoc.nodes = Array.isArray(gdoc.nodes) ? gdoc.nodes : [];
    gdoc.edges = Array.isArray(gdoc.edges) ? gdoc.edges : [];
    var before = gdoc.nodes.length;
    gdoc.nodes = gdoc.nodes.filter(function (n) {
      return !n || String(n.id) !== nid;
    });
    if (gdoc.nodes.length === before) {
      return { ok: false, message: "Node id not found in graph_document." };
    }
    gdoc.edges = gdoc.edges.filter(function (e) {
      if (!e) {
        return false;
      }
      return String(e.from) !== nid && String(e.to) !== nid;
    });
    setGraphDocument(card, gdoc);
    return { ok: true, message: "Removed node " + nid + " and its edges." };
  }

  function tryMoveGraphNodeInGraphDoc(card, nodeId, x, y) {
    var nid = String(nodeId || "").trim();
    if (!nid) {
      return { ok: false, message: "Node id missing." };
    }
    var gdoc;
    try {
      gdoc = parseGraphTextarea(card);
    } catch (e2) {
      return { ok: false, message: "Invalid JSON in graph document: " + (e2.message || e2) };
    }
    var nodes = Array.isArray(gdoc.nodes) ? gdoc.nodes : [];
    var node = nodes.find(function (n) {
      return n && String(n.id) === nid;
    });
    if (!node) {
      return { ok: false, message: "Node not found in graph_document." };
    }
    var nx = Math.round(Number(x) * 10) / 10;
    var ny = Math.round(Number(y) * 10) / 10;
    if (!Number.isFinite(nx) || !Number.isFinite(ny)) {
      return { ok: false, message: "Invalid coordinates." };
    }
    node.x = nx;
    node.y = ny;
    setGraphDocument(card, gdoc);
    return { ok: true, message: "Moved node " + nid + "." };
  }

  function setPaintEditorVisibility(graphSec, operation) {
    var wrap = graphSec.querySelector(".macro-graph-edit-paint-wrap");
    if (!wrap) {
      return;
    }
    if (String(operation) === "painter") {
      wrap.classList.remove("hidden");
    } else {
      wrap.classList.add("hidden");
    }
  }

  function updateWorkbenchStats(graphSec, card) {
    var el = graphSec.querySelector("[data-macro-inspector-stats]");
    if (!el) {
      return;
    }
    try {
      var gdoc = parseGraphTextarea(card);
      var nn = (gdoc.nodes || []).length;
      var ne = (gdoc.edges || []).length;
      el.textContent = "Nodes: " + nn + " · Edges: " + ne;
    } catch (e) {
      el.textContent = "—";
    }
  }

  function updateMacroGraphToolbar(card, graphSec, nodeId) {
    var label = graphSec.querySelector(".macro-graph-selected-id");
    if (label) {
      label.textContent = nodeId || "none";
    }
    var ins = graphSec.querySelector("[data-macro-inspector-node]");
    var insProp = graphSec.querySelector("[data-macro-inspector-properties]");
    var nid = String(nodeId || "").trim();
    if (ins) {
      if (!nid) {
        ins.innerHTML =
          '<p class="text-[11px] text-slate-500">캔버스에서 노드를 선택하세요.</p>';
        if (insProp) {
          insProp.innerHTML =
            '<p class="text-[11px] text-slate-500">노드를 선택하면 속성이 표시됩니다.</p>';
        }
      } else {
        try {
          var gdoc0 = parseGraphTextarea(card);
          var nodes0 = Array.isArray(gdoc0.nodes) ? gdoc0.nodes : [];
          var n0 = nodes0.find(function (n) {
            return n && String(n.id) === nid;
          });
          if (!n0) {
            ins.innerHTML = '<p class="text-[11px] text-rose-300">노드를 찾을 수 없습니다.</p>';
            if (insProp) {
              insProp.innerHTML = '<p class="text-[11px] text-rose-300">—</p>';
            }
          } else if (n0.kind === "shape") {
            ins.innerHTML =
              '<p class="font-mono text-[11px] text-cyan-200/90">' +
              esc(nid) +
              '</p><p class="mt-1 text-[10px] text-slate-500">shape · ' +
              esc(String(n0.role || "intermediate")) +
              "</p>";
          } else {
            ins.innerHTML =
              '<p class="font-mono text-[11px] text-amber-200/90">' +
              esc(nid) +
              '</p><p class="mt-1 text-[10px] text-slate-500">operation · ' +
              esc(String(n0.operation || "")) +
              "</p>";
          }
        } catch (eI) {
          ins.textContent = "—";
          if (insProp) {
            insProp.textContent = "—";
          }
        }
      }
    }
    var shapeBlock = graphSec.querySelector(".macro-graph-edit-shape-block");
    var opBlock = graphSec.querySelector(".macro-graph-edit-op-block");
    if (!shapeBlock || !opBlock) {
      updateWorkbenchStats(graphSec, card);
      return;
    }
    if (!nid) {
      shapeBlock.classList.add("hidden");
      shapeBlock.classList.remove("grid");
      opBlock.classList.add("hidden");
      opBlock.classList.remove("grid");
      updateWorkbenchStats(graphSec, card);
      return;
    }
    var gdoc;
    try {
      gdoc = parseGraphTextarea(card);
    } catch (e2) {
      shapeBlock.classList.add("hidden");
      shapeBlock.classList.remove("grid");
      opBlock.classList.add("hidden");
      opBlock.classList.remove("grid");
      if (insProp) {
        insProp.textContent = "—";
      }
      updateWorkbenchStats(graphSec, card);
      return;
    }
    var nodes = Array.isArray(gdoc.nodes) ? gdoc.nodes : [];
    var node = nodes.find(function (n) {
      return n && String(n.id) === nid;
    });
    if (!node) {
      shapeBlock.classList.add("hidden");
      shapeBlock.classList.remove("grid");
      opBlock.classList.add("hidden");
      opBlock.classList.remove("grid");
      if (insProp) {
        insProp.innerHTML = '<p class="text-[11px] text-rose-300">노드를 찾을 수 없습니다.</p>';
      }
      updateWorkbenchStats(graphSec, card);
      return;
    }
    if (insProp) {
      if (node.kind === "shape") {
        insProp.innerHTML =
          '<dl class="space-y-0.5 text-[10px] text-slate-300">' +
          '<div><dt class="inline text-slate-500">shape_code</dt> <dd class="inline font-mono">' +
          esc(String(node.shape_code != null ? node.shape_code : "")) +
          "</dd></div>" +
          '<div><dt class="inline text-slate-500">role</dt> <dd class="inline">' +
          esc(String(node.role || "intermediate")) +
          "</dd></div></dl>";
      } else if (node.kind === "operation") {
        var pcv =
          String(node.operation || "") === "painter" && node.paint_color != null
            ? '<div><dt class="inline text-slate-500">paint</dt> <dd class="inline font-mono">' +
              esc(String(node.paint_color)) +
              "</dd></div>"
            : "";
        insProp.innerHTML =
          '<dl class="space-y-0.5 text-[10px] text-slate-300">' +
          '<div><dt class="inline text-slate-500">operation</dt> <dd class="inline font-mono">' +
          esc(String(node.operation || "")) +
          "</dd></div>" +
          pcv +
          "</dl>";
      } else {
        insProp.textContent = "—";
      }
    }
    if (node.kind === "shape") {
      shapeBlock.classList.remove("hidden");
      shapeBlock.classList.add("grid");
      opBlock.classList.add("hidden");
      opBlock.classList.remove("grid");
      var sc = graphSec.querySelector(".macro-graph-edit-shape-code");
      var sr = graphSec.querySelector(".macro-graph-edit-shape-role");
      if (sc) {
        sc.value = node.shape_code != null ? String(node.shape_code) : "";
      }
      if (sr) {
        sr.value = node.role || "intermediate";
      }
    } else if (node.kind === "operation") {
      shapeBlock.classList.add("hidden");
      shapeBlock.classList.remove("grid");
      opBlock.classList.remove("hidden");
      opBlock.classList.add("grid");
      var ot = graphSec.querySelector(".macro-graph-edit-op-type");
      var pc = graphSec.querySelector(".macro-graph-edit-paint-color");
      if (ot) {
        ot.value = String(node.operation || "");
      }
      if (pc) {
        pc.value = node.paint_color != null ? String(node.paint_color) : "";
      }
      setPaintEditorVisibility(graphSec, node.operation);
    } else {
      shapeBlock.classList.add("hidden");
      shapeBlock.classList.remove("grid");
      opBlock.classList.add("hidden");
      opBlock.classList.remove("grid");
    }
    updateWorkbenchStats(graphSec, card);
  }

  function refreshMacroGraphToolbarOperationSelects(graphSec) {
    var addSel = graphSec.querySelector(".macro-graph-add-op-select");
    var editOp = graphSec.querySelector(".macro-graph-edit-op-type");
    var engine = catalog.recipe_graph_engine_operations || [];
    var labels = {};
    (catalog.operations || []).forEach(function (o) {
      labels[o.value] = o.label;
    });
    var optsHtml = engine
      .map(function (v) {
        return '<option value="' + esc(v) + '">' + esc(labels[v] || v) + "</option>";
      })
      .join("");
    if (addSel) {
      addSel.innerHTML = optsHtml;
    }
    if (editOp) {
      editOp.innerHTML = optsHtml;
    }
  }

  function macroPaletteBaseShapeArt() {
    return (
      '<svg class="h-6 w-6 text-cyan-200/90" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<rect x="8" y="8" width="32" height="32" rx="5" stroke="currentColor" stroke-width="2.2"/>' +
      '<path d="M24 8v32M8 24h32" stroke="currentColor" stroke-width="1.5" opacity="0.45"/>' +
      "</svg>"
    );
  }

  /** 팔레트 그룹(표시 순서). 엔진 목록에 있는 연산만 렌더한다. */
  var MACRO_PALETTE_GROUPS = [
    { title: "Shape", shape: true, ops: [] },
    { title: "Rotate", ops: ["rotate_cw", "rotate_ccw", "rotate_180"] },
    { title: "Cut", ops: ["cutter", "half_destroyer", "splitter"] },
    { title: "Flow", ops: ["stacker", "swapper", "pin_pusher"] },
    { title: "Color", ops: ["painter", "color_mixer"] },
  ];

  function macroPaletteShapeCardHtml(shapeTitle) {
    return (
      '<div class="macro-palette-card flex min-w-0 cursor-grab select-none flex-row items-center gap-1.5 rounded border border-cyan-700/50 bg-cyan-950/40 p-1 outline-none ring-0 transition hover:bg-cyan-950/55 hover:ring-1 hover:ring-cyan-500/30 active:cursor-grabbing" draggable="true" data-palette-kind="shape" title="' +
      esc(shapeTitle) +
      '">' +
      '<div class="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-slate-950/90">' +
      macroPaletteBaseShapeArt() +
      "</div>" +
      '<p class="min-w-0 flex-1 text-left text-[9px] font-medium leading-tight text-cyan-100/90">' +
      esc(shapeTitle) +
      "</p>" +
      "</div>"
    );
  }

  function macroPaletteOpCardHtml(op, opLabel, icons) {
    var art;
    if (icons[op]) {
      art =
        '<img src="' +
        esc(icons[op]) +
        '" alt="" class="h-7 w-7 max-w-full shrink-0 object-contain" width="28" height="28" draggable="false" loading="lazy" />';
    } else {
      art =
        '<span class="flex h-7 w-7 shrink-0 items-center justify-center text-[8px] font-mono text-amber-300/80" title="no icon in catalog">?</span>';
    }
    return (
      '<div class="macro-palette-card flex min-w-0 cursor-grab select-none flex-row items-center gap-1.5 rounded border border-amber-800/45 bg-amber-950/30 p-1 outline-none ring-0 transition hover:bg-amber-950/45 hover:ring-1 hover:ring-amber-500/25 active:cursor-grabbing" draggable="true" data-palette-kind="operation" data-palette-op="' +
      esc(op) +
      '" title="' +
      esc(opLabel) +
      '">' +
      '<div class="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-slate-950/90">' +
      art +
      "</div>" +
      '<p class="min-w-0 flex-1 text-left text-[9px] font-medium leading-tight text-amber-100/90">' +
      esc(opLabel) +
      "</p>" +
      "</div>"
    );
  }

  function fillMacroGraphPalette(graphSec) {
    var host = graphSec.querySelector("[data-macro-graph-palette]");
    if (!host) {
      return;
    }
    var engine = catalog.recipe_graph_engine_operations || [];
    var engineSet = {};
    var ei;
    for (ei = 0; ei < engine.length; ei += 1) {
      engineSet[engine[ei]] = true;
    }
    var labels = {};
    var icons = {};
    (catalog.operations || []).forEach(function (o) {
      labels[o.value] = o.label;
      if (o.icon) {
        icons[o.value] = o.icon;
      }
    });
    var shapeTitle = "Base shape";
    var grouped = {};
    var gi;
    var html = "";
    for (gi = 0; gi < MACRO_PALETTE_GROUPS.length; gi += 1) {
      var g = MACRO_PALETTE_GROUPS[gi];
      var sectionInner = "";
      if (g.shape) {
        sectionInner += macroPaletteShapeCardHtml(shapeTitle);
      }
      var oi;
      if (g.ops && g.ops.length) {
        for (oi = 0; oi < g.ops.length; oi += 1) {
          var opKey = g.ops[oi];
          if (!engineSet[opKey]) {
            continue;
          }
          grouped[opKey] = true;
          sectionInner += macroPaletteOpCardHtml(opKey, labels[opKey] || opKey, icons);
        }
      }
      if (!sectionInner) {
        continue;
      }
      html +=
        '<details open class="macro-palette-group rounded border border-slate-800/90 bg-slate-950/70">' +
        '<summary class="cursor-pointer select-none px-1 py-0.5 text-[8px] font-semibold uppercase tracking-wide text-slate-500 hover:text-slate-400">' +
        esc(g.title) +
        "</summary>" +
        '<div class="flex flex-col gap-1 px-1 pb-1 pt-0">' +
        sectionInner +
        "</div></details>";
    }
    var otherOps = [];
    for (ei = 0; ei < engine.length; ei += 1) {
      var ek = engine[ei];
      if (!grouped[ek]) {
        otherOps.push(ek);
      }
    }
    if (otherOps.length) {
      var otherInner = "";
      for (oi = 0; oi < otherOps.length; oi += 1) {
        var ope = otherOps[oi];
        otherInner += macroPaletteOpCardHtml(ope, labels[ope] || ope, icons);
      }
      html +=
        '<details open class="macro-palette-group rounded border border-slate-800/90 bg-slate-950/70">' +
        '<summary class="cursor-pointer select-none px-1 py-0.5 text-[8px] font-semibold uppercase tracking-wide text-slate-500 hover:text-slate-400">Other</summary>' +
        '<div class="flex flex-col gap-1 px-1 pb-1 pt-0">' +
        otherInner +
        "</div></details>";
    }
    host.innerHTML = html;
    host.querySelectorAll("[draggable=true]").forEach(function (el) {
      el.addEventListener("dragstart", function (ev) {
        var kind = el.getAttribute("data-palette-kind");
        var payload =
          kind === "shape"
            ? { kind: "shape" }
            : { kind: "operation", operation: el.getAttribute("data-palette-op") };
        var json = JSON.stringify(payload);
        ev.dataTransfer.setData("application/x-macro-palette", json);
        ev.dataTransfer.setData("text/plain", json);
        ev.dataTransfer.effectAllowed = "copy";
      });
    });
  }

  function wireMacroGraphPaletteGrid(graphSec) {
    var host = graphSec.querySelector("[data-macro-visual-graph-host]");
    var toggle = graphSec.querySelector(".macro-graph-grid-toggle");
    if (!toggle || !host) {
      return;
    }
    var key = "macroStaffRecipeGraphGrid";
    try {
      toggle.checked = window.localStorage.getItem(key) === "1";
    } catch (eSt) {
      /* ignore */
    }
    function apply() {
      host.classList.toggle("recipe-graph-grid-on", toggle.checked);
      try {
        window.localStorage.setItem(key, toggle.checked ? "1" : "0");
      } catch (eSt2) {
        /* ignore */
      }
    }
    apply();
    toggle.addEventListener("change", apply);
  }

  function tryApplySelectedNodeEditsToGraphDoc(card, graphSec) {
    var nid = String(card._macroStaffSelectedGraphNodeId || "").trim();
    if (!nid) {
      return { ok: false, message: "Select a node in the preview first." };
    }
    var gdoc;
    try {
      gdoc = parseGraphTextarea(card);
    } catch (e2) {
      return { ok: false, message: "Invalid JSON in graph document: " + (e2.message || e2) };
    }
    var nodes = Array.isArray(gdoc.nodes) ? gdoc.nodes : [];
    var node = nodes.find(function (n) {
      return n && String(n.id) === nid;
    });
    if (!node) {
      return { ok: false, message: "Selected node not found in JSON." };
    }
    if (node.kind === "shape") {
      var sc = graphSec.querySelector(".macro-graph-edit-shape-code");
      var sr = graphSec.querySelector(".macro-graph-edit-shape-role");
      node.shape_code = sc ? String(sc.value || "").trim() : "";
      node.role = sr ? String(sr.value || "intermediate") : "intermediate";
    } else if (node.kind === "operation") {
      var ot = graphSec.querySelector(".macro-graph-edit-op-type");
      var pc = graphSec.querySelector(".macro-graph-edit-paint-color");
      var opv = ot ? String(ot.value || "").trim() : "";
      if (!opv) {
        return { ok: false, message: "operation is required." };
      }
      node.operation = opv;
      if (opv === "painter") {
        var pch = pc ? String(pc.value || "").trim() : "";
        if (!pch) {
          pch = "r";
        }
        node.paint_color = pch.slice(0, 1);
      } else {
        delete node.paint_color;
      }
    } else {
      return { ok: false, message: "Unknown node kind." };
    }
    setGraphDocument(card, gdoc);
    return { ok: true, message: "Node " + nid + " updated in JSON." };
  }

  function wireMacroGraphCrudEvents(graphSec, card, recipeId) {
    var addShapeBtn = graphSec.querySelector(".macro-graph-add-shape");
    var addOpBtn = graphSec.querySelector(".macro-graph-add-op");
    var addOpSel = graphSec.querySelector(".macro-graph-add-op-select");
    var delBtn = graphSec.querySelector(".macro-graph-del-node");
    var applyBtn = graphSec.querySelector(".macro-graph-apply-edit");
    var editOpType = graphSec.querySelector(".macro-graph-edit-op-type");
    var applyEditDebTimer = null;
    function scheduleApplyAndLivePreview() {
      clearTimeout(applyEditDebTimer);
      applyEditDebTimer = setTimeout(async function () {
        applyEditDebTimer = null;
        var r = tryApplySelectedNodeEditsToGraphDoc(card, graphSec);
        if (!r.ok) {
          return;
        }
        try {
          var data = await runMacroGraphDryRecompute(card, recipeId, { skipStatus: true });
          setGraphWarnings(card, data.warnings);
          setGraphValidationList(card, data.validation);
          updateMacroGraphToolbar(card, graphSec, card._macroStaffSelectedGraphNodeId);
        } catch (e2) {
          setStatus(String(e2.message || e2), true);
        }
      }, 420);
    }
    var scInput = graphSec.querySelector(".macro-graph-edit-shape-code");
    if (scInput) {
      scInput.addEventListener("input", scheduleApplyAndLivePreview);
    }
    var pcInput = graphSec.querySelector(".macro-graph-edit-paint-color");
    if (pcInput) {
      pcInput.addEventListener("input", scheduleApplyAndLivePreview);
    }
    var srSel = graphSec.querySelector(".macro-graph-edit-shape-role");
    if (srSel) {
      srSel.addEventListener("change", async function () {
        var r = tryApplySelectedNodeEditsToGraphDoc(card, graphSec);
        if (!r.ok) {
          setStatus(r.message, true);
          return;
        }
        try {
          var data = await runMacroGraphDryRecompute(card, recipeId, { skipStatus: true });
          setGraphWarnings(card, data.warnings);
          setGraphValidationList(card, data.validation);
          updateMacroGraphToolbar(card, graphSec, card._macroStaffSelectedGraphNodeId);
          setStatus(
            (data.validation && data.validation.ok === false) ||
              (data.warnings && data.warnings.length)
              ? "Role updated — see validation / warnings."
              : "Role updated. Preview refreshed.",
          );
        } catch (e2) {
          setStatus(String(e2.message || e2), true);
        }
      });
    }
    if (editOpType) {
      editOpType.addEventListener("change", async function () {
        setPaintEditorVisibility(graphSec, editOpType.value);
        var r = tryApplySelectedNodeEditsToGraphDoc(card, graphSec);
        if (!r.ok) {
          setStatus(r.message, true);
          return;
        }
        try {
          var data = await runMacroGraphDryRecompute(card, recipeId, { skipStatus: true });
          setGraphWarnings(card, data.warnings);
          setGraphValidationList(card, data.validation);
          updateMacroGraphToolbar(card, graphSec, card._macroStaffSelectedGraphNodeId);
          setStatus(
            (data.validation && data.validation.ok === false) ||
              (data.warnings && data.warnings.length)
              ? "Operation updated — see validation / warnings."
              : "Operation updated. Preview refreshed.",
          );
        } catch (e2) {
          setStatus(String(e2.message || e2), true);
        }
      });
    }
    if (addShapeBtn) {
      addShapeBtn.addEventListener("click", async function () {
        var r = tryAppendShapeNodeToGraphDoc(card);
        if (!r.ok) {
          setStatus(r.message, true);
          return;
        }
        try {
          var data = await runMacroGraphDryRecompute(card, recipeId, { skipStatus: true });
          setGraphWarnings(card, data.warnings);
          setGraphValidationList(card, data.validation);
          setStatus(
            (data.validation && data.validation.ok === false) ||
              (data.warnings && data.warnings.length)
              ? r.message + " Recompute — see validation / warnings."
              : r.message + " Preview updated.",
          );
        } catch (e2) {
          setStatus(String(e2.message || e2), true);
        }
      });
    }
    if (addOpBtn && addOpSel) {
      addOpBtn.addEventListener("click", async function () {
        var r = tryAppendOperationNodeToGraphDoc(card, addOpSel.value);
        if (!r.ok) {
          setStatus(r.message, true);
          return;
        }
        try {
          var data = await runMacroGraphDryRecompute(card, recipeId, { skipStatus: true });
          setGraphWarnings(card, data.warnings);
          setGraphValidationList(card, data.validation);
          setStatus(
            (data.validation && data.validation.ok === false) ||
              (data.warnings && data.warnings.length)
              ? r.message + " Recompute — see validation / warnings."
              : r.message + " Preview updated.",
          );
        } catch (e2) {
          setStatus(String(e2.message || e2), true);
        }
      });
    }
    if (delBtn) {
      delBtn.addEventListener("click", async function () {
        var nid = String(card._macroStaffSelectedGraphNodeId || "").trim();
        if (!nid) {
          setStatus("Select a node in the preview first.", true);
          return;
        }
        if (!window.confirm("Remove node " + nid + " and all edges attached to it?")) {
          return;
        }
        var r = tryRemoveNodeFromGraphDoc(card, nid);
        if (!r.ok) {
          setStatus(r.message, true);
          return;
        }
        card._macroStaffSelectedGraphNodeId = null;
        updateMacroGraphToolbar(card, graphSec, null);
        try {
          var data = await runMacroGraphDryRecompute(card, recipeId, { skipStatus: true });
          setGraphWarnings(card, data.warnings);
          setGraphValidationList(card, data.validation);
          setStatus(
            (data.validation && data.validation.ok === false) ||
              (data.warnings && data.warnings.length)
              ? r.message + " Recompute — see validation / warnings."
              : r.message + " Preview updated.",
          );
        } catch (e2) {
          setStatus(String(e2.message || e2), true);
        }
      });
    }
    if (applyBtn) {
      applyBtn.addEventListener("click", async function () {
        var r = tryApplySelectedNodeEditsToGraphDoc(card, graphSec);
        if (!r.ok) {
          setStatus(r.message, true);
          return;
        }
        try {
          var data = await runMacroGraphDryRecompute(card, recipeId, { skipStatus: true });
          setGraphWarnings(card, data.warnings);
          setGraphValidationList(card, data.validation);
          updateMacroGraphToolbar(card, graphSec, card._macroStaffSelectedGraphNodeId);
          setStatus(
            (data.validation && data.validation.ok === false) ||
              (data.warnings && data.warnings.length)
              ? r.message + " Recompute — see validation / warnings."
              : r.message + " Preview updated.",
          );
          var editDlg = graphSec.querySelector("[data-macro-staff-dialog-edit]");
          if (editDlg && typeof editDlg.close === "function") {
            editDlg.close();
          }
        } catch (e2) {
          setStatus(String(e2.message || e2), true);
        }
      });
    }
  }

  var MACRO_STAFF_DIALOG_ANCHOR_GAP = 12;
  var MACRO_STAFF_DIALOG_VIEWPORT_PAD = 8;

  function clearMacroStaffDialogPosition(dialog) {
    if (!dialog) {
      return;
    }
    dialog.style.margin = "";
    dialog.style.position = "";
    dialog.style.left = "";
    dialog.style.top = "";
    dialog.style.right = "";
    dialog.style.bottom = "";
    dialog.style.transform = "";
  }

  function findGraphNodeElement(card, nodeId) {
    var panel = card.querySelector("[data-macro-graph-panel]");
    if (!panel) {
      return null;
    }
    var canvas = panel.querySelector("[data-solver-graph-canvas]");
    if (!canvas) {
      return null;
    }
    var want = String(nodeId || "");
    var found = null;
    canvas.querySelectorAll("[data-graph-node-id]").forEach(function (el) {
      if (found) {
        return;
      }
      if (String(el.getAttribute("data-graph-node-id") || "") === want) {
        found = el;
      }
    });
    return found;
  }

  /**
   * 선택 노드 카드의 상단 중앙 위에 모달이 오도록 고정 배치한다 (뷰포트 클램프).
   */
  function positionMacroStaffDialogOverNode(card, nodeId, dialog) {
    if (!dialog) {
      return;
    }
    var nodeEl = findGraphNodeElement(card, nodeId);
    if (!nodeEl) {
      clearMacroStaffDialogPosition(dialog);
      return;
    }
    var nr = nodeEl.getBoundingClientRect();
    var dw = dialog.offsetWidth;
    var dh = dialog.offsetHeight;
    var pad = MACRO_STAFF_DIALOG_VIEWPORT_PAD;
    var gap = MACRO_STAFF_DIALOG_ANCHOR_GAP;
    if (!dw || !dh) {
      dialog.style.margin = "0";
      dialog.style.position = "fixed";
      dw = dialog.offsetWidth;
      dh = dialog.offsetHeight;
    }
    var anchorX = nr.left + nr.width / 2;
    var topWant = nr.top - dh - gap;
    var leftWant = anchorX - dw / 2;
    leftWant = Math.min(
      Math.max(pad, leftWant),
      window.innerWidth - dw - pad,
    );
    topWant = Math.min(
      Math.max(pad, topWant),
      window.innerHeight - dh - pad,
    );
    dialog.style.margin = "0";
    dialog.style.position = "fixed";
    dialog.style.left = leftWant + "px";
    dialog.style.top = topWant + "px";
    dialog.style.right = "auto";
    dialog.style.bottom = "auto";
    dialog.style.transform = "none";
  }

  function scheduleMacroStaffDialogPosition(card, nodeId, dialog) {
    if (!dialog) {
      return;
    }
    function run() {
      positionMacroStaffDialogOverNode(card, nodeId, dialog);
    }
    run();
    window.requestAnimationFrame(run);
  }

  function attachMacroStaffDialogLivePosition(card, nodeId, dialog) {
    if (!dialog) {
      return;
    }
    var reposition = function () {
      if (dialog.open) {
        positionMacroStaffDialogOverNode(card, nodeId, dialog);
      }
    };
    window.addEventListener("resize", reposition);
    var ro = null;
    if (typeof ResizeObserver !== "undefined") {
      ro = new ResizeObserver(function () {
        reposition();
      });
      try {
        ro.observe(dialog);
      } catch (eRo) {}
    }
    dialog.addEventListener(
      "close",
      function onClose() {
        window.removeEventListener("resize", reposition);
        if (ro) {
          try {
            ro.disconnect();
          } catch (eDisc) {}
        }
        clearMacroStaffDialogPosition(dialog);
        dialog.removeEventListener("close", onClose);
      },
      { once: true },
    );
  }

  function wireStaffGraphModals(graphSec, card) {
    var detailDlg = graphSec.querySelector("[data-macro-staff-dialog-detail]");
    var editDlg = graphSec.querySelector("[data-macro-staff-dialog-edit]");
    var detailBody = graphSec.querySelector("[data-macro-staff-dialog-detail-body]");

    graphSec.querySelectorAll(".macro-staff-dialog-close").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var d = btn.closest("dialog");
        if (d && typeof d.close === "function") {
          d.close();
        }
      });
    });
    if (detailDlg) {
      detailDlg.addEventListener("click", function (e) {
        if (e.target === detailDlg) {
          detailDlg.close();
        }
      });
    }
    if (editDlg) {
      editDlg.addEventListener("click", function (e) {
        if (e.target === editDlg) {
          editDlg.close();
        }
      });
    }

    card._macroStaffOpenDetailModal = async function (nodeId) {
      var panel = card.querySelector("[data-macro-graph-panel]");
      var graph = panel && panel._displayedGraph;
      if (!detailDlg || !detailBody || !graph || !nodeId) {
        return;
      }
      try {
        var mod = await import("./solver_timeline/graph_detail.js?v=20260504-modal");
        await mod.renderSelectedNodeDetailInto(
          detailBody,
          panel.dataset.assetBase || "",
          graph,
          nodeId,
        );
        if (typeof detailDlg.showModal === "function") {
          detailDlg.showModal();
          scheduleMacroStaffDialogPosition(card, nodeId, detailDlg);
          attachMacroStaffDialogLivePosition(card, nodeId, detailDlg);
        }
      } catch (e) {
        console.error(e);
        setStatus(String(e.message || e), true);
      }
    };

    card._macroStaffOpenEditModal = function (nodeId) {
      var panel = card.querySelector("[data-macro-graph-panel]");
      if (panel && typeof panel._selectDisplayedGraphNode === "function") {
        panel._selectDisplayedGraphNode(nodeId);
      }
      card._macroStaffSelectedGraphNodeId = nodeId;
      updateMacroGraphToolbar(card, graphSec, nodeId);
      if (editDlg && typeof editDlg.showModal === "function") {
        editDlg.showModal();
        scheduleMacroStaffDialogPosition(card, nodeId, editDlg);
        attachMacroStaffDialogLivePosition(card, nodeId, editDlg);
      }
    };
  }

  /**
   * JSON 편집 중에는 커서 보존을 위해 포커스가 textarea일 때 서버 정규화 문자열로 덮어쓰지 않는다.
   * 타이핑마다 이전 요청은 Abort 로 취소한다.
   */
  function attachLiveJsonRecompute(ta, card, recipeId) {
    if (!ta) {
      return;
    }
    card._macroGraphJsonDebTimer = null;
    card._macroGraphJsonAbort = null;
    function bumpJsonAbort() {
      if (card._macroGraphJsonAbort) {
        try {
          card._macroGraphJsonAbort.abort();
        } catch (eAb) {}
      }
      card._macroGraphJsonAbort = new AbortController();
      return card._macroGraphJsonAbort.signal;
    }
    ta.addEventListener("input", function () {
      clearTimeout(card._macroGraphJsonDebTimer);
      card._macroGraphJsonDebTimer = setTimeout(async function () {
        card._macroGraphJsonDebTimer = null;
        var sig = bumpJsonAbort();
        try {
          await runMacroGraphDryRecompute(card, recipeId, {
            skipStatus: true,
            preserveTextareaIfFocused: true,
            signal: sig,
          });
        } catch (e2) {
          var aborted =
            e2 &&
            (e2.name === "AbortError" ||
              (typeof DOMException !== "undefined" &&
                e2 instanceof DOMException &&
                e2.name === "AbortError"));
          if (aborted) {
            return;
          }
          var msg = String(e2.message || e2);
          if (msg.indexOf("Invalid JSON") !== -1) {
            setStatus(msg, true);
          }
        }
      }, 450);
    });
    ta.addEventListener("blur", async function () {
      clearTimeout(card._macroGraphJsonDebTimer);
      card._macroGraphJsonDebTimer = null;
      if (card._macroGraphJsonAbort) {
        try {
          card._macroGraphJsonAbort.abort();
        } catch (eAb2) {}
        card._macroGraphJsonAbort = null;
      }
      try {
        card._graphDocument = JSON.parse(ta.value || "{}");
      } catch (eInv) {
        return;
      }
      try {
        await runMacroGraphDryRecompute(card, recipeId, { skipStatus: true });
      } catch (e3) {
        setStatus(String(e3.message || e3), true);
      }
    });
  }

  function wireMacroWorkbenchChrome(graphSec, recipeId) {
    var search = graphSec.querySelector("[data-macro-palette-search]");
    if (search) {
      search.addEventListener("input", function () {
        var q = String(search.value || "").trim().toLowerCase();
        graphSec.querySelectorAll(".macro-palette-card").forEach(function (cEl) {
          var op = String(cEl.getAttribute("data-palette-op") || "").toLowerCase();
          var text = (cEl.textContent || "").toLowerCase();
          var match = !q || text.indexOf(q) !== -1 || op.indexOf(q) !== -1;
          cEl.classList.toggle("hidden", !match);
        });
        graphSec.querySelectorAll(".macro-palette-group").forEach(function (det) {
          var any = false;
          det.querySelectorAll(".macro-palette-card").forEach(function (cEl) {
            if (!cEl.classList.contains("hidden")) {
              any = true;
            }
          });
          det.style.display = any ? "" : "none";
        });
      });
    }
    function clickViewportControl(sel) {
      var host = graphSec.querySelector("[data-macro-visual-graph-host]");
      if (!host) {
        return;
      }
      var btn = host.querySelector(sel);
      if (btn && typeof btn.click === "function") {
        btn.click();
      }
    }
    var fit = graphSec.querySelector("[data-macro-canvas-fit]");
    if (fit) {
      fit.addEventListener("click", function () {
        clickViewportControl("[data-graph-reset]");
      });
    }
    var zi = graphSec.querySelector("[data-macro-canvas-zoom-in]");
    var zo = graphSec.querySelector("[data-macro-canvas-zoom-out]");
    if (zi) {
      zi.addEventListener("click", function () {
        clickViewportControl("[data-graph-zoom-in]");
      });
    }
    if (zo) {
      zo.addEventListener("click", function () {
        clickViewportControl("[data-graph-zoom-out]");
      });
    }
    var notes = graphSec.querySelector("[data-macro-inspector-notes]");
    if (notes && recipeId != null) {
      var k = "macroWorkbenchNotes:" + String(recipeId);
      try {
        notes.value = window.localStorage.getItem(k) || "";
      } catch (eLs) {
        /* ignore */
      }
      notes.addEventListener("input", function () {
        try {
          window.localStorage.setItem(k, notes.value);
        } catch (eLs2) {
          /* ignore */
        }
      });
    }
  }

  function attachRecipeGraphSection(card, recipe) {
    var id = recipe.id;
    var graphSec = document.createElement("section");
    graphSec.className = "";
    graphSec.innerHTML =
      '<h3 class="text-xs font-semibold uppercase tracking-wide text-amber-200/80">' +
      "Recipe Graph Workbench</h3>" +
      '<details class="mb-2 mt-1 rounded border border-slate-800 bg-slate-950/50 text-xs">' +
      '<summary class="cursor-pointer select-none px-2 py-1.5 text-[11px] font-semibold text-slate-500 hover:bg-slate-900/60">Editor &amp; wiring (click)</summary>' +
      '<div class="space-y-1.5 border-t border-slate-800 px-2 py-2 text-slate-500">' +
      "<p>The canvas is the main editor: drag from the palette, connect ports, use <span class=\"font-semibold text-slate-400\">Recompute</span> / <span class=\"font-semibold text-slate-400\">save</span> for <code class=\"font-mono text-slate-400\">graph_document</code>.</p>" +
      '<p class="text-cyan-200/80">Wire: <span class="font-semibold text-amber-200/90">output</span> (amber) → <span class="font-semibold text-cyan-200">input</span> (cyan). Esc cancels. Click a wire to remove (confirm).</p>' +
      "</div></details>" +
      "<style type=\"text/css\">" +
      ".recipe-graph-grid-on [data-graph-viewport]{background-color:rgb(15 23 42);background-image:linear-gradient(rgba(148,163,184,0.14) 1px,transparent 1px),linear-gradient(90deg,rgba(148,163,184,0.14) 1px,transparent 1px);background-size:24px 24px;background-position:-1px -1px;}" +
      ".macro-graph-palette .macro-palette-card img{-webkit-user-drag:none;user-select:none;}" +
      ".macro-palette-group>summary{list-style:none;}" +
      ".macro-palette-group>summary::-webkit-details-marker{display:none;}" +
      ".macro-palette-group>summary::before{content:'▸';display:inline-block;margin-right:0.2rem;opacity:0.6;}" +
      ".macro-palette-group[open]>summary::before{content:'▾';}" +
      "</style>" +
      '<div class="flex flex-col gap-3">' +
      '<div class="macro-graph-visual-layout flex min-h-[min(68vh,860px)] flex-col gap-3 xl:flex-row">' +
      '<aside class="macro-graph-palette-aside w-full max-w-full shrink-0 self-start rounded border border-slate-800 bg-slate-900/50 p-2 xl:max-w-[18rem]" data-macro-graph-palette-wrap>' +
      '<div class="flex flex-col gap-1.5 border-b border-slate-800/80 pb-2">' +
      '<div class="flex items-center justify-between gap-2">' +
      '<span class="text-[9px] font-bold uppercase tracking-wide text-slate-500">Palette</span>' +
      '<label class="flex shrink-0 cursor-pointer items-center gap-0.5 text-[9px] text-slate-500" title="Canvas background grid">' +
      '<input type="checkbox" class="macro-graph-grid-toggle h-3 w-3 rounded border-slate-600 bg-slate-900" /> grid</label>' +
      "</div>" +
      '<input type="search" data-macro-palette-search placeholder="Filter palette…" class="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 text-[10px] text-slate-200 placeholder:text-slate-600" />' +
      "</div>" +
      '<div class="macro-graph-palette macro-palette-scroll mt-2 flex max-h-[min(48vh,420px)] flex-col gap-1 overflow-y-auto overflow-x-hidden [scrollbar-gutter:stable]" data-macro-graph-palette></div>' +
      "</aside>" +
      '<div class="flex min-h-[min(62vh,780px)] min-w-0 flex-1 flex-col gap-2">' +
      '<div class="flex flex-wrap items-center gap-1.5 rounded-lg border border-slate-800/80 bg-slate-900/40 px-2 py-1.5" data-macro-canvas-toolbar>' +
      '<span class="text-[9px] font-bold uppercase tracking-wide text-slate-500">Canvas</span>' +
      '<button type="button" data-macro-canvas-fit class="rounded border border-slate-600 bg-slate-900 px-2 py-1 text-[10px] font-semibold text-slate-200 hover:border-cyan-600/50">Fit</button>' +
      '<button type="button" data-macro-canvas-zoom-in class="rounded border border-slate-600 bg-slate-900 px-2 py-0.5 font-mono text-sm font-semibold leading-none text-slate-200 hover:border-cyan-600/50" aria-label="Zoom in">+</button>' +
      '<button type="button" data-macro-canvas-zoom-out class="rounded border border-slate-600 bg-slate-900 px-2 py-0.5 font-mono text-sm font-semibold leading-none text-slate-200 hover:border-cyan-600/50" aria-label="Zoom out">−</button>' +
      '<span class="ml-auto inline-flex items-center rounded border border-dashed border-slate-700 px-2 py-0.5 text-[9px] text-slate-600" title="Reserved">Minimap</span>' +
      "</div>" +
      '<div class="min-h-0 flex-1 rounded-lg border border-cyan-900/30 bg-slate-950/50" data-macro-visual-graph-host></div>' +
      "</div></div>" +
      '<div class="rounded-lg border border-slate-800 bg-slate-950/60 p-3" data-macro-workbench-inspector>' +
      '<p class="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Inspector</p>' +
      '<div class="mt-2 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">' +
      "<div><p class=\"text-[9px] font-bold uppercase text-slate-600\">Node</p>" +
      '<div class="mt-1 min-h-11 rounded border border-slate-800/80 bg-slate-950/50 p-2" data-macro-inspector-node>' +
      '<p class="text-[11px] text-slate-500">캔버스에서 노드를 선택하세요.</p></div></div>' +
      "<div><p class=\"text-[9px] font-bold uppercase text-slate-600\">Properties</p>" +
      '<div class="mt-1 min-h-11 rounded border border-slate-800/80 bg-slate-950/50 p-2" data-macro-inspector-properties>' +
      '<p class="text-[11px] text-slate-500">노드를 선택하면 속성이 표시됩니다.</p></div></div>' +
      "<div><p class=\"text-[9px] font-bold uppercase text-slate-600\">Validation</p>" +
      '<div class="mt-1 max-h-28 min-h-11 overflow-y-auto rounded border border-slate-800/80 bg-slate-950/50 p-2 text-[11px] text-amber-100/90" data-macro-inspector-validation>' +
      '<p class="text-[11px] text-emerald-200/90">No issues in the last recompute.</p></div></div>' +
      "<div><p class=\"text-[9px] font-bold uppercase text-slate-600\">Stats</p>" +
      '<p class="mt-1 font-mono text-[11px] text-slate-300" data-macro-inspector-stats>—</p></div>' +
      "<div><p class=\"text-[9px] font-bold uppercase text-slate-600\">Notes</p>" +
      '<textarea data-macro-inspector-notes rows="2" class="mt-1 w-full rounded border border-slate-800 bg-slate-950 px-2 py-1 text-[11px] text-slate-200 placeholder:text-slate-600" placeholder="Staff notes (browser only)"></textarea></div>' +
      "</div></div></div>" +
      '<div class="macro-graph-crud-toolbar mt-3 flex flex-col gap-3 rounded-lg border border-slate-700/80 bg-slate-950/50 p-3" data-macro-graph-crud-toolbar>' +
      '<div class="flex flex-wrap items-end gap-3">' +
      '<div class="min-w-32 flex-1">' +
      '<p class="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Visual graph CRUD</p>' +
      '<p class="mt-1 text-xs text-slate-400"><span class="text-slate-500">Selected:</span> <span class="macro-graph-selected-id font-mono text-cyan-200/90">none</span></p>' +
      "</div>" +
      '<div class="flex flex-wrap gap-2">' +
      '<button type="button" class="macro-graph-add-shape rounded-lg border border-cyan-700/50 bg-cyan-950/40 px-3 py-2 text-xs font-semibold text-cyan-100">Add shape</button>' +
      '<select class="macro-graph-add-op-select rounded border border-slate-600 bg-slate-900 px-2 py-2 text-xs"></select>' +
      '<button type="button" class="macro-graph-add-op rounded-lg border border-cyan-700/50 bg-cyan-950/40 px-3 py-2 text-xs font-semibold text-cyan-100">Add operation</button>' +
      '<button type="button" class="macro-graph-del-node rounded-lg border border-rose-700/50 bg-rose-950/40 px-3 py-2 text-xs font-semibold text-rose-100">Delete selected</button>' +
      "</div>" +
      "</div>" +
      '<p class="mt-2 text-[11px] leading-snug text-slate-500">' +
      '카드 <span class="font-semibold text-slate-400">우클릭</span> → 노드 정보 / 노드 편집. 카드 <span class="font-semibold text-slate-400">더블클릭</span> → 노드 편집 창.</p>' +
      "</div>" +
      '<details class="macro-edge-add-details mt-3 rounded-lg border border-slate-700/80 bg-slate-950/50 p-3">' +
      '<summary class="cursor-pointer text-xs font-semibold text-slate-300">Add / remove edge</summary>' +
      '<div class="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-5">' +
      '<label class="block text-xs text-slate-500">From node id<br /><input type="text" class="macro-edge-from mt-1 w-full rounded border border-slate-600 bg-slate-900 px-2 py-1 font-mono text-xs" list="macro-edge-datalist-' +
      esc(String(id)) +
      '" autocomplete="off" /></label>' +
      '<label class="block text-xs text-slate-500">To node id<br /><input type="text" class="macro-edge-to mt-1 w-full rounded border border-slate-600 bg-slate-900 px-2 py-1 font-mono text-xs" list="macro-edge-datalist-' +
      esc(String(id)) +
      '" autocomplete="off" /></label>' +
      '<label class="block text-xs text-slate-500">Kind<br /><select class="macro-edge-kind mt-1 w-full rounded border border-slate-600 bg-slate-900 px-2 py-1 text-xs">' +
      '<option value="input">input</option><option value="output">output</option></select></label>' +
      '<label class="block text-xs text-slate-500">Slot (optional)<br /><input type="text" class="macro-edge-slot mt-1 w-full rounded border border-slate-600 bg-slate-900 px-2 py-1 font-mono text-xs" placeholder="e.g. 0 or A" /></label>' +
      '<div class="flex flex-col gap-2 items-stretch justify-end">' +
      '<button type="button" class="macro-edge-append w-full rounded-lg border border-emerald-700/50 bg-emerald-950/30 px-2 py-2 text-xs font-semibold text-emerald-100 hover:bg-emerald-900/30">Append edge</button>' +
      '<button type="button" class="macro-edge-remove w-full rounded-lg border border-rose-700/50 bg-rose-950/30 px-2 py-2 text-xs font-semibold text-rose-100 hover:bg-rose-900/30">Remove matching edge</button>' +
      "</div>" +
      "</div>" +
      '<div class="mt-2 flex flex-wrap gap-2">' +
      '<button type="button" class="macro-edge-fill-from rounded border border-slate-600 bg-slate-900 px-2 py-1 text-[11px] font-semibold text-slate-200 hover:border-cyan-600/50">From = selected</button>' +
      '<button type="button" class="macro-edge-fill-to rounded border border-slate-600 bg-slate-900 px-2 py-1 text-[11px] font-semibold text-slate-200 hover:border-cyan-600/50">To = selected</button>' +
      "</div>" +
      '<datalist id="macro-edge-datalist-' +
      esc(String(id)) +
      '"></datalist>' +
      "</details>" +
      '<div class="mt-2 flex flex-wrap gap-2">' +
      '<button type="button" class="macro-graph-recompute rounded-lg border border-cyan-700/50 bg-cyan-950/40 px-3 py-2 text-xs font-semibold text-cyan-100 hover:bg-cyan-900/40">Recompute (dry-run)</button>' +
      '<button type="button" class="macro-graph-recompute-save rounded-lg border border-amber-600/50 bg-amber-950/30 px-3 py-2 text-xs font-semibold text-amber-100 hover:bg-amber-900/30">Recompute &amp; save graph</button>' +
      "</div>" +
      '<p class="mt-2 hidden text-xs text-amber-200/90" data-macro-graph-warnings role="status"></p>' +
      '<div class="mt-3 hidden rounded-lg border border-slate-700 bg-slate-950/80 p-3 text-xs" data-macro-validation-issues></div>' +
      '<details class="macro-graph-advanced-json mt-4 rounded-lg border border-slate-800 bg-slate-950/60 p-3">' +
      '<summary class="cursor-pointer text-xs font-semibold text-slate-400">Advanced: raw graph_document JSON</summary>' +
      '<textarea class="macro-graph-json mt-2 block w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-xs leading-relaxed text-slate-100" rows="10" spellcheck="false"></textarea>' +
      "</details>" +
      '<dialog class="open:backdrop:bg-black/60 macro-staff-dlg-detail max-h-[90vh] w-[min(100%,40rem)] max-w-[100vw] rounded-2xl border border-cyan-900/50 bg-slate-950 p-0 text-slate-100 shadow-2xl" data-macro-staff-dialog-detail>' +
      '<div class="flex max-h-[90vh] flex-col">' +
      '<div class="flex shrink-0 items-center justify-between gap-2 border-b border-slate-800 px-4 py-3">' +
      '<h2 class="text-sm font-semibold text-cyan-200/90">노드 정보</h2>' +
      '<button type="button" class="macro-staff-dialog-close rounded-lg border border-slate-600 px-2.5 py-1 text-sm text-slate-300 hover:bg-slate-800" aria-label="닫기">×</button>' +
      "</div>" +
      '<div class="min-h-0 flex-1 overflow-y-auto px-4 py-3" data-macro-staff-dialog-detail-body></div>' +
      "</div></dialog>" +
      '<dialog class="open:backdrop:bg-black/60 macro-staff-dlg-edit max-h-[90vh] w-[min(100%,28rem)] max-w-[100vw] rounded-2xl border border-amber-900/50 bg-slate-950 p-0 text-slate-100 shadow-2xl" data-macro-staff-dialog-edit>' +
      '<div class="flex max-h-[90vh] flex-col p-4">' +
      '<div class="flex shrink-0 items-center justify-between gap-2 border-b border-slate-800 pb-3">' +
      '<h2 class="text-sm font-semibold text-amber-200/90">노드 편집</h2>' +
      '<button type="button" class="macro-staff-dialog-close rounded-lg border border-slate-600 px-2.5 py-1 text-sm text-slate-300 hover:bg-slate-800" aria-label="닫기">×</button>' +
      "</div>" +
      '<p class="mt-2 text-[11px] text-slate-500">shape_code, role, operation 변경 후 적용하면 그래프가 다시 계산됩니다.</p>' +
      '<div class="macro-graph-edit-shape-block mt-3 hidden gap-2 sm:grid-cols-2">' +
      '<label class="text-xs text-slate-500">shape_code<br /><input type="text" class="macro-graph-edit-shape-code mt-1 w-full rounded border border-slate-600 bg-slate-900 px-2 py-1 font-mono text-xs" autocomplete="off" /></label>' +
      '<label class="text-xs text-slate-500">role<br /><select class="macro-graph-edit-shape-role mt-1 w-full rounded border border-slate-600 bg-slate-900 px-2 py-1 text-xs">' +
      '<option value="source">source</option><option value="intermediate">intermediate</option><option value="target">target</option></select></label>' +
      "</div>" +
      '<div class="macro-graph-edit-op-block mt-2 hidden gap-2 sm:grid-cols-2">' +
      '<label class="text-xs text-slate-500">operation<br /><select class="macro-graph-edit-op-type mt-1 w-full rounded border border-slate-600 bg-slate-900 px-2 py-1 text-xs"></select></label>' +
      '<label class="macro-graph-edit-paint-wrap hidden text-xs text-slate-500">paint_color (painter)<br /><input type="text" class="macro-graph-edit-paint-color mt-1 w-full max-w-24 rounded border border-slate-600 bg-slate-900 px-2 py-1 font-mono text-xs" maxlength="4" autocomplete="off" /></label>' +
      "</div>" +
      '<button type="button" class="macro-graph-apply-edit mt-4 w-full rounded-lg border border-emerald-700/50 bg-emerald-950/30 px-3 py-2 text-xs font-semibold text-emerald-100">Apply edits &amp; preview</button>' +
      "</div></dialog>";
    card.appendChild(graphSec);
    setGraphDocument(card, card._graphDocument);
    card._macroRecipeGraphSection = graphSec;
    card._macroStaffSelectedGraphNodeId = null;
    refreshMacroGraphToolbarOperationSelects(graphSec);
    fillMacroGraphPalette(graphSec);
    wireMacroGraphPaletteGrid(graphSec);
    wireMacroWorkbenchChrome(graphSec, id);
    wireMacroGraphCrudEvents(graphSec, card, id);
    wireStaffGraphModals(graphSec, card);
    attachLiveJsonRecompute(graphSec.querySelector(".macro-graph-json"), card, id);
    updateMacroGraphToolbar(card, graphSec, null);
    void remountVisualGraph(card, recipe.visual_graph, { recipeId: id, card: card });

    var edgeDetails = graphSec.querySelector(".macro-edge-add-details");
    var datalist = graphSec.querySelector("datalist");
    var edgeAppend = graphSec.querySelector(".macro-edge-append");
    var edgeRemove = graphSec.querySelector(".macro-edge-remove");
    var edgeFillFrom = graphSec.querySelector(".macro-edge-fill-from");
    var edgeFillTo = graphSec.querySelector(".macro-edge-fill-to");
    if (edgeDetails && datalist) {
      edgeDetails.addEventListener("toggle", function () {
        if (!edgeDetails.open) {
          return;
        }
        try {
          var gdoc = parseGraphTextarea(card);
          if (!gdoc || !Array.isArray(gdoc.nodes)) {
            datalist.innerHTML = "";
            return;
          }
          datalist.innerHTML = gdoc.nodes
            .map(function (n) {
              if (!n || n.id == null) {
                return "";
              }
              return '<option value="' + esc(String(n.id)) + '"></option>';
            })
            .join("");
        } catch (e2) {
          datalist.innerHTML = "";
        }
      });
    }
    function readMacroEdgeFormEdge() {
      var fromId = graphSec.querySelector(".macro-edge-from").value.trim();
      var toId = graphSec.querySelector(".macro-edge-to").value.trim();
      var kind = graphSec.querySelector(".macro-edge-kind").value;
      var slotRaw = graphSec.querySelector(".macro-edge-slot").value.trim();
      var edge = { from: fromId, to: toId, kind: kind };
      if (slotRaw) {
        edge.slot = slotRaw;
      }
      return edge;
    }
    if (edgeAppend) {
      edgeAppend.addEventListener("click", async function () {
        var edge = readMacroEdgeFormEdge();
        if (!edge.from || !edge.to) {
          setStatus("From and To node ids are required.", true);
          return;
        }
        var r = tryAppendEdgeToGraphDoc(card, edge);
        if (!r.ok) {
          setStatus(r.message, true);
          return;
        }
        try {
          var data = await runMacroGraphDryRecompute(card, id, { skipStatus: true });
          setGraphWarnings(card, data.warnings);
          setGraphValidationList(card, data.validation);
          await remountVisualGraph(card, data.visual_graph, { recipeId: id, card: card });
          setStatus(
            (data.validation && data.validation.ok === false) ||
              (data.warnings && data.warnings.length)
              ? r.message + " Recompute — see validation / warnings."
              : r.message + " Preview updated.",
          );
        } catch (e2) {
          setStatus(String(e2.message || e2), true);
        }
      });
    }
    if (edgeRemove) {
      edgeRemove.addEventListener("click", async function () {
        var edge = readMacroEdgeFormEdge();
        if (!edge.from || !edge.to) {
          setStatus("From and To node ids are required.", true);
          return;
        }
        if (!window.confirm("Remove this edge from graph_document (matching from/to/kind/slot)?")) {
          return;
        }
        var r = tryRemoveEdgeFromGraphDoc(card, edge);
        if (!r.ok) {
          setStatus(r.message, true);
          return;
        }
        try {
          var data = await runMacroGraphDryRecompute(card, id, { skipStatus: true });
          setGraphWarnings(card, data.warnings);
          setGraphValidationList(card, data.validation);
          await remountVisualGraph(card, data.visual_graph, { recipeId: id, card: card });
          setStatus(
            (data.validation && data.validation.ok === false) ||
              (data.warnings && data.warnings.length)
              ? r.message + " Recompute — see validation / warnings."
              : r.message + " Preview updated.",
          );
        } catch (e2) {
          setStatus(String(e2.message || e2), true);
        }
      });
    }
    if (edgeFillFrom) {
      edgeFillFrom.addEventListener("click", function () {
        var nid = String(card._macroStaffSelectedGraphNodeId || "").trim();
        if (!nid) {
          setStatus("Select a node in the preview first.", true);
          return;
        }
        graphSec.querySelector(".macro-edge-from").value = nid;
        setStatus("From set to " + nid + ".");
      });
    }
    if (edgeFillTo) {
      edgeFillTo.addEventListener("click", function () {
        var nid = String(card._macroStaffSelectedGraphNodeId || "").trim();
        if (!nid) {
          setStatus("Select a node in the preview first.", true);
          return;
        }
        graphSec.querySelector(".macro-edge-to").value = nid;
        setStatus("To set to " + nid + ".");
      });
    }

    graphSec.querySelector(".macro-graph-recompute").addEventListener("click", async function () {
      try {
        await runMacroGraphDryRecompute(card, id);
      } catch (e) {
        setStatus(String(e.message || e), true);
      }
    });

    graphSec.querySelector(".macro-graph-recompute-save").addEventListener("click", async function () {
      var doc;
      try {
        doc = parseGraphTextarea(card);
      } catch (e) {
        setStatus("Invalid JSON in graph document: " + (e.message || e), true);
        return;
      }
      try {
        var resp = await api("POST", graphRecomputeUrl(id), {
          graph_document: doc,
          commit: true,
        });
        if (taSave && resp && resp.graph_document) {
          setGraphDocument(card, resp.graph_document);
        }
        setGraphWarnings(card, resp.warnings || []);
        setGraphValidationList(card, resp.validation);
        await remountVisualGraph(card, resp.visual_graph, { recipeId: id, card: card });
        setStatus(
          "Graph saved to DB (" + recipe.code + ")." + stepsSyncedFragment(resp, { showStepsSynced: true }),
        );
      } catch (e) {
        setStatus(String(e.message || e), true);
      }
    });
  }


  async function initMacroGraphMount(host, graph, wireCtx) {
    var assetBase = "";
    if (editorRoot && editorRoot.dataset) {
      assetBase = String(editorRoot.dataset.shapePreviewAssetBase || "").trim();
    }
    var g = graph && typeof graph === "object" ? graph : { nodes: [], edges: [] };
    if (!Array.isArray(g.nodes)) {
      g.nodes = [];
    }
    if (!Array.isArray(g.edges)) {
      g.edges = [];
    }
    var staffCtx = wireCtx && wireCtx.recipeId && wireCtx.card;
    if (!g.nodes.length && !staffCtx) {
      return;
    }
    try {
      const mod = await import("./macro_pattern_staff_graph.mjs?v=20260504-grid-pinned");
      const hooks =
        wireCtx && wireCtx.recipeId && wireCtx.card
          ? {
              recipeWireConnect: async function (edge) {
                var r = tryAppendEdgeToGraphDoc(wireCtx.card, edge);
                if (!r.ok) {
                  setStatus(r.message, true);
                  return;
                }
                try {
                  var data = await runMacroGraphDryRecompute(wireCtx.card, wireCtx.recipeId, {
                    skipStatus: true,
                  });
                  setGraphWarnings(wireCtx.card, data.warnings);
                  setGraphValidationList(wireCtx.card, data.validation);
                  await remountVisualGraph(wireCtx.card, data.visual_graph, {
                    recipeId: wireCtx.recipeId,
                    card: wireCtx.card,
                  });
                  setStatus(
                    (data.validation && data.validation.ok === false) ||
                      (data.warnings && data.warnings.length)
                      ? "Edge added (wire). Recompute done — see validation / warnings."
                      : "Edge added (wire). Preview updated.",
                  );
                } catch (e2) {
                  setStatus(String(e2.message || e2), true);
                }
              },
              recipeWireDelete: async function (edge) {
                if (
                  !window.confirm(
                    "Remove wire " +
                      edge.from +
                      " → " +
                      edge.to +
                      " (" +
                      edge.kind +
                      ") from graph_document?",
                  )
                ) {
                  return;
                }
                var r = tryRemoveEdgeFromGraphDoc(wireCtx.card, edge);
                if (!r.ok) {
                  setStatus(r.message, true);
                  return;
                }
                try {
                  var data = await runMacroGraphDryRecompute(wireCtx.card, wireCtx.recipeId, {
                    skipStatus: true,
                  });
                  setGraphWarnings(wireCtx.card, data.warnings);
                  setGraphValidationList(wireCtx.card, data.validation);
                  await remountVisualGraph(wireCtx.card, data.visual_graph, {
                    recipeId: wireCtx.recipeId,
                    card: wireCtx.card,
                  });
                  setStatus(
                    (data.validation && data.validation.ok === false) ||
                      (data.warnings && data.warnings.length)
                      ? r.message + " Recompute — see validation / warnings."
                      : r.message + " Preview updated.",
                  );
                } catch (e2) {
                  setStatus(String(e2.message || e2), true);
                }
              },
              onGraphNodeSelect: function (nodeId) {
                wireCtx.card._macroStaffSelectedGraphNodeId = nodeId;
                var gs = wireCtx.card._macroRecipeGraphSection;
                if (gs) {
                  updateMacroGraphToolbar(wireCtx.card, gs, nodeId);
                }
              },
              recipeNodeDragCommit: async function (payload) {
                var r = tryMoveGraphNodeInGraphDoc(
                  wireCtx.card,
                  payload.nodeId,
                  payload.x,
                  payload.y,
                );
                if (!r.ok) {
                  setStatus(r.message, true);
                  return;
                }
                try {
                  var data = await runMacroGraphDryRecompute(wireCtx.card, wireCtx.recipeId, {
                    skipStatus: true,
                  });
                  setStatus(
                    (data.validation && data.validation.ok === false) ||
                      (data.warnings && data.warnings.length)
                      ? r.message + " Recompute — see validation / warnings."
                      : r.message + " Preview updated.",
                  );
                } catch (e2) {
                  setStatus(String(e2.message || e2), true);
                }
              },
              recipeCanvasDrop: async function (payload) {
                var r;
                if (payload.kind === "shape") {
                  r = tryAppendShapeNodeToGraphDocAt(
                    wireCtx.card,
                    payload.graphX,
                    payload.graphY,
                  );
                } else if (payload.kind === "operation" && payload.operation) {
                  r = tryAppendOperationNodeToGraphDocAt(
                    wireCtx.card,
                    String(payload.operation),
                    payload.graphX,
                    payload.graphY,
                  );
                } else {
                  return;
                }
                if (!r.ok) {
                  setStatus(r.message, true);
                  return;
                }
                try {
                  var data = await runMacroGraphDryRecompute(wireCtx.card, wireCtx.recipeId, {
                    skipStatus: true,
                  });
                  setGraphWarnings(wireCtx.card, data.warnings);
                  setGraphValidationList(wireCtx.card, data.validation);
                  await remountVisualGraph(wireCtx.card, data.visual_graph, {
                    recipeId: wireCtx.recipeId,
                    card: wireCtx.card,
                  });
                  setStatus(
                    (data.validation && data.validation.ok === false) ||
                      (data.warnings && data.warnings.length)
                      ? r.message + " Recompute — see validation / warnings."
                      : r.message + " Dropped on canvas.",
                  );
                } catch (e2) {
                  setStatus(String(e2.message || e2), true);
                }
              },
              staffOpenNodeDetailModal: function (nid) {
                if (wireCtx.card._macroStaffOpenDetailModal) {
                  return wireCtx.card._macroStaffOpenDetailModal(nid);
                }
              },
              staffOpenNodeEditModal: function (nid) {
                if (wireCtx.card._macroStaffOpenEditModal) {
                  wireCtx.card._macroStaffOpenEditModal(nid);
                }
              },
            }
          : undefined;
      await mod.mountMacroRecipeGraph(host, g, assetBase, hooks);
    } catch (e) {
      console.error("macro staff graph:", e);
      host.innerHTML =
        '<p class="text-xs text-rose-300">Could not load graph preview. See browser console.</p>';
    }
  }

  function setStatus(msg, isError) {
    if (!statusEl) {
      return;
    }
    statusEl.textContent = msg || "";
    statusEl.classList.toggle("text-rose-300", Boolean(isError));
    statusEl.classList.toggle("text-amber-200/90", !isError && Boolean(msg));
  }

  async function api(method, url, body, fetchOpts) {
    fetchOpts = fetchOpts || {};
    const headers = {
      "Content-Type": "application/json",
    };
    const csrftoken = getCookie("csrftoken");
    if (csrftoken) {
      headers["X-CSRFToken"] = csrftoken;
    }
    const res = await fetch(url, {
      method,
      headers,
      credentials: "same-origin",
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: fetchOpts.signal,
    });
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch (e) {
      data = { ok: false, error: text || res.statusText };
    }
    if (!res.ok) {
      const err = (data && data.error) || res.statusText || "request failed";
      throw new Error(err);
    }
    return data;
  }

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  var recipe = readJsonScript("macro-graph-initial-recipe");
  if (!recipe || recipe.id == null) {
    setStatus("Missing recipe payload.", true);
    return;
  }
  editorRoot._graphDocument = recipe.graph_document
    ? JSON.parse(JSON.stringify(recipe.graph_document))
    : JSON.parse(JSON.stringify(EMPTY_GRAPH_DOCUMENT));
  attachRecipeGraphSection(editorRoot, recipe);
})();
