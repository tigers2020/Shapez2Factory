"""Migrate SQLite and start Django for Playwright visual tests (no reload)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str], *, env: dict[str, str]) -> None:
    if sys.platform == "win32":
        subprocess.run(cmd, check=True, env=env, shell=True)
    else:
        subprocess.run(cmd, check=True, env=env)


def main() -> int:
    os.chdir(ROOT)
    env = os.environ.copy()
    env.setdefault("DJANGO_USE_SQLITE", "1")
    env.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    env.setdefault("PYTHONUNBUFFERED", "1")
    port = env.get("PLAYWRIGHT_DJANGO_PORT", "8765")

    _run(["npm", "run", "build:css"], env=env)
    _run([sys.executable, "manage.py", "migrate", "--noinput"], env=env)
    return subprocess.call(
        [
            sys.executable,
            "manage.py",
            "runserver",
            f"127.0.0.1:{port}",
            "--noreload",
        ],
        env=env,
    )


if __name__ == "__main__":
    raise SystemExit(main())
