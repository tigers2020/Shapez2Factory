/**
 * Map mining_map row → sprite key + rotation (deg) + overlay keys.
 * globalThis.AM_AsteroidMapSpriteResolver — pure helpers; no DOM.
 */
(function (g) {
  "use strict";

  function entityTypeString(entity) {
    if (!entity || typeof entity !== "object") return "";
    var v =
      entity.T != null
        ? entity.T
        : entity.type != null
          ? entity.type
          : entity.t != null
            ? entity.t
            : entity.kind != null
              ? entity.kind
              : entity.cell_kind != null
                ? entity.cell_kind
                : "";
    return v != null && v !== "" ? String(v) : "";
  }

  function manifestSprites(manifest) {
    return manifest && manifest.sprites && typeof manifest.sprites === "object"
      ? manifest.sprites
      : null;
  }

  function manifestEntityMap(manifest) {
    return manifest && manifest.entityTypeToSprite && typeof manifest.entityTypeToSprite === "object"
      ? manifest.entityTypeToSprite
      : null;
  }

  function spriteExists(manifest, key) {
    var sp = manifestSprites(manifest);
    return !!(sp && key && sp[key]);
  }

  /**
   * Rotation from blueprint ``R`` / ``r`` (same convention as map inline ``outputOffsetFromRotation`` index).
   * Returns null if absent so callers may fall back to topology rotation for transport.
   */
  function rotationDegFromEntity(entity) {
    if (!entity || typeof entity !== "object") return null;
    var rRaw = entity.R != null ? entity.R : entity.r;
    if (rRaw != null && rRaw !== "") {
      var rNum = typeof rRaw === "number" ? rRaw : parseInt(String(rRaw), 10);
      if (isFinite(rNum)) {
        var k = ((rNum | 0) % 4 + 4) % 4;
        return k * 90;
      }
    }
    var od = entity.output_direction;
    if (od != null && od !== "") {
      var map = { north: 270, n: 270, south: 90, s: 90, east: 0, e: 0, west: 180, w: 180 };
      var s = String(od).toLowerCase();
      if (Object.prototype.hasOwnProperty.call(map, s)) return map[s];
    }
    return null;
  }

  function surfaceFluid(surface) {
    return surface === "fluid";
  }

  function rotationForStraight(n, e, s, w) {
    if (n && s && !e && !w) return 90;
    if (e && w && !n && !s) return 0;
    if (n && !s && !e && !w) return 90;
    if (s && !n && !e && !w) return 90;
    if (e && !w && !n && !s) return 0;
    if (w && !e && !n && !s) return 0;
    return 0;
  }

  function rotationForTurn(n, e, s, w) {
    if (n && e) return 0;
    if (e && s) return 90;
    if (s && w) return 180;
    if (w && n) return 270;
    return 0;
  }

  function countDirs(n, e, s, w) {
    return (n ? 1 : 0) + (e ? 1 : 0) + (s ? 1 : 0) + (w ? 1 : 0);
  }

  /**
   * @param {"belt"|"pipe"} transportRole
   * @param {{ n: boolean, e: boolean, s: boolean, w: boolean }} dirs
   * @param {boolean} isOutputStub extractor output anchor cell (same straight tile as cnt<=1)
   */
  function resolveTransportSprite(transportRole, dirs, isOutputStub) {
    var n = !!dirs.n;
    var e = !!dirs.e;
    var s = !!dirs.s;
    var w = !!dirs.w;
    var cnt = countDirs(n, e, s, w);
    var prefix = transportRole === "pipe" ? "pipe" : "belt";

    // Extractor output anchor: full straight belt/pipe sprite (not empty stub atlas tile).
    if (isOutputStub) {
      return {
        base: prefix + "_straight",
        rotationDeg: rotationForStraight(n, e, s, w),
        overlays: [],
      };
    }

    if (cnt <= 1) {
      return {
        base: prefix + "_straight",
        rotationDeg: rotationForStraight(n, e, s, w),
        overlays: [],
      };
    }

    if (cnt === 2) {
      if ((n && s && !e && !w) || (e && w && !n && !s)) {
        return {
          base: prefix + "_straight",
          rotationDeg: rotationForStraight(n, e, s, w),
          overlays: [],
        };
      }
      return { base: prefix + "_turn", rotationDeg: rotationForTurn(n, e, s, w), overlays: [] };
    }

    return { base: prefix + "_turn", rotationDeg: 0, overlays: [] };
  }

  function suffixCategoryFallback(suffix, family) {
    var straight = family === "pipe" ? "pipe_straight" : "belt_straight";
    var turn = family === "pipe" ? "pipe_turn" : "belt_turn";
    if (!suffix) return straight;
    if (/_Forward$/i.test(suffix) || suffix === "Forward") return straight;
    if (/_LeftTurn$/i.test(suffix) || /_RightTurn$/i.test(suffix)) return turn;
    if (/_Merger/i.test(suffix) || /_Splitter/i.test(suffix) || /Merger$/i.test(suffix) || /Splitter$/i.test(suffix)) {
      return straight;
    }
    if (/_Lift1/i.test(suffix) || /^Lift1/i.test(suffix)) return straight;
    return straight;
  }

  /**
   * Shared SpaceBelt_/SpacePipe_ suffix taxonomy (never cross belt/pipe families).
   */
  function resolveSpaceTransportComposedKey(fullType, family, manifest) {
    var sprites = manifestSprites(manifest);
    var ett = manifestEntityMap(manifest);
    if (!sprites || !fullType) return family === "pipe" ? "pipe_straight" : "belt_straight";

    if (ett && ett[fullType] && sprites[ett[fullType]]) {
      return ett[fullType];
    }

    var prefix = family === "pipe" ? "SpacePipe_" : "SpaceBelt_";
    var suffix = "";
    if (fullType.indexOf(prefix) === 0) {
      suffix = fullType.slice(prefix.length);
    }
    var composed = (family === "pipe" ? "pipe_" : "belt_") + fullType;
    if (sprites[composed]) return composed;

    return suffixCategoryFallback(suffix, family);
  }

  function layoutEquipmentFallbackKey(typ) {
    if (!typ) return null;
    var s = String(typ);
    if (s.indexOf("FluidMinerExtension") >= 0) return "equipment_Layout_FluidMinerExtension";
    if (s.indexOf("ShapeMinerExtension") >= 0) return "equipment_Layout_ShapeMinerExtension";
    if (s.indexOf("FluidMiner") >= 0) return "equipment_Layout_FluidMiner";
    if (s.indexOf("ShapeMiner") >= 0) return "equipment_Layout_ShapeMiner";
    if (s.indexOf("MinerExtension") >= 0) return "extension";
    if (s.indexOf("Miner") >= 0) return "extractor_shape";
    return null;
  }

  function semanticTerrainKey(entity, paintRole, manifest) {
    var err = entity && entity.map_error ? String(entity.map_error) : "";
    if (err === "overlap") return "error_overlap";
    var cs = entity && entity.commit_state ? String(entity.commit_state) : "";
    if (cs === "QUARANTINED_UNROUTED") return "error_unrouted";

    var role = entity && entity.role ? entity.role : "occupied";
    var lk = entity && entity.layout_kind ? String(entity.layout_kind) : "";
    var surf = entity && entity.surface ? String(entity.surface) : "shape";
    var t = entity && entity.t != null ? String(entity.t) : "";

    if (lk === "asteroid_field") {
      return surfaceFluid(surf) ? "mineable_fluid" : "mineable_shape";
    }

    if (role === "mineable") {
      return surfaceFluid(surf) ? "mineable_fluid" : "mineable_shape";
    }

    if (role === "inferred") {
      return "interior_patch";
    }

    if (lk === "miner" || lk === "extractor") {
      if (spriteExists(manifest, "equipment_Layout_ShapeMiner")) return "equipment_Layout_ShapeMiner";
      return "extractor_shape";
    }
    if (lk === "fluid_miner" || lk === "fluid_extractor") {
      if (spriteExists(manifest, "equipment_Layout_FluidMiner")) return "equipment_Layout_FluidMiner";
      return "extractor_fluid";
    }
    if (lk === "extension") {
      if (surfaceFluid(surf)) {
        if (spriteExists(manifest, "equipment_Layout_FluidMinerExtension")) {
          return "equipment_Layout_FluidMinerExtension";
        }
        return "extractor_fluid";
      }
      if (spriteExists(manifest, "equipment_Layout_ShapeMinerExtension")) {
        return "equipment_Layout_ShapeMinerExtension";
      }
      return "extension";
    }
    if (lk === "fluid_extension") {
      if (spriteExists(manifest, "equipment_Layout_FluidMinerExtension")) {
        return "equipment_Layout_FluidMinerExtension";
      }
      return "extractor_fluid";
    }

    if (t && t.indexOf("AsteroidField") === 0 && t.indexOf("PreviewReplace") < 0 && lk !== "asteroid_field") {
      return "asteroid_shell";
    }

    if (paintRole === "belt" || paintRole === "pipe") {
      return "empty";
    }

    return "empty";
  }

  /**
   * Primary sprite key for a cell row + manifest (exact → suffix transport → layout → semantic).
   */
  function resolveAsteroidSpriteKey(entity, manifest, paintRole) {
    var sprites = manifestSprites(manifest);
    if (!sprites) return "empty";

    var typ = entityTypeString(entity);
    var ett = manifestEntityMap(manifest);

    if (typ && ett && ett[typ] && sprites[ett[typ]]) {
      return ett[typ];
    }

    if (typ.indexOf("SpaceBelt_") === 0) {
      return resolveSpaceTransportComposedKey(typ, "belt", manifest);
    }
    if (typ.indexOf("SpacePipe_") === 0) {
      return resolveSpaceTransportComposedKey(typ, "pipe", manifest);
    }

    if (typ.indexOf("Layout_") === 0 || typ.indexOf("Miner") >= 0 || typ.indexOf("Fluid") >= 0) {
      var lay = layoutEquipmentFallbackKey(typ);
      if (lay && sprites[lay]) return lay;
      if (lay) return lay;
    }

    var sem = semanticTerrainKey(entity, paintRole, manifest);
    if (sem && sprites[sem]) return sem;
    return sem || "empty";
  }

  /**
   * Full draw spec: base atlas key, rotation, optional overlay sprite keys (corridor etc. added by caller).
   */
  function resolveMiningCellSpriteDrawSpec(entity, manifest, paintRole, transportOpts) {
    var role = entity && entity.role ? entity.role : "occupied";
    var typ = entityTypeString(entity);
    var overlays = [];

    if (typ.indexOf("SpaceBelt_") === 0) {
      var kb = resolveSpaceTransportComposedKey(typ, "belt", manifest);
      var rotBb = rotationDegFromEntity(entity);
      if (rotBb == null && transportOpts && transportOpts.dirs) {
        rotBb = resolveTransportSprite("belt", transportOpts.dirs, !!transportOpts.isStub).rotationDeg || 0;
      } else if (rotBb == null) {
        rotBb = 0;
      }
      return { baseKey: kb, rotationDeg: rotBb, overlays: overlays };
    }
    if (typ.indexOf("SpacePipe_") === 0) {
      var kpp = resolveSpaceTransportComposedKey(typ, "pipe", manifest);
      var rotPp = rotationDegFromEntity(entity);
      if (rotPp == null && transportOpts && transportOpts.dirs) {
        rotPp = resolveTransportSprite("pipe", transportOpts.dirs, !!transportOpts.isStub).rotationDeg || 0;
      } else if (rotPp == null) {
        rotPp = 0;
      }
      return { baseKey: kpp, rotationDeg: rotPp, overlays: overlays };
    }

    if (role === "belt" || role === "pipe") {
      var tr = role === "pipe" ? "pipe" : "belt";
      var topo =
        transportOpts && transportOpts.dirs
          ? resolveTransportSprite(tr, transportOpts.dirs, !!transportOpts.isStub)
          : { base: tr === "pipe" ? "pipe_straight" : "belt_straight", rotationDeg: 0, overlays: [] };
      return { baseKey: topo.base, rotationDeg: topo.rotationDeg || 0, overlays: overlays };
    }

    var key = resolveAsteroidSpriteKey(entity, manifest, paintRole);
    var rot = rotationDegFromEntity(entity);
    if (rot == null) rot = 0;
    return { baseKey: key, rotationDeg: rot, overlays: overlays };
  }

  g.AM_AsteroidMapSpriteResolver = {
    entityTypeString: entityTypeString,
    rotationDegFromEntity: rotationDegFromEntity,
    semanticTerrainKey: function (entity, paintRole, manifest) {
      return semanticTerrainKey(entity, paintRole, manifest || {});
    },
    resolveTerrainSprite: function (row, paintRole) {
      var k = semanticTerrainKey(row, paintRole, null);
      return { base: k, rotationDeg: 0, overlays: [] };
    },
    resolveTransportSprite: resolveTransportSprite,
    rotationForStraight: rotationForStraight,
    rotationForTurn: rotationForTurn,
    resolveAsteroidSpriteKey: resolveAsteroidSpriteKey,
    resolveMiningCellSpriteDrawSpec: resolveMiningCellSpriteDrawSpec,
    resolveSpaceTransportComposedKey: resolveSpaceTransportComposedKey,
    layoutEquipmentFallbackKey: layoutEquipmentFallbackKey,
  };
})(typeof globalThis !== "undefined" ? globalThis : window);
