# Shapez 2: Simulated Swapper

## 주장(참고용)

Simulated Swapper는 두 shape 신호를 입력받고, **두 도형의 west halves를 서로 교환한 결과**를 출력한다는 설명이 있다.

## 솔버 함수 형태(개념)

```python
swap_west_halves(a, b) -> (a_with_b_west, b_with_a_west)
```

## 최적화 관점

checker/stripe류 패턴은 **cut + stack 반복**보다 **swap 계열**이 더 짧은 경로일 수 있다.

예시 패턴(개념):

```text
RcRcRcRc + CuCuCuCu
회전/정렬 후 swap halves -> RcCuRcCu 계열
```

## 신뢰도

- 위키 **중간**. 실제 시뮬레이션 빌딩 동작은 게임 내 검증 권장.

## 관련

- [solver_search_strategy.md](solver_search_strategy.md)
