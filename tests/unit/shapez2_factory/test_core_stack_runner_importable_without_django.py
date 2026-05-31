"""PR-CLI-2e Step 2 — core ``stack_runner`` imports in a Django-free subprocess (BA-1).

The relocated core orchestrator must import with ``DJANGO_SETTINGS_MODULE`` unset and without
pulling any ``django`` module into ``sys.modules``.
"""

from __future__ import annotations

import os
import subprocess
import sys


def test_core_stack_runner_does_not_import_django() -> None:
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE"}
    code = (
        "import sys\n"
        "import shapez2_factory.application.asteroid_lab.stack_runner as m\n"
        "assert hasattr(m, 'run_layers_02_to_06'), 'run_layers_02_to_06 missing'\n"
        "assert hasattr(m, 'CoreStackRunResult'), 'CoreStackRunResult missing'\n"
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
