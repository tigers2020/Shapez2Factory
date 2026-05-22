"""Deterministic game_data JSON importer."""

# ruff: noqa: E501

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from django.db import transaction

from django_apps.game_data.importers.base import ImportContext, dig
from django_apps.game_data.importers.building_assembly_audit import record_assembly_reflection_audit
from django_apps.game_data.importers.shape_recipes import import_shape_rows
from django_apps.game_data.importers.simulation_systems import import_simulation_systems
from django_apps.game_data.importers.source_loader import load_json, sha256_file
from django_apps.game_data.importers.toolbar_tree import import_toolbar_tree
from django_apps.game_data.models import (
    ArtifactChecksum,
    AssetMetaReference,
    BuildingConnector,
    BuildingFootprintTile,
    BuildingGroup,
    BuildingGroupMember,
    BuildingLocalizationOverlay,
    BuildingPlacementRule,
    BuildingSimulationSetting,
    BuildingVariant,
    ExportIncompleteSection,
    ExportWarning,
    FluidColor,
    GameContentAsset,
    ImportBatch,
    LazyLocalizedPlaceholderReplacement,
    LazyLocalizedTextRef,
    LocalizationExportStatus,
    ResearchMechanic,
    ResearchMilestone,
    ResearchPrerequisite,
    ResearchSideQuest,
    ResearchSideUpgrade,
    ResearchUnlockCost,
    ResearchUpgrade,
    ShapeRecipe,
    ShapeRecipeSourceAppearance,
    SourceObject,
    TransportBuildingRegistry,
)
from django_apps.game_data.services import classifiers, identifiers
from django_apps.game_data.services.identifiers import InvalidCanonicalIdError
from django_apps.game_data.services.import_guards import (
    assert_import_preconditions,
    run_post_import_guards,
)
from django_apps.game_data.services.lazy_localized_text import parse_lazy_localized_text


class GameDataImporter:
    def __init__(self, source_dir: Path, batch_name: str = "") -> None:
        self.source_dir = source_dir.resolve()
        self.batch_name = batch_name
        self.ctx: ImportContext | None = None

    def run(self) -> dict[str, Any]:
        assert_import_preconditions()
        with transaction.atomic():
            batch = self._load_manifest()
            self.ctx = ImportContext(batch)
            self._import_fluids()
            self._import_shapes(
                catalog_source=ShapeRecipeSourceAppearance.CatalogSource.FULL,
                filename="shapes.json",
            )
            self._import_shapes(
                catalog_source=ShapeRecipeSourceAppearance.CatalogSource.ITEMS,
                filename="items.json",
            )
            self._import_building_variants()
            self._import_buildings_plain()
            self._import_building_groups()
            self._import_content_assets()
            self._import_asset_meta()
            self._import_research()
            self._import_simulation_systems()
            self._import_toolbar()
            self._import_translations_status()
            self._import_transport_registry()
            self._import_clr_types()
        assert self.ctx is not None
        summary = dict(self.ctx.summary)
        run_post_import_guards()
        return summary

    def _path(self, name: str) -> Path:
        return self.source_dir / name

    def _load_manifest(self) -> ImportBatch:
        path = self._path("manifest.json")
        data = load_json(path)
        manifest_hash = sha256_file(path)
        ts_raw = data.get("dump_timestamp_utc", "")
        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        batch, _ = ImportBatch.objects.update_or_create(
            manifest_self_hash=manifest_hash,
            defaults={
                "batch_name": self.batch_name,
                "game_version": data.get("game_version", ""),
                "unity_version": data.get("unity_version", ""),
                "dump_mod_version": data.get("dump_mod_version", ""),
                "dump_schema_version": data.get("dump_schema_version", ""),
                "source_method": data.get("source_method", ""),
                "dump_timestamp_utc": ts,
            },
        )
        ArtifactChecksum.objects.filter(import_batch=batch).delete()
        for filename, expected in (data.get("file_hashes") or {}).items():
            fpath = self._path(filename)
            actual = sha256_file(fpath) if fpath.is_file() else ""
            ArtifactChecksum.objects.create(
                import_batch=batch,
                artifact_filename=filename,
                expected_sha256=expected,
                import_status="ok" if actual == expected else "mismatch",
                is_incomplete=filename in (data.get("incomplete_sections") or []),
            )
        ExportWarning.objects.filter(import_batch=batch).delete()
        for idx, msg in enumerate(data.get("warnings") or []):
            ExportWarning.objects.create(import_batch=batch, warning_index=idx, message=str(msg))
        ExportIncompleteSection.objects.filter(import_batch=batch).delete()
        for section in data.get("incomplete_sections") or []:
            ExportIncompleteSection.objects.create(import_batch=batch, section_code=str(section))
        if self.ctx:
            self.ctx.bump("import_batch")
        return batch

    def _source_object(
        self,
        filename: str,
        index: int,
        row: dict[str, Any],
        *,
        source_path: str = "",
        system_id: str = "",
        clr_type: str = "",
    ) -> SourceObject:
        assert self.ctx is not None
        return self.ctx.record_source_row(
            filename,
            index,
            row,
            source_path=source_path,
            system_id=system_id,
            clr_type=clr_type,
        )

    def _import_fluids(self) -> None:
        assert self.ctx is not None
        rows = load_json(self._path("fluids.json"))
        for i, row in enumerate(rows):
            color_name = dig(row, "definition_snapshot", "Color", "name", default="")
            if not color_name:
                continue
            cid = identifiers.canonical_fluid_color(color_name)
            FluidColor.objects.update_or_create(
                canonical_id=cid,
                defaults={
                    "import_batch": self.ctx.batch,
                    "color_name": color_name,
                    "source_stable_id": str(row.get("stable_id", "")),
                    "source_row_index": i,
                },
            )
            self.ctx.bump("fluid_color")

    def _import_shapes(self, *, catalog_source: str, filename: str) -> None:
        assert self.ctx is not None
        rows = load_json(self._path(filename))
        import_shape_rows(
            self.ctx,
            catalog_source=catalog_source,
            filename=filename,
            rows=rows,
            record_source_row=self._source_object,
        )

    def _import_building_variants(self) -> None:
        assert self.ctx is not None
        rows = load_json(self._path("building_variants.json"))
        for i, row in enumerate(rows):
            snap = row.get("definition_snapshot") or {}
            internal = str(dig(snap, "Id", "Name", default=""))
            if not internal:
                continue
            cid = identifiers.canonical_building_variant(internal)
            src = self._source_object("building_variants.json", i, row)
            variant, _ = BuildingVariant.objects.update_or_create(
                canonical_id=cid,
                defaults={
                    "import_batch": self.ctx.batch,
                    "internal_name": internal,
                    "source_stable_id": str(row.get("stable_id", "")),
                    "display_name_key": str(row.get("display_name_key", "")),
                    "is_mirrored": internal.endswith("Mirrored"),
                    "size_x": int(
                        dig(snap, "ConnectorData", "TileDimensions", "x", default=0) or 0
                    ),
                    "size_y": int(
                        dig(snap, "ConnectorData", "TileDimensions", "y", default=0) or 0
                    ),
                    "size_z": int(
                        dig(snap, "ConnectorData", "TileDimensions", "z", default=0) or 0
                    ),
                    "source_row_index": i,
                    "source_object": src,
                },
            )
            connectors = dig(snap, "ConnectorData", "AllBuildingConnectors", default=[]) or []
            variant.connector_count = len(connectors)
            variant.save(update_fields=["connector_count"])
            BuildingConnector.objects.filter(building_variant=variant).delete()
            for oi, conn in enumerate(connectors):
                role = str(conn.get("$type", "unknown")).rsplit(".", maxsplit=1)[-1]
                pos = conn.get("Position_L") or {}
                BuildingConnector.objects.create(
                    canonical_id=identifiers.canonical_connector(cid, oi),
                    building_variant=variant,
                    order_index=oi,
                    connector_role=role[:64],
                    tile_direction=str(dig(conn, "TileDirection", "Value", default="")),
                    io_channel_type=str(conn.get("IOType", "")),
                    has_seperators=bool(conn.get("Seperators")),
                    position_x=int(pos.get("x", 0) or 0),
                    position_y=int(pos.get("y", 0) or 0),
                    position_z=int(pos.get("z", 0) or 0),
                )
            BuildingFootprintTile.objects.filter(building_variant=variant).delete()
            for oi, tile in enumerate(dig(snap, "ConnectorData", "Tiles", default=[]) or []):
                BuildingFootprintTile.objects.create(
                    canonical_id=identifiers.canonical_footprint_tile(cid, oi),
                    building_variant=variant,
                    order_index=oi,
                    x=int(tile.get("x", 0) or 0),
                    y=int(tile.get("y", 0) or 0),
                    z=int(tile.get("z", 0) or 0),
                )
            self.ctx.bump("building_variant")

    def _upsert_building_group(
        self,
        row: dict[str, Any],
        *,
        filename: str,
        index: int,
        profile: str,
    ) -> BuildingGroup | None:
        assert self.ctx is not None
        group_key = str(
            row.get("source_guid") or dig(row, "definition_snapshot", "Id", "Id", default="")
        )
        if not group_key:
            return None
        snap = row.get("definition_snapshot") or {}
        cid = identifiers.canonical_building_group(group_key)
        src = self._source_object(filename, index, row)
        group, _ = BuildingGroup.objects.update_or_create(
            canonical_id=cid,
            defaults={
                "import_batch": self.ctx.batch,
                "group_key": group_key,
                "registry_stable_id": str(row.get("stable_id", "")),
                "display_profile": profile,
                "display_name_key": str(row.get("display_name_key", "")),
                "is_transport_building": bool(dig(snap, "IsTransportBuilding", default=False)),
                "placement_mode": str(dig(snap, "DefaultPreferredPlacementMode", default="")),
                "player_buildable": bool(dig(snap, "PlayerBuildable", default=True)),
                "selectable": bool(dig(snap, "Selectable", default=True)),
                "removable": bool(dig(snap, "Removable", default=True)),
                "auto_connect": bool(dig(snap, "AutoConnect", default=False)),
                "source_row_index": index,
                "source_object": src,
            },
        )
        sim = row.get("simulation_parameters") or {}
        BuildingSimulationSetting.objects.update_or_create(
            building_group=group,
            defaults={
                "is_transport_building": bool(sim.get("IsTransportBuilding", False)),
                "pipette_override_id": str(dig(sim, "PipetteOverrideId", "Id", default="")),
                "show_stat_belt_processing_time": bool(
                    sim.get("ShowStatBeltProcessingTime", False)
                ),
                "show_stat_buildings_per_full_belt": bool(
                    sim.get("ShowStatBuildingsPerFullBelt", False)
                ),
                "show_in_speed_overview": bool(sim.get("ShowInSpeedOverview", False)),
            },
        )
        if profile == BuildingGroup.DisplayProfile.LAZY:
            BuildingLocalizationOverlay.objects.update_or_create(
                building_group=group,
                defaults={
                    "title_key": str(row.get("display_name_key", "")),
                    "description_key": str(row.get("description_key", "")),
                    "lazy_text_namespace": "building-variant",
                },
            )
        BuildingGroupMember.objects.filter(building_group=group).delete()
        for oi, member in enumerate(snap.get("Definitions") or []):
            internal = str(dig(member, "Id", "Name", default=""))
            variant = (
                BuildingVariant.objects.filter(internal_name=internal).first() if internal else None
            )
            resolution = BuildingGroupMember.MemberResolution.EMBEDDED
            cycle = ""
            if "$cycle" in member:
                resolution = BuildingGroupMember.MemberResolution.CYCLE_REF
                cycle = str(member.get("$cycle", ""))
            BuildingGroupMember.objects.create(
                canonical_id=identifiers.canonical_group_member(cid, oi),
                building_group=group,
                building_variant=variant,
                order_index=oi,
                member_resolution=resolution,
                internal_variant_name=internal,
                cycle_label=cycle,
            )
        BuildingPlacementRule.objects.filter(building_group=group).delete()
        for oi, rule in enumerate(snap.get("PlacementRequirements") or []):
            kind = str(rule.get("$type", "unknown")).rsplit(".", maxsplit=1)[-1]
            BuildingPlacementRule.objects.create(
                canonical_id=identifiers.canonical_placement_rule(cid, oi),
                building_group=group,
                order_index=oi,
                rule_kind=kind[:128],
            )
        record_assembly_reflection_audit(
            self.ctx,
            owner_key=group_key,
            definition_snapshot=snap if isinstance(snap, dict) else {},
        )
        return group

    def _import_building_groups(self) -> None:
        assert self.ctx is not None
        rows = load_json(self._path("building_groups.json"))
        for i, row in enumerate(rows):
            if self._upsert_building_group(
                row,
                filename="building_groups.json",
                index=i,
                profile=BuildingGroup.DisplayProfile.LAZY,
            ):
                self.ctx.bump("building_group")

    def _import_buildings_plain(self) -> None:
        assert self.ctx is not None
        rows = load_json(self._path("buildings.json"))
        for i, row in enumerate(rows):
            if self._upsert_building_group(
                row, filename="buildings.json", index=i, profile=BuildingGroup.DisplayProfile.PLAIN
            ):
                self.ctx.bump("building_group_plain")

    def _import_content_assets(self) -> None:
        assert self.ctx is not None
        specs = [
            ("prefabs.json", GameContentAsset.ContentKind.PREFAB, "prefab_path"),
            ("sprites.json", GameContentAsset.ContentKind.SPRITE, "sprite_path"),
            ("materials.json", GameContentAsset.ContentKind.MATERIAL, "material_path"),
        ]
        for filename, kind, path_key in specs:
            rows = load_json(self._path(filename))
            for i, row in enumerate(rows):
                stable = str(row.get("stable_id", ""))
                path = str(row.get(path_key, ""))
                cid = identifiers.canonical_content_asset(kind, stable)
                src = self._source_object(filename, i, row)
                GameContentAsset.objects.update_or_create(
                    canonical_id=cid,
                    defaults={
                        "import_batch": self.ctx.batch,
                        "content_kind": kind,
                        "source_stable_id": stable,
                        "content_path": path,
                        "logical_path": str(row.get("source_path", path)),
                        "display_name_key": str(row.get("display_name_key", "")),
                        "dump_source_type": str(row.get("source_type_name", "")),
                        "unity_source_guid": str(row.get("source_guid", "")),
                        "source_row_index": i,
                        "source_object": src,
                    },
                )
                self.ctx.bump("game_content_asset")

    def _import_asset_meta(self) -> None:
        assert self.ctx is not None
        rows = load_json(self._path("asset_references.json"))
        for i, row in enumerate(rows):
            meta_stable = str(row.get("stable_id", ""))
            content_stable = str(row.get("ref_stable_id", ""))
            kind = str(row.get("asset_type", "prefab")).lower()
            asset = GameContentAsset.objects.filter(
                source_stable_id=content_stable, content_kind=kind
            ).first()
            if not asset:
                continue
            cid = identifiers.canonical_meta_reference(meta_stable)
            AssetMetaReference.objects.update_or_create(
                canonical_id=cid,
                defaults={
                    "import_batch": self.ctx.batch,
                    "meta_stable_id": meta_stable,
                    "content_asset": asset,
                    "logical_path": str(row.get("source_path", "")),
                    "display_name_key": str(row.get("display_name_key", "")),
                    "source_row_index": i,
                },
            )
            self.ctx.bump("asset_meta_reference")

    def _upsert_lazy_localized_text(
        self,
        raw: Any,
        *,
        owner_model: str,
        owner_key: str,
    ) -> LazyLocalizedTextRef | None:
        assert self.ctx is not None
        parsed = parse_lazy_localized_text(raw)
        if parsed is None:
            return None
        if isinstance(raw, dict):
            for unknown_key in parsed.unknown_top_level_keys:
                self.ctx.record_unknown(
                    owner_model,
                    owner_key,
                    f"LazyLocalizedText.{unknown_key}",
                    unknown_key,
                    raw.get(unknown_key),
                )
        try:
            cid = identifiers.canonical_lazy_localized_text(
                parsed.message_key,
                cycle_reference=parsed.cycle_reference,
            )
        except InvalidCanonicalIdError:
            return None
        ref, _ = LazyLocalizedTextRef.objects.update_or_create(
            canonical_id=cid,
            defaults={
                "import_batch": self.ctx.batch,
                "message_key": parsed.message_key,
                "lazy_text_type": parsed.lazy_text_type,
                "placeholder_resolver_type": parsed.placeholder_resolver_type,
                "is_cycle_reference": parsed.is_cycle_reference,
                "cycle_reference": parsed.cycle_reference,
            },
        )
        LazyLocalizedPlaceholderReplacement.objects.filter(lazy_text=ref).delete()
        for order_index, replacement in enumerate(parsed.replacements):
            LazyLocalizedPlaceholderReplacement.objects.create(
                canonical_id=identifiers.canonical_lazy_localized_replacement(
                    cid, replacement.replacement_key
                ),
                lazy_text=ref,
                replacement_key=replacement.replacement_key,
                value_kind=replacement.value_kind,
                nested_message_key=replacement.nested_message_key,
                value_preview=replacement.value_preview,
                order_index=order_index,
            )
        self.ctx.bump("lazy_localized_text_ref")
        if parsed.replacements:
            self.ctx.bump("lazy_localized_placeholder_replacement", len(parsed.replacements))
        return ref

    def _import_research(self) -> None:
        assert self.ctx is not None
        rows = load_json(self._path("research_unlocks.json"))
        for _i, row in enumerate(rows):
            stype = str(row.get("source_type_name", ""))
            snap = row.get("definition_snapshot") or row.get("manager_snapshot") or {}
            stable = str(row.get("stable_id", ""))
            if "ResearchUpgradeId" in stype or snap.get("$type", "").endswith("ResearchUpgradeId"):
                key = str(snap.get("Id") or dig(snap, "Id", "Id", default=""))
                if key:
                    cid = identifiers.canonical_research_upgrade(key)
                    ResearchUpgrade.objects.update_or_create(
                        canonical_id=cid,
                        defaults={
                            "import_batch": self.ctx.batch,
                            "upgrade_key": key,
                            "source_stable_id": stable,
                        },
                    )
                    self.ctx.bump("research_upgrade")
            elif "ResearchMechanicId" in stype:
                key = str(snap.get("Id") or dig(snap, "Id", "Id", default=""))
                if key:
                    ResearchMechanic.objects.update_or_create(
                        canonical_id=identifiers.canonical_research_mechanic(key),
                        defaults={
                            "import_batch": self.ctx.batch,
                            "mechanic_key": key,
                            "source_stable_id": stable,
                        },
                    )
                    self.ctx.bump("research_mechanic")
            elif "ResearchLevel" in stype:
                key = str(dig(snap, "Id", "Id", default=""))
                if key:
                    title_lazy = self._upsert_lazy_localized_text(
                        snap.get("Title"),
                        owner_model="ResearchMilestone",
                        owner_key=key,
                    )
                    description_lazy = self._upsert_lazy_localized_text(
                        snap.get("Description"),
                        owner_model="ResearchMilestone",
                        owner_key=key,
                    )
                    src = self._source_object("research_unlocks.json", _i, row)
                    ResearchMilestone.objects.update_or_create(
                        canonical_id=identifiers.canonical_research_node("milestone", key),
                        defaults={
                            "import_batch": self.ctx.batch,
                            "node_key": key,
                            "title_lazy": title_lazy,
                            "description_lazy": description_lazy,
                            "source_stable_id": stable,
                            "source_object": src,
                        },
                    )
                    self._import_research_costs(snap, milestone_key=key)
                    self._import_research_prerequisites(
                        snap,
                        parent_kind="milestone",
                        parent_key=key,
                    )
                    self.ctx.bump("research_milestone")
            elif "ResearchSideQuest" in stype:
                key = str(dig(snap, "Id", "Id", default=""))
                if key:
                    title_lazy = self._upsert_lazy_localized_text(
                        snap.get("Title"),
                        owner_model="ResearchSideQuest",
                        owner_key=key,
                    )
                    description_lazy = self._upsert_lazy_localized_text(
                        snap.get("Description"),
                        owner_model="ResearchSideQuest",
                        owner_key=key,
                    )
                    quest, _ = ResearchSideQuest.objects.update_or_create(
                        canonical_id=identifiers.canonical_research_node("side_quest", key),
                        defaults={
                            "import_batch": self.ctx.batch,
                            "node_key": key,
                            "title_lazy": title_lazy,
                            "description_lazy": description_lazy,
                            "source_stable_id": stable,
                        },
                    )
                    self._import_research_costs(snap, side_quest=quest)
                    self._import_research_prerequisites(
                        snap,
                        parent_kind="side_quest",
                        parent_key=key,
                    )
                    self.ctx.bump("research_side_quest")
            elif "ResearchSideUpgrade" in stype:
                key = str(dig(snap, "Id", "Id", default=""))
                if key:
                    ResearchSideUpgrade.objects.update_or_create(
                        canonical_id=identifiers.canonical_research_node("side_upgrade", key),
                        defaults={
                            "import_batch": self.ctx.batch,
                            "node_key": key,
                            "source_stable_id": stable,
                        },
                    )
                    self.ctx.bump("research_side_upgrade")

    def _import_research_prerequisites(
        self,
        snap: dict[str, Any],
        *,
        parent_kind: str,
        parent_key: str,
    ) -> None:
        assert self.ctx is not None

        def _ref_key(item: object) -> str:
            if isinstance(item, dict):
                raw = item.get("Id")
                if isinstance(raw, dict):
                    return str(raw.get("Id", "") or "")
                return str(raw or "")
            return str(item)

        for item in snap.get("RequiredUpgrades") or []:
            key = _ref_key(item)
            if not key:
                continue
            upgrade = ResearchUpgrade.objects.filter(upgrade_key=key).first()
            cid = identifiers.canonical_research_prerequisite(
                parent_kind, parent_key, "upgrade", key
            )
            ResearchPrerequisite.objects.update_or_create(
                canonical_id=cid,
                defaults={
                    "parent_kind": parent_kind,
                    "parent_key": parent_key,
                    "required_upgrade": upgrade,
                    "required_mechanic": None,
                },
            )
            self.ctx.bump("research_prerequisite")

        for item in snap.get("RequiredMechanics") or []:
            key = _ref_key(item)
            if not key:
                continue
            mechanic = ResearchMechanic.objects.filter(mechanic_key=key).first()
            cid = identifiers.canonical_research_prerequisite(
                parent_kind, parent_key, "mechanic", key
            )
            ResearchPrerequisite.objects.update_or_create(
                canonical_id=cid,
                defaults={
                    "parent_kind": parent_kind,
                    "parent_key": parent_key,
                    "required_upgrade": None,
                    "required_mechanic": mechanic,
                },
            )
            self.ctx.bump("research_prerequisite")

    def _import_research_costs(
        self,
        snap: dict[str, Any],
        *,
        milestone_key: str = "",
        side_quest: ResearchSideQuest | None = None,
    ) -> None:
        assert self.ctx is not None
        costs = snap.get("Costs") or []
        milestone = None
        if milestone_key:
            milestone = ResearchMilestone.objects.filter(node_key=milestone_key).first()
        for oi, cost in enumerate(costs):
            shape_hash = str(cost.get("ShapeHash", ""))
            recipe = ShapeRecipe.objects.filter(shape_hash=shape_hash).first()
            if not recipe:
                continue
            parent_kind = (
                ResearchUnlockCost.ParentKind.SIDE_QUEST
                if side_quest
                else ResearchUnlockCost.ParentKind.MILESTONE
            )
            parent_id = side_quest.node_key if side_quest else milestone_key
            cid = identifiers.canonical_research_cost(parent_kind, parent_id, oi, shape_hash)
            ResearchUnlockCost.objects.update_or_create(
                canonical_id=cid,
                defaults={
                    "parent_kind": parent_kind,
                    "milestone": milestone,
                    "side_quest": side_quest,
                    "shape_recipe": recipe,
                    "order_index": oi,
                    "amount": int(cost.get("Amount", 1) or 1),
                },
            )

    def _import_simulation_systems(self) -> None:
        assert self.ctx is not None
        rows = load_json(self._path("simulation_systems.json"))
        import_simulation_systems(self.ctx, rows)

    def _import_toolbar(self) -> None:
        assert self.ctx is not None
        rows = load_json(self._path("toolbar_entries.json"))
        import_toolbar_tree(self.ctx, rows)

    def _import_translations_status(self) -> None:
        assert self.ctx is not None
        path = self._path("translations.json")
        rows = load_json(path)
        LocalizationExportStatus.objects.update_or_create(
            import_batch=self.ctx.batch,
            defaults={
                "is_empty": len(rows) == 0,
                "is_incomplete": True,
                "expected_hash": sha256_file(path),
            },
        )
        self.ctx.bump("localization_export_status")

    def _import_transport_registry(self) -> None:
        assert self.ctx is not None
        rows = load_json(self._path("belts_pipes_transport.json"))
        for i, row in enumerate(rows):
            kind = str(row.get("transport_kind", ""))
            if not kind:
                continue
            snap = row.get("definition_snapshot") or {}
            internal = str(dig(snap, "Id", "Name", default=""))
            variant = BuildingVariant.objects.filter(internal_name=internal).first()
            if not variant:
                continue
            cid = identifiers.canonical_transport_kind(kind)
            TransportBuildingRegistry.objects.update_or_create(
                canonical_id=cid,
                defaults={
                    "import_batch": self.ctx.batch,
                    "transport_kind": kind,
                    "transport_category": classifiers.transport_category(kind),
                    "building_variant": variant,
                    "display_name_key": str(row.get("display_name_key", "")),
                    "source_row_index": i,
                },
            )
            self.ctx.bump("transport_building_registry")

    def _import_clr_types(self) -> None:
        assert self.ctx is not None
        from django_apps.game_data.models import ClrTypeRegistryEntry

        rows = load_json(self._path("raw_type_index.json"))
        for i, row in enumerate(rows):
            tname = str(row.get("type_name", ""))
            assembly = str(row.get("assembly_name", ""))
            if not tname:
                continue
            cid = identifiers.canonical_clr_type(tname, assembly)
            ClrTypeRegistryEntry.objects.update_or_create(
                canonical_id=cid,
                defaults={
                    "import_batch": self.ctx.batch,
                    "type_name": tname,
                    "assembly_name": assembly,
                    "source_stable_id": str(row.get("stable_id", "")),
                    "is_compiler_generated": "<" in tname,
                    "source_row_index": i,
                },
            )
            self.ctx.bump("clr_type_registry_entry")
