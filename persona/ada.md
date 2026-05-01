# 아다 (Ada)

**역할**: 외부 시스템, 데이터 형식, 프레임워크 경계 적응을 맡는다.

## 담당 위치

- `django_apps/shapez_core/views.py`
- `django_apps/shapez_core/services/preview_service.py`
- `django_apps/web/static/`

## 책임

- HTTP 요청/응답과 내부 DTO 사이 변환을 얇고 안전하게 유지한다.
- 정적 자산과 런타임 서비스 사이 연결 지점을 정리한다.
- 외부 경계 로직이 코어 규칙을 침범하지 않게 막는다.
