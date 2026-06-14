# UI UX Pro Max — Design Intelligence Integration

**Status:** APPROVED (2026-06-13 — S1 agent overlay in progress)
**Date:** 2026-06-13
**Related:** `concepts/ui-ux-pro-max-skill.md`, `raw/ui-ux-pro-max-skill.md`
**Plan:** `documents/superpowers/plans/2026-06-13-ui-ux-pro-max-integration.md`

---

## 1. Problem

shapez2Factory 웹 앱의 UI 개발은 `DESIGN.md` YAML 토큰과 Tailwind utility 클래스 기반으로 진행되지만, AI 코딩 에이전트(Cursor, Claude Code 등)가 UI 코드를 생성할 때 체계적인 디자인 데이터베이스(스타일, 컬러, 타이포그래피, UX 가이드라인)가 부족함. 에이전트가 일관된 디자인 결정을 내리기 위한 참조 자료가 없으며, 매 생성마다 에이전트 임의의 스타일이 적용될 위험이 있음.

### Success metric

```text
AI 에이전트가 UI 생성 시 프로젝트 디자인 토큰(컬러, 폰트, 테마)을 자동 인식하고 적용
→ 생성된 Tailwind 코드가 DESIGN.md 토큰과 충돌 없이 npm run build:css 통과
```

---

## 2. Strategy

```text
Primary:   A) UI UX Pro Max 스킬을 프로젝트에 통합하여 디자인 데이터베이스 제공
           B) 프로젝트 디자인 토큰을 에이전트 컨텍스트에 주입 (DESIGN.md + input.css 스니펫)
           C) 커스텀 스타일 컴포넌트 정의 (ui-ux-pro-max-themes.css)
Secondary: D) 에이전트별 rule 파일 작성 (Cursor .mdc, Claude .md)
```

---

## 3. Core invariants

```text
기존 컬러 토큰(#020617, #22D3EE, #34D399 등)은 유지
기존 폰트(Google Sans Code, Fira Code)는 유지
Dark OLED dashboard 테마 방향성은 유지
기존 lab- 프리픽스 CSS 클래스는 호환
Tailwind CSS v4 + Flowbite 호환 유지
```

### Design tokens (soT — DESIGN.md)

| Role | Value |
|------|-------|
| primary | `#020617` |
| secondary | `#1E293B` |
| tertiary / accent | `#06B6D4` |
| surface | `#0F172A` |
| border-default | `#1E293B` |
| border-accent | `#22D3EE` |
| success | `#34D399` |
| warning | `#F59E0B` |
| error | `#FB7185` |
| headline / body / label | `Google Sans Code` |
| code / mono | `Fira Code` |

### UI UX Pro Max database

| Category | Count | Project relevance |
|----------|-------|-------------------|
| UI Styles | 57 | 다크 테마 호환 스타일만 추출 (Aurora UI, Motion-Driven 등) |
| Color Palettes | 95 | 다크 SaaS/Developer Tools 팔레트 중 프로젝트 토큰과 매핑 |
| Font Pairings | 56 | `Google Sans Code` 기반 추천만 활용 |
| Tech Stacks | 8 | React, Next.js, Tailwind — 프로젝트 스택과 일치 |
| Chart Types | 24 | Dashboard UI 참고용 |
| Landing Patterns | 29 | 프로젝트 랜딩 페이지 참고용 |

### Forbidden patterns

```text
UI UX Pro Max 기본 스타일(예: Glassmorphism, Neumorphism)을 프로젝트 다크 테마와 무작정 혼합하지 않음
기존 기능 로직을 변경하는 CSS/JS 변경
프로젝트 빌드 파이프라인(npm run build:css, esbuild)을 우회하는 정적 파일 생성
모바일 네이티브 앱(SwiftUI/React Native/Flutter) 개발 — 현재 계획 없음
3D 레이블/스프라이트 렌더링(Three.js) UI 변경
```

---

## 4. Authority map

```text
DESIGN.md (YAML tokens)          → canon design contract
assets/css/input.css             → Tailwind source + @layer components
ui-ux-pro-max-themes.css         → UI UX Pro Max 스타일 파생 규칙 (NEW)
.cursor/rules/ui-ux-pro-max-skill.mdc  → Cursor 에이전트 컨텍스트 (NEW)
.cursor/prompts/ui-design.md     → Cursor 프롬프트 규칙 (NEW)
```

### Module layout pattern

| Layer | Module pattern | Authority |
|-------|----------------|-----------|
| Design tokens | `DESIGN.md` | Canon — YAML 토큰 |
| Tailwind source | `assets/css/input.css` | Tailwind build entry |
| Custom components | `assets/css/ui-ux-pro-max-themes.css` | UI UX Pro Max 파생 |
| Agent rules | `.cursor/rules/*.mdc` | Cursor agent context |
| Agent prompts | `.cursor/prompts/*.md` | Cursor agent behavior |

---

## 5. Phased rollout

### Phase 0 — 스타일 매핑 분석 (no behavior change)

| Deliverable | Path |
|-------------|------|
| UI UX Pro Max 스타일 매핑 분석 | `documents/knowledge/raw/ai/ui_ux_pro_max_theme_mapping.md` (NEW) |
| 프로젝트 테마와 호환되는 스타일 식별 | `ui-ux-pro-max-themes.css` `@layer components` |

### Phase 1 — CSS 컴포넌트 정의

| Order | Target | Action |
|-------|--------|--------|
| 1 | `assets/css/ui-ux-pro-max-themes.css` | 프로젝트 테마 커스터마이징된 스타일 컴포넌트 정의 |
| 2 | `assets/css/input.css` | 새 테마 파일 `@import` 추가 |
| 3 | `npm run build:css` | 빌드 통과 검증 |

### Phase 2 — 에이전트 설정

| Order | Target | Action |
|-------|--------|--------|
| 1 | `.cursor/rules/ui-ux-pro-max-skill.mdc` | Cursor용 UI UX Pro Max skill rules |
| 2 | `.cursor/prompts/ui-design.md` | UI 생성 시 프로젝트 디자인 토큰 참조 규칙 |
| 3 | Cursor / Claude Code에서 테스트 작동 | 에이전트 컨텍스트 주입 검증 |

### Phase 3 — 통합 테스트

| Order | Target | Action |
|-------|--------|--------|
| 1 | 에이전트 UI 생성 | 자연어 프롬프트 → Tailwind 코드 생성 |
| 2 | `npm run build:css` | 빌드 통과 |
| 3 | `python manage.py check` | Django 체크 통과 |
| 4 | 수동 검증 | 기존 asteroid lab UI 파괴 여부 |

---

## 6. Testing and validation

### Per-phase gates

```bash
# Phase 1: CSS 빌드
npm run build:css

# Phase 2-3: Django + test
python manage.py check
powershell -File scripts/test_fast.ps1
```

### Acceptance criteria

| Criterion | Verification |
|-----------|--------------|
| UI UX Pro Max 스킬이 Cursor/Claude Code에서 작동 | 에이전트 컨텍스트 주입 확인 |
| 에이전트가 UI 생성 시 프로젝트 컬러 토큰 기본값 사용 | 생성 코드의 hex 값 확인 |
| `npm run build:css` 통과 | 빌드 결과 |
| `python manage.py check` 통과 | Django check 결과 |
| `assets/css/ui-ux-pro-max-themes.css` 존재 및 import됨 | 파일 존재 + input.css import 확인 |
| `.cursor/rules/ui-ux-pro-max-skill.mdc` 존재 및 에이전트 인식 | 파일 존재 + 에이전트 인식 |
| 기존 asteroid lab UI가 파괴되지 않음 | 수동 검증 |
| `DESIGN.md` 토큰과 UI UX Pro Max 데이터베이스 충돌 없음 | 토큰 비교 |

---

## 7. Risks and non-goals

### Risks

| Risk | Mitigation |
|------|------------|
| UI UX Pro Max 기본 스타일과 프로젝트 테마 충돌 | 커스텀 스타일 컴포넌트에서 재정의 (ui-ux-pro-max-themes.css) |
| Tailwind v4와 Flowbite 호환성 | 기존 빌드 파이프라인 유지, 새 파일만 추가 |
| 에이전트별 설정 차이 | Cursor 우선, 이후 다른 에이전트 확장 |
| 생성 코드의 디자인 토큰 무시 | 에이전트 컨텍스트에 DESIGN.md 스니펫 포함 |

### Non-goals

- UI UX Pro Max 자체 fork/수정
- Django 템플릿 기능 로직 변경
- 모바일 네이티브 앱 개발 (SwiftUI/React Native/Flutter)
- 3D 레이블/스프라이트 렌더링(Three.js) UI 변경
- AI 생성 UI의 자동화된 테스트 — 현재 수동 검증만
- 다른 에이전트(Qoder, Kiro, Copilot 등) 통합 — Cursor/Claude Code 우선

---

## 8. Approval record

| Section | Status |
|---------|--------|
| §1 Problem | APPROVED |
| §2 Strategy | APPROVED |
| §3 Invariants / forbidden | APPROVED |
| §4 Authority map | APPROVED |
| §5 Phased rollout | APPROVED |
| §6 Testing / success criteria | APPROVED |
| §7 Risks / non-goals | APPROVED |

---

## 9. Execution plan

[[../plans/2026-06-13-ui-ux-pro-max-integration.md]]
