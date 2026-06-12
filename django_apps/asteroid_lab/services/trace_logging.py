"""Asteroid Lab 援ъ“??trace JSONL writer.

濡쒓렇???붾쾭洹??곗텧臾쇱씠硫?solver ?낅젰?쇰줈 ?쎌? ?딅뒗??
"""

from __future__ import annotations

import dataclasses
import json
import re
import secrets
from collections import Counter
from collections.abc import Mapping, Sequence
from enum import Enum
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO

_SCHEMA_VERSION = 1
_STAGE_FILES: tuple[tuple[str, str], ...] = (
    ("request", "00_request.jsonl"),
    ("decode", "01_decode.jsonl"),
    ("cleanup", "02_cleanup.jsonl"),
    ("reconstruction", "03_reconstruction.jsonl"),
    ("validation", "04_validation.jsonl"),
    ("replay_payload", "05_replay_payload.jsonl"),
    ("response_payload", "06_response_payload.jsonl"),
)


def _json_safe(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Enum):
        return value.value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _json_safe(dataclasses.asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return [_json_safe(v) for v in sorted(value, key=lambda z: str(z))]
    if isinstance(value, Path):
        return str(value)
    return str(value)


def _settings_bool(name: str, default: bool = False) -> bool:
    raw = getattr(settings, name, default)
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _settings_int(name: str, default: int) -> int:
    raw = getattr(settings, name, default)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _safe_slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    return text.strip("-") or "run"


def _new_run_id() -> str:
    stamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
    return f"lab-{stamp}-{secrets.token_hex(3)}"


class AsteroidLabTraceLogger:
    """run_id/stage ?⑥쐞 JSONL writer."""

    def __init__(
        self,
        *,
        run_id: str,
        root_dir: Path,
        project_slug: str | None = None,
        solver_run_id: int | None = None,
        replay_track_id: int | None = None,
        max_events: int = 5000,
        max_bytes: int = 5_000_000,
        sample_limit: int = 128,
    ) -> None:
        self.run_id = run_id
        self.project_slug = project_slug
        self.solver_run_id = solver_run_id
        self.replay_track_id = replay_track_id
        self.max_events = max(1, int(max_events))
        self.max_bytes = max(1024, int(max_bytes))
        self.sample_limit = max(1, int(sample_limit))
        self.run_dir = Path(root_dir) / "runs" / _safe_slug(run_id)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._event_count = 0
        self._byte_count = 0
        self._truncated = False
        self._stage_counts: Counter[str] = Counter()

    def bind_context(
        self,
        *,
        solver_run_id: int | None = None,
        replay_track_id: int | None = None,
    ) -> None:
        """?섏쨷???앹꽦??DB ?앸퀎?먮? ?댄썑 ?대깽??而⑦뀓?ㅽ듃??遺숈씤??"""

        if solver_run_id is not None:
            self.solver_run_id = int(solver_run_id)
        if replay_track_id is not None:
            self.replay_track_id = int(replay_track_id)

    def event(
        self,
        *,
        stage: str,
        event: str,
        severity: str = "debug",
        source: Mapping[str, object] | None = None,
        **payload: object,
    ) -> None:
        """???대깽?몃? stage蹂?JSONL ?뚯씪??append?쒕떎."""

        if self._truncated:
            return
        row = {
            "schema_version": _SCHEMA_VERSION,
            "run_id": self.run_id,
            "project_slug": self.project_slug,
            "solver_run_id": self.solver_run_id,
            "replay_track_id": self.replay_track_id,
            "stage": stage,
            "event": event,
            "severity": severity,
            "timestamp": timezone.localtime().isoformat(),
            "source": dict(source or {}),
        }
        row.update(_json_safe(payload))
        self._write_event(row)

    def close(self) -> None:
        """summary.json??媛깆떊?쒕떎."""

        summary = {
            "schema_version": _SCHEMA_VERSION,
            "run_id": self.run_id,
            "project_slug": self.project_slug,
            "solver_run_id": self.solver_run_id,
            "replay_track_id": self.replay_track_id,
            "event_count": self._event_count,
            "byte_count": self._byte_count,
            "truncated": self._truncated,
            "stage_counts": dict(sorted(self._stage_counts.items())),
        }
        path = self.run_dir / "summary.json"
        path.write_text(
            json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2),
            encoding="utf-8",
        )

    def _stage_file_name(self, stage: str) -> str:
        stage_s = str(stage)
        for prefix, name in _STAGE_FILES:
            if stage_s == prefix or stage_s.startswith(prefix + "."):
                return name
        return "99_misc.jsonl"

    def _write_event(self, row: Mapping[str, object]) -> None:
        data = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        size = len(data.encode("utf-8"))
        if self._event_count >= self.max_events or self._byte_count + size > self.max_bytes:
            self._write_truncated_marker()
            return
        path = self.run_dir / self._stage_file_name(str(row.get("stage") or "misc"))
        with path.open("a", encoding="utf-8") as fh:
            fh.write(data)
        self._event_count += 1
        self._byte_count += size
        self._stage_counts[str(row.get("stage") or "misc")] += 1

    def _write_truncated_marker(self) -> None:
        if self._truncated:
            return
        self._truncated = True
        row = {
            "schema_version": _SCHEMA_VERSION,
            "run_id": self.run_id,
            "project_slug": self.project_slug,
            "solver_run_id": self.solver_run_id,
            "replay_track_id": self.replay_track_id,
            "stage": "request",
            "event": "trace_log_truncated",
            "severity": "warning",
            "timestamp": timezone.localtime().isoformat(),
            "source": {"module": __name__, "function": "_write_truncated_marker"},
            "diagnostic": {
                "reason": "trace_log_cap_reached",
                "event_count": self._event_count,
                "byte_count": self._byte_count,
                "max_events": self.max_events,
                "max_bytes": self.max_bytes,
            },
        }
        data = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        path = self.run_dir / self._stage_file_name("request")
        with path.open("a", encoding="utf-8") as fh:
            fh.write(data)
        self._event_count += 1
        self._byte_count += len(data.encode("utf-8"))
        self._stage_counts["request"] += 1


def create_asteroid_lab_trace_logger(
    *,
    project_slug: str | None = None,
    solver_run_id: int | None = None,
    replay_track_id: int | None = None,
    run_id: str | None = None,
) -> AsteroidLabTraceLogger | None:
    """settings flag媛 耳쒖졇 ?덉쓣 ?뚮쭔 ?뚯씪 logger瑜?留뚮뱺??"""

    if not _settings_bool("ASTEROID_LAB_TRACE_LOG_ENABLED", False):
        return None
    root = Path(settings.ASTEROID_LAB_TRACE_LOG_DIR)
    return AsteroidLabTraceLogger(
        run_id=run_id or _new_run_id(),
        root_dir=root,
        project_slug=project_slug,
        solver_run_id=solver_run_id,
        replay_track_id=replay_track_id,
        max_events=_settings_int("ASTEROID_LAB_TRACE_LOG_MAX_EVENTS", 5000),
        max_bytes=_settings_int("ASTEROID_LAB_TRACE_LOG_MAX_BYTES", 5_000_000),
        sample_limit=_settings_int("ASTEROID_LAB_TRACE_LOG_SAMPLE_LIMIT", 128),
    )


def record_decoded_snapshot_trace(
    trace_logger: AsteroidLabTraceLogger | None,
    snapshot: DecodedBlueprintSnapshotDTO,
    *,
    copy_code_hash: str,
    input_length: int,
) -> None:
    """decode 요약과 raw 좌표 projection sample을 기록한다."""

    if trace_logger is None:
        return
    cells = tuple(snapshot.cells)
    raw_pairs = [(c.x, c.y) for c in cells]
    dup_pairs = sum(n - 1 for n in Counter(raw_pairs).values() if n > 1)
    trace_logger.event(
        stage="decode.raw",
        event="raw_blueprint_loaded",
        severity="info",
        source={
            "module": "django_apps.asteroid_lab.services.cell_snapshot_service",
            "function": "build_decoded_blueprint_snapshot_from_input",
        },
        diagnostic={
            "copy_code_hash": copy_code_hash,
            "input_length": int(input_length),
            "building_count": len(cells),
            "cell_count": len({(c.x, c.y, c.layer) for c in cells}),
            "raw_bbox": dict(snapshot.bbox_json),
            "raw_x_zero_count": sum(1 for c in cells if int(c.x) == 0),
            "duplicate_raw_coord_count": dup_pairs,
            "coord_sample_limit": int(trace_logger.sample_limit),
            "coord_rows_logged": min(len(cells), int(trace_logger.sample_limit)),
            "cell_kind_counts": dict(snapshot.cell_kind_counts_json),
            "transport_kind_counts": dict(snapshot.transport_kind_counts_json),
        },
    )
    for cell in cells[: trace_logger.sample_limit]:
        reason = None
        if int(cell.x) == 0:
            reason = "raw_x_zero"
        trace_logger.event(
            stage="decode.coord",
            event="coord_recorded" if reason is None else "coord_diagnostic",
            source={
                "module": "django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot",
                "function": "build_decoded_blueprint_snapshot",
            },
            cell={
                "raw_x": cell.x,
                "raw_y": cell.y,
                "layer": cell.layer,
                "cell_kind": cell.cell_kind,
                "tile_type": cell.tile_type,
                "transport_kind": cell.transport_kind,
            },
            diagnostic={} if reason is None else {"reason": reason},
        )


def record_reconstruction_trace_events(
    trace_logger: AsteroidLabTraceLogger | None,
    trace_events: Sequence[object],
) -> None:
    """湲곗〈 reconstruction trace collector ?대깽?몃? JSONL?먮룄 蹂듭궗?쒕떎."""

    if trace_logger is None:
        return
    evs = tuple(trace_events)
    limit = int(trace_logger.sample_limit)
    critical_types = frozenset({"reconstruction_final", "reconstruction_skip"})
    if len(evs) <= limit:
        selected = list(evs)
    else:
        tail_crit_idx = [
            i
            for i, e in enumerate(evs)
            if str(getattr(e, "trace_event_type", "")) in critical_types and i >= limit
        ]
        if not tail_crit_idx:
            selected = list(evs[:limit])
        else:
            keep = max(0, limit - len(tail_crit_idx))
            selected = list(evs[:keep]) + [evs[i] for i in tail_crit_idx]

    for ev in selected:
        trace_logger.event(
            stage="reconstruction",
            event=str(getattr(ev, "trace_event_type", "trace_event")),
            source={
                "module": "django_apps.asteroid_lab.reconstruction.pipeline",
                "function": "run_topology_reconstruction",
            },
            diagnostic=dict(getattr(ev, "summary_json", {}) or {}),
            coord_count=len(getattr(ev, "coords", ()) or ()),
            coord_sample=list(tuple(getattr(ev, "coords", ()) or ())[: trace_logger.sample_limit]),
        )


__all__ = [
    "AsteroidLabTraceLogger",
    "create_asteroid_lab_trace_logger",
    "record_decoded_snapshot_trace",
    "record_reconstruction_trace_events",
]
