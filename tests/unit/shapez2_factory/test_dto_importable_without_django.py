"""PR-CLI-2a Step 4 — moved DTOs import in a Django-free subprocess (BA-1).

Each relocated core module must import with ``DJANGO_SETTINGS_MODULE`` unset and without pulling any
``django`` module into ``sys.modules``.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

_MOVED_MODULES = [
    "shapez2_factory.domain.asteroid_lab.grid_contract",
    "shapez2_factory.domain.asteroid_lab.coord_frames",
    "shapez2_factory.domain.asteroid_lab.game_data_snapshot",
    "shapez2_factory.domain.asteroid_lab.game_data_snapshot_provenance",
    "shapez2_factory.domain.asteroid_lab.building_catalog_slice",
    "shapez2_factory.domain.asteroid_lab.building_catalog_slice_hash",
]


@pytest.mark.parametrize("module", _MOVED_MODULES)
def test_moved_dto_imports_without_django(module: str) -> None:
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE"}
    code = (
        "import sys\n"
        f"import {module}\n"
        "leaked = sorted(m for m in sys.modules if m == 'django' or m.startswith('django.'))\n"
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
