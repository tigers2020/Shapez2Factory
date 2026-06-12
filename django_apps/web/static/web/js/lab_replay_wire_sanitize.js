/**
 * Read-path replay wire sanitizer (candidate compat) and committed-cell audit.
 * Mirrors django_apps/asteroid_lab/replay/replay_wire_read_sanitize.py
 */
(function (global) {
  "use strict";

  var CANDIDATE_OUTPUT_HINT_KINDS = {
    candidate_miner: 1,
    candidate_transport_stub: 1,
    candidate_route_path: 1,
    route_probe_path: 1,
  };

  var BANNED_CANDIDATE_OCCUPANCY = {
    space_belt: 1,
    space_pipe: 1,
    shape_belt: 1,
    fluid_pipe: 1,
    shape: 1,
    fluid: 1,
    belt: 1,
    pipe: 1,
  };

  var BANNED_LEGACY_COMMITTED_TRANSPORT = {
    shape_belt: 1,
    fluid_pipe: 1,
    shape: 1,
    fluid: 1,
    belt: 1,
    pipe: 1,
  };

  var COMMITTED_TRANSPORT_KINDS = { space_belt: 1, space_pipe: 1 };

  function normalizeProjectTransportKind(raw) {
    if (
      typeof LabEffectiveCellView !== "undefined" &&
      LabEffectiveCellView.normalizeProjectTransportKind
    ) {
      return LabEffectiveCellView.normalizeProjectTransportKind(raw);
    }
    var value = String(raw || "")
      .trim()
      .toLowerCase();
    if (!value || value === "none") {
      return "none";
    }
    if (
      value === "shape_belt" ||
      value === "belt" ||
      value === "shape" ||
      value === "space_belt"
    ) {
      return "space_belt";
    }
    if (
      value === "fluid_pipe" ||
      value === "pipe" ||
      value === "fluid" ||
      value === "space_pipe"
    ) {
      return "space_pipe";
    }
    return "none";
  }

  function wireKind(cell) {
    if (!cell) {
      return "";
    }
    if (cell.kind != null && String(cell.kind) !== "") {
      return String(cell.kind);
    }
    if (cell.cell_kind != null && String(cell.cell_kind) !== "") {
      return String(cell.cell_kind);
    }
    return "";
  }

  function wireTransport(cell) {
    if (!cell) {
      return "";
    }
    if (cell.transport != null && String(cell.transport) !== "") {
      return String(cell.transport);
    }
    if (cell.transport_kind != null && String(cell.transport_kind) !== "") {
      return String(cell.transport_kind);
    }
    return "";
  }

  function isCandidateOutputHintKind(kind) {
    return CANDIDATE_OUTPUT_HINT_KINDS[String(kind || "")] === 1;
  }

  function auditReplayWireCell(cell) {
    var kind = wireKind(cell);
    var transport = wireTransport(cell).trim().toLowerCase();
    if (isCandidateOutputHintKind(kind)) {
      if (BANNED_CANDIDATE_OCCUPANCY[transport]) {
        throw new Error("candidate overlay must not claim transport=" + transport);
      }
      return;
    }
    if (COMMITTED_TRANSPORT_KINDS[kind] && BANNED_LEGACY_COMMITTED_TRANSPORT[transport]) {
      throw new Error("committed transport invalid transport=" + transport);
    }
  }

  function sanitizeReplayWireCellForRead(cell) {
    if (!cell || typeof cell !== "object") {
      return cell;
    }
    var out = Object.assign({}, cell);
    var kind = wireKind(out);
    if (!isCandidateOutputHintKind(kind)) {
      return out;
    }
    var transport = wireTransport(out).trim().toLowerCase();
    if (!BANNED_CANDIDATE_OCCUPANCY[transport]) {
      auditReplayWireCell(out);
      return out;
    }
    var normalized = normalizeProjectTransportKind(transport);
    if (normalized === "none") {
      auditReplayWireCell(out);
      return out;
    }
    out.transport = "none";
    out.transport_kind = "none";
    var existing = out.output_transport_kind != null ? String(out.output_transport_kind).trim() : "";
    if (!existing || normalizeProjectTransportKind(existing) === "none") {
      out.output_transport_kind = normalized;
    }
    return out;
  }

  function cellKey(x, y, layer) {
    if (layer != null && layer !== 0) {
      return String(layer) + ":" + String(x) + "," + String(y);
    }
    return String(x) + "," + String(y);
  }

  global.LabReplayWireSanitize = {
    auditReplayWireCell: auditReplayWireCell,
    cellKey: cellKey,
    isCandidateOutputHintKind: isCandidateOutputHintKind,
    sanitizeReplayWireCellForRead: sanitizeReplayWireCellForRead,
  };
})(typeof window !== "undefined" ? window : globalThis);
