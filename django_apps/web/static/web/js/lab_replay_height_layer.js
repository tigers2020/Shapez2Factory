/**
 * Shapez 2 island height layer (L=0/1/2) for replay wire cells — browser read path.
 * Mirrors django_apps/asteroid_lab/replay/map_height_layer.py (keep in sync).
 */
(function (global) {
  "use strict";

  var REPLAY_HEIGHT_LAYER_MIN = 0;
  var REPLAY_HEIGHT_LAYER_MAX = 2;

  var SHAPE_FIELD_KINDS = {
    asteroid_shape_field: 1,
    shape_miner: 1,
    shape_miner_extension: 1,
    inner_field_block: 1,
  };
  var FLUID_FIELD_KINDS = {
    asteroid_fluid_field: 1,
    fluid_miner: 1,
    fluid_miner_extension: 1,
  };
  var FLUID_TRANSPORT_KINDS = {
    space_pipe: 1,
    fluid_pipe: 1,
  };
  var FLUID_TRANSPORT_VALUES = { fluid: 1, fluid_pipe: 1 };
  var SHAPE_TRANSPORT_VALUES = { shape: 1, shape_belt: 1 };

  function clampReplayHeightLayer(value) {
    if (typeof value === "boolean") {
      return REPLAY_HEIGHT_LAYER_MIN;
    }
    var n;
    if (typeof value === "number" && Number.isFinite(value)) {
      n = Math.trunc(value);
    } else if (typeof value === "string") {
      var parsed = parseInt(value, 10);
      if (!Number.isFinite(parsed)) {
        return REPLAY_HEIGHT_LAYER_MIN;
      }
      n = parsed;
    } else {
      return REPLAY_HEIGHT_LAYER_MIN;
    }
    return Math.max(
      REPLAY_HEIGHT_LAYER_MIN,
      Math.min(REPLAY_HEIGHT_LAYER_MAX, n),
    );
  }

  function wireExplicitHeightLayer(data) {
    if (!data || typeof data !== "object") {
      return null;
    }
    var keys = ["layer", "L", "z", "Z"];
    for (var i = 0; i < keys.length; i++) {
      var key = keys[i];
      if (!(key in data)) {
        continue;
      }
      var raw = data[key];
      if (raw == null || raw === "") {
        continue;
      }
      return clampReplayHeightLayer(raw);
    }
    return null;
  }

  function layerFromTileType(tile) {
    if (tile.indexOf("Lift") >= 0) {
      return 1;
    }
    if (tile.indexOf("SpacePipe") >= 0 || tile.indexOf("SpacePipe") === 0) {
      return 1;
    }
    if (tile.indexOf("SpaceBelt") >= 0 || tile.indexOf("SpaceBelt") === 0) {
      return 0;
    }
    return null;
  }

  function resolveReplayHeightLayer(opts) {
    opts = opts || {};
    if (opts.layer != null) {
      return clampReplayHeightLayer(opts.layer);
    }

    var kind = String(opts.cell_kind || "");
    var transport = String(opts.transport_kind || "");
    var tile = String(opts.tile_type || "");

    var tileLayer = layerFromTileType(tile);
    if (tileLayer != null) {
      return tileLayer;
    }

    if (kind === "candidate_miner") {
      return FLUID_TRANSPORT_VALUES[transport] ? 1 : 0;
    }
    if (kind === "candidate_transport_stub") {
      return FLUID_TRANSPORT_VALUES[transport] ? 1 : 0;
    }
    if (kind === "space_belt") {
      return 0;
    }
    if (FLUID_TRANSPORT_KINDS[kind]) {
      return 1;
    }
    if (FLUID_FIELD_KINDS[kind] || FLUID_TRANSPORT_VALUES[transport]) {
      return 1;
    }
    if (SHAPE_FIELD_KINDS[kind] || SHAPE_TRANSPORT_VALUES[transport]) {
      return 0;
    }
    if (kind.indexOf("route") >= 0) {
      return FLUID_TRANSPORT_VALUES[transport] ? 1 : 0;
    }
    return 0;
  }

  function wireTransportKindForLayerResolution(row) {
    if (!row || typeof row !== "object") {
      return "";
    }
    var kind = String(row.kind != null ? row.kind : row.cell_kind || "");
    if (
      kind === "candidate_miner" ||
      kind === "candidate_transport_stub" ||
      kind === "candidate_route_path" ||
      kind === "route_probe_path" ||
      kind === "inner_field_block"
    ) {
      var outputTransport = row.output_transport_kind;
      if (outputTransport != null && String(outputTransport).trim()) {
        return String(outputTransport);
      }
    }
    return String(
      row.transport_kind != null ? row.transport_kind : row.transport || "",
    );
  }

  function enrichReplayWireRowWithLayer(row) {
    var out = Object.assign({}, row || {});
    var explicit = wireExplicitHeightLayer(out);
    var kind = String(out.kind != null ? out.kind : out.cell_kind || "");
    var transport = wireTransportKindForLayerResolution(out);
    var tile = String(
      out.tile_type != null ? out.tile_type : out.sprite_identifier || "",
    );
    out.layer = resolveReplayHeightLayer({
      cell_kind: kind,
      transport_kind: transport,
      tile_type: tile,
      layer: explicit,
    });
    return out;
  }

  function resolveReplayHeightLayerForWireRow(row) {
    return enrichReplayWireRowWithLayer(row).layer;
  }

  global.LabReplayHeightLayer = {
    clampReplayHeightLayer: clampReplayHeightLayer,
    wireExplicitHeightLayer: wireExplicitHeightLayer,
    resolveReplayHeightLayer: resolveReplayHeightLayer,
    wireTransportKindForLayerResolution: wireTransportKindForLayerResolution,
    enrichReplayWireRowWithLayer: enrichReplayWireRowWithLayer,
    resolveReplayHeightLayerForWireRow: resolveReplayHeightLayerForWireRow,
  };
})(typeof window !== "undefined" ? window : globalThis);
