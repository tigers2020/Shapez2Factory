# 솔버 수량(quantity): 노드만이 아니라 엣지·플랜에도

## 흔한 불일치 증상

```text
요약(demand summary)은 1:1:2인데 그래프는 1:1:1
```

## 대표 원인

1. 소스 노드 수량만 바꾸고 **엣지 수요**를 갱신하지 않음
2. 연산 출력 **다중성(multiplicity)** 이 그래프에 반영되지 않음
3. `target_count` 등이 **물질화 그래프 생성 단계**에서 1로 리셋됨
4. **shape identity** 집계와 **수량 집계**가 분리되지 않음

## 권장 모델 스케치

```python
# 개념 예시 — 실제 필드명은 프로젝트 DTO에 맞출 것
Node:
    shape_code
    node_type
    display_quantity

Edge:
    quantity
    throughput   # 또는 시간당 처리량 등
    role: input | output | top | bottom | east | west   # 빌딩·포트 의미
```

## 관련

- 그래프 UI와 요약 수치 혼동 방지: [documents/ai/manuals/graph_ui.md](../ai/manuals/graph_ui.md)
- [solver_graph_dag.md](solver_graph_dag.md)
