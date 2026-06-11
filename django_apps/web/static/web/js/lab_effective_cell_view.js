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
      return String(cell.kind);
    }
    if (cell.cell_kind != null) {
      return String(cell.cell_kind);
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
    var occupantRotation = null;
    var transportKind = "none";
    var transportTileId = null;
    var simulation = null;
    var outputTransportKind = "none";
    var layer = 0;

    function applyCell(cell) {
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
      var occupant = occupantKindFromCell(kind);
      if (occupant) {
        occupantKind = occupant;
        var rot = wireRotation(cell);
        if (rot != null) {
          occupantRotation = rot;
        }
        var profile = wireOutputTransportKind(cell);
        if (profile !== "none") {
          outputTransportKind = profile;
        }
      }
      if (isRouteTile(tileType, kind)) {
        transportKind = routeTransportKind(tileType, kind, wireTransportRaw(cell));
        transportTileId = tileType || null;
        simulation = simulationForTileId(transportTileId);
      }
    }

    applyCell(fullCell);
    applyCell(deltaCell);
    if (overlayCells) {
      for (var i = 0; i < overlayCells.length; i++) {
        applyCell(overlayCells[i]);
      }
    }
    if (!base && overlayCells && overlayCells.length) {
      layer = wireLayer(overlayCells[0], layer);
    }

    return {
      frame_index: frameIndex,
      coord: { x: x, y: y, layer: layer },
      terrain: { kind: terrainKind, tile_type: terrainTileType },
      occupant: { kind: occupantKind, rotation: occupantRotation },
      transport: {
        kind: transportKind,
        tile_id: transportTileId,
        simulation: simulation,
      },
      output: { transport_kind: outputTransportKind },
      sources: sources,
    };
  }

  function effectiveCellViewDisplayRows(view) {
    if (!view) {
      return [];
    }
    var rotLabels = ["East", "North", "West", "South"];
    var rot =
      view.occupant && view.occupant.rotation != null && rotLabels[view.occupant.rotation] != null
        ? rotLabels[view.occupant.rotation]
        : view.occupant && view.occupant.rotation != null
          ? String(view.occupant.rotation)
          : "—";
    return [
      ["coord", "(" + view.coord.x + "," + view.coord.y + ",L" + view.coord.layer + ")"],
      ["terrain", view.terrain.kind],
      ["occupant", view.occupant.kind],
      ["output_transport", view.output.transport_kind],
      ["transport_tile", view.transport.tile_id || "none"],
      ["transport_kind", view.transport.kind],
      ["simulation", view.transport.simulation || "—"],
      ["rotation", rot],
    ];
  }

  global.LabEffectiveCellView = {
    mergeEffectiveCellView: mergeEffectiveCellView,
    normalizeProjectTransportKind: normalizeProjectTransportKind,
    simulationForTileId: simulationForTileId,
    effectiveCellViewDisplayRows: effectiveCellViewDisplayRows,
  };
})(typeof window !== "undefined" ? window : globalThis);
