"""Pre/post conditions for game_data import (migrations, schema contracts)."""

from __future__ import annotations

from django.db import connections
from django.db.migrations.executor import MigrationExecutor

from django_apps.game_data.services.validators import assert_no_domain_json_fields

GAME_DATA_APP_LABEL = "game_data"


class GameDataImportBlockedError(RuntimeError):
    """Import refused until migrations or schema contracts are satisfied."""


def assert_game_data_migrations_applied() -> None:
    connection = connections["default"]
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes(GAME_DATA_APP_LABEL)
    plan = executor.migration_plan(targets)
    if plan:
        pending = [migration.name for migration, _ in plan]
        raise GameDataImportBlockedError(
            f"game_data has unapplied migrations: {', '.join(pending)}. "
            "Run: python manage.py migrate game_data"
        )


def assert_import_preconditions() -> None:
    """Run before GameDataImporter mutates the database."""
    assert_game_data_migrations_applied()


def run_post_import_guards() -> None:
    """Run after a successful import transaction."""
    assert_no_domain_json_fields()
