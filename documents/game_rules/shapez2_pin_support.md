# Shapez 2: Pin과 부유 도형·지지(support)

## Steam 개발 로그 요지(신뢰도: 높음 쪽)

- Shapez 2는 **floating shape** 를 그대로 허용하지 않는 방향으로 설계되었다는 설명이 있다.
- **Pin** 관련: Pin Pusher가 한 quadrant 전체를 제거하고 `P-` 같은 **pin part** 로 대체한다는 식의 소개가 있다(정확한 문자 코드는 게임 데이터 기준).

## 솔버 의미(개념)

```text
일반 part 없이 위층만 떠 있으면 invalid
Pin이 support 역할을 하면 valid
```

즉 Shapez 2 솔버에는 **지지(support) 검증** 레이어가 필요할 수 있다.

## 개략 알고리즘 스케치(확정 아님)

```python
is_supported(part at layer L, quadrant Q):
    return exists physical_or_pin_part at layer L-1, same quadrant
        or connected_to_supported_adjacent_part(...)
```

**정확한 인접·낙하 규칙은 추가 검증 필요**라고 적는 것이 정직하다.

## 관련

- [solver_domain_model.md](solver_domain_model.md) 의 `pin` part
