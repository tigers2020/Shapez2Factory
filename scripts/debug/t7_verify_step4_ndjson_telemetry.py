#!/usr/bin/env python3
"""[DEPRECATED] Previously verified v1 STEP4 NDJSON telemetry against ``asteroid_mining_layout``.

v1 was removed from the runtime path. Use v2 routing/STEP4 tests under
``tests/unit/shapez_asteroid_v2/`` instead.
"""

from __future__ import annotations

import sys


def main() -> None:
    print(
        "t7_verify_step4_ndjson_telemetry.py: v1 mining layout removed; "
        "see tests/unit/shapez_asteroid_v2/test_step4_routing_contract.py.",
        file=sys.stderr,
    )
    raise SystemExit(2)


if __name__ == "__main__":
    main()
