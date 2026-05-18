"""Node smoke tests for ``lab_optimization_overlay_accumulator.js`` (cumulative overlay)."""

from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[3]
_JS = _ROOT / "django_apps/web/static/web/js/lab_optimization_overlay_accumulator.js"


@pytest.mark.unit
def test_node_lab_optimization_overlay_accumulator_server_to_raw_lookup() -> None:
    if shutil.which("node") is None:
        pytest.skip("node not on PATH")

    env = os.environ.copy()
    env["LAB_OPT_ACCUM_JS"] = str(_JS)
    script = textwrap.dedent("""
        const fs = require("fs");
        const vm = require("vm");
        const p = process.env.LAB_OPT_ACCUM_JS;
        const ctx = { console, globalThis: {} };
        vm.createContext(ctx);
        vm.runInContext(fs.readFileSync(p, "utf8"), ctx);
        const A = ctx.globalThis.LabOptimizationOverlayAccumulator;
        const rows = [{ x: 1, y: 0 }, { x: 3, y: 0 }];
        const r = A.serverToRawWorld(0, 0, 2, 0, rows);
        if (r.x !== 3 || r.y !== 0) process.exit(2);
        process.exit(0);
        """)
    subprocess.run(["node", "-e", script], check=True, env=env)


@pytest.mark.unit
def test_node_cell_to_raw_world_uses_xy_only_ignores_server_metadata() -> None:
    if shutil.which("node") is None:
        pytest.skip("node not on PATH")

    env = os.environ.copy()
    env["LAB_OPT_ACCUM_JS"] = str(_JS)
    script = textwrap.dedent("""
        const fs = require("fs");
        const vm = require("vm");
        const p = process.env.LAB_OPT_ACCUM_JS;
        const ctx = { console, globalThis: {} };
        vm.createContext(ctx);
        vm.runInContext(fs.readFileSync(p, "utf8"), ctx);
        const A = ctx.globalThis.LabOptimizationOverlayAccumulator;
        const w = A.cellToRawWorld({
          x: 1,
          y: 0,
          server_x: 999,
          server_y: 888,
          cell_kind: "optimization_overlay",
        });
        if (!w || w.x !== 1 || w.y !== 0) process.exit(11);
        process.exit(0);
        """)
    subprocess.run(["node", "-e", script], check=True, env=env)


@pytest.mark.unit
def test_node_cumulative_overlay_retains_first_candidate_cells() -> None:
    if shutil.which("node") is None:
        pytest.skip("node not on PATH")

    env = os.environ.copy()
    env["LAB_OPT_ACCUM_JS"] = str(_JS)
    script = textwrap.dedent("""
        const fs = require("fs");
        const vm = require("vm");
        const p = process.env.LAB_OPT_ACCUM_JS;
        const ctx = { console, globalThis: {} };
        vm.createContext(ctx);
        vm.runInContext(fs.readFileSync(p, "utf8"), ctx);
        const A = ctx.globalThis.LabOptimizationOverlayAccumulator;
        const garbageAnchor = [{ x: 99999, y: 99999 }];
        function resolve(c) {
          const k = c.x + "," + c.y;
          if (k === "1,0") return 10;
          if (k === "3,0") return 20;
          return null;
        }
        const mk = (et, cells) => ({
          phase: "optimization",
          frame_key: "optimization_00_x",
          event_type: et,
          cell_overlay_json: {
            cells: cells.map((c) =>
              Object.assign({ cell_kind: "optimization_overlay", severity: "info" }, c),
            ),
          },
        });
        const frames = [
          { phase: "decode", frame_key: "reconstruction_x" },
          mk("candidate.generated", [{ x: 1, y: 0, overlay_role: "candidate_occupied" }]),
          mk("route_probe.succeeded", [{ x: 3, y: 0, overlay_role: "route_path" }]),
        ];
        const out = A.projectCumulative(frames, 0, 2, resolve, garbageAnchor);
        const by = new Map(out.directives.map((d) => [d.domIndex, d]));
        if (!by.get(10) || by.get(10).status !== "active") process.exit(3);
        if (!by.get(20) || by.get(20).roles.has("route_path") !== true) process.exit(4);
        process.exit(0);
        """)
    subprocess.run(["node", "-e", script], check=True, env=env)


@pytest.mark.unit
def test_node_rejected_marks_only_reject_frame_cells() -> None:
    if shutil.which("node") is None:
        pytest.skip("node not on PATH")

    env = os.environ.copy()
    env["LAB_OPT_ACCUM_JS"] = str(_JS)
    script = textwrap.dedent("""
        const fs = require("fs");
        const vm = require("vm");
        const p = process.env.LAB_OPT_ACCUM_JS;
        const ctx = { console, globalThis: {} };
        vm.createContext(ctx);
        vm.runInContext(fs.readFileSync(p, "utf8"), ctx);
        const A = ctx.globalThis.LabOptimizationOverlayAccumulator;
        function resolve(c) {
          const k = c.x + "," + c.y;
          if (k === "1,0") return 10;
          if (k === "3,0") return 20;
          return null;
        }
        const mk = (et, cells) => ({
          phase: "optimization",
          frame_key: "optimization_00_x",
          event_type: et,
          cell_overlay_json: {
            cells: cells.map((c) =>
              Object.assign({ cell_kind: "optimization_overlay", severity: "info" }, c),
            ),
          },
        });
        const frames = [
          { phase: "decode", frame_key: "reconstruction_x" },
          mk("candidate.generated", [{ x: 1, y: 0, overlay_role: "candidate_occupied" }]),
          mk("candidate.generated", [{ x: 3, y: 0, overlay_role: "candidate_occupied" }]),
          mk("candidate.rejected", [{ x: 3, y: 0, overlay_role: "candidate_occupied" }]),
        ];
        const out = A.projectCumulative(frames, 0, 3, resolve, []);
        const by = new Map(out.directives.map((d) => [d.domIndex, d]));
        if (by.get(10).status !== "active") process.exit(5);
        if (by.get(20).status !== "rejected") process.exit(6);
        process.exit(0);
        """)
    subprocess.run(["node", "-e", script], check=True, env=env)


@pytest.mark.unit
def test_node_rolled_back_overlays_previous_committed_tone() -> None:
    if shutil.which("node") is None:
        pytest.skip("node not on PATH")

    env = os.environ.copy()
    env["LAB_OPT_ACCUM_JS"] = str(_JS)
    script = textwrap.dedent("""
        const fs = require("fs");
        const vm = require("vm");
        const p = process.env.LAB_OPT_ACCUM_JS;
        const ctx = { console, globalThis: {} };
        vm.createContext(ctx);
        vm.runInContext(fs.readFileSync(p, "utf8"), ctx);
        const A = ctx.globalThis.LabOptimizationOverlayAccumulator;
        function resolve(c) {
          return c.x === 1 && c.y === 0 ? 10 : null;
        }
        const mk = (et, cells) => ({
          phase: "optimization",
          frame_key: "optimization_00_x",
          event_type: et,
          cell_overlay_json: {
            cells: cells.map((c) =>
              Object.assign({ cell_kind: "optimization_overlay", severity: "info" }, c),
            ),
          },
        });
        const frames = [
          { phase: "decode", frame_key: "reconstruction_x" },
          mk("route.committed", [{ x: 1, y: 0, overlay_role: "route_path" }]),
          mk("route.rolled_back", [{ x: 1, y: 0, overlay_role: "route_path" }]),
        ];
        const out = A.projectCumulative(frames, 0, 2, resolve, []);
        const d = out.directives[0];
        if (d.domIndex !== 10 || d.status !== "rolled_back") process.exit(7);
        process.exit(0);
        """)
    subprocess.run(["node", "-e", script], check=True, env=env)
