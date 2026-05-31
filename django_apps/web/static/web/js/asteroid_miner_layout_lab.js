/**
 * Client-side replay controls for the asteroid mining lab page (shell UI).
 *
 * Shapez2 asteroid map invariant (Lab + runtime replay):
 * - There is no x == 0 column. Horizontal order: ..., -2, -1, 1, 2, ...
 * - (-1, y) is horizontally adjacent to (1, y), not (0, y).
 * - World (1, 0) is the UI anchor: visual column index 0, row y = 0 at grid center (symmetric padding).
 *
 * Domain rotation contract (blueprint JSON; never mutate ``cell.rotation`` in JS):
 * - R = 0 means East; R increases by quarter-turns clockwise (0..3).
 * - Lab SVGs are East-facing; display rotation is CSS ``rotate`` on the sprite ``img`` from ``R`` only.
 *   Do not apply ad-hoc R+1 or rewrite domain rotation.
 */
(function () {
  "use strict";

  const GRID_W = 23;
  const GRID_H = 15;

  /** Canonical map rotation: 0 = East, 1 = South, 2 = West, 3 = North; quarter-turns clockwise. */
  const DIR = Object.freeze({
    EAST: 0,
    SOUTH: 1,
    WEST: 2,
    NORTH: 3,
  });

  const LINK_KEY_TO_DIR = Object.freeze({
    e: DIR.EAST,
    s: DIR.SOUTH,
    w: DIR.WEST,
    n: DIR.NORTH,
  });

  const DIR_TO_BRIDGE_SUFFIX = Object.freeze({
    0: "e",
    1: "s",
    2: "w",
    3: "n",
  });

  function normalizeQuarterTurns(q) {
    const n = Number(q);
    if (!Number.isFinite(n)) return 0;
    return ((Math.trunc(n) % 4) + 4) % 4;
  }

  /* Sprite canonical direction contract (East-facing assets; CSS rotate only):
   * quarter 0 = E = 0deg, 1 = S = 90deg clockwise on screen, 2 = W = 180deg, 3 = N = 270deg.
   * Row/col grid mapping must not alter this rotation (no scaleX/rotateY mirror tricks). */
  function rotationToDeg(q) {
    return normalizeQuarterTurns(q) * 90;
  }

  function snapToDevicePixel(value) {
    const dpr = window.devicePixelRatio || 1;
    return Math.round(Number(value) * dpr) / dpr;
  }

  /** Base cell look; replay grid uses grid cell size instead of h-5 w-5. ``relative`` anchors the sprite layer. */
  const LAB_CELL_BASE =
    "lab-cell relative shrink-0 overflow-visible border bg-slate-950 border-slate-900";

  /** Map blueprint ``T`` (:class:`ShapezGameIdentifier` ``value``) → ``sprite_static_relpath``; from ``json_script`` id ``lab-identifier-sprite-paths-data``. */
  let labIdentifierSpriteRelpaths = {};

  /** When ``#lab-root`` has ``data-lab-debug-rotation="1"``, grid shows R overlay on cells with sprites. */
  function labRotationDebugEnabled(rootEl) {
    return Boolean(rootEl && rootEl.dataset && rootEl.dataset.labDebugRotation === "1");
  }

  /** ``cell_kind`` → blueprint ``T`` when ``tile_type`` is missing (not used for ambiguous kinds like ``space_pipe``). */
  const LAB_SPRITE_CELL_KIND_TO_IDENTIFIER = Object.freeze({
    fluid_miner: "Layout_FluidMiner",
    fluid_miner_extension: "Layout_FluidMinerExtension",
    shape_miner: "Layout_ShapeMiner",
    shape_miner_extension: "Layout_ShapeMinerExtension",
    /** Legacy L4 replay observation aliases (defense-in-depth if wire not yet domain kinds). */
    miner: "Layout_ShapeMiner",
    extension: "Layout_ShapeMinerExtension",
  });

  /** Blueprint ``T`` alias when art matches another identifier (mirrors ``lab_sprite_path.py``). */
  const LAB_SPRITE_TILE_TYPE_ALIASES = Object.freeze({
    Layout_ProMiner: "Layout_ShapeMiner",
    SpaceBelt_Left: "SpaceBelt_LeftTurn",
    SpacePipe_Left: "SpacePipe_LeftTurn",
    SpaceBelt_Right: "SpaceBelt_RightTurn",
    SpacePipe_Right: "SpacePipe_RightTurn",
  });

  /** Mineable asteroid field tiles (``cell_kind`` wins over export ``Layout_*MinerExtension`` ``T``). */
  const LAB_SPRITE_CELL_KIND_STATIC_RELPATH = Object.freeze({
    asteroid_fluid_field: "AsteroidField_Fluid.svg",
    asteroid_shape_field: "AsteroidField_Shape.svg",
  });

  /** Sprite stack container; styles in ``assets/css/input.css`` (``.lab-cell-sprite-layer``). */
  const LAB_CELL_SPRITE_LAYER_CLASS = "lab-cell-sprite-layer";

  /** Set in ``init`` from ``#lab-root`` ``data-lab-sprite-base`` (Django ``{% static %}``). */
  let labSpriteBaseUrl = "";

  const labRootForTotals = document.getElementById("lab-root");
  const rawTotal = labRootForTotals
    ? Number(labRootForTotals.dataset.labTotalFrames)
    : NaN;
  const TOTAL_FRAMES = Number.isFinite(rawTotal) ? rawTotal : 0;

  /** Extra empty cells beyond union bbox on each side (visual col / row), symmetric around (1,0). */
  const REPLAY_GRID_EDGE_PADDING = 5;

  const LAB_VIEWPORT_MIN_SCALE = 0.35;
  const LAB_VIEWPORT_MAX_SCALE = 7;
  const LAB_VIEWPORT_DRAG_THRESHOLD_PX = 6;

  let labViewportInteractionsBound = false;

  function clampNumber(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  /** Human-readable timeline position (1-based slot / total frame count). */
  function formatLabFrameCounter(zeroBasedSlot, totalCount) {
    const total = Number.isFinite(totalCount) && totalCount > 0 ? Math.floor(totalCount) : 0;
    if (total <= 0) {
      return "0 / 0";
    }
    const slot = Number.isFinite(zeroBasedSlot) ? Math.floor(zeroBasedSlot) : 0;
    const clamped = clampNumber(slot, 0, total - 1);
    return String(clamped + 1) + " / " + String(total);
  }

  /** HUD: ``data-overlay-role``, ``data-cell-kind``, ``data-tile-type`` (cleared in ``resetGridBase``). */
  function applyLabCellHudAttributes(el, cell, overlayRoleForAttr) {
    if (!el) return;
    const r =
      overlayRoleForAttr != null && String(overlayRoleForAttr) !== ""
        ? String(overlayRoleForAttr)
        : "";
    if (r) {
      el.setAttribute("data-overlay-role", r);
    } else {
      el.removeAttribute("data-overlay-role");
    }
    if (cell && cell.cell_kind != null) {
      el.setAttribute("data-cell-kind", String(cell.cell_kind));
    } else {
      el.removeAttribute("data-cell-kind");
    }
    if (cell && cell.tile_type != null && String(cell.tile_type) !== "") {
      el.setAttribute("data-tile-type", String(cell.tile_type));
    } else {
      el.removeAttribute("data-tile-type");
    }
  }

  function canonicalLabTileType(tileType) {
    const t = tileType == null ? "" : String(tileType).trim();
    if (!t) return "";
    const alias = LAB_SPRITE_TILE_TYPE_ALIASES[t];
    return alias || t;
  }

  function labSpriteRelpathFromTileType(tileType) {
    const t = canonicalLabTileType(tileType);
    if (!t) return null;
    const rel = labIdentifierSpriteRelpaths[t];
    if (typeof rel === "string" && rel.length) return rel;
    if (t.startsWith("SpaceBelt_")) return "SpaceBelt/" + t + ".svg";
    if (t.startsWith("SpacePipe_")) return "SpacePipe/" + t + ".svg";
    if (t.startsWith("Layout_")) return "Miner/" + t + ".svg";
    return null;
  }

  function labSpriteRelpathFromCellKind(cellKind) {
    const ck = cellKind == null ? "" : String(cellKind);
    if (!ck) return null;
    const ident = LAB_SPRITE_CELL_KIND_TO_IDENTIFIER[ck];
    if (!ident) return null;
    return labSpriteRelpathFromTileType(ident);
  }

  /** Last-resort: infer Forward-only sprite from transport kind when tile_type is absent.
   * Turn/splitter/merger variants require replay-provided tile_type — no topology inference here. */
  function inferTransportSpriteIdentifier(cell) {
    const ck = cell.cell_kind != null ? String(cell.cell_kind) : "";
    if (
      ck === "miner" ||
      ck === "extension" ||
      ck === "shape_miner" ||
      ck === "shape_miner_extension" ||
      ck === "fluid_miner" ||
      ck === "fluid_miner_extension"
    ) {
      return null;
    }
    const tk = cell.transport_kind || cell.transport;
    if (!tk) return null;
    if (tk === "shape_belt" || cell.cell_kind === "space_belt") return "SpaceBelt_Forward";
    if (tk === "fluid_pipe" || cell.cell_kind === "space_pipe") return "SpacePipe_Forward";
    return null;
  }

  function labSpriteRelpathForCell(cell, frame) {
    if (!cell || typeof cell !== "object") return null;
    if (isNonSpriteOverlayCell(cell, frame)) return null;
    const ck = cell.cell_kind != null ? String(cell.cell_kind) : "";
    const fieldRel = ck ? LAB_SPRITE_CELL_KIND_STATIC_RELPATH[ck] : null;
    if (fieldRel) return fieldRel;
    // sprite_identifier is the alias emitted alongside tile_type; prefer it so either field works.
    const tileKey = cell.sprite_identifier || cell.tile_type;
    let rel = labSpriteRelpathFromTileType(tileKey);
    if (!rel && cell.cell_kind != null) {
      rel = labSpriteRelpathFromCellKind(cell.cell_kind);
    }
    if (!rel) {
      const inferred = inferTransportSpriteIdentifier(cell);
      if (inferred) rel = labSpriteRelpathFromTileType(inferred);
    }
    return rel;
  }

  function attachLabSpriteImgNoDrag(img) {
    if (!img || img.__labSpriteNoDrag) return;
    img.__labSpriteNoDrag = true;
    img.draggable = false;
    img.setAttribute("draggable", "false");
    img.addEventListener("dragstart", function (ev) {
      ev.preventDefault();
    });
  }

  function ensureLabCellSpriteLayer(cellEl) {
    let layer = cellEl.querySelector("[data-lab-sprite-layer]");
    if (!layer) {
      layer = document.createElement("div");
      layer.setAttribute("data-lab-sprite-layer", "1");
      layer.setAttribute("aria-hidden", "true");
      layer.className = LAB_CELL_SPRITE_LAYER_CLASS;
      const img = document.createElement("img");
      img.className = "lab-cell-sprite";
      img.alt = "";
      img.setAttribute("aria-hidden", "true");
      attachLabSpriteImgNoDrag(img);
      layer.appendChild(img);
      cellEl.appendChild(layer);
    }
    return layer;
  }

  function clearPlannedExteriorConnectorHighlight(el) {
    if (!el) return;
    const marker = el.querySelector("[data-lab-exterior-connector-marker]");
    if (marker) {
      marker.remove();
    }
  }

  function plannedConnectorCoordKey(x, y) {
    return String(x) + "," + String(y);
  }

  /** Paint cells from ``metrics.exterior_connector_plan`` (SoT), not overlay_cells alone. */
  function plannedConnectorCellsFromWire(wire) {
    if (!wire || typeof wire !== "object") {
      return [];
    }
    const list = wire.planned_connectors;
    if (!Array.isArray(list)) {
      return [];
    }
    const out = [];
    for (let i = 0; i < list.length; i++) {
      const item = list[i];
      if (!item || typeof item !== "object") {
        continue;
      }
      const vc = item.void_coord;
      let x = null;
      let y = null;
      if (vc && typeof vc === "object") {
        x = vc.x;
        y = vc.y;
      } else {
        x = item.x;
        y = item.y;
      }
      if (x == null || y == null) {
        continue;
      }
      out.push({
        x: x,
        y: y,
        overlay_role: "planned_exterior_connector",
        connector_role: item.role != null ? String(item.role) : "required",
        tile_type: item.layout_t != null ? String(item.layout_t) : "",
        rotation: item.rotation,
        connector_id: item.connector_id != null ? String(item.connector_id) : "",
      });
    }
    return out;
  }

  function plannedConnectorCoordKeySet(wire) {
    const keys = new Set();
    const cells = plannedConnectorCellsFromWire(wire);
    for (let i = 0; i < cells.length; i++) {
      const c = cells[i];
      keys.add(plannedConnectorCoordKey(c.x, c.y));
    }
    return keys;
  }

  function applyPlannedExteriorConnectorWhiteHighlight(el) {
    if (!el) return;
    clearPlannedExteriorConnectorHighlight(el);
    el.style.zIndex = "2";
    el.style.border = "";
    el.style.backgroundColor = "rgba(255, 255, 255, 0.12)";
    el.style.boxShadow = "inset 0 0 0 2px rgba(255, 255, 255, 0.92)";
    el.style.outline = "none";
  }

  function applyPlannedExteriorConnectorSpareHighlight(el) {
    if (!el) return;
    clearPlannedExteriorConnectorHighlight(el);
    el.style.zIndex = "2";
    el.style.border = "";
    el.style.backgroundColor = "rgba(34, 211, 238, 0.14)";
    el.style.boxShadow = "inset 0 0 0 2px rgba(34, 211, 238, 0.92)";
    el.style.outline = "none";
  }

  function normalizeConnectorRole(raw) {
    const role = String(raw || "required").trim().toLowerCase();
    return role === "spare" ? "spare" : "required";
  }

  function renderPlannedExteriorConnectorHighlights(
    frame,
    baseClasses,
    domCells,
    resolveCellIndex,
    trackMetrics,
  ) {
    const wire = resolveExteriorConnectorPlanWire(frame, trackMetrics);
    let cells = plannedConnectorCellsFromWire(wire);
    if (!cells.length) {
      const mapView = frame && frame.map_view;
      const ov =
        mapView && typeof mapView === "object" && Array.isArray(mapView.overlay_cells)
          ? mapView.overlay_cells
          : [];
      for (let i = 0; i < ov.length; i++) {
        const raw = ov[i];
        if (!raw || typeof raw !== "object") continue;
        if (String(raw.overlay_role || "") !== "planned_exterior_connector") continue;
        const mapped = overlayCellsFromMapView({ overlay_cells: [raw] });
        if (mapped[0]) cells.push(mapped[0]);
      }
    }
    for (let i = 0; i < cells.length; i++) {
      const cell = cells[i];
      if (!cell || typeof cell !== "object") continue;
      const idx = resolveCellIndex(cell);
      if (idx == null || idx < 0 || idx >= domCells.length) continue;
      const el = domCells[idx];
      const role = normalizeConnectorRole(cell.connector_role);
      if (role === "spare") {
        el.className = LAB_CELL_BASE + " lab-planned-exterior-connector-spare";
        applyLabCellHudAttributes(el, cell, "planned_exterior_connector");
        applyLabCellSprite(el, cell);
        applyPlannedExteriorConnectorSpareHighlight(el);
      } else {
        el.className = LAB_CELL_BASE + " lab-planned-exterior-connector";
        applyLabCellHudAttributes(el, cell, "planned_exterior_connector");
        applyLabCellSprite(el, cell);
        applyPlannedExteriorConnectorWhiteHighlight(el);
      }
    }
  }

  function clearLabCellSprite(el) {
    const layer = el.querySelector("[data-lab-sprite-layer]");
    if (layer) {
      layer.remove();
    }
    el.style.backgroundImage = "";
    el.style.backgroundSize = "";
    el.style.backgroundPosition = "";
    el.style.backgroundRepeat = "";
    el.style.transform = "";
    el.removeAttribute("data-lab-sprite");
    el.removeAttribute("data-r");
    el.removeAttribute("data-sprite-q");
    el.removeAttribute("data-sprite-file");
  }

  function applyLabCellSprite(el, cell, frame) {
    if (!cell || typeof cell !== "object") return;
    const ck = overlayCellKind(cell);
    if (isRouteOverlayCellKind(ck) || isNonSpriteOverlayCell(cell, frame)) return;
    clearLabCellSprite(el);
    if (!labSpriteBaseUrl) return;
    const rel = labSpriteRelpathForCell(cell, frame);
    if (!rel) return;
    const layer = ensureLabCellSpriteLayer(el);
    const img = layer.querySelector("img.lab-cell-sprite");
    if (!img) return;
    attachLabSpriteImgNoDrag(img);
    const base = String(labSpriteBaseUrl).replace(/\/?$/, "/");
    img.src = base + rel;
    const logicalQ = normalizeQuarterTurns(cell.rotation);
    const deg = rotationToDeg(logicalQ);
    if (deg !== 0) {
      img.style.transform = "rotate(" + String(deg) + "deg)";
    } else {
      img.style.transform = "";
    }
    layer.setAttribute("data-lab-sprite", rel);
    const rootDbg = document.getElementById("lab-root");
    if (labRotationDebugEnabled(rootDbg)) {
      el.setAttribute("data-r", String(logicalQ));
      el.setAttribute("data-sprite-file", rel);
    }
  }

  function readJsonScript(id) {
    const el = document.getElementById(id);
    if (!el || !el.textContent) {
      return null;
    }
    try {
      return JSON.parse(el.textContent);
    } catch {
      return null;
    }
  }

  const RTTP_OPS_SLUG_CLASS_PASS_CAPABLE = "pass_capable";
  const RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON = "diagnostic_canon";

  function resolveRttpOpsSlugClass(run) {
    if (!run || typeof run !== "object") return null;
    const top = run.rttp_ops_slug_class;
    if (top != null && top !== "" && top !== "—") return String(top);
    const tt =
      run.throughput_target && typeof run.throughput_target === "object"
        ? run.throughput_target
        : null;
    if (
      tt &&
      tt.rttp_ops_slug_class != null &&
      tt.rttp_ops_slug_class !== "" &&
      tt.rttp_ops_slug_class !== "—"
    ) {
      return String(tt.rttp_ops_slug_class);
    }
    if (run.diagnostic_expected_shortfall === true) {
      return RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON;
    }
    return null;
  }

  function isDiagnosticCanonRun(run) {
    return Boolean(run && run.diagnostic_expected_shortfall === true);
  }

  function passCapableBadgeLabel() {
    const msgid = "Pass-capable";
    return typeof shapezUiT === "function" ? shapezUiT(msgid) : msgid;
  }

  function shouldShowPassCapableBadge(run) {
    return (
      resolveRttpOpsSlugClass(run) === RTTP_OPS_SLUG_CLASS_PASS_CAPABLE &&
      !isDiagnosticCanonRun(run)
    );
  }

  function passCapableBadgeHtml() {
    return (
      '<span class="lab-ops-slug-badge lab-ops-slug-badge--pass-capable inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide">' +
      passCapableBadgeLabel() +
      "</span>"
    );
  }

  function passCapableReferenceStatusText(run) {
    if (!shouldShowPassCapableBadge(run)) return null;
    const msgid =
      "T3 reference slug (pass-capable registry; throughput shortfall is a regression signal).";
    return typeof shapezUiT === "function" ? shapezUiT(msgid) : msgid;
  }

  function updateOpsSlugBadge(run) {
    const el = document.getElementById("lab-detail-ops-slug-badge");
    if (!el) return;
    if (shouldShowPassCapableBadge(run)) {
      el.innerHTML = passCapableBadgeHtml();
      el.classList.remove("hidden");
    } else {
      el.textContent = "";
      el.classList.add("hidden");
    }
  }

  function diagnosticT2ShortfallStatusText(run) {
    if (!run || run.diagnostic_expected_shortfall !== true) return null;
    const msgid =
      "Expected diagnostic T2 shortfall (route-feasible vs reconstruction max); not a regression gate.";
    return typeof shapezUiT === "function" ? shapezUiT(msgid) : msgid;
  }

  function runCapacityFailed(run) {
    if (!run || typeof run !== "object") return false;
    if (run.diagnostic_expected_shortfall === true) return false;
    if (run.run_success === true) return false;
    // Top-level null when no throughput target (see _throughput_budget_satisfied_top_level).
    if (run.throughput_budget_satisfied === false) {
      return true;
    }
    if (run.throughput_budget_satisfied === true) return false;
    if (run.capacity_satisfied === true) return false;
    if (run.status === "partial") return true;
    return run.validation_passed === true && run.capacity_satisfied === false;
  }

  function capacityFailedStatusText(run) {
    const placed =
      run.placed != null && run.placed !== "" && run.placed !== "—" ? run.placed : "—";
    const target =
      run.target_miner_bundle_count != null && run.target_miner_bundle_count !== ""
        ? run.target_miner_bundle_count
        : run.target_placement_count != null
          ? run.target_placement_count
          : "—";
    let text =
      "validation passed, capacity failed, placements short: " +
      String(placed) +
      " / " +
      String(target);
    if (run.throughput_budget_satisfied === true) {
      const tp =
        run.confirmed_throughput != null && run.confirmed_throughput !== ""
          ? run.confirmed_throughput
          : "—";
      const tgtTp =
        run.target_throughput != null && run.target_throughput !== ""
          ? run.target_throughput
          : target;
      text += ", throughput OK: " + String(tp) + " / " + String(tgtTp);
    }
    return text;
  }

  function formatMacroCommitHudLine(summary) {
    if (!summary || typeof summary !== "object") {
      return "";
    }
    const hud = summary.macro_commit_summary;
    if (!hud || typeof hud !== "object") {
      return "";
    }
    const macroIds = Array.isArray(hud.committed_macro_ids) ? hud.committed_macro_ids.length : 0;
    const childIds = Array.isArray(hud.committed_child_ids) ? hud.committed_child_ids.length : 0;
    const domainVersion =
      hud.domain_version != null && hud.domain_version !== "" ? String(hud.domain_version) : "—";
    const validation =
      hud.validation_passed === true ? "true" : hud.validation_passed === false ? "false" : "—";
    const conflicts =
      hud.conflict_count != null && hud.conflict_count !== "" ? String(hud.conflict_count) : "0";
    return (
      "macro: on | macros: " +
      String(macroIds) +
      " | children: " +
      String(childIds) +
      " | domain_v: " +
      domainVersion +
      " | validation: " +
      validation +
      " | conflicts: " +
      conflicts
    );
  }

  function renderMacroCommitHud(summary) {
    const hudEl = document.getElementById("lab-macro-commit-hud");
    if (!hudEl) return;
    const line = formatMacroCommitHudLine(summary);
    if (!line) {
      hudEl.textContent = "—";
      hudEl.classList.add("hidden");
      return;
    }
    hudEl.textContent = line;
    hudEl.classList.remove("hidden");
  }

  function renderReplayRunStatus(feedback) {
    const runEl = document.getElementById("lab-replay-run-status");
    if (!runEl) return;
    const dash = "—";
    if (!feedback || typeof feedback !== "object") {
      runEl.textContent = dash;
      renderMacroCommitHud(null);
      return;
    }
    if (feedback.running === true) {
      runEl.textContent = "run: running…";
    } else if (typeof feedback.error_code === "string" && feedback.error_code) {
      runEl.textContent = "run: error " + feedback.error_code;
    } else if (feedback.solver_run_id != null) {
      const vp =
        feedback.validation_passed === true
          ? "passed"
          : feedback.validation_passed === false
            ? "failed"
            : "—";
      let statusText = "run: id " + String(feedback.solver_run_id) + " validation " + vp;
      const rs = feedback.run_summary;
      if (rs && runCapacityFailed(rs)) {
        statusText += " (" + capacityFailedStatusText(rs) + ")";
      }
      if (feedback.gene_template_source && feedback.gene_template_source.gene_count != null) {
        statusText += " genes:" + String(feedback.gene_template_source.gene_count);
      }
      runEl.textContent = statusText;
      renderMacroCommitHud(rs || feedback.run_summary || null);
    } else {
      runEl.textContent = dash;
      renderMacroCommitHud(null);
    }
  }

  function getCookie(name) {
    const prefix = "; " + name + "=";
    const raw = document.cookie;
    const start = raw.indexOf(prefix);
    if (start < 0) {
      return "";
    }
    const from = start + prefix.length;
    const end = raw.indexOf(";", from);
    const token = end < 0 ? raw.substring(from) : raw.substring(from, end);
    try {
      return decodeURIComponent(token);
    } catch {
      return token;
    }
  }

  function replayPhaseForFrame(frame) {
    if (frame < 40) return "Decode + Reconstruction";
    if (frame < 90) return "Candidate Expansion";
    if (frame < 150) return "Route Feasibility";
    return "Final Validation";
  }

  function replayOverlayForFrame(frame) {
    if (frame < 90) return "candidates";
    if (frame < 150) return "routes";
    return "confirmed";
  }

  function overlayIndex(overlay) {
    if (overlay === "routes") return 1;
    if (overlay === "confirmed") return 2;
    return 0;
  }

  /** World x to dense visual column index (lab map: no x == 0 column). */
  function rawXToDenseX(x) {
    const xi = Number(x);
    if (!Number.isFinite(xi)) return null;
    if (xi < 0) return Math.floor((xi + 1) / 2);
    if (xi > 0) return Math.floor((xi - 1) / 2) + 1;
    return 0;
  }

  /** World x to dense visual column for replay grid layout (Lab anchor). */
  function visualCol(x) {
    const xi = Number(x);
    if (!Number.isFinite(xi)) return null;
    if (xi < 0) return xi;
    if (xi > 0) return xi - 1;
    return 0;
  }

  function cellIndexDemo(x, y) {
    const xi = Number(x);
    const yi = Number(y);
    if (!Number.isFinite(xi) || !Number.isFinite(yi)) return null;
    if (xi < 0 || yi < 0 || xi >= GRID_W || yi >= GRID_H) return null;
    return yi * GRID_W + xi;
  }

  function pushCellList(out, list, defaultRole) {
    if (!Array.isArray(list)) return;
    for (let i = 0; i < list.length; i++) {
      const c = list[i];
      if (!c || typeof c !== "object") continue;
      const role = c.overlay_role != null ? String(c.overlay_role) : defaultRole;
      if (role) {
        out.push({ cell: c, role: role });
      } else {
        out.push({ cell: c, role: "" });
      }
    }
  }

  function pushFromComponentBlocks(out, blocks, roleForCells) {
    if (!Array.isArray(blocks)) return;
    for (let j = 0; j < blocks.length; j++) {
      const block = blocks[j];
      if (!block || typeof block !== "object") continue;
      if (Array.isArray(block.cells)) {
        pushCellList(out, block.cells, roleForCells);
      } else if (block.x != null && block.y != null) {
        out.push({ cell: block, role: roleForCells });
      }
    }
  }

  function labCellsFromMapView(mapView) {
    if (!mapView || typeof mapView !== "object") return [];
    const full = mapView.full_cells;
    if (!Array.isArray(full) || !full.length) return [];
    const out = [];
    for (let i = 0; i < full.length; i++) {
      const c = full[i];
      if (!c || typeof c !== "object") continue;
      out.push({
        x: c.x,
        y: c.y,
        cell_kind: c.kind != null ? c.kind : c.cell_kind,
        transport_kind: c.transport != null ? c.transport : c.transport_kind,
        tile_type: c.tile_type != null ? String(c.tile_type) : "",
        sprite_identifier: c.sprite_identifier != null ? String(c.sprite_identifier) : (c.tile_type != null ? String(c.tile_type) : ""),
        rotation: c.rotation,
      });
    }
    return out;
  }

  function sortOverlayCellsForPaint(cells) {
    if (!Array.isArray(cells) || cells.length < 2) return cells;
    const regular = [];
    const planned = [];
    for (let i = 0; i < cells.length; i++) {
      const cell = cells[i];
      if (!cell || typeof cell !== "object") {
        regular.push(cell);
        continue;
      }
      if (String(cell.overlay_role || "") === "planned_exterior_connector") {
        planned.push(cell);
      } else {
        regular.push(cell);
      }
    }
    return regular.concat(planned);
  }

  function overlayCellsFromMapView(mapView, options) {
    if (!mapView || typeof mapView !== "object") return [];
    const ov = mapView.overlay_cells;
    if (!Array.isArray(ov) || !ov.length) return [];
    const skipPlanned =
      options && typeof options === "object" && options.skipPlannedExteriorConnectors === true;
    const plannedCoordKeys =
      options && typeof options === "object" && options.plannedConnectorCoordKeys
        ? options.plannedConnectorCoordKeys
        : null;
    const out = [];
    for (let i = 0; i < ov.length; i++) {
      const c = ov[i];
      if (!c || typeof c !== "object") continue;
      if (skipPlanned && String(c.overlay_role || "") === "planned_exterior_connector") {
        continue;
      }
      if (
        plannedCoordKeys &&
        c.x != null &&
        c.y != null &&
        plannedCoordKeys.has(plannedConnectorCoordKey(c.x, c.y))
      ) {
        continue;
      }
      const row = {
        x: c.x,
        y: c.y,
        cell_kind: c.kind != null ? c.kind : c.cell_kind,
        transport_kind: c.transport != null ? c.transport : c.transport_kind,
        tile_type: c.tile_type != null ? String(c.tile_type) : "",
        sprite_identifier: c.sprite_identifier != null ? String(c.sprite_identifier) : (c.tile_type != null ? String(c.tile_type) : ""),
        rotation: c.rotation,
      };
      if (c.overlay_role != null && String(c.overlay_role) !== "") {
        row.overlay_role = String(c.overlay_role);
      }
      if (c.connector_id != null && String(c.connector_id) !== "") {
        row.connector_id = String(c.connector_id);
      }
      if (c.connector_role != null && String(c.connector_role) !== "") {
        row.connector_role = String(c.connector_role);
      }
      out.push(row);
    }
    return out;
  }

  function cellDeltaCellsFromMapView(mapView) {
    if (!mapView || typeof mapView !== "object") return [];
    const delta = mapView.cell_delta;
    if (!Array.isArray(delta) || !delta.length) return [];
    const out = [];
    for (let i = 0; i < delta.length; i++) {
      const c = delta[i];
      if (!c || typeof c !== "object") continue;
      out.push({
        x: c.x,
        y: c.y,
        cell_kind: c.kind != null ? c.kind : c.cell_kind,
        transport_kind: c.transport != null ? c.transport : c.transport_kind,
        tile_type: c.tile_type != null ? String(c.tile_type) : "",
        sprite_identifier: c.sprite_identifier != null ? String(c.sprite_identifier) : (c.tile_type != null ? String(c.tile_type) : ""),
        rotation: c.rotation,
      });
    }
    return out;
  }

  function fullMapCellsFromFrame(frame) {
    if (!frame || typeof frame !== "object") return [];
    const fromMapView = labCellsFromMapView(frame.map_view);
    if (fromMapView.length) return fromMapView;
    const fromDelta = cellDeltaCellsFromMapView(frame.map_view);
    if (fromDelta.length) return fromDelta;
    if (Array.isArray(frame.full_map) && frame.full_map.length) return frame.full_map;
    const p = frame.frame_payload;
    if (p && typeof p === "object") {
      const nested = p.full_map;
      if (Array.isArray(nested) && nested.length) return nested;
    }
    const ov = frame.cell_overlay_json;
    if (ov && typeof ov === "object" && Array.isArray(ov.cells) && ov.cells.length) return ov.cells;
    return [];
  }

  function frameDiffFromFrame(frame) {
    if (!frame || typeof frame !== "object") return null;
    let d = frame.diff;
    if (d && typeof d === "object") return d;
    const p = frame.frame_payload;
    if (p && typeof p === "object" && p.diff && typeof p.diff === "object") return p.diff;
    return null;
  }

  function pushDiffCells(out, arr, role) {
    if (!Array.isArray(arr)) return;
    for (let i = 0; i < arr.length; i++) {
      const c = arr[i];
      if (!c || typeof c !== "object") continue;
      out.push({ cell: c, role: role });
    }
  }

  function collectDiffPaintTargets(frame) {
    const out = [];
    if (!frame || typeof frame !== "object") return out;
    const d = frameDiffFromFrame(frame);
    if (!d || typeof d !== "object") return out;
    pushDiffCells(out, d.removed, "diff_removed");
    pushDiffCells(out, d.added, "diff_added");
    const ch = d.changed;
    if (!Array.isArray(ch)) return out;
    for (let i = 0; i < ch.length; i++) {
      const item = ch[i];
      if (item && typeof item === "object" && item.after) {
        out.push({ cell: item.after, role: "diff_changed" });
      }
    }
    return out;
  }

  function collectFrameSpatialTargets(frame) {
    const out = [];
    pushCellList(out, fullMapCellsFromFrame(frame), "");
    const mapView = frame && frame.map_view;
    if (mapView && typeof mapView === "object") {
      pushCellList(out, overlayCellsFromMapView(mapView), "");
      pushCellList(out, cellDeltaCellsFromMapView(mapView), "");
    }
    const diffT = collectDiffPaintTargets(frame);
    for (let i = 0; i < diffT.length; i++) out.push(diffT[i]);
    return out;
  }

  /** Collect drawable cells from tolerant overlay shapes (decode / existing_layout). */
  function collectOverlayPaintTargets(overlay) {
    const out = [];
    if (!overlay || typeof overlay !== "object") return out;

    pushCellList(out, overlay.cells, "");
    pushCellList(out, overlay.equipment_cells, "equipment");
    pushCellList(out, overlay.equipment, "equipment");
    pushCellList(out, overlay.adjacent_transport, "adjacent_transport");
    pushFromComponentBlocks(out, overlay.components, "transport");
    pushFromComponentBlocks(out, overlay.transport_components, "transport");
    pushCellList(out, overlay.transport, "transport");

    const main = overlay.main_component_candidate;
    if (main && typeof main === "object") {
      if (Array.isArray(main.cells_json)) {
        pushCellList(out, main.cells_json, "main_component");
      } else if (main.x != null && main.y != null) {
        out.push({ cell: main, role: "main_component" });
      }
    }
    pushCellList(out, overlay.cleanup_candidate_cells, "cleanup_candidate");

    const handled = new Set([
      "cells",
      "equipment_cells",
      "equipment",
      "adjacent_transport",
      "components",
      "transport_components",
      "transport",
      "main_component_candidate",
      "cleanup_candidate_cells",
    ]);
    const keys = Object.keys(overlay);
    for (let k = 0; k < keys.length; k++) {
      const key = keys[k];
      if (handled.has(key)) continue;
      const val = overlay[key];
      if (val && typeof val === "object" && !Array.isArray(val) && Array.isArray(val.cells_json)) {
        pushCellList(out, val.cells_json, key);
      }
    }
    return out;
  }

  function computeReplayGridLayout(replayFrames) {
    /* Lab grid uses island-local ``cell.x`` / ``cell.y`` (visualCol); no dense server frame. */
    let minD = Infinity;
    let maxD = -Infinity;
    let minR = Infinity;
    let maxR = -Infinity;
    let any = false;
    for (let fi = 0; fi < replayFrames.length; fi++) {
      const fr = replayFrames[fi];
      if (!fr || typeof fr !== "object") continue;
      const targets = collectFrameSpatialTargets(fr);
      for (let ti = 0; ti < targets.length; ti++) {
        const cell = targets[ti].cell;
        if (!cell || typeof cell !== "object") continue;
        const d = visualCol(cell.x);
        if (d == null) continue;
        const yi = Number(cell.y);
        if (!Number.isFinite(yi)) continue;
        any = true;
        if (d < minD) minD = d;
        if (d > maxD) maxD = d;
        if (yi < minR) minR = yi;
        if (yi > maxR) maxR = yi;
      }
    }
    if (!any) {
      minD = maxD = minR = maxR = 0;
    }
    const coreHalfX = Math.max(Math.max(0, -minD), Math.max(0, maxD), 1);
    const coreHalfY = Math.max(Math.max(0, -minR), Math.max(0, maxR), 1);
    const halfX = coreHalfX + REPLAY_GRID_EDGE_PADDING;
    const halfY = coreHalfY + REPLAY_GRID_EDGE_PADDING;
    return {
      minD: -halfX,
      maxD: halfX,
      minR: -halfY,
      maxR: halfY,
      gridW: 2 * halfX + 1,
      gridH: 2 * halfY + 1,
    };
  }

  var ROUTE_OVERLAY_CELL_KINDS = {
    route_probe: true,
    route_probe_path: true,
    confirmed_route: true,
    route_goal: true,
  };

  /** L3 pool probe window (+ legacy wire on that frame): tint-only overlays (no belt/pipe sprites). */
  var NON_SPRITE_OVERLAY_CELL_KINDS = {
    candidate_miner: true,
    candidate_transport_stub: true,
    candidate_route_path: true,
    route_path: true,
  };

  var LAYER03_POOL_SUMMARY_EVENT = "layer03_rim_bundle_pool_summary";
  var LAYER03_POOL_PROBE_WINDOW_EVENT = "layer03_rim_bundle_pool_probe_window";
  var LAYER03_GREEDY_EVENT_PREFIX = "layer03_rim_greedy_";

  /** Pre-candidate_* replay wire on L3 pool summary frames only. */
  var LEGACY_L3_POOL_OVERLAY_CELL_KINDS = {
    miner: true,
    extension: true,
    transport_stub: true,
    route_path: true,
  };

  var CANDIDATE_OBSERVATION_TITLE = "candidate only / not committed";

  function isRouteOverlayCellKind(cellKind) {
    return ROUTE_OVERLAY_CELL_KINDS[String(cellKind || "")] === true;
  }

  function overlayCellKind(cell) {
    if (!cell || typeof cell !== "object") return "";
    if (cell.cell_kind != null && String(cell.cell_kind) !== "") {
      return String(cell.cell_kind);
    }
    if (cell.kind != null && String(cell.kind) !== "") {
      return String(cell.kind);
    }
    return "";
  }

  function isL3PoolProbeWindowFrame(frame) {
    if (!frame) return false;
    return String(frame.event_type || "") === LAYER03_POOL_PROBE_WINDOW_EVENT;
  }

  function isL3GreedyReplayFrame(frame) {
    if (!frame) return false;
    return String(frame.event_type || "").indexOf(LAYER03_GREEDY_EVENT_PREFIX) === 0;
  }

  /** Legacy pool windows + rim greedy placement preview frames. */
  function isL3PoolCandidateObservationFrame(frame) {
    return isL3PoolProbeWindowFrame(frame) || isL3GreedyReplayFrame(frame);
  }

  function isL3ProbeWindowBaseFieldCellKind(cellKind) {
    const ck = String(cellKind || "");
    return (
      ck === "asteroid_shape_field" ||
      ck === "asteroid_fluid_field" ||
      ck === "internal_void"
    );
  }

  function labCellHasBaseSprite(el) {
    if (!el) return false;
    return Boolean(el.querySelector(".lab-cell-sprite-layer[data-lab-sprite], .lab-cell-sprite-layer img.lab-cell-sprite"));
  }

  function isCandidateMinerOverlayKind(cellKind) {
    const ck = String(cellKind || "");
    return ck === "candidate_miner" || ck === "miner";
  }

  /** Stub/route tints are void-only; asteroid sprites stay unchanged unless miner. */
  function shouldSkipCandidateObservationOnSpriteCell(frame, cellKind, el) {
    if (!isL3PoolCandidateObservationFrame(frame)) return false;
    if (!labCellHasBaseSprite(el)) return false;
    return !isCandidateMinerOverlayKind(cellKind);
  }

  function sortL3CandidateOverlayCellsForPaint(cells) {
    if (!Array.isArray(cells) || cells.length < 2) return cells;
    const rank = function (cell) {
      const ck = overlayCellKind(cell);
      if (isCandidateMinerOverlayKind(ck)) return 2;
      if (ck === "candidate_transport_stub" || ck === "transport_stub") return 1;
      if (ck === "candidate_route_path" || ck === "route_path") return 0;
      return 1;
    };
    return cells.slice().sort(function (a, b) {
      return rank(a) - rank(b);
    });
  }

  /** Tint-only L3 candidate overlay; ring when a base sprite is already painted. */
  function candidateObservationToneClasses(cellKind, el) {
    const ck = String(cellKind || "");
    const hasSprite = labCellHasBaseSprite(el);
    if (isCandidateMinerOverlayKind(ck)) {
      return hasSprite
        ? "lab-overlay-candidate-miner-ring relative"
        : "lab-overlay-candidate-miner relative";
    }
    if (hasSprite) {
      return "";
    }
    if (ck === "candidate_transport_stub" || ck === "transport_stub") {
      return "lab-overlay-candidate-transport-stub relative";
    }
    if (ck === "candidate_route_path" || ck === "route_path") {
      return "lab-overlay-candidate-route-path relative";
    }
    return "";
  }

  function isNonSpriteOverlayCell(cell, frame) {
    const ck = overlayCellKind(cell);
    if (!ck) return false;
    if (NON_SPRITE_OVERLAY_CELL_KINDS[ck] === true) return true;
    if (isL3PoolCandidateObservationFrame(frame) && LEGACY_L3_POOL_OVERLAY_CELL_KINDS[ck] === true) {
      return true;
    }
    return false;
  }

  function isCandidateObservationOverlayKind(cellKind) {
    const ck = String(cellKind || "");
    if (NON_SPRITE_OVERLAY_CELL_KINDS[ck] === true) return true;
    return LEGACY_L3_POOL_OVERLAY_CELL_KINDS[ck] === true;
  }

  function toneForRouteOverlayKind(cellKind) {
    const ck = String(cellKind || "");
    if (ck === "route_goal") {
      return "lab-route-goal-tone ring-2 ring-inset ring-violet-400/90 bg-violet-500/35";
    }
    if (ck === "confirmed_route") {
      return "lab-route-confirmed-tone ring-2 ring-inset ring-lime-400/90 bg-lime-500/35";
    }
    if (ck === "route_probe" || ck === "route_probe_path") {
      return "lab-route-probe-tone ring-2 ring-inset ring-amber-400/85 bg-amber-500/30";
    }
    return "";
  }

  function overlayToneClasses(role, cell) {
    const r = String(role || "");
    if (r === "equipment" || r === "equipment_cells") {
      return "ring-1 ring-inset ring-amber-400/50 bg-amber-950/20";
    }
    if (r === "transport" || r === "adjacent_transport" || r === "main_component") {
      return "ring-1 ring-inset ring-cyan-400/40 bg-cyan-950/20";
    }
    if (r === "cleanup_candidate") {
      return "ring-1 ring-inset ring-orange-400/45 bg-orange-950/20";
    }
    if (r === "decode") {
      return "lab-decode-cell-tone";
    }
    if (r === "planned_exterior_connector") {
      return "lab-planned-exterior-connector relative";
    }
    return "ring-1 ring-inset ring-violet-400/35 bg-violet-950/15";
  }

  function toneForFullMapCell(cell, frame) {
    const ckEarly =
      cell && cell.cell_kind != null
        ? String(cell.cell_kind)
        : cell && cell.kind != null
          ? String(cell.kind)
          : "";
    if (isL3PoolProbeWindowFrame(frame) && isL3ProbeWindowBaseFieldCellKind(ckEarly)) {
      return "";
    }
    const overlayRole =
      cell && cell.overlay_role != null ? String(cell.overlay_role) : "";
    if (overlayRole === "planned_exterior_connector") {
      if (normalizeConnectorRole(cell.connector_role) === "spare") {
        return "lab-planned-exterior-connector-spare relative";
      }
      return "lab-planned-exterior-connector relative";
    }
    const ck = cell && cell.cell_kind != null ? String(cell.cell_kind) : "";
    if (ck === "candidate_miner") {
      return "lab-overlay-candidate-miner relative";
    }
    if (ck === "candidate_transport_stub") {
      return "lab-overlay-candidate-transport-stub relative";
    }
    if (ck === "candidate_route_path" || ck === "route_path") {
      return "lab-overlay-candidate-route-path relative";
    }
    const routeTone = toneForRouteOverlayKind(ck);
    if (routeTone) return routeTone;
    if (ck === "space_pipe" || ck === "space_belt") {
      return "ring-1 ring-inset ring-cyan-400/40 bg-cyan-950/20";
    }
    if (ck === "fluid_miner" || ck === "shape_miner") {
      return "ring-1 ring-inset ring-amber-400/50 bg-amber-950/20";
    }
    if (ck === "fluid_miner_extension" || ck === "shape_miner_extension") {
      return "ring-1 ring-inset ring-amber-300/40 bg-amber-950/12";
    }
    if (ck === "asteroid_fluid_field") {
      return "ring-1 ring-inset ring-teal-400/50 bg-teal-950/28";
    }
    if (ck === "asteroid_shape_field") {
      return "ring-1 ring-inset ring-emerald-400/50 bg-emerald-950/28";
    }
    if (ck === "internal_void") {
      return "ring-1 ring-inset ring-fuchsia-400/55 bg-fuchsia-950/28";
    }
    return overlayToneClasses("", cell);
  }

  function toneForDiffRole(role) {
    const r = String(role || "");
    if (r === "diff_removed") {
      return "opacity-75 ring-1 ring-inset ring-red-500/70 bg-red-950/35";
    }
    if (r === "diff_added") {
      return "ring-1 ring-inset ring-emerald-400/55 bg-emerald-950/25";
    }
    if (r === "diff_changed") {
      return "ring-1 ring-inset ring-yellow-400/50 bg-yellow-950/20";
    }
    return "";
  }

  function renderFullMapCells(baseClasses, domCells, cells, resolveCellIndex, frame) {
    if (!Array.isArray(cells)) return;
    for (let i = 0; i < cells.length; i++) {
      const cell = cells[i];
      if (!cell || typeof cell !== "object") continue;
      const idx = resolveCellIndex(cell);
      if (idx == null || idx < 0 || idx >= domCells.length) continue;
      const base = baseClasses[idx] || "";
      const ck = overlayCellKind(cell);
      const el = domCells[idx];
      const candidateObs = isNonSpriteOverlayCell(cell, frame);
      if (candidateObs && shouldSkipCandidateObservationOnSpriteCell(frame, ck, el)) {
        continue;
      }
      let tone = toneForFullMapCell(cell, frame);
      if (candidateObs) {
        const obsTone = candidateObservationToneClasses(ck, el);
        if (obsTone) {
          tone = obsTone;
        } else if (isL3PoolProbeWindowFrame(frame)) {
          continue;
        }
      }
      el.className = tone ? base + " " + tone : base;
      const hudRole =
        cell.overlay_role != null
          ? String(cell.overlay_role)
          : isRouteOverlayCellKind(ck)
            ? ck
            : candidateObs
              ? ck
              : "";
      applyLabCellHudAttributes(el, cell, hudRole);
      if (candidateObs) {
        el.setAttribute("title", CANDIDATE_OBSERVATION_TITLE);
        el.setAttribute("data-lab-candidate-overlay", "1");
      } else {
        el.removeAttribute("title");
        el.removeAttribute("data-lab-candidate-overlay");
      }
      if (!candidateObs) {
        applyLabCellSprite(el, cell, frame);
      }
    }
  }

  function renderDiffOverlays(baseClasses, domCells, frame, resolveCellIndex) {
    const targets = collectDiffPaintTargets(frame);
    for (let i = 0; i < targets.length; i++) {
      const cell = targets[i].cell;
      const role = targets[i].role;
      const idx = resolveCellIndex(cell);
      if (idx == null || idx < 0 || idx >= domCells.length) continue;
      const tone = toneForDiffRole(role);
      if (!tone) continue;
      const base = baseClasses[idx] || "";
      const el = domCells[idx];
      el.className = base + " " + tone;
      applyLabCellHudAttributes(el, cell, role);
      applyLabCellSprite(el, cell);
    }
  }

  /** Per-bundle outer edges (1px; complementary pairs — matches pattern SVG palette). */
  var BUNDLE_EDGE_PALETTE = [
    { n: "border-t border-t-blue-400", e: "border-r border-r-blue-400", s: "border-b border-b-blue-400", w: "border-l border-l-blue-400" },
    { n: "border-t border-t-orange-400", e: "border-r border-r-orange-400", s: "border-b border-b-orange-400", w: "border-l border-l-orange-400" },
    { n: "border-t border-t-violet-400", e: "border-r border-r-violet-400", s: "border-b border-b-violet-400", w: "border-l border-l-violet-400" },
    { n: "border-t border-t-amber-300", e: "border-r border-r-amber-300", s: "border-b border-b-amber-300", w: "border-l border-l-amber-300" },
    { n: "border-t border-t-green-400", e: "border-r border-r-green-400", s: "border-b border-b-green-400", w: "border-l border-l-green-400" },
    { n: "border-t border-t-rose-400", e: "border-r border-r-rose-400", s: "border-b border-b-rose-400", w: "border-l border-l-rose-400" },
    { n: "border-t border-t-cyan-400", e: "border-r border-r-cyan-400", s: "border-b border-b-cyan-400", w: "border-l border-l-cyan-400" },
    { n: "border-t border-t-red-400", e: "border-r border-r-red-400", s: "border-b border-b-red-400", w: "border-l border-l-red-400" },
  ];

  /** Inset fill per bundle id (paired with ``BUNDLE_EDGE_PALETTE``); not Tailwind — avoids purge. */
  var BUNDLE_FILL_INSET_RGBA = [
    "rgba(96, 165, 250, 0.12)",
    "rgba(251, 146, 60, 0.12)",
    "rgba(192, 132, 252, 0.12)",
    "rgba(250, 204, 21, 0.12)",
    "rgba(74, 222, 128, 0.12)",
    "rgba(251, 113, 133, 0.12)",
    "rgba(34, 211, 238, 0.12)",
    "rgba(248, 113, 113, 0.12)",
  ];

  /** Solid bridge bars (paired with ``BUNDLE_EDGE_PALETTE`` / inset fill). */
  var BUNDLE_BRIDGE_HEX = [
    "#60a5fa",
    "#fb923c",
    "#c084fc",
    "#facc15",
    "#4ade80",
    "#fb7185",
    "#22d3ee",
    "#f87171",
  ];

  function clearLabCellBundleBridges(el) {
    if (!el || !el.querySelectorAll) return;
    var bridges = el.querySelectorAll("[data-lab-bundle-bridge]");
    for (var i = 0; i < bridges.length; i++) {
      bridges[i].remove();
    }
  }

  function cellOverlayJsonFromFrame(frame) {
    if (!frame || typeof frame !== "object") return null;
    var top = frame.cell_overlay_json;
    if (top && typeof top === "object") return top;
    var p = frame.frame_payload;
    if (p && typeof p === "object" && p.cell_overlay_json && typeof p.cell_overlay_json === "object") {
      return p.cell_overlay_json;
    }
    return null;
  }

  /** ``cell_overlay_json``: ``equipment_bundles[].cells_json`` with ``bundle_edges`` (hull) + ``bundle_links`` (gap bridges). */
  function applyEquipmentBundleGroupVisualsFromOverlay(ov, domCells, resolveCellIndex) {
    if (!ov || typeof ov !== "object") return;
    var bundles = ov.equipment_bundles;
    if (!Array.isArray(bundles) || bundles.length === 0) return;
    for (var bi = 0; bi < bundles.length; bi++) {
      var block = bundles[bi];
      if (!block || typeof block !== "object") continue;
      var bid = Number(block.bundle_id);
      var pi = (Number.isFinite(bid) ? bid - 1 : 0) % BUNDLE_EDGE_PALETTE.length;
      if (pi < 0) pi = 0;
      var colors = BUNDLE_EDGE_PALETTE[pi];
      var fillRgba = BUNDLE_FILL_INSET_RGBA[pi % BUNDLE_FILL_INSET_RGBA.length];
      var cells = block.cells_json;
      if (!Array.isArray(cells)) continue;
      for (var ci = 0; ci < cells.length; ci++) {
        var cell = cells[ci];
        if (!cell || typeof cell !== "object") continue;
        var idx = resolveCellIndex(cell);
        if (idx == null || idx < 0 || idx >= domCells.length) continue;
        var el = domCells[idx];
        clearLabCellBundleBridges(el);
        el.style.boxShadow = "inset 0 0 0 9999px " + fillRgba;
        var edges = cell.bundle_edges != null ? String(cell.bundle_edges) : "";
        var parts = [];
        if (edges.indexOf("n") >= 0) parts.push(colors.n);
        if (edges.indexOf("e") >= 0) parts.push(colors.e);
        if (edges.indexOf("s") >= 0) parts.push(colors.s);
        if (edges.indexOf("w") >= 0) parts.push(colors.w);
        if (parts.length) {
          el.className = el.className + " " + parts.join(" ");
        }
        var linkStr = cell.bundle_links != null ? String(cell.bundle_links) : "";
        if (linkStr) {
          var hex = BUNDLE_BRIDGE_HEX[pi % BUNDLE_BRIDGE_HEX.length];
          for (var li = 0; li < linkStr.length; li++) {
            var d = linkStr.charAt(li);
            var dir = LINK_KEY_TO_DIR[d];
            if (dir === undefined) continue;
            var suffix = DIR_TO_BRIDGE_SUFFIX[dir];
            var br = document.createElement("div");
            br.setAttribute("data-lab-bundle-bridge", "1");
            br.setAttribute("aria-hidden", "true");
            br.className = "lab-bundle-bridge lab-bundle-bridge-" + suffix;
            br.style.backgroundColor = hex;
            el.appendChild(br);
          }
        }
      }
    }
  }

  function applyEquipmentBundleStrokeClasses(frame, domCells, resolveCellIndex) {
    maybeApplyEquipmentBundleGroupVisualsFromOverlay(
      cellOverlayJsonFromFrame(frame),
      domCells,
      resolveCellIndex,
    );
  }

  const LAB_TERRAIN_RIM_STORAGE_KEY = "lab-terrain-rim-highlight";
  const LAB_PATTERN_BUNDLE_STORAGE_KEY = "lab-pattern-bundle-highlight";
  const LAB_PATTERN_BUNDLE_PALETTE_SIZE = 8;
  const LAB_EXTERIOR_CONNECTOR_ROLE = "planned_exterior_connector";
  const LAB_EXTERIOR_CONNECTOR_METRICS_KEY = "exterior_connector_plan";
  const LAB_FROZEN_EXTERIOR_CONNECTOR_PLAN_KEY = "frozen_exterior_connector_plan";

  function isTerrainRimHighlightEnabled() {
    const toggle = document.getElementById("lab-terrain-rim-highlight-toggle");
    if (toggle && !toggle.checked) {
      return false;
    }
    try {
      const stored = window.localStorage.getItem(LAB_TERRAIN_RIM_STORAGE_KEY);
      if (stored === "0") {
        return false;
      }
    } catch (_err) {
      return true;
    }
    return true;
  }

  function persistTerrainRimHighlightEnabled(enabled) {
    try {
      window.localStorage.setItem(LAB_TERRAIN_RIM_STORAGE_KEY, enabled ? "1" : "0");
    } catch (_err) {
      /* ignore */
    }
  }

  function isPatternBundleHighlightEnabled() {
    const toggle = document.getElementById("lab-pattern-bundle-highlight-toggle");
    if (toggle && !toggle.checked) {
      return false;
    }
    try {
      const stored = window.localStorage.getItem(LAB_PATTERN_BUNDLE_STORAGE_KEY);
      if (stored === "0") {
        return false;
      }
    } catch (_err) {
      return true;
    }
    return true;
  }

  function persistPatternBundleHighlightEnabled(enabled) {
    try {
      window.localStorage.setItem(LAB_PATTERN_BUNDLE_STORAGE_KEY, enabled ? "1" : "0");
    } catch (_err) {
      /* ignore */
    }
  }

  function resolvePatternBundleHighlightWire(frame) {
    if (!frame || typeof frame !== "object") {
      return null;
    }
    const fm =
      frame.metrics && typeof frame.metrics === "object"
        ? frame.metrics.pattern_bundle_highlights
        : null;
    if (fm && typeof fm === "object") {
      return fm;
    }
    return null;
  }

  function resolveTerrainRimHighlightWire(frame, trackMetrics) {
    if (!frame || typeof frame !== "object") {
      return null;
    }
    const fm =
      frame.metrics && typeof frame.metrics === "object"
        ? frame.metrics.terrain_rim_highlight
        : null;
    if (fm && typeof fm === "object") {
      return fm;
    }
    const tm = trackMetrics && typeof trackMetrics === "object" ? trackMetrics : {};
    const frozen = tm.frozen_terrain_rim_highlight;
    if (frozen && typeof frozen === "object") {
      return frozen;
    }
    return null;
  }

  function resolveExteriorConnectorPlanWire(frame, trackMetrics) {
    if (!frame || typeof frame !== "object") {
      return null;
    }
    const fm =
      frame.metrics && typeof frame.metrics === "object"
        ? frame.metrics[LAB_EXTERIOR_CONNECTOR_METRICS_KEY]
        : null;
    if (fm && typeof fm === "object") {
      return fm;
    }
    const tm = trackMetrics && typeof trackMetrics === "object" ? trackMetrics : {};
    const frozen = tm[LAB_FROZEN_EXTERIOR_CONNECTOR_PLAN_KEY];
    if (frozen && typeof frozen === "object") {
      return frozen;
    }
    return null;
  }

  function cornerToStagePx(cx, cy, layout, cellPx, gapPx) {
    const d = visualCol(cx);
    if (d == null || !layout) return null;
    const yi = Number(cy);
    if (!Number.isFinite(yi)) return null;
    const col = d - layout.minD;
    const row = yi - layout.minR;
    const step = cellPx + gapPx;
    return { x: col * step, y: row * step };
  }

  function clearTerrainRimOutlineSvg() {
    const layer = document.getElementById("lab-optimization-overlay-layer");
    if (!layer) {
      return;
    }
    const nodes = layer.querySelectorAll(".lab-terrain-rim-outline-svg");
    for (let i = 0; i < nodes.length; i++) {
      nodes[i].remove();
    }
  }

  function clearPatternBundleOutlineSvg() {
    const layer = document.getElementById("lab-optimization-overlay-layer");
    if (!layer) {
      return;
    }
    const nodes = layer.querySelectorAll(".lab-pattern-bundle-outline-svg");
    for (let i = 0; i < nodes.length; i++) {
      nodes[i].remove();
    }
  }

  function buildSvgPathDataFromOutlineLoops(loops, layout, cellPx, gapPx) {
    if (!Array.isArray(loops) || loops.length === 0 || !layout) {
      return "";
    }
    let pathData = "";
    for (let li = 0; li < loops.length; li++) {
      const loop = loops[li];
      if (!Array.isArray(loop) || loop.length < 2) {
        continue;
      }
      let segment = "";
      for (let pi = 0; pi < loop.length; pi++) {
        const pt = loop[pi];
        if (!Array.isArray(pt) || pt.length < 2) {
          continue;
        }
        const px = cornerToStagePx(Number(pt[0]), Number(pt[1]), layout, cellPx, gapPx);
        if (!px) {
          continue;
        }
        segment += (pi === 0 ? "M " : " L ") + String(px.x) + " " + String(px.y);
      }
      if (segment) {
        pathData += segment + " Z ";
      }
    }
    return pathData.trim();
  }

  function applyTerrainRimOutlineSvg(wire, layout, cellPx, gapPx) {
    clearTerrainRimOutlineSvg();
    if (!wire || typeof wire !== "object" || !layout) {
      return;
    }
    const pathData = buildSvgPathDataFromOutlineLoops(
      wire.outer_outline_loops,
      layout,
      cellPx,
      gapPx,
    );
    if (!pathData) {
      return;
    }
    const layer = document.getElementById("lab-optimization-overlay-layer");
    if (!layer) {
      return;
    }
    const svgNs = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNs, "svg");
    svg.setAttribute("class", "lab-terrain-rim-outline-svg");
    svg.setAttribute("width", "100%");
    svg.setAttribute("height", "100%");
    svg.setAttribute("aria-hidden", "true");
    const pathEl = document.createElementNS(svgNs, "path");
    pathEl.setAttribute("class", "lab-terrain-rim-outline-path");
    pathEl.setAttribute("d", pathData);
    svg.appendChild(pathEl);
    layer.appendChild(svg);
  }

  function applyPatternBundleHighlightSvg(wire, layout, cellPx, gapPx) {
    clearPatternBundleOutlineSvg();
    if (!wire || typeof wire !== "object" || !layout) {
      return;
    }
    const bundles = wire.bundles;
    if (!Array.isArray(bundles) || bundles.length === 0) {
      return;
    }
    const layer = document.getElementById("lab-optimization-overlay-layer");
    if (!layer) {
      return;
    }
    const svgNs = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNs, "svg");
    svg.setAttribute("class", "lab-pattern-bundle-outline-svg");
    svg.setAttribute("width", "100%");
    svg.setAttribute("height", "100%");
    svg.setAttribute("aria-hidden", "true");
    for (let bi = 0; bi < bundles.length; bi++) {
      const block = bundles[bi];
      if (!block || typeof block !== "object") {
        continue;
      }
      const pathData = buildSvgPathDataFromOutlineLoops(
        block.outline_loops,
        layout,
        cellPx,
        gapPx,
      );
      if (!pathData) {
        continue;
      }
      let colorIndex = Number(block.color_index);
      if (!Number.isFinite(colorIndex)) {
        colorIndex = bi % LAB_PATTERN_BUNDLE_PALETTE_SIZE;
      } else {
        colorIndex =
          ((colorIndex % LAB_PATTERN_BUNDLE_PALETTE_SIZE) + LAB_PATTERN_BUNDLE_PALETTE_SIZE) %
          LAB_PATTERN_BUNDLE_PALETTE_SIZE;
      }
      const pathEl = document.createElementNS(svgNs, "path");
      pathEl.setAttribute("class", "lab-pattern-bundle-outline-path");
      pathEl.setAttribute("data-color-index", String(colorIndex));
      pathEl.setAttribute("d", pathData);
      svg.appendChild(pathEl);
    }
    if (svg.childNodes.length) {
      layer.appendChild(svg);
    }
  }

  function applyTerrainRimHighlight(wire, layout, cellPx, gapPx) {
    applyTerrainRimOutlineSvg(wire, layout, cellPx, gapPx);
  }

  function applyLabOverlayHighlights(frame, trackMetrics, rimDrawCtx) {
    if (!rimDrawCtx || !rimDrawCtx.layout) {
      clearTerrainRimOutlineSvg();
      clearPatternBundleOutlineSvg();
      return;
    }
    if (isTerrainRimHighlightEnabled()) {
      const rimWire = resolveTerrainRimHighlightWire(frame, trackMetrics);
      if (rimWire) {
        applyTerrainRimHighlight(rimWire, rimDrawCtx.layout, rimDrawCtx.cellPx, rimDrawCtx.gapPx);
      } else {
        clearTerrainRimOutlineSvg();
      }
    } else {
      clearTerrainRimOutlineSvg();
    }
    if (isPatternBundleHighlightEnabled()) {
      const patternWire = resolvePatternBundleHighlightWire(frame);
      if (patternWire) {
        applyPatternBundleHighlightSvg(
          patternWire,
          rimDrawCtx.layout,
          rimDrawCtx.cellPx,
          rimDrawCtx.gapPx,
        );
      } else {
        clearPatternBundleOutlineSvg();
      }
    } else {
      clearPatternBundleOutlineSvg();
    }
  }

  function maybeApplyEquipmentBundleGroupVisualsFromOverlay(ov, domCells, resolveCellIndex) {
    if (isPatternBundleHighlightEnabled()) {
      return;
    }
    applyEquipmentBundleGroupVisualsFromOverlay(ov, domCells, resolveCellIndex);
  }

  function renderDecodedCells(baseClasses, domCells, cells, resolveCellIndex) {
    if (!Array.isArray(cells)) return;
    const targets = [];
    pushCellList(targets, cells, "");
    for (let i = 0; i < targets.length; i++) {
      const cell = targets[i].cell;
      const role = targets[i].role;
      const idx = resolveCellIndex(cell);
      if (idx == null || idx < 0 || idx >= domCells.length) continue;
      const base = baseClasses[idx] || "";
      const tone = overlayToneClasses("decode", cell);
      const el = domCells[idx];
      el.className = base + " " + tone;
      applyLabCellHudAttributes(el, cell, role != null ? String(role) : "");
      applyLabCellSprite(el, cell);
    }
  }

  function renderExistingLayoutOverlay(baseClasses, domCells, overlay, resolveCellIndex) {
    const targets = collectOverlayPaintTargets(overlay);
    for (let i = 0; i < targets.length; i++) {
      const cell = targets[i].cell;
      const role = targets[i].role;
      const idx = resolveCellIndex(cell);
      if (idx == null || idx < 0 || idx >= domCells.length) continue;
      const base = baseClasses[idx] || "";
      const tone = overlayToneClasses(role, cell);
      const el = domCells[idx];
      el.className = base + " " + tone;
      applyLabCellHudAttributes(el, cell, role != null ? String(role) : "");
      applyLabCellSprite(el, cell);
    }
  }

  function renderCellOverlay(baseClasses, domCells, overlay, resolveCellIndex) {
    if (!overlay || typeof overlay !== "object") return;
    const cells = overlay.cells;
    if (Array.isArray(cells) && cells.length > 0) {
      renderDecodedCells(baseClasses, domCells, cells, resolveCellIndex);
      maybeApplyEquipmentBundleGroupVisualsFromOverlay(overlay, domCells, resolveCellIndex);
      return;
    }
    renderExistingLayoutOverlay(baseClasses, domCells, overlay, resolveCellIndex);
    maybeApplyEquipmentBundleGroupVisualsFromOverlay(overlay, domCells, resolveCellIndex);
  }

  function resetGridBase(domCells, baseClasses) {
    for (let i = 0; i < domCells.length; i++) {
      clearLabCellBundleBridges(domCells[i]);
      clearPlannedExteriorConnectorHighlight(domCells[i]);
      domCells[i].className = baseClasses[i] || "";
      domCells[i].style.boxShadow = "";
      domCells[i].style.backgroundColor = "";
      domCells[i].style.border = "";
      domCells[i].style.zIndex = "";
      domCells[i].removeAttribute("data-cell-kind");
      domCells[i].removeAttribute("data-overlay-role");
      domCells[i].removeAttribute("data-tile-type");
      clearLabCellSprite(domCells[i]);
    }
  }

  function frameHasRenderableMap(frame) {
    return fullMapCellsFromFrame(frame).length > 0;
  }

  function formatOptimizationMilestoneHint(frame) {
    if (!frame || typeof frame !== "object") {
      return "—";
    }
    const parts = [];
    if (frame.event_type) {
      parts.push(String(frame.event_type));
    }
    const m = frame.metrics;
    if (m && typeof m === "object") {
      if (m.normal_count != null) {
        parts.push("normal_count=" + String(m.normal_count));
      }
      if (m.rejected_count != null) {
        parts.push("rejected_count=" + String(m.rejected_count));
      }
      if (m.commit_order != null) {
        parts.push("commit_order=" + String(m.commit_order));
      }
      if (parts.length <= 1) {
        const keys = Object.keys(m).slice(0, 4);
        for (let ki = 0; ki < keys.length; ki++) {
          const k = keys[ki];
          parts.push(k + "=" + String(m[k]));
        }
      }
    }
    return parts.length ? parts.join(" · ") : "optimization milestone";
  }

  function renderFullMapReplayFrame(frame, baseClasses, domCells, resolveCellIndex, trackMetrics, rimDrawCtx) {
    const fm = fullMapCellsFromFrame(frame);
    if (!fm.length) return false;
    renderFullMapCells(baseClasses, domCells, fm, resolveCellIndex, frame);
    const planWire = resolveExteriorConnectorPlanWire(frame, trackMetrics);
    const plannedCoordKeys = plannedConnectorCoordKeySet(planWire);
    let ovCells = overlayCellsFromMapView(frame.map_view, {
      skipPlannedExteriorConnectors: true,
      plannedConnectorCoordKeys: plannedCoordKeys,
    });
    if (isL3PoolCandidateObservationFrame(frame) && ovCells.length > 1) {
      ovCells = sortL3CandidateOverlayCellsForPaint(ovCells);
    }
    if (ovCells.length) {
      renderFullMapCells(baseClasses, domCells, ovCells, resolveCellIndex, frame);
    }
    const deltaCells = cellDeltaCellsFromMapView(frame.map_view);
    if (deltaCells.length) {
      renderFullMapCells(baseClasses, domCells, deltaCells, resolveCellIndex, frame);
    }
    renderDiffOverlays(baseClasses, domCells, frame, resolveCellIndex);
    if (!isPatternBundleHighlightEnabled()) {
      applyEquipmentBundleStrokeClasses(frame, domCells, resolveCellIndex);
    }
    renderPlannedExteriorConnectorHighlights(
      frame,
      baseClasses,
      domCells,
      resolveCellIndex,
      trackMetrics,
    );
    applyLabOverlayHighlights(frame, trackMetrics, rimDrawCtx);
    return true;
  }

  function renderReplayFrame(
    frame,
    baseClasses,
    domCells,
    resolveCellIndex,
    allFrames,
    trackMetrics,
    rimDrawCtx,
  ) {
    if (!frame || typeof frame !== "object") {
      resetGridBase(domCells, baseClasses);
      return;
    }
    const fm = fullMapCellsFromFrame(frame);
    if (fm.length) {
      resetGridBase(domCells, baseClasses);
      renderFullMapReplayFrame(
        frame,
        baseClasses,
        domCells,
        resolveCellIndex,
        trackMetrics,
        rimDrawCtx,
      );
      return;
    }
    clearTerrainRimOutlineSvg();
    clearPatternBundleOutlineSvg();
    const ov = frame.cell_overlay_json;
    if (ov && typeof ov === "object") {
      resetGridBase(domCells, baseClasses);
      renderCellOverlay(baseClasses, domCells, ov, resolveCellIndex);
      applyLabOverlayHighlights(frame, trackMetrics, rimDrawCtx);
      return;
    }
    resetGridBase(domCells, baseClasses);
    applyLabOverlayHighlights(frame, trackMetrics, rimDrawCtx);
  }

  function updateFrameInfo(frame, totalCount, phaseEl, frameEl, gridEl, timelineSlotIndex) {
    const dash = "—";
    const denom = Number.isFinite(totalCount) ? totalCount : 0;
    if (!frame || typeof frame !== "object") {
      if (phaseEl) phaseEl.textContent = dash;
      const et = document.getElementById("lab-replay-event-type");
      const ti = document.getElementById("lab-replay-title");
      const de = document.getElementById("lab-replay-description");
      if (et) et.textContent = dash;
      if (ti) ti.textContent = dash;
      if (de) de.textContent = dash;
      if (frameEl) frameEl.textContent = formatLabFrameCounter(0, denom);
      return;
    }
    if (phaseEl) phaseEl.textContent = frame.phase != null ? String(frame.phase) : dash;
    const et = document.getElementById("lab-replay-event-type");
    const ti = document.getElementById("lab-replay-title");
    const de = document.getElementById("lab-replay-description");
    if (et) et.textContent = frame.event_type ? String(frame.event_type) : dash;
    if (ti) ti.textContent = frame.title != null ? String(frame.title) : dash;
    if (de) de.textContent = frame.description != null ? String(frame.description) : dash;
    let slot = timelineSlotIndex;
    if (slot == null || !Number.isFinite(Number(slot))) {
      const fi = Number(frame.frame_index);
      slot = Number.isFinite(fi) ? fi : 0;
    }
    if (frameEl) frameEl.textContent = formatLabFrameCounter(slot, denom);
    if (gridEl) gridEl.dataset.overlay = frame.frame_key ? String(frame.frame_key) : "";
  }

  function updateReplayTruncationHud(frame, trackMetrics) {
    const hud = document.getElementById("lab-replay-truncation-hud");
    if (!hud) return;
    const dash = "—";
    const fm = frame && frame.metrics && typeof frame.metrics === "object" ? frame.metrics : {};
    const tm = trackMetrics && typeof trackMetrics === "object" ? trackMetrics : {};
    const parts = [];
    const diag =
      typeof tm.diagnostic_reason === "string" && tm.diagnostic_reason ? tm.diagnostic_reason : null;
    if (diag) {
      parts.push("diagnostic: " + diag);
    }
    const truncated = fm.replay_truncated === true || tm.replay_truncated === true;
    if (truncated) {
      const reason =
        typeof fm.truncation_reason === "string" && fm.truncation_reason
          ? fm.truncation_reason
          : typeof tm.truncation_reason === "string" && tm.truncation_reason
            ? tm.truncation_reason
            : "unknown";
      let text = "truncated: " + reason;
      const dropped = fm.dropped_frame_count != null ? fm.dropped_frame_count : tm.dropped_frame_count;
      if (dropped != null && Number.isFinite(Number(dropped))) {
        text += " · dropped " + String(dropped);
      }
      parts.push(text);
    }
    hud.textContent = parts.length ? parts.join(" · ") : dash;
  }

  function init() {
    const matrix = readJsonScript("lab-cell-overlay-matrix-data");
    let runs = readJsonScript("lab-runs-data");
    if (!Array.isArray(runs)) {
      runs = [];
    }
    const uiInitial = readJsonScript("lab-ui-initial-state");
    const manifestRaw = readJsonScript("lab-replay-manifest-data");
    let replayFrames = [];
    let replayTrackMetrics = {};
    const labReplayLoadState = {
      mode: "inline",
      status: "idle",
      frameCount: 0,
      fetchUrl: null,
      errorMessage: null,
      loadPromise: null,
    };

    if (manifestRaw && manifestRaw.mode === "lazy") {
      labReplayLoadState.mode = "lazy";
      labReplayLoadState.frameCount = Number(manifestRaw.frame_count) || 0;
      labReplayLoadState.fetchUrl =
        typeof manifestRaw.fetch_url === "string" ? manifestRaw.fetch_url : null;
      if (manifestRaw.replay_track_metrics && typeof manifestRaw.replay_track_metrics === "object") {
        replayTrackMetrics = manifestRaw.replay_track_metrics;
      }
      const preview =
        manifestRaw.preview_frame && typeof manifestRaw.preview_frame === "object"
          ? manifestRaw.preview_frame
          : null;
      replayFrames = preview ? [preview] : [];
      if (!labReplayLoadState.fetchUrl) {
        labReplayLoadState.status = "idle";
      }
    } else {
      const replayFramesRaw = readJsonScript("lab-replay-frames-data");
      replayFrames = Array.isArray(replayFramesRaw) ? replayFramesRaw : [];
      const trackMetricsRaw = readJsonScript("lab-replay-track-metrics-data");
      replayTrackMetrics =
        trackMetricsRaw && typeof trackMetricsRaw === "object" ? trackMetricsRaw : {};
    }
    const lazyReplayAwaitingCompose =
      labReplayLoadState.mode === "lazy" &&
      (labReplayLoadState.frameCount > 0 || Boolean(labReplayLoadState.fetchUrl));
    let hasServerReplay = replayFrames.length > 0 || lazyReplayAwaitingCompose;

    function renderLabReplayLoadStatus() {
      const el = document.getElementById("lab-replay-load-status");
      if (!el) return;
      if (labReplayLoadState.mode !== "lazy") {
        el.textContent = "";
        return;
      }
      if (labReplayLoadState.status === "loading") {
        el.textContent = "Replay: loading…";
      } else if (labReplayLoadState.status === "loaded") {
        el.textContent = "Replay: loaded " + String(labReplayLoadState.frameCount) + " frames";
      } else if (labReplayLoadState.status === "error") {
        el.textContent = "Replay: failed to load — retry";
      } else {
        el.textContent = "Replay: preview only";
      }
    }

    function applyLoadedLabReplayPayload(payload) {
      if (!payload || !Array.isArray(payload.frames)) return;
      if (payload.replay_track_metrics && typeof payload.replay_track_metrics === "object") {
        replayTrackMetrics = payload.replay_track_metrics;
      }
      const prevIndex = replayArrayIndex;
      replayFrames = payload.frames;
      hasServerReplay = replayFrames.length > 0;
      replayCleanup();
      replayCleanup = initializeServerReplaySurface(replayFrames);
      replayArrayIndex = Math.min(prevIndex, Math.max(0, replayFrames.length - 1));
      labReplayLoadState.status = "loaded";
      labReplayLoadState.frameCount = replayFrames.length;
      renderLabReplayLoadStatus();
      applyFrame();
    }

    function ensureLabReplayFramesLoaded(reason) {
      if (labReplayLoadState.mode !== "lazy" || labReplayLoadState.status === "loaded") {
        return Promise.resolve();
      }
      if (!labReplayLoadState.fetchUrl) {
        return Promise.resolve();
      }
      if (labReplayLoadState.loadPromise) {
        return labReplayLoadState.loadPromise;
      }
      labReplayLoadState.status = "loading";
      renderLabReplayLoadStatus();
      labReplayLoadState.loadPromise = fetch(labReplayLoadState.fetchUrl, {
        credentials: "same-origin",
        headers: { Accept: "application/json" },
      })
        .then(function (res) {
          return res.json().then(function (data) {
            return { ok: res.ok, data: data };
          });
        })
        .then(function (bundle) {
          if (!bundle.ok || !bundle.data || !Array.isArray(bundle.data.frames)) {
            throw new Error("lab_replay_load_failed");
          }
          applyLoadedLabReplayPayload(bundle.data);
        })
        .catch(function () {
          labReplayLoadState.status = "error";
          labReplayLoadState.errorMessage = "load_failed";
          renderLabReplayLoadStatus();
        })
        .finally(function () {
          labReplayLoadState.loadPromise = null;
        });
      return labReplayLoadState.loadPromise;
    }

    let initialFromServer = Object.assign(
      {},
      uiInitial && typeof uiInitial === "object" ? uiInitial : {},
    );

    const gridViewport = document.getElementById("lab-replay-grid-viewport");
    const cells = document.querySelectorAll("[data-lab-cell-index]");
    const phaseEl = document.getElementById("lab-replay-phase");
    const frameEl = document.getElementById("lab-frame-display");
    const gridEl = document.getElementById("lab-replay-grid");
    const scrubEl = document.getElementById("lab-timeline-scrub");
    const playBtn = document.getElementById("lab-timeline-play");
    const playIcon = document.getElementById("lab-timeline-play-icon");
    const pauseIcon = document.getElementById("lab-timeline-pause-icon");
    const modal = document.getElementById("lab-topology-modal");
    const openTopology = document.getElementById("lab-open-topology");
    const closeTopology = document.getElementById("lab-close-topology");
    const blueprintInput = document.getElementById("lab-blueprint-input");

    if (!gridEl) {
      return;
    }

    const gridStage = document.getElementById("lab-replay-grid-stage");
    const gridHudCoord = document.getElementById("lab-replay-grid-hud-coord");
    const gridHudRole = document.getElementById("lab-replay-grid-hud-role");

    let labViewportTransform = { zoom: 1, tx: 0, ty: 0 };
    let labPanState = null;
    /** Fitted cell edge (px) at zoom 1 for runtime replay; from ``applyReplayGridSizing``. */
    let replayFitBasePx = 20;
    /** Measured cell edge (px) at zoom 1 for demo matrix grid. */
    let demoBaseCellPxAtZoom1 = 20;

    let domCells;
    let baseClasses;

    function labViewportContentOffset(clientX, clientY) {
      if (!gridViewport) {
        return { vx: 0, vy: 0 };
      }
      const vr = gridViewport.getBoundingClientRect();
      const cs = window.getComputedStyle(gridViewport);
      const pl = parseFloat(cs.paddingLeft) || 0;
      const pt = parseFloat(cs.paddingTop) || 0;
      return {
        vx: clientX - vr.left - pl,
        vy: clientY - vr.top - pt,
      };
    }

    function labBaseCellAndGapPx() {
      if (hasServerReplay && replayLayout) {
        const cellPx = Math.max(4, Math.round(Number(replayFitBasePx)));
        const gapPx = Math.max(0, Math.round(cellPx * 0.2));
        return { cellPx: cellPx, gapPx: gapPx, gw: replayLayout.gridW, gh: replayLayout.gridH };
      }
      if (domCells && domCells.length) {
        const cellPx = Math.max(4, Math.round(Number(demoBaseCellPxAtZoom1)));
        const gapPx = Math.max(0, Math.round(cellPx * 0.2));
        return { cellPx: cellPx, gapPx: gapPx, gw: GRID_W, gh: GRID_H };
      }
      return null;
    }

    function labWorldPointFromClient(clientX, clientY) {
      const o = labViewportContentOffset(clientX, clientY);
      const t = labViewportTransform;
      const z = Number(t.zoom);
      const zoom = Number.isFinite(z) && z > 0 ? z : 1;
      return {
        wx: (o.vx - t.tx) / zoom,
        wy: (o.vy - t.ty) / zoom,
      };
    }

    function syncLabReplayStageSizeFromGrid() {
      if (!gridStage || !gridEl) {
        return;
      }
      const w = gridEl.offsetWidth;
      const h = gridEl.offsetHeight;
      if (w > 0 && h > 0) {
        gridStage.style.width = w + "px";
        gridStage.style.height = h + "px";
      }
    }

    function applyLabViewportTransform() {
      if (!gridStage) {
        return;
      }
      const t = labViewportTransform;
      const tx = snapToDevicePixel(t.tx);
      const ty = snapToDevicePixel(t.ty);
      const z = Number(t.zoom);
      const zoom = Number.isFinite(z) && z > 0 ? z : 1;
      gridStage.style.transformOrigin = "0 0";
      gridStage.style.transform =
        "translate(" + tx + "px, " + ty + "px) scale(" + zoom + ")";
    }

    function applyLabGridLayoutForZoom() {
      let cellPx = null;
      if (hasServerReplay && replayLayout) {
        const gw = replayLayout.gridW;
        const gh = replayLayout.gridH;
        cellPx = Math.max(4, Math.round(Number(replayFitBasePx)));
        gridEl.style.gridTemplateColumns = "repeat(" + gw + ", minmax(0, " + cellPx + "px))";
        gridEl.style.gridTemplateRows = "repeat(" + gh + ", minmax(0, " + cellPx + "px))";
      } else if (domCells && domCells.length) {
        cellPx = Math.max(4, Math.round(Number(demoBaseCellPxAtZoom1)));
        gridEl.style.gridTemplateColumns = "repeat(" + GRID_W + ", minmax(0, " + cellPx + "px))";
        gridEl.style.gridTemplateRows = "repeat(" + GRID_H + ", minmax(0, " + cellPx + "px))";
      }
      if (cellPx != null) {
        /* ~0.25rem at ~20px cells in CSS; gap scales with stage ``scale()`` via world cell size. */
        const gapPx = Math.max(0, Math.round(cellPx * 0.2));
        gridEl.style.setProperty("--lab-cell-gap", gapPx + "px");
        const radiusPx = Math.max(2, Math.min(7, Math.round(cellPx * 0.14)));
        gridEl.style.setProperty("--lab-cell-radius", radiusPx + "px");
      }
      syncLabReplayStageSizeFromGrid();
      applyLabViewportTransform();
    }

    function resetLabViewportTransform() {
      labViewportTransform = { zoom: 1, tx: 0, ty: 0 };
      applyLabGridLayoutForZoom();
    }

    let resolveCellIndex = function (cell) {
      if (!cell || typeof cell !== "object") return null;
      return cellIndexDemo(cell.x, cell.y);
    };
    let replayLayout = null;
    let resizeObserver = null;
    let replayResizeMode = null;
    let replayCleanup = function () {};

    function initializeServerReplaySurface(framesArr) {
      const neutralClass = LAB_CELL_BASE;
      replayLayout = computeReplayGridLayout(framesArr);
      const gw = replayLayout.gridW;
      const gh = replayLayout.gridH;
      gridEl.textContent = "";
      for (let i = 0; i < gw * gh; i++) {
        const div = document.createElement("div");
        div.setAttribute("data-lab-cell-index", String(i));
        div.className = neutralClass;
        gridEl.appendChild(div);
      }
      domCells = Array.prototype.slice.call(gridEl.querySelectorAll("[data-lab-cell-index]"));
      baseClasses = domCells.map(function (el) {
        return String(el.className || "");
      });

      resolveCellIndex = function (cell) {
        if (!cell || typeof cell !== "object") return null;
        const gw = replayLayout.gridW;
        const gh = replayLayout.gridH;
        const d = visualCol(cell.x);
        if (d == null) return null;
        const yi = Number(cell.y);
        if (!Number.isFinite(yi)) return null;
        const col = d - replayLayout.minD;
        const row = yi - replayLayout.minR;
        if (col < 0 || row < 0 || col >= gw || row >= gh) return null;
        return row * gw + col;
      };

      const padPx = 16;
      const minCell = 4;
      const maxCell = 36;

      function applyReplayGridSizing() {
        if (!gridViewport || !replayLayout) return;
        const cw = gridViewport.clientWidth - padPx * 2;
        const ch = gridViewport.clientHeight - padPx * 2;
        replayFitBasePx = Math.max(
          minCell,
          Math.min(maxCell, Math.floor(Math.min(cw / replayLayout.gridW, ch / replayLayout.gridH))),
        );
        applyLabGridLayoutForZoom();
      }

      function labReplayViewportOnWindowResize() {
        applyReplayGridSizing();
        resetLabViewportTransform();
      }

      applyReplayGridSizing();
      resizeObserver = null;
      replayResizeMode = null;
      if (gridViewport && typeof ResizeObserver !== "undefined") {
        /* Do not reset zoom/pan here: cell-pixel zoom changes inner layout and can
         * retrigger the observer; ``applyReplayGridSizing`` already calls
         * ``applyLabGridLayoutForZoom`` with the current ``labViewportTransform``. */
        resizeObserver = new ResizeObserver(function () {
          applyReplayGridSizing();
        });
        resizeObserver.observe(gridViewport);
        replayResizeMode = "observer";
      } else if (gridViewport) {
        window.addEventListener("resize", labReplayViewportOnWindowResize);
        replayResizeMode = "window";
      }

      return function cleanupReplaySurface() {
        if (replayResizeMode === "observer" && resizeObserver) {
          try {
            resizeObserver.disconnect();
          } catch (e) {
            /* ignore */
          }
          resizeObserver = null;
        }
        if (replayResizeMode === "window" && gridViewport) {
          window.removeEventListener("resize", labReplayViewportOnWindowResize);
        }
        replayResizeMode = null;
      };
    }

    if (hasServerReplay) {
      if (!matrix || !Array.isArray(matrix)) {
        return;
      }
      replayCleanup = initializeServerReplaySurface(replayFrames);
    } else {
      if (!matrix || !Array.isArray(matrix) || cells.length !== matrix.length) {
        return;
      }
      domCells = Array.prototype.slice.call(cells);
      baseClasses = domCells.map(function (el) {
        return String(el.className || "");
      });
      requestAnimationFrame(function () {
        const first = domCells[0];
        if (first && first.offsetWidth > 0) {
          demoBaseCellPxAtZoom1 = Math.max(4, first.offsetWidth);
        }
        applyLabGridLayoutForZoom();
      });
    }

    const rootEl = document.getElementById("lab-root");
    function syncLabDebugRotationClass() {
      if (!gridEl) return;
      if (labRotationDebugEnabled(rootEl)) {
        gridEl.classList.add("lab-debug-rotation");
      } else {
        gridEl.classList.remove("lab-debug-rotation");
      }
    }
    syncLabDebugRotationClass();
    const idSpriteRaw = readJsonScript("lab-identifier-sprite-paths-data");
    labIdentifierSpriteRelpaths =
      idSpriteRaw && typeof idSpriteRaw === "object" && !Array.isArray(idSpriteRaw)
        ? idSpriteRaw
        : {};
    labSpriteBaseUrl =
      rootEl && rootEl.dataset && rootEl.dataset.labSpriteBase != null
        ? String(rootEl.dataset.labSpriteBase)
        : "";
    const parseFrame = function (v, fallback) {
      const n = parseInt(String(v), 10);
      return Number.isNaN(n) ? fallback : n;
    };
    const datasetFrame = parseFrame(rootEl?.dataset.labInitialFrame, 0);
    let baselineFrame = parseFrame(initialFromServer.frame, datasetFrame);
    let baselineBlueprint =
      typeof initialFromServer.blueprintCode === "string"
        ? initialFromServer.blueprintCode
        : blueprintInput
          ? String(blueprintInput.value)
          : "";
    const baselineRun =
      initialFromServer.defaultRun && typeof initialFromServer.defaultRun === "object"
        ? initialFromServer.defaultRun
        : Array.isArray(runs) && runs.length
          ? runs[0]
          : null;
    const baselineRunId =
      typeof initialFromServer.defaultRunId === "string"
        ? initialFromServer.defaultRunId
        : baselineRun && baselineRun.id
          ? String(baselineRun.id)
          : null;

    function replaySlotForServerInitialFrame() {
      if (!hasServerReplay || !replayFrames.length) return 0;
      const wantFi = parseFrame(initialFromServer.frame, datasetFrame);
      let i = 0;
      for (; i < replayFrames.length; i++) {
        const fr = replayFrames[i];
        if (!fr || typeof fr !== "object") continue;
        const fi = Number(fr.frame_index);
        if (Number.isFinite(fi) && fi === wantFi) {
          return i;
        }
      }
      for (let j = 0; j < replayFrames.length; j++) {
        if (fullMapCellsFromFrame(replayFrames[j]).length) {
          return j;
        }
      }
      return 0;
    }

    let frame = baselineFrame;
    let isPlaying = false;
    let timerId = null;

    let replayArrayIndex = replaySlotForServerInitialFrame();

    function getMaxTimelineIndex() {
      if (hasServerReplay) {
        if (
          labReplayLoadState.mode === "lazy" &&
          labReplayLoadState.status !== "loaded" &&
          labReplayLoadState.frameCount > replayFrames.length
        ) {
          return Math.max(0, labReplayLoadState.frameCount - 1);
        }
        return Math.max(0, replayFrames.length - 1);
      }
      return TOTAL_FRAMES;
    }

    function getCurrentTimelineIndex() {
      return hasServerReplay ? replayArrayIndex : frame;
    }

    function setTimelineIndex(nextIndex, options) {
      const opt = options || {};
      const pause = opt.pause !== false;
      const max = getMaxTimelineIndex();
      const parsed = parseInt(String(nextIndex), 10);
      const raw = Number.isFinite(parsed) ? parsed : 0;
      const clamped = clampNumber(raw, 0, max);
      if (hasServerReplay) {
        replayArrayIndex = clamped;
      } else {
        frame = clamped;
      }
      if (pause) {
        setPlaying(false);
      }
      applyFrame();
    }

    function syncLabTimelineScrub() {
      if (!scrubEl) {
        return;
      }
      const max = getMaxTimelineIndex();
      scrubEl.min = "0";
      scrubEl.max = String(max);
      const noFrames =
        (hasServerReplay && replayFrames.length === 0) || (!hasServerReplay && TOTAL_FRAMES <= 0);
      scrubEl.disabled = noFrames;
      if (!noFrames) {
        const cur = getCurrentTimelineIndex();
        scrubEl.value = String(clampNumber(cur, 0, max));
      }
    }

    function getCurrentReplayFrame() {
      if (!hasServerReplay) return null;
      return replayFrames[replayArrayIndex] || null;
    }

    function buildRimDrawCtx() {
      if (!replayLayout) {
        return null;
      }
      const sizing = labBaseCellAndGapPx();
      if (!sizing) {
        return null;
      }
      return {
        layout: replayLayout,
        cellPx: sizing.cellPx,
        gapPx: sizing.gapPx,
      };
    }

    function applyFrame() {
      const rimDrawCtx = buildRimDrawCtx();
      if (hasServerReplay) {
        if (replayArrayIndex < 0) replayArrayIndex = 0;
        if (replayArrayIndex >= replayFrames.length) replayArrayIndex = replayFrames.length - 1;
        const fr = getCurrentReplayFrame();
        renderReplayFrame(
          fr,
          baseClasses,
          domCells,
          resolveCellIndex,
          replayFrames,
          replayTrackMetrics,
          rimDrawCtx,
        );
        updateFrameInfo(fr, replayFrames.length, phaseEl, frameEl, gridEl, replayArrayIndex);
        updateReplayTruncationHud(fr, replayTrackMetrics);
        const cycle = document.getElementById("lab-computation-cycle");
        if (cycle) {
          if (fr && fr.inspector && fr.inspector.source_frame_index != null) {
            cycle.textContent =
              "source_frame_index " + String(fr.inspector.source_frame_index);
          } else if (fr && fr.frame_key != null) {
            cycle.textContent = "frame_key " + String(fr.frame_key);
          } else {
            cycle.textContent = formatLabFrameCounter(replayArrayIndex, replayFrames.length);
          }
        }
        const hint = document.getElementById("lab-replay-footer-hint");
        if (hint) {
          if (fr && fr.description) {
            hint.textContent = String(fr.description);
          } else if (fr && fr.inspector) {
            const optEv = fr.inspector.optimization_event_type;
            const labEv = fr.inspector.lab_event_type;
            hint.textContent = optEv
              ? "optimization " + String(optEv)
              : labEv
                ? "lab " + String(labEv)
                : "replay frame";
          } else {
            hint.textContent =
              fr && fr.id != null
                ? "ReplayFrame id " + String(fr.id) + (fr.is_keyframe ? " · keyframe" : "")
                : "—";
          }
        }
        syncLabTimelineScrub();
        return;
      }

      if (frame < 0) frame = 0;
      if (frame > TOTAL_FRAMES) frame = TOTAL_FRAMES;
      const overlay = TOTAL_FRAMES <= 0 ? "candidates" : replayOverlayForFrame(frame);
      const oi = overlayIndex(overlay);
      for (let i = 0; i < domCells.length; i++) {
        const row = matrix[i];
        if (row && row[oi]) {
          domCells[i].className = row[oi];
        }
      }
      if (phaseEl) {
        phaseEl.textContent = TOTAL_FRAMES <= 0 ? "—" : replayPhaseForFrame(frame);
      }
      if (frameEl) frameEl.textContent = formatLabFrameCounter(frame, TOTAL_FRAMES);
      if (gridEl) gridEl.dataset.overlay = overlay;
      const cycle = document.getElementById("lab-computation-cycle");
      if (cycle) cycle.textContent = "computation_cycle #" + String(frame);
      syncLabTimelineScrub();
    }

    function setPlaying(next) {
      let wantPlay = next;
      const cap = hasServerReplay ? replayFrames.length : TOTAL_FRAMES;
      if (wantPlay && cap <= 0) {
        wantPlay = false;
      }
      if (wantPlay) {
        if (hasServerReplay) {
          replayArrayIndex = 0;
        } else {
          frame = 0;
        }
      }
      isPlaying = wantPlay;
      if (timerId !== null) {
        window.clearInterval(timerId);
        timerId = null;
      }
      if (isPlaying && cap > 0) {
        timerId = window.setInterval(function () {
          if (hasServerReplay) {
            if (replayArrayIndex >= replayFrames.length - 1) {
              replayArrayIndex = Math.max(0, replayFrames.length - 1);
              applyFrame();
              setPlaying(false);
              return;
            }
            replayArrayIndex += 1;
          } else {
            if (frame >= TOTAL_FRAMES) {
              frame = TOTAL_FRAMES;
              applyFrame();
              setPlaying(false);
              return;
            }
            frame += 1;
          }
          applyFrame();
        }, 220);
      }
      if (playIcon && pauseIcon) {
        playIcon.classList.toggle("hidden", isPlaying);
        pauseIcon.classList.toggle("hidden", !isPlaying);
      }
    }

    function closeTopologyModal() {
      if (!modal) return;
      modal.classList.add("hidden");
      modal.classList.remove("flex");
    }

    function applyRunSelectionHighlight(runId) {
      const wanted = runId != null ? String(runId) : null;
      document.querySelectorAll("[data-lab-run-id]").forEach(function (b) {
        const bid = b.getAttribute("data-lab-run-id");
        const run = (runs || []).find(function (r) {
          return r && String(r.id) === bid;
        });
        b.className = evolutionRunButtonClasses(run, wanted != null && bid === wanted);
      });
    }

    function runDetailStatusLabel(run) {
      if (!run || typeof run !== "object") return "—";
      if (run.status === "failed" || run.validation_passed === false) {
        return "validation failed";
      }
      const diagnosticText = diagnosticT2ShortfallStatusText(run);
      if (diagnosticText) return diagnosticText;
      const passCapableText = passCapableReferenceStatusText(run);
      if (passCapableText) return passCapableText;
      if (runCapacityFailed(run)) {
        return capacityFailedStatusText(run);
      }
      if (run.status === "completed" || run.run_success === true) {
        return "completed";
      }
      return run.status != null ? String(run.status) : "—";
    }

    function labUiDash() {
      return "—";
    }

    /** Map persisted issue_code enum values to gettext msgids (never show raw snake_case). */
    function formatLabIssueCodeLabel(code, run) {
      if (code == null || code === "") {
        return labUiDash();
      }
      const key = String(code);
      const tt =
        run && run.throughput_target && typeof run.throughput_target === "object"
          ? run.throughput_target
          : null;
      let diagnosticSuffix = "";
      if (run && isDiagnosticCanonRun(run)) {
        diagnosticSuffix =
          typeof shapezUiT === "function"
            ? shapezUiT(" (expected on diagnostic canon)")
            : " (expected on diagnostic canon)";
      } else if (
        run &&
        key === "throughput_target_shortfall" &&
        resolveRttpOpsSlugClass(run) === RTTP_OPS_SLUG_CLASS_PASS_CAPABLE
      ) {
        diagnosticSuffix =
          typeof shapezUiT === "function"
            ? shapezUiT(" (regression on pass-capable slug)")
            : " (regression on pass-capable slug)";
      }
      if (key === "throughput_target_shortfall" && tt) {
        const dash = labUiDash();
        const shortfall = tt.throughput_shortfall_per_min;
        if (shortfall != null && shortfall !== dash) {
          const perMinLabel = typeof shapezUiT === "function" ? shapezUiT("/min") : "/min";
          const shortLabel = typeof shapezUiT === "function" ? shapezUiT("Short by") : "Short by";
          return shortLabel + " " + formatCompactNumber(shortfall) + perMinLabel + diagnosticSuffix;
        }
      }
      const msgidByCode = {
        throughput_target_shortfall: "throughput target shortfall",
        rttp_validation_failed: "Validation failed",
      };
      const msgid = msgidByCode[key] || key;
      const base = typeof shapezUiT === "function" ? shapezUiT(msgid) : msgid;
      return key === "throughput_target_shortfall" ? base + diagnosticSuffix : base;
    }

    function formatCompactNumber(value) {
      const dash = labUiDash();
      if (value == null || value === "" || value === dash) return dash;
      const n = Number.parseFloat(String(value));
      if (!Number.isFinite(n)) return String(value);
      return Math.round(n).toLocaleString();
    }

    function formatOutputUnitShort(unit) {
      const dash = labUiDash();
      if (unit == null || unit === "" || unit === dash) return "";
      const u = String(unit);
      if (u === "shapes_per_min") return "shapes/min";
      if (u === "L_per_min") return "L/min";
      return u.replace(/_/g, "/");
    }

    function formatThroughputDetail(value, unit) {
      const dash = labUiDash();
      const num = formatCompactNumber(value);
      if (num === dash) return dash;
      const shortUnit = formatOutputUnitShort(unit);
      return shortUnit ? num + " " + shortUnit : num;
    }

    function buildRunListSubtitle(run) {
      const dash = labUiDash();
      if (!run || typeof run !== "object") return dash;
      const cap = run.capacity && typeof run.capacity === "object" ? run.capacity : {};
      const rec =
        run.reconstruction && typeof run.reconstruction === "object" ? run.reconstruction : {};
      const rttp = run.rttp && typeof run.rttp === "object" ? run.rttp : {};
      const primaryKind =
        cap.primary_resource_kind != null && cap.primary_resource_kind !== dash
          ? String(cap.primary_resource_kind)
          : "shape";
      const theor =
        primaryKind === "fluid"
          ? formatCompactNumber(cap.fluid_max_throughput_per_min)
          : formatCompactNumber(cap.shape_max_throughput_per_min);
      const committed = rttp.confirmed_count != null ? String(rttp.confirmed_count) : dash;
      const fieldCells =
        rec.field_cell_count != null && rec.field_cell_count !== dash
          ? String(rec.field_cell_count)
          : dash;
      const theorPart =
        theor !== dash ? theor + "/min " + (typeof shapezUiT === "function" ? shapezUiT("theor.") : "theor.") : dash;
      const committedPart =
        committed !== dash
          ? committed + " " + (typeof shapezUiT === "function" ? shapezUiT("committed") : "committed")
          : dash;
      const cellsPart =
        fieldCells !== dash
          ? fieldCells + " " + (typeof shapezUiT === "function" ? shapezUiT("cells") : "cells")
          : dash;
      return theorPart + " | " + committedPart + " | " + cellsPart;
    }

    function layerOutcomeBadgeClass(outcome) {
      if (outcome === "completed") {
        return "text-emerald-400 border-emerald-800/80";
      }
      if (outcome === "failed") {
        return "text-rose-400 border-rose-800/80";
      }
      if (outcome === "skipped_budget") {
        return "text-amber-400 border-amber-800/80";
      }
      return "text-slate-500 border-slate-700";
    }

    function formatLayerOutcomeLabel(outcome) {
      const dash = labUiDash();
      if (outcome == null || outcome === "" || outcome === dash) {
        return dash;
      }
      const key = String(outcome);
      const msgidByOutcome = {
        completed: "completed",
        failed: "failed",
        skipped_budget: "skipped (budget)",
        pending: "pending",
      };
      const msgid = msgidByOutcome[key] || key.replace(/_/g, " ");
      return typeof shapezUiT === "function" ? shapezUiT(msgid) : msgid;
    }

    function renderLabLayerSummaries(run) {
      const root = document.getElementById("lab-layer-summaries");
      const stackEl = document.getElementById("lab-detail-stack-status");
      const dash = labUiDash();
      if (stackEl) {
        const stackStatus =
          run && run.stack_run_status != null && run.stack_run_status !== dash
            ? String(run.stack_run_status)
            : "";
        if (stackStatus) {
          stackEl.textContent = "stack: " + stackStatus;
          stackEl.classList.remove("hidden");
        } else {
          stackEl.textContent = "";
          stackEl.classList.add("hidden");
        }
      }
      if (!root) return;
      root.replaceChildren();
      if (!run || !Array.isArray(run.layer_summaries) || !run.layer_summaries.length) {
        const empty = document.createElement("p");
        empty.id = "lab-layer-summaries-placeholder";
        empty.className = "text-sm text-slate-500";
        empty.textContent = dash;
        root.appendChild(empty);
        return;
      }
      run.layer_summaries.forEach(function (layer) {
        if (!layer || typeof layer !== "object") return;
        const card = document.createElement("article");
        card.className = "rounded-xl border border-slate-800 bg-slate-900/80 p-3";
        card.setAttribute("role", "listitem");
        if (layer.layer_slug) {
          card.setAttribute("data-lab-layer-slug", String(layer.layer_slug));
        }

        const head = document.createElement("div");
        head.className = "flex items-start justify-between gap-2";

        const titleWrap = document.createElement("div");
        titleWrap.className = "min-w-0";
        const title = document.createElement("h3");
        title.className = "text-sm font-medium text-slate-100";
        const layerIndex = layer.layer_index != null ? String(layer.layer_index) : "?";
        const layerTitle = layer.title != null ? String(layer.title) : dash;
        title.textContent = "L" + layerIndex + " · " + layerTitle;
        titleWrap.appendChild(title);
        if (layer.layer_slug) {
          const slugLine = document.createElement("p");
          slugLine.className = "mt-0.5 truncate font-mono text-xs text-slate-500";
          slugLine.textContent = String(layer.layer_slug);
          titleWrap.appendChild(slugLine);
        }

        const badge = document.createElement("span");
        const outcome = layer.outcome != null ? String(layer.outcome) : dash;
        badge.className =
          "shrink-0 rounded-md border px-2 py-0.5 text-xs font-medium " +
          layerOutcomeBadgeClass(outcome);
        badge.textContent = formatLayerOutcomeLabel(outcome);

        head.appendChild(titleWrap);
        head.appendChild(badge);
        card.appendChild(head);

        const highlights = Array.isArray(layer.highlights) ? layer.highlights : [];
        const dl = document.createElement("dl");
        dl.className = "mt-2 space-y-1 text-sm";
        highlights.forEach(function (row) {
          if (!row || typeof row !== "object") return;
          let val = row.value != null ? String(row.value) : dash;
          if (row.label === "First issue" && val !== dash) {
            val = formatLabIssueCodeLabel(val, run);
          }
          if (val === dash) return;
          const line = document.createElement("div");
          line.className = "flex justify-between gap-3 text-slate-400";
          const dt = document.createElement("dt");
          dt.className = "min-w-0 truncate";
          dt.textContent = row.label != null ? String(row.label) : "";
          const dd = document.createElement("dd");
          dd.className = "shrink-0 text-right text-slate-100";
          dd.textContent = val;
          line.appendChild(dt);
          line.appendChild(dd);
          dl.appendChild(line);
        });
        if (dl.childElementCount > 0) {
          card.appendChild(dl);
        }
        root.appendChild(card);
      });
    }

    function setRunDetail(run) {
      const dash = labUiDash();
      if (!run) {
        const title = document.getElementById("lab-detail-run-id");
        if (title) title.textContent = dash;
        const statusEl = document.getElementById("lab-detail-status");
        if (statusEl) statusEl.textContent = dash;
        updateOpsSlugBadge(null);
        renderLabLayerSummaries(null);
        return;
      }
      const statusEl = document.getElementById("lab-detail-status");
      if (statusEl) statusEl.textContent = runDetailStatusLabel(run);
      updateOpsSlugBadge(run);
      const title = document.getElementById("lab-detail-run-id");
      if (title) {
        title.textContent = run.id != null ? "Run #" + String(run.id) : dash;
      }
      renderLabLayerSummaries(run);
    }

    function evolutionRunButtonClasses(run, selected) {
      const failed = run && (run.status === "failed" || run.validation_passed === false);
      const partial = run && !failed && runCapacityFailed(run);
      if (selected) {
        if (failed) {
          return "w-full rounded-xl border p-3 text-left transition border-rose-500/80 bg-rose-950/40";
        }
        if (partial) {
          return "w-full rounded-xl border p-3 text-left transition border-amber-500/80 bg-amber-950/40";
        }
        return "w-full rounded-xl border p-3 text-left transition border-cyan-500 bg-cyan-500/10";
      }
      if (failed) {
        return "w-full rounded-xl border p-3 text-left transition border-rose-800/80 bg-rose-950/20 hover:border-rose-700";
      }
      if (partial) {
        return "w-full rounded-xl border p-3 text-left transition border-amber-800/80 bg-amber-950/20 hover:border-amber-700";
      }
      return "w-full rounded-xl border p-3 text-left transition border-slate-800 bg-slate-900 hover:border-slate-700";
    }

    function renderEvolutionRunsList(selectedRunId) {
      const list = document.getElementById("lab-evolution-runs-list");
      if (!list) return;
      list.innerHTML = "";
      if (!runs.length) {
        const empty = document.createElement("p");
        empty.className = "text-sm text-slate-500";
        empty.textContent = "No runs";
        list.appendChild(empty);
        return;
      }
      const selected =
        selectedRunId != null ? String(selectedRunId) : runs[0] && runs[0].id ? String(runs[0].id) : null;
      runs.forEach(function (run) {
        if (!run || run.id == null) return;
        const rid = String(run.id);
        const failed = run.status === "failed" || run.validation_passed === false;
        const partial = !failed && runCapacityFailed(run);
        const btn = document.createElement("button");
        btn.type = "button";
        btn.setAttribute("data-lab-run-id", rid);
        btn.className = evolutionRunButtonClasses(run, selected === rid);
        const headlineLabel = failed
          ? "validation failed"
          : partial
            ? "capacity failed (" +
              String(run.rttp && run.rttp.confirmed_count != null ? run.rttp.confirmed_count : "—") +
              "/" +
              String(run.target_miner_bundle_count) +
              ")"
            : "Run #" + rid;
        const passCapableBadge = shouldShowPassCapableBadge(run) ? passCapableBadgeHtml() : "";
        btn.innerHTML =
          '<div class="flex items-center justify-between gap-2">' +
          '<div class="flex flex-wrap items-center gap-2 font-medium">' +
          "<span>Run #" +
          rid +
          "</span>" +
          passCapableBadge +
          "</div>" +
          '<div class="text-sm ' +
          (failed ? "text-rose-300" : partial ? "text-amber-300" : "text-cyan-300") +
          '">' +
          headlineLabel +
          "</div>" +
          "</div>" +
          '<div class="mt-2 text-xs text-slate-400 lab-run-list-subtitle">' +
          buildRunListSubtitle(run) +
          "</div>";
        if (run.first_issue_code) {
          const issue = document.createElement("p");
          issue.className = "mt-2 truncate text-xs text-rose-300/90";
          const issueLabel = formatLabIssueCodeLabel(run.first_issue_code, run);
          issue.title = issueLabel;
          issue.textContent = issueLabel;
          btn.appendChild(issue);
        }
        btn.addEventListener("click", function () {
          applyRunSelectionHighlight(rid);
          setRunDetail(run);
        });
        list.appendChild(btn);
      });
    }

    function upsertRunSummary(runSummary) {
      if (!runSummary || typeof runSummary !== "object" || runSummary.id == null) {
        return;
      }
      const id = String(runSummary.id);
      runs = [runSummary].concat(
        (runs || []).filter(function (r) {
          return r && String(r.id) !== id;
        }),
      );
      renderEvolutionRunsList(id);
      applyRunSelectionHighlight(id);
      setRunDetail(runSummary);
    }

    function resetToInitial() {
      setPlaying(false);
      if (hasServerReplay) {
        replayArrayIndex = replaySlotForServerInitialFrame();
      } else {
        frame = baselineFrame;
      }
      closeTopologyModal();
      closeCellDetailModal();
      if (blueprintInput) blueprintInput.value = baselineBlueprint;
      applyRunSelectionHighlight(baselineRunId);
      setRunDetail(baselineRun);
      applyFrame();
    }

    const resetMapBtn = document.getElementById("lab-header-reset");
    resetMapBtn?.addEventListener("click", function () {
      const resetUrl =
        rootEl && rootEl.dataset && rootEl.dataset.labResetMapUrl
          ? String(rootEl.dataset.labResetMapUrl)
          : "";
      if (!resetUrl) {
        replayRunFeedback = { error_code: "save_project_first" };
        renderReplayRunStatus(replayRunFeedback);
        return;
      }
      if (resetMapBtn.disabled) {
        return;
      }
      const confirmed = window.confirm(
        "Reset map to inspection baseline? Runtime solver data in the database will be removed.",
      );
      if (!confirmed) {
        return;
      }
      resetMapBtn.disabled = true;
      replayRunFeedback = { running: true, reset: true };
      renderReplayRunStatus(replayRunFeedback);
      fetch(resetUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "X-CSRFToken": labCsrfToken(),
        },
      })
        .then(function (res) {
          return res
            .json()
            .catch(function () {
              return { ok: false };
            })
            .then(function (data) {
              return { res: res, data: data };
            });
        })
        .then(function (bundle) {
          const res = bundle.res;
          const data = bundle.data || {};
          if (!res.ok || data.ok === false || data.replay_ok === false) {
            replayRunFeedback = {
              error_code:
                typeof data.error_code === "string" ? data.error_code : "reset_failed",
            };
            renderReplayRunStatus(replayRunFeedback);
            return;
          }
          replayRunFeedback = null;
          renderReplayRunStatus(replayRunFeedback);
          window.location.assign(window.location.pathname);
        })
        .catch(function () {
          replayRunFeedback = { error_code: "network_error" };
          renderReplayRunStatus(replayRunFeedback);
        })
        .finally(function () {
          syncLabActionButtons();
        });
    });
    syncLabActionButtons();

    document.getElementById("lab-timeline-prev")?.addEventListener("click", function () {
      ensureLabReplayFramesLoaded("prev").then(function () {
        if (labReplayLoadState.status === "error") return;
        if (hasServerReplay) {
          replayArrayIndex = Math.max(0, replayArrayIndex - 1);
        } else {
          frame = Math.max(0, frame - 1);
        }
        applyFrame();
      });
    });

    playBtn?.addEventListener("click", function () {
      ensureLabReplayFramesLoaded("play").then(function () {
        if (labReplayLoadState.status === "error") return;
        const cap = hasServerReplay ? replayFrames.length : TOTAL_FRAMES;
        if (cap <= 0) return;
        setPlaying(!isPlaying);
        applyFrame();
      });
    });

    document.getElementById("lab-timeline-next")?.addEventListener("click", function () {
      ensureLabReplayFramesLoaded("next").then(function () {
        if (labReplayLoadState.status === "error") return;
        if (hasServerReplay) {
          replayArrayIndex = Math.min(replayFrames.length - 1, replayArrayIndex + 1);
        } else {
          frame = Math.min(TOTAL_FRAMES, frame + 1);
        }
        applyFrame();
      });
    });

    if (scrubEl) {
      scrubEl.addEventListener("pointerdown", function (event) {
        event.stopPropagation();
        setPlaying(false);
      });
      scrubEl.addEventListener("input", function () {
        ensureLabReplayFramesLoaded("scrub").then(function () {
          if (labReplayLoadState.status === "error") return;
          setTimelineIndex(scrubEl.value, { pause: true });
        });
      });
    }

    const rimToggleEl = document.getElementById("lab-terrain-rim-highlight-toggle");
    if (rimToggleEl) {
      try {
        const storedRim = window.localStorage.getItem(LAB_TERRAIN_RIM_STORAGE_KEY);
        if (storedRim === "0") {
          rimToggleEl.checked = false;
        } else if (storedRim === "1") {
          rimToggleEl.checked = true;
        }
      } catch (_rimErr) {
        /* ignore */
      }
      rimToggleEl.addEventListener("change", function () {
        persistTerrainRimHighlightEnabled(rimToggleEl.checked);
        applyFrame();
      });
    }

    const patternToggleEl = document.getElementById("lab-pattern-bundle-highlight-toggle");
    if (patternToggleEl) {
      try {
        const storedPattern = window.localStorage.getItem(LAB_PATTERN_BUNDLE_STORAGE_KEY);
        if (storedPattern === "0") {
          patternToggleEl.checked = false;
        } else if (storedPattern === "1") {
          patternToggleEl.checked = true;
        }
      } catch (_patternErr) {
        /* ignore */
      }
      patternToggleEl.addEventListener("change", function () {
        persistPatternBundleHighlightEnabled(patternToggleEl.checked);
        applyFrame();
      });
    }

    openTopology?.addEventListener("click", function () {
      modal?.classList.remove("hidden");
      modal?.classList.add("flex");
    });
    closeTopology?.addEventListener("click", function () {
      closeTopologyModal();
    });
    modal?.addEventListener("click", function (ev) {
      if (ev.target === modal) {
        closeTopologyModal();
      }
    });

    function labProjectSlugFromRedirect(redirectUrl) {
      if (!redirectUrl) {
        return "";
      }
      try {
        const u = new URL(redirectUrl, window.location.origin);
        const m = u.pathname.match(/\/asteroid-miner-layout\/p\/([^/]+)\/?/);
        return m ? decodeURIComponent(m[1]) : "";
      } catch {
        return "";
      }
    }

    function syncLabProjectEndpoints(payload) {
      if (!rootEl || !payload || typeof payload !== "object") {
        return;
      }
      let slug =
        typeof payload.project_slug === "string" ? payload.project_slug.trim() : "";
      let runUrl =
        typeof payload.run_solver_url === "string" ? payload.run_solver_url.trim() : "";
      if (!slug && typeof payload.redirect === "string") {
        slug = labProjectSlugFromRedirect(payload.redirect);
      }
      if (slug) {
        rootEl.dataset.labProjectSlug = slug;
      }
      if (runUrl) {
        rootEl.dataset.labRunSolverUrl = runUrl;
      }
      const resetUrl =
        typeof payload.reset_map_url === "string" ? payload.reset_map_url.trim() : "";
      if (resetUrl) {
        rootEl.dataset.labResetMapUrl = resetUrl;
      }
      syncLabActionButtons();
    }

    function syncLabActionButtons() {
      const runUrl =
        rootEl && rootEl.dataset && rootEl.dataset.labRunSolverUrl
          ? String(rootEl.dataset.labRunSolverUrl)
          : "";
      const resetUrl =
        rootEl && rootEl.dataset && rootEl.dataset.labResetMapUrl
          ? String(rootEl.dataset.labResetMapUrl)
          : "";
      const runBtn = document.getElementById("lab-header-run");
      const resetBtn = document.getElementById("lab-header-reset");
      if (runBtn) {
        runBtn.disabled = !runUrl;
        runBtn.classList.toggle("opacity-50", !runUrl);
        runBtn.classList.toggle("cursor-not-allowed", !runUrl);
      }
      if (resetBtn) {
        resetBtn.disabled = !resetUrl;
        resetBtn.classList.toggle("opacity-50", !resetUrl);
        resetBtn.classList.toggle("cursor-not-allowed", !resetUrl);
      }
    }

    function replaceLabReplayPayload(payload, opts) {
      if (!payload || typeof payload !== "object") return;
      syncLabProjectEndpoints(payload);
      const redirectTo = typeof payload.redirect === "string" ? payload.redirect : "";
      if (blueprintInput && typeof payload.blueprint_code === "string") {
        blueprintInput.value = payload.blueprint_code;
        baselineBlueprint = payload.blueprint_code;
      }
      if (payload.lab_ui_initial && typeof payload.lab_ui_initial === "object") {
        Object.assign(initialFromServer, payload.lab_ui_initial);
      }
      if (rootEl && payload.lab_ui_initial && typeof payload.lab_ui_initial === "object") {
        const tid = payload.lab_ui_initial.replayTrackId;
        rootEl.dataset.labReplayTrackId = tid != null ? String(tid) : "";
      }
      baselineFrame = parseFrame(initialFromServer.frame, datasetFrame);
      const lazy = payload.lab_replay;
      if (lazy && lazy.mode === "lazy") {
        if (payload.replay_track_metrics && typeof payload.replay_track_metrics === "object") {
          replayTrackMetrics = payload.replay_track_metrics;
        }
        labReplayLoadState.mode = "lazy";
        labReplayLoadState.status = "idle";
        labReplayLoadState.frameCount = Number(lazy.frame_count) || 0;
        labReplayLoadState.fetchUrl = typeof lazy.fetch_url === "string" ? lazy.fetch_url : null;
        labReplayLoadState.errorMessage = null;
        labReplayLoadState.loadPromise = null;
        const preview =
          lazy.preview_frame && typeof lazy.preview_frame === "object" ? lazy.preview_frame : null;
        replayFrames = preview ? [preview] : [];
        hasServerReplay = replayFrames.length > 0;
        if (!hasServerReplay) {
          window.location.assign(redirectTo || window.location.href);
          return;
        }
        replayCleanup();
        replayCleanup = initializeServerReplaySurface(replayFrames);
        replayArrayIndex = 0;
        setPlaying(false);
        renderLabReplayLoadStatus();
        applyFrame();
        return;
      }
      labReplayLoadState.mode = "inline";
      labReplayLoadState.status = "idle";
      labReplayLoadState.loadPromise = null;
      renderLabReplayLoadStatus();
      const next = Array.isArray(payload.lab_replay_frames_json) ? payload.lab_replay_frames_json : [];
      replayFrames = next;
      if (payload.replay_track_metrics && typeof payload.replay_track_metrics === "object") {
        replayTrackMetrics = payload.replay_track_metrics;
      }
      hasServerReplay = replayFrames.length > 0;
      if (!hasServerReplay) {
        window.location.assign(redirectTo || window.location.href);
        return;
      }
      replayCleanup();
      replayCleanup = initializeServerReplaySurface(replayFrames);
      resetLabViewportTransform();
      const seekLast =
        opts && typeof opts === "object" && opts.seekLastFrame === true;
      replayArrayIndex = seekLast
        ? Math.max(0, replayFrames.length - 1)
        : replaySlotForServerInitialFrame();
      setPlaying(false);
      applyFrame();
    }

    function syncProjectSlugHiddenFromRedirect(form, redirectUrl) {
      if (!form || !redirectUrl) return;
      try {
        const u = new URL(redirectUrl, window.location.origin);
        const m = u.pathname.match(/\/asteroid-miner-layout\/p\/([^/]+)\/?/);
        if (!m) return;
        const slug = decodeURIComponent(m[1]);
        let hi = form.querySelector('input[name="project_slug"]');
        if (!hi) {
          hi = document.createElement("input");
          hi.type = "hidden";
          hi.name = "project_slug";
          form.appendChild(hi);
        }
        hi.value = slug;
      } catch {
        /* ignore */
      }
    }

    const importForm = document.getElementById("lab-import-project-form");
    if (importForm) {
      importForm.addEventListener("submit", function (ev) {
        ev.preventDefault();
        const fd = new FormData(importForm);
        fetch(importForm.action, {
          method: "POST",
          body: fd,
          credentials: "same-origin",
          headers: { Accept: "application/json" },
        })
          .then(function (res) {
            return res
              .json()
              .catch(function () {
                return { ok: false };
              })
              .then(function (data) {
                return { res: res, data: data };
              });
          })
          .then(function (bundle) {
            const res = bundle.res;
            const data = bundle.data;
            if (!res.ok || !data || data.ok === false) {
              if (data && data.redirect) {
                window.location.assign(data.redirect);
              } else {
                window.location.reload();
              }
              return;
            }
            syncLabProjectEndpoints(data);
            if (data.in_place) {
              replaceLabReplayPayload(data);
              return;
            }
            if (data.redirect) {
              if (typeof history.pushState === "function") {
                try {
                  history.pushState(null, "", data.redirect);
                  syncProjectSlugHiddenFromRedirect(importForm, data.redirect);
                  syncLabProjectEndpoints(data);
                } catch {
                  window.location.assign(data.redirect);
                  return;
                }
              } else {
                window.location.assign(data.redirect);
                return;
              }
            }
            replaceLabReplayPayload(data);
          })
          .catch(function () {
            importForm.submit();
          });
      });
    }

    function domIndexToWorldXY(domIdx) {
      if (!hasServerReplay || !replayLayout) {
        return null;
      }
      const gw = replayLayout.gridW;
      const i = Number(domIdx);
      if (!Number.isFinite(i) || i < 0) {
        return null;
      }
      const col = i % gw;
      const row = Math.floor(i / gw);
      const d = col + replayLayout.minD;
      const y = row + replayLayout.minR;
      const xWorld = d < 0 ? d : d + 1;
      return { x: xWorld, y: y };
    }

    function findLabCellFromPoint(clientX, clientY) {
      const w = labWorldPointFromClient(clientX, clientY);
      const dims = labBaseCellAndGapPx();
      if (!dims || !domCells || !domCells.length) {
        return null;
      }
      const cellPx = dims.cellPx;
      const gapPx = dims.gapPx;
      const gw = dims.gw;
      const gh = dims.gh;
      const stride = cellPx + gapPx;
      let x = 0;
      let col = -1;
      for (let c = 0; c < gw; c++) {
        if (w.wx >= x && w.wx < x + cellPx) {
          col = c;
          break;
        }
        x += stride;
      }
      if (col < 0) {
        return null;
      }
      let y = 0;
      let row = -1;
      for (let r = 0; r < gh; r++) {
        if (w.wy >= y && w.wy < y + cellPx) {
          row = r;
          break;
        }
        y += stride;
      }
      if (row < 0) {
        return null;
      }
      const idx = row * gw + col;
      if (idx < 0 || idx >= domCells.length) {
        return null;
      }
      return domCells[idx] || null;
    }

    function updateLabGridHudEmpty() {
      if (gridHudCoord) {
        gridHudCoord.textContent = "—";
      }
      if (gridHudRole) {
        gridHudRole.textContent = "—";
      }
    }

    function getLabCellDisplayIslandCoord(cellEl) {
      const indexText = cellEl && cellEl.getAttribute ? cellEl.getAttribute("data-lab-cell-index") : null;
      const idx = Number.parseInt(indexText || "", 10);
      if (!Number.isFinite(idx)) {
        return "—";
      }
      if (hasServerReplay && replayLayout) {
        const coord = domIndexToWorldXY(idx);
        if (!coord) {
          return "—";
        }
        return "(" + coord.x + ", " + coord.y + ")";
      }
      const demoX = idx % GRID_W;
      const demoY = Math.floor(idx / GRID_W);
      return "(" + demoX + ", " + demoY + ")";
    }

    function getLabCellDisplayRole(cellEl) {
      if (!cellEl) {
        return "—";
      }
      const ov = cellEl.getAttribute("data-overlay-role");
      if (ov != null && ov !== "") {
        return ov;
      }
      const ck = cellEl.getAttribute("data-cell-kind");
      if (ck != null && ck !== "") {
        return ck;
      }
      const tt = cellEl.getAttribute("data-tile-type");
      if (tt != null && tt !== "") {
        return tt;
      }
      return "—";
    }

    function updateLabGridHudFromPoint(clientX, clientY) {
      const cellEl = findLabCellFromPoint(clientX, clientY);
      if (!cellEl || !gridEl.contains(cellEl)) {
        updateLabGridHudEmpty();
        return;
      }
      if (gridHudCoord) {
        gridHudCoord.textContent = getLabCellDisplayIslandCoord(cellEl);
      }
      if (gridHudRole) {
        gridHudRole.textContent = getLabCellDisplayRole(cellEl);
      }
    }

    function handleLabViewportWheel(event) {
      if (!gridViewport || !gridStage) {
        return;
      }
      event.preventDefault();
      const o = labViewportContentOffset(event.clientX, event.clientY);
      const vx = o.vx;
      const vy = o.vy;
      const oldZoom = labViewportTransform.zoom;
      const zoomFactor = event.deltaY < 0 ? 1.12 : 1 / 1.12;
      const nextZoom = clampNumber(oldZoom * zoomFactor, LAB_VIEWPORT_MIN_SCALE, LAB_VIEWPORT_MAX_SCALE);
      if (nextZoom === oldZoom) {
        updateLabGridHudFromPoint(event.clientX, event.clientY);
        return;
      }
      const z0 = oldZoom;
      const z1 = nextZoom;
      const tx0 = labViewportTransform.tx;
      const ty0 = labViewportTransform.ty;
      labViewportTransform.zoom = nextZoom;
      labViewportTransform.tx = vx - (z1 / z0) * (vx - tx0);
      labViewportTransform.ty = vy - (z1 / z0) * (vy - ty0);
      applyLabViewportTransform();
      updateLabGridHudFromPoint(event.clientX, event.clientY);
    }

    function labPointerShouldStartViewportPan(event) {
      if (!gridViewport || event.button !== 0) {
        return false;
      }
      const t = event.target;
      if (!(t instanceof Element)) {
        return false;
      }
      if (t.closest("#lab-timeline-controls, #lab-timeline-scrub")) {
        return false;
      }
      if (t.closest("input, button, select, textarea, a, label")) {
        return false;
      }
      return true;
    }

    function endLabViewportPan(event) {
      if (!labPanState || labPanState.pointerId !== event.pointerId) {
        return;
      }
      if (
        labPanState.dragging &&
        typeof gridViewport.releasePointerCapture === "function" &&
        typeof gridViewport.hasPointerCapture === "function" &&
        gridViewport.hasPointerCapture(event.pointerId)
      ) {
        gridViewport.releasePointerCapture(event.pointerId);
      }
      labPanState = null;
    }

    function handleLabViewportPointerDown(event) {
      if (!labPointerShouldStartViewportPan(event)) {
        return;
      }
      labPanState = {
        pointerId: event.pointerId,
        startClientX: event.clientX,
        startClientY: event.clientY,
        startTx: labViewportTransform.tx,
        startTy: labViewportTransform.ty,
        dragging: false,
      };
    }

    function handleLabViewportPointerMove(event) {
      updateLabGridHudFromPoint(event.clientX, event.clientY);
      if (!labPanState || labPanState.pointerId !== event.pointerId) {
        return;
      }
      const dx = event.clientX - labPanState.startClientX;
      const dy = event.clientY - labPanState.startClientY;
      const distance = Math.hypot(dx, dy);
      if (!labPanState.dragging) {
        if (distance < LAB_VIEWPORT_DRAG_THRESHOLD_PX) {
          return;
        }
        labPanState.dragging = true;
        gridViewport.setPointerCapture(event.pointerId);
      }
      event.preventDefault();
      labViewportTransform.tx = labPanState.startTx + dx;
      labViewportTransform.ty = labPanState.startTy + dy;
      applyLabViewportTransform();
    }

    function handleLabViewportPointerUp(event) {
      endLabViewportPan(event);
    }

    function handleLabViewportPointerLeave(event) {
      updateLabGridHudEmpty();
      endLabViewportPan(event);
    }

    function bindLabViewportInteractions() {
      if (labViewportInteractionsBound || !gridViewport) {
        return;
      }
      labViewportInteractionsBound = true;
      function preventLabViewportSelectDrag(ev) {
        ev.preventDefault();
      }
      gridViewport.addEventListener("dragstart", preventLabViewportSelectDrag);
      gridViewport.addEventListener("selectstart", preventLabViewportSelectDrag);
      if (gridStage) {
        gridStage.addEventListener("dragstart", preventLabViewportSelectDrag);
        gridStage.addEventListener("selectstart", preventLabViewportSelectDrag);
      }
      if (gridEl) {
        gridEl.addEventListener("dragstart", preventLabViewportSelectDrag);
        gridEl.addEventListener("selectstart", preventLabViewportSelectDrag);
      }
      gridViewport.addEventListener("wheel", handleLabViewportWheel, { passive: false });
      gridViewport.addEventListener("pointerdown", handleLabViewportPointerDown);
      gridViewport.addEventListener("pointermove", handleLabViewportPointerMove);
      gridViewport.addEventListener("pointerup", handleLabViewportPointerUp);
      gridViewport.addEventListener("pointercancel", handleLabViewportPointerUp);
      gridViewport.addEventListener("pointerleave", handleLabViewportPointerLeave);
    }

    function labCsrfToken() {
      const mc = document.querySelector("[name=csrfmiddlewaretoken]");
      if (mc && mc.value) {
        return mc.value;
      }
      return getCookie("csrftoken") || "";
    }

    let replayRunFeedback = null;
    renderReplayRunStatus(replayRunFeedback);

    function labReplayFetchUrlForRun(projectSlug, runId) {
      if (!projectSlug || runId == null) {
        return "";
      }
      return (
        "/asteroid-miner-layout/p/" +
        encodeURIComponent(String(projectSlug)) +
        "/solver-runs/" +
        encodeURIComponent(String(runId)) +
        "/lab-replay/"
      );
    }

    function applyCompletedSolverStatus(statusData) {
      replayRunFeedback = {
        solver_run_id: statusData.solver_run_id,
        validation_passed: statusData.validation_passed,
        run_summary: statusData.run_summary || null,
      };
      renderReplayRunStatus(replayRunFeedback);
      if (statusData.run_summary) {
        upsertRunSummary(statusData.run_summary);
      }
      const slug =
        rootEl && rootEl.dataset && rootEl.dataset.labProjectSlug
          ? String(rootEl.dataset.labProjectSlug)
          : "";
      const replayUrl = labReplayFetchUrlForRun(slug, statusData.solver_run_id);
      if (!replayUrl) {
        return;
      }
      fetch(replayUrl, {
        method: "GET",
        credentials: "same-origin",
        headers: { Accept: "application/json" },
      })
        .then(function (res) {
          return res
            .json()
            .catch(function () {
              return { ok: false };
            })
            .then(function (replayPayload) {
              return { res: res, replayPayload: replayPayload };
            });
        })
        .then(function (bundle) {
          if (!bundle.res.ok || bundle.replayPayload.ok === false) {
            replayRunFeedback = { error_code: "replay_fetch_failed" };
            renderReplayRunStatus(replayRunFeedback);
            return;
          }
          const frames = Array.isArray(bundle.replayPayload.frames)
            ? bundle.replayPayload.frames
            : [];
          replaceLabReplayPayload(
            {
              ok: true,
              solver_run_id: statusData.solver_run_id,
              validation_passed: statusData.validation_passed,
              run_summary: statusData.run_summary || null,
              lab_replay_frames_json: frames,
              replay_track_metrics: bundle.replayPayload.replay_track_metrics || {},
            },
            { seekLastFrame: true }
          );
        })
        .catch(function () {
          replayRunFeedback = { error_code: "replay_fetch_failed" };
          renderReplayRunStatus(replayRunFeedback);
        });
    }

    function pollSolverRunStatus(statusUrl, onTerminal) {
      const pollIntervalMs = 1500;
      function tick() {
        fetch(statusUrl, {
          method: "GET",
          credentials: "same-origin",
          headers: { Accept: "application/json" },
        })
          .then(function (res) {
            return res
              .json()
              .catch(function () {
                return { ok: false };
              })
              .then(function (data) {
                return { res: res, data: data };
              });
          })
          .then(function (bundle) {
            const data = bundle.data || {};
            if (data.status === "running") {
              replayRunFeedback = { running: true, log_tail: data.log_tail || "" };
              renderReplayRunStatus(replayRunFeedback);
              window.setTimeout(tick, pollIntervalMs);
              return;
            }
            onTerminal(data, bundle.res);
          })
          .catch(function () {
            replayRunFeedback = { error_code: "network_error" };
            renderReplayRunStatus(replayRunFeedback);
          });
      }
      tick();
    }

    const runSolverBtn = document.getElementById("lab-header-run");
    runSolverBtn?.addEventListener("click", function () {
      const runUrl =
        rootEl && rootEl.dataset && rootEl.dataset.labRunSolverUrl
          ? String(rootEl.dataset.labRunSolverUrl)
          : "";
      if (!runUrl) {
        replayRunFeedback = { error_code: "save_project_first" };
        renderReplayRunStatus(replayRunFeedback);
        return;
      }
      if (runSolverBtn.disabled) {
        return;
      }
      runSolverBtn.disabled = true;
      replayRunFeedback = { running: true };
      renderReplayRunStatus(replayRunFeedback);
      const macroOnlyEl = document.getElementById("lab-macro-only-mode");
      const macroOnlyMode = Boolean(macroOnlyEl && macroOnlyEl.checked);
      const runSolverHeaders = {
        Accept: "application/json",
        "X-CSRFToken": labCsrfToken(),
      };
      const runSolverInit = {
        method: "POST",
        credentials: "same-origin",
        headers: runSolverHeaders,
      };
      const percentEl = document.getElementById("lab-throughput-target-percent");
      const postBody = {};
      if (percentEl) {
        const parsed = parseInt(String(percentEl.value), 10);
        if (!Number.isNaN(parsed)) {
          postBody.throughput_target_percent = parsed;
        }
      }
      if (macroOnlyMode) {
        postBody.macro_only_mode = true;
        postBody.rttp_record_replay = true;
      }
      if (Object.keys(postBody).length > 0) {
        runSolverHeaders["Content-Type"] = "application/json";
        runSolverInit.body = JSON.stringify(postBody);
      }
      fetch(runUrl, runSolverInit)
        .then(function (res) {
          return res
            .json()
            .catch(function () {
              return { ok: false };
            })
            .then(function (data) {
              return { res: res, data: data };
            });
        })
        .then(function (bundle) {
          const res = bundle.res;
          const data = bundle.data || {};
          if (res.status === 202 && typeof data.status_url === "string" && data.status_url) {
            pollSolverRunStatus(data.status_url, function (statusData, statusRes) {
              if (!statusRes.ok || statusData.ok === false) {
                replayRunFeedback = {
                  error_code:
                    typeof statusData.error_code === "string"
                      ? statusData.error_code
                      : "request_failed",
                };
                renderReplayRunStatus(replayRunFeedback);
                return;
              }
              if (statusData.status === "failed") {
                replayRunFeedback = {
                  error_code:
                    typeof statusData.error_code === "string"
                      ? statusData.error_code
                      : "solver_failed",
                  solver_run_id: statusData.solver_run_id,
                };
                renderReplayRunStatus(replayRunFeedback);
                if (statusData.run_summary) {
                  upsertRunSummary(statusData.run_summary);
                }
                return;
              }
              applyCompletedSolverStatus(statusData);
            });
            return;
          }
          if (!res.ok || data.ok === false) {
            replayRunFeedback = {
              error_code:
                typeof data.error_code === "string" ? data.error_code : "request_failed",
            };
            if (data.solver_run_id != null) {
              replayRunFeedback.solver_run_id = data.solver_run_id;
              replayRunFeedback.validation_passed = data.validation_passed;
            }
            renderReplayRunStatus(replayRunFeedback);
            if (data.run_summary) {
              upsertRunSummary(data.run_summary);
            }
            if (Array.isArray(data.lab_replay_frames_json)) {
              replaceLabReplayPayload(data);
            }
            return;
          }
          replayRunFeedback = {
            solver_run_id: data.solver_run_id,
            validation_passed: data.validation_passed,
            run_summary: data.run_summary || null,
            gene_template_source: data.gene_template_source || null,
          };
          renderReplayRunStatus(replayRunFeedback);
          if (data.run_summary) {
            upsertRunSummary(data.run_summary);
          }
          replaceLabReplayPayload(data, { seekLastFrame: true });
        })
        .catch(function () {
          replayRunFeedback = { error_code: "network_error" };
          renderReplayRunStatus(replayRunFeedback);
        })
        .finally(function () {
          runSolverBtn.disabled = false;
        });
    });

    const throughputSlider = document.getElementById("lab-throughput-target-percent");
    const throughputSliderLabel = document.getElementById("lab-throughput-target-percent-label");
    function syncThroughputTargetLabel() {
      if (!throughputSlider || !throughputSliderLabel) {
        return;
      }
      throughputSliderLabel.textContent = String(throughputSlider.value) + "%";
    }
    throughputSlider?.addEventListener("input", syncThroughputTargetLabel);
    syncThroughputTargetLabel();

    function labReplayFrameOrmId(fr) {
      if (!fr || typeof fr !== "object") {
        return null;
      }
      if (fr.id != null && fr.id !== "") {
        const legacy = parseInt(String(fr.id), 10);
        if (Number.isFinite(legacy)) {
          return legacy;
        }
      }
      const insp = fr.inspector;
      if (insp && typeof insp === "object" && insp.replay_frame_id != null) {
        const fromInsp = parseInt(String(insp.replay_frame_id), 10);
        if (Number.isFinite(fromInsp)) {
          return fromInsp;
        }
      }
      return null;
    }

    function setLabCellDetailUnavailableHint(message) {
      const hint = document.getElementById("lab-replay-footer-hint");
      if (hint) {
        hint.textContent = message;
      }
    }

    function labCellMatchesWorldXY(cell, x, y) {
      if (!cell || typeof cell !== "object") {
        return false;
      }
      const cx = Number(cell.x);
      const cy = Number(cell.y);
      return Number.isFinite(cx) && Number.isFinite(cy) && cx === x && cy === y;
    }

    function labTimelineWireCellToDetail(cell) {
      if (!cell || typeof cell !== "object") {
        return null;
      }
      const out = {
        x: cell.x,
        y: cell.y,
        rotation: cell.rotation != null ? cell.rotation : 0,
        cell_kind: cell.kind != null ? cell.kind : cell.cell_kind != null ? cell.cell_kind : "",
        transport_kind:
          cell.transport != null ? cell.transport : cell.transport_kind != null ? cell.transport_kind : "",
        tile_type:
          cell.tile_type != null
            ? String(cell.tile_type)
            : cell.sprite_identifier != null
              ? String(cell.sprite_identifier)
              : "",
      };
      if (cell.layer != null) {
        out.layer = cell.layer;
      }
      return out;
    }

    function labCellDetailLookupInMapView(mapView, x, y) {
      if (!mapView || typeof mapView !== "object") {
        return { cell: null, sources: {} };
      }
      const sources = {};
      const layers = [];
      const full = mapView.full_cells;
      if (Array.isArray(full)) {
        for (let i = 0; i < full.length; i++) {
          const c = full[i];
          if (labCellMatchesWorldXY(c, x, y)) {
            sources.map_view_full_cells = c;
            const mapped = labTimelineWireCellToDetail(c);
            if (mapped) {
              layers.push(mapped);
            }
          }
        }
      }
      const delta = mapView.cell_delta;
      if (Array.isArray(delta)) {
        for (let j = 0; j < delta.length; j++) {
          const d = delta[j];
          if (labCellMatchesWorldXY(d, x, y)) {
            sources.map_view_cell_delta = d;
            const mapped = labTimelineWireCellToDetail(d);
            if (mapped) {
              layers.push(mapped);
            }
          }
        }
      }
      const overlay = mapView.overlay_cells;
      if (Array.isArray(overlay)) {
        const matches = [];
        for (let k = 0; k < overlay.length; k++) {
          const o = overlay[k];
          if (labCellMatchesWorldXY(o, x, y)) {
            matches.push(o);
            const mapped = labTimelineWireCellToDetail(o);
            if (mapped) {
              layers.push(mapped);
            }
          }
        }
        if (matches.length) {
          sources.map_view_overlay_cells = matches.length === 1 ? matches[0] : matches;
        }
      }
      if (!layers.length) {
        return { cell: null, sources: sources };
      }
      const merged = {};
      for (let m = 0; m < layers.length; m++) {
        Object.assign(merged, layers[m]);
      }
      return { cell: merged, sources: sources };
    }

    function labCellDetailFromTimelineFrame(fr, x, y) {
      const lookup = labCellDetailLookupInMapView(fr.map_view, x, y);
      const payload = {
        ok: true,
        cell: lookup.cell,
        sources: lookup.sources,
        message: lookup.cell ? "" : "no_cell_at_xy",
        frame_index: fr.frame_index != null ? fr.frame_index : null,
      };
      if (fr.event_type != null) {
        payload.event_type = String(fr.event_type);
      }
      const insp = fr.inspector;
      if (insp && insp.optimization_event_type != null) {
        payload.optimization_event_type = String(insp.optimization_event_type);
      }
      if (lookup.sources.map_view_full_cells || lookup.sources.map_view_cell_delta) {
        payload.detail_source = "map_view_client";
      } else if (Object.keys(lookup.sources).length) {
        payload.detail_source = "map_view_overlay_client";
      }
      const mergedKind =
        lookup.cell && lookup.cell.cell_kind != null ? String(lookup.cell.cell_kind) : "";
      if (isL3PoolCandidateObservationFrame(fr) && isCandidateObservationOverlayKind(mergedKind)) {
        payload.observation_note = CANDIDATE_OBSERVATION_TITLE;
      }
      return payload;
    }

    const LAB_CELL_DETAIL_KEY_ORDER = [
      "x",
      "y",
      "layer",
      "rotation",
      "cell_kind",
      "tile_type",
      "transport_kind",
    ];

    function labCellDetailIsSuppressedKey(key) {
      return String(key || "").startsWith("server_");
    }

    function labCellDetailEscapeHtml(s) {
      return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function labCellDetailOrderedKeys(obj) {
      const keys = Object.keys(obj || {});
      const seen = {};
      const out = [];
      for (let i = 0; i < LAB_CELL_DETAIL_KEY_ORDER.length; i++) {
        const k = LAB_CELL_DETAIL_KEY_ORDER[i];
        if (keys.indexOf(k) >= 0) {
          out.push(k);
          seen[k] = true;
        }
      }
      const rest = keys
        .filter(function (k) {
          return !seen[k] && !labCellDetailIsSuppressedKey(k);
        })
        .sort();
      return out.concat(rest);
    }

    function labCellDetailFormatValue(v) {
      if (v === null || v === undefined) {
        return '<span class="text-slate-500">—</span>';
      }
      if (typeof v === "number" || typeof v === "boolean") {
        return labCellDetailEscapeHtml(String(v));
      }
      if (typeof v === "string") {
        const t = v.trim();
        if (t === "") {
          return '<span class="text-slate-500">(empty)</span>';
        }
        return labCellDetailEscapeHtml(v);
      }
      const json = JSON.stringify(v);
      if (json.length <= 140) {
        return (
          '<span class="wrap-break-word font-mono text-[11px]">' + labCellDetailEscapeHtml(json) + "</span>"
        );
      }
      return (
        '<details class="mt-1">' +
        '<summary class="cursor-pointer text-xs text-slate-400">JSON (' +
        String(json.length) +
        " chars)</summary>" +
        '<pre class="mt-2 max-h-40 overflow-auto whitespace-pre-wrap wrap-break-word rounded border border-slate-800 bg-slate-900/80 p-2 font-mono text-[11px] leading-snug">' +
        labCellDetailEscapeHtml(JSON.stringify(v, null, 2)) +
        "</pre></details>"
      );
    }

    function labCellDetailKvTableHtml(obj) {
      if (!obj || typeof obj !== "object") {
        return '<p class="text-slate-500">—</p>';
      }
      const keys = labCellDetailOrderedKeys(obj);
      if (!keys.length) {
        return '<p class="text-slate-500">(empty object)</p>';
      }
      let rows = "";
      for (let i = 0; i < keys.length; i++) {
        const k = keys[i];
        let dd = labCellDetailFormatValue(obj[k]);
        if (k === "rotation") {
          dd +=
            ' <span class="whitespace-nowrap text-xs text-slate-500">(East=0, clockwise)</span>';
        }
        rows +=
          '<div class="grid grid-cols-[minmax(0,auto)_1fr] gap-x-3 border-b border-slate-800/80 py-2 last:border-b-0">' +
          '<dt class="shrink-0 font-mono text-xs text-slate-500">' +
          labCellDetailEscapeHtml(k) +
          "</dt>" +
          '<dd class="min-w-0 text-slate-200">' +
          dd +
          "</dd></div>";
      }
      return '<dl class="rounded-lg border border-slate-800/80 px-3">' + rows + "</dl>";
    }

    function labCellDetailFrameMetaHtml(data) {
      const parts = [];
      if (data.frame_index !== undefined && data.frame_index !== null) {
        parts.push("frame_index: " + String(data.frame_index));
      }
      if (data.frame_key !== undefined && data.frame_key !== null && String(data.frame_key) !== "") {
        parts.push("frame_key: " + String(data.frame_key));
      }
      if (!parts.length) {
        return "";
      }
      return (
        '<p class="mb-3 font-mono text-[11px] leading-relaxed text-slate-500">' +
        labCellDetailEscapeHtml(parts.join(" · ")) +
        "</p>"
      );
    }

    function labCellDetailSourceBlockHtml(sourceKey, val, mergedCell) {
      if (
        sourceKey === "full_map" &&
        mergedCell &&
        typeof mergedCell === "object" &&
        val &&
        typeof val === "object" &&
        !Array.isArray(val) &&
        JSON.stringify(val) === JSON.stringify(mergedCell)
      ) {
        return (
          '<div class="mb-4 last:mb-0">' +
          '<h4 class="mb-1 font-mono text-xs text-slate-400">' +
          labCellDetailEscapeHtml(sourceKey) +
          "</h4>" +
          '<p class="text-xs text-slate-500">Same as merged cell above.</p></div>'
        );
      }
      const head =
        '<h4 class="mb-2 font-mono text-xs text-slate-400">' +
        labCellDetailEscapeHtml(sourceKey) +
        "</h4>";
      if (val !== null && val !== undefined && typeof val === "object" && !Array.isArray(val)) {
        return '<div class="mb-4 last:mb-0">' + head + labCellDetailKvTableHtml(val) + "</div>";
      }
      return (
        '<div class="mb-4 last:mb-0">' +
        head +
        '<div class="text-slate-200">' +
        labCellDetailFormatValue(val) +
        "</div></div>"
      );
    }

    function labCellDetailRenderSuccess(cellDetailEl, data) {
      const cell = data.cell;
      const sources = data.sources || {};
      const frameMeta = labCellDetailFrameMetaHtml(data);
      const observationBanner =
        data.observation_note && String(data.observation_note) !== ""
          ? '<p class="mb-2 rounded border border-amber-500/40 bg-amber-950/30 px-2 py-1 text-xs text-amber-200">' +
            labCellDetailEscapeHtml(String(data.observation_note)) +
            "</p>"
          : "";
      let html = '<div class="space-y-6">';
      if (cell && typeof cell === "object") {
        html +=
          '<section class="space-y-2">' +
          '<h3 class="text-xs font-semibold uppercase tracking-wide text-slate-400">Merged cell</h3>' +
          observationBanner +
          frameMeta +
          labCellDetailKvTableHtml(cell) +
          "</section>";
      } else {
        const msg = data.message || "no_cell_at_xy";
        html +=
          '<section class="space-y-2">' +
          '<p class="text-slate-300">' +
          labCellDetailEscapeHtml(msg) +
          "</p>" +
          frameMeta +
          "</section>";
      }
      const srcKeys = Object.keys(sources);
      if (srcKeys.length) {
        let srcHtml = "";
        for (let s = 0; s < srcKeys.length; s++) {
          srcHtml += labCellDetailSourceBlockHtml(srcKeys[s], sources[srcKeys[s]], cell);
        }
        html +=
          '<section class="space-y-3">' +
          '<h3 class="text-xs font-semibold uppercase tracking-wide text-slate-400">Sources</h3>' +
          srcHtml +
          "</section>";
      }
      html += "</div>";
      cellDetailEl.innerHTML = html;
    }

    const cellDetailModal = document.getElementById("lab-cell-detail-modal");
    const cellDetailBody = document.getElementById("lab-cell-detail-body");
    const closeCellDetailBtn = document.getElementById("lab-close-cell-detail");

    function closeCellDetailModal() {
      if (!cellDetailModal) {
        return;
      }
      cellDetailModal.classList.add("hidden");
      cellDetailModal.classList.remove("flex");
    }

    function openCellDetailModal() {
      if (!cellDetailModal) {
        return;
      }
      cellDetailModal.classList.remove("hidden");
      cellDetailModal.classList.add("flex");
    }

    if (gridEl && cellDetailModal) {
      gridEl.addEventListener("click", function (ev) {
        if (!hasServerReplay || !replayLayout) {
          return;
        }
        const hit = ev.target.closest("[data-lab-cell-index]");
        if (!hit || !gridEl.contains(hit)) {
          return;
        }
        const idx = parseInt(hit.getAttribute("data-lab-cell-index") || "", 10);
        const xy = domIndexToWorldXY(idx);
        if (!xy) {
          return;
        }
        const fr = getCurrentReplayFrame();
        if (!fr) {
          setLabCellDetailUnavailableHint("cell detail unavailable (no replay frame)");
          return;
        }
        const frameOrmId = labReplayFrameOrmId(fr);
        const cellUrl = rootEl && rootEl.dataset ? rootEl.dataset.labReplayCellUrl || "" : "";
        const trackIdStr =
          rootEl && rootEl.dataset && rootEl.dataset.labReplayTrackId != null
            ? String(rootEl.dataset.labReplayTrackId)
            : "";
        if (!cellUrl || !trackIdStr) {
          setLabCellDetailUnavailableHint("cell detail unavailable (replay track not configured)");
          return;
        }
        if (frameOrmId == null) {
          openCellDetailModal();
          if (cellDetailBody) {
            labCellDetailRenderSuccess(cellDetailBody, labCellDetailFromTimelineFrame(fr, xy.x, xy.y));
          }
          setLabCellDetailUnavailableHint("cell detail from map_view (no persisted ReplayFrame)");
          return;
        }
        const projectSlug =
          rootEl && rootEl.dataset && rootEl.dataset.labProjectSlug != null
            ? String(rootEl.dataset.labProjectSlug)
            : "";
        const payload = {
          replay_frame_id: frameOrmId,
          replay_track_id: parseInt(trackIdStr, 10),
          x: xy.x,
          y: xy.y,
        };
        if (projectSlug) {
          payload.project_slug = projectSlug;
        }
        if (cellDetailBody) {
          cellDetailBody.textContent = "Loading…";
        }
        openCellDetailModal();
        fetch(cellUrl, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": labCsrfToken(),
          },
          body: JSON.stringify(payload),
        })
          .then(function (res) {
            return res
              .json()
              .catch(function () {
                return { ok: false, error: "bad_json" };
              })
              .then(function (data) {
                return { res: res, data: data };
              });
          })
          .then(function (bundle) {
            const res = bundle.res;
            const data = bundle.data;
            if (!cellDetailBody) {
              return;
            }
            if (!res.ok || !data || data.ok !== true) {
              const err = data && data.error ? String(data.error) : "request_failed " + res.status;
              cellDetailBody.textContent = err;
              return;
            }
            labCellDetailRenderSuccess(cellDetailBody, data);
          })
          .catch(function () {
            if (cellDetailBody) {
              cellDetailBody.textContent = "Network error.";
            }
          });
      });
    }

    closeCellDetailBtn?.addEventListener("click", function () {
      closeCellDetailModal();
    });
    cellDetailModal?.addEventListener("click", function (ev) {
      if (ev.target === cellDetailModal) {
        closeCellDetailModal();
      }
    });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && cellDetailModal && !cellDetailModal.classList.contains("hidden")) {
        closeCellDetailModal();
      }
    });

    window.AsteroidLabReplay = {
      getCurrentReplayFrame: getCurrentReplayFrame,
      renderReplayFrame: function (fr) {
        renderReplayFrame(
          fr,
          baseClasses,
          domCells,
          resolveCellIndex,
          replayFrames,
          replayTrackMetrics,
          buildRimDrawCtx(),
        );
      },
      renderCellOverlay: function (ov) {
        resetGridBase(domCells, baseClasses);
        renderCellOverlay(baseClasses, domCells, ov, resolveCellIndex);
      },
      applyEquipmentBundleHighlight: function (ov) {
        maybeApplyEquipmentBundleGroupVisualsFromOverlay(ov, domCells, resolveCellIndex);
      },
      renderDecodedCells: function (list) {
        resetGridBase(domCells, baseClasses);
        renderDecodedCells(baseClasses, domCells, list, resolveCellIndex);
      },
      renderExistingLayoutOverlay: function (ov) {
        resetGridBase(domCells, baseClasses);
        renderExistingLayoutOverlay(baseClasses, domCells, ov, resolveCellIndex);
      },
      updateFrameInfo: function (fr) {
        updateFrameInfo(
          fr,
          hasServerReplay ? replayFrames.length : 0,
          phaseEl,
          frameEl,
          gridEl,
          replayArrayIndex,
        );
      },
      collectOverlayPaintTargets: collectOverlayPaintTargets,
      visualCol: visualCol,
      rawXToDenseX: rawXToDenseX,
      replaceLabReplayPayload: replaceLabReplayPayload,
    };

    applyLabGridLayoutForZoom();
    updateLabGridHudEmpty();
    bindLabViewportInteractions();

    renderEvolutionRunsList(baselineRunId);
    setRunDetail(baselineRun);
    renderLabReplayLoadStatus();

    function needsLazyReplayComposeFetch() {
      if (labReplayLoadState.mode !== "lazy" || !labReplayLoadState.fetchUrl) {
        return false;
      }
      if (!replayFrames.length) {
        return true;
      }
      for (let i = 0; i < replayFrames.length; i++) {
        if (frameHasRenderableMap(replayFrames[i])) {
          return false;
        }
      }
      return true;
    }

    if (needsLazyReplayComposeFetch()) {
      ensureLabReplayFramesLoaded("init");
    } else {
      applyFrame();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
