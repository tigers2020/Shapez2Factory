/**
 * Pure helpers for Lab optimization overlay: server→raw projection (with baseline lookup)
 * and cumulative replay state for frames ``anchorIndex < i <= endIndex``.
 *
 * Loaded before ``asteroid_miner_layout_lab.js``; attaches ``globalThis.LabOptimizationOverlayAccumulator``.
 */
(function (g) {
  "use strict";

  function rawXToDenseX(x) {
    var xi = Math.trunc(Number(x));
    if (!Number.isFinite(xi) || xi === 0) return null;
    if (xi < 0) return Math.floor((xi + 1) / 2);
    return Math.floor((xi - 1) / 2) + 1;
  }

  function serverXYFromRaw(rx, ry, maxDx, minY) {
    var d = rawXToDenseX(rx);
    if (d == null) return null;
    return [maxDx - d, ry - minY];
  }

  function labRowXY(row) {
    if (!row || typeof row !== "object") return null;
    if (row.x != null && row.y != null) return [Number(row.x), Number(row.y)];
    if (row.X != null && row.Y != null) return [Number(row.X), Number(row.Y)];
    return null;
  }

  function serverToRawWorld(sx, sy, maxDx, minY, labRows) {
    var rawY = sy + minY;
    var tSx = Number(sx);
    var tSy = Number(sy);
    var i, pair, rx, ry, sp, d;
    if (Array.isArray(labRows) && labRows.length) {
      for (i = 0; i < labRows.length; i++) {
        pair = labRowXY(labRows[i]);
        if (!pair) continue;
        rx = pair[0];
        ry = pair[1];
        if (!Number.isFinite(rx) || !Number.isFinite(ry) || rx === 0) continue;
        sp = serverXYFromRaw(rx, ry, maxDx, minY);
        if (sp && sp[0] === tSx && sp[1] === tSy) {
          return { x: rx, y: ry };
        }
      }
    }
    d = maxDx - tSx;
    return { x: 2 * d - 1, y: rawY };
  }

  function metricSource(frame) {
    if (!frame || typeof frame !== "object") return {};
    var s = frame.metric_snapshot_json || frame.summary;
    if (s && typeof s === "object") return s;
    var p = frame.frame_payload;
    if (p && typeof p === "object") {
      var mj = p.metrics_json;
      if (mj && typeof mj === "object") return mj;
    }
    return {};
  }

  function serverXYParamsFromFrame(frame) {
    var m = metricSource(frame);
    var p = m.server_xy_params;
    if (Array.isArray(p) && p.length >= 2) {
      return [Number(p[0]), Number(p[1])];
    }
    var a = m.lab_projection_max_dense_x;
    var b = m.lab_projection_min_raw_y;
    if (Number.isFinite(a) && Number.isFinite(b)) {
      return [a, b];
    }
    return null;
  }

  function cellOverlayFromFrame(frame) {
    if (!frame || typeof frame !== "object") return null;
    var top = frame.cell_overlay_json;
    if (top && typeof top === "object") return top;
    var fp = frame.frame_payload;
    if (fp && typeof fp === "object" && fp.cell_overlay_json && typeof fp.cell_overlay_json === "object") {
      return fp.cell_overlay_json;
    }
    return null;
  }

  function cellToRawWorld(cell, params, labRows) {
    if (!cell || typeof cell !== "object") return null;
    if (cell.lab_world_x != null && cell.lab_world_y != null) {
      return { x: Number(cell.lab_world_x), y: Number(cell.lab_world_y) };
    }
    var sx = cell.server_x != null ? Number(cell.server_x) : null;
    var sy = cell.server_y != null ? Number(cell.server_y) : null;
    if (sx != null && sy != null && params) {
      return serverToRawWorld(sx, sy, params[0], params[1], labRows);
    }
    var x = Number(cell.x);
    var y = Number(cell.y);
    if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
    var ck = cell.cell_kind != null ? String(cell.cell_kind) : "";
    if (params && ck === "optimization_overlay") {
      return serverToRawWorld(x, y, params[0], params[1], labRows);
    }
    return { x: x, y: y };
  }

  function overlayTargets(overlay) {
    var out = [];
    if (!overlay || typeof overlay !== "object" || !Array.isArray(overlay.cells)) return out;
    for (var i = 0; i < overlay.cells.length; i++) {
      var c = overlay.cells[i];
      if (!c || typeof c !== "object") continue;
      var role = c.overlay_role != null ? String(c.overlay_role) : "";
      out.push({ cell: c, role: role ? role.toLowerCase() : "" });
    }
    return out;
  }

  function eventTypeOf(frame) {
    if (!frame || typeof frame !== "object") return "";
    if (frame.event_type != null) return String(frame.event_type);
    var p = frame.frame_payload;
    if (p && p.event_type != null) return String(p.event_type);
    return "";
  }

  function isOptimizationLabFrame(fr) {
    if (!fr || typeof fr !== "object") return false;
    var ph = fr.phase != null ? String(fr.phase) : "";
    if (ph === "optimization") return true;
    var fk = fr.frame_key != null ? String(fr.frame_key) : "";
    return fk.indexOf("optimization_") === 0;
  }

  function labOptimizationOverlaySeverityRank(s) {
    var x = s != null ? String(s).toLowerCase() : "info";
    if (x === "error") return 3;
    if (x === "warn") return 2;
    return 1;
  }

  function labOptimizationMergeSeverity(a, b) {
    return labOptimizationOverlaySeverityRank(a) >= labOptimizationOverlaySeverityRank(b) ? a : b;
  }

  function labOptClassesForEntry(roles, severity, status) {
    var parts = ["lab-opt-cell-slot"];
    if (roles.has("candidate_occupied")) {
      parts.push("lab-opt-candidate-occupied");
    }
    if (roles.has("output_stub")) {
      parts.push("lab-opt-output-stub");
    }
    if (roles.has("route_path")) {
      parts.push("lab-opt-route-path");
    }
    var st = status != null ? String(status).toLowerCase() : "active";
    if (st === "committed") {
      parts.push("lab-opt-status-committed");
    } else if (st === "rejected") {
      parts.push("lab-opt-status-rejected");
    } else if (st === "rolled_back") {
      parts.push("lab-opt-status-rolled-back");
    } else if (st === "probe_failed") {
      parts.push("lab-opt-status-probe-failed");
    }
    var s = severity != null ? String(severity).toLowerCase() : "info";
    if (s === "error") {
      parts.push("lab-opt-severity-error");
    } else if (s === "warn") {
      parts.push("lab-opt-severity-warn");
    }
    return parts.join(" ");
  }

  function projectCumulative(frames, anchorIndex, endIndex, resolveCellIndex, anchorLabRows) {
    var diagnostics = { dropped: 0, reasons: [] };
    if (!Array.isArray(frames) || endIndex < 0) {
      return { directives: [], diagnostics: diagnostics };
    }
    var labRows = Array.isArray(anchorLabRows) ? anchorLabRows : [];
    var cellState = new Map();

    var fallbackParams = null;
    var fj;
    for (fj = anchorIndex + 1; fj <= endIndex; fj++) {
      var p0 = serverXYParamsFromFrame(frames[fj]);
      if (p0) {
        fallbackParams = p0;
        break;
      }
    }

    for (var fi = anchorIndex + 1; fi <= endIndex; fi++) {
      var fr = frames[fi];
      if (!isOptimizationLabFrame(fr)) continue;
      var params = serverXYParamsFromFrame(fr) || fallbackParams;
      var evt = eventTypeOf(fr);
      var overlay = cellOverlayFromFrame(fr);
      var targets = overlayTargets(overlay);
      var bump = null;
      if (evt === "candidate.rejected") bump = "rejected";
      else if (evt === "route.rolled_back") bump = "rolled_back";
      else if (evt === "route.committed") bump = "committed";
      else if (evt === "route_probe.failed") bump = "probe_failed";

      var ti, t, raw, idx, row, sev, role;
      for (ti = 0; ti < targets.length; ti++) {
        t = targets[ti];
        raw = params ? cellToRawWorld(t.cell, params, labRows) : cellToRawWorld(t.cell, null, labRows);
        if (!raw || !Number.isFinite(raw.x) || !Number.isFinite(raw.y)) {
          diagnostics.dropped += 1;
          continue;
        }
        idx = resolveCellIndex({ x: raw.x, y: raw.y });
        if (idx == null) {
          diagnostics.dropped += 1;
          continue;
        }
        sev = t.cell && t.cell.severity != null ? String(t.cell.severity) : "info";
        role = t.role || (t.cell && t.cell.overlay_role != null ? String(t.cell.overlay_role) : "");
        role = role ? role.toLowerCase() : "";
        row = cellState.get(idx);
        if (!row) {
          row = { roles: new Set(), severity: "info", status: "active" };
          cellState.set(idx, row);
        }
        if (role) {
          row.roles.add(role);
        }
        row.severity = labOptimizationMergeSeverity(row.severity, sev);
        if (bump) {
          row.status = bump;
        }
      }
    }

    if (diagnostics.dropped > 0) {
      diagnostics.reasons.push("missing_or_oob_coord");
    }
    var directives = [];
    cellState.forEach(function (row, domIndex) {
      directives.push({
        domIndex: domIndex,
        roles: row.roles,
        severity: row.severity,
        status: row.status,
        className: labOptClassesForEntry(row.roles, row.severity, row.status),
      });
    });
    directives.sort(function (a, b) {
      return a.domIndex - b.domIndex;
    });
    return { directives: directives, diagnostics: diagnostics };
  }

  g.LabOptimizationOverlayAccumulator = {
    projectCumulative: projectCumulative,
    cellToRawWorld: cellToRawWorld,
    serverXYParamsFromFrame: serverXYParamsFromFrame,
    serverToRawWorld: serverToRawWorld,
    eventTypeOf: eventTypeOf,
  };
})(typeof globalThis !== "undefined" ? globalThis : this);
