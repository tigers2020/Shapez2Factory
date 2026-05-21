"""LazyLocalizedText parsing and research import storage."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.game_data.services.lazy_localized_text import parse_lazy_localized_text

SAMPLE_SIDE_GOAL = {
    "Id": {"<Id>k__BackingField": "side-goal.hard-postFinalT3-1"},
    "PlaceholderResolver": {
        "Replacements": {},
        "$type": "Core.Localization.LazyLocalizedTextPlaceholderResolver",
    },
    "$type": "Core.Localization.LazyLocalizedText",
}


def test_parse_lazy_localized_text_extracts_all_observed_fields() -> None:
    parsed = parse_lazy_localized_text(SAMPLE_SIDE_GOAL)
    assert parsed is not None
    assert parsed.message_key == "side-goal.hard-postFinalT3-1"
    assert parsed.lazy_text_type == "Core.Localization.LazyLocalizedText"
    assert (
        parsed.placeholder_resolver_type
        == "Core.Localization.LazyLocalizedTextPlaceholderResolver"
    )
    assert parsed.is_cycle_reference is False
    assert parsed.cycle_reference == ""
    assert parsed.replacements == ()


def test_parse_plain_string_title() -> None:
    parsed = parse_lazy_localized_text("plain-title")
    assert parsed is not None
    assert parsed.message_key == "plain-title"
    assert parsed.lazy_text_type == ""


def test_parse_none_returns_none() -> None:
    assert parse_lazy_localized_text(None) is None


@pytest.fixture
def game_data_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "documents" / "game_data"
    if not (root / "manifest.json").is_file():
        pytest.skip("documents/game_data not present")
    return root


@pytest.mark.django_db
def test_research_side_quest_stores_lazy_ref_not_raw_dict_string(game_data_dir: Path) -> None:
    from django_apps.game_data.importers import GameDataImporter
    from django_apps.game_data.models import ResearchSideQuest

    GameDataImporter(game_data_dir, batch_name="l10n").run()
    quest = ResearchSideQuest.objects.filter(node_key="SG_PostFinalT3_1_1").first()
    if quest is None:
        pytest.skip("SG_PostFinalT3_1_1 not in dump")
    assert quest.title_lazy_id is not None
    assert quest.title_lazy.message_key == "side-goal.hard-postFinalT3-1"
    assert "k__BackingField" not in quest.title_lazy.message_key
    assert quest.description_lazy_id is not None
    assert quest.description_lazy.message_key

    for row in ResearchSideQuest.objects.select_related("title_lazy", "description_lazy"):
        assert row.title_lazy_id is not None
        assert row.description_lazy_id is not None
        assert "k__BackingField" not in row.title_lazy.message_key
        assert row.title_lazy.lazy_text_type.endswith("LazyLocalizedText")
