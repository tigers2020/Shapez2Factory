"""import_guards contract: migrations gate and post-import validators."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from django_apps.game_data.services import import_guards


def test_assert_game_data_migrations_applied_raises_when_pending() -> None:
    pending_migration = type("M", (), {"name": "0020_pending"})()
    with patch.object(import_guards, "MigrationExecutor") as mock_executor_cls:
        instance = mock_executor_cls.return_value
        instance.loader.graph.leaf_nodes.return_value = [("game_data", "0020_pending")]
        instance.migration_plan.return_value = [(pending_migration, False)]
        with pytest.raises(import_guards.GameDataImportBlockedError, match="unapplied migrations"):
            import_guards.assert_game_data_migrations_applied()


def test_assert_import_preconditions_calls_migration_check() -> None:
    with patch.object(import_guards, "assert_game_data_migrations_applied") as check:
        import_guards.assert_import_preconditions()
        check.assert_called_once()


def test_run_post_import_guards_calls_json_validator() -> None:
    with patch.object(import_guards, "assert_no_domain_json_fields") as validate:
        import_guards.run_post_import_guards()
        validate.assert_called_once()
