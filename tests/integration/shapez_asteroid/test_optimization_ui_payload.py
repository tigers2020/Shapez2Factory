"""Lab context exposes optimization replay envelope (Sequence 9B–9C, DB-backed shell)."""

from __future__ import annotations

import json
import re

import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory

from django_apps.shapez_asteroid.optimization.optimization_ui_payload import (
    OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY,
    empty_optimization_replay_track_payload,
)
from django_apps.web.services.asteroid_lab_page_context import lab_page_context, neutral_lab_context

_SCRIPT_RE = re.compile(
    r'<script id="optimization-replay-json" type="application/json">(?P<body>.*?)</script>',
    re.DOTALL,
)


@pytest.mark.django_db
def test_lab_page_context_optimization_replay_matches_empty_payload_helper() -> None:
    ctx = lab_page_context()
    assert ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY] == empty_optimization_replay_track_payload()


@pytest.mark.integration
def test_lab_shell_template_json_script_exposes_optimization_replay() -> None:
    ctx = neutral_lab_context()
    ctx["blueprint_code"] = ""
    ctx["lab_project_slug"] = ""
    html = render_to_string(
        "web/asteroid_miner_layout_solver.html",
        ctx,
        request=RequestFactory().get("/"),
    )
    m = _SCRIPT_RE.search(html)
    assert m is not None
    assert json.loads(m.group("body")) == empty_optimization_replay_track_payload()
