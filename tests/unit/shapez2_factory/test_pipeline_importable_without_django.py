"""PR-CLI-2f Step 2 (tests-first) — core decode/cleanup/reconstruction import Django-free (BA-1).

These modules do not exist yet (they are relocated from ``django_apps`` in PR-CLI-2f Step 4), so this
test is RED until the move lands. After the move it proves the relocated pipeline imports with
``DJANGO_SETTINGS_MODULE`` unset and pulls **no** ``django`` module into ``sys.modules``.

Target core module paths are fixed by the PR-CLI-2f plan
(``docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-2f-decode-cleanup-reconstruction-move.md``).
"""

from __future__ import annotations

import os
import subprocess
import sys

_CORE_PIPELINE_MODULES = (
    "shapez2_factory.domain.asteroid_lab.copy_decode",
    "shapez2_factory.domain.asteroid_lab.normalization",
    "shapez2_factory.domain.asteroid_lab.decoded_blueprint_snapshot",
    "shapez2_factory.domain.asteroid_lab.cell_classifier",
    "shapez2_factory.domain.asteroid_lab.copy_json_coords",
    "shapez2_factory.domain.asteroid_lab.cleanup.pipeline",
    "shapez2_factory.domain.asteroid_lab.reconstruction.pipeline",
    "shapez2_factory.domain.asteroid_lab.reconstruction.confidence",
    "shapez2_factory.domain.asteroid_lab.reconstruction.fill",
    "shapez2_factory.domain.asteroid_lab.reconstruction.flood_fill",
    "shapez2_factory.domain.asteroid_lab.reconstruction.island",
    "shapez2_factory.domain.asteroid_lab.reconstruction.perimeter_closing",
    "shapez2_factory.domain.asteroid_lab.reconstruction.shell",
    "shapez2_factory.domain.asteroid_lab.reconstruction.trace",
    "shapez2_factory.domain.asteroid_lab.reconstruction.topology_contract",
)


def test_core_pipeline_imports_without_django() -> None:
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE"}
    imports = "\n".join(f"import {m}" for m in _CORE_PIPELINE_MODULES)
    code = (
        "import sys\n"
        f"{imports}\n"
        "leaked = sorted(x for x in sys.modules if x == 'django' or x.startswith('django.'))\n"
        "assert not leaked, leaked\n"
        "print('OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "OK" in result.stdout
