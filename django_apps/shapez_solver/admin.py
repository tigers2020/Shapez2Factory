from django.contrib import admin

from django_apps.shapez_solver.models import (
    MacroRecipe,
    MacroRecipeCompiledBoundary,
    MacroRecipeStep,
    PatternExample,
    PatternFamily,
    PatternTemplate,
    SolverProject,
    SolverRun,
)


class MacroRecipeCompiledBoundaryInline(admin.TabularInline):
    model = MacroRecipeCompiledBoundary
    extra = 0
    fields = ("graph_shape_id", "pattern_signature", "boundary")
    readonly_fields = ("graph_shape_id", "pattern_signature", "boundary")
    can_delete = False
    ordering = ("boundary", "graph_shape_id")

    def has_add_permission(self, request, obj=None):
        return False


class MacroRecipeStepInline(admin.TabularInline):
    model = MacroRecipeStep
    extra = 1
    fields = ("step_index", "operation", "input_slots", "output_slots", "note")


@admin.register(PatternFamily)
class PatternFamilyAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "signature",
        "allow_rotation",
        "allow_reflection",
        "priority",
        "is_active",
    )
    list_filter = ("is_active", "allow_rotation", "allow_reflection", "signature")
    search_fields = ("code", "name", "signature", "description")
    ordering = ("priority", "code")


@admin.register(PatternTemplate)
class PatternTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "family",
        "template",
        "normalized_template",
        "min_distinct_parts",
        "max_distinct_parts",
        "is_active",
    )
    list_filter = ("is_active", "family")
    search_fields = ("display_name", "template", "normalized_template", "family__code")
    ordering = ("family__priority", "normalized_template")


@admin.register(MacroRecipe)
class MacroRecipeAdmin(admin.ModelAdmin):
    inlines = (MacroRecipeStepInline, MacroRecipeCompiledBoundaryInline)
    list_display = (
        "code",
        "strategy_code",
        "family",
        "estimated_operation_cost",
        "estimated_stage_cost",
        "estimated_waste_cost",
        "priority",
        "is_active",
    )
    list_filter = ("is_active", "family", "strategy_code")
    search_fields = ("code", "strategy_code", "name", "family__code")
    ordering = ("priority", "code")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change and obj.graph_document is None:
            from django_apps.shapez_solver.services.macro_recipe_staff_catalog import (
                apply_graph_derived_catalog_fields,
            )
            from django_apps.shapez_solver.services.recipe_graph_recompute import (
                default_empty_graph_document,
            )

            obj.graph_document = default_empty_graph_document()
            obj.save(update_fields=["graph_document"])
            apply_graph_derived_catalog_fields(obj, obj.graph_document)


@admin.register(MacroRecipeCompiledBoundary)
class MacroRecipeCompiledBoundaryAdmin(admin.ModelAdmin):
    list_display = ("macro", "graph_shape_id", "pattern_signature", "boundary")
    list_select_related = ("macro",)
    list_filter = ("boundary",)
    search_fields = ("graph_shape_id", "pattern_signature", "macro__code", "macro__name")
    ordering = ("macro_id", "boundary", "graph_shape_id")
    readonly_fields = ("macro", "graph_shape_id", "pattern_signature", "boundary")

    def has_add_permission(self, request):
        return False


@admin.register(PatternExample)
class PatternExampleAdmin(admin.ModelAdmin):
    list_display = ("input_shape_code", "expected_signature", "family", "expected_macro")
    list_filter = ("family", "expected_signature")
    search_fields = ("input_shape_code", "expected_signature", "family__code")


@admin.register(SolverProject)
class SolverProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "target_shape", "target_rate_per_min", "created_at", "updated_at")
    search_fields = ("title", "target_shape")


@admin.register(SolverRun)
class SolverRunAdmin(admin.ModelAdmin):
    list_display = ("project", "status", "runtime_ms", "explored_states", "created_at")
    list_filter = ("status",)
    search_fields = ("project__title", "project__target_shape")
