"""PR-2: frozen genetic_sample_seeds and game_data fixture loader tests."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures import (
    golden_fixture_dir,
    load_game_data_rules,
    load_genetic_sample_seeds,
    load_genetic_sample_seeds_payload,
)

_REPO = Path(__file__).resolve().parents[4]
_SEEDS = golden_fixture_dir() / "genetic_sample_seeds.json"
_GAME_DATA = golden_fixture_dir() / "game_data_snapshot_min.json"
_EXPORT_SCRIPT = _REPO / "scripts" / "export_golden_gene_seeds_fixture.py"


def _fixtures_ready() -> bool:
    return _SEEDS.is_file() and _GAME_DATA.is_file()


@pytest.mark.skipif(not _fixtures_ready(), reason="PR-2 frozen fixtures missing")
def test_load_genetic_sample_seeds_without_django_db() -> None:
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE"}
    code = (
        "from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures import "
        "load_genetic_sample_seeds\n"
        "import sys\n"
        "snap = load_genetic_sample_seeds()\n"
        "assert snap.schema_version == 'genetic_sample_seed_v1'\n"
        "assert len(snap.entries) >= 18\n"
        "leaked = sorted(x for x in sys.modules if x == 'django' or x.startswith('django.'))\n"
        "assert not leaked, leaked\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        cwd=_REPO,
    )
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"


@pytest.mark.skipif(not _fixtures_ready(), reason="PR-2 frozen fixtures missing")
def test_genetic_sample_seeds_payload_is_deterministic() -> None:
    digest_a = hashlib.sha256(_SEEDS.read_bytes()).hexdigest()
    digest_b = hashlib.sha256(_SEEDS.read_bytes()).hexdigest()
    assert digest_a == digest_b
    payload = load_genetic_sample_seeds_payload()
    assert payload["schema_version"] == "genetic_sample_seed_v1"
    assert payload["deterministic_sort_key"] == "by_gene_id_then_throughput_desc"
    entries = payload.get("entries")
    assert isinstance(entries, list)
    assert entries
    snap_a = load_genetic_sample_seeds()
    snap_b = load_genetic_sample_seeds()
    assert [e.gene_id for e in snap_a.entries] == [e.gene_id for e in snap_b.entries]


@pytest.mark.skipif(not _fixtures_ready(), reason="PR-2 frozen fixtures missing")
def test_load_genetic_sample_seeds_in_process_smoke() -> None:
    snapshot = load_genetic_sample_seeds()
    assert snapshot.schema_version == "genetic_sample_seed_v1"
    assert len(snapshot.entries) >= 18


@pytest.mark.skipif(not _fixtures_ready(), reason="PR-2 frozen fixtures missing")
def test_load_game_data_rules_from_asteroid_golden_fixture() -> None:
    rules = load_game_data_rules()
    shape_rule = rules.mining_extraction_rule(resource_kind="shape")
    assert shape_rule.mini_unit_output_per_min > 0


def test_export_golden_gene_seeds_fixture_import_safe() -> None:
    assert _EXPORT_SCRIPT.is_file()
    before = set(sys.modules)
    spec = importlib.util.spec_from_file_location(
        "export_golden_gene_seeds_fixture_test",
        _EXPORT_SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    after = set(sys.modules)
    new_modules = after - before
    assert not any(name == "django" or name.startswith("django.") for name in new_modules)
    assert callable(module.main)
