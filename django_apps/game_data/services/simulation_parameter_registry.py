"""Sync simulation_parameters top-level keys into ParameterKey / Occurrence tables."""

from __future__ import annotations

from django_apps.game_data.importers.base import ImportContext
from django_apps.game_data.models import (
    SimulationSystem,
    SimulationSystemParameterKey,
    SimulationSystemParameterOccurrence,
    UnknownProperty,
)
from django_apps.game_data.services.simulation_parameter_classify import (
    SIM_PARAM_IGNORE_REASON_PREFIX,
    ParameterClassification,
    classify_simulation_parameter_key,
    is_non_domain_simulation_parameter,
    reason_code_for_simulation_parameter,
)


def _source_path_for_key(key_name: str) -> str:
    return f"simulation_parameters.{key_name}"


def _ensure_parameter_key(key_name: str) -> SimulationSystemParameterKey:
    classification = classify_simulation_parameter_key(key_name)
    param_key, created = SimulationSystemParameterKey.objects.get_or_create(
        name=key_name,
        defaults={
            "classification": classification,
            "occurrence_count": 0,
        },
    )
    if (
        not created
        and param_key.classification == ParameterClassification.UNKNOWN
        and classification != ParameterClassification.UNKNOWN
    ):
        param_key.classification = classification
        param_key.save(update_fields=["classification"])
    return param_key


def _reconcile_occurrence_count(param_key: SimulationSystemParameterKey) -> None:
    count = SimulationSystemParameterOccurrence.objects.filter(parameter_key=param_key).count()
    if param_key.occurrence_count != count:
        param_key.occurrence_count = count
        param_key.save(update_fields=["occurrence_count"])


def sync_simulation_parameter_registry(
    system: SimulationSystem,
    params: dict[str, object],
    *,
    touched_keys: set[str] | None = None,
) -> set[str]:
    """Record top-level keys for one system; drop stale occurrences. Returns key names seen."""
    if not isinstance(params, dict):
        params = {}

    key_names = {str(k) for k in params if isinstance(k, str) and str(k).strip()}
    existing = SimulationSystemParameterOccurrence.objects.filter(simulation_system=system)
    if key_names:
        existing.exclude(parameter_key__name__in=key_names).delete()
    else:
        existing.delete()

    for key_name in sorted(key_names):
        param_key = _ensure_parameter_key(key_name)
        SimulationSystemParameterOccurrence.objects.update_or_create(
            simulation_system=system,
            parameter_key=param_key,
            defaults={"source_path": _source_path_for_key(key_name)},
        )
        if touched_keys is not None:
            touched_keys.add(key_name)

    return key_names


def reconcile_parameter_key_counts(key_names: set[str]) -> None:
    for name in key_names:
        try:
            param_key = SimulationSystemParameterKey.objects.get(name=name)
        except SimulationSystemParameterKey.DoesNotExist:
            continue
        _reconcile_occurrence_count(param_key)


def sync_ignored_simulation_parameters(
    ctx: ImportContext,
    source_stable_id: str,
    params: dict[str, object],
) -> int:
    """Record delegate/reflection/runtime keys on UnknownProperty (preview+hash only)."""
    if not isinstance(params, dict):
        params = {}

    key_names = {str(k) for k in params if isinstance(k, str) and str(k).strip()}
    ignored_paths = {
        _source_path_for_key(name)
        for name in key_names
        if is_non_domain_simulation_parameter(classify_simulation_parameter_key(name))
    }

    stale = UnknownProperty.objects.filter(
        import_batch=ctx.batch,
        owner_model="SimulationSystem",
        owner_key=source_stable_id,
        reason_code__startswith=SIM_PARAM_IGNORE_REASON_PREFIX,
    )
    if ignored_paths:
        stale.exclude(json_path__in=ignored_paths).delete()
    else:
        stale.delete()

    recorded = 0
    for key_name in sorted(key_names):
        classification = classify_simulation_parameter_key(key_name)
        if not is_non_domain_simulation_parameter(classification):
            continue
        reason_code = reason_code_for_simulation_parameter(classification)
        ctx.record_unknown(
            "SimulationSystem",
            source_stable_id,
            _source_path_for_key(key_name),
            key_name,
            params[key_name],
            reason_code=reason_code,
            classification=classification,
        )
        recorded += 1
    return recorded
