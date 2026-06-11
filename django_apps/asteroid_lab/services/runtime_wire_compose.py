"""Load, validate, and project solver runtime wires into Lab replay frames."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
    build_solver_runtime_replay_frames,
)
from django_apps.asteroid_lab.services.artifact_manifest_reader import ArtifactManifestRecord
from django_apps.asteroid_lab.services.lab_replay_diagnostics import (
    DIAGNOSTIC_MISSING_RUNTIME_WIRES,
    DIAGNOSTIC_RUNTIME_WIRE_COMPLETE_MAP_MISMATCH,
    DIAGNOSTIC_RUNTIME_WIRE_L3_ORDER_INVALID,
    DIAGNOSTIC_RUNTIME_WIRE_L4_PLACEMENT_MISMATCH,
    DIAGNOSTIC_RUNTIME_WIRE_LAYER_FAILED,
    DIAGNOSTIC_RUNTIME_WIRE_LAYER_PARTIAL_BUDGET,
    DIAGNOSTIC_RUNTIME_WIRE_LAYER_SKIPPED,
    DIAGNOSTIC_RUNTIME_WIRE_SCHEMA_UNKNOWN,
    diagnostic_severity_for_reason,
)
from shapez2_factory.adapters.asteroid_lab.runtime_wires.deserialize import (
    RuntimeWiresProjectionBundle,
    deserialize_l3_wire,
    deserialize_l4_wire,
    deserialize_l5_wire,
)
from shapez2_factory.adapters.asteroid_lab.runtime_wires.envelope import (
    COMPLETE_MAP_MANIFEST_PATH_KEY,
    MANIFEST_PATH_KEY,
    RUNTIME_WIRES_ARTIFACT_REL_PATH,
    RUNTIME_WIRES_SCHEMA_VERSION,
    LayerOutcome,
    RuntimeWireValidationError,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
)

_LAYER_SLUGS_IN_ORDER = (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
)

_VALIDATION_CODE_TO_DIAGNOSTIC: dict[str, str] = {
    "runtime_wire_schema_unknown": DIAGNOSTIC_RUNTIME_WIRE_SCHEMA_UNKNOWN,
    "runtime_wire_l3_order_invalid": DIAGNOSTIC_RUNTIME_WIRE_L3_ORDER_INVALID,
    "runtime_wire_l4_placement_mismatch": DIAGNOSTIC_RUNTIME_WIRE_L4_PLACEMENT_MISMATCH,
}


@dataclass(frozen=True, slots=True)
class RuntimeWireLoadResult:
    ok: bool
    degraded_reason: str | None
    diagnostic_severity: str
    document: dict[str, Any] | None
    bundle: RuntimeWiresProjectionBundle | None


def _manifest_relpath(manifest: ArtifactManifestRecord, key: str) -> str | None:
    relpath = manifest.paths.get(key)
    if not isinstance(relpath, str) or not relpath:
        return None
    return relpath


def _resolve_artifact_path(root: Path, relpath: str) -> Path | None:
    resolved_root = root.resolve()
    path = (resolved_root / relpath).resolve()
    try:
        path.relative_to(resolved_root)
    except ValueError:
        return None
    return path


def _truncate_layers_for_projection(
    document: dict[str, Any],
) -> tuple[dict[str, Any], str | None]:
    layers_raw = document.get("layers")
    if not isinstance(layers_raw, dict):
        return document, None

    truncated_layers: dict[str, Any] = {}
    diagnostic_reason: str | None = None
    for slug in _LAYER_SLUGS_IN_ORDER:
        layer_wire = layers_raw.get(slug)
        if not isinstance(layer_wire, dict):
            continue
        outcome = str(layer_wire.get("outcome") or LayerOutcome.COMPLETED.value)
        if outcome == LayerOutcome.FAILED.value:
            diagnostic_reason = DIAGNOSTIC_RUNTIME_WIRE_LAYER_FAILED
            break
        if outcome == LayerOutcome.SKIPPED.value:
            diagnostic_reason = DIAGNOSTIC_RUNTIME_WIRE_LAYER_SKIPPED
            break
        truncated_layers[slug] = layer_wire
        if outcome == LayerOutcome.PARTIAL_BUDGET.value:
            diagnostic_reason = DIAGNOSTIC_RUNTIME_WIRE_LAYER_PARTIAL_BUDGET

    if truncated_layers == layers_raw:
        return document, diagnostic_reason

    return {**document, "layers": truncated_layers}, diagnostic_reason


def _deserialize_truncated_bundle(document: dict[str, Any]) -> RuntimeWiresProjectionBundle:
    layers = document.get("layers")
    if not isinstance(layers, dict):
        return RuntimeWiresProjectionBundle(
            exterior_plan_wire=None,
            rim_greedy=None,
            inner_fill=None,
            route_plan=None,
        )

    exterior_plan_wire: dict[str, Any] | None = None
    l2 = layers.get(LAYER_02_EXTERIOR_TRANSPORT)
    if isinstance(l2, dict):
        plan = l2.get("exterior_connector_plan")
        if isinstance(plan, dict):
            exterior_plan_wire = plan

    rim_greedy = None
    l3 = layers.get(LAYER_03_RIM_GREEDY_PLACEMENT)
    if isinstance(l3, dict):
        rim_greedy = deserialize_l3_wire(l3)

    inner_fill = None
    l4 = layers.get(LAYER_04_INNER_PATTERN_FILL)
    if isinstance(l4, dict):
        inner_fill = deserialize_l4_wire(l4)

    route_plan = None
    l5 = layers.get(LAYER_05_TRANSPORT_ROUTING)
    if isinstance(l5, dict):
        route_plan = deserialize_l5_wire(l5)

    return RuntimeWiresProjectionBundle(
        exterior_plan_wire=exterior_plan_wire,
        rim_greedy=rim_greedy,
        inner_fill=inner_fill,
        route_plan=route_plan,
    )


def load_and_validate_runtime_wires(
    root: Path,
    manifest: ArtifactManifestRecord,
) -> RuntimeWireLoadResult:
    """Load artifact runtime wires; return projection bundle or degraded reason."""

    wires_relpath = _manifest_relpath(manifest, MANIFEST_PATH_KEY)
    if wires_relpath is None:
        return RuntimeWireLoadResult(
            ok=False,
            degraded_reason=DIAGNOSTIC_MISSING_RUNTIME_WIRES,
            diagnostic_severity=diagnostic_severity_for_reason(DIAGNOSTIC_MISSING_RUNTIME_WIRES),
            document=None,
            bundle=None,
        )

    wires_path = _resolve_artifact_path(root, wires_relpath)
    if wires_path is None or not wires_path.is_file():
        return RuntimeWireLoadResult(
            ok=False,
            degraded_reason=DIAGNOSTIC_MISSING_RUNTIME_WIRES,
            diagnostic_severity=diagnostic_severity_for_reason(DIAGNOSTIC_MISSING_RUNTIME_WIRES),
            document=None,
            bundle=None,
        )

    try:
        payload = json.loads(wires_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return RuntimeWireLoadResult(
            ok=False,
            degraded_reason=DIAGNOSTIC_MISSING_RUNTIME_WIRES,
            diagnostic_severity=diagnostic_severity_for_reason(DIAGNOSTIC_MISSING_RUNTIME_WIRES),
            document=None,
            bundle=None,
        )

    if not isinstance(payload, dict):
        return RuntimeWireLoadResult(
            ok=False,
            degraded_reason=DIAGNOSTIC_MISSING_RUNTIME_WIRES,
            diagnostic_severity=diagnostic_severity_for_reason(DIAGNOSTIC_MISSING_RUNTIME_WIRES),
            document=None,
            bundle=None,
        )

    schema_version = payload.get("schema_version")
    if schema_version != RUNTIME_WIRES_SCHEMA_VERSION:
        return RuntimeWireLoadResult(
            ok=False,
            degraded_reason=DIAGNOSTIC_RUNTIME_WIRE_SCHEMA_UNKNOWN,
            diagnostic_severity=diagnostic_severity_for_reason(
                DIAGNOSTIC_RUNTIME_WIRE_SCHEMA_UNKNOWN
            ),
            document=None,
            bundle=None,
        )

    complete_map_relpath = manifest.paths.get(COMPLETE_MAP_MANIFEST_PATH_KEY)
    if not isinstance(complete_map_relpath, str):
        complete_map_relpath = "output/layer01_complete_map.json"
    expected_hash = manifest.content_hashes.get(complete_map_relpath)
    ref = payload.get("complete_map_ref")
    if isinstance(ref, dict):
        wire_hash = ref.get("content_hash")
        if expected_hash and wire_hash and wire_hash != expected_hash:
            return RuntimeWireLoadResult(
                ok=False,
                degraded_reason=DIAGNOSTIC_RUNTIME_WIRE_COMPLETE_MAP_MISMATCH,
                diagnostic_severity=diagnostic_severity_for_reason(
                    DIAGNOSTIC_RUNTIME_WIRE_COMPLETE_MAP_MISMATCH,
                ),
                document=None,
                bundle=None,
            )

    truncated_doc, partial_diagnostic = _truncate_layers_for_projection(payload)
    try:
        bundle = _deserialize_truncated_bundle(truncated_doc)
    except RuntimeWireValidationError as exc:
        degraded = _VALIDATION_CODE_TO_DIAGNOSTIC.get(
            exc.code, DIAGNOSTIC_RUNTIME_WIRE_SCHEMA_UNKNOWN
        )
        return RuntimeWireLoadResult(
            ok=False,
            degraded_reason=degraded,
            diagnostic_severity=diagnostic_severity_for_reason(degraded),
            document=None,
            bundle=None,
        )

    return RuntimeWireLoadResult(
        ok=True,
        degraded_reason=partial_diagnostic,
        diagnostic_severity=diagnostic_severity_for_reason(partial_diagnostic),
        document=truncated_doc,
        bundle=bundle,
    )


def compose_lab_replay_frames_from_runtime_wires(
    *,
    complete_map: ReconstructionCompleteMap,
    wires_doc: dict[str, Any],
    bundle: RuntimeWiresProjectionBundle,
    diagnostic_reason: str | None = None,
    diagnostic_severity: str = "none",
) -> list[dict[str, Any]]:
    """Project validated runtime wires via assembler (no solver layer execution)."""

    transport_summary = wires_doc.get("transport_summary")
    transport_kind = "shape_belt"
    if isinstance(transport_summary, dict):
        effective = transport_summary.get("effective_transport_kind")
        if isinstance(effective, str) and effective:
            transport_kind = effective

    frames = build_solver_runtime_replay_frames(
        complete_map=complete_map,
        lab_frames_before_append=(),
        exterior_plan_wire=bundle.exterior_plan_wire,
        layer03=bundle.rim_greedy,
        layer04=None,
        layer04_inner_fill=bundle.inner_fill,
        layer05_route_plan=bundle.route_plan,
        transport_kind=transport_kind,
    )

    for frame in frames:
        inspector = frame.setdefault("inspector", {})
        if isinstance(inspector, dict):
            inspector["replay_source"] = "artifact_runtime_wire_projection"
            inspector["wire_schema_version"] = RUNTIME_WIRES_SCHEMA_VERSION

    if frames:
        meta = frames[0].setdefault("inspector", {})
        if isinstance(meta, dict):
            meta["replay_compose_meta"] = {
                "diagnostic_reason": diagnostic_reason,
                "diagnostic_severity": diagnostic_severity,
                "replay_projection_mode": "runtime_wires_v1",
                "algorithm_rerun_count": 0,
                "wire_schema_version": RUNTIME_WIRES_SCHEMA_VERSION,
                "wire_content_hash": None,
            }

    return frames


def wire_content_hash_from_document(document: dict[str, Any]) -> str | None:
    import hashlib

    try:
        encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError):
        return None
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "RuntimeWireLoadResult",
    "compose_lab_replay_frames_from_runtime_wires",
    "load_and_validate_runtime_wires",
    "wire_content_hash_from_document",
    "RUNTIME_WIRES_ARTIFACT_REL_PATH",
]
