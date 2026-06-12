/**
 * LabPaintLayers resolver + per-frame effective-cell wire index.
 * Parity authority: tests/support/lab_replay_paint_plan.py (keep in sync).
 */
(function (global) {
  "use strict";

  var BACKGROUND_FILL = "rgb(2, 6, 23)";
  var VOID_FILL = "rgba(74, 4, 78, 0.72)";

  var VOID_TERRAIN_KINDS = { internal_void: 1, void: 1 };
  var TRANSPORT_KINDS = { space_belt: 1, space_pipe: 1 };
  var NONE_KINDS = { "": 1, none: 1 };

  var CANDIDATE_RING_STROKE = "rgba(244,114,182,0.9)";

  var DOM_CANDIDATE_MINER_RING = "lab-overlay-candidate-miner-ring relative";
  var DOM_CANDIDATE_MINER_FILL = "lab-overlay-candidate-miner relative";

  var CELL_KIND_STATIC_RELPATH = {
    asteroid_fluid_field: "AsteroidField_Fluid.svg",
    asteroid_shape_field: "AsteroidField_Shape.svg",
  };

  var CELL_KIND_TO_IDENTIFIER = {
    fluid_miner: "Layout_FluidMiner",
    fluid_miner_extension: "Layout_FluidMinerExtension",
    shape_miner: "Layout_ShapeMiner",
    shape_miner_extension: "Layout_ShapeMinerExtension",
    miner: "Layout_ShapeMiner",
    extension: "Layout_ShapeMinerExtension",
  };

  var SPRITE_TILE_TYPE_ALIASES = {
    Layout_ProMiner: "Layout_ShapeMiner",
    SpaceBelt_Left: "SpaceBelt_LeftTurn",
    SpacePipe_Left: "SpacePipe_LeftTurn",
    SpaceBelt_Right: "SpaceBelt_RightTurn",
    SpacePipe_Right: "SpacePipe_RightTurn",
  };

  function wireSection(view, key) {
    var section = view && view[key];
    if (!section || typeof section !== "object") {
      return {};
    }
    return Object.assign({}, section);
  }

  function kindStr(section, field) {
    var key = field != null ? field : "kind";
    var raw = section[key];
    if (raw == null) {
      return "";
    }
    return String(raw).trim();
  }

  function rotation(section) {
    var raw = section.rotation;
    if (raw == null) {
      return 0;
    }
    var rot = parseInt(String(raw), 10);
    return Number.isFinite(rot) ? rot : 0;
  }

  function spriteRelpathFromTileType(tileType) {
    var t = String(tileType || "").trim();
    if (!t) {
      return null;
    }
    t = SPRITE_TILE_TYPE_ALIASES[t] || t;
    if (t.indexOf("SpaceBelt_") === 0) {
      return "SpaceBelt/" + t + ".svg";
    }
    if (t.indexOf("SpacePipe_") === 0) {
      return "SpacePipe/" + t + ".svg";
    }
    if (t.indexOf("Layout_") === 0) {
      return "Miner/" + t + ".svg";
    }
    return null;
  }

  function candidateMinerOccupant(outputTransportKind, rot) {
    var rel =
      outputTransportKind === "space_pipe"
        ? "Miner/Layout_FluidMiner.svg"
        : "Miner/Layout_ShapeMiner.svg";
    return { rel: rel, rotation: rot };
  }

  function committedOccupantSprite(occupantKind, outputTransportKind) {
    if (occupantKind === "committed_miner") {
      var ident =
        outputTransportKind === "space_pipe" ? "Layout_FluidMiner" : "Layout_ShapeMiner";
      return spriteRelpathFromTileType(ident);
    }
    if (occupantKind === "extension") {
      var extIdent =
        outputTransportKind === "space_pipe"
          ? "Layout_FluidMinerExtension"
          : "Layout_ShapeMinerExtension";
      return spriteRelpathFromTileType(extIdent);
    }
    var mapped = CELL_KIND_TO_IDENTIFIER[occupantKind];
    if (mapped) {
      return spriteRelpathFromTileType(mapped);
    }
    return null;
  }

  function resolveOccupant(view) {
    var occupant = wireSection(view, "occupant");
    var output = wireSection(view, "output");
    var kind = kindStr(occupant);
    if (NONE_KINDS[kind]) {
      return { occupant: null, chrome: [] };
    }

    var rot = rotation(occupant);
    var outputTransportKind = kindStr(output, "transport_kind") || "none";
    var chrome = [];

    if (kind === "candidate_miner") {
      chrome.push({ kind: "candidate_ring", stroke_only: true });
      return { occupant: candidateMinerOccupant(outputTransportKind, rot), chrome: chrome };
    }

    var rel = committedOccupantSprite(kind, outputTransportKind);
    if (rel) {
      return { occupant: { rel: rel, rotation: rot }, chrome: chrome };
    }
    return { occupant: null, chrome: chrome };
  }

  function rotationFromOverlaySources(view) {
    var sources = view && view.sources;
    if (!sources || typeof sources !== "object") {
      return 0;
    }
    var overlays = sources.overlay_cells;
    if (!overlays) {
      return 0;
    }
    var rows = Array.isArray(overlays) ? overlays : [overlays];
    for (var i = 0; i < rows.length; i++) {
      var rot = rotation(rows[i]);
      if (rot) {
        return rot;
      }
    }
    return 0;
  }

  function resolveTransport(view, occupantKind) {
    if (occupantKind === "candidate_miner") {
      return null;
    }

    var transport = wireSection(view, "transport");
    var transportKind = kindStr(transport);
    if (!TRANSPORT_KINDS[transportKind]) {
      return null;
    }

    var tileId = transport.tile_id;
    if (!tileId || !String(tileId).trim()) {
      return null;
    }

    var rel = spriteRelpathFromTileType(String(tileId));
    if (!rel) {
      return null;
    }

    var occupant = wireSection(view, "occupant");
    var rot = rotation(occupant);
    if (NONE_KINDS[kindStr(occupant)]) {
      var overlayRot = rotationFromOverlaySources(view);
      if (overlayRot) {
        rot = overlayRot;
      }
    }
    return { rel: rel, rotation: rot };
  }

  function resolveTerrain(view, hasSprite) {
    var terrain = wireSection(view, "terrain");
    var kind = kindStr(terrain) || "empty";

    var staticRel = CELL_KIND_STATIC_RELPATH[kind];
    if (staticRel) {
      return { mode: "field_sprite", rel: staticRel };
    }

    if (VOID_TERRAIN_KINDS[kind]) {
      return { mode: "void_fill", fill: VOID_FILL };
    }

    if (!hasSprite) {
      return { mode: "background_fill", fill: BACKGROUND_FILL };
    }

    return null;
  }

  function labPaintLayersFromView(view) {
    var resolved = resolveOccupant(view);
    var occupant = resolved.occupant;
    var chrome = resolved.chrome;
    var occupantKind = kindStr(wireSection(view, "occupant")) || "none";
    var transport = resolveTransport(view, occupantKind);
    var hasSprite = occupant != null || transport != null;
    var terrain = resolveTerrain(view, hasSprite);

    if (
      terrain != null &&
      hasSprite &&
      terrain.mode === "background_fill"
    ) {
      terrain = null;
    }

    return {
      terrain: terrain,
      occupant: occupant,
      transport: transport,
      chrome: chrome,
    };
  }

  function rowInt(value, defaultVal) {
    if (defaultVal == null) {
      defaultVal = 0;
    }
    if (typeof value === "boolean") {
      return value ? 1 : 0;
    }
    if (typeof value === "number" && Number.isFinite(value)) {
      return Math.trunc(value);
    }
    if (typeof value === "string") {
      var parsed = parseInt(value, 10);
      return Number.isFinite(parsed) ? parsed : defaultVal;
    }
    return defaultVal;
  }

  function cellCoord(row) {
    return [rowInt(row.x), rowInt(row.y), rowInt(row.layer)];
  }

  function rowsAtCoord(rows, x, y, layer) {
    if (!rows || !rows.length) {
      return [];
    }
    var out = [];
    for (var i = 0; i < rows.length; i++) {
      var coord = cellCoord(rows[i]);
      if (coord[0] === x && coord[1] === y && coord[2] === layer) {
        out.push(rows[i]);
      }
    }
    return out;
  }

  function firstRowAtCoord(rows, x, y, layer) {
    var matches = rowsAtCoord(rows, x, y, layer);
    return matches.length ? matches[0] : null;
  }

  function cellOverlayJsonFromFrame(frame) {
    if (!frame || typeof frame !== "object") {
      return null;
    }
    var top = frame.cell_overlay_json;
    if (top && typeof top === "object") {
      return top;
    }
    var payload = frame.frame_payload;
    if (payload && typeof payload === "object" && payload.cell_overlay_json) {
      return payload.cell_overlay_json;
    }
    return null;
  }

  function pushOverlayCellList(out, rows) {
    if (!Array.isArray(rows)) {
      return;
    }
    for (var i = 0; i < rows.length; i++) {
      if (rows[i] && typeof rows[i] === "object") {
        out.push(Object.assign({}, rows[i]));
      }
    }
  }

  function overlayJsonRowsFromFrame(frame) {
    var overlay = cellOverlayJsonFromFrame(frame);
    if (!overlay) {
      return [];
    }
    var out = [];
    pushOverlayCellList(out, overlay.cells);
    pushOverlayCellList(out, overlay.equipment_cells);
    pushOverlayCellList(out, overlay.equipment);
    pushOverlayCellList(out, overlay.adjacent_transport);
    pushOverlayCellList(out, overlay.transport);
    return out;
  }

  function collectCoordUniverse(mapView, extraRows) {
    var coords = {};
    var keys = ["full_cells", "overlay_cells", "cell_delta"];
    for (var k = 0; k < keys.length; k++) {
      var rows = mapView[keys[k]];
      if (!rows || !Array.isArray(rows)) {
        continue;
      }
      for (var i = 0; i < rows.length; i++) {
        var row = rows[i];
        if (!row || typeof row !== "object") {
          continue;
        }
        var coord = cellCoord(row);
        var key = coord[0] + "," + coord[1] + "," + coord[2];
        coords[key] = coord;
      }
    }
    if (extraRows && extraRows.length) {
      for (var j = 0; j < extraRows.length; j++) {
        var extraRow = extraRows[j];
        if (!extraRow || typeof extraRow !== "object") {
          continue;
        }
        var extraCoord = cellCoord(extraRow);
        var extraKey = extraCoord[0] + "," + extraCoord[1] + "," + extraCoord[2];
        coords[extraKey] = extraCoord;
      }
    }
    return Object.keys(coords)
      .sort()
      .map(function (key) {
        return coords[key];
      });
  }

  function sanitizeCell(cell) {
    if (
      typeof LabReplayWireSanitize !== "undefined" &&
      LabReplayWireSanitize.sanitizeReplayWireCellForRead
    ) {
      return LabReplayWireSanitize.sanitizeReplayWireCellForRead(cell);
    }
    return cell;
  }

  function mergeCellView(options) {
    if (
      typeof LabEffectiveCellView !== "undefined" &&
      LabEffectiveCellView.mergeEffectiveCellView
    ) {
      return LabEffectiveCellView.mergeEffectiveCellView(options);
    }
    return null;
  }

  function keyForCell(x, y, layer) {
    if (
      typeof LabReplayWireSanitize !== "undefined" &&
      LabReplayWireSanitize.cellKey
    ) {
      return LabReplayWireSanitize.cellKey(x, y, layer);
    }
    if (layer != null && layer !== 0) {
      return String(layer) + ":" + String(x) + "," + String(y);
    }
    return String(x) + "," + String(y);
  }

  function buildEffectiveCellViewIndex(frame, options) {
    options = options || {};
    if (!frame || typeof frame !== "object") {
      return {};
    }

    var mapView = frame.map_view;
    if (!mapView || typeof mapView !== "object") {
      return {};
    }

    var fullRows = [];
    var overlayRows = [];
    var deltaRows = [];
    var fullSource = mapView.full_cells;
    var overlaySource = mapView.overlay_cells;
    var deltaSource = mapView.cell_delta;
    var i;

    if (Array.isArray(fullSource)) {
      for (i = 0; i < fullSource.length; i++) {
        if (fullSource[i] && typeof fullSource[i] === "object") {
          fullRows.push(Object.assign({}, fullSource[i]));
        }
      }
    }
    if (Array.isArray(overlaySource)) {
      for (i = 0; i < overlaySource.length; i++) {
        if (overlaySource[i] && typeof overlaySource[i] === "object") {
          overlayRows.push(Object.assign({}, overlaySource[i]));
        }
      }
    }
    if (Array.isArray(deltaSource)) {
      for (i = 0; i < deltaSource.length; i++) {
        if (deltaSource[i] && typeof deltaSource[i] === "object") {
          deltaRows.push(Object.assign({}, deltaSource[i]));
        }
      }
    }

    var overlayJsonRows = overlayJsonRowsFromFrame(frame);

    var frameIndex = null;
    if (frame.frame_index != null) {
      var fi = parseInt(String(frame.frame_index), 10);
      frameIndex = Number.isFinite(fi) ? fi : null;
    }

    var index = {};
    var universe = collectCoordUniverse(mapView, overlayJsonRows);
    for (i = 0; i < universe.length; i++) {
      var x = universe[i][0];
      var y = universe[i][1];
      var layer = universe[i][2];

      var fullCell = firstRowAtCoord(fullRows, x, y, layer);
      var deltaCell = firstRowAtCoord(deltaRows, x, y, layer);
      var overlayCells = rowsAtCoord(overlayRows, x, y, layer);
      var overlayJsonAtCoord = rowsAtCoord(overlayJsonRows, x, y, layer);
      for (var oj = 0; oj < overlayJsonAtCoord.length; oj++) {
        overlayCells.push(overlayJsonAtCoord[oj]);
      }
      if (!overlayCells.length) {
        overlayCells = null;
      }

      var sanitizedFull = fullCell ? sanitizeCell(fullCell) : null;
      var sanitizedDelta = deltaCell ? sanitizeCell(deltaCell) : null;
      var sanitizedOverlays = null;
      if (overlayCells) {
        sanitizedOverlays = [];
        for (var j = 0; j < overlayCells.length; j++) {
          sanitizedOverlays.push(sanitizeCell(overlayCells[j]));
        }
      }

      var wire = mergeCellView({
        x: x,
        y: y,
        frameIndex: frameIndex,
        fullCell: sanitizedFull,
        deltaCell: sanitizedDelta,
        overlayCells: sanitizedOverlays,
      });
      if (!wire) {
        continue;
      }
      index[keyForCell(x, y, layer)] = wire;
    }

    return index;
  }

  function isRgbaFill(value) {
    return typeof value === "string" && value.trim().toLowerCase().indexOf("rgba(") === 0;
  }

  function spritePlanEntry(gridIdx, rel, rot) {
    return { idx: gridIdx, rel: rel, rotation: rot };
  }

  function canvasPlanFromPaintLayers(layers, gridIdx) {
    if (gridIdx == null) {
      gridIdx = 0;
    }
    var sprites = [];

    var terrain = layers && layers.terrain;
    if (terrain && typeof terrain === "object" && terrain.mode === "field_sprite") {
      if (terrain.rel) {
        sprites.push(spritePlanEntry(gridIdx, String(terrain.rel), 0));
      }
    }

    var occupant = layers && layers.occupant;
    if (occupant && typeof occupant === "object" && occupant.rel) {
      sprites.push(spritePlanEntry(gridIdx, String(occupant.rel), rotation(occupant)));
    }

    var transport = layers && layers.transport;
    if (transport && typeof transport === "object" && transport.rel) {
      sprites.push(spritePlanEntry(gridIdx, String(transport.rel), rotation(transport)));
    }

    var overlays = [];
    var chrome = layers && layers.chrome;
    if (Array.isArray(chrome)) {
      for (var i = 0; i < chrome.length; i++) {
        var entry = chrome[i];
        if (!entry || typeof entry !== "object") {
          continue;
        }
        if (kindStr(entry) === "candidate_ring") {
          overlays.push({
            idx: gridIdx,
            kind: "candidate_ring",
            stroke: CANDIDATE_RING_STROKE,
            fill: null,
          });
        }
      }
    }

    if (sprites.length) {
      overlays = overlays.filter(function (overlay) {
        return !isRgbaFill(overlay.fill);
      });
    }

    return { sprites: sprites, overlays: overlays };
  }

  function layersHasDrawableSprite(layers) {
    if (layers.occupant && layers.occupant.rel) {
      return true;
    }
    if (layers.transport && layers.transport.rel) {
      return true;
    }
    if (layers.terrain && layers.terrain.mode === "field_sprite") {
      return true;
    }
    return false;
  }

  function indexHasSpriteCapableCells(index) {
    var keys = Object.keys(index);
    for (var i = 0; i < keys.length; i++) {
      if (layersHasDrawableSprite(labPaintLayersFromView(index[keys[i]]))) {
        return true;
      }
    }
    return false;
  }

  function filterIndexSpriteEntries(index) {
    var out = {};
    var keys = Object.keys(index);
    for (var i = 0; i < keys.length; i++) {
      var key = keys[i];
      if (layersHasDrawableSprite(labPaintLayersFromView(index[key]))) {
        out[key] = index[key];
      }
    }
    return out;
  }

  function mergeCarriedIndexKeys(carryIndex, currentIndex) {
    var merged = Object.assign({}, filterIndexSpriteEntries(carryIndex), currentIndex);
    return merged;
  }

  function lastFrameWithSpriteCapableCells(replayFrames, upToArrayIndex) {
    if (!replayFrames || !replayFrames.length) {
      return null;
    }
    var cap = Math.min(upToArrayIndex, replayFrames.length - 1);
    for (var i = cap; i >= 0; i--) {
      var fr = replayFrames[i];
      if (indexHasSpriteCapableCells(buildEffectiveCellViewIndex(fr))) {
        return fr;
      }
    }
    return null;
  }

  function buildEffectiveCellViewIndexWithCarry(frame, options) {
    options = options || {};
    var index = buildEffectiveCellViewIndex(frame);
    if (
      options.replayFrames &&
      options.hasServerReplay &&
      !indexHasSpriteCapableCells(index)
    ) {
      var replayArrayIndex =
        options.replayArrayIndex != null
          ? options.replayArrayIndex
          : options.replayFrames.length - 1;
      var layoutFrame = lastFrameWithSpriteCapableCells(
        options.replayFrames,
        replayArrayIndex
      );
      if (layoutFrame && layoutFrame !== frame) {
        index = mergeCarriedIndexKeys(
          buildEffectiveCellViewIndex(layoutFrame),
          index
        );
      }
    }
    return index;
  }

  function layersHaveSprite(layers) {
    if (!layers) {
      return false;
    }
    var occupant = layers.occupant;
    if (occupant && typeof occupant === "object" && occupant.rel) {
      return true;
    }
    var transport = layers.transport;
    if (transport && typeof transport === "object" && transport.rel) {
      return true;
    }
    return false;
  }

  function domPlanFromPaintLayers(layers, opts) {
    opts = opts || {};
    var overlayKind = opts.overlayKind != null ? String(opts.overlayKind) : "";

    var occupant = layers && layers.occupant;
    var chrome = layers && layers.chrome;
    var hasSprite = layersHaveSprite(layers);
    var hasCandidateRing = false;
    if (Array.isArray(chrome)) {
      for (var i = 0; i < chrome.length; i++) {
        var c = chrome[i];
        if (c && typeof c === "object" && kindStr(c) === "candidate_ring") {
          hasCandidateRing = true;
          break;
        }
      }
    }

    var spriteRel = null;
    var spriteRotation = 0;
    if (occupant && typeof occupant === "object" && occupant.rel) {
      spriteRel = String(occupant.rel);
      spriteRotation = rotation(occupant);
    }

    var toneClasses = "";
    if (hasCandidateRing) {
      toneClasses = hasSprite ? DOM_CANDIDATE_MINER_RING : DOM_CANDIDATE_MINER_FILL;
    } else if (overlayKind === "candidate_miner" && !hasSprite) {
      toneClasses = DOM_CANDIDATE_MINER_FILL;
    }

    return {
      toneClasses: toneClasses,
      spriteRel: spriteRel,
      spriteRotation: spriteRotation,
      candidateObservation: hasCandidateRing || overlayKind === "candidate_miner",
      skipFullFill: hasSprite,
    };
  }

  function overlayCellKindFromWire(cell) {
    if (!cell || typeof cell !== "object") {
      return "";
    }
    if (cell.cell_kind != null && String(cell.cell_kind) !== "") {
      return String(cell.cell_kind);
    }
    if (cell.kind != null && String(cell.kind) !== "") {
      return String(cell.kind);
    }
    return "";
  }

  function buildDomPlanResolverForFrame(frame, options) {
    if (!frame) {
      return function () {
        return null;
      };
    }
    options = options || {};
    var index = buildEffectiveCellViewIndexWithCarry(frame, options);
    return function resolveDomPlan(cell) {
      if (!cell) {
        return null;
      }
      var layer = cell.layer != null ? cell.layer : 0;
      var key = keyForCell(cell.x, cell.y, layer);
      var wire = index[key];
      if (!wire) {
        return null;
      }
      var layers = labPaintLayersFromView(wire);
      return domPlanFromPaintLayers(layers, {
        overlayKind: overlayCellKindFromWire(cell),
      });
    };
  }

  function coordFromWireOrKey(wire, cellKeyStr) {
    if (wire && wire.coord && typeof wire.coord === "object") {
      return wire.coord;
    }
    var layer = 0;
    var xy = cellKeyStr;
    var colonIdx = cellKeyStr.indexOf(":");
    if (colonIdx !== -1) {
      var parsedLayer = parseInt(cellKeyStr.slice(0, colonIdx), 10);
      layer = Number.isFinite(parsedLayer) ? parsedLayer : 0;
      xy = cellKeyStr.slice(colonIdx + 1);
    }
    var parts = xy.split(",");
    return {
      x: parseInt(parts[0], 10) || 0,
      y: parseInt(parts[1], 10) || 0,
      layer: layer,
    };
  }

  function cellKindFromEffectiveWire(wire) {
    var occupant = wireSection(wire, "occupant");
    var occKind = kindStr(occupant);
    if (occKind && occKind !== "none") {
      return occKind;
    }
    var transport = wireSection(wire, "transport");
    var transportKind = kindStr(transport);
    if (TRANSPORT_KINDS[transportKind]) {
      return transportKind;
    }
    var terrain = wireSection(wire, "terrain");
    return kindStr(terrain) || "empty";
  }

  function overlayRoleFromWireSources(wire) {
    var sources = wire && wire.sources;
    if (!sources || typeof sources !== "object") {
      return null;
    }
    var overlay = sources.overlay_cells;
    if (!overlay) {
      return null;
    }
    if (Array.isArray(overlay)) {
      for (var i = overlay.length - 1; i >= 0; i--) {
        var row = overlay[i];
        if (row && row.overlay_role != null && String(row.overlay_role) !== "") {
          return String(row.overlay_role);
        }
      }
      return null;
    }
    if (overlay.overlay_role != null && String(overlay.overlay_role) !== "") {
      return String(overlay.overlay_role);
    }
    return null;
  }

  function cellLikeFromEffectiveWire(wire) {
    var coord = coordFromWireOrKey(wire, "");
    var occupant = wireSection(wire, "occupant");
    var kind = cellKindFromEffectiveWire(wire);
    var cell = {
      x: coord.x,
      y: coord.y,
      layer: coord.layer,
      kind: kind,
      cell_kind: kind,
    };
    if (occupant.rotation != null) {
      cell.rotation = occupant.rotation;
    }
    var overlayRole = overlayRoleFromWireSources(wire);
    if (overlayRole) {
      cell.overlay_role = overlayRole;
    }
    return cell;
  }

  function buildCellByGridIndexFromFrame(frame, resolveCellIndex, options) {
    options = options || {};
    var map = new Map();
    if (!frame || typeof frame !== "object" || typeof resolveCellIndex !== "function") {
      return map;
    }
    var index = buildEffectiveCellViewIndexWithCarry(frame, options);
    var keys = Object.keys(index);
    for (var i = 0; i < keys.length; i++) {
      var cellKeyStr = keys[i];
      var wire = index[cellKeyStr];
      if (!wire) {
        continue;
      }
      var coord = coordFromWireOrKey(wire, cellKeyStr);
      var gridIdx = resolveCellIndex({
        x: coord.x,
        y: coord.y,
        layer: coord.layer,
      });
      if (gridIdx == null || gridIdx < 0) {
        continue;
      }
      map.set(gridIdx, cellLikeFromEffectiveWire(wire));
    }
    return map;
  }

  function buildLabPaintPlanFromFrame(frame, resolveCellIndex, options) {
    options = options || {};
    var index = buildEffectiveCellViewIndex(frame);

    // Layout carry: sparse current frame (no drawable sprites in its index) inherits
    // sprite-capable effective views from the nearest prior replay frame — mirrors
    // lastFrameWithSpriteCapableCells + layoutFrame staging in buildCanvasPaintPlan.
    if (
      options.replayFrames &&
      options.hasServerReplay &&
      !indexHasSpriteCapableCells(index)
    ) {
      var replayArrayIndex =
        options.replayArrayIndex != null ? options.replayArrayIndex : options.replayFrames.length - 1;
      var layoutFrame = lastFrameWithSpriteCapableCells(
        options.replayFrames,
        replayArrayIndex
      );
      if (layoutFrame && layoutFrame !== frame) {
        index = mergeCarriedIndexKeys(buildEffectiveCellViewIndex(layoutFrame), index);
      }
    }

    var sprites = [];
    var overlays = [];
    var cellKeys = Object.keys(index).sort();

    for (var i = 0; i < cellKeys.length; i++) {
      var ck = cellKeys[i];
      var wire = index[ck];
      var layers = labPaintLayersFromView(wire);
      var coord = coordFromWireOrKey(wire, ck);
      if (typeof resolveCellIndex !== "function") {
        continue;
      }
      var gridIdx = resolveCellIndex({ x: coord.x, y: coord.y });
      if (gridIdx == null || gridIdx < 0) {
        continue;
      }
      var plan = canvasPlanFromPaintLayers(layers, gridIdx);
      sprites = sprites.concat(plan.sprites);
      overlays = overlays.concat(plan.overlays);
    }

    return { overlays: overlays, sprites: sprites };
  }

  function collectSpriteRelsFromPaintPlanFrames(framesArr, resolveCellIndex, options) {
    options = options || {};
    if (!Array.isArray(framesArr) || !framesArr.length) {
      return [];
    }
    var rels = new Set();
    for (var fi = 0; fi < framesArr.length; fi++) {
      var fr = framesArr[fi];
      if (!fr || typeof fr !== "object") {
        continue;
      }
      var frameOpts = Object.assign({}, options, {
        replayArrayIndex: fi,
        replayFrames: framesArr,
      });
      var plan = buildLabPaintPlanFromFrame(fr, resolveCellIndex, frameOpts);
      var sprites = plan.sprites || [];
      for (var si = 0; si < sprites.length; si++) {
        var rel = sprites[si].rel;
        if (rel) {
          rels.add(rel);
        }
      }
    }
    return Array.from(rels);
  }

  global.LabReplayPaintPlan = {
    BACKGROUND_FILL: BACKGROUND_FILL,
    VOID_FILL: VOID_FILL,
    CANDIDATE_RING_STROKE: CANDIDATE_RING_STROKE,
    buildEffectiveCellViewIndex: buildEffectiveCellViewIndex,
    buildEffectiveCellViewIndexWithCarry: buildEffectiveCellViewIndexWithCarry,
    buildCellByGridIndexFromFrame: buildCellByGridIndexFromFrame,
    buildDomPlanResolverForFrame: buildDomPlanResolverForFrame,
    buildLabPaintPlanFromFrame: buildLabPaintPlanFromFrame,
    canvasPlanFromPaintLayers: canvasPlanFromPaintLayers,
    collectSpriteRelsFromPaintPlanFrames: collectSpriteRelsFromPaintPlanFrames,
    domPlanFromPaintLayers: domPlanFromPaintLayers,
    indexHasSpriteCapableCells: indexHasSpriteCapableCells,
    labPaintLayersFromView: labPaintLayersFromView,
    lastFrameWithSpriteCapableCells: lastFrameWithSpriteCapableCells,
  };
})(typeof window !== "undefined" ? window : globalThis);
