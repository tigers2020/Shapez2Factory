"""Canonical game_data domain models (see documents/game_data_analysis/_audit/09)."""

# ruff: noqa: E501

from __future__ import annotations

from django.db import models

from django_apps.game_data.enums import SimulationAuditIssueCode, SimulationAuditSeverity
from django_apps.game_data.models.buildings import BuildingVariant
from django_apps.game_data.models.import_meta import ImportBatch, SourceObject
from django_apps.game_data.models.research import ResearchUpgrade


class SimulationProfile(models.Model):
    profile_key = models.CharField(max_length=64, unique=True)
    profile_name = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        verbose_name = "simulation profile"
        verbose_name_plural = "⑥ Simulation · Profiles"

    def __str__(self) -> str:
        return self.profile_key


class SimulationSystem(models.Model):
    import_batch = models.ForeignKey(
        ImportBatch, on_delete=models.CASCADE, related_name="simulation_systems"
    )
    source_stable_id = models.CharField(max_length=64)
    source_row_index = models.PositiveIntegerField()
    system_family = models.CharField(max_length=128)
    profile = models.ForeignKey(SimulationProfile, on_delete=models.PROTECT, related_name="systems")
    canonical_id = models.CharField(max_length=255, db_index=True)
    display_name_key = models.CharField(max_length=512, blank=True, default="")
    source_object = models.ForeignKey(
        SourceObject,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="simulation_systems",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["import_batch", "source_stable_id"],
                name="uq_simulation_system_batch_stable",
            ),
        ]
        verbose_name = "simulation system"
        verbose_name_plural = "⑥ Simulation · Systems"

    def __str__(self) -> str:
        return f"{self.system_family} #{self.source_row_index}"


class SimulationType(models.Model):
    simulation_system = models.OneToOneField(
        SimulationSystem, on_delete=models.CASCADE, related_name="simulation_type"
    )
    simulation_class = models.CharField(max_length=128)
    assembly_name = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        verbose_name = "simulation type"
        verbose_name_plural = "⑥ Simulation · Types"

    def __str__(self) -> str:
        return self.simulation_class


class SimulationStateType(models.Model):
    simulation_system = models.OneToOneField(
        SimulationSystem, on_delete=models.CASCADE, related_name="state_type"
    )
    state_class = models.CharField(max_length=128)
    assembly_name = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        verbose_name = "simulation state type"
        verbose_name_plural = "⑥ Simulation · State types"

    def __str__(self) -> str:
        return self.state_class


class SimulationClrProvenance(models.Model):
    """Per-row CLR type string from ``simulation_systems.json`` ``source_type_name``.

    This is **not** an import-run audit log and must not store ``simulation_parameters``,
    JSON blobs, or domain-queryable fields. Parsed simulation/state classes live on
    ``SimulationType`` / ``SimulationStateType``; ``profile_signature`` mirrors detected
    ``simulation_parameters`` profile for debug only.
    """

    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(
        ImportBatch, on_delete=models.CASCADE, related_name="simulation_clr_provenances"
    )
    source_file = models.CharField(max_length=128, default="simulation_systems.json")
    source_stable_id = models.CharField(max_length=64)
    source_row_index = models.PositiveIntegerField()
    clr_type_string = models.TextField()
    profile_signature = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["import_batch", "source_stable_id", "source_file"],
                name="uq_sim_clr_prov_batch_stable_file",
            ),
        ]
        verbose_name = "simulation CLR provenance"
        verbose_name_plural = "⑥ Simulation · CLR provenance"

    def __str__(self) -> str:
        return f"{self.source_file}[{self.source_row_index}]"


class ConnectableSimulation(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    simulation_system = models.ForeignKey(
        SimulationSystem, on_delete=models.CASCADE, related_name="connectables"
    )
    connectable_key = models.CharField(max_length=64)
    attachment_index = models.PositiveIntegerField()
    building_variant = models.ForeignKey(
        BuildingVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="connectables",
    )
    num_connectors = models.PositiveIntegerField(default=0)
    num_occupied_tiles = models.PositiveIntegerField(default=0)
    connector_signature = models.CharField(max_length=512, blank=True, default="")
    lane_signature = models.CharField(max_length=512, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["simulation_system", "connectable_key"],
                name="uq_connectable_system_key",
            ),
        ]
        verbose_name = "connectable simulation"
        verbose_name_plural = "⑥ Simulation · Connectables"

    def __str__(self) -> str:
        return f"{self.connectable_key} @ {self.simulation_system_id}"


class SimulationConnector(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    connectable_simulation = models.ForeignKey(
        ConnectableSimulation, on_delete=models.CASCADE, related_name="connectors"
    )
    order_index = models.PositiveIntegerField()
    direction = models.CharField(max_length=32, blank=True, default="")
    connector_role = models.CharField(max_length=64, blank=True, default="")
    io_channel_type = models.CharField(max_length=32, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["connectable_simulation", "order_index"],
                name="uq_sim_connector_order",
            ),
        ]
        verbose_name = "simulation connector"
        verbose_name_plural = "⑥ Simulation · Connectors"
        ordering = ["order_index"]

    def __str__(self) -> str:
        return f"{self.connectable_simulation_id} #{self.order_index}"


class SimulationConnectorProperty(models.Model):
    connector = models.ForeignKey(
        SimulationConnector, on_delete=models.CASCADE, related_name="properties"
    )
    property_key = models.CharField(max_length=64)
    value_int = models.BigIntegerField(null=True, blank=True)
    value_float = models.FloatField(null=True, blank=True)
    value_bool = models.BooleanField(null=True, blank=True)
    value_text = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["connector", "property_key"],
                name="uq_sim_connector_property_key",
            ),
        ]
        verbose_name = "simulation connector property"
        verbose_name_plural = "⑥ Simulation · Connector properties"

    def __str__(self) -> str:
        return f"{self.property_key}"


class SimulationLaneDefinition(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    connectable_simulation = models.ForeignKey(
        ConnectableSimulation, on_delete=models.CASCADE, related_name="lane_definitions"
    )
    lane_key = models.CharField(max_length=64)
    lane_index = models.PositiveIntegerField()
    capacity = models.PositiveIntegerField(null=True, blank=True)
    direction = models.CharField(max_length=32, blank=True, default="")
    transport_type = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["connectable_simulation", "lane_key"],
                name="uq_lane_definition_key",
            ),
        ]
        verbose_name = "simulation lane definition"
        verbose_name_plural = "⑥ Simulation · Lane definitions"
        ordering = ["lane_index"]

    def __str__(self) -> str:
        return self.lane_key


class SimulationLaneRuntimeState(models.Model):
    lane_definition = models.ForeignKey(
        SimulationLaneDefinition, on_delete=models.CASCADE, related_name="runtime_states"
    )
    state_key = models.CharField(max_length=64)
    state_value_text = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["lane_definition", "state_key"],
                name="uq_lane_runtime_state_key",
            ),
        ]
        verbose_name = "simulation lane runtime state"
        verbose_name_plural = "⑥ Simulation · Lane runtime states"

    def __str__(self) -> str:
        return f"{self.state_key}"


class SimulationChunkBounds(models.Model):
    connectable_simulation = models.ForeignKey(
        ConnectableSimulation, on_delete=models.CASCADE, related_name="chunk_bounds"
    )
    order_index = models.PositiveSmallIntegerField(default=0)
    min_x = models.IntegerField(default=0)
    min_y = models.IntegerField(default=0)
    min_z = models.IntegerField(default=0)
    max_x = models.IntegerField(default=0)
    max_y = models.IntegerField(default=0)
    max_z = models.IntegerField(default=0)

    class Meta:
        verbose_name = "simulation chunk bounds"
        verbose_name_plural = "⑥ Simulation · Chunk bounds"

    def __str__(self) -> str:
        return f"chunk {self.connectable_simulation_id}"


class SimulationTileBounds(models.Model):
    connectable_simulation = models.ForeignKey(
        ConnectableSimulation, on_delete=models.CASCADE, related_name="tile_bounds"
    )
    order_index = models.PositiveSmallIntegerField(default=0)
    min_x = models.IntegerField(default=0)
    min_y = models.IntegerField(default=0)
    min_z = models.IntegerField(default=0)
    max_x = models.IntegerField(default=0)
    max_y = models.IntegerField(default=0)
    max_z = models.IntegerField(default=0)

    class Meta:
        verbose_name = "simulation tile bounds"
        verbose_name_plural = "⑥ Simulation · Tile bounds"

    def __str__(self) -> str:
        return f"tile {self.connectable_simulation_id}"


class GlobalBeltSpeedPolicy(models.Model):
    import_batch = models.OneToOneField(
        ImportBatch, on_delete=models.CASCADE, related_name="belt_speed_policy"
    )
    simulation_system = models.OneToOneField(
        SimulationSystem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="belt_speed_policy",
    )
    base_speed = models.CharField(max_length=64, blank=True, default="")
    research_upgrade = models.ForeignKey(
        ResearchUpgrade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="belt_policies",
    )
    steps_per_tick = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "global belt speed policy"
        verbose_name_plural = "⑥ Simulation · Belt speed policy"

    def __str__(self) -> str:
        return f"belt:{self.base_speed}"


class SimulationBuffableSpeed(models.Model):
    """Per-system ``BuffableBeltSpeed`` (BeltSpeed / ConveyorSpeed / SpaceConveyorSpeed)."""

    canonical_id = models.CharField(max_length=255, unique=True)
    simulation_system = models.ForeignKey(
        SimulationSystem, on_delete=models.CASCADE, related_name="buffable_speeds"
    )
    parameter_name = models.CharField(max_length=100)
    dump_type = models.CharField(max_length=64, default="BuffableBeltSpeed")
    base_speed = models.CharField(max_length=64, blank=True, default="")
    research_upgrade = models.ForeignKey(
        ResearchUpgrade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="buffable_speeds",
    )
    steps_per_tick = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["simulation_system", "parameter_name"],
                name="uq_sim_buffable_speed_system_param",
            ),
        ]
        verbose_name = "simulation buffable speed"
        verbose_name_plural = "⑥ Simulation · Buffable speeds"

    def __str__(self) -> str:
        return f"{self.parameter_name}:{self.base_speed}"


class SimulationMultipleBeltSpeed(models.Model):
    """Per-system ``MultipleBeltSpeed`` (typically JumpSpeed → BuffableBeltSpeed cycle)."""

    canonical_id = models.CharField(max_length=255, unique=True)
    simulation_system = models.ForeignKey(
        SimulationSystem, on_delete=models.CASCADE, related_name="multiple_belt_speeds"
    )
    parameter_name = models.CharField(max_length=100, default="JumpSpeed")
    dump_type = models.CharField(max_length=64, default="MultipleBeltSpeed")
    cycle_ref_type = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="``BaseSpeed.$cycle`` target (e.g. BuffableBeltSpeed).",
    )
    buffable_base = models.ForeignKey(
        SimulationBuffableSpeed,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="multiple_speed_children",
    )
    multiplier = models.PositiveIntegerField(default=0)
    steps_per_tick = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["simulation_system", "parameter_name"],
                name="uq_sim_multiple_belt_speed_system_param",
            ),
        ]
        verbose_name = "simulation multiple belt speed"
        verbose_name_plural = "⑥ Simulation · Multiple belt speeds"

    def __str__(self) -> str:
        return f"{self.parameter_name}:x{self.multiplier}"


class SimulationSystemParameterKey(models.Model):
    """Global registry of simulation_parameters top-level keys (no values)."""

    class Classification(models.TextChoices):
        DOMAIN_CONFIG = "domain_config", "Domain config"
        RUNTIME_STATE = "runtime_state", "Runtime state"
        EVENT_DELEGATE = "event_delegate", "Event delegate"
        REFLECTION_DUMP = "reflection_dump", "Reflection dump"
        CACHE_SNAPSHOT = "cache_snapshot", "Cache snapshot"
        IGNORED_RUNTIME = "ignored_runtime", "Ignored runtime"
        UNKNOWN = "unknown", "Unknown"

    name = models.CharField(max_length=200, unique=True)
    classification = models.CharField(
        max_length=50,
        choices=Classification.choices,
        default=Classification.UNKNOWN,
    )
    occurrence_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "simulation parameter key"
        verbose_name_plural = "⑥ Simulation · Parameter keys"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.classification})"


class SimulationSystemParameterOccurrence(models.Model):
    """Per-system presence of a parameter key (path only; no JSON value)."""

    simulation_system = models.ForeignKey(
        SimulationSystem,
        on_delete=models.CASCADE,
        related_name="parameter_occurrences",
    )
    parameter_key = models.ForeignKey(
        SimulationSystemParameterKey,
        on_delete=models.CASCADE,
        related_name="occurrences",
    )
    source_path = models.CharField(max_length=1000)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["simulation_system", "parameter_key"],
                name="uq_sim_param_occurrence_system_key",
            ),
        ]
        verbose_name = "simulation parameter occurrence"
        verbose_name_plural = "⑥ Simulation · Parameter occurrences"

    def __str__(self) -> str:
        return f"{self.simulation_system_id}:{self.parameter_key_id}"


class SimulationRuntimeAuditIssue(models.Model):
    simulation_system = models.ForeignKey(
        SimulationSystem,
        on_delete=models.CASCADE,
        related_name="audit_issues",
    )
    issue_code = models.CharField(
        max_length=128,
        choices=SimulationAuditIssueCode.choices,
        default=SimulationAuditIssueCode.UNKNOWN,
    )
    severity = models.CharField(
        max_length=32,
        choices=SimulationAuditSeverity.choices,
        default=SimulationAuditSeverity.INFO,
    )
    message = models.TextField()
    source_path = models.CharField(max_length=512, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["simulation_system", "issue_code"],
                name="uq_sim_runtime_audit_issue_system_code",
            ),
        ]
        verbose_name = "simulation runtime audit issue"
        verbose_name_plural = "⑥ Simulation · Runtime audit issues"
        ordering = ["simulation_system_id", "issue_code"]

    def __str__(self) -> str:
        return f"{self.issue_code}:{self.simulation_system_id}"
