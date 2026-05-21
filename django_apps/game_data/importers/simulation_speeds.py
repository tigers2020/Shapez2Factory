"""Import simulation_parameters speed keys into typed per-system tables."""

from __future__ import annotations

from typing import Any

from django_apps.game_data.importers.base import ImportContext
from django_apps.game_data.models import (
    GlobalBeltSpeedPolicy,
    ResearchUpgrade,
    SimulationBuffableSpeed,
    SimulationMultipleBeltSpeed,
    SimulationSystem,
)
from django_apps.game_data.services import identifiers
from django_apps.game_data.services.simulation_parameter_classify import (
    ParameterClassification,
)
from django_apps.game_data.services.simulation_speed_extract import (
    REASON_SIM_PARAM_SPEED_SHAPE_INVALID,
    REASON_SIM_PARAM_SPEED_SHAPE_MISMATCH,
    SPEED_PARAMETER_NAMES,
    SpeedRoute,
    SpeedShapeError,
    classify_speed_entry,
    parameter_matches_route,
    parse_buffable_speed_blob,
    parse_multiple_speed_blob,
)


def _resolve_research_upgrade(upgrade_key: str) -> ResearchUpgrade | None:
    if not upgrade_key:
        return None
    return ResearchUpgrade.objects.filter(upgrade_key=upgrade_key).first()


def _import_global_belt_policy_from_buffable(
    ctx: ImportContext,
    system: SimulationSystem,
    buffable: SimulationBuffableSpeed,
) -> None:
    if buffable.parameter_name != "BeltSpeed":
        return
    GlobalBeltSpeedPolicy.objects.update_or_create(
        import_batch=ctx.batch,
        defaults={
            "simulation_system": system,
            "base_speed": buffable.base_speed,
            "research_upgrade": buffable.research_upgrade,
            "steps_per_tick": buffable.steps_per_tick,
        },
    )
    ctx.bump("global_belt_speed_policy")


def _record_speed_import_issue(
    ctx: ImportContext,
    source_stable_id: str,
    parameter_name: str,
    blob: dict[str, Any],
    *,
    reason_code: str,
) -> None:
    ctx.record_unknown(
        "SimulationSystem",
        source_stable_id,
        f"simulation_parameters.{parameter_name}",
        parameter_name,
        blob,
        reason_code=reason_code,
        classification=ParameterClassification.DOMAIN_CONFIG,
    )


def import_simulation_speeds(
    ctx: ImportContext,
    system: SimulationSystem,
    params: dict[str, Any],
    *,
    source_stable_id: str = "",
) -> None:
    if not isinstance(params, dict):
        params = {}

    owner_key = source_stable_id or system.source_stable_id
    present_buffable: list[str] = []
    present_multiple: list[str] = []

    for name in sorted(SPEED_PARAMETER_NAMES):
        if name not in params or not isinstance(params[name], dict):
            continue
        blob = params[name]
        route, _dtype = classify_speed_entry(name, blob)

        if route == SpeedRoute.SKIP:
            continue
        if not parameter_matches_route(name, route):
            _record_speed_import_issue(
                ctx,
                owner_key,
                name,
                blob,
                reason_code=REASON_SIM_PARAM_SPEED_SHAPE_MISMATCH,
            )
            continue

        try:
            if route == SpeedRoute.BUFFABLE:
                parse_buffable_speed_blob(name, blob)
                present_buffable.append(name)
            else:
                parse_multiple_speed_blob(name, blob)
                present_multiple.append(name)
        except SpeedShapeError:
            _record_speed_import_issue(
                ctx,
                owner_key,
                name,
                blob,
                reason_code=REASON_SIM_PARAM_SPEED_SHAPE_INVALID,
            )

    SimulationBuffableSpeed.objects.filter(simulation_system=system).exclude(
        parameter_name__in=present_buffable
    ).delete()
    SimulationMultipleBeltSpeed.objects.filter(simulation_system=system).exclude(
        parameter_name__in=present_multiple
    ).delete()

    buffable_by_type: dict[str, SimulationBuffableSpeed] = {}

    for name in present_buffable:
        blob = params[name]
        assert isinstance(blob, dict)
        parsed = parse_buffable_speed_blob(name, blob)
        upgrade = _resolve_research_upgrade(parsed["research_upgrade_key"])
        cid = identifiers.canonical_simulation_buffable_speed(system.pk, name)
        buffable, _ = SimulationBuffableSpeed.objects.update_or_create(
            simulation_system=system,
            parameter_name=name,
            defaults={
                "canonical_id": cid,
                "dump_type": parsed["dump_type"],
                "base_speed": parsed["base_speed"],
                "research_upgrade": upgrade,
                "steps_per_tick": parsed["steps_per_tick"],
            },
        )
        buffable_by_type[parsed["dump_type"]] = buffable
        ctx.bump("simulation_buffable_speed")
        _import_global_belt_policy_from_buffable(ctx, system, buffable)

    for name in present_multiple:
        blob = params[name]
        assert isinstance(blob, dict)
        parsed = parse_multiple_speed_blob(name, blob)
        base_ref = buffable_by_type.get(parsed["cycle_ref_type"])
        if base_ref is None and parsed["cycle_ref_type"]:
            base_ref = SimulationBuffableSpeed.objects.filter(
                simulation_system=system,
                dump_type=parsed["cycle_ref_type"],
            ).first()
        if base_ref is None:
            base_ref = SimulationBuffableSpeed.objects.filter(simulation_system=system).first()

        cid = identifiers.canonical_simulation_multiple_belt_speed(system.pk, name)
        SimulationMultipleBeltSpeed.objects.update_or_create(
            simulation_system=system,
            parameter_name=name,
            defaults={
                "canonical_id": cid,
                "dump_type": parsed["dump_type"],
                "cycle_ref_type": parsed["cycle_ref_type"],
                "buffable_base": base_ref,
                "multiplier": parsed["multiplier"],
                "steps_per_tick": parsed["steps_per_tick"],
            },
        )
        ctx.bump("simulation_multiple_belt_speed")
