"""Django layer_03 package must not host algorithm modules."""

from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
_DJANGO_L3 = _REPO / "django_apps" / "asteroid_lab" / "layers" / "layer_03_rim_greedy_placement"

_FORBIDDEN = frozenset(
    {
        "greedy_pass1.py",
        "greedy_pass2.py",
        "traversal_variants.py",
        "rim_anchors.py",
        "append.py",
        "greedy_seed.py",
        "seed_orient.py",
        "cardinal_map.py",
        "local_window.py",
        "dps_policy.py",
    }
)


def test_no_django_l3_algorithm_modules_on_disk() -> None:
    names = {p.name for p in _DJANGO_L3.iterdir() if p.is_file()}
    assert names <= {"__init__.py", "run.py"}
    assert not names & _FORBIDDEN


def test_django_run_reexports_core_entrypoint() -> None:
    import django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.run as django_run
    from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement import (
        run as core_run,
    )

    assert (
        django_run.run_layer_03_rim_greedy_placement is core_run.run_layer_03_rim_greedy_placement
    )
    assert django_run.ALGORITHM_STUB_ID is core_run.ALGORITHM_STUB_ID


def test_core_l3_run_entrypoint_is_authoritative() -> None:
    from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement import (
        run as core_run,
    )

    assert callable(core_run.run_layer_03_rim_greedy_placement)
    assert core_run.ALGORITHM_STUB_ID == "algorithm_reset"
