# UI UX Pro Max — Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox syntax.
>
> **Spec:** [`documents/superpowers/specs/2026-06-13-ui-ux-pro-max-integration.md`](../specs/2026-06-13-ui-ux-pro-max-integration.md)
> **Date:** 2026-06-13
> **Type:** `implementation change` | `UI change`
> **Position:** `Implementer` — Cursor/Claude Code 에이전트에 UI UX Pro Max 스킬 설치 및 프로젝트 커스터마이징

---

## 1. Goal

AI 코딩 에이전트(Cursor, Claude Code 등)가 shapez2Factory 웹 앱의 UI 코드를 생성할 때,
프로젝트의 디자인 토큰(컬러, 폰트, 스타일 규칙)을 자동 인식하고 적용하도록
UI UX Pro Max 스킬을 통합함.

## 2. Current behavior

- AI 코딩 에이전트가 UI 코드를 생성할 때 `DESIGN.md`를 수동 참조해야 함
- 디자인 데이터베이스(스타일, 컬러 시스템, 폰트페어링, UX 가이드라인)가 에이전트 내에 없음
- Tailwind CSS utility 생성 시 프로젝트 테마와 무관한 스타일 적용 가능
- 일관된 디자인 결정이 불가능 — 매 생성마다 에이전트 임의의 스타일 선택

## 3. Target behavior

- UI UX Pro Max 스킬이 프로젝트에 통합되어 디자인 데이터베이스 자동 제공
- 에이전트가 프로젝트 컬러 토큰을 기본값으로 인식
- Tailwind CSS 코드가 `input.css`의 `@layer components`와 호환
- AI 생성 코드가 `npm run build:css`와 `python manage.py check` 통과

## 4. Contract

- **Invariant 1:** 기존 컬러 토큰(`#020617`, `#22D3EE`, `#34D399` 등) 유지
- **Invariant 2:** 기존 폰트(`Google Sans Code`, `Fira Code`) 유지
- **Invariant 3:** Dark OLED dashboard 테마 방향성 유지
- **Invariant 4:** 기존 `lab-` 프리픽스 CSS 클래스 호환
- **Forbidden:** UI UX Pro Max 기본 스타일(예: Glassmorphism)을 프로젝트 테마와 무작정 혼합하지 않음

## 5. Non-goals

- UI UX Pro Max 자체 fork/수정
- Django 템플릿 기능 로직 변경
- 모바일 네이티브 앱 개발
- 3D 레이블/스프라이트 렌더링(Three.js) UI 변경

## 6. File map

| File | Change |
|------|--------|
| `assets/css/ui-ux-pro-max-themes.css` | UI UX Pro Max 스타일 기반 커스텀 컴포넌트 정의 (NEW) |
| `assets/css/input.css` | 새 테마 파일 import 및 토큰 추가 (MODIFY) |
| `.cursor/rules/ui-ux-pro-max-skill.mdc` | Cursor용 UI UX Pro Max skill rules (NEW) |
| `.cursor/prompts/ui-design.md` | Cursor 프롬프트: UI 생성 시 프로젝트 디자인 토큰 참조 규칙 (NEW) |
| `frontend/recipe_graph_editor/src/` | 스킴 분석 — 새로운 React 컴포넌트에 UI UX Pro Max 스타일 적용 (READ-ONLY) |
| `django_apps/web/templates/` | Django 템플릿에 Tailwind 클래스 생성 규칙 확인 (READ-ONLY) |

## 7. Steps

### Task 1: UI UX Pro Max 스타일 매핑 분석

- [ ] UI UX Pro Max 57개 스타일 중 shapez2Factory 테마와 호환되는 스타일 식별
  - 다크 테마와 호환: Aurora UI, Motion-Driven, Glassmorphism (다크 버전)
  - 부적합: Light-only 스타일, 네온/밝은 배경 기반 스타일
- [ ] 95개 컬러 팔레트 중 프로젝트 다크 테마와 어울리는 시스템 추출
  - 다크 SaaS, Developer Tools, Fintech 팔레트 우선
  - 프로젝트 토큰(`#020617`, `#22D3EE`, `#34D399`)과 매핑
- [ ] 56개 폰트페어링 중 `Google Sans Code` 기반 추천 매핑

**Output:** `documents/knowledge/raw/ai/ui_ux_pro_max_theme_mapping.md` (optional)

---

### Task 2: CSS 컴포넌트 정의

**Files:** `assets/css/ui-ux-pro-max-themes.css`, `assets/css/input.css`

- [ ] `assets/css/ui-ux-pro-max-themes.css` 생성
  - `@layer components` 섹션
  - 프로젝트 테마 커스터마이징된 스타일 컴포넌트 정의
  - `--lab-bg`, `--lab-surface`, `--lab-border` 등 기존 CSS 변수 활용
  - 다크 테마 호환 스타일만 포함
- [ ] `assets/css/input.css`에 `@import` 추가
- [ ] `npm run build:css` 통과 검증

**Example component:**

```css
@layer components {
  /* UI UX Pro Max: Project-adapted dark style tokens */
  .pro-max-dark-card {
    @apply bg-slate-900 border border-slate-700 rounded-lg;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
  }

  .pro-max-accent-btn {
    @apply bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-semibold rounded-md px-4 py-2 transition-all;
  }

  .pro-max-muted-text {
    @apply text-slate-400;
  }
}
```

---

### Task 3: Cursor rule 작성

**Files:** `.cursor/rules/ui-ux-pro-max-skill.mdc`, `.cursor/prompts/ui-design.md`

- [ ] `.cursor/rules/ui-ux-pro-max-skill.mdc` 생성
  - UI UX Pro Max 스킬의 6대 데이터베이스(스타일, 컬러, 폰트, 스택, 차트, 랜딩 패턴) 소개
  - 프로젝트 디자인 토큰(`DESIGN.md` YAML) 참조 규칙
  - Tailwind utility 클래스 기반 생성 규칙
  - `@layer components` 확장 방법
- [ ] `.cursor/prompts/ui-design.md` 생성
  - UI 생성 시 프로젝트 디자인 토큰 참조 규칙
  - "스타일 선택 시 프로젝트 다크 테마 우선" 등 구체적인 가이드라인

**Example rule structure:**

```markdown
# UI UX Pro Max Integration Rules

## Overview
UI UX Pro Max provides design intelligence for AI coding agents.
When generating UI code, follow these project-specific rules:

## Design Tokens (from DESIGN.md)
- Primary: #020617 (OLED black)
- Surface: #0F172A (dark slate)
- Accent: #22D3EE (cyan)
- Success: #34D399 (green)
- Font: Google Sans Code (headings/body), Fira Code (code/mono)

## Rules
1. Always use project dark theme — no light backgrounds
2. Use Tailwind utilities from input.css components
3. Extend @layer components in ui-ux-pro-max-themes.css for custom styles
4. Respect lab- prefix compatibility for existing components
5. Verify with npm run build:css before committing

## UI UX Pro Max Database
- 57 UI styles: only dark-compatible ones (Aurora, Motion-Driven, Glassmorphism-dark)
- 95 color palettes: dark SaaS/Developer Tools/Fintech
- 56 font pairings: Google Sans Code based only
- 8 tech stacks: React, Next.js, Tailwind (project stacks)
```

---

### Task 4: 에이전트 테스트

**Tools:** Cursor / Claude Code

- [ ] UI UX Pro Max 스킬이 Cursor/Claude Code에서 작동
- [ ] 에이전트가 UI 생성 시 프로젝트 컬러 토폰 기본값 사용
  - 예: "asteroid lab의 층 선택 UI 개선해줘" → 다크 테마 토큰 적용
- [ ] 생성 코드의 Tailwind utility가 프로젝트 토큰과 일치

---

### Task 5: Validation gate

```bash
# CSS 빌드 검증
npm run build:css

# Django 체크
python manage.py check

# 전체 테스트 (선택)
powershell -File scripts/test_fast.ps1
```

**Manual verification:**
- [ ] 기존 asteroid lab UI가 파괴되지 않음
- [ ] `DESIGN.md` 토큰과 UI UX Pro Max 데이터베이스 충돌 없음

## 8. Stop conditions

- Public contract conflict (DESIGN.md 토큰 충돌) discovered
- Scope grows beyond UI enhancement
- Existing invariant violation
- Agent setup failure (에이전트별 설정 필요 — 이 경우 수동 작업으로 전환)

## 9. Completion boundary

This plan is complete when all listed steps are finished or explicitly `BLOCKED:`.

After the final step:
- run validation
- write final report (`Completed`, `Validation`, `Deferred Work`, `STOPPED_AT_APPROVED_SCOPE`)
- stop

No additional task creation is allowed (no D-1, follow-up phase, opportunistic cleanup/refactor, or unapproved deferred implementation).

Deferred work may be listed; must not be implemented without explicit user approval.

## 10. Deferred Work (not in scope)

- UI UX Pro Max 스킬의 8개 기술 스택 지원 중 React Native/SwiftUI/Flutter 적용 (모바일 앱은 현재 계획 없음)
- 3D 레이블/스프라이트 렌더링 UI 개선
- AI 생성 UI의 자동화된 테스트 (현재 수동 검증만)
- 다른 에이전트(Qoder, Kiro, Copilot 등) 통합 — Cursor/Claude Code 우선
