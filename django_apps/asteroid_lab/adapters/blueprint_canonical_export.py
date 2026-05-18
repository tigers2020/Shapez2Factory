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

OFFICIAL_ISLAND_ICON: dict[str, Any] = {
    "Data": ["icon:Platforms", None, None, "shape:RuRuRuRu"],
}

# User-provided connected west+branch fluid pipe (game copy; no trailing ``=`` on payload).
_CONNECTED_BRANCH_B64_PAYLOAD = (
    "H4sIAMsrC2oA/4yQzQrCMBCE32XwGA+lByFHUaGgUFSKRUQWGzEQ05IftJS8uzEF8SSysLDszLfLDKjAsyyfMcxL8AET13cCHIVVpBswFJdWvxcLcgR+hIwzLxW5a2vuFkx7pcYGe6NO8K0fC6fAsNTOSGGjccABfJox7CN9TX3r3XmlvGw2UguzfDqhrYynAvso6/gawxY8/8tV/+Anwd+kQzr8xdt1dBGl7MR51ZoHmQbhFBOTmkxfCZOMKcYQXgIMAFZBsdNSAQAA"
)

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


def _extractor_anchor(entries: list[dict[str, Any]]) -> tuple[int, int]:
    candidates: list[tuple[int, int]] = []
    for row in entries:
        t = str(row.get("T", ""))
        if _is_extractor_tile(t):
            candidates.append((_as_int(row.get("X")), _as_int(row.get("Y"))))
    if not candidates:
        msg = "no Layout_*Miner extractor in BP.Entries for official export anchor"
        raise ValueError(msg)
    return min(candidates)


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


def encode_official_copy_string(root: dict[str, Any]) -> str:
    """gzip + base64 + prefix (no per-layout gzip byte pinning)."""

    body = serialize_game_island_export_bytes(root)
    gz = gzip.compress(body, compresslevel=9, mtime=0)
    b64 = base64.b64encode(gz).decode("ascii")
    return f"{SHAPEZ2_COPY_PREFIX_V4}{b64}"
