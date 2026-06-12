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
    return { rel: rel, rotation: rotation(occupant) };
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

  function collectCoordUniverse(mapView) {
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

    var frameIndex = null;
    if (frame.frame_index != null) {
      var fi = parseInt(String(frame.frame_index), 10);
      frameIndex = Number.isFinite(fi) ? fi : null;
    }

    var index = {};
    var universe = collectCoordUniverse(mapView);
    for (i = 0; i < universe.length; i++) {
      var x = universe[i][0];
      var y = universe[i][1];
      var layer = universe[i][2];

      var fullCell = firstRowAtCoord(fullRows, x, y, layer);
      var deltaCell = firstRowAtCoord(deltaRows, x, y, layer);
      var overlayCells = rowsAtCoord(overlayRows, x, y, layer);
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

  global.LabReplayPaintPlan = {
    BACKGROUND_FILL: BACKGROUND_FILL,
    VOID_FILL: VOID_FILL,
    buildEffectiveCellViewIndex: buildEffectiveCellViewIndex,
    labPaintLayersFromView: labPaintLayersFromView,
  };
})(typeof window !== "undefined" ? window : globalThis);
