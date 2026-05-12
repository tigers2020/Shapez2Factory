# 핵심 추상화: 도형은 물리가 아니라 토큰 그리드

## 결론

shapez 계열의 도형 시스템은 **강체 물리 시뮬레이션**이라기보다, 다음과 같은 **격자형 기호 조작 시스템**으로 모델링하는 것이 맞다.

- 도형은 실제 rigid body가 아니라 **최대 4층 × 각 층 4분면**의 정규화된 토큰 구조다.
- 기계(빌딩)는 이 토큰을 변환하는 **순수 함수**에 가깝다.

## 솔버 관점의 한 줄 정의

```text
Shape = Layer[]
Layer = Quadrant[4]   # 이 프로젝트: SW, NW, NE, SE (= quadrants[0..3], shape_encoding.md)
Operation = (Shape, ...) -> (Shape, ...)
```

이 추상화를 깔면 **절단·회전·적층·색칠**은 모두 “배열·치환·병합·색만 교체”로 표현할 수 있다.

## 관련 문서

- [shape_encoding.md](shape_encoding.md)
- [solver_domain_model.md](solver_domain_model.md)
