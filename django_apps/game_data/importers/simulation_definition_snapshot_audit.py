"""Record definition_snapshot ignore_audit coverage for SimulationSystem rows."""

from __future__ import annotations

from django_apps.game_data.coverage.disposition import Disposition
from django_apps.game_data.coverage.simulation_paths import classify_norm_path
from django_apps.game_data.importers.base import ImportContext

_MAX_RECORDS = 40
_LIST_HEAVY = ("ChainPositions", "TileBasedSystems", "k__BackingField", "Listeners")


def _norm_path(prefix: str) -> str:
    if not prefix:
        return "definition_snapshot"
    return f"definition_snapshot.{prefix}"


def _should_record_prefix(path: str) -> bool:
    return any(marker in path for marker in _LIST_HEAVY)


def sync_definition_snapshot_coverage_audit(
    ctx: ImportContext,
    *,
    owner_key: str,
    definition_snapshot: dict[str, object] | None,
) -> int:
    if not isinstance(definition_snapshot, dict):
        return 0

    recorded = 0
    seen: set[str] = set()

    def _record(path: str, key: str, value: object) -> None:
        nonlocal recorded
        if recorded >= _MAX_RECORDS or path in seen:
            return
        classified = classify_norm_path(path)
        if not classified or classified[0] != Disposition.IGNORE_AUDIT:
            return
        ctx.record_unknown(
            "SimulationSystem",
            owner_key,
            path,
            key,
            value,
            reason_code=classified[1],
            classification="definition_snapshot_coverage",
        )
        seen.add(path)
        recorded += 1

    def walk(obj: object, prefix: str) -> None:
        if recorded >= _MAX_RECORDS:
            return
        if isinstance(obj, dict):
            for key, val in obj.items():
                sub = f"{prefix}.{key}" if prefix else key
                path = _norm_path(sub)
                if _should_record_prefix(sub) or not isinstance(val, (dict, list)):
                    _record(path, key, val)
                walk(val, sub)
        elif isinstance(obj, list) and prefix:
            path = _norm_path(prefix)
            if _should_record_prefix(prefix):
                _record(path, prefix.rsplit(".", 1)[-1], obj)
            for item in obj[:3]:
                walk(item, f"{prefix}[]")

    walk(definition_snapshot, "")
    return recorded
