# 연산: Stacker / Combiner

## shapez 1 위키 계열 설명(요약)

- 두 입력 도형을 결합한다.
- 두 도형이 **같은 레이어 안에서 나란히** 들어갈 수 있으면 같은 층에서 **fuse/merge** 한다.
- 그렇지 않으면 한 도형을 다른 도형 **위에 쌓는다**.
- **최대 4층**까지만 유지되고, 초과 레이어는 **삭제**된다는 설명이 있다(게임판·패치 기준 재확인 권장).

## 솔버 서명(개념)

```text
stack(bottom, top) -> combined_shape
```

## Shapez 2 역할 이름 주의

Shapez 2 설명에서는 입력을 **bottom / top** 으로 두는 경우가 많다. 솔버·그래프 모델에서 **left/right** 로 표현하면 나중에 배선·수요 계산이 어긋날 수 있으므로 **bottom·top 용어를 우선**한다 ([shapez2_stacker_inputs.md](shapez2_stacker_inputs.md)).

## 예: 같은 층 병합(빈 분면 활용)

```text
A = Rc------     # NE만 있음
B = --Cu----     # SE만 있음

stack(A, B) -> RcCu----   # 같은 layer에서 merge 가능
```

## 예: 같은 분면 충돌 시 층 증가

```text
A = Rc------
B = Cu------

stack(A, B) -> Rc------:Cu------   # 같은 quadrant 충돌 → 위층
```

## 근거·신뢰도

- shapez 1 Stacker 위키: **중간~높음**.
- “초과 레이어 삭제” 등 세부는 **버전·게임**에 따라 다를 수 있어 테스트가 필요하다.
