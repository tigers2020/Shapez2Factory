# materialized graph render parity 리서치
날짜: 2026-05-02

## 증상

사용자 확인 기준:

- solver 페이지 본문 문구는 최신으로 보인다.
- 하지만 materialized graph 토글에서는 예전 곡선 edge 와 카드 스크롤이 그대로 보인다.

## 코드 기준 사실

- raw graph 와 materialized graph 는 모두 `timeline_request.js -> mountGraph() -> renderSolverGraph()` 동일 렌더 경로를 탄다.
- 별도의 materialized 전용 graph renderer 는 없다.
- 따라서 코드만 놓고 보면 raw/materialized 표시 차이가 발생할 구조는 아니다.

## 가능한 원인

1. **브라우저 모듈 캐시**
   - 템플릿 HTML 은 갱신되지만 `solver_timeline.js` 와 그 하위 module import 가 같은 URL 이라 브라우저가 이전 JS 를 계속 사용할 수 있다.
   - 이 경우 "문구는 최신, 그래프만 예전" 증상과 정확히 맞는다.

2. **materialized payload 렌더 회귀**
   - generic graph sample 은 새 마크업을 통과해도, 실제 `materialized_graph` 구조에서는 예외 경로가 있을 수 있다.
   - 이를 막으려면 실제 API payload 를 가져와 `renderSolverGraph(materialized_graph)` 로 검증하는 테스트가 필요하다.

## 대응 방향

- 그래프 엔트리 script 와 graph 관련 nested module import 에 version query 를 붙여 브라우저 캐시를 확실히 분리한다.
- materialized graph API payload 를 실제로 `renderSolverGraph()` 에 넣어 current markup 이 적용되는지 테스트를 추가한다.

## 결론

이번 보강은 backend graph semantics 변경이 아니라:

- graph UI module cache busting
- materialized graph rendering parity test 추가

두 가지로 정리하는 것이 가장 안전하다.
