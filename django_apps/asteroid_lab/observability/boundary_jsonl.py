"""Append-only JSONL logs at data transformation boundaries (no stdlib logging / no stderr).

Enable with ``ASTEROID_LAB_BOUNDARY_JSONL=1`` (or ``true`` / ``on``). Lines go under
``ASTEROID_LAB_BOUNDARY_JSONL_DIR`` or ``<BASE_DIR>/var/asteroid_boundary_logs``
(``var/`` is gitignored).
"""

from __future__ import annotations

import json
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_write_lock = threading.Lock()


def boundary_jsonl_enabled() -> bool:
    v = os.environ.get("ASTEROID_LAB_BOUNDARY_JSONL", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _repo_base_dir() -> Path:
    try:
        from django.conf import settings

        return Path(settings.BASE_DIR).resolve()
    except Exception:
        # django_apps/asteroid_lab/observability/boundary_jsonl.py → repo root
        return Path(__file__).resolve().parents[3]


def boundary_jsonl_dir() -> Path:
    raw = os.environ.get("ASTEROID_LAB_BOUNDARY_JSONL_DIR", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return _repo_base_dir() / "var" / "asteroid_boundary_logs"


def _sanitize_run_id(run_id: str) -> str:
    s = run_id.strip() or "unset"
    for ch in ("/", "\\", ":", "\x00"):
        s = s.replace(ch, "_")
    return s[:200]


def emit_boundary_jsonl(
    *,
    run_id: str,
    stage: str,
    boundary: str,
    data: dict[str, Any],
) -> None:
    """Write one JSON object as a single line to ``{dir}/{run_id}.jsonl``."""

    if not boundary_jsonl_enabled():
        return

    ts = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    record: dict[str, Any] = {
        "ts": ts,
        "run_id": run_id,
        "stage": stage,
        "boundary": boundary,
        **data,
    }
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
    root = boundary_jsonl_dir()
    path = root / f"{_sanitize_run_id(run_id)}.jsonl"

    with _write_lock:
        root.mkdir(parents=True, exist_ok=True)
        path.open("a", encoding="utf-8").write(line)


def summarize_cell_kind_transitions(
    before: tuple[Any, ...],
    after: tuple[Any, ...],
    *,
    max_items: int = 8000,
) -> list[dict[str, Any]]:
    """Pair cells by ``(x, y, layer)`` and list ``cell_kind`` changes (for JSONL payloads).

    Each item includes explicit ``raw_x`` / ``raw_y`` names.
    """

    before_map: dict[tuple[int, int, int | None], str] = {}
    for c in before:
        before_map[(int(c.x), int(c.y), c.layer)] = str(c.cell_kind)

    out: list[dict[str, Any]] = []
    for c in after:
        key = (int(c.x), int(c.y), c.layer)
        prev = before_map.get(key)
        cur = str(c.cell_kind)
        if prev != cur:
            item: dict[str, Any] = {
                "raw_x": key[0],
                "raw_y": key[1],
                "layer": key[2],
                "cell_kind_before": prev,
                "cell_kind_after": cur,
            }
            out.append(item)
        if len(out) >= max_items:
            break
    return out


__all__ = [
    "boundary_jsonl_dir",
    "boundary_jsonl_enabled",
    "emit_boundary_jsonl",
    "summarize_cell_kind_transitions",
]
