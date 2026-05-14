from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.decode import (
    analyze_decoded_layout,
    decode_copy_payload,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    DecodedExistingLayoutContext,
    ReconstructionResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction.asteroid_reconstruction import (  # noqa: E501
    reconstruct_asteroid_mining_field,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction.patch_interior import (  # noqa: E501
    compute_patch_interior_cells,
)


def _bp(entries: list[dict[str, object]]) -> dict[str, object]:
    return {"V": 1, "BP": {"Entries": entries}}


def test_reconstruction_empty_blueprint() -> None:
    r = reconstruct_asteroid_mining_field(_bp([]))
    assert r.mineable_placement_cells == ()
    assert r.extraction_shell_cells == ()
    assert r.full_barrier_cells == ()
    assert r.belt_cells == ()
    assert r.pipe_cells == ()
    assert r.interior_patch_cells == ()
    assert r.asteroid_bbox is None
    assert r.external_margin == 0
    assert r.external_margin_bbox_source == "none"


def test_reconstruction_miner_shell_and_mineable() -> None:
    payload = _bp(
        [
            {"X": 1, "Y": 0, "T": "Layout_ShapeMiner"},
            {"X": 2, "Y": 0, "T": "Layout_ShapeMinerExtension"},
        ]
    )
    r = reconstruct_asteroid_mining_field(payload)
    assert len(r.extraction_shell_cells) == 2
    assert (1, 0) in r.extraction_shell_cells
    assert (2, 0) in r.extraction_shell_cells
    assert len(r.mineable_placement_cells) >= 2
    assert len(r.full_barrier_cells) == 2
    assert r.belt_cells == ()
    assert r.pipe_cells == ()


def test_reconstruction_separate_belt_and_pipe_cells() -> None:
    r = reconstruct_asteroid_mining_field(
        _bp(
            [
                {"X": 1, "Y": 0, "T": "Layout_ShapeMiner"},
                {"X": 2, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                {"X": 3, "Y": 0, "T": "SpacePipe_MK2"},
            ]
        )
    )
    assert r.belt_cells == ((2, 0),)
    assert r.pipe_cells == ((3, 0),)
    assert set(r.belt_cells).isdisjoint(r.pipe_cells)
    assert (2, 0) not in r.mineable_placement_cells
    assert (3, 0) not in r.mineable_placement_cells


def test_orphan_transport_not_extraction_shell() -> None:
    r = reconstruct_asteroid_mining_field(
        _bp(
            [
                {"X": 50, "Y": 50, "T": "SpacePipe_MK2"},
                {"X": 51, "Y": 50, "T": "Layout_UndergroundBelt", "R": 0},
            ]
        )
    )
    assert r.extraction_shell_cells == ()
    assert r.pipe_cells == ((50, 50),)
    assert r.belt_cells == ((51, 50),)
    assert r.mineable_placement_cells == ()
    assert r.interior_patch_cells == ()


def test_existing_layout_context_does_not_replace_mineable() -> None:
    bp = _bp(
        [
            {"X": 1, "Y": 0, "T": "Layout_ShapeMiner"},
            {"X": 2, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
        ]
    )
    base = reconstruct_asteroid_mining_field(bp)
    analysis = analyze_decoded_layout(bp)
    ctx = DecodedExistingLayoutContext(analysis=analysis)
    merged = reconstruct_asteroid_mining_field(bp, ctx)
    assert base.mineable_placement_cells == merged.mineable_placement_cells
    assert base.interior_patch_cells == merged.interior_patch_cells


def test_interior_patch_inference_not_in_decode_or_analysis_dto() -> None:
    bp = _bp([{"X": 1, "Y": 0, "T": "Layout_ShapeMiner"}])
    doc = decode_copy_payload(bp)
    assert "interior_patch_cells" not in doc.as_mutable_dict()
    analysis = analyze_decoded_layout(bp)
    assert not hasattr(analysis, "interior_patch_cells")


def test_flood_fill_closing_adds_interior_vs_no_closing() -> None:
    """Chebyshev closing (steps=1) seals a 1-cell outer gap; interior appears only then."""

    shell = {
        (1, 0),
        (3, 0),
        (4, 0),
        (1, 1),
        (4, 1),
        (1, 2),
        (4, 2),
        (1, 3),
        (2, 3),
        (3, 3),
        (4, 3),
    }
    no_close = compute_patch_interior_cells(set(shell), perimeter_bridge_steps=0)
    with_close = compute_patch_interior_cells(set(shell), perimeter_bridge_steps=1)
    assert no_close == []
    assert with_close != []


def test_reconstruction_deterministic() -> None:
    bp = _bp(
        [
            {"X": 1, "Y": 0, "T": "Layout_ShapeMiner"},
            {"X": 2, "Y": 1, "T": "Layout_ShapeMinerExtension"},
            {"X": 5, "Y": 0, "T": "SpacePipe_MK2"},
        ]
    )
    a = reconstruct_asteroid_mining_field(bp)
    b = reconstruct_asteroid_mining_field(bp)
    assert a == b
    assert isinstance(a, ReconstructionResult)


def test_external_margin_metadata_from_mineable_bbox() -> None:
    r = reconstruct_asteroid_mining_field(
        _bp(
            [
                {"X": 1, "Y": 0, "T": "Layout_ShapeMiner"},
                {"X": 2, "Y": 0, "T": "Layout_ShapeMinerExtension"},
            ]
        )
    )
    assert r.asteroid_bbox is not None
    assert r.external_margin_bbox_source == "mineable"
    assert r.external_margin == 3  # max(w,h)=2 → ceil(0.3)=1 clamped to min 3
