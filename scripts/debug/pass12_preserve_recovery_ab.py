#!/usr/bin/env python3
"""[DEPRECATED] Previously ran v1 ``asteroid_mining_layout`` Pass12 preserve A/B experiments.

v1 runtime imports were removed. Use ``tests/unit/shapez_asteroid_v2/`` and
``django_apps.shapez_asteroid.services.asteroid_mining_layout_v2`` for current work.
Historical procedure notes remain in ``documents/ai/pass12_telemetry_policy_note_2026-05-11.md``.
"""

from __future__ import annotations

import sys


def main() -> None:
    print(
        "pass12_preserve_recovery_ab.py: v1 mining layout package removed; "
        "see asteroid_mining_layout_v2 and tests/unit/shapez_asteroid_v2/.",
        file=sys.stderr,
    )
    raise SystemExit(2)


if __name__ == "__main__":
    main()
