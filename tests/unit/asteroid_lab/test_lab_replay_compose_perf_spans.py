"""Contract: lab-replay cache-miss compose path exposes perf_span phase names (#176)."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PUBLIC_PAGES = REPO / "django_apps" / "web" / "views" / "public_pages.py"
TIMELINE_PAYLOAD = (
    REPO / "django_apps" / "asteroid_lab" / "services" / "lab_replay_timeline_payload.py"
)
VIEWER_COMPOSE = (
    REPO / "django_apps" / "asteroid_lab" / "services" / "artifact_replay_viewer_compose.py"
)

_LAB_REPLAY_GET_SPANS = (
    "replay_cache_lookup_ms",
    "replay_cache_miss_compose_ms",
    "replay_compose_entry_ms",
    "replay_cache_persist_ms",
    "replay_response_serialize_ms",
)

_COMPOSE_CHAIN_SPANS = (
    "compose_artifact_frames_ms",
    "replay_timeline_assembly_ms",
    "replay_metrics_build_ms",
    "artifact_manifest_load_ms",
    "replay_core_parse_ms",
)


def test_lab_replay_get_handler_declares_compose_perf_spans() -> None:
    block = PUBLIC_PAGES.read_text(encoding="utf-8")
    start = block.index("def asteroid_miner_layout_project_solver_run_lab_replay")
    end = block.index("@require_POST", start)
    handler = block[start:end]
    for span in _LAB_REPLAY_GET_SPANS:
        assert f'perf_span("{span}")' in handler


def test_compose_chain_declares_nested_perf_spans() -> None:
    sources = (
        TIMELINE_PAYLOAD.read_text(encoding="utf-8"),
        VIEWER_COMPOSE.read_text(encoding="utf-8"),
    )
    joined = "\n".join(sources)
    for span in _COMPOSE_CHAIN_SPANS:
        assert f'perf_span("{span}")' in joined
