"""Print live Lab page URL after create + solver run (for Playwright capture)."""

from __future__ import annotations

import base64
import gzip
import json
import os
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _unique_valid_copy() -> str:
    root = {
        "V": random.randint(1, 10_000_000),
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
            ],
        },
    }
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    return f"SHAPEZ2-4-{base64.b64encode(gzip.compress(text)).decode('ascii')}"


def main() -> int:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    import django

    django.setup()

    from django.conf import settings
    from django.test import Client, override_settings
    from django.urls import reverse

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    settings.ASTEROID_LAB_REPLAY_PAYLOAD_MODE = "inline"
    client = Client()
    with override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="inline"):
        create_resp = client.post(
            reverse("web:asteroid-miner-layout-projects-create"),
            {"copy_code": _unique_valid_copy()},
            HTTP_ACCEPT="application/json",
        )
        if create_resp.status_code != 200:
            print(create_resp.content.decode(), file=sys.stderr)
            return 1
        slug = json.loads(create_resp.content.decode())["project_slug"]
        run_url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
        run_resp = client.post(run_url, HTTP_ACCEPT="application/json")
        if run_resp.status_code != 200:
            print(run_resp.content.decode(), file=sys.stderr)
            return 1
        page_path = reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug})
    print(f"{base_url.rstrip('/')}{page_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
