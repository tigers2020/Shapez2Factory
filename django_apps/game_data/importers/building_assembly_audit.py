"""Record building Assembly/DeclaredMembers as reflection metadata (ignore_audit)."""

from __future__ import annotations

from django_apps.game_data.coverage.reason_codes import REFLECTION_METADATA
from django_apps.game_data.importers.base import ImportContext

_REFLECTION_KEYS = frozenset({"Assembly", "DeclaredMembers"})
_MAX_DEPTH = 14


def _scan_reflection(
    obj: object,
    path: str,
    *,
    ctx: ImportContext,
    owner_key: str,
    recorded: set[str],
    depth: int,
) -> None:
    if depth > _MAX_DEPTH or len(recorded) >= 4:
        return
    if isinstance(obj, dict):
        for key, val in obj.items():
            child_path = f"{path}.{key}" if path else key
            if key in _REFLECTION_KEYS and child_path not in recorded:
                recorded.add(child_path)
                ctx.record_unknown(
                    owner_model="building_group",
                    owner_key=owner_key,
                    json_path=child_path,
                    key=key,
                    value=val if not isinstance(val, list) else f"list[{len(val)}]",
                    reason_code=REFLECTION_METADATA,
                    classification="assembly_reflection",
                )
            _scan_reflection(
                val,
                child_path,
                ctx=ctx,
                owner_key=owner_key,
                recorded=recorded,
                depth=depth + 1,
            )
    elif isinstance(obj, list) and depth < _MAX_DEPTH:
        for i, item in enumerate(obj[:32]):
            _scan_reflection(
                item,
                f"{path}[{i}]",
                ctx=ctx,
                owner_key=owner_key,
                recorded=recorded,
                depth=depth + 1,
            )


def record_assembly_reflection_audit(
    ctx: ImportContext,
    *,
    owner_key: str,
    definition_snapshot: dict[str, object],
) -> None:
    if not isinstance(definition_snapshot, dict):
        return
    _scan_reflection(
        definition_snapshot,
        "definition_snapshot",
        ctx=ctx,
        owner_key=owner_key,
        recorded=set(),
        depth=0,
    )
