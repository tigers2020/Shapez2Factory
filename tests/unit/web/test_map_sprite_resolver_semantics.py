"""Contract: mineable / asteroid_field rows must not resolve as interior_patch."""

from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_map_sprite_resolver_js_source_checks_layout_kind_before_inferred() -> None:
    path = (
        _repo_root()
        / "django_apps"
        / "web"
        / "static"
        / "web"
        / "asteroid_optimizer"
        / "js"
        / "map_sprite_resolver.js"
    )
    text = path.read_text(encoding="utf-8")
    start = text.find("function semanticTerrainKey")
    assert start != -1
    sub = text[start : start + 1200]
    pos_af = sub.find('lk === "asteroid_field"')
    pos_m = sub.find('role === "mineable"')
    pos_inf = sub.find('role === "inferred"')
    assert pos_af != -1 and pos_inf != -1
    assert pos_af < pos_inf
    assert pos_m != -1
    assert pos_af < pos_m < pos_inf


def test_map_sprite_resolver_runtime_semantics_via_node() -> None:
    node = shutil.which("node")
    if node is None:
        import pytest

        pytest.skip("node not on PATH")
    root = _repo_root()
    js_path = root / "django_apps/web/static/web/asteroid_optimizer/js/map_sprite_resolver.js"
    script = textwrap.dedent(f"""
        const fs = require("fs");
        const vm = require("vm");
        const code = fs.readFileSync({json.dumps(str(js_path))}, "utf8");
        const sandbox = {{}};
        sandbox.globalThis = sandbox;
        vm.createContext(sandbox);
        vm.runInContext(code, sandbox);
        const R = sandbox.AM_AsteroidMapSpriteResolver;
        function k(row) {{
          return R.semanticTerrainKey(row, null, {{}});
        }}
        const cases = [
          [{{ role: "inferred", layout_kind: "asteroid_field", surface: "shape" }},
            "mineable_shape"],
          [{{ role: "inferred", layout_kind: "asteroid_field", surface: "fluid" }},
            "mineable_fluid"],
          [{{ role: "inferred", surface: "shape" }}, "interior_patch"],
          [{{ role: "mineable", surface: "shape" }}, "mineable_shape"],
          [{{ role: "mineable", surface: "fluid" }}, "mineable_fluid"],
        ];
        for (const [row, want] of cases) {{
          const got = k(row);
          if (got !== want) {{
            console.error("want", want, "got", got, "row", JSON.stringify(row));
            process.exit(1);
          }}
        }}
        """)
    proc = subprocess.run(
        [node, "-e", script],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
