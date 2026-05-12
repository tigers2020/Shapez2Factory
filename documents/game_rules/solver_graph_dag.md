# 솔버 그래프: Shape는 트리가 아니라 DAG

## 이유

같은 **중간 도형**을 여러 연산 입력으로 재사용할 수 있다.

```text
RcRcRcRc
   ├─ rotate
   ├─ cut
   └─ swap
```

## 권장 그래프 형태

```text
Source -> Operation -> Intermediate -> Operation -> Target
```

중간 노드는 **식별 가능한 shape 코드**(또는 정규화 해시)를 가진다.

## 프로젝트 규칙과의 정렬

- 연산 출력은 다른 연산 입력에 **직접 접합**하지 않고 **중간 도형 노드**를 경유한다는 모델 규칙이 있다 ([architecture.mdc](../../.cursor/rules/architecture.mdc)).
- 이 문서의 DAG 개념과 충돌하지 않게, **시각화 그래프**와 **물리/도메인 그래프** 용어를 혼동하지 않는다.
