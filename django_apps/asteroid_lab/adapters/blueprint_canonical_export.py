"""Official-style Shapez2 v4 island blueprint JSON bytes + copy-string encoding.

``BP.Entries`` use **game raw** ``X`` (…, ``-1``, ``1``, ``2``, … — no column ``0``).
Export from lab raw positions uses ``raw_x_to_dense_index`` for horizontal anchoring
(``export_x = dense(raw_x) - dense(extractor_x)``) and ``export_y = raw_y - extractor_y - 1``.
Do not use ``raw_x - (extractor_x + 1)`` — it leaves a gap in dense columns for west branches.
"""

from __future__ import annotations

import base64
import gzip
import json
from typing import Any

from django_apps.asteroid_lab.snapshots.server_coords import raw_x_to_dense_index

SHAPEZ2_COPY_PREFIX_V4 = "SHAPEZ2-4-"

OFFICIAL_BINARY_VERSION = 1137

# Supported Shapez2 blueprint code version identifiers.
_SUPPORTED_VERSIONS: dict[int, str] = {
    4: SHAPEZ2_COPY_PREFIX_V4,
}


def resolve_blueprint_code_version(target_game_version: int) -> str:
    """Return the copy-string prefix for *target_game_version*.

    Raises ``ValueError`` for unsupported versions so callers fail loudly
    instead of producing silently mis-versioned blueprints.
    """
    prefix = _SUPPORTED_VERSIONS.get(int(target_game_version))
    if prefix is None:
        supported = sorted(_SUPPORTED_VERSIONS)
        raise ValueError(
            f"Unsupported target_game_version={target_game_version!r}. " f"Supported: {supported}"
        )
    return prefix


OFFICIAL_ISLAND_ICON: dict[str, Any] = {
    "Data": ["icon:Platforms", None, None, "shape:RuRuRuRu"],
}

# User-provided connected west+branch fluid pipe (game copy; no trailing ``=`` on payload).
_CONNECTED_BRANCH_B64_PAYLOAD = "H4sIAMsrC2oA/4yQzQrCMBCE32XwGA+lByFHUaGgUFSKRUQWGzEQ05IftJS8uzEF8SSysLDszLfLDKjAsyyfMcxL8AET13cCHIVVpBswFJdWvxcLcgR+hIwzLxW5a2vuFkx7pcYGe6NO8K0fC6fAsNTOSGGjccABfJox7CN9TX3r3XmlvGw2UguzfDqhrYynAvso6/gawxY8/8tV/+Anwd+kQzr8xdt1dBGl7MR51ZoHmQbhFBOTmkxfCZOMKcYQXgIMAFZBsdNSAQAA"  # noqa: E501

CONNECTED_BRANCH_FLUID_PIPE_COPY = f"{SHAPEZ2_COPY_PREFIX_V4}{_CONNECTED_BRANCH_B64_PAYLOAD}"
CONNECTED_BRANCH_FLUID_PIPE_GZIP = base64.b64decode(_CONNECTED_BRANCH_B64_PAYLOAD)
CONNECTED_BRANCH_FLUID_PIPE_JSON_BYTES = gzip.decompress(CONNECTED_BRANCH_FLUID_PIPE_GZIP)

_GAME_ENTRY_KEYS = frozenset({"X", "Y", "R", "T"})


def _as_int(val: Any) -> int:
    if val is None:
        return 0
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, int):
        return val
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _is_extractor_tile(t: str) -> bool:
    return t in ("Layout_FluidMiner", "Layout_ShapeMiner")


def _is_field_extension_tile(t: str) -> bool:
    return t in ("Layout_FluidMinerExtension", "Layout_ShapeMinerExtension")


_FIELD_EXPORT_TILES: frozenset[str] = frozenset(
    {
        "Layout_FluidMinerExtension",
        "Layout_ShapeMinerExtension",
    }
)


def _strip_lab_entry(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k in _GAME_ENTRY_KEYS:
        if k not in row:
            continue
        if k in ("X", "Y", "R"):
            out[k] = _as_int(row[k])
        else:
            out[k] = row[k]
    return out


def _export_anchor(entries: list[dict[str, Any]]) -> tuple[int, int]:
    """Anchor for lab → official XY: miner first, else min ``Layout_*MinerExtension``."""

    miners: list[tuple[int, int]] = []
    extensions: list[tuple[int, int]] = []
    for row in entries:
        t = str(row.get("T", ""))
        xy = (_as_int(row.get("X")), _as_int(row.get("Y")))
        if _is_extractor_tile(t):
            miners.append(xy)
        elif _is_field_extension_tile(t):
            extensions.append(xy)
    if miners:
        return min(miners)
    if extensions:
        return min(extensions)
    msg = "no Layout_*Miner or Layout_*MinerExtension anchor in BP.Entries for official export"
    raise ValueError(msg)


def _extractor_anchor(entries: list[dict[str, Any]]) -> tuple[int, int]:
    return _export_anchor(entries)


def _coords_look_like_game_export(entries: list[dict[str, Any]]) -> bool:
    """True when blueprint ``X`` values match in-game paste space (negative columns common)."""

    xs = [_as_int(row.get("X")) for row in entries if isinstance(row, dict)]
    return bool(xs) and min(xs) < 0


def strip_lab_fields_from_root(root: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow copy without lab-only top-level keys; entries lose ``server_*``."""

    bp_in = root.get("BP")
    if not isinstance(bp_in, dict):
        msg = "expected BP object"
        raise ValueError(msg)
    entries_raw = bp_in.get("Entries")
    if not isinstance(entries_raw, list):
        msg = "expected BP.Entries list"
        raise ValueError(msg)

    entries: list[dict[str, Any]] = []
    for item in entries_raw:
        if not isinstance(item, dict):
            continue
        clean = {k: v for k, v in item.items() if k not in ("server_x", "server_y")}
        entries.append(clean)

    bp: dict[str, Any] = {"$type": str(bp_in.get("$type", "Island")), "Entries": entries}
    for k in ("Icon", "BinaryVersion", "B"):
        if k in bp_in:
            bp[k] = bp_in[k]

    out: dict[str, Any] = {"V": root.get("V"), "BP": bp}
    for k, v in root.items():
        if k.startswith("_") or k in ("V", "BP"):
            continue
        out[k] = v
    return out


def translate_lab_entries_to_official_xy(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Lab raw ``X,Y`` → game export ``X,Y`` (dense column anchor).

    Let ``(ex_x, ex_y)`` be the extractor raw cell (minimum ``(X,Y)`` among miners). Let
    ``ex_dense = raw_x_to_dense_index(ex_x)``. For each entry raw ``(x, y)``:

    - ``export_x = raw_x_to_dense_index(x) - ex_dense``
    - ``export_y = raw_y - ex_y - 1``

    ``X=0`` / ``Y=0`` are omitted at serialize time. Same horizontal seam as
    ``server_coords`` / ``_asteroid_lab_coord_system``.
    """

    stripped = [_strip_lab_entry(dict(e)) for e in entries if isinstance(e, dict)]
    ex_x, ex_y = _extractor_anchor(stripped)
    ex_dense = raw_x_to_dense_index(ex_x)
    out: list[dict[str, Any]] = []
    for row in stripped:
        x = _as_int(row.get("X"))
        y = _as_int(row.get("Y"))
        ox = raw_x_to_dense_index(x) - ex_dense
        oy = y - ex_y - 1
        r = _as_int(row.get("R"))
        t = row.get("T")
        if not isinstance(t, str):
            msg = "each entry must have string T"
            raise ValueError(msg)
        out.append({"X": ox, "Y": oy, "R": r, "T": t})
    out.sort(key=lambda e: (_as_int(e.get("X")), _as_int(e.get("Y")), str(e.get("T", ""))))
    return out


def _field_export_entries(entries_raw: list[Any]) -> list[dict[str, Any]]:
    """Keep only Extension field tiles for in-game asteroid-field paste (no miners/pipes)."""

    out: list[dict[str, Any]] = []
    for item in entries_raw:
        if not isinstance(item, dict):
            continue
        t = str(item.get("T", ""))
        if t not in _FIELD_EXPORT_TILES:
            continue
        out.append(_strip_lab_entry(dict(item)))
    out.sort(key=lambda row: (_as_int(row.get("X")), _as_int(row.get("Y")), str(row.get("T", ""))))
    return out


def to_game_paste_island_root(lab_layout_root: dict[str, Any]) -> dict[str, Any]:
    """Build island JSON for in-game paste.

    Field tiles only (``Layout_*MinerExtension``). Game-import coordinates (``X < 0``) are kept;
    positive lab-space layouts use ``translate_lab_entries_to_official_xy``.
    """

    base = strip_lab_fields_from_root(lab_layout_root)
    bp_in = base["BP"]
    assert isinstance(bp_in, dict)
    entries_raw = bp_in.get("Entries")
    assert isinstance(entries_raw, list)
    field_entries = _field_export_entries(entries_raw)
    if not field_entries:
        msg = "no Layout_*MinerExtension field entries for game paste export"
        raise ValueError(msg)

    if _coords_look_like_game_export(field_entries):
        return {
            "V": OFFICIAL_BINARY_VERSION,
            "BP": {
                "$type": "Island",
                "Icon": dict(OFFICIAL_ISLAND_ICON),
                "Entries": field_entries,
                "BinaryVersion": OFFICIAL_BINARY_VERSION,
            },
        }

    tmp_root: dict[str, Any] = {
        "V": base.get("V", OFFICIAL_BINARY_VERSION),
        "BP": {
            "$type": "Island",
            "Icon": dict(OFFICIAL_ISLAND_ICON),
            "Entries": field_entries,
            "BinaryVersion": OFFICIAL_BINARY_VERSION,
        },
    }
    return to_official_island_root(tmp_root)


def to_official_island_root(lab_layout_root: dict[str, Any]) -> dict[str, Any]:
    """Build ``V``/``BP`` dict matching game island export (1137 + Icon + BinaryVersion)."""

    base = strip_lab_fields_from_root(lab_layout_root)
    bp_in = base["BP"]
    assert isinstance(bp_in, dict)
    entries_raw = bp_in.get("Entries")
    assert isinstance(entries_raw, list)
    official_entries = translate_lab_entries_to_official_xy(entries_raw)

    bp: dict[str, Any] = {
        "$type": "Island",
        "Icon": dict(OFFICIAL_ISLAND_ICON),
        "Entries": official_entries,
        "BinaryVersion": OFFICIAL_BINARY_VERSION,
    }
    return {"V": OFFICIAL_BINARY_VERSION, "BP": bp}


def _serialize_entry_row(x: int, y: int, r: int, t: str) -> str:
    parts: list[str] = []
    if x != 0:
        parts.append(f'"X":{x}')
    if y != 0:
        parts.append(f'"Y":{y}')
    if r != 0:
        parts.append(f'"R":{r}')
    parts.append(f'"T":{json.dumps(t, ensure_ascii=False)}')
    return "{" + ",".join(parts) + "}"


def serialize_game_island_export_bytes(root: dict[str, Any]) -> bytes:
    """Deterministic JSON bytes for island export (field order + default key omission)."""

    v = _as_int(root.get("V"))
    bp = root.get("BP")
    if not isinstance(bp, dict):
        msg = "missing BP"
        raise ValueError(msg)
    if str(bp.get("$type")) != "Island":
        msg = "only Island $type supported for official serialize"
        raise ValueError(msg)

    icon = bp.get("Icon")
    if not isinstance(icon, dict):
        msg = "missing BP.Icon dict"
        raise ValueError(msg)
    if icon != OFFICIAL_ISLAND_ICON:
        msg = "BP.Icon must match OFFICIAL_ISLAND_ICON for serialize_game_island_export_bytes"
        raise ValueError(msg)
    icon_json = '{"Data":["icon:Platforms",null,null,"shape:RuRuRuRu"]}'

    entries_raw = bp.get("Entries")
    if not isinstance(entries_raw, list):
        msg = "missing BP.Entries"
        raise ValueError(msg)

    entry_strs: list[str] = []
    for row in entries_raw:
        if not isinstance(row, dict):
            continue
        tx = _as_int(row.get("X"))
        ty = _as_int(row.get("Y"))
        tr = _as_int(row.get("R"))
        t_raw = row.get("T")
        if not isinstance(t_raw, str):
            msg = "entry T must be str"
            raise ValueError(msg)
        entry_strs.append(_serialize_entry_row(tx, ty, tr, t_raw))

    entries_body = "[" + ",".join(entry_strs) + "]"
    bv = _as_int(bp.get("BinaryVersion", v))

    text = (
        '{"V":'
        + str(v)
        + ',"BP":{"$type":"Island","Icon":'
        + icon_json
        + ',"Entries":'
        + entries_body
        + ',"BinaryVersion":'
        + str(bv)
        + "}}"
    )
    return text.encode("utf-8")


def export_dense_x_set(entries: list[dict[str, Any]]) -> set[int]:
    """Dense column indices for export ``X`` values (omitted ``X`` → 0)."""

    return {raw_x_to_dense_index(_as_int(row.get("X"))) for row in entries if isinstance(row, dict)}


def export_dense_x_is_contiguous(entries: list[dict[str, Any]]) -> bool:
    """True when dense(export X) values form a contiguous interval with no gaps."""

    dense = export_dense_x_set(entries)
    if not dense:
        return True
    lo, hi = min(dense), max(dense)
    return hi - lo + 1 == len(dense)


def encode_official_copy_string(
    root: dict[str, Any],
    *,
    target_game_version: int = 4,
) -> str:
    """gzip + base64 + versioned prefix.

    *target_game_version* defaults to 4 (the only currently supported version).
    Pass an unknown version to get an immediate ``ValueError`` rather than a
    silently mis-versioned blueprint.
    """
    prefix = resolve_blueprint_code_version(target_game_version)
    body = serialize_game_island_export_bytes(root)
    gz = gzip.compress(body, compresslevel=9, mtime=0)
    b64 = base64.b64encode(gz).decode("ascii")
    return f"{prefix}{b64}"


def make_minimal_official_root() -> dict[str, Any]:
    """Return a valid empty island root dict (useful for tests and stub exports)."""
    return {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Icon": dict(OFFICIAL_ISLAND_ICON),
            "Entries": [],
            "BinaryVersion": OFFICIAL_BINARY_VERSION,
        },
    }
