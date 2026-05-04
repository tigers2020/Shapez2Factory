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


def test_mix_same_channel_stable() -> None:
    assert mix_color_pair("r", "r") == "r"


def test_mix_empty_channel() -> None:
    assert mix_color_pair("-", "r") == "r"
    assert mix_color_pair("-", "-") == "-"


def test_mix_unsupported_raises() -> None:
    with pytest.raises(ValueError):
        mix_color_pair("y", "r")
