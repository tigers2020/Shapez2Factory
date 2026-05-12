from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_build_locale_ko_strict_exits_zero() -> None:
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "build_locale_ko.py"
    r = subprocess.run(
        [sys.executable, str(script), "--strict"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
