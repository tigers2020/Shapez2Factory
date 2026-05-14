"""Django ``settings``에 노출되는 SHAPEZ_* / SOLVER_GRAPH_* 런타임 플래그.

``config.settings``가 ``load_dotenv``로 ``.env``를 먼저 적용한 뒤 이 모듈을 import한다.
이 모듈은 ``load_dotenv``를 호출하지 않는다.
"""

from __future__ import annotations

import os
from pathlib import Path

# 프로젝트 루트 (``config/settings.py``의 ``BASE_DIR``와 동일 계산식).
_BASE_DIR = Path(__file__).resolve().parent.parent

# --- SHAPEZ_COPY_* ---
# ``SHAPEZ_COPY_DEBUG_DIR``: copy-preview 성공 시 암호화 코드·디코드 JSON 덤프 경로.
# 기본 빈 문자열(OFF).
SHAPEZ_COPY_DEBUG_DIR = (os.environ.get("SHAPEZ_COPY_DEBUG_DIR", "") or "").strip()

# --- SHAPEZ_MINING_* (env: 1/true/yes/on → True) ---
# 기본 OFF. 스크래치 수송·맵 행·routing_state 불일치 디버깅 시 켠다.
_truthy_env = frozenset({"1", "true", "yes", "on"})

# --- SHAPEZ_DEV_* (copy-preview 개발용 MD 보고서; 기본 OFF) ---
SHAPEZ_DEV_ASTEROID_STEP_REPORT = (
    os.environ.get("SHAPEZ_DEV_ASTEROID_STEP_REPORT", "").strip().lower() in _truthy_env
)
# 비우면 ``BASE_DIR / "var" / "asteroid_optimizer_dev_report.md"`` (뷰에서 조합).
SHAPEZ_DEV_ASTEROID_REPORT_MD = (os.environ.get("SHAPEZ_DEV_ASTEROID_REPORT_MD", "") or "").strip()
SHAPEZ_MINING_ASSERT_SCRATCH_TRANSPORT_SUBSET = (
    os.environ.get(
        "SHAPEZ_MINING_ASSERT_SCRATCH_TRANSPORT_SUBSET",
        "",
    )
    .strip()
    .lower()
    in _truthy_env
)
# ``build_solver_timeline`` 반환 전 STEP9: 보호 회랑과 최종 맵 벨트 일치 assert. 기본 OFF.
SHAPEZ_MINING_ASSERT_STEP9_ROUTING_STATE = (
    os.environ.get("SHAPEZ_MINING_ASSERT_STEP9_ROUTING_STATE", "").strip().lower() in _truthy_env
)
# Pass12 보존 채굴기: 완화된 스텁·회전 복구. 기본 OFF.
SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY = (
    os.environ.get("SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY", "").strip().lower() in _truthy_env
)
# Pass12: 스텁 추론 → 동종 trunk BFS·NEAR_TRANSPORT 지연 큐. 기본 ON. 0/false/no/off 끔.
# NDJSON ``pass12_stub_route_recovery_disabled_by_flag=true`` ↔ 이 값이 False일 때.
SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY = os.environ.get(
    "SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY", "true"
).strip().lower() not in {"0", "false", "no", "off"}
# Pass2 내부 mineable void 채움(existing_fluid_layout). 기본 ON.
# 0/false/no/off 시 레거시(양 루프 스킵)에 가깝게.
SHAPEZ_MINING_PASS2_FLUID_INTERNAL_FILL_ENABLED = os.environ.get(
    "SHAPEZ_MINING_PASS2_FLUID_INTERNAL_FILL_ENABLED", "true"
).strip().lower() not in {"0", "false", "no", "off"}

# ``SHAPEZ_MINING_LAYOUT_ENGINE``: 예약. ``copy_preview``는 항상 v2 타임라인·분석.
# 이 값으로 분기하지 않음. 배포·문서 호환을 위해 env 키는 유지한다. 기본 ``v2``.
SHAPEZ_MINING_LAYOUT_ENGINE = os.environ.get("SHAPEZ_MINING_LAYOUT_ENGINE", "v2").strip().lower()
# ``asteroid_mining_layout`` 폴더가 없고 ``asteroid_mining_layout.zip``만 있을 때 copy-preview가
# ``build_solver_timeline``을 쓰기 전에 zip을 sibling 폴더로 한 번 푼다. 읽기 전용 배포에서는 끈다.
SHAPEZ_MINING_LAYOUT_ZIP_AUTO_EXTRACT = os.environ.get(
    "SHAPEZ_MINING_LAYOUT_ZIP_AUTO_EXTRACT", "true"
).strip().lower() not in {"0", "false", "no", "off"}

# --- SOLVER_GRAPH_PREVIEW_* ---
# ``SOLVER_GRAPH_PREVIEW_RENDERER``: playwright_png | noop 등. 기본 playwright_png.
SOLVER_GRAPH_PREVIEW_RENDERER = (
    os.environ.get("SOLVER_GRAPH_PREVIEW_RENDERER", "playwright_png").strip().lower()
)
# ``SOLVER_GRAPH_PREVIEW_STORAGE``: filesystem | database. 기본 filesystem.
SOLVER_GRAPH_PREVIEW_STORAGE = (
    os.environ.get("SOLVER_GRAPH_PREVIEW_STORAGE", "filesystem").strip().lower()
)
SOLVER_GRAPH_PREVIEW_CACHE_DIR = _BASE_DIR / ".graph_preview_cache"

__all__ = [
    "SHAPEZ_COPY_DEBUG_DIR",
    "SHAPEZ_DEV_ASTEROID_REPORT_MD",
    "SHAPEZ_DEV_ASTEROID_STEP_REPORT",
    "SHAPEZ_MINING_ASSERT_SCRATCH_TRANSPORT_SUBSET",
    "SHAPEZ_MINING_ASSERT_STEP9_ROUTING_STATE",
    "SHAPEZ_MINING_LAYOUT_ENGINE",
    "SHAPEZ_MINING_LAYOUT_ZIP_AUTO_EXTRACT",
    "SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY",
    "SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY",
    "SHAPEZ_MINING_PASS2_FLUID_INTERNAL_FILL_ENABLED",
    "SOLVER_GRAPH_PREVIEW_RENDERER",
    "SOLVER_GRAPH_PREVIEW_STORAGE",
    "SOLVER_GRAPH_PREVIEW_CACHE_DIR",
]
