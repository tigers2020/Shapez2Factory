"""Recipe graph editor: schema version and engine-backed operation allow-list."""

from __future__ import annotations

from django_apps.shapez_solver.domain.operations import OperationType

# graph_document JSON 최상위 schema_version과 동기화한다.
RECIPE_GRAPH_SCHEMA_VERSION = 1

# graph_document 자동 생성 노드 좌표: ``solver_graph_layout.js`` 의 COLUMN_GAP / ROW_GAP 와 맞춘다
# (브라우저에서 카드가 겹치지 않게)
RECIPE_GRAPH_AUTO_OUTPUT_X_OFFSET = 280.0
RECIPE_GRAPH_AUTO_OUTPUT_COL_SPACING = 270
RECIPE_GRAPH_AUTO_OUTPUT_ROW_SPACING = 356
RECIPE_GRAPH_AUTO_OUTPUT_GRID_COLUMNS = 2
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
        OperationType.PAINTER.value,
        OperationType.COLOR_MIXER.value,
        OperationType.CRYSTAL_GENERATOR.value,
    }
)

__all__ = [
    "RECIPE_GRAPH_AUTO_OUTPUT_COL_SPACING",
    "RECIPE_GRAPH_AUTO_OUTPUT_GRID_COLUMNS",
    "RECIPE_GRAPH_AUTO_OUTPUT_ROW_SPACING",
    "RECIPE_GRAPH_AUTO_OUTPUT_X_OFFSET",
    "RECIPE_GRAPH_ENGINE_OPERATIONS",
    "RECIPE_GRAPH_SCHEMA_VERSION",
]
