# 연산: Color Mixer (액체 혼합)

## 일반 규칙(개념)

색상 액체를 조합해 새 색을 만든다. 예:

```text
red + green = yellow
red + blue = magenta
green + blue = cyan
red + green + blue = white
```

## 솔버 설계 권장

도형의 레이어·분면 연산과 섞지 말고 **paint resource dependency** 로 분리하는 편이 단순하다.

- 도형 변환 함수: `Shape -> Shape`
- 색 액체 파이프: **어떤 기본 색·중간 색이 몇 단위 필요한지** 별도 그래프/수량 모델

이렇게 나누면 “형태 솔버”와 “잉크 공급 솔버”의 경계가 명확해진다.

## 근거·신뢰도

- 색 혼합 표는 커뮤니티·가이드에서 흔히 인용되지만, **정확한 게임 내 레시피**는 플레이·데이터 추출로 검증하는 것이 안전하다.
