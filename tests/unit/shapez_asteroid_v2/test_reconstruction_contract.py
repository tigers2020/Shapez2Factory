from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction.asteroid_reconstruction import (  # noqa: E501
    reconstruct_asteroid_mining_field,
)


def test_reconstruction_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        reconstruct_asteroid_mining_field({})
