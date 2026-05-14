/**
 * Sprite tile: canvas drawImage + SVG atlas crop (viewBox).
 * globalThis.AM_AsteroidMapSpriteRenderer
 */
(function (g) {
  "use strict";

  var XLINK = "http://www.w3.org/1999/xlink";

  function frameFor(atlas, spriteKey) {
    if (!atlas || !atlas.meta || !atlas.meta.sprites) return null;
    return atlas.meta.sprites[spriteKey] || null;
  }

  /**
   * @param {CanvasRenderingContext2D} ctx
   * @param {{ image: HTMLImageElement|HTMLCanvasElement, meta: { sprites: object } }} atlas
   * @param {string} spriteKey
   * @param {number} px
   * @param {number} py
   * @param {number} size
   * @param {number} rotationDeg
   * @param {number} [opacity]
   */
  function drawSpriteTile(ctx, atlas, spriteKey, px, py, size, rotationDeg, opacity) {
    if (!ctx) return false;
    var frame = frameFor(atlas, spriteKey);
    if (!frame) return false;
    var img = atlas.image;
    if (!img) return false;
    ctx.save();
    ctx.imageSmoothingEnabled = false;
    var op = opacity != null ? opacity : 1;
    if (op !== 1) ctx.globalAlpha = op;
    var mid = px + size / 2;
    var midy = py + size / 2;
    var rot = rotationDeg || 0;
    ctx.translate(mid, midy);
    ctx.rotate((rot * Math.PI) / 180);
    ctx.translate(-size / 2, -size / 2);
    ctx.drawImage(img, frame.x, frame.y, frame.w, frame.h, 0, 0, size, size);
    ctx.restore();
    return true;
  }

  function appendSvgSpriteTile(parent, svgNs, atlas, spriteKey, x0, y0, size, rotationDeg, opts) {
    var o = opts || {};
    if (!atlas || !atlas.meta || !atlas.meta.sprites) return false;
    var frame = atlas.meta.sprites[spriteKey];
    if (!frame) return false;
    var href = atlas.href || (atlas.image && atlas.image.toDataURL ? atlas.image.toDataURL("image/png") : "");
    if (!href) return false;

    var gEl = document.createElementNS(svgNs, "g");
    if (o.className) {
      gEl.setAttribute("class", o.className);
    }
    var op = o.opacity;
    if (op != null && op !== "") {
      gEl.setAttribute("opacity", String(op));
    }

    var mid = x0 + size / 2;
    var midy = y0 + size / 2;
    var rot = rotationDeg || 0;
    if (rot) {
      gEl.setAttribute(
        "transform",
        "translate(" +
          mid +
          "," +
          midy +
          ") rotate(" +
          rot +
          ") translate(" +
          -size / 2 +
          "," +
          -size / 2 +
          ")"
      );
      x0 = 0;
      y0 = 0;
    } else {
      gEl.setAttribute("transform", "translate(" + x0 + "," + y0 + ")");
      x0 = 0;
      y0 = 0;
    }

    var inner = document.createElementNS(svgNs, "svg");
    inner.setAttribute("x", String(x0));
    inner.setAttribute("y", String(y0));
    inner.setAttribute("width", String(size));
    inner.setAttribute("height", String(size));
    inner.setAttribute("viewBox", frame.x + " " + frame.y + " " + frame.w + " " + frame.h);
    inner.setAttribute("preserveAspectRatio", "none");

    var im = document.createElementNS(svgNs, "image");
    var aw = atlas.meta.atlasWidth || frame.w;
    var ah = atlas.meta.atlasHeight || frame.h;
    im.setAttribute("width", String(aw));
    im.setAttribute("height", String(ah));
    im.setAttribute("href", href);
    im.setAttributeNS(XLINK, "xlink:href", href);
    im.setAttribute("style", "image-rendering: pixelated; image-rendering: crisp-edges;");
    inner.appendChild(im);
    gEl.appendChild(inner);

    if (o.stroke) {
      var border = document.createElementNS(svgNs, "rect");
      border.setAttribute("x", String(x0));
      border.setAttribute("y", String(y0));
      border.setAttribute("width", String(size));
      border.setAttribute("height", String(size));
      border.setAttribute("fill", "none");
      border.setAttribute("stroke", o.stroke);
      border.setAttribute("stroke-width", o.strokeWidth != null ? String(o.strokeWidth) : "0.12");
      border.setAttribute("rx", "0.06");
      border.setAttribute("ry", "0.06");
      gEl.appendChild(border);
    }

    if (o.titleText) {
      var tt = document.createElementNS(svgNs, "title");
      tt.textContent = o.titleText;
      gEl.appendChild(tt);
    }

    parent.appendChild(gEl);
    return true;
  }

  function appendSvgSpriteOverlays(parent, svgNs, atlas, spriteKeys, x0, y0, size, rotationDeg, opts) {
    if (!Array.isArray(spriteKeys) || !spriteKeys.length) return;
    var i;
    for (i = 0; i < spriteKeys.length; i++) {
      var k = spriteKeys[i];
      if (!k) continue;
      appendSvgSpriteTile(parent, svgNs, atlas, k, x0, y0, size, rotationDeg, opts);
    }
  }

  g.AM_AsteroidMapSpriteRenderer = {
    drawSpriteTile: drawSpriteTile,
    appendSvgSpriteTile: appendSvgSpriteTile,
    appendSvgSpriteOverlays: appendSvgSpriteOverlays,
  };
})(typeof globalThis !== "undefined" ? globalThis : window);
