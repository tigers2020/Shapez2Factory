from __future__ import annotations

import json
from pathlib import Path

import pytest

from django_apps.asteroid_lab.replay.replay_wire_read_sanitize import audit_replay_wire_cell
from tests.support.lab_replay_sprite_wire import golden_transport_replay_frames

_REPO = Path(__file__).resolve().parents[4]
_FIXTURE_ROOT = _REPO / "tests" / "fixtures" / "asteroid_lab"
_BANNED = "shape_belt"


def _iter_wire_rows(obj: object, path: str) -> list[tuple[str, dict]]:
    rows: list[tuple[str, dict]] = []
    if isinstance(obj, dict):
        if "kind" in obj and "x" in obj and "y" in obj:
            rows.append((path, obj))
        for k, v in obj.items():
            rows.extend(_iter_wire_rows(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            rows.extend(_iter_wire_rows(item, f"{path}[{i}]"))
    return rows


def test_persisted_replay_frames_wire_audit_golden_assembler() -> None:
    violations: list[str] = []
    for frame in golden_transport_replay_frames():
        for path, row in _iter_wire_rows(frame, "frame"):
            try:
                audit_replay_wire_cell(row)
            except Exception as exc:
                violations.append(f"{path}: {exc}")
    assert not violations, violations


@pytest.mark.skipif(not _FIXTURE_ROOT.is_dir(), reason="no fixture dir")
def test_persisted_fixture_json_no_shape_belt_on_candidate_transport() -> None:
    for path in sorted(_FIXTURE_ROOT.rglob("*.json")):
        text = path.read_text(encoding="utf-8")
        if _BANNED not in text:
            continue
        payload = json.loads(text)
        for rel_path, row in _iter_wire_rows(payload, str(path)):
            kind = str(row.get("kind") or row.get("cell_kind") or "")
            transport = str(row.get("transport") or row.get("transport_kind") or "")
            if "candidate" in kind and _BANNED in transport:
                pytest.fail(f"{rel_path}: candidate row still has shape_belt transport")
