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
# ``SHAPEZ_COPY_DEBUG_DIR``: copy 디버그 덤프 디렉터리(비어 있으면 OFF).
# 상대 경로면 프로젝트 ``BASE_DIR`` 기준(``var/...`` 권장). 절대 경로는 그대로 사용.
_copy_debug_raw = (os.environ.get("SHAPEZ_COPY_DEBUG_DIR", "") or "").strip()
if not _copy_debug_raw:
    SHAPEZ_COPY_DEBUG_DIR = ""
else:
    _p = Path(_copy_debug_raw)
    SHAPEZ_COPY_DEBUG_DIR = str(_p if _p.is_absolute() else (_BASE_DIR / _p))

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
    "SOLVER_GRAPH_PREVIEW_RENDERER",
    "SOLVER_GRAPH_PREVIEW_STORAGE",
    "SOLVER_GRAPH_PREVIEW_CACHE_DIR",
]
