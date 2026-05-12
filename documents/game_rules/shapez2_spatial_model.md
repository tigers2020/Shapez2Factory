# Shapez 2: 공간 모델 vs 도형 모델

## 요약

- **공장 배치·물류**는 3D/플랫폼 기반으로 바뀔 수 있다.
- 그러나 **도형 자체**는 여전히 **layer / part(분면 단위)** 구조로 설명되는 경우가 많다.

## 솔버 내부 모델에 대한 시사

솔버가 다루는 핵심은 “벨트가 어느 층을 오가나”보다 우선 **도형 코드의 불변 구조**:

```python
Shape = tuple[Layer, ...]   # 아래층 → 위층
Layer = tuple[Quadrant, Quadrant, Quadrant, Quadrant]
```

quadrant 각각은 `Part | Empty` 로 두는 패턴이 문서화·테스트에 유리하다 ([solver_domain_model.md](solver_domain_model.md)).

## 근거·신뢰도

- wiki.gg “Shapes” 등: **중간~높음** (교차 검증 권장).
