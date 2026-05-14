/**
 * Asteroid optimizer map: sprite atlas load + MVP in-memory atlas (no binary asset).
 * Exposes globalThis.AM_AsteroidMapSpriteAtlas for the embedded page script.
 */
(function (g) {
  "use strict";

  var SPRITE_KEY_ORDER = [
    "empty",
    "mineable_shape",
    "mineable_fluid",
    "asteroid_shell",
    "interior_patch",
    "extractor_shape",
    "extractor_fluid",
    "extension",
    "belt_stub",
    "belt_straight",
    "belt_turn",
    "pipe_stub",
    "pipe_straight",
    "pipe_turn",
    "route_final",
    "route_candidate",
    "error_overlap",
    "error_unrouted",
    "overlay_hard_protected",
    "overlay_soft_protected",
    "overlay_candidate_corridor",
    "overlay_selected",
    "overlay_hover",
    "overlay_replay_cursor",
  ];

  /** Set by page when external atlas load fails (one-shot warn in template). */
  g.spriteAtlasLoadFailed = false;

  function loadImage(url) {
    return new Promise(function (resolve, reject) {
      var img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = function () {
        resolve(img);
      };
      img.onerror = function () {
        reject(new Error("sprite image load failed"));
      };
      img.src = url;
    });
  }

  function drawFallbackTile(ctx, key, w, h) {
    var fills = {
      empty: "#0f172a",
      mineable_shape: "#334155",
      mineable_fluid: "#0369a1",
      asteroid_shell: "#57534e",
      interior_patch: "#1e293b",
      extractor_shape: "#7c3aed",
      extractor_fluid: "#0ea5e9",
      extension: "#38bdf8",
      belt_stub: "#f59e0b",
      belt_straight: "#22c55e",
      belt_turn: "#16a34a",
      pipe_stub: "#f472b6",
      pipe_straight: "#a855f7",
      pipe_turn: "#9333ea",
      route_final: "#2563eb",
      route_candidate: "#60a5fa",
      error_overlap: "#dc2626",
      error_unrouted: "#f97316",
      overlay_hard_protected: "#991b1b",
      overlay_soft_protected: "#ca8a04",
      overlay_candidate_corridor: "#0891b2",
      overlay_selected: "#facc15",
      overlay_hover: "#fde047",
      overlay_replay_cursor: "#ec4899",
    };
    var fill = fills[key] || "#475569";
    ctx.fillStyle = fill;
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = "rgba(15,23,42,0.45)";
    ctx.lineWidth = 2;
    ctx.strokeRect(1, 1, w - 2, h - 2);
    ctx.fillStyle = "rgba(248,250,252,0.55)";
    ctx.font = "bold 10px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    var label = key.replace(/_/g, " ").slice(0, 3);
    ctx.fillText(label, w / 2, h / 2);
  }

  function createFallbackSpriteAtlas(tileSize) {
    var ts = tileSize || 32;
    var cols = 8;
    var rows = Math.ceil(SPRITE_KEY_ORDER.length / cols);
    var aw = cols * ts;
    var ah = rows * ts;
    var canvas = document.createElement("canvas");
    canvas.width = aw;
    canvas.height = ah;
    var ctx = canvas.getContext("2d");
    var sprites = Object.create(null);
    var i;
    for (i = 0; i < SPRITE_KEY_ORDER.length; i++) {
      var key = SPRITE_KEY_ORDER[i];
      var col = i % cols;
      var row = (i / cols) | 0;
      var x = col * ts;
      var y = row * ts;
      sprites[key] = { x: x, y: y, w: ts, h: ts };
      ctx.save();
      ctx.translate(x, y);
      drawFallbackTile(ctx, key, ts, ts);
      ctx.restore();
    }
    var href = canvas.toDataURL("image/png");
    var manifest = {
      tileSize: ts,
      atlasWidth: aw,
      atlasHeight: ah,
      sprites: sprites,
      entityTypeToSprite: {},
      fallbacks: {},
    };
    return {
      image: canvas,
      href: href,
      manifest: manifest,
      meta: manifest,
    };
  }

  function normalizeLoadedManifest(img, raw) {
    var sprites = raw && raw.sprites ? raw.sprites : null;
    if (!sprites || typeof sprites !== "object") {
      throw new Error("sprite meta missing sprites");
    }
    var manifest = {
      tileSize: raw.tileSize || 32,
      columns: raw.columns,
      sprites: sprites,
      entityTypeToSprite: raw.entityTypeToSprite && typeof raw.entityTypeToSprite === "object"
        ? raw.entityTypeToSprite
        : {},
      fallbacks: raw.fallbacks && typeof raw.fallbacks === "object" ? raw.fallbacks : {},
    };
    var meta = {
      tileSize: manifest.tileSize,
      atlasWidth: img.naturalWidth || img.width,
      atlasHeight: img.naturalHeight || img.height,
      sprites: sprites,
      entityTypeToSprite: manifest.entityTypeToSprite,
      fallbacks: manifest.fallbacks,
    };
    return { manifest: manifest, meta: meta };
  }

  function loadSpriteAtlas(imageUrl, manifestUrl) {
    return Promise.all([
      loadImage(imageUrl),
      fetch(manifestUrl).then(function (r) {
        if (!r.ok) throw new Error("sprite meta http " + r.status);
        return r.json();
      }),
    ]).then(function (pair) {
      var img = pair[0];
      var raw = pair[1];
      var norm = normalizeLoadedManifest(img, raw);
      return {
        image: img,
        manifest: norm.manifest,
        href: imageUrl,
        meta: norm.meta,
      };
    });
  }

  function loadOrCreate(imageUrl, metaUrl) {
    if (!imageUrl || !metaUrl) {
      return Promise.resolve(createFallbackSpriteAtlas(32));
    }
    return loadSpriteAtlas(imageUrl, metaUrl).catch(function () {
      return createFallbackSpriteAtlas(32);
    });
  }

  g.AM_AsteroidMapSpriteAtlas = {
    SPRITE_KEY_ORDER: SPRITE_KEY_ORDER,
    loadImage: loadImage,
    createFallbackSpriteAtlas: createFallbackSpriteAtlas,
    loadSpriteAtlas: loadSpriteAtlas,
    loadOrCreate: loadOrCreate,
  };
})(typeof globalThis !== "undefined" ? globalThis : window);
