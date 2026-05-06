from django.db import models

from django_apps.shapez_solver.domain.operations import OperationType

PATTERN_FAMILY_VERBOSE_NAME = "패턴 패밀리"
MACRO_RECIPE_VERBOSE_NAME = "매크로 레시피"


class PatternFamily(models.Model):
    """Solver macro 후보를 묶는 symbolic pattern family."""

    code = models.SlugField(unique=True, verbose_name="코드")
    name = models.CharField(max_length=100, verbose_name="이름")
    signature = models.CharField(max_length=16, db_index=True, verbose_name="시그니처")
    description = models.TextField(blank=True, verbose_name="설명")
    allow_rotation = models.BooleanField(default=True, verbose_name="회전 허용")
    allow_reflection = models.BooleanField(default=False, verbose_name="반사 허용")
    priority = models.IntegerField(default=100, verbose_name="우선순위")
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="활성")
    schema_version = models.PositiveIntegerField(default=1, verbose_name="스키마 버전")

    class Meta:
        verbose_name = PATTERN_FAMILY_VERBOSE_NAME
        verbose_name_plural = PATTERN_FAMILY_VERBOSE_NAME
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["signature"]),
            models.Index(fields=["is_active", "priority"]),
        ]
        ordering = ("priority", "code")

    def __str__(self) -> str:
        return f"{self.name} ({self.signature})"


class PatternTemplate(models.Model):
    """PatternFamily에 속한 symbolic slot template."""

    family = models.ForeignKey(
        PatternFamily,
        on_delete=models.CASCADE,
        related_name="templates",
        verbose_name=PATTERN_FAMILY_VERBOSE_NAME,
    )
    template = models.CharField(max_length=32, verbose_name="템플릿")
    normalized_template = models.CharField(
        max_length=32, db_index=True, verbose_name="정규화 템플릿"
    )
    display_name = models.CharField(max_length=100, verbose_name="표시 이름")
    min_distinct_parts = models.PositiveSmallIntegerField(default=1, verbose_name="최소 파트 수")
    max_distinct_parts = models.PositiveSmallIntegerField(default=4, verbose_name="최대 파트 수")
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="활성")

    class Meta:
        verbose_name = "패턴 템플릿"
        verbose_name_plural = "패턴 템플릿"
        indexes = [
            models.Index(fields=["normalized_template"]),
            models.Index(fields=["is_active"]),
        ]
        ordering = ("family__priority", "normalized_template")

    def __str__(self) -> str:
        return f"{self.display_name} [{self.normalized_template}]"


class MacroRecipe(models.Model):
    """DB에서 켜고 끄는 Python macro strategy catalog 항목."""

    family = models.ForeignKey(
        PatternFamily,
        on_delete=models.CASCADE,
        related_name="macro_recipes",
        verbose_name=PATTERN_FAMILY_VERBOSE_NAME,
    )
    code = models.SlugField(unique=True, verbose_name="코드")
    strategy_code = models.SlugField(db_index=True, verbose_name="Python strategy 코드")
    name = models.CharField(max_length=100, verbose_name="이름")
    estimated_operation_cost = models.PositiveIntegerField(default=1, verbose_name="예상 작업 비용")
    estimated_stage_cost = models.PositiveIntegerField(default=1, verbose_name="예상 단계 비용")
    estimated_waste_cost = models.PositiveIntegerField(default=0, verbose_name="예상 폐기 비용")
    priority = models.IntegerField(default=100, verbose_name="우선순위")
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="활성")
    schema_version = models.PositiveIntegerField(default=1, verbose_name="스키마 버전")
    graph_document = models.JSONField(
        null=True,
        blank=True,
        verbose_name="레시피 그래프 문서",
        help_text="Recipe Graph Editor용 노드·엣지·좌표(JSON). null이면 스텝 테이블만 사용.",
    )

    class Meta:
        verbose_name = MACRO_RECIPE_VERBOSE_NAME
        verbose_name_plural = MACRO_RECIPE_VERBOSE_NAME
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["strategy_code"]),
            models.Index(fields=["is_active", "priority"]),
        ]
        ordering = ("priority", "code")

    def __str__(self) -> str:
        return f"{self.name} [{self.strategy_code}]"


class MacroRecipeCompiledBoundary(models.Model):
    """매크로 그래프 compile 시 경계(source/target) 패턴 시그니처 캐시."""

    class Boundary(models.TextChoices):
        START = "start", "start"
        END = "end", "end"

    macro = models.ForeignKey(
        MacroRecipe,
        on_delete=models.CASCADE,
        related_name="compiled_boundaries",
        verbose_name=MACRO_RECIPE_VERBOSE_NAME,
    )
    graph_shape_id = models.CharField(max_length=128, verbose_name="그래프 shape 노드 id")
    pattern_signature = models.CharField(max_length=16, verbose_name="패턴 시그니처")
    boundary = models.CharField(
        max_length=8,
        choices=Boundary.choices,
        verbose_name="경계",
    )

    class Meta:
        verbose_name = "매크로 컴파일 경계"
        verbose_name_plural = "매크로 컴파일 경계"
        constraints = [
            models.UniqueConstraint(
                fields=["macro", "graph_shape_id"],
                name="unique_macro_compiled_boundary_shape_id",
            )
        ]
        indexes = [
            models.Index(fields=["macro", "boundary", "pattern_signature"]),
        ]

    def __str__(self) -> str:
        return f"{self.macro.code} {self.boundary} {self.pattern_signature}"


class MacroRecipeStep(models.Model):
    """Admin과 Pattern Lab에 표시할 macro recipe 설명용 step."""

    macro = models.ForeignKey(
        MacroRecipe,
        on_delete=models.CASCADE,
        related_name="steps",
        verbose_name=MACRO_RECIPE_VERBOSE_NAME,
    )
    step_index = models.PositiveIntegerField(verbose_name="단계 번호")
    operation = models.CharField(
        max_length=32,
        choices=[(item.value, item.name) for item in OperationType],
        verbose_name="작업",
    )
    input_slots = models.JSONField(default=list, verbose_name="입력 슬롯")
    output_slots = models.JSONField(default=list, verbose_name="출력 슬롯")
    note = models.TextField(blank=True, verbose_name="메모")

    class Meta:
        verbose_name = "매크로 레시피 단계"
        verbose_name_plural = "매크로 레시피 단계"
        constraints = [
            models.UniqueConstraint(
                fields=["macro", "step_index"],
                name="unique_macro_recipe_step_index",
            )
        ]
        ordering = ("macro", "step_index")

    def __str__(self) -> str:
        return f"{self.macro.code} #{self.step_index}: {self.operation}"


class PatternExample(models.Model):
    """패턴 catalog 검증과 admin 확인에 쓰는 예시 shape."""

    family = models.ForeignKey(
        PatternFamily,
        on_delete=models.CASCADE,
        related_name="examples",
        verbose_name=PATTERN_FAMILY_VERBOSE_NAME,
    )
    input_shape_code = models.CharField(max_length=64, verbose_name="입력 shape code")
    expected_signature = models.CharField(max_length=16, verbose_name="예상 시그니처")
    expected_macro = models.ForeignKey(
        MacroRecipe,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="examples",
        verbose_name="예상 매크로",
    )
    note = models.TextField(blank=True, verbose_name="메모")

    class Meta:
        verbose_name = "패턴 예시"
        verbose_name_plural = "패턴 예시"
        indexes = [
            models.Index(fields=["input_shape_code"]),
            models.Index(fields=["expected_signature"]),
        ]
        ordering = ("family__priority", "input_shape_code")

    def __str__(self) -> str:
        return f"{self.input_shape_code} -> {self.expected_signature}"


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
