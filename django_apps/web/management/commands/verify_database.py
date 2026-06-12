"""One-shot connectivity check for Render / DATABASE_URL troubleshooting."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):  # type: ignore[misc]
    help = (
        "Open the default database connection and print vendor/name/host. "
        "Does not print passwords."
    )

    def handle(self, *_args: object, **_options: object) -> None:
        connection.ensure_connection()
        vendor = connection.vendor
        cfg = connection.settings_dict
        engine = cfg.get("ENGINE", "")
        name = cfg.get("NAME") or ""
        host = cfg.get("HOST") or ""

        if vendor == "sqlite":
            self.stdout.write(
                self.style.SUCCESS(
                    f"OK: default DB reachable ({vendor})\n  ENGINE={engine}\n  NAME={name}"
                )
            )
            return

        port = cfg.get("PORT") or ""
        self.stdout.write(
            self.style.SUCCESS(
                "OK: default DB reachable\n"
                + f"  vendor={vendor}\n"
                + f"  ENGINE={engine}\n"
                + f"  NAME={name}\n"
                + f"  HOST={host}\n"
                + f"  PORT={port}"
            )
        )
