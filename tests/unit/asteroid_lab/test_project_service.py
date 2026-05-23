"""``project_service`` ??copy-seeded project creation."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.decode_adapter import encode_copy_string
from django_apps.asteroid_lab.services import project_service


@pytest.mark.django_db
def test_create_project_from_copy_code_dto_shape() -> None:
    raw = encode_copy_string(
        {
            "V": 21,
            "BP": {
                "$type": "Island",
                "Entries": [{"X": 1, "Y": 0, "T": "Layout_FluidMiner"}],
            },
        }
    )
    dto = project_service.create_project_from_copy_code(raw, source_label="Island A")
    assert dto.project_id > 0
    assert dto.slug
    assert dto.map_input_id > 0
    assert len(dto.copy_code_sha256) == 64

    proj = m.AsteroidProject.objects.get(pk=dto.project_id)
    assert proj.slug == dto.slug
    inp = m.AsteroidMapInput.objects.get(pk=dto.map_input_id)
    assert inp.copy_code == raw
    assert inp.decoded_json.get("BP", {}).get("Entries")
    assert inp.source_kind == m.AsteroidMapInput.SourceKind.DECODED_JSON


def _minimal_island_copy() -> str:
    return encode_copy_string(
        {
            "V": 21,
            "BP": {
                "$type": "Island",
                "Entries": [{"X": 0, "Y": 0, "T": "Layout_FluidMiner"}],
            },
        }
    )


@pytest.mark.django_db
def test_resolve_or_create_project_slug_dedupes() -> None:
    code = _minimal_island_copy()
    slug_a = project_service.resolve_or_create_project_slug_for_copy_code(code)
    slug_b = project_service.resolve_or_create_project_slug_for_copy_code(code)
    assert slug_a == slug_b
    assert m.AsteroidProject.objects.count() == 1


@pytest.mark.django_db
def test_resolve_or_create_strips_whitespace_for_digest() -> None:
    code = _minimal_island_copy()
    slug_a = project_service.resolve_or_create_project_slug_for_copy_code(f"  {code}  ")
    slug_b = project_service.resolve_or_create_project_slug_for_copy_code(code)
    assert slug_a == slug_b
    assert m.AsteroidProject.objects.count() == 1
    inp = m.AsteroidMapInput.objects.order_by("-created_at").first()
    assert inp is not None
    assert inp.copy_code.strip() == code.strip()


@pytest.mark.django_db
def test_resolve_or_create_empty_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        project_service.resolve_or_create_project_slug_for_copy_code("   ")
