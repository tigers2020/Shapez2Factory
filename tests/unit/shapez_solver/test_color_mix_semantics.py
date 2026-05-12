import pytest

from django_apps.shapez_solver.services.color_mix_semantics import mix_color_pair


def test_mix_uncolored_passes_partner() -> None:
    assert mix_color_pair("u", "r") == "r"
    assert mix_color_pair("g", "u") == "g"


def test_mix_primaries_to_secondaries() -> None:
    assert mix_color_pair("r", "g") == "y"
    assert mix_color_pair("g", "r") == "y"
    assert mix_color_pair("r", "b") == "m"
    assert mix_color_pair("g", "b") == "c"


def test_mix_secondary_and_primary_to_white() -> None:
    assert mix_color_pair("y", "b") == "w"
    assert mix_color_pair("b", "y") == "w"
    assert mix_color_pair("m", "g") == "w"
    assert mix_color_pair("c", "r") == "w"


def test_mix_same_channel_stable() -> None:
    assert mix_color_pair("r", "r") == "r"
    assert mix_color_pair("w", "w") == "w"


def test_mix_empty_channel() -> None:
    assert mix_color_pair("-", "r") == "r"
    assert mix_color_pair("-", "-") == "-"


def test_mix_unsupported_raises() -> None:
    with pytest.raises(ValueError):
        mix_color_pair("y", "r")
    with pytest.raises(ValueError):
        mix_color_pair("w", "r")
