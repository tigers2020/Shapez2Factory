"""Domain-complete coverage manifest for game_data JSON artifacts."""

from django_apps.game_data.coverage.disposition import Disposition
from django_apps.game_data.coverage.manifest import MANIFEST

__all__ = ["MANIFEST", "Disposition"]
