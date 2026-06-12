"""Import simulation_systems.json into C-lite normalized models."""

from __future__ import annotations

from django_apps.game_data.enums import SimulationAuditIssueCode, SimulationAuditSeverity
from django_apps.game_data.importers.base import ImportContext
from django_apps.game_data.importers.simulation_definition_snapshot_audit import (
    sync_definition_snapshot_coverage_audit,
)
from django_apps.game_data.importers.simulation_speeds import import_simulation_speeds
from django_apps.game_data.models import (
    BuildingVariant,
    ConnectableSimulation,
    SimulationChunkBounds,
    SimulationClrProvenance,
    SimulationConnector,
    SimulationConnectorProperty,
    SimulationLaneDefinition,
    SimulationLaneRuntimeState,
    SimulationProfile,
    SimulationRuntimeAuditIssue,
    SimulationStateType,
    SimulationSystem,
    SimulationTileBounds,
    SimulationType,
)
from django_apps.game_data.services import identifiers
from django_apps.game_data.services.connectable_signatures import (
    build_connectable_key,
    build_connector_signature,
    build_lane_signature,
    connector_type_name,
    pivot_direction,
    simulation_transport_slug,
)
from django_apps.game_data.services.simulation_clr_parser import parse_simulation_clr
from django_apps.game_data.services.simulation_parameter_registry import (
    reconcile_parameter_key_counts,
    sync_ignored_simulation_parameters,
    sync_simulation_parameter_registry,
)
from django_apps.game_data.services.simulation_profile_detect import (
    PROFILE_CONNECTABLE,
    PROFILE_CONVERTER,
    PROFILE_FACTORY,
    detect_simulation_profile_key,
)

_PROFILE_LABELS: dict[str, str] = {
    "factory": "Simulation factory stub",
    "connectable_graph": "Connectable simulation graph",
    "converter_runtime": "Converter runtime capture",
    "belt_policy": "Global belt speed policy",
    "other": "Other simulation parameters",
}


def _ensure_profile(profile_key: str) -> SimulationProfile:
    profile, _ = SimulationProfile.objects.get_or_create(
        profile_key=profile_key,
        defaults={"profile_name": _PROFILE_LABELS.get(profile_key, profile_key)},
    )
    return profile


def _bounds_coords(bounds: dict[str, object] | None) -> tuple[int, int, int, int, int, int]:
    if not isinstance(bounds, dict):
        return (0, 0, 0, 0, 0, 0)
    min_pt = bounds.get("<Min>k__BackingField") or bounds.get("Min") or {}
    max_pt = bounds.get("<Max>k__BackingField") or bounds.get("Max") or {}
    if not isinstance(min_pt, dict):
        min_pt = {}
    if not isinstance(max_pt, dict):
        max_pt = {}
    return (
        int(min_pt.get("x", 0) or 0),
        int(min_pt.get("y", 0) or 0),
        int(min_pt.get("z", 0) or 0),
        int(max_pt.get("x", 0) or 0),
        int(max_pt.get("y", 0) or 0),
        int(max_pt.get("z", 0) or 0),
    )


def _building_internal_name(building: dict[str, object] | None) -> str:
    if not isinstance(building, dict):
        return ""
    definition = building.get("Definition")
    if isinstance(definition, dict):
        name = definition.get("Id")
        if isinstance(name, str):
            return name
        nested = definition.get("Id")
        if isinstance(nested, dict):
            return str(nested.get("Name", "") or "")
    return ""


def _set_connector_property(
    connector: SimulationConnector,
    property_key: str,
    value: object,
) -> None:
    defaults: dict[str, object] = {
        "value_int": None,
        "value_float": None,
        "value_bool": None,
        "value_text": "",
    }
    if isinstance(value, bool):
        defaults["value_bool"] = value
    elif isinstance(value, int) and not isinstance(value, bool):
        defaults["value_int"] = value
    elif isinstance(value, float):
        defaults["value_float"] = value
    else:
        defaults["value_text"] = str(value)[:2000]
    SimulationConnectorProperty.objects.update_or_create(
        connector=connector,
        property_key=property_key,
        defaults=defaults,
    )


def _import_connectable_attachment(
    ctx: ImportContext,
    system: SimulationSystem,
    attachment: dict[str, object],
    attachment_index: int,
) -> None:
    building = attachment.get("Building") if isinstance(attachment.get("Building"), dict) else {}
    internal = _building_internal_name(building)
    variant = BuildingVariant.objects.filter(internal_name=internal).first() if internal else None

    sim_obj = attachment.get("Simulation") if isinstance(attachment.get("Simulation"), dict) else {}
    connectors_raw = attachment.get("Connectors")
    if not isinstance(connectors_raw, list):
        connectors_raw = []
    conn_sig = build_connector_signature(connectors_raw)

    transport = simulation_transport_slug(sim_obj)
    lane_defs_for_sig: list[tuple[str, int | None, str]] = []
    lanes = sim_obj.get("_Lanes") or sim_obj.get("InputLanes")
    if isinstance(lanes, list):
        for li, _lane in enumerate(lanes):
            lane_defs_for_sig.append((transport, None, str(li)))
    lane_sig = build_lane_signature(simulation=sim_obj, lane_definitions=lane_defs_for_sig)

    num_connectors = int(attachment.get("NumConnectors", len(connectors_raw)) or 0)
    num_tiles = int(attachment.get("NumOccupiedTiles", 0) or 0)
    variant_pk = variant.pk if variant else None
    key = build_connectable_key(
        building_variant_id=variant_pk,
        num_connectors=num_connectors,
        num_occupied_tiles=num_tiles,
        connector_signature=conn_sig,
        lane_signature=lane_sig,
    )
    conn_cid = identifiers.canonical_connectable_simulation(system.pk, key)
    connectable, _ = ConnectableSimulation.objects.update_or_create(
        simulation_system=system,
        connectable_key=key,
        defaults={
            "canonical_id": conn_cid,
            "attachment_index": attachment_index,
            "building_variant": variant,
            "num_connectors": num_connectors,
            "num_occupied_tiles": num_tiles,
            "connector_signature": conn_sig[:512],
            "lane_signature": lane_sig[:512],
        },
    )

    SimulationConnector.objects.filter(connectable_simulation=connectable).delete()
    for oi, conn in enumerate(connectors_raw):
        if not isinstance(conn, dict):
            continue
        direction = pivot_direction(conn.get("Pivot"))
        role = connector_type_name(conn)
        ccid = identifiers.canonical_simulation_connector(conn_cid, oi)
        sim_conn = SimulationConnector.objects.create(
            canonical_id=ccid,
            connectable_simulation=connectable,
            order_index=oi,
            direction=direction[:32],
            connector_role=role[:64],
            io_channel_type=str(conn.get("UpdatePriority", ""))[:32],
        )
        if conn.get("UpdatePriority"):
            _set_connector_property(sim_conn, "update_priority", conn.get("UpdatePriority"))

    SimulationLaneDefinition.objects.filter(connectable_simulation=connectable).delete()
    if isinstance(lanes, list):
        for li, lane in enumerate(lanes):
            lane_key = f"{transport}:{li}"
            lcid = identifiers.canonical_simulation_lane_definition(conn_cid, lane_key)
            lane_def = SimulationLaneDefinition.objects.create(
                canonical_id=lcid,
                connectable_simulation=connectable,
                lane_key=lane_key[:64],
                lane_index=li,
                capacity=None,
                direction="",
                transport_type=transport[:64],
            )
            SimulationLaneRuntimeState.objects.update_or_create(
                lane_definition=lane_def,
                state_key="dump",
                defaults={"state_value_text": str(lane)[:2000]},
            )

    for bounds_kind, model_cls in (
        ("ChunkBounds", SimulationChunkBounds),
        ("TileBounds", SimulationTileBounds),
    ):
        model_cls.objects.filter(connectable_simulation=connectable).delete()
        bounds = attachment.get(bounds_kind)
        if isinstance(bounds, dict):
            coords = _bounds_coords(bounds)
            model_cls.objects.create(
                connectable_simulation=connectable,
                order_index=0,
                min_x=coords[0],
                min_y=coords[1],
                min_z=coords[2],
                max_x=coords[3],
                max_y=coords[4],
                max_z=coords[5],
            )

    ctx.bump("connectable_simulation")


def import_simulation_systems(ctx: ImportContext, rows: list[dict[str, object]]) -> None:
    touched_param_keys: set[str] = set()
    for i, row in enumerate(rows):
        params = row.get("simulation_parameters")
        if not isinstance(params, dict):
            params = {}

        stype = str(row.get("source_type_name", ""))
        parsed = parse_simulation_clr(stype)
        profile_key = detect_simulation_profile_key(params, source_type_name=stype)
        profile = _ensure_profile(profile_key)

        group_key = identifiers.canonical_simulation_group_key(
            parsed.family,
            parsed.simulation_class,
            parsed.state_class,
            profile.profile_key,
        )
        group_id = identifiers.canonical_simulation_group_id(group_key)
        stable_id = str(row.get("stable_id", ""))
        src = ctx.record_source_row(
            "simulation_systems.json",
            i,
            row,
            clr_type=stype,
            system_id=stable_id,
        )

        system, _ = SimulationSystem.objects.update_or_create(
            import_batch=ctx.batch,
            source_stable_id=stable_id,
            defaults={
                "canonical_id": group_id,
                "source_row_index": i,
                "system_family": parsed.family[:128],
                "profile": profile,
                "display_name_key": str(row.get("display_name_key", ""))[:512],
                "source_object": src,
            },
        )

        if parsed.simulation_class:
            SimulationType.objects.update_or_create(
                simulation_system=system,
                defaults={
                    "simulation_class": parsed.simulation_class[:128],
                    "assembly_name": "",
                },
            )
        else:
            SimulationType.objects.filter(simulation_system=system).delete()

        if parsed.state_class:
            SimulationStateType.objects.update_or_create(
                simulation_system=system,
                defaults={
                    "state_class": parsed.state_class[:128],
                    "assembly_name": "",
                },
            )
        else:
            SimulationStateType.objects.filter(simulation_system=system).delete()

        prov_cid = identifiers.canonical_simulation_clr_provenance(ctx.batch.id, stable_id)
        SimulationClrProvenance.objects.update_or_create(
            canonical_id=prov_cid,
            defaults={
                "import_batch": ctx.batch,
                "source_file": "simulation_systems.json",
                "source_stable_id": stable_id,
                "source_row_index": i,
                "clr_type_string": stype[:8000],
                "profile_signature": profile_key,
            },
        )
        ctx.bump("simulation_clr_provenance")

        seen_keys = sync_simulation_parameter_registry(
            system, params, touched_keys=touched_param_keys
        )
        for _ in seen_keys:
            ctx.bump("simulation_parameter_occurrence")

        ignored_n = sync_ignored_simulation_parameters(ctx, stable_id, params)
        for _ in range(ignored_n):
            ctx.bump("ignored_simulation_parameter")

        snap = row.get("definition_snapshot")
        audit_n = sync_definition_snapshot_coverage_audit(
            ctx,
            owner_key=stable_id,
            definition_snapshot=snap if isinstance(snap, dict) else None,
        )
        if audit_n:
            ctx.bump("definition_snapshot_coverage_audit", audit_n)

        import_simulation_speeds(ctx, system, params, source_stable_id=stable_id)

        if profile_key == PROFILE_CONNECTABLE:
            for ai, att in enumerate(params.get("ConnectableSimulations") or []):
                if isinstance(att, dict):
                    _import_connectable_attachment(ctx, system, att, ai)
        elif profile_key == PROFILE_CONVERTER:
            SimulationRuntimeAuditIssue.objects.update_or_create(
                simulation_system=system,
                issue_code=SimulationAuditIssueCode.CONVERTER_PROFILE,
                defaults={
                    "severity": SimulationAuditSeverity.INFO,
                    "message": f"converter capture row_index={i}",
                    "source_path": f"simulation_systems.json[{i}]",
                },
            )
            ctx.bump("simulation_runtime_audit_issue")
        elif profile_key == PROFILE_FACTORY:
            pass

        ctx.bump("simulation_system")

    if touched_param_keys:
        reconcile_parameter_key_counts(touched_param_keys)
