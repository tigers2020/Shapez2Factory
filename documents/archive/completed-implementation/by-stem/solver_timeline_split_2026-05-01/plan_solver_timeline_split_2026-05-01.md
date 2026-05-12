# Plan: solver_timeline split (2026-05-01)

관련 리서치: [documents/research_solver_timeline_split_2026-05-01.md](./research_solver_timeline_split_2026-05-01.md)

원본 요청 요약: [django_apps/web/static/web/js/solver_timeline.js](../../../../../django_apps/web/static/web/js/solver_timeline.js) 를 책임 단위 ES 모듈로 분리하되, 진입점 파일명, 자동 초기화, DOM `data-*` 계약, 서버 응답 shape 는 유지한다.

## 구현 접근

1. 신규 폴더 [django_apps/web/static/web/js/solver_timeline/](../../../../../django_apps/web/static/web/js/solver_timeline/) 를 만든다.
2. 상수와 공통 DOM 유틸을 먼저 추출한 뒤, 그래프 마크업과 viewport 로직을 분리한다.
3. 선택 상세패널과 graph mount wiring 을 한 모듈로 정리하고, throughput summary 와 요청 orchestration 을 따로 분리한다.
4. 마지막에 [solver_timeline.js](../../../../../django_apps/web/static/web/js/solver_timeline.js) 를 thin entry 로 축소한다.

## 호환성 기준

- `solver.html` 의 `<script type="module" src="{% static 'web/js/solver_timeline.js' %}"></script>` 는 수정하지 않는다.
- `document.querySelectorAll("[data-solver-timeline]")` 기반 자동 초기화는 유지한다.
- 기존 `code`, `target_count` 요청 payload 와 `ok`, `warnings`, `graph`, `target_count`, `base_demands` 응답 사용 방식은 그대로 둔다.
- 현재 더티 워크트리에서 이미 들어간 quantity badge, throughput summary, `target_count` 반영 동작은 기능 회귀 없이 유지한다.

## 검증

- `pytest tests/integration/web/test_web_smoke.py` 실행.
- 가능하면 solver 페이지 로딩과 타임라인 진입 경로를 수동 확인한다.
- 실패가 나면 이번 JS 리팩토링 회귀인지, 기존 backend import 문제인지 분리해서 보고한다.
