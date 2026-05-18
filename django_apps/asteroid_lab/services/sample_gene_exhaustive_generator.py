"""Exhaustive sample-gene layouts: one extractor, one R-side transport, N/W/S extension tree (≤3).

Abstract grid (see ``documents/ai/plans/exhaustive_sample_gene_seed.md``):
extractor at (0,0), output transport at (1,0).
``abstract_grid_to_raw_xy`` maps to blueprint ``X,Y`` obeying Shapez raw **no column X==0**
(see ``django_apps/asteroid_lab/reconstruction/grid.py``).
``build_layout_root`` asserts every entry.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Literal

from django_apps.asteroid_lab.adapters.blueprint_canonical_export import (
    encode_official_copy_string,
    to_official_island_root,
)
from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.snapshots.equipment_bundles import (
    direction_from_a_to_b,
    ports_compatible,
)

GridCoord = tuple[int, int]
TransportKind = Literal["belt", "pipe"]
AttachDir = Literal["N", "W", "S"]

DELTA_NWS: dict[AttachDir, GridCoord] = {"N": (0, -1), "W": (-1, 0), "S": (0, 1)}
EXTRACTOR_GRID: GridCoord = (0, 0)
OUTPUT_TRANSPORT_GRID: GridCoord = (1, 0)


def abstract_grid_to_raw_xy(gx: int, gy: int) -> tuple[int, int]:
    """Map abstract sample-gene integer grid to blueprint raw ``X,Y``.

    Shapez ``BP.Entries`` raw ``X`` 에는 **열 0이 없다** (…, -2, -1, 1, 2, …). 추상 열 ``gx`` 를
    그 스킵에 맞춰 옮긴다.

    - ``gx >= 0`` (비음수 추상 열) → ``X = gx + 1`` … ``gx=0`` 이 게임 ``X=1`` 열.
    - ``gx < 0`` → ``X = gx`` … 음수 열은 그대로 (여전히 ``X != 0``).
    - ``Y = gy`` (앵커 ``(0,0) -> (1,0)``).

    임의의 ``(gx, gy)`` 를 넣기 전에, 배치 규칙이 위 식으로 **절대 ``X==0`` 이 되지 않는지**
    확인할 것.
    """

    rx = gx + 1 if gx >= 0 else gx
    return (rx, gy)


def assert_blueprint_entries_raw_x_nonzero(entries: list[dict[str, Any]]) -> None:
    """Fail fast if any top-level entry would use forbidden raw ``X == 0``."""

    for row in entries:
        x = row.get("X")
        if isinstance(x, int) and x == 0:
            msg = "blueprint entry has raw X==0 (invalid column in Shapez copy JSON)"
            raise ValueError(msg)


@dataclass(frozen=True)
class SampleGeneNode:
    node_id: str
    kind: Literal["extractor", "extension"]
    coord: GridCoord
    parent_id: str | None
    attach_dir: AttachDir | None


@dataclass(frozen=True)
class GeneratedSampleGene:
    key: str
    name: str
    transport_kind: TransportKind
    extension_count: int
    nodes: tuple[SampleGeneNode, ...]
    transport_cells: tuple[GridCoord, ...]
    layout_json: dict[str, Any]
    encoded_copy_string: str
    metadata: dict[str, Any]


@dataclass
class ExhaustiveGenerationStats:
    complete_trees_attempted: int = 0
    duplicate_keys_skipped: int = 0
    invalid_rejected: int = 0
    unique_topologies: int = 0
    by_extension_count: dict[int, int] = field(default_factory=dict)
    by_transport_kind: dict[str, int] = field(default_factory=dict)


def canonical_gene_key(
    transport_kind: TransportKind,
    extension_count: int,
    edges: list[tuple[GridCoord, GridCoord, AttachDir]],
) -> str:
    """Deterministic topology key: transport_kind + extension_count + sorted edges."""

    ser = sorted(
        [([pa[0], pa[1]], [pb[0], pb[1]], d) for pa, pb, d in edges],
        key=lambda t: (t[0], t[1], t[2]),
    )
    payload = {"ec": extension_count, "e": ser, "tk": transport_kind}
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _enumerate_extension_placements(k: int) -> Any:
    """Yield lists of extension dicts (id, coord, parent_id, parent_coord, attach_dir)."""

    if k < 0:
        return
    if k == 0:
        yield []
        return

    occupied_base: set[GridCoord] = {EXTRACTOR_GRID, OUTPUT_TRANSPORT_GRID}

    def rec(exts: list[dict[str, Any]]) -> Any:
        if len(exts) == k:
            yield list(exts)
            return
        occ = occupied_base | {tuple(e["coord"]) for e in exts}
        parents: list[tuple[str, GridCoord]] = [("E0", EXTRACTOR_GRID)] + [
            (str(e["id"]), tuple(e["coord"])) for e in exts
        ]
        for pid, pcoord in parents:
            for ad in ("N", "W", "S"):
                dx, dy = DELTA_NWS[ad]
                nc = (pcoord[0] + dx, pcoord[1] + dy)
                if abstract_grid_to_raw_xy(*nc)[0] == 0:
                    msg = "extension abstract coord maps to forbidden raw X==0"
                    raise ValueError(msg)
                if nc in occ:
                    continue
                if nc == OUTPUT_TRANSPORT_GRID:
                    continue
                new_id = f"E{len(exts) + 1}"
                new_ext = {
                    "id": new_id,
                    "coord": nc,
                    "parent_id": pid,
                    "parent_coord": pcoord,
                    "attach_dir": ad,
                }
                yield from rec(exts + [new_ext])

    yield from rec([])


def _edges_from_exts(exts: list[dict[str, Any]]) -> list[tuple[GridCoord, GridCoord, AttachDir]]:
    out: list[tuple[GridCoord, GridCoord, AttachDir]] = []
    for e in exts:
        pa = tuple(e["parent_coord"])
        pb = tuple(e["coord"])
        out.append((pa, pb, e["attach_dir"]))
    return out


def _deterministic_display_name(
    transport_kind: TransportKind,
    extension_count: int,
    edges: list[tuple[GridCoord, GridCoord, AttachDir]],
    gene_key: str,
    used: set[str],
) -> str:
    sfx = "Belt" if transport_kind == "belt" else "Pipe"
    if extension_count == 0:
        base = f"E_Solo_Out_R_{sfx}"
    else:
        root_dirs = sorted(d for p, _c, d in edges if p == EXTRACTOR_GRID)
        root = EXTRACTOR_GRID
        root_children = [c for p, c, _d in edges if p == root]
        max_depth = _max_tree_depth(root, edges)

        if extension_count == len(root_children) and all(p == root for p, _c, _d in edges):
            tag = "".join(root_dirs) if root_dirs else "X"
            base = f"E_{tag}{extension_count}_Out_R_{sfx}"
        elif max_depth >= extension_count and extension_count > 1:
            # chain-like (single path to deepest leaf)
            first = root_dirs[0] if root_dirs else "X"
            base = f"E_{first}Chain{extension_count}_Out_R_{sfx}"
        else:
            tag = "".join(root_dirs) if root_dirs else "Tree"
            base = f"E_Branch_{tag}_{extension_count}_Out_R_{sfx}"

    if base not in used:
        used.add(base)
        return base
    h = hashlib.sha256(gene_key.encode("utf-8")).hexdigest()[:6]
    candidate = f"{base}_{h}"
    used.add(candidate)
    return candidate


def _max_tree_depth(root: GridCoord, edges: list[tuple[GridCoord, GridCoord, AttachDir]]) -> int:
    children: dict[GridCoord, list[GridCoord]] = {}
    for pa, pb, _d in edges:
        children.setdefault(pa, []).append(pb)
    depth: dict[GridCoord, int] = {root: 0}
    stack = [root]
    while stack:
        u = stack.pop()
        for v in children.get(u, []):
            if v not in depth:
                depth[v] = depth[u] + 1
                stack.append(v)
    return max(depth.values(), default=0)


def _extractor_cell_kind(transport_kind: TransportKind) -> str:
    return "shape_miner" if transport_kind == "belt" else "fluid_miner"


def _extension_cell_kind(transport_kind: TransportKind) -> str:
    return "shape_miner_extension" if transport_kind == "belt" else "fluid_miner_extension"


def compute_extension_rotations_by_parent(
    exts: list[dict[str, Any]],
    *,
    transport_kind: TransportKind,
) -> dict[str, int]:
    """Quarter ``R`` per extension id: ports face the parent (lab decode contract).

    ``exts`` must list each extension after its parent (DFS enumeration order).
    """

    child_ck = _extension_cell_kind(transport_kind)
    ext_rot: dict[str, int] = {}
    for e in exts:
        eid = str(e["id"])
        parent_id = str(e["parent_id"])
        parent_coord = tuple(e["parent_coord"])
        child_coord = tuple(e["coord"])
        cx, cy = abstract_grid_to_raw_xy(*child_coord)
        px, py = abstract_grid_to_raw_xy(*parent_coord)
        dir_child_to_parent = direction_from_a_to_b(cx, cy, px, py)
        if dir_child_to_parent is None:
            msg = "extension and parent are not raw-grid 4-neighbors"
            raise ValueError(msg)
        if parent_id == "E0":
            parent_ck = _extractor_cell_kind(transport_kind)
            parent_r = 0
        else:
            parent_ck = child_ck
            parent_r = ext_rot[parent_id]
        for q in range(4):
            if ports_compatible(child_ck, q, parent_ck, parent_r, dir_child_to_parent):
                ext_rot[eid] = q
                break
        else:
            msg = "no extension R links extension to parent"
            raise ValueError(msg)
    return ext_rot


def _build_nodes(exts: list[dict[str, Any]]) -> tuple[SampleGeneNode, ...]:
    nodes: list[SampleGeneNode] = [
        SampleGeneNode("E0", "extractor", EXTRACTOR_GRID, None, None),
    ]
    for e in sorted(exts, key=lambda x: x["id"]):
        nodes.append(
            SampleGeneNode(
                str(e["id"]),
                "extension",
                tuple(e["coord"]),
                str(e["parent_id"]),
                e["attach_dir"],
            )
        )
    return tuple(nodes)


def build_layout_root(
    *, transport_kind: TransportKind, exts: list[dict[str, Any]]
) -> dict[str, Any]:
    if transport_kind == "belt":
        miner_t = "Layout_ShapeMiner"
        ext_t = "Layout_ShapeMinerExtension"
        transport_t = "SpaceBelt_Left"
    else:
        miner_t = "Layout_FluidMiner"
        ext_t = "Layout_FluidMinerExtension"
        transport_t = "SpacePipe_Forward"

    entries: list[dict[str, Any]] = []
    rx, ry = abstract_grid_to_raw_xy(*EXTRACTOR_GRID)
    entries.append({"X": rx, "Y": ry, "R": 0, "T": miner_t})
    ext_rots = compute_extension_rotations_by_parent(exts, transport_kind=transport_kind)
    for e in exts:
        x, y = abstract_grid_to_raw_xy(*tuple(e["coord"]))
        rq = ext_rots[str(e["id"])]
        entries.append({"X": x, "Y": y, "R": rq, "T": ext_t})
    tx, ty = abstract_grid_to_raw_xy(*OUTPUT_TRANSPORT_GRID)
    entries.append({"X": tx, "Y": ty, "R": 0, "T": transport_t})
    entries.sort(key=lambda r: (r["X"], r["Y"], r["T"]))
    assert_blueprint_entries_raw_x_nonzero(entries)
    return {"V": 1, "BP": {"$type": "Island", "Entries": entries}}


def encode_layout_with_suffix(layout: dict[str, Any]) -> str:
    return encode_official_copy_string(to_official_island_root(layout)) + "$"


def validate_roundtrip(encoded: str) -> None:
    decode_copy_string(encoded.strip())


def build_metadata(
    *,
    generator_version: str,
    transport_kind: TransportKind,
    extension_count: int,
    gene_key: str,
) -> dict[str, Any]:
    return {
        "generator": generator_version,
        "output_dir": "R",
        "transport_kind": transport_kind,
        "extension_count": extension_count,
        "extension_topology_key": gene_key,
        "rules": {
            "r_output_transport_required": True,
            "extension_attach_dirs": ["N", "W", "S"],
            "max_extensions": 3,
            "extension_chain_allowed": True,
            "extension_r_quarter_turns_face_parent": True,
        },
    }


def generate_exhaustive_sample_genes(
    *,
    max_extensions: int = 3,
    transport_kinds: tuple[TransportKind, ...] = ("belt", "pipe"),
    generator_version: str = "exhaustive_sample_gene_v1",
) -> tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats]:
    stats = ExhaustiveGenerationStats()
    seen: set[str] = set()
    used_names: set[str] = set()
    out: list[GeneratedSampleGene] = []

    for tk in transport_kinds:
        stats.by_transport_kind.setdefault(tk, 0)
        for ec in range(0, max_extensions + 1):
            stats.by_extension_count.setdefault(ec, 0)
            for exts in _enumerate_extension_placements(ec):
                stats.complete_trees_attempted += 1
                edges = _edges_from_exts(exts)
                gkey = canonical_gene_key(tk, ec, edges)
                if gkey in seen:
                    stats.duplicate_keys_skipped += 1
                    continue
                seen.add(gkey)
                stats.unique_topologies += 1
                stats.by_extension_count[ec] += 1
                stats.by_transport_kind[tk] += 1

                layout = build_layout_root(transport_kind=tk, exts=exts)
                try:
                    code = encode_layout_with_suffix(layout)
                    validate_roundtrip(code)
                except Exception:
                    stats.invalid_rejected += 1
                    seen.remove(gkey)
                    stats.unique_topologies -= 1
                    stats.by_extension_count[ec] -= 1
                    stats.by_transport_kind[tk] -= 1
                    continue

                name = _deterministic_display_name(tk, ec, edges, gkey, used_names)
                meta = build_metadata(
                    generator_version=generator_version,
                    transport_kind=tk,
                    extension_count=ec,
                    gene_key=gkey,
                )
                out.append(
                    GeneratedSampleGene(
                        key=gkey,
                        name=name,
                        transport_kind=tk,
                        extension_count=ec,
                        nodes=_build_nodes(exts),
                        transport_cells=(OUTPUT_TRANSPORT_GRID,),
                        layout_json=layout,
                        encoded_copy_string=code,
                        metadata=meta,
                    )
                )
    return out, stats
