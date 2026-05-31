"""Phase 1 persistence for Asteroid Lab UI, replay, topology help, and hybrid solver artifacts.

Solver code must consume DTOs only; these models are for persistence, cache, UI, and inspection.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models


class AsteroidProject(models.Model):
    """One lab page / work unit."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["-updated_at"]),
        ]

    def __str__(self) -> str:
        return str(self.name)


class AsteroidMapInput(models.Model):
    """Decoded blueprint and copy-code metadata for a project."""

    class SourceKind(models.TextChoices):
        COPY_CODE = "copy_code", "Copy code"
        DECODED_JSON = "decoded_json", "Decoded JSON"
        IMPORT_FILE = "import_file", "Import file"
        OTHER = "other", "Other"

    project = models.ForeignKey(
        AsteroidProject,
        on_delete=models.CASCADE,
        related_name="map_inputs",
    )
    source_kind = models.CharField(
        max_length=40,
        choices=SourceKind.choices,
        default=SourceKind.OTHER,
    )
    copy_code = models.TextField(blank=True)
    decoded_json = models.JSONField(default=dict, blank=True)
    content_sha256 = models.CharField(max_length=64, blank=True, db_index=True)
    layout_fingerprint = models.CharField(max_length=64, blank=True, db_index=True)
    absolute_layout_fingerprint = models.CharField(max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=["project", "source_kind"]),
            models.Index(fields=["content_sha256"]),
            models.Index(fields=["-updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.project.slug} ({self.source_kind})"


class AsteroidCellSnapshot(models.Model):
    """Grid / cell paint state the UI can render."""

    map_input = models.ForeignKey(
        AsteroidMapInput,
        on_delete=models.CASCADE,
        related_name="cell_snapshots",
    )
    layer = models.CharField(max_length=80, default="combined")
    cell_grid_json = models.JSONField(default=dict, blank=True)
    overlay_json = models.JSONField(default=dict, blank=True)
    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-captured_at",)
        indexes = [
            models.Index(fields=["map_input", "layer"]),
            models.Index(fields=["map_input", "-captured_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.map_input_id} layer={self.layer}"


class PatternTemplate(models.Model):
    """Local pattern / DP template for the lab (app ``asteroid_lab``; not ``shapez_solver``)."""

    template_key = models.CharField(max_length=160, unique=True)
    title = models.CharField(max_length=200)
    pattern_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("template_key",)
        indexes = [models.Index(fields=["template_key"])]

    def __str__(self) -> str:
        return str(self.title)


class PatternVariant(models.Model):
    """Rotation / mirror / transport-specific view of a lab ``PatternTemplate``."""

    template = models.ForeignKey(
        PatternTemplate,
        on_delete=models.CASCADE,
        related_name="variants",
    )
    variant_key = models.CharField(max_length=160)
    rotation_quarter_turns = models.PositiveSmallIntegerField(default=0)
    mirrored = models.BooleanField(default=False)
    transport_kind = models.CharField(max_length=40, default="default")
    variant_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("template", "variant_key")
        constraints = [
            models.UniqueConstraint(
                fields=("template", "variant_key"),
                name="uniq_al_pattern_variant_per_template",
            ),
        ]
        indexes = [
            models.Index(fields=["template", "variant_key"]),
        ]

    def __str__(self) -> str:
        return f"{self.template.template_key}:{self.variant_key}"


class SolverRun(models.Model):
    """One GA / hybrid solver execution for a lab project (``asteroid_lab`` app)."""

    class RunStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        PARTIAL = "partial", "Partial"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    project = models.ForeignKey(
        AsteroidProject,
        on_delete=models.CASCADE,
        related_name="solver_runs",
    )
    run_key = models.CharField(max_length=120, db_index=True)
    algorithm_label = models.CharField(max_length=120, default="ga_hybrid")
    status = models.CharField(
        max_length=40,
        choices=RunStatus.choices,
        default=RunStatus.PENDING,
    )
    config_json = models.JSONField(default=dict, blank=True)
    artifact_root = models.CharField(
        max_length=500,
        blank=True,
        help_text="Artifact directory pointer; cache/index only, not solver input.",
    )
    lifecycle_status = models.CharField(
        max_length=40,
        blank=True,
        help_text=(
            "DB lifecycle mirror for artifact/index state; " "manifest remains artifact authority."
        ),
    )
    lab_replay_manifest_summary_json = models.JSONField(
        default=dict,
        help_text="UI cache mirror of lab replay manifest summary (not solver input).",
    )
    lab_replay_payload_json = models.JSONField(
        default=dict,
        help_text="UI cache mirror of composed lab replay payload (not solver input).",
    )
    solver_summary_json = models.JSONField(
        default=dict,
        help_text="UI cache mirror of solver_summary (not solver input).",
    )
    solver_runtime_replay_frames_json = models.JSONField(
        default=list,
        help_text="UI cache mirror of solver_runtime_replay_frames (not solver input).",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("project", "run_key"),
                name="uniq_al_solver_run_key_per_project",
            ),
        ]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["project", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.project.slug} {self.run_key}"


class SolverMetricSnapshot(models.Model):
    """Per-frame fitness / score components for inspection (not solver input)."""

    solver_run = models.ForeignKey(
        SolverRun,
        on_delete=models.CASCADE,
        related_name="metric_snapshots",
    )
    frame_index = models.PositiveIntegerField()
    phase = models.CharField(max_length=80, blank=True)
    fitness_components_json = models.JSONField(default=dict, blank=True)
    aggregate_score = models.FloatField(null=True, blank=True)
    throughput_hint = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("solver_run", "frame_index")
        constraints = [
            models.UniqueConstraint(
                fields=("solver_run", "frame_index"),
                name="uniq_al_metric_snapshot_frame",
            ),
        ]
        indexes = [
            models.Index(fields=["solver_run", "frame_index"]),
        ]

    def __str__(self) -> str:
        return f"run={self.solver_run_id} frame={self.frame_index}"


class CandidateBundle(models.Model):
    """Gene-level placement bundle (not cell-level rows)."""

    solver_run = models.ForeignKey(
        SolverRun,
        on_delete=models.CASCADE,
        related_name="candidate_bundles",
    )
    bundle_key = models.CharField(max_length=160)
    generation_index = models.PositiveIntegerField(null=True, blank=True)

    extractor_coord = models.JSONField()
    output_direction = models.CharField(max_length=20)
    output_stub_coord = models.JSONField()

    extension_pattern_key = models.CharField(max_length=120, blank=True)
    extension_coords_json = models.JSONField(default=list, blank=True)

    transport_kind = models.CharField(max_length=40)
    placement_state = models.CharField(max_length=60, default="provisional")

    local_score = models.FloatField(default=0)
    fitness_json = models.JSONField(default=dict, blank=True)
    reject_reason = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ("solver_run", "bundle_key")
        constraints = [
            models.UniqueConstraint(
                fields=("solver_run", "bundle_key"),
                name="uniq_al_candidate_bundle_key_per_run",
            ),
        ]
        indexes = [
            models.Index(fields=["solver_run", "generation_index"]),
            models.Index(fields=["solver_run", "placement_state"]),
        ]

    def __str__(self) -> str:
        return f"{self.solver_run_id}:{self.bundle_key}"


class RoutingProbe(models.Model):
    """Fast feasibility routing probe result for a candidate bundle."""

    candidate_bundle = models.ForeignKey(
        CandidateBundle,
        on_delete=models.CASCADE,
        related_name="routing_probes",
    )
    probe_kind = models.CharField(max_length=80, default="fast_feasibility")
    start_stub_coord = models.JSONField()
    goal_summary_json = models.JSONField(default=dict, blank=True)

    reachable = models.BooleanField(default=False)
    path_cost = models.FloatField(null=True, blank=True)
    path_cells_json = models.JSONField(default=list, blank=True)

    failure_reason = models.CharField(max_length=120, blank=True)
    explored_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("candidate_bundle", "id")
        indexes = [
            models.Index(fields=["candidate_bundle", "probe_kind"]),
            models.Index(fields=["candidate_bundle", "reachable"]),
        ]

    def __str__(self) -> str:
        return f"bundle={self.candidate_bundle_id} reachable={self.reachable}"


class ReplayTrack(models.Model):
    """UI replay timeline container (orthogonal to solver DTO inputs)."""

    project = models.ForeignKey(
        AsteroidProject,
        on_delete=models.CASCADE,
        related_name="replay_tracks",
    )
    solver_run = models.ForeignKey(
        SolverRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replay_tracks",
    )
    track_key = models.CharField(max_length=160)
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("project", "track_key"),
                name="uniq_replay_track_key_per_project",
            ),
        ]
        indexes = [
            models.Index(fields=["project", "track_key"]),
        ]

    def __str__(self) -> str:
        return f"{self.project.slug}:{self.track_key}"


class ReplayFrame(models.Model):
    """Single UI playback step (play / pause / scrub targets)."""

    replay_track = models.ForeignKey(
        ReplayTrack,
        on_delete=models.CASCADE,
        related_name="frames",
    )
    frame_index = models.PositiveIntegerField()
    frame_key = models.CharField(max_length=120)

    phase = models.CharField(max_length=80)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    frame_payload = models.JSONField(default=dict, blank=True)
    cell_overlay_json = models.JSONField(default=dict, blank=True)
    metric_snapshot_json = models.JSONField(default=dict, blank=True)

    is_placeholder = models.BooleanField(default=False)
    is_keyframe = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("replay_track", "frame_index")
        constraints = [
            models.UniqueConstraint(
                fields=("replay_track", "frame_index"),
                name="uniq_replay_frame_index_per_track",
            ),
        ]
        indexes = [
            models.Index(fields=["replay_track", "frame_index"]),
            models.Index(fields=["replay_track", "is_keyframe"]),
        ]

    def __str__(self) -> str:
        return f"{self.replay_track_id}#{self.frame_index}"


class UIPlaybackSession(models.Model):
    """Client- or server-side persisted transport / scrubber state."""

    replay_track = models.OneToOneField(
        ReplayTrack,
        on_delete=models.CASCADE,
        related_name="playback_session",
    )

    current_frame_index = models.PositiveIntegerField(default=0)
    is_playing = models.BooleanField(default=False)
    playback_speed_ms = models.PositiveIntegerField(default=800)

    selected_layer = models.CharField(max_length=80, default="combined")
    selected_candidate_id = models.CharField(max_length=120, blank=True)
    selected_bundle_id = models.CharField(max_length=120, blank=True)

    ui_state_json = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["replay_track"]),
            models.Index(fields=["-updated_at"]),
        ]

    def __str__(self) -> str:
        return f"session track={self.replay_track_id}"


class TopologyRule(models.Model):
    """Catalog row for topology / routing rules shown in modals."""

    rule_key = models.CharField(max_length=120, unique=True)
    title = models.CharField(max_length=200)
    short_label = models.CharField(max_length=80)

    rule_group = models.CharField(max_length=80)
    severity = models.CharField(max_length=40, default="info")

    description = models.TextField(blank=True)
    examples_json = models.JSONField(default=list, blank=True)
    diagram_json = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "rule_key")
        indexes = [
            models.Index(fields=["rule_group", "is_active", "sort_order"]),
            models.Index(fields=["rule_key"]),
        ]

    def __str__(self) -> str:
        return str(self.title)


class TopologyRuleModalContent(models.Model):
    """Rich modal body linked to a topology rule (separate from the summary row)."""

    rule = models.OneToOneField(
        TopologyRule,
        on_delete=models.CASCADE,
        related_name="modal_content",
    )
    modal_title = models.CharField(max_length=200, blank=True)
    lead_html = models.TextField(blank=True)
    sections_json = models.JSONField(default=list, blank=True)
    footer_json = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["rule"])]

    def __str__(self) -> str:
        return f"modal:{self.rule.rule_key}"


class GeneticSample(models.Model):
    """유전자 샘플: 복사 문자열 저장 시 디코드되어 ``decoded_json``에 반영된다."""

    name = models.CharField(max_length=200, blank=True, verbose_name="이름")
    gene_key = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="gene 키",
        help_text="전수 생성 샘플의 정본 식별자(update_or_create 기준). 수동 샘플은 비움.",
    )
    metadata_json = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="메타데이터",
        help_text="예: generator 버전, transport_kind, topology 요약(게임 JSON과 분리).",
    )
    project = models.ForeignKey(
        AsteroidProject,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="genetic_samples",
        verbose_name="프로젝트",
    )
    code = models.TextField(verbose_name="복사 문자열")
    decoded_json = models.JSONField(default=dict, blank=True, verbose_name="디코드 JSON")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        verbose_name = "유전자 샘플"
        verbose_name_plural = "유전자 샘플"
        indexes = [
            models.Index(fields=["-updated_at"]),
            models.Index(fields=["project", "-updated_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("gene_key",),
                name="uniq_genetic_sample_gene_key_when_set",
                condition=models.Q(gene_key__isnull=False),
            ),
        ]

    def __str__(self) -> str:
        if self.name:
            return str(self.name)
        return f"GeneticSample #{self.pk}" if self.pk else "GeneticSample (unsaved)"

    def clean(self) -> None:
        super().clean()
        from django_apps.asteroid_lab.adapters.decode_adapter import (
            AsteroidLabCopyDecodeError,
            decode_copy_string,
        )
        from django_apps.asteroid_lab.adapters.normalization import normalize_decoded_blueprint
        from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
            build_decoded_blueprint_snapshot,
        )
        from django_apps.asteroid_lab.snapshots.island_bbox import island_bbox_from_cells
        from django_apps.asteroid_lab.snapshots.island_coord_meta import (
            attach_island_coord_meta_to_decoded_json,
        )

        code = (self.code or "").strip()
        if not code:
            self.decoded_json = {}
            return
        try:
            raw = decode_copy_string(code)
            dto = normalize_decoded_blueprint(raw)
            merged = dict(dto.decoded_json)
            attach_island_coord_meta_to_decoded_json(merged)
            snap = build_decoded_blueprint_snapshot(merged)
            bbox = island_bbox_from_cells(snap.cells)
            if bbox is None:
                bb = snap.bbox_json
                if int(bb.get("width", 0)) > 0 and int(bb.get("height", 0)) > 0:
                    bbox = {
                        k: int(bb[k])
                        for k in ("min_x", "max_x", "min_y", "max_y", "width", "height")
                        if k in bb
                    }
            if bbox:
                recon = merged.setdefault("_asteroid_lab_reconstruction", {})
                if isinstance(recon, dict):
                    recon["full_map_island_bbox"] = dict(bbox)
            self.decoded_json = merged
        except AsteroidLabCopyDecodeError as exc:
            raise ValidationError({"code": str(exc)}) from exc

    def save(self, *args, **kwargs) -> None:
        """Ensure ``decoded_json`` is populated even when ``save()`` is called outside ModelForm."""

        self.full_clean()
        super().save(*args, **kwargs)


class IslandExtractorBlueprint(models.Model):
    """In-game island blueprint for a shape/fluid extractor variant (balance / omni / fluid)."""

    variant_key = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="variant key",
        help_text="예: shape_balance, shape_omni, fluid_default",
    )
    carrier_kind = models.CharField(max_length=16, verbose_name="carrier")
    display_name = models.CharField(max_length=120, verbose_name="표시 이름")
    summary = models.TextField(blank=True, verbose_name="설명")
    layout_t = models.CharField(max_length=80, verbose_name="Layout T")
    copy_code = models.TextField(verbose_name="SHAPEZ2-4- 복사 문자열")
    inner_fingerprint = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="내부 B.Entries 지문",
    )
    metadata_json = models.JSONField(default=dict, blank=True, verbose_name="메타데이터")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("variant_key",)
        verbose_name = "섬 추출기 기본 블루프린트"
        verbose_name_plural = "섬 추출기 기본 블루프린트"
        indexes = [models.Index(fields=["carrier_kind", "variant_key"])]

    def __str__(self) -> str:
        return f"{self.variant_key} ({self.layout_t})"


class ReconstructedAsteroidMap(models.Model):
    """Reconstruction-complete full_map: original snapshot + merged lab copy/json."""

    map_input = models.ForeignKey(
        AsteroidMapInput,
        on_delete=models.CASCADE,
        related_name="reconstructed_maps",
    )
    project = models.ForeignKey(
        AsteroidProject,
        on_delete=models.CASCADE,
        related_name="reconstructed_maps",
    )
    solver_run = models.ForeignKey(
        SolverRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reconstructed_maps",
    )
    run_key = models.CharField(max_length=120, db_index=True)
    original_copy_code = models.TextField(blank=True, verbose_name="원본 paste copy")
    original_decoded_json = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="원본 디코드 JSON (persist 시점 스냅샷)",
    )
    copy_code = models.TextField(blank=True, verbose_name="full_map lab copy (SHAPEZ2-4-…$)")
    decoded_json = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="full_map lab 디코드 JSON",
    )
    admin_list_thumbnail = models.ImageField(
        upload_to="reconstructed_maps/list/%Y/%m/",
        blank=True,
        verbose_name="Admin changelist thumbnail",
    )
    admin_list_thumbnail_hash = models.CharField(max_length=64, blank=True)
    admin_list_thumbnail_renderer_version = models.CharField(max_length=16, blank=True)
    admin_list_thumbnail_cell_count = models.PositiveIntegerField(default=0)
    admin_list_thumbnail_grid_w = models.PositiveSmallIntegerField(default=0)
    admin_list_thumbnail_grid_h = models.PositiveSmallIntegerField(default=0)
    admin_list_thumbnail_truncated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        verbose_name = "복원 소행성 맵"
        verbose_name_plural = "복원 소행성 맵"
        constraints = [
            models.UniqueConstraint(
                fields=("map_input", "run_key"),
                name="uniq_reconstructed_map_per_map_input_run_key",
            ),
        ]
        indexes = [
            models.Index(fields=["map_input", "-updated_at"]),
            models.Index(fields=["project", "-updated_at"]),
            models.Index(fields=["-updated_at"]),
        ]

    def __str__(self) -> str:
        return f"ReconstructedAsteroidMap #{self.pk} map_input={self.map_input_id}"
