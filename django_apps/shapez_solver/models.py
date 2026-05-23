from django.db import models


class SolverProject(models.Model):
    """Solver 실행 설정과 목표 shape를 저장하는 프로젝트."""

    title = models.CharField(max_length=120)
    target_shape = models.CharField(max_length=255)
    target_rate_per_min = models.FloatField(default=60.0)
    solver_settings = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title


class SolverRunStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    RUNNING = "running", "Running"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class SolverRun(models.Model):
    """SolverProject에 속한 개별 solver 실행 기록."""

    project = models.ForeignKey(SolverProject, on_delete=models.CASCADE, related_name="runs")
    status = models.CharField(
        max_length=32,
        choices=SolverRunStatus.choices,
        default=SolverRunStatus.QUEUED,
        db_index=True,
    )
    input_snapshot = models.JSONField(default=dict)
    result_graph = models.JSONField(default=dict)
    statistics = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    runtime_ms = models.PositiveIntegerField(null=True, blank=True)
    explored_states = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.project} ({self.status})"
