/**
 * Typed registry for cell_overlay_json bucket harvest by consumer role.
 * Mirrors django_apps/asteroid_lab/replay/replay_overlay_bucket_registry.py
 */
(function (global) {
  "use strict";

  var PAINT_TARGET = "paint_target";
  var SEMANTIC_LOOKUP = "semantic_lookup";

  function appendCells(out, lst) {
    if (!Array.isArray(lst)) {
      return;
    }
    for (var i = 0; i < lst.length; i++) {
      if (lst[i] && typeof lst[i] === "object") {
        out.push(Object.assign({}, lst[i]));
      }
    }
  }

  function pushFromBlocks(out, blocks) {
    if (!Array.isArray(blocks)) {
      return;
    }
    for (var i = 0; i < blocks.length; i++) {
      var block = blocks[i];
      if (!block || typeof block !== "object") {
        continue;
      }
      if (Array.isArray(block.cells)) {
        appendCells(out, block.cells);
      } else if (block.x != null && block.y != null) {
        out.push(Object.assign({}, block));
      }
    }
  }

  function harvestCellList(key) {
    return function (overlay, out) {
      appendCells(out, overlay[key]);
    };
  }

  function harvestCellBlocks(key) {
    return function (overlay, out) {
      pushFromBlocks(out, overlay[key]);
    };
  }

  function harvestBlocksCellsJson(key) {
    return function (overlay, out) {
      var blocks = overlay[key];
      if (!Array.isArray(blocks)) {
        return;
      }
      for (var i = 0; i < blocks.length; i++) {
        var block = blocks[i];
        if (!block || typeof block !== "object") {
          continue;
        }
        appendCells(out, block.cells_json);
      }
    };
  }

  function harvestMainComponentCandidate(overlay, out) {
    var main = overlay.main_component_candidate;
    if (!main || typeof main !== "object") {
      return;
    }
    if (Array.isArray(main.cells_json)) {
      appendCells(out, main.cells_json);
    } else if (main.x != null && main.y != null) {
      out.push(Object.assign({}, main));
    }
  }

  function registryHandledKeys() {
    var keys = {};
    for (var i = 0; i < OVERLAY_BUCKET_REGISTRY.length; i++) {
      keys[OVERLAY_BUCKET_REGISTRY[i].key] = 1;
    }
    return keys;
  }

  function harvestDynamicDictCellsJson(overlay, out) {
    var handled = registryHandledKeys();
    var keys = Object.keys(overlay);
    for (var i = 0; i < keys.length; i++) {
      var key = keys[i];
      if (handled[key]) {
        continue;
      }
      var val = overlay[key];
      if (!val || typeof val !== "object" || Array.isArray(val)) {
        continue;
      }
      appendCells(out, val.cells_json);
    }
  }

  var OVERLAY_BUCKET_REGISTRY = [
    {
      key: "cells",
      roles: { semantic_lookup: 1, paint_target: 1 },
      harvest: harvestCellList("cells"),
    },
    {
      key: "equipment_cells",
      roles: { semantic_lookup: 1, paint_target: 1 },
      harvest: harvestCellList("equipment_cells"),
    },
    {
      key: "equipment",
      roles: { semantic_lookup: 1, paint_target: 1 },
      harvest: harvestCellList("equipment"),
    },
    {
      key: "adjacent_transport",
      roles: { semantic_lookup: 1, paint_target: 1 },
      harvest: harvestCellList("adjacent_transport"),
    },
    {
      key: "components",
      roles: { semantic_lookup: 1 },
      harvest: harvestCellBlocks("components"),
    },
    {
      key: "transport_components",
      roles: { semantic_lookup: 1 },
      harvest: harvestCellBlocks("transport_components"),
    },
    {
      key: "transport",
      roles: { semantic_lookup: 1, paint_target: 1 },
      harvest: harvestCellList("transport"),
    },
    {
      key: "main_component_candidate",
      roles: { semantic_lookup: 1 },
      harvest: harvestMainComponentCandidate,
    },
    {
      key: "cleanup_candidate_cells",
      roles: { semantic_lookup: 1 },
      harvest: harvestCellList("cleanup_candidate_cells"),
    },
    {
      key: "equipment_bundles",
      roles: { paint_target: 1 },
      harvest: harvestBlocksCellsJson("equipment_bundles"),
    },
  ];

  function overlayBucketSpecs(role) {
    if (!role) {
      return OVERLAY_BUCKET_REGISTRY.slice();
    }
    return OVERLAY_BUCKET_REGISTRY.filter(function (spec) {
      return spec.roles[role];
    });
  }

  function overlayBucketKeysForRole(role) {
    return overlayBucketSpecs(role).map(function (spec) {
      return spec.key;
    });
  }

  function collectOverlayCellsForRole(overlay, role) {
    if (!overlay || typeof overlay !== "object") {
      return [];
    }
    var out = [];
    var specs = overlayBucketSpecs(role);
    for (var i = 0; i < specs.length; i++) {
      specs[i].harvest(overlay, out);
    }
    if (role === SEMANTIC_LOOKUP) {
      harvestDynamicDictCellsJson(overlay, out);
    }
    return out;
  }

  function collectOverlayCellsForSemanticLookup(overlay) {
    return collectOverlayCellsForRole(overlay, SEMANTIC_LOOKUP);
  }

  function collectOverlayCellsForPaintTarget(overlay) {
    return collectOverlayCellsForRole(overlay, PAINT_TARGET);
  }

  global.LabReplayOverlayBucketRegistry = {
    PAINT_TARGET: PAINT_TARGET,
    SEMANTIC_LOOKUP: SEMANTIC_LOOKUP,
    overlayBucketKeysForRole: overlayBucketKeysForRole,
    collectOverlayCellsForRole: collectOverlayCellsForRole,
    collectOverlayCellsForSemanticLookup: collectOverlayCellsForSemanticLookup,
    collectOverlayCellsForPaintTarget: collectOverlayCellsForPaintTarget,
  };
})(typeof window !== "undefined" ? window : globalThis);
