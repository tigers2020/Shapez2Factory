"""Shared fixtures for ``tests/unit/asteroid_lab`` (reconstruction / genetic_sample)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.genetic_sample.exhaustive_generator import (
    ExhaustiveGenerationStats,
    GeneratedSampleGene,
    generate_exhaustive_sample_genes,
)
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    load_reconstruction_fixture_line_pairs,
)
from django_apps.shapez_core.models import (
    ShapezBasedataRelease,
    ShapezGameIdentifier,
    ShapezIdentifierCategory,
)

CONNECTED_BRANCH_GENE_KEY = (
    '{"e":[[[-1,1],[-1,2],"S"],[[0,0],[0,1],"S"],[[0,1],[-1,1],"W"]],"ec":3,"tk":"pipe"}'
)


@pytest.fixture
def lab_sprite_identifiers_for_admin() -> ShapezBasedataRelease:
    r = ShapezBasedataRelease.objects.create(
        game_version=900_043,
        notes="genetic-lab-sprite-test",
        integrity_status_id=ShapezBasedataRelease.IntegrityStatus.IMPORTED.value,
    )
    cat = ShapezIdentifierCategory.objects.create(release=r, key="BuildingVariantIds", sort_order=0)
    for value, rel in (
        ("SpacePipe_LeftTurn", "SpacePipe/SpacePipe_LeftTurn.svg"),
        ("SpacePipe_RightTurn", "SpacePipe/SpacePipe_RightTurn.svg"),
        ("SpacePipe_LeftFwdSplitter", "SpacePipe/SpacePipe_LeftFwdSplitter.svg"),
        ("SpacePipe_Forward", "SpacePipe/SpacePipe_Forward.svg"),
    ):
        ShapezGameIdentifier.objects.create(
            release=r,
            identifier_category=cat,
            value=value,
            normalized_value=value,
            sprite_static_relpath=rel,
        )
    return r


@pytest.fixture(params=range(len(load_reconstruction_fixture_line_pairs())))
def reconstruction_fixture_line_index(request: pytest.FixtureRequest) -> int:
    return int(request.param)


@pytest.fixture(scope="module")
def exhaustive_genes_ext3() -> tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats]:
    return generate_exhaustive_sample_genes(max_extensions=3)


@pytest.fixture(scope="module")
def exhaustive_genes_ext0() -> tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats]:
    return generate_exhaustive_sample_genes(max_extensions=0)


@pytest.fixture(scope="module")
def exhaustive_genes_ext0_belt() -> tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats]:
    return generate_exhaustive_sample_genes(max_extensions=0, transport_kinds=("belt",))


@pytest.fixture(scope="module")
def exhaustive_genes_ext0_belt_v1() -> tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats]:
    return generate_exhaustive_sample_genes(
        max_extensions=0,
        transport_kinds=("belt",),
        generator_version="exhaustive_sample_gene_v1",
    )


@pytest.fixture(scope="module")
def exhaustive_genes_ext1_belt() -> tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats]:
    return generate_exhaustive_sample_genes(max_extensions=1, transport_kinds=("belt",))


@pytest.fixture
def connected_branch_gene_ext3(
    exhaustive_genes_ext3: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
) -> GeneratedSampleGene:
    genes, _stats = exhaustive_genes_ext3
    return next(g for g in genes if g.key == CONNECTED_BRANCH_GENE_KEY)


@pytest.fixture
def staff_client(db: None):
    from django.contrib.auth import get_user_model
    from django.test import Client

    User = get_user_model()
    user = User.objects.create_user(
        username="recon_map_admin_staff",
        password="pass-word-123",
        is_staff=True,
        is_superuser=True,
    )
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def reconstructed_row(db: None):
    from django_apps.asteroid_lab import models as m

    proj = m.AsteroidProject.objects.create(name="ThumbProj", slug="thumb-proj-admin")
    inp = m.AsteroidMapInput.objects.create(
        project=proj,
        copy_code="",
        source_kind=m.AsteroidMapInput.SourceKind.COPY_CODE,
    )
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [{"X": 1, "Y": 1, "T": "SpaceBelt_Forward", "R": 0}],
        },
    }
    return m.ReconstructedAsteroidMap.objects.create(
        map_input=inp,
        project=proj,
        run_key="rk-thumb",
        decoded_json=decoded,
    )
