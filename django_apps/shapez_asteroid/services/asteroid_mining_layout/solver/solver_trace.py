"""Env-gated NDJSON trace for asteroid mining layout solver (correlation via run_id).

**Trace / debug layer (Algorithm §STEP10):** from the solver algorithm's perspective this module
is **write-only** to NDJSON and debug files. Routing, Pass3, Reclaim, and Recovery must **not**
read ``latest.ndjson``, ``replay_latest.ndjson``, prior ``solver_summary`` trace lines, or
``replay_events`` from disk to make decisions — use live maps, ``routing_state``, and stage
contracts only. Offline tools under ``scripts/debug/`` may read these artifacts for audit,
regression, and UI replay export.

**Replay NDJSON** (``var/asteroid_mining_layout_replay`` by default): ``trace_event`` lines only —
wire shape ``{"location","message","data"}`` (§STEP10). Per-run ``{run_id}.ndjson`` plus
``replay_latest.ndjson``. Override with ``SHAPEZ_SOLVER_TRACE_PATH`` (single file) or
``SHAPEZ_SOLVER_REPLAY_DIR`` (directory for the two-file pattern).
``replay_frame`` rows omit full ``mining_map`` on disk (``mining_map_row_count`` only); full maps
stay in in-memory ``replay_events`` for the API snapshot.

**Debug NDJSON** (``var/asteroid_mining_layout_debug``): ``debug_log_event`` / ``kind: action``,
``run_start`` / ``run_end``, placement-verbose and bundle-reject diagnostics — **no** duplicate
``trace_event`` rows (replay stream is separate).

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
_REPLAY_DIR_ENV = "SHAPEZ_SOLVER_REPLAY_DIR"
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
# STEP10 trace step counter (one increment per ``trace_event`` primary call; replay wire only).
_trace_computation_cycle_var: ContextVar[int] = ContextVar(
    "mining_layout_trace_computation_cycle",
    default=0,
)
_replay_events_sink_var: ContextVar[list[dict[str, Any]] | None] = ContextVar(
    "mining_layout_replay_events_sink",
    default=None,
)
_replay_layout_ctx_var: ContextVar[dict[str, Any] | None] = ContextVar(
    "mining_layout_replay_layout_ctx",
    default=None,
)
# Pass12-only merge inputs for ``replay_frame`` layout snapshots (output; never read by routing).
_pass12_trace_merge_ctx_var: ContextVar[dict[str, Any] | None] = ContextVar(
    "mining_layout_pass12_trace_merge_ctx",
    default=None,
)
_trace_replay_stats_var: ContextVar[dict[str, int] | None] = ContextVar(
    "mining_layout_trace_replay_stats",
    default=None,
)
_run_end_solver_summary_snapshot_var: ContextVar[dict[str, Any] | None] = ContextVar(
    "mining_layout_run_end_solver_summary_snapshot",
    default=None,
)

_RUN_END_SOLVER_SUMMARY_SNAPSHOT_KEYS = frozenset(
    {
        "trace_frame_counter_glossary",
        "replay_event_count",
        "replay_frame_count",
        "replay_frame_source",
        "replay_candidate_event_count",
        "map_timeline_frame_count",
        "solver_timeline_frame_count",
        "pass3_zero_gain_reason",
        "pass3_zero_gain_context",
    }
)

_REPLAY_FRAME_STRIDE = 10
_CANDIDATE_REJECT_MESSAGES = frozenset(
    {
        "bundle_reject_invalid_stub",
        "bundle_reject_no_route",
    },
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


def trace_bind_replay_events(events: list[dict[str, Any]]) -> None:
    """Bind ``replay_events`` for optional ``replay_frame`` appends (output-only)."""

    _replay_events_sink_var.set(events)


def trace_bind_pass12_merge_context(ctx: dict[str, Any] | None) -> Token[dict[str, Any] | None]:
    """Bind merge inputs for Pass12 ``replay_frame`` ``mining_map`` snapshots (output-only)."""

    return _pass12_trace_merge_ctx_var.set(ctx)


def trace_reset_pass12_merge_context(token: Token[dict[str, Any] | None]) -> None:
    _pass12_trace_merge_ctx_var.reset(token)


def trace_pass12_merge_context_get() -> dict[str, Any] | None:
    c = _pass12_trace_merge_ctx_var.get()
    return c if isinstance(c, dict) else None


def trace_publish_layout_observation(
    *,
    phase: str | None = None,
    step_index: int | None = None,
    mining_map: list[dict[str, Any]] | None = None,
    metrics: dict[str, Any] | None = None,
) -> None:
    """Publish layout/metrics hints for ``replay_frame`` payloads (trace output only)."""

    cur = dict(_replay_layout_ctx_var.get() or {})
    if phase is not None:
        cur["phase"] = phase
    if step_index is not None:
        cur["step_index"] = int(step_index)
    if mining_map is not None:
        cur["mining_map"] = mining_map
    if metrics is not None:
        cur["metrics"] = dict(metrics)
    _replay_layout_ctx_var.set(cur)


def trace_publish_pass12_scratch_metrics(scratch: Any, *, transport_kind: str) -> None:
    """Update trace metrics from Pass12 scratch (cheap counts; output-only)."""

    if scratch is None:
        return
    try:
        metrics = {
            "extractor_count": len(scratch.extractor_cells),
            "extension_count": len(scratch.extension_facings),
            "route_cell_count": len(scratch.transport_cells),
            "internal_transport_count": None,
            "extension_count_transport_adjacent": None,
            "transport_connected": None,
        }
    except (TypeError, AttributeError):
        return
    _ = transport_kind
    trace_publish_layout_observation(metrics=metrics)


def _trace_stats_ensure() -> dict[str, int]:
    s = _trace_replay_stats_var.get()
    if s is None:
        s = {"replay_event": 0, "replay_frame": 0, "candidate_reject": 0}
        _trace_replay_stats_var.set(s)
    return s


def _canonical_trace_event_type(message: str) -> str:
    if message in _CANDIDATE_REJECT_MESSAGES:
        return "candidate_reject"
    return message


def _replay_diag_for_summary() -> dict[str, Any]:
    if not trace_enabled():
        return {
            "replay_event_count": 0,
            "replay_frame_count": 0,
            "replay_candidate_event_count": 0,
            "replay_has_computation_cycle": False,
            "replay_frame_source": "trace_disabled",
        }
    s = _trace_replay_stats_var.get() or {
        "replay_event": 0,
        "replay_frame": 0,
        "candidate_reject": 0,
    }
    rec = int(s.get("replay_event", 0))
    rfc = int(s.get("replay_frame", 0))
    crc = int(s.get("candidate_reject", 0))
    if rfc > 0:
        src = "replay_trace"
    elif rec > 0:
        src = "pass_snapshot_fallback"
    else:
        src = "unknown"
    return {
        "replay_event_count": rec,
        "replay_frame_count": rfc,
        "replay_candidate_event_count": crc,
        "replay_has_computation_cycle": rec > 0,
        "replay_frame_source": src,
    }


def replay_diag_counts_for_solver_summary() -> dict[str, Any]:
    """Replay-layer counts for ``solver_summary`` (NDJSON ``emit_solver_summary_once`` keys)."""

    return dict(_replay_diag_for_summary())


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
    merged.update(_replay_diag_for_summary())
    snap = {k: merged[k] for k in _RUN_END_SOLVER_SUMMARY_SNAPSHOT_KEYS if k in merged}
    if snap:
        _run_end_solver_summary_snapshot_var.set(snap)
    trace_event(location, "solver_summary", {"solver_summary": merged})
    if trace_enabled():
        debug_log_event(
            location,
            "solver_summary",
            {"solver_summary": merged},
        )
    return True


def trace_bundle_reject_no_route(location: str, data: dict[str, Any] | None = None) -> None:
    """bundle route probe no_route 이벤트를 NDJSON trace에 기록한다 (§16 STEP10 streaming)."""
    trace_event(location, "bundle_reject_no_route", dict(data or {}))


def trace_bundle_reject_invalid_stub(
    location: str,
    data: dict[str, Any] | None = None,
    *,
    scratch: Any = None,
) -> None:
    """``stub_cell`` not in merged transport (generator bug); not a route probe miss."""

    if scratch is not None:
        trace_publish_pass12_scratch_metrics(
            scratch,
            transport_kind=str(getattr(scratch, "transport_kind", "") or ""),
        )
    trace_event(location, "bundle_reject_invalid_stub", dict(data or {}))


def _replay_log_dir() -> Path:
    """Replay NDJSON 루트 (per-run + replay_latest).

    ``SHAPEZ_SOLVER_TRACE_PATH``가 설정되면 이 디렉터리는 쓰이지 않는다.
    """

    custom = os.environ.get(_REPLAY_DIR_ENV, "").strip()
    if custom:
        return Path(custom)
    return Path(settings.BASE_DIR) / "var" / "asteroid_mining_layout_replay"


def _replay_log_paths(run_id: str | None) -> list[Path]:
    """STEP10 replay NDJSON 출력 경로. ``SHAPEZ_SOLVER_TRACE_PATH``면 단일 파일만."""

    custom = os.environ.get(_TRACE_PATH_ENV, "").strip()
    if custom:
        return [Path(custom)]
    root = _replay_log_dir()
    name = run_id or "no-run"
    return [root / f"{name}.ndjson", root / "replay_latest.ndjson"]


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


def _truncate_replay_files(run_id: str) -> None:
    """Clear replay NDJSON targets so each traced solver run starts from empty files."""

    for path in _replay_log_paths(run_id):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        except OSError as exc:
            _logger.warning("mining_layout replay trace truncate failed path=%s err=%s", path, exc)


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
    snap_tok = _run_end_solver_summary_snapshot_var.set(None)
    started = time.perf_counter()
    _trace_computation_cycle_var.set(0)
    _replay_events_sink_var.set(None)
    _replay_layout_ctx_var.set({})
    _pass12_trace_merge_ctx_var.set(None)
    _trace_replay_stats_var.set({"replay_event": 0, "replay_frame": 0, "candidate_reject": 0})
    if trace_enabled():
        _prune_var_logging_files()
        _truncate_replay_files(run_id)
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
                    "replay_dir_override": os.environ.get(_REPLAY_DIR_ENV, ""),
                    "debug_dir_override": os.environ.get(_DEBUG_DIR_ENV, ""),
                    "resolved_debug_dir": str(_debug_log_dir()),
                    "resolved_replay_dir": str(_replay_log_dir()),
                },
            },
        )
    try:
        yield
    finally:
        elapsed = time.perf_counter() - started
        snap = _run_end_solver_summary_snapshot_var.get()
        _run_end_solver_summary_snapshot_var.reset(snap_tok)
        end_payload: dict[str, Any] = {"run_id": run_id, "elapsed_s": round(elapsed, 6)}
        if isinstance(snap, dict) and snap:
            end_payload["solver_summary"] = snap
        debug_log_event(
            "solver_trace.trace_run_scope",
            "run_end",
            end_payload,
        )
        _summary_emitted_var.reset(summary_tok)
        trace_run_id_reset(token)
        _trace_computation_cycle_var.set(0)
        _replay_events_sink_var.set(None)
        _replay_layout_ctx_var.set(None)
        _pass12_trace_merge_ctx_var.set(None)
        _trace_replay_stats_var.set(None)


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


def _write_replay_ndjson_record(record: dict[str, Any]) -> None:
    """Append one replay NDJSON line (no ``trace_enabled`` gate — caller gates)."""

    line = json.dumps(record, ensure_ascii=False, default=str)
    _logger.debug("%s", line)
    rid = _run_id_var.get()
    for path in _replay_log_paths(rid):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError as exc:
            _logger.warning("mining_layout replay trace append failed path=%s err=%s", path, exc)


def _emit_supplemental_replay_frame(*, trace_computation_cycle: int) -> None:
    """Emit ``replay_frame`` row + optional in-memory replay event (stride-based).

    ``replay_events`` payloads keep ``mining_map`` when present (API ``cycle_frames``).
    Replay NDJSON omits full ``mining_map`` and writes ``mining_map_row_count`` only so
    ``replay_latest.ndjson`` does not grow by megabytes per line.
    """

    if trace_computation_cycle <= 0 or (trace_computation_cycle % _REPLAY_FRAME_STRIDE) != 0:
        return
    ctx = dict(_replay_layout_ctx_var.get() or {})
    phase = str(ctx.get("phase") or "unknown")
    step_index = ctx.get("step_index")
    layout_snap = ctx.get("layout_snapshot_phase")
    mining_map = ctx.get("mining_map")
    raw_m = ctx.get("metrics")
    base_metrics: dict[str, Any] = dict(raw_m) if isinstance(raw_m, dict) else {}
    metrics: dict[str, Any] = {
        "extractor_count": base_metrics.get("extractor_count"),
        "extension_count": base_metrics.get("extension_count"),
        "route_cell_count": base_metrics.get("route_cell_count"),
        "internal_transport_count": base_metrics.get("internal_transport_count"),
        "transport_connected": base_metrics.get("transport_connected"),
    }
    payload: dict[str, Any] = {
        "frame_kind": "cycle_snapshot",
        "trace_computation_cycle": int(trace_computation_cycle),
        "phase": phase,
        "layout_snapshot_phase": layout_snap if isinstance(layout_snap, str) else None,
        "metrics": metrics,
        "decision": None,
    }
    if isinstance(mining_map, list):
        from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_mutation_transaction import (  # noqa: E501
            copy_mining_map_rows as _copy_mining_map_rows,
        )

        payload["mining_map"] = _copy_mining_map_rows(mining_map)

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_events import (  # noqa: E501
        SolverMutationEventKind,
    )

    sink = _replay_events_sink_var.get()
    if sink is not None:
        sink.append(
            {
                "kind": SolverMutationEventKind.REPLAY_FRAME.value,
                "phase": phase,
                "payload": dict(payload),
            }
        )

    rid = _run_id_var.get()
    merged_rf: dict[str, Any] = {
        "ts": time.time(),
        "event_type": "replay_frame",
        "computation_cycle": int(trace_computation_cycle),
        "frame_kind": "cycle_snapshot",
        "trace_computation_cycle": int(trace_computation_cycle),
        "phase": phase,
        "step_index": step_index,
        "layout_snapshot_phase": payload["layout_snapshot_phase"],
        "metrics": metrics,
        "decision": None,
    }
    if isinstance(mining_map, list):
        merged_rf["mining_map"] = mining_map
    if rid is not None:
        merged_rf["run_id"] = rid
    ndjson_data = {k: v for k, v in merged_rf.items() if k != "mining_map"}
    if isinstance(mining_map, list):
        ndjson_data["mining_map_row_count"] = len(mining_map)
    _write_replay_ndjson_record(
        {"location": "solver_trace.replay_frame", "message": "replay_frame", "data": ndjson_data}
    )
    st = _trace_stats_ensure()
    st["replay_frame"] = int(st.get("replay_frame", 0)) + 1


def trace_event(location: str, message: str, data: dict[str, Any] | None = None) -> None:
    """STEP10 replay UI가 읽는 NDJSON trace event를 기록한다 (§16).

    Writes **replay wire only** (see module docstring). Debug NDJSON is not written here.

    상세: documents/Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md"""
    if not trace_enabled():
        return
    merged: dict[str, Any] = dict(data or {})
    n = _trace_computation_cycle_var.get() + 1
    _trace_computation_cycle_var.set(n)
    merged["computation_cycle"] = n
    merged["event_type"] = _canonical_trace_event_type(message)
    merged["ts"] = time.time()
    rid = _run_id_var.get()
    if rid is not None:
        merged["run_id"] = rid
    record = {"location": location, "message": message, "data": merged}
    _write_replay_ndjson_record(record)

    st = _trace_stats_ensure()
    st["replay_event"] = int(st.get("replay_event", 0)) + 1
    if merged["event_type"] == "candidate_reject":
        st["candidate_reject"] = int(st.get("candidate_reject", 0)) + 1

    _emit_supplemental_replay_frame(trace_computation_cycle=n)
