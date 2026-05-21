"""Stable enum codes for game_data (no free-form issue/ref strings)."""

from __future__ import annotations

from django.db import models


class GameDataRefKind(models.TextChoices):
    BUILDING_VARIANT = "building_variant", "Building variant"
    BUILDING_GROUP = "building_group", "Building group"
    RESEARCH_MECHANIC = "research_mechanic", "Research mechanic"
    RESEARCH_UPGRADE = "research_upgrade", "Research upgrade"
    SHAPE_RECIPE = "shape_recipe", "Shape recipe"
    CONTENT_ASSET = "content_asset", "Content asset"
    SIMULATION_SYSTEM = "simulation_system", "Simulation system"
    TOOLBAR_NODE = "toolbar_node", "Toolbar node"
    OTHER = "other", "Other"


class SimulationAuditIssueCode(models.TextChoices):
    CONVERTER_PROFILE = "converter_profile", "Converter profile capture"
    RUNTIME_STUB = "runtime_stub", "Runtime stub"
    UNKNOWN = "unknown", "Unknown"


class SimulationAuditSeverity(models.TextChoices):
    INFO = "info", "Info"
    WARNING = "warning", "Warning"
    ERROR = "error", "Error"
