from __future__ import annotations

import base64
import gzip
import json

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.decode import (
    ShapezCopyDecodeError,
    analyze_decoded_layout,
    decode_copy_payload,
    trivial_unknown_analysis,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ExistingLayoutAnalysis,
    FinalValidationReport,
    ReconstructionDTO,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    ExistingLayoutIssueCode,
    SourceKind,
    TransportComponentStatus,
    TransportKind,
)
from django_apps.shapez_core.services.shapez_copy_decode import SHAPEZ2_COPY_PREFIX_V4


def _bp(entries: list[dict[str, object]]) -> dict[str, object]:
    return {"V": 1, "BP": {"Entries": entries}}


def _encode_copy(obj: object) -> str:
    body = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    compressed = gzip.compress(body)
    b64 = base64.b64encode(compressed).decode("ascii")
    return f"{SHAPEZ2_COPY_PREFIX_V4}{b64}"


def test_trivial_unknown_analysis_contract() -> None:
    ctx = trivial_unknown_analysis()
    assert ctx.source_kind is SourceKind.UNKNOWN
    assert ctx.issues == ()


def test_decode_copy_string_round_trip() -> None:
    payload = _bp([])
    doc = decode_copy_payload(_encode_copy(payload))
    assert dict(doc.document) == payload


def test_decode_accepts_mapping_fixture() -> None:
    payload = _bp([{"X": 1, "Y": 0, "T": "Layout_ShapeMiner"}])
    doc = decode_copy_payload(payload)
    assert doc.as_mutable_dict()["BP"]["Entries"][0]["T"] == "Layout_ShapeMiner"


def test_decode_rejects_bad_prefix() -> None:
    with pytest.raises(ShapezCopyDecodeError):
        decode_copy_payload("NOT-A-COPY")


def test_raw_asteroid_empty_bp_not_existing_shape() -> None:
    a = analyze_decoded_layout(_bp([]))
    assert a.source_kind is SourceKind.RAW_ASTEROID_FIELD


def test_existing_fluid_layout_miner_and_pipe() -> None:
    entries = [
        {"X": 1, "Y": 0, "T": "Layout_FluidMiner"},
        {"X": 2, "Y": 0, "T": "SpacePipe_MK2"},
        {"X": 3, "Y": 0, "T": "SpacePipe_MK2"},
    ]
    a = analyze_decoded_layout(_bp(entries))
    assert a.source_kind is SourceKind.EXISTING_FLUID_LAYOUT
    assert a.pipe_transport.component_count == 1
    assert a.belt_transport.component_count == 0


def test_existing_shape_layout_miner_and_belt() -> None:
    entries = [
        {"X": 1, "Y": 0, "T": "Layout_ShapeMiner"},
        {"X": 2, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
        {"X": 3, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
    ]
    a = analyze_decoded_layout(_bp(entries))
    assert a.source_kind is SourceKind.EXISTING_SHAPE_LAYOUT
    assert a.belt_transport.component_count == 1
    assert a.pipe_transport.component_count == 0


def test_mixed_existing_layout_belt_and_pipe() -> None:
    entries = [
        {"X": 1, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
        {"X": 10, "Y": 0, "T": "SpacePipe_MK2"},
    ]
    a = analyze_decoded_layout(_bp(entries))
    assert a.source_kind is SourceKind.MIXED_EXISTING_LAYOUT


def test_source_kind_ambiguous_fluid_miner_with_belt_only() -> None:
    entries = [
        {"X": 1, "Y": 0, "T": "Layout_FluidMiner"},
        {"X": 2, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
    ]
    a = analyze_decoded_layout(_bp(entries))
    assert a.source_kind is SourceKind.UNKNOWN
    codes = {i.code for i in a.issues}
    assert ExistingLayoutIssueCode.SOURCE_KIND_AMBIGUOUS in codes


def test_main_trunk_seed_union_excludes_orphan_and_single_cell() -> None:
    entries = [
        {"X": 1, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
        {"X": 2, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
        {"X": 3, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
        {"X": 10, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
        {"X": 11, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
        {"X": 20, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
    ]
    a = analyze_decoded_layout(_bp(entries))
    main_cells = {Coord(1, 0), Coord(2, 0), Coord(3, 0)}
    orphan_cells = {Coord(10, 0), Coord(11, 0)}
    artifact = {Coord(20, 0)}
    assert a.solver_hints.trunk_seed_cell_union == frozenset(main_cells)
    assert a.solver_hints.cleanup_candidate_cell_union == frozenset(orphan_cells | artifact)
    mains = [
        c
        for c in a.belt_transport.components
        if c.status is TransportComponentStatus.MAIN_TRUNK_CANDIDATE
    ]
    assert len(mains) == 1
    assert mains[0].cells == frozenset(main_cells)


def test_analysis_is_not_reconstruction_mineable_cells() -> None:
    a = analyze_decoded_layout(_bp([]))
    assert not isinstance(a, ReconstructionDTO)
    assert not hasattr(a, "mineable_placement_cells")


def test_existing_layout_fields_disjoint_from_final_validation() -> None:
    ev = {f.name for f in ExistingLayoutAnalysis.__dataclass_fields__.values()}
    fv = {f.name for f in FinalValidationReport.__dataclass_fields__.values()}
    assert ev.isdisjoint(fv)


def test_belt_and_pipe_cells_disjoint() -> None:
    entries = [
        {"X": 1, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
        {"X": 2, "Y": 0, "T": "SpacePipe_MK2"},
    ]
    a = analyze_decoded_layout(_bp(entries))
    assert a.belt_transport.transport_kind is TransportKind.SHAPE_BELT
    assert a.pipe_transport.transport_kind is TransportKind.FLUID_PIPE
    belt_cells = frozenset().union(*(c.cells for c in a.belt_transport.components))
    pipe_cells = frozenset().union(*(c.cells for c in a.pipe_transport.components))
    assert belt_cells.isdisjoint(pipe_cells)


def test_coord_tuple_roundtrip_sorted() -> None:
    entries = [{"X": 3, "Y": 1, "T": "Layout_UndergroundBelt", "R": 0}]
    a = analyze_decoded_layout(_bp(entries))
    t = tuple(
        (c.x, c.y)
        for c in sorted(a.solver_hints.cleanup_candidate_cell_union, key=lambda z: (z.x, z.y))
    )
    assert t == ((3, 1),)


def test_solver_hints_do_not_imply_hard_protected_corridors() -> None:
    a = analyze_decoded_layout(
        _bp(
            [
                {"X": 1, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                {"X": 2, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
            ]
        )
    )
    assert not hasattr(a.solver_hints, "hard_protected_corridors")
