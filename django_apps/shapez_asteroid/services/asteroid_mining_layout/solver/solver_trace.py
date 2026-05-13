"""Env-gated NDJSON trace for asteroid mining layout solver (correlation via run_id).

**Trace / debug layer (Algorithm §STEP10):** from the solver algorithm's perspective this module
is **write-only** to NDJSON and debug files. Routing, Pass3, Reclaim, and Recovery must **not**
read ``latest.ndjson``, ``mining_layout_solver_trace.ndjson``, prior ``solver_summary`` trace
lines, or ``replay_events`` from disk to make decisions — use live maps, ``routing_state``, and
stage contracts only. Offline tools under ``scripts/debug/`` may read these artifacts for audit,
regression, and UI replay export.

Single ``solver_summary`` payload per run: see ``build_solver_timeline`` output and
``documents/Algorithm/cursor_agent_tier1_prompts_2026-05-10.md`` §Trace contract (recovery
chain, Pass3/P4 fields, ``before_return_validate``, STEP 0.5 ``existing_layout_analysis``).

Debug NDJSON under ``var/asteroid_mining_layout_debug`` includes:

- ``run_start`` / ``run_end`` with ``debug_session`` (env overrides, resolved paths) and
  ``elapsed_s`` on end.
- ``bundle_reject_no_route`` rows include ``transport_probe`` / ``cheap_escape_probe`` diagnosis
  from ``routing/route_probe.py`` (component size, skip reasons, visit caps).
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from pathlib import Path
from typing import Any

from django.conf import settings

_ALGO_DBG_ENV = "SHAPEZ_SOLVER_ALGO_DEBUG"
_TRACE_PATH_ENV = "SHAPEZ_SOLVER_TRACE_PATH"
_DEBUG_DIR_ENV = "SHAPEZ_SOLVER_DEBUG_DIR"
# Per-candidate / per-direction placement logs (e.g. select_extension_tree_relaxed exit).
# DEBUG alone does not enable these — avoids multi‑MB NDJSON on large maps.
_PLACEMENT_VERBOSE_ENV = "SHAPEZ_SOLVER_TRACE_PLACEMENT_VERBOSE"

_logger = logging.getLogger("shapez_asteroid.mining_layout_solver")

# ``var/`` 아래 NDJSON·``.log``가 이 개수 이상이면 mtime 오래된 순으로 지워 최대 (값-1)개만 남긴다.
_VAR_LOG_PRUNE_THRESHOLD = 10
_VAR_LOG_SUFFIXES = frozenset({".ndjson", ".log"})

_run_id_var: ContextVar[str | None] = ContextVar("mining_layout_solver_run_id", default=None)
_summary_emitted_var: ContextVar[bool] = ContextVar(
    "mining_layout_solver_summary_emitted",
    default=False,
)


def trace_enabled() -> bool:
    """STEP10 replay/cycle streaming trace 활성 여부를 env/settings에서 읽는다 (§16)."""
    raw = os.environ.get(_ALGO_DBG_ENV, "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    return bool(getattr(settings, "DEBUG", False))


def trace_placement_verbose() -> bool:
    """High-volume placement NDJSON lines. Opt-in via env even when ``trace_enabled()`` is True."""

    raw = os.environ.get(_PLACEMENT_VERBOSE_ENV, "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def new_trace_run_id() -> str:
    """STEP10 trace correlation용 짧은 run_id를 생성한다 (§16 replay UI)."""
    return uuid.uuid4().hex[:12]


def trace_run_id_set(run_id: str) -> Token[str | None]:
    """현재 context에 STEP10 trace run_id를 설정한다 (§16 replay UI)."""
    return _run_id_var.set(run_id)


def trace_run_id_reset(token: Token[str | None]) -> None:
    """trace_run_scope 종료 시 run_id context token을 원복한다 (§16 replay UI)."""
    _run_id_var.reset(token)


def trace_run_id_current() -> str | None:
    """현재 STEP10 trace run_id를 조회한다 (§16 replay UI)."""
    return _run_id_var.get()


def emit_solver_summary_once(location: str, payload: dict[str, Any]) -> bool:
    """Emit at most one ``solver_summary`` trace event per ``trace_run_scope``.

    Returns True if this call emitted, False if a summary was already emitted in this scope.
    """

    if _summary_emitted_var.get():
        return False
    _summary_emitted_var.set(True)
    rid = _run_id_var.get()
    merged = dict(payload)
    if rid is not None:
        merged.setdefault("run_id", rid)
    trace_event(location, "solver_summary", {"solver_summary": merged})
    return True


def trace_bundle_reject_no_route(location: str, data: dict[str, Any] | None = None) -> None:
    """bundle route probe no_route 이벤트를 NDJSON trace에 기록한다 (§16 STEP10 streaming)."""
    trace_event(location, "bundle_reject_no_route", dict(data or {}))


def trace_bundle_reject_invalid_stub(location: str, data: dict[str, Any] | None = None) -> None:
    """``stub_cell`` not in merged transport (generator bug); not a route probe miss."""

    trace_event(location, "bundle_reject_invalid_stub", dict(data or {}))


def _trace_paths() -> list[Path]:
    """STEP10 NDJSON trace 출력 경로 목록을 결정한다 (§16 replay UI)."""
    custom = os.environ.get(_TRACE_PATH_ENV, "").strip()
    base = Path(settings.BASE_DIR)
    if custom:
        return [Path(custom)]
    return [base / "var" / "mining_layout_solver_trace.ndjson"]


def _debug_log_dir() -> Path:
    """asteroid mining layout debug 로그 폴더를 결정한다."""

    custom = os.environ.get(_DEBUG_DIR_ENV, "").strip()
    if custom:
        return Path(custom)
    return Path(settings.BASE_DIR) / "var" / "asteroid_mining_layout_debug"


def _debug_log_paths(run_id: str | None) -> list[Path]:
    """run_id별 debug NDJSON과 latest NDJSON 경로를 돌려준다."""

    root = _debug_log_dir()
    name = run_id or "no-run"
    return [root / f"{name}.ndjson", root / "latest.ndjson"]


def _var_log_file_candidates(var_root: Path) -> list[Path]:
    """``var/`` 이하의 NDJSON·``.log`` 파일 경로를 수집한다 (디렉터리 제외)."""

    if not var_root.is_dir():
        return []
    out: list[Path] = []
    for path in var_root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _VAR_LOG_SUFFIXES:
            continue
        out.append(path)
    return out


def _prune_var_logging_files() -> None:
    """``var/`` 로그가 ``_VAR_LOG_PRUNE_THRESHOLD``개 이상이면 mtime 오래된 순으로 삭제한다."""

    var_root = Path(settings.BASE_DIR) / "var"
    try:
        candidates = _var_log_file_candidates(var_root)
        if len(candidates) < _VAR_LOG_PRUNE_THRESHOLD:
            return
        max_retained = _VAR_LOG_PRUNE_THRESHOLD - 1
        delete_count = len(candidates) - max_retained
        ordered = sorted(
            candidates,
            key=lambda p: (p.stat().st_mtime_ns, str(p)),
        )
        for path in ordered[:delete_count]:
            try:
                path.unlink()
            except OSError as exc:
                _logger.warning("var log prune unlink failed path=%s err=%s", path, exc)
    except OSError as exc:
        _logger.warning("var log prune scan failed root=%s err=%s", var_root, exc)


def _truncate_trace_files() -> None:
    """Clear trace NDJSON targets so each traced solver run starts from an empty file."""
    for path in _trace_paths():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        except OSError as exc:
            _logger.warning("mining_layout trace truncate failed path=%s err=%s", path, exc)


def _prepare_debug_log_files(run_id: str) -> None:
    """이번 solver run의 debug NDJSON 파일을 빈 파일로 준비한다."""

    for path in _debug_log_paths(run_id):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        except OSError as exc:
            _logger.warning("mining_layout debug log prepare failed path=%s err=%s", path, exc)


def _write_debug_record(record: dict[str, Any]) -> None:
    """debug NDJSON record를 var/asteroid_mining_layout_debug 아래에 append한다."""

    if not trace_enabled():
        return
    rid = _run_id_var.get()
    if rid is not None:
        record.setdefault("run_id", rid)
    record.setdefault("ts", time.time())
    line = json.dumps(record, ensure_ascii=False, default=str)
    for path in _debug_log_paths(rid):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError as exc:
            _logger.warning("mining_layout debug log append failed path=%s err=%s", path, exc)


@contextmanager
def trace_run_scope() -> Iterator[None]:
    """solver 실행 하나를 STEP10 trace run scope로 감싼다 (§16 cycle streaming)."""
    run_id = new_trace_run_id()
    token = trace_run_id_set(run_id)
    summary_tok = _summary_emitted_var.set(False)
    started = time.perf_counter()
    if trace_enabled():
        _prune_var_logging_files()
        _truncate_trace_files()
        _prepare_debug_log_files(run_id)
        debug_log_event(
            "solver_trace.trace_run_scope",
            "run_start",
            {
                "run_id": run_id,
                "debug_session": {
                    "django_debug": bool(getattr(settings, "DEBUG", False)),
                    "algo_debug_env": os.environ.get(_ALGO_DBG_ENV, ""),
                    "placement_verbose": trace_placement_verbose(),
                    "trace_path_override": os.environ.get(_TRACE_PATH_ENV, ""),
                    "debug_dir_override": os.environ.get(_DEBUG_DIR_ENV, ""),
                    "resolved_debug_dir": str(_debug_log_dir()),
                },
            },
        )
    try:
        yield
    finally:
        elapsed = time.perf_counter() - started
        debug_log_event(
            "solver_trace.trace_run_scope",
            "run_end",
            {"run_id": run_id, "elapsed_s": round(elapsed, 6)},
        )
        _summary_emitted_var.reset(summary_tok)
        trace_run_id_reset(token)


def debug_log_event(
    location: str,
    action: str,
    data: dict[str, Any] | None = None,
    *,
    level: str = "debug",
) -> None:
    """asteroid mining layout action log를 run_id별 debug NDJSON에 기록한다."""

    _write_debug_record(
        {
            "kind": "action",
            "level": level,
            "location": location,
            "action": action,
            "data": dict(data or {}),
        }
    )


def debug_trace_event(
    location: str,
    message: str,
    data: dict[str, Any] | None = None,
    *,
    frame_id: str,
) -> None:
    """Phase-boundary NDJSON trace; ``frame_id`` matches ``solver_timeline`` frame ``id``."""

    if not trace_enabled():
        return
    merged: dict[str, Any] = {"frame_id": frame_id, **(data or {})}
    trace_event(location, message, merged)


def trace_event(location: str, message: str, data: dict[str, Any] | None = None) -> None:
    """STEP10 replay UI가 읽는 NDJSON trace event를 기록한다 (§16).

    상세: documents/Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md"""
    if not trace_enabled():
        return
    merged: dict[str, Any] = dict(data or {})
    merged["ts"] = time.time()
    rid = _run_id_var.get()
    if rid is not None:
        merged["run_id"] = rid
    record = {"location": location, "message": message, "data": merged}
    line = json.dumps(record, ensure_ascii=False, default=str)
    _logger.debug("%s", line)
    _write_debug_record(
        {
            "kind": "trace",
            "level": "debug",
            "location": location,
            "message": message,
            "data": merged,
        }
    )
    for path in _trace_paths():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError as exc:
            _logger.warning("mining_layout trace append failed path=%s err=%s", path, exc)
