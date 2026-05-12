# 매뉴얼: Database · 마이그레이션

## 전제

스키마 변경·데이터 마이그레이션은 [`AGENTS.md`](../../../AGENTS.md)의 **명시적 승인 없이 하지 말 것**에 해당할 수 있다. 프로젝트 플랜·승인 게이트를 먼저 확인한다.

## Django 모델

앱별 `models.py` 및 마이그레이션은 각 Django 앱 디렉터리 규칙을 따른다. 레이어 위반 import를 두지 않는다 ([`architecture.mdc`](../../../.cursor/rules/architecture.mdc)).

## 작업 후

- 마이그레이션 파일 생성이 포함되면 **검토 대상**임을 전제로 한다.
- 통합/스테이징 시드·데이터 이슈를 [`documents/ai/context_notes.md`](../../context_notes.md)에 남긴다.

## 관련

- Django 앱 구조: [`django.md`](django.md)
