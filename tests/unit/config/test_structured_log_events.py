"""Structured event name contracts for migrated call sites (PR-3)."""

from __future__ import annotations

import json
import logging
import re
from unittest.mock import patch

import pytest

from config.logging_json import JsonLogFormatter, RequestIdFilter
from django_apps.asteroid_lab.models import GeneSeed
from django_apps.asteroid_lab.services.genetic_sample_gene_export import (
    gene_template_from_gene_seed,
)
from django_apps.web.services.graph_preview import _PlaywrightPrerenderer

_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")


def _capture_log(logger_name: str) -> tuple[logging.Logger, list[logging.LogRecord]]:
    logger = logging.getLogger(logger_name)
    records: list[logging.LogRecord] = []

    class _Handler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _Handler()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger, records


def _payload(record: logging.LogRecord) -> dict[str, object]:
    RequestIdFilter().filter(record)
    return json.loads(JsonLogFormatter().format(record))


@pytest.mark.django_db
def test_gene_cache_miss_event() -> None:
    seed = GeneSeed(name="manual", gene_key="missing_key_xyz", code="x", metadata_json={})
    logger, records = _capture_log("django_apps.asteroid_lab.services.genetic_sample_gene_export")
    handler = logger.handlers[0]
    try:
        with patch(
            "django_apps.asteroid_lab.services.genetic_sample_gene_export._build_exhaustive_cache",
            return_value={},
        ):
            gene_template_from_gene_seed(seed)
    finally:
        logger.removeHandler(handler)

    debug_records = [r for r in records if r.levelno == logging.DEBUG]
    assert debug_records
    payload = _payload(debug_records[0])
    assert payload["message"] == "gene_cache_miss"
    assert _SNAKE_CASE.match(str(payload["message"]))
    assert payload["gene_key"] == "missing_key_xyz"
    assert payload["step"] == "validate"


def test_graph_preview_script_missing_event(tmp_path) -> None:
    missing = tmp_path / "missing_render.js"
    renderer = _PlaywrightPrerenderer(missing, timeout_seconds=5, cache_dir=tmp_path)
    logger, records = _capture_log("django_apps.web.services.graph_preview")
    handler = logger.handlers[0]
    try:
        renderer.render_png({}, tmp_path / "out.png")
    finally:
        logger.removeHandler(handler)

    warn_records = [r for r in records if r.levelno == logging.WARNING]
    assert warn_records
    payload = _payload(warn_records[0])
    assert payload["message"] == "graph_preview_script_missing"
    assert _SNAKE_CASE.match(str(payload["message"]))
    assert payload["script_path"] == str(missing)


def test_recipe_graph_recompute_timing_event() -> None:
    from django_apps.shapez_solver.services.recipe_graph_recompute import (
        default_empty_graph_document,
        recompute_graph_document,
    )

    logger, records = _capture_log("django_apps.shapez_solver.services.recipe_graph_recompute")
    handler = logger.handlers[0]
    try:
        recompute_graph_document(default_empty_graph_document())
    finally:
        logger.removeHandler(handler)

    info_records = [r for r in records if r.levelno == logging.INFO]
    timing = [r for r in info_records if r.getMessage() == "recipe_graph_recompute"]
    assert timing
    payload = _payload(timing[0])
    assert _SNAKE_CASE.match(str(payload["message"]))
    assert "ms" in payload
