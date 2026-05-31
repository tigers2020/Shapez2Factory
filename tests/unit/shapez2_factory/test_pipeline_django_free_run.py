"""PR-CLI-2f Step 2 (tests-first) ??full decode?’cleanup?’reconstruction runs Django-free (3b prereq).

This is the prerequisite that unblocks PR-CLI-3b's "no Django required" full CLI run: the relocated
core pipeline must execute end-to-end (copy string ??``ReconstructionResult``) in a subprocess with
``DJANGO_SETTINGS_MODULE`` unset and without importing any ``django`` module.

RED until PR-CLI-2f Step 4: the core modules do not exist yet.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_FIXTURE = _REPO / "tests" / "fixtures" / "asteroid_lab" / "reconstruction_required_.txt"


def test_full_pipeline_runs_without_django() -> None:
    assert _FIXTURE.is_file(), f"fixture missing: {_FIXTURE}"
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE"}
    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "from shapez2_factory.domain.asteroid_lab.reconstruction.topology_contract import "
        "decode_shapez_copy_string\n"
        "from shapez2_factory.domain.asteroid_lab.cleanup.pipeline import deconstruct_snapshot\n"
        "from shapez2_factory.domain.asteroid_lab.reconstruction.pipeline import "
        "run_topology_reconstruction\n"
        f"line = Path(r'{_FIXTURE}').read_text(encoding='utf-8').splitlines()[0].strip()\n"
        "snap = decode_shapez_copy_string(line)\n"
        "cleanup = deconstruct_snapshot(snap)\n"
        "recon = run_topology_reconstruction(cleanup)\n"
        "assert recon is not None\n"
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
