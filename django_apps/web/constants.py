"""웹 레이어 전용 상수(페이지 기본값·JSON API 메시지·프리뷰 타임아웃 등)."""

from __future__ import annotations

# 홈 페이지 기본 shape 코드 입력값
HOME_INITIAL_SHAPE_CODE = "CuRuSuWu"

# 데모 페이지 고정 샘플 목록 (파싱 행 데모용)
DEMO_FIXED_SAMPLE_CODES: tuple[str, ...] = (
    "SuSuSuSu",
    "[RuRuRuRu, WrCrRgSy]",
    "RuRuRuRu:WrCrRgSy",
    "--RuRuRu",
    "CuCuCuCu",
    "P-P-P-P-",
    "XuXuXuXu",
    "PrPrPrPr",
)

# JSON 본문 파싱 실패 시 API ``error`` 필드
JSON_API_ERROR_INVALID = "invalid JSON"

# 그래프 PNG 프리렌더(node subprocess) 최대 대기 시간(초)
WEB_GRAPH_PREVIEW_TIMEOUT_SECONDS = 45

__all__ = [
    "DEMO_FIXED_SAMPLE_CODES",
    "HOME_INITIAL_SHAPE_CODE",
    "JSON_API_ERROR_INVALID",
    "WEB_GRAPH_PREVIEW_TIMEOUT_SECONDS",
]
