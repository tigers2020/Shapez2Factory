/**
 * EffectiveCellView — terrain / occupant / transport occupancy / output transport merge.
 * Mirrors django_apps/asteroid_lab/replay/effective_cell_view.py
 */
(function (global) {
  "use strict";

  var LEGACY_SHAPE_OUTPUT = { shape_belt: 1, belt: 1, shape: 1, space_belt: 1 };
  var LEGACY_FLUID_OUTPUT = { fluid_pipe: 1, pipe: 1, fluid: 1, space_pipe: 1 };
  var ROUTE_CELL_KINDS = { space_belt: 1, space_pipe: 1 };
  var TERRAIN_KINDS = {
    asteroid_shape_field: 1,
    asteroid_fluid_field: 1,
    void: 1,
    empty: 1,
  };
  var OCCUPANT_KINDS = {
    candidate_miner: 1,
    candidate_transport_stub: 1,
    candidate_route_path: 1,
    shape_miner: 1,
    fluid_miner: 1,
    shape_miner_extension: 1,
    fluid_miner_extension: 1,
    miner: 1,
    extension: 1,
    committed_miner: 1,
    building: 1,
  };
  var OVERLAY_SEMANTIC_KINDS = {
    inner_field_block: 1,
    candidate_miner: 1,
    candidate_transport_stub: 1,
    candidate_route_path: 1,
    route_probe_path: 1,
    planned_exterior_connector: 1,
  };

  function normalizeProjectTransportKind(raw) {
    var value = String(raw || "")
      .trim()
      .toLowerCase();
    if (!value || value === "none") {
      return "none";
    }
    if (LEGACY_SHAPE_OUTPUT[value]) {
      return "space_belt";
    }
    if (LEGACY_FLUID_OUTPUT[value]) {
      return "space_pipe";
    }
    return "none";
  }

  function simulationForTileId(tileId) {
    if (!tileId) {
      return null;
    }
    if (tileId.indexOf("Merger") >= 0) {
      return "SpaceMergerSimulation";
    }
    if (tileId.indexOf("Splitter") >= 0) {
      return "SpaceSplitterSimulation";
    }
    if (tileId.indexOf("SpaceBelt_") === 0 || tileId.indexOf("SpacePipe_") === 0) {
      return "SpaceConveyorSimulation";
    }
    return null;
  }

  function wireCellKind(cell) {
    if (!cell || typeof cell !== "object") {
      return "";
    }
    if (cell.kind != null) {
      var kind = String(cell.kind).trim();
      if (kind) {
        return kind;
      }
    }
    if (cell.cell_kind != null) {
      var cellKind = String(cell.cell_kind).trim();
      if (cellKind) {
        return cellKind;
      }
    }
    return "";
  }

  function wireTransportRaw(cell) {
    if (!cell || typeof cell !== "object") {
      return "";
    }
    if (cell.transport != null) {
      return String(cell.transport);
    }
    if (cell.transport_kind != null) {
      return String(cell.transport_kind);
    }
    return "";
  }

  function wireOutputTransportKind(cell) {
    if (!cell || typeof cell !== "object") {
      return "none";
    }
    if (cell.output_transport_kind != null && String(cell.output_transport_kind).trim()) {
      var normalized = normalizeProjectTransportKind(cell.output_transport_kind);
      if (normalized !== "none") {
        return normalized;
      }
    }
    var kind = wireCellKind(cell);
    if (occupantKindFromCell(kind)) {
      return normalizeProjectTransportKind(wireTransportRaw(cell));
    }
    return "none";
  }

  function wireTileType(cell) {
    if (!cell || typeof cell !== "object") {
      return "";
    }
    if (cell.tile_type != null) {
      return String(cell.tile_type);
    }
    if (cell.sprite_identifier != null) {
      return String(cell.sprite_identifier);
    }
    return "";
  }

  function wireRotation(cell) {
    if (!cell || cell.rotation == null) {
      return null;
    }
    var rot = parseInt(String(cell.rotation), 10);
    return Number.isFinite(rot) ? rot : null;
  }

  function wireLayer(cell, defaultLayer) {
    if (!cell || cell.layer == null) {
      return defaultLayer != null ? defaultLayer : 0;
    }
    var layer = parseInt(String(cell.layer), 10);
    return Number.isFinite(layer) ? layer : defaultLayer != null ? defaultLayer : 0;
  }

  function isRouteTile(tileType, kind) {
    if (tileType.indexOf("SpaceBelt_") === 0 || tileType.indexOf("SpacePipe_") === 0) {
      return true;
    }
    return !!ROUTE_CELL_KINDS[kind];
  }

  function overlayRoleFromCell(cell) {
    if (!cell || typeof cell !== "object") {
      return null;
    }
    if (cell.overlay_role != null && String(cell.overlay_role).trim()) {
      return String(cell.overlay_role).trim();
    }
    var kind = wireCellKind(cell).trim();
    if (OVERLAY_SEMANTIC_KINDS[kind]) {
      return kind;
    }
    return null;
  }

  function occupantKindFromCell(kind) {
    if (!kind) {
      return null;
    }
    if (!OCCUPANT_KINDS[kind]) {
      return null;
    }
    if (kind === "shape_miner" || kind === "fluid_miner" || kind === "miner") {
      return "committed_miner";
    }
    if (kind === "shape_miner_extension" || kind === "fluid_miner_extension" || kind === "extension") {
      return "extension";
    }
    return kind;
  }

  function routeTransportKind(tileType, kind, transportRaw) {
    var normalized = normalizeProjectTransportKind(kind || transportRaw);
    if (normalized !== "none") {
      return normalized;
    }
    if (tileType.indexOf("SpacePipe_") === 0) {
      return "space_pipe";
    }
    if (tileType.indexOf("SpaceBelt_") === 0) {
      return "space_belt";
    }
    return "none";
  }

  function mergeEffectiveCellView(options) {
    var x = options.x;
    var y = options.y;
    var frameIndex = options.frameIndex != null ? options.frameIndex : null;
    var fullCell = options.fullCell || null;
    var deltaCell = options.deltaCell || null;
    var overlayCells = options.overlayCells || null;
    var base = deltaCell || fullCell;
    if (!base && (!overlayCells || !overlayCells.length)) {
      return null;
    }

    var sources = {};
    if (fullCell) {
      sources.full_cell = fullCell;
    }
    if (deltaCell) {
      sources.delta_cell = deltaCell;
    }
    if (overlayCells && overlayCells.length) {
      sources.overlay_cells = overlayCells.length === 1 ? overlayCells[0] : overlayCells;
    }

    var terrainKind = "empty";
    var terrainTileType = null;
    var occupantKind = "none";
    var occupantWireKind = null;
    var occupantSpriteId = null;
    var occupantRotation = null;
    var transportKind = "none";
    var transportTileId = null;
    var simulation = null;
    var outputTransportKind = "none";
    var overlayRole = null;
    var layer = 0;

    function applyCell(cell, isOverlay) {
      if (!cell) {
        return;
      }
      var kind = wireCellKind(cell);
      var tileType = wireTileType(cell);
      layer = wireLayer(cell, layer);
      if (TERRAIN_KINDS[kind] || (!kind && !tileType)) {
        if (kind) {
          terrainKind = kind;
        }
        if (tileType) {
          terrainTileType = tileType;
        }
      }
      if (isOverlay) {
        var role = overlayRoleFromCell(cell);
        if (role) {
          overlayRole = role;
        }
        var outputProfile = wireOutputTransportKind(cell);
        if (outputProfile !== "none" && !occupantKindFromCell(kind)) {
          outputTransportKind = outputProfile;
        }
      }
      var occupant = occupantKindFromCell(kind);
      if (occupant) {
        occupantKind = occupant;
        if (kind) {
          occupantWireKind = kind;
        }
        var rot = wireRotation(cell);
        if (rot != null) {
          occupantRotation = rot;
        }
        var profile = wireOutputTransportKind(cell);
        if (profile !== "none") {
          outputTransportKind = profile;
        }
        if (tileType && !isRouteTile(tileType, kind)) {
          occupantSpriteId = tileType;
        }
      }
      if (isRouteTile(tileType, kind)) {
        transportKind = routeTransportKind(tileType, kind, wireTransportRaw(cell));
        transportTileId = tileType || null;
        simulation = simulationForTileId(transportTileId);
      }
    }

    applyCell(fullCell, false);
    applyCell(deltaCell, false);
    if (overlayCells) {
      for (var i = 0; i < overlayCells.length; i++) {
        applyCell(overlayCells[i], true);
      }
    }
    if (!base && overlayCells && overlayCells.length) {
      layer = wireLayer(overlayCells[0], layer);
    }

    return {
      frame_index: frameIndex,
      coord: { x: x, y: y, layer: layer },
      terrain: { kind: terrainKind, tile_type: terrainTileType },
      occupant: {
        kind: occupantKind,
        wire_kind: occupantWireKind,
        sprite_id: occupantSpriteId,
        rotation: occupantRotation,
      },
      transport: {
        kind: transportKind,
        tile_id: transportTileId,
        simulation: simulation,
      },
      output: { transport_kind: outputTransportKind },
      overlay_role: overlayRole,
      sources: sources,
    };
  }

  function humanizeKindToken(token) {
    var value = String(token || "")
      .trim()
      .toLowerCase();
    if (!value || value === "none" || value === "empty") {
      return "None";
    }
    return value
      .split("_")
      .filter(function (part) {
        return !!part;
      })
      .map(function (part) {
        return part.charAt(0).toUpperCase() + part.slice(1);
      })
      .join(" ");
  }

  function formatRotationLabel(rotation) {
    var rotLabels = ["East", "North", "West", "South"];
    if (rotation == null) {
      return "";
    }
    var idx = parseInt(String(rotation), 10);
    if (Number.isFinite(idx) && rotLabels[idx] != null) {
      return rotLabels[idx];
    }
    return String(rotation);
  }

  function spriteDisplayValue(view) {
    if (!view || typeof view !== "object") {
      return "None";
    }
    var occupant = view.occupant || {};
    var occSprite =
      occupant.sprite_id != null && String(occupant.sprite_id).trim()
        ? String(occupant.sprite_id).trim()
        : "";
    if (occSprite) {
      return occSprite;
    }
    var transport = view.transport || {};
    var tileId = transport.tile_id != null ? String(transport.tile_id).trim() : "";
    if (tileId) {
      return tileId;
    }
    return "None";
  }

  function occupantDisplayLabel(view) {
    var occupant = view && view.occupant ? view.occupant : {};
    var wireKind =
      occupant.wire_kind != null && String(occupant.wire_kind).trim()
        ? String(occupant.wire_kind).trim()
        : "";
    if (wireKind) {
      return humanizeKindToken(wireKind);
    }
    var occKind = occupant.kind != null ? String(occupant.kind).trim() : "none";
    return humanizeKindToken(occKind);
  }

  function isOverlaySemanticKind(token) {
    var value = String(token || "").trim();
    return !!value && OVERLAY_SEMANTIC_KINDS[value] === 1;
  }

  function isOverlayOutputHint(view) {
    if (!view || typeof view !== "object") {
      return false;
    }
    var occupant = view.occupant || {};
    var wireKind =
      occupant.wire_kind != null && String(occupant.wire_kind).trim()
        ? String(occupant.wire_kind).trim().toLowerCase()
        : "";
    var occKind = occupant.kind != null ? String(occupant.kind).trim().toLowerCase() : "none";
    if (
      occKind &&
      occKind !== "none" &&
      !isOverlaySemanticKind(occKind) &&
      !isOverlaySemanticKind(wireKind)
    ) {
      return false;
    }
    var outputKind =
      view.output && view.output.transport_kind != null
        ? String(view.output.transport_kind).trim().toLowerCase()
        : "none";
    var transportKind =
      view.transport && view.transport.kind != null
        ? String(view.transport.kind).trim().toLowerCase()
        : "none";
    return outputKind !== "none" && transportKind === "none";
  }

  function hasMachineSummary(view) {
    if (!view || typeof view !== "object") {
      return false;
    }
    var occupant = view.occupant || {};
    var wireKind =
      occupant.wire_kind != null && String(occupant.wire_kind).trim()
        ? String(occupant.wire_kind).trim()
        : "";
    var occKind = occupant.kind != null ? String(occupant.kind).trim().toLowerCase() : "none";
    if (isOverlaySemanticKind(wireKind) || isOverlaySemanticKind(occKind)) {
      return false;
    }
    if (view.overlay_role && isOverlaySemanticKind(view.overlay_role)) {
      return false;
    }
    return !!occKind && occKind !== "none";
  }

  function effectiveCellViewDisplayModel(view, meta) {
    meta = meta || {};
    if (!view) {
      return {
        coord: "",
        title: "",
        summary: [],
        sections: [],
        debug: { sprite: null, rawSourcesAvailable: false },
        frame_index: null,
        detail_source: null,
      };
    }

    var coord = view.coord || { x: 0, y: 0, layer: 0 };
    var coordStr =
      "(" + coord.x + "," + coord.y + ",L" + (coord.layer != null ? coord.layer : 0) + ")";
    var terrainKind =
      view.terrain && view.terrain.kind != null ? String(view.terrain.kind).trim().toLowerCase() : "empty";
    var outputKind =
      view.output && view.output.transport_kind != null
        ? String(view.output.transport_kind).trim().toLowerCase()
        : "none";
    var transportKind =
      view.transport && view.transport.kind != null
        ? String(view.transport.kind).trim().toLowerCase()
        : "none";
    var overlayRole = view.overlay_role ? String(view.overlay_role).trim() : "";
    var overlayOutputHint = isOverlayOutputHint(view);
    var machine = hasMachineSummary(view);
    var sections = [];
    var summary = [];

    sections.push({
      id: "cell",
      title: "Cell",
      items: [{ value: coordStr }],
    });

    if (machine) {
      var machineLabel = occupantDisplayLabel(view);
      var machineItems = [{ value: machineLabel }];
      summary.push(["Machine", machineLabel]);
      if (view.occupant.rotation != null) {
        var facing = formatRotationLabel(view.occupant.rotation);
        machineItems.push({ value: "Facing: " + facing });
        summary.push(["Facing", facing]);
      }
      if (outputKind !== "none") {
        var outputLabel = humanizeKindToken(outputKind).toLowerCase();
        machineItems.push({ value: "Output: " + outputLabel });
        summary.push(["Output", outputLabel]);
      }
      sections.push({
        id: "machine",
        title: "Machine",
        items: machineItems,
      });
    } else {
      if (terrainKind && terrainKind !== "empty") {
        var terrainLabel = humanizeKindToken(terrainKind);
        sections.push({
          id: "terrain",
          title: "Terrain",
          items: [{ value: terrainLabel }],
        });
      }
      if (overlayRole) {
        var overlayItems = [{ value: humanizeKindToken(overlayRole) }];
        if (overlayOutputHint) {
          overlayItems.push({
            value: "Requires output: " + humanizeKindToken(outputKind).toLowerCase(),
          });
        }
        sections.push({
          id: "overlay",
          title: "Overlay",
          items: overlayItems,
        });
      }
      sections.push({
        id: "occupant",
        title: "Occupant",
        items: [{ value: "None" }],
      });
      if (transportKind && transportKind !== "none") {
        var routeItems = [{ value: humanizeKindToken(transportKind) }];
        var transportTile =
          view.transport.tile_id != null ? String(view.transport.tile_id).trim() : "";
        if (transportTile) {
          routeItems.push({ value: "Tile: " + transportTile });
        }
        if (view.occupant && view.occupant.rotation != null) {
          var routeFacing = formatRotationLabel(view.occupant.rotation);
          if (routeFacing) {
            routeItems.push({ value: "Facing: " + routeFacing });
          }
        }
        var simulation =
          view.transport.simulation != null ? String(view.transport.simulation).trim() : "";
        if (simulation) {
          routeItems.push({ value: "Simulation: " + simulation });
        }
        sections.push({
          id: "transport",
          title: "Transport",
          items: routeItems,
        });
      } else if (terrainKind !== "empty" || overlayRole) {
        sections.push({
          id: "transport",
          title: "Transport",
          items: [{ value: "None" }],
        });
      }
    }

    var spriteDebug = spriteDisplayValue(view);
    return {
      coord: coordStr,
      title: machine ? occupantDisplayLabel(view) : overlayRole ? humanizeKindToken(overlayRole) : "",
      summary: summary,
      sections: sections,
      debug: {
        sprite: spriteDebug !== "None" ? spriteDebug : null,
        rawSourcesAvailable: !!(view.sources && typeof view.sources === "object"),
      },
      frame_index: meta.frame_index != null ? meta.frame_index : view.frame_index,
      detail_source:
        meta.detail_source != null && String(meta.detail_source).trim()
          ? String(meta.detail_source).trim()
          : null,
    };
  }

  function effectiveCellViewDisplaySections(view, meta) {
    var model = effectiveCellViewDisplayModel(view, meta);
    return {
      frame_index: model.frame_index,
      detail_source: model.detail_source,
      sections: model.sections,
      debug: model.debug,
    };
  }

  function effectiveCellViewDisplayRows(view) {
    var display = effectiveCellViewDisplaySections(view);
    var rows = [];
    for (var i = 0; i < display.sections.length; i++) {
      var section = display.sections[i];
      for (var j = 0; j < section.items.length; j++) {
        rows.push([section.title, section.items[j].value]);
      }
    }
    return rows;
  }

  function collectWireSpriteIds(cell) {
    if (!cell || typeof cell !== "object") {
      return [];
    }
    var out = [];
    var fields = ["sprite_identifier", "tile_type"];
    for (var i = 0; i < fields.length; i++) {
      var raw = cell[fields[i]];
      if (raw != null && String(raw).trim()) {
        out.push(String(raw).trim());
      }
    }
    return out;
  }

  function effectiveCellViewDisplayDiagnostics(view, sourceBag) {
    sourceBag = sourceBag || {};
    var items = [];
    if (!view || typeof view !== "object") {
      return { items: items, hasContent: false };
    }

    var occupant = view.occupant || {};
    var terrain = view.terrain || {};
    var transport = view.transport || {};
    var spriteSeen = {};

    function pushItem(label, value) {
      var text = value != null ? String(value).trim() : "";
      if (!text) {
        return;
      }
      items.push({ label: label, value: text });
    }

    function pushSprite(label, value) {
      var text = value != null ? String(value).trim() : "";
      if (!text || spriteSeen[text]) {
        return;
      }
      spriteSeen[text] = true;
      pushItem(label, text);
    }

    var machine = hasMachineSummary(view);
    var transportKind =
      transport.kind != null ? String(transport.kind).trim().toLowerCase() : "none";
    var transportTile =
      transport.tile_id != null ? String(transport.tile_id).trim() : "";
    var showTransportSummary = transportKind !== "none";

    pushSprite("Occupant sprite", occupant.sprite_id);
    pushSprite("Terrain sprite", terrain.tile_type);
    if (!showTransportSummary) {
      pushSprite("Transport sprite", transport.tile_id);
    }

    var sourceKeys = Object.keys(sourceBag);
    for (var sk = 0; sk < sourceKeys.length; sk++) {
      var bagVal = sourceBag[sourceKeys[sk]];
      var cells = Array.isArray(bagVal) ? bagVal : [bagVal];
      for (var ci = 0; ci < cells.length; ci++) {
        var wireIds = collectWireSpriteIds(cells[ci]);
        for (var wi = 0; wi < wireIds.length; wi++) {
          if (showTransportSummary && wireIds[wi] === transportTile) {
            continue;
          }
          pushSprite("Source sprite", wireIds[wi]);
        }
      }
    }

    var simulation =
      transport.simulation != null ? String(transport.simulation).trim() : "";
    if (simulation && (!showTransportSummary || machine)) {
      pushItem("Simulation", simulation);
    }

    return { items: items, hasContent: items.length > 0 };
  }

  global.LabEffectiveCellView = {
    mergeEffectiveCellView: mergeEffectiveCellView,
    normalizeProjectTransportKind: normalizeProjectTransportKind,
    simulationForTileId: simulationForTileId,
    effectiveCellViewDisplayModel: effectiveCellViewDisplayModel,
    effectiveCellViewDisplaySections: effectiveCellViewDisplaySections,
    effectiveCellViewDisplayRows: effectiveCellViewDisplayRows,
    effectiveCellViewDisplayDiagnostics: effectiveCellViewDisplayDiagnostics,
  };
})(typeof window !== "undefined" ? window : globalThis);
