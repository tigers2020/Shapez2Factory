#!/usr/bin/env python
"""Export frozen genetic_sample_seeds.json for asteroid_golden fixtures.

Regenerate::

    python scripts/export_golden_gene_seeds_fixture.py

Requires Django (runs ``seed_miner_patterns`` then serializes GeneSeed rows).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_OUT = _REPO / "tests" / "fixtures" / "asteroid_golden" / "genetic_sample_seeds.json"


def main() -> int:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    sys.path.insert(0, str(_REPO))

    import django

    django.setup()

    from django.core.management import call_command

    from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import MINER_SEED_SCHEMA_V2
    from django_apps.asteroid_lab.models import GeneSeed
    from django_apps.asteroid_lab.services.genetic_sample_catalog_snapshot import (
        build_genetic_sample_seed_snapshot,
    )

    call_command("seed_miner_patterns", verbosity=0)
    payload = build_genetic_sample_seed_snapshot(
        GeneSeed.objects.filter(metadata_json__schema=MINER_SEED_SCHEMA_V2),
    )
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {_OUT} ({len(payload.get('entries', []))} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
