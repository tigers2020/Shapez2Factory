"""Space transport layout registry import from game_data JSON."""

from __future__ import annotations

import pytest
from django.core.management import call_command

from django_apps.game_data.models import SpaceTransportLayoutRegistry
from tests.unit.game_data.dump_paths import resolve_game_data_source_dir


@pytest.mark.django_db
def test_import_registers_54_space_transport_layouts() -> None:
    source = resolve_game_data_source_dir()
    if source is None:
        pytest.skip("game_data bundle not present")

    call_command("import_game_data", source=str(source), batch_name="test-space-layouts")

    assert SpaceTransportLayoutRegistry.objects.count() == 54
    assert SpaceTransportLayoutRegistry.objects.filter(transport_kind="space_belt").count() == 27
    assert SpaceTransportLayoutRegistry.objects.filter(transport_kind="space_pipe").count() == 27

    forward = SpaceTransportLayoutRegistry.objects.get(tile_id="SpaceBelt_Forward")
    assert forward.layout_suffix == "Forward"
    assert forward.group_id == "SpaceBeltsGroup"
    assert forward.routing_allowed is True
    assert forward.simulation_family == "conveyor"
    assert forward.has_io_signature is True
    assert forward.input_mask_eswn == "0010"
    assert forward.output_mask_eswn == "1000"

    lift = SpaceTransportLayoutRegistry.objects.get(tile_id="SpaceBelt_Lift1UpForward")
    assert lift.routing_allowed is False
    assert lift.has_io_signature is False

    merger = SpaceTransportLayoutRegistry.objects.get(tile_id="SpacePipe_YMerger")
    assert merger.simulation_family == "merger"
