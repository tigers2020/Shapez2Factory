"""copy-preview 개발용: 타임라인·리플레이 요약 Markdown (``var/`` 덮어쓰기).

솔버 입력으로 사용하지 않는다. 레거시 v1(``asteroid_mining_layout`` / zip 추출본)의
``solver_trace.trace_event`` / ``debug_log_event`` NDJSON은 별도 계약이며,
zip 동봉본 갱신 시 ``documents/Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md``
단계와 경계 로깅을 재점검한다.
"""

from __future__ import annotations

import logging
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SOLVER_ENV_PREFIXES = ("SHAPEZ_SOLVER_", "SHAPEZ_DEV_ASTEROID_")


def resolve_dev_report_md_path(*, base_dir: Path, override: str) -> Path:
    raw = (override or "").strip()
    if raw:
        p = Path(raw)
        return p if p.is_absolute() else (base_dir / p)
    return base_dir / "var" / "asteroid_optimizer_dev_report.md"


def _format_dev_report_header_lines(
    *,
    now: str,
    preview_schema_version: int | None,
    mining_layout_engine: str | None,
    include_solver_overlay: bool,
    include_solver_replay: bool,
    solver_layout_package_unavailable: bool,
    code_fingerprint: str | None,
) -> list[str]:
    lines = [
        "# Asteroid optimizer — dev step / replay report",
        "",
        f"- **generated_utc**: `{now}`",
        f"- **preview_schema_version**: `{preview_schema_version}`",
        f"- **mining_layout_engine**: `{mining_layout_engine}`",
        f"- **include_solver_overlay**: `{include_solver_overlay}`",
        f"- **include_solver_replay**: `{include_solver_replay}`",
        f"- **solver_layout_package_unavailable**: `{solver_layout_package_unavailable}`",
    ]
    if code_fingerprint:
        lines.append(f"- **code_sha256_prefix**: `{code_fingerprint}`")
    lines.append("")
    return lines


def _format_json_code_block_section(*, heading: str, payload: Any) -> list[str]:
    return [
        heading,
        "",
        "```json",
        _short_json(payload),
        "```",
        "",
    ]


def _format_map_timeline_section(map_timeline: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Map timeline (`map_timeline`)",
        "",
        "| idx | id | entry_count | phase | preview_placeholder |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for i, fr in enumerate(map_timeline):
        if not isinstance(fr, dict):
            lines.append(f"| {i} | (non-dict) | | | |")
            continue
        fid = fr.get("id", "")
        summ_raw = fr.get("summary")
        summ: dict[str, Any] = summ_raw if isinstance(summ_raw, dict) else {}
        ec = summ.get("entry_count", "")
        ph = summ.get("phase", "")
        pph = summ.get("preview_placeholder", "")
        lines.append(f"| {i} | `{fid}` | {ec} | `{ph}` | `{pph}` |")
    lines.append("")
    return lines


def _format_solver_timeline_section(solver_timeline: list[dict[str, Any]] | None) -> list[str]:
    lines = [
        "## Solver timeline (`solver_timeline`)",
        "",
    ]
    if not solver_timeline:
        lines.append("_(absent or empty)_")
        lines.append("")
        return lines
    lines.append("| idx | id |")
    lines.append("| --- | --- |")
    for i, fr in enumerate(solver_timeline):
        if isinstance(fr, dict) and isinstance(fr.get("id"), str):
            lines.append(f"| {i} | `{fr['id']}` |")
        else:
            lines.append(f"| {i} | _(invalid row)_ |")
    lines.append("")
    return lines


def _solver_replay_event_kinds_table(events: list[Any]) -> list[str]:
    kinds = Counter(
        str(e["kind"]) for e in events if isinstance(e, dict) and e.get("kind") is not None
    )
    if not kinds:
        return []
    out = [
        "",
        "### Event kinds (count)",
        "",
        "| kind | count |",
        "| --- | ---: |",
    ]
    for k, c in kinds.most_common():
        out.append(f"| `{k}` | {c} |")
    return out


def _format_solver_replay_section(solver_replay: dict[str, Any] | None) -> list[str]:
    lines = ["## Solver replay (`solver_replay`)", ""]
    if not isinstance(solver_replay, dict):
        lines.append("_(absent)_")
        lines.append("")
        return lines
    ev = solver_replay.get("events")
    contract = solver_replay.get("contractVersion", solver_replay.get("contract_version"))
    lines.append(f"- **contractVersion**: `{contract}`")
    if not isinstance(ev, list):
        lines.append("- **events**: _(missing or not a list)_")
        lines.append("")
        return lines
    lines.append(f"- **events_len**: {len(ev)}")
    lines.extend(_solver_replay_event_kinds_table(ev))
    lines.append("")
    return lines


def _sorted_matching_env_rows() -> list[tuple[str, str]]:
    return sorted(
        (k, v)
        for k, v in os.environ.items()
        if any(k.startswith(p) for p in _SOLVER_ENV_PREFIXES) and v != ""
    )


def _format_process_env_section() -> list[str]:
    lines = [
        "## Process env (NDJSON / dev; non-secret keys only)",
        "",
    ]
    rows = _sorted_matching_env_rows()
    if not rows:
        lines.append("_(no matching env vars set)_")
        lines.append("")
        return lines
    lines.append("| variable | value |")
    lines.append("| --- | --- |")
    for k, v in rows:
        lines.append(f"| `{k}` | `{v}` |")
    lines.append("")
    return lines


def format_asteroid_optimizer_dev_report_md(
    *,
    map_timeline: list[dict[str, Any]],
    root_summary: dict[str, Any],
    reconstruction_summary: dict[str, Any] | None,
    mining_layout_engine: str | None,
    include_solver_overlay: bool,
    include_solver_replay: bool,
    solver_timeline: list[dict[str, Any]] | None,
    solver_replay: dict[str, Any] | None,
    solver_layout_package_unavailable: bool,
    mining_layout_runtime_flags: dict[str, Any] | None,
    preview_schema_version: int | None,
    code_fingerprint: str | None,
) -> str:
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = []
    lines.extend(
        _format_dev_report_header_lines(
            now=now,
            preview_schema_version=preview_schema_version,
            mining_layout_engine=mining_layout_engine,
            include_solver_overlay=include_solver_overlay,
            include_solver_replay=include_solver_replay,
            solver_layout_package_unavailable=solver_layout_package_unavailable,
            code_fingerprint=code_fingerprint,
        )
    )
    lines.extend(
        _format_json_code_block_section(
            heading="## Root summary (last frame)",
            payload=root_summary,
        )
    )
    if reconstruction_summary is not None:
        lines.extend(
            _format_json_code_block_section(
                heading="## Reconstruction summary",
                payload=reconstruction_summary,
            )
        )
    if mining_layout_runtime_flags:
        lines.extend(
            _format_json_code_block_section(
                heading="## Mining layout runtime flags (response)",
                payload=mining_layout_runtime_flags,
            )
        )
    lines.extend(_format_map_timeline_section(map_timeline))
    lines.extend(_format_solver_timeline_section(solver_timeline))
    lines.extend(_format_solver_replay_section(solver_replay))
    lines.extend(_format_process_env_section())
    return "\n".join(lines) + "\n"


def write_asteroid_optimizer_dev_report(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    except OSError as exc:
        logger.warning("asteroid dev report: write failed path=%s: %s", path, exc)


def _short_json(obj: Any, *, limit: int = 8000) -> str:
    import json

    raw = json.dumps(obj, indent=2, ensure_ascii=False, default=str)
    if len(raw) > limit:
        return raw[: limit - 20] + "\n…(truncated)…\n"
    return raw


__all__ = [
    "format_asteroid_optimizer_dev_report_md",
    "resolve_dev_report_md_path",
    "write_asteroid_optimizer_dev_report",
]
