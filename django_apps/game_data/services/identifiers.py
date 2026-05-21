"""Canonical ID policy: domain keys only, never runtime CLR names."""

from __future__ import annotations

import hashlib
import re

_RUNTIME_TYPE_RE = re.compile(
    r"(PublicKeyToken|Version=|`\d|Game\.Content\.|UnityEngine\.|AtomicStateful)",
)


class InvalidCanonicalIdError(ValueError):
    pass


def reject_runtime_canonical(candidate: str) -> str:
    if _RUNTIME_TYPE_RE.search(candidate):
        raise InvalidCanonicalIdError(f"runtime/reflection string rejected: {candidate[:80]}")
    return candidate


def _slug(*parts: str) -> str:
    return ":".join(str(p).strip() for p in parts if str(p).strip())


def canonical_import_batch(manifest_hash: str) -> str:
    return reject_runtime_canonical(_slug("batch", manifest_hash))


def canonical_content_asset(kind: str, stable_id: str) -> str:
    return reject_runtime_canonical(_slug("asset", kind, stable_id))


def canonical_meta_reference(meta_stable_id: str) -> str:
    return reject_runtime_canonical(_slug("meta", meta_stable_id))


def canonical_fluid_color(color_name: str) -> str:
    return reject_runtime_canonical(_slug("fluid", color_name))


def canonical_shape_recipe(operation_uid: int, shape_hash: str) -> str:
    return reject_runtime_canonical(_slug("shape", str(operation_uid), shape_hash))


def canonical_shape_layer(recipe_cid: str, layer_index: int) -> str:
    return _slug(recipe_cid, "layer", str(layer_index))


def canonical_quadrant_slot(layer_cid: str, quadrant_index: int) -> str:
    return _slug(layer_cid, "q", str(quadrant_index))


def canonical_component_kind(component_key: str) -> str:
    return reject_runtime_canonical(_slug("component", component_key))


def canonical_building_variant(internal_name: str) -> str:
    return reject_runtime_canonical(_slug("variant", internal_name))


def canonical_building_group(group_key: str) -> str:
    return reject_runtime_canonical(_slug("building_group", group_key))


def canonical_connector(variant_cid: str, order_index: int) -> str:
    return _slug(variant_cid, "connector", str(order_index))


def canonical_footprint_tile(variant_cid: str, order_index: int) -> str:
    return _slug(variant_cid, "tile", str(order_index))


def canonical_group_member(group_cid: str, order_index: int) -> str:
    return _slug(group_cid, "member", str(order_index))


def canonical_placement_rule(group_cid: str, order_index: int) -> str:
    return _slug(group_cid, "rule", str(order_index))


def canonical_transport_kind(transport_kind: str) -> str:
    return reject_runtime_canonical(_slug("transport", transport_kind))


def canonical_research_upgrade(upgrade_key: str) -> str:
    return reject_runtime_canonical(_slug("upgrade", upgrade_key))


def canonical_research_mechanic(mechanic_key: str) -> str:
    return reject_runtime_canonical(_slug("mechanic", mechanic_key))


def canonical_research_node(kind: str, node_key: str) -> str:
    return reject_runtime_canonical(_slug("research", kind, node_key))


def canonical_lazy_localized_text(message_key: str, *, cycle_reference: str = "") -> str:
    key = message_key.strip() or cycle_reference.strip()
    if not key:
        raise InvalidCanonicalIdError("lazy localized text requires message_key or cycle_reference")
    return reject_runtime_canonical(_slug("lazytext", key))


def canonical_lazy_localized_replacement(lazy_cid: str, replacement_key: str) -> str:
    return _slug(lazy_cid, "repl", replacement_key)


def canonical_research_cost(
    parent_kind: str, parent_id: str, order_index: int, shape_hash: str
) -> str:
    return _slug("cost", parent_kind, parent_id, str(order_index), shape_hash)


def canonical_toolbar_node(
    *,
    source_stable_id: str,
    parent_canonical_id: str,
    child_index: int,
) -> str:
    if source_stable_id:
        return reject_runtime_canonical(_slug("toolbar-node", source_stable_id))
    return reject_runtime_canonical(_slug("toolbar-node", parent_canonical_id, str(child_index)))


def canonical_toolbar_element(stable_key: str) -> str:
    return reject_runtime_canonical(_slug("toolbar-action", stable_key))


def canonical_simulation_entry(batch_id: int, row_index: int) -> str:
    return _slug("sim", str(batch_id), str(row_index))


def canonical_clr_type(type_name: str, assembly_name: str) -> str:
    """Hash (type_name, assembly_name) — CLR names may contain UnityEngine.* segments."""
    payload = f"{assembly_name}\0{type_name}".encode()
    digest = hashlib.sha256(payload).hexdigest()[:32]
    return _slug("clr", digest)


def hash_preview(value: object) -> tuple[str, str]:
    text = repr(value)[:500]
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return text, digest
