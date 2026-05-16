---
status: ACTIVE
owner: web-backend
last_reviewed: 2026-05-15
supersedes: []
superseded_by:
related_epics: []
---

# Asteroid Mining Lab: URL에서 copy string 제거

## 목표

- 거대한 Shapez2 blueprint copy string을 **GET 쿼리 `?code=`**에서 제거한다.
- **POST**로 제출 후 **PRG(302)**로 `AsteroidProject.slug` 기반 짧은 URL로 이동한다.
- 동일 내용 재제출 시 **`AsteroidMapInput.content_sha256`**로 기존 프로젝트를 찾아 dedupe한다.

## URL 계약

| 메서드 | 경로 | 동작 |
|--------|------|------|
| GET | `/asteroid-miner-layout/` | 빈 랩(쿼리 `code` 무시) |
| POST | `/asteroid-miner-layout/projects/` | `copy_code` 저장·dedupe 후 `/asteroid-miner-layout/p/<slug>/`로 리다이렉트 |
| GET | `/asteroid-miner-layout/p/<slug>/` | 해당 프로젝트 최신 `AsteroidMapInput.copy_code`로 랩 렌더 |

## Dedupe

- 해시: UTF-8 바이트 기준 `sha256` — `django_apps.asteroid_lab.services.input_service.content_sha256_for_copy_code`와 `create_copy_code_map_input`이 동일 규칙 사용.
- 제출 전 **앞뒤 공백 strip** 후 해시·저장(빈 문자열이면 베이스 URL로 리다이렉트).

## GET `?code=` 호환

- **브레이킹**: 대형 payload 북마크는 URL 한계로 원래 복구 불가. 베이스 GET의 `code`는 읽지 않음.

## 테스트 범위

- 통합: POST → 302 Location → GET 본문에 `copy_code` 반영.
- 단위: 동일 문자열 두 번 제출 시 프로젝트 수 증가 없음·동일 slug.

## 구현 참조

- 뷰: `django_apps/web/views/public_pages.py`
- URL: `django_apps/web/urls.py`
- 서비스: `django_apps/asteroid_lab/services/project_service.py`
