#!/usr/bin/env python3
# ruff: noqa: E501
"""Replace legacy server-coordinate wording in documents/plans body text (PR-F)."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PLANS = REPO / "documents" / "plans"

# Order: longer / more specific first
REPLACEMENTS: list[tuple[str, str]] = [
    ("decoded_cell_to_server_coord", "island cell coord at decode boundary"),
    (
        "test_optimization_input_topology_graph_adjacency_matches_neighbors4_server",
        "test_optimization_input_topology_graph_adjacency_matches_neighbors4",
    ),
    (
        "test_candidate_generator_server_coord_contract",
        "test_candidate_generator_island_coord_contract",
    ),
    (
        "test_route_probe_respects_server_cardinal_adjacency",
        "test_route_probe_respects_island_cardinal_adjacency",
    ),
    (
        "``django_apps.shapez_asteroid.optimization`` 패키지와 post-inspection evolution 모듈은 "
        "``asteroid_lab.snapshots.server_coords`` 브리지를 직접 참조하지 않는다(어댑터·decode 경계만).",
        "dense ``server_coords`` 브리지는 **삭제됨** (PR-F). ``CoordFrame.ISLAND_RAW`` 정본.",
    ),
    (
        "asteroid_lab.snapshots.server_coords 의 raw→dense 브리지를 직접 참조하지 않는다"
        "(회귀: tests/unit/shapez_asteroid/test_import_boundaries.py).",
        "**removed** `server_coords` bridge (PR-F). AST: `test_coordinate_frame_ast_gate.py`.",
    ),
    (
        "raw X==0 열은 dense 가로 인덱스가 없으므로, decode·토폴로지 fill에서 "
        "server_x=0·server_y=Y-min_raw_y 로 명시한다.",
        "copy JSON ``X==0``은 island-local에서 유효; lab world map ``x==0`` 열 없음 — 프레임 혼동 금지.",
    ),
    (
        "**Sequence 12L (좌표 경계):** decode/cleanup/reconstruction이 붙인 **Server X/Y** 이후 "
        "알고리즘 계층에서는 raw blueprint ``X``/``Y``·``server_xy_for_raw_xy``를 쓰지 않는다.",
        "**Sequence 12L + PR-F:** decode/cleanup/reconstruction 이후 알고리즘은 **island-local** "
        "``(x,y)`` 만; dense server bridge **삭제**.",
    ),
    (
        "**Sequence 12L**(decode/fill·`decoded_cell_to_server_coord`에서 raw ``X==0``을 dense server로 "
        "명시; optimization 트리·post-inspection에서 ``server_coords`` 브리지 금지·정적 테스트)는 "
        "2026-05-17 반영.",
        "**Sequence 12L** (optimization 경계 AST) 2026-05-17. **PR-F:** island-local replay; "
        "`server_coords` 삭제.",
    ),
    ("### 3.3 Sequence 12L — Server 좌표 경계 (optimization 입력)", "### 3.3 Sequence 12L — Island-local coord boundary"),
    (
        "OptimizationInput 이후(및 동일 좌표를 쓰는 candidate·route·evolution·replay 기록)는 Server X/Y만 사용한다.",
        "OptimizationInput 이후는 `CoordFrame.ISLAND_RAW` island `(x, y)` only (PR-F).",
    ),
    (
        "OptimizationInput·TopologyGraph·RouteGoal.coord·candidate·probe·commit·validation·replay에 "
        "등장하는 모든 Coord = Server X / Server Y.",
        "OptimizationInput·TopologyGraph·RouteGoal·candidate·probe·commit·validation·replay의 "
        "모든 Coord = island-local (x, y).",
    ),
    (
        "Server 격자는 정수 밀집(…, -1, 0, 1, …)이며 카테인 이웃은 일반 ±1 규칙이다. "
        "본 최적화 플랜에는 다른 좌표 표현을 두지 않는다.",
        "Island map grid: integer (x, y) with `grid_contract.neighbors4`. Lab world map has no x==0 column.",
    ),
    ("``server_xy_for_raw_xy``", "dense bridge (removed PR-F)"),
    ("`server_xy_for_raw_xy`", "dense bridge (removed PR-F)"),
    ("server_xy_for_raw_xy", "dense bridge (removed PR-F)"),
    ("raw `X`/`Y`, `raw_to_server`, `server_to_raw`,", "copy JSON `X`/`Y`; forbidden re-conversion:"),
    ("이미 채워진 `server_x`/`server_y`만 소비하며", "island `Coord` only;"),
    ("Critical invariant: decode/import normalization이 Server X/Y를 만든 뒤에는", "Critical invariant: after decode/normalize to island grid,"),
    ("알고리즘 계층의 정본 좌표는 Server X/Y dense grid이다.", "canonical coords are island-local (PR-F)."),
    ("입력 구성은 Server X/Y만 사용한다.", "input uses island-local coords only."),
    ("all Coord satisfy Server dense grid contract", "all Coord satisfy island map grid contract"),
    (
        "- **Server Dense Grid 정본화**: 최적화 계층 전체는 `Coord = Server X/Y`만 사용한다. "
        "즉 `..., -1, 0, 1, ...` 밀집 좌표계를 정본으로 사용.",
        "- **Island map grid (historical note, PR-F):** was Server Dense; now `CoordFrame.ISLAND_RAW`.",
    ),
    ("neighbors4_server(coord: Coord)", "grid_contract.neighbors4(coord, frame)"),
    ("neighbors4_server(coord)", "grid_contract.neighbors4(coord, frame)"),
    ("neighbors4_server", "grid_contract.neighbors4"),
    ("Server X / Server Y", "island-local x / y"),
    ("(Server X, Server Y)", "(island x, island y)"),
    ("Server X/Y", "island-local (x, y)"),
    ("Server 밀집 격자", "island map grid"),
    ("Server 밀집 이웃", "island 4-neighbor"),
    ("Server 격자", "island map grid"),
    ("Server dense grid", "island map grid"),
    ("Server Dense Grid", "Island map grid"),
    ("Server 좌표", "Island-local"),
    ("Server 전용", "island map"),
    ("Server 밀집", "island map"),
    ("server `x == 0`", "copy JSON `X==0`"),
    ("server x=0", "copy JSON X==0"),
    ("server x==0", "copy JSON X==0"),
    ("dense server로 명시", "island-local로 처리"),
    ("dense server", "removed dense server"),
]


def is_banner_line(line: str) -> bool:
    s = line.strip()
    return s.startswith("> **Plans") or s.startswith("> **Canonical")


def transform_body(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    for line in lines:
        if is_banner_line(line):
            out.append(line)
            continue
        new_line = line
        for old, new in REPLACEMENTS:
            new_line = new_line.replace(old, new)
        out.append(new_line)
    return "".join(out)


def main() -> None:
    changed: list[str] = []
    for path in sorted(PLANS.rglob("*.md")):
        if path.name == "README.md":
            continue
        original = path.read_text(encoding="utf-8")
        updated = transform_body(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed.append(str(path.relative_to(PLANS)))
    print(f"Updated {len(changed)} file(s):")
    for c in changed:
        print(f"  - documents/plans/{c}")


if __name__ == "__main__":
    main()
