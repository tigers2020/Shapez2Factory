"""Recipe graph editor: schema version and engine-backed operation allow-list."""

from __future__ import annotations

from django_apps.shapez_solver.domain.operations import OperationType

# graph_document JSON 최상위 schema_version과 동기화한다.
RECIPE_GRAPH_SCHEMA_VERSION = 1

# ``react_flow_initial`` / ``domain_graph_to_react_flow`` JSON의 ``version`` 필드.
# ``recipe_graph_react_flow_adapter`` 가 읽고 직렬화한다.
REACT_FLOW_GRAPH_PAYLOAD_VERSION = 1

# graph_document 자동 생성 노드 좌표: ``frontend/graph_layout/src/metrics.ts`` 의
# ``SOLVER_LAYOUT_METRICS`` (COLUMN_GAP / ROW_GAP) 및 빌드 산출물
# ``solver_graph_layout.js`` 와 맞춘다
# (브라우저에서 카드가 겹치지 않게)
RECIPE_GRAPH_AUTO_OUTPUT_X_OFFSET = 280.0
RECIPE_GRAPH_AUTO_OUTPUT_COL_SPACING = 270
RECIPE_GRAPH_AUTO_OUTPUT_ROW_SPACING = 356
RECIPE_GRAPH_AUTO_OUTPUT_GRID_COLUMNS = 2

# 매크로 그래프 shape 소스 수량 기본값 — 프로젝트 규약 고정(임의 변경 금지).
# 프론트 ``recipe_graph_editor/src/EditorFoundation/constants.ts`` 와 동일 수식 유지.
RECIPE_GRAPH_DEFAULT_SOURCE_QUANTITY_MATERIAL = 480 * 12
RECIPE_GRAPH_DEFAULT_SOURCE_QUANTITY_FLUID = 28000 * 12

RECIPE_GRAPH_ENGINE_OPERATIONS: frozenset[str] = frozenset(
    {
        OperationType.ROTATE_CW.value,
        OperationType.ROTATE_CCW.value,
        OperationType.ROTATE_180.value,
        OperationType.CUTTER.value,
        OperationType.HALF_DESTROYER.value,
        OperationType.SPLITTER.value,
        OperationType.PIN_PUSHER.value,
        OperationType.SWAPPER.value,
        OperationType.STACKER.value,
        OperationType.MERGE.value,
        OperationType.PAINTER.value,
        OperationType.COLOR_MIXER.value,
        OperationType.CRYSTAL_GENERATOR.value,
    }
)

__all__ = [
    "REACT_FLOW_GRAPH_PAYLOAD_VERSION",
    "RECIPE_GRAPH_AUTO_OUTPUT_COL_SPACING",
    "RECIPE_GRAPH_AUTO_OUTPUT_GRID_COLUMNS",
    "RECIPE_GRAPH_AUTO_OUTPUT_ROW_SPACING",
    "RECIPE_GRAPH_AUTO_OUTPUT_X_OFFSET",
    "RECIPE_GRAPH_DEFAULT_SOURCE_QUANTITY_FLUID",
    "RECIPE_GRAPH_DEFAULT_SOURCE_QUANTITY_MATERIAL",
    "RECIPE_GRAPH_ENGINE_OPERATIONS",
    "RECIPE_GRAPH_SCHEMA_VERSION",
]
