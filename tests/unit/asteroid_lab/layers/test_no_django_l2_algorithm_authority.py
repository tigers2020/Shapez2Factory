"""Django layer_02 package must not host algorithm modules."""

from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
_DJANGO_L2 = _REPO / "django_apps" / "asteroid_lab" / "layers" / "layer_02_exterior_transport"

_FORBIDDEN = frozenset(
    {
        "capacity.py",
        "layout_t.py",
        "placement.py",
        "plan.py",
        "rotation.py",
        "slots.py",
        "wire.py",
    }
)


def test_no_django_l2_algorithm_modules_on_disk() -> None:
    names = {p.name for p in _DJANGO_L2.iterdir() if p.is_file()}
    assert names <= {"__init__.py", "run.py"}
    assert not names & _FORBIDDEN


def test_django_run_wraps_core_entrypoint() -> None:
    import django_apps.asteroid_lab.layers.layer_02_exterior_transport.run as django_run
    from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport import (
        run as core_run,
    )

    assert callable(django_run.run_layer_02_exterior_transport)
    assert callable(core_run.run_layer_02_exterior_transport)
    # Django shim injects ORM rules default — not a bare reexport.
    assert (
        django_run.run_layer_02_exterior_transport
        is not core_run.run_layer_02_exterior_transport
    )
