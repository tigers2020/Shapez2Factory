# Architecture

이 문서는 [`.cursor/rules/architecture.mdc`](../../.cursor/rules/architecture.mdc)의 사람 친화 버전이다.

## 문서 층

| 트리 | 역할 |
|---|---|
| `docs/architecture/` (본 문서) | 레이어·의존·앱 소유 **요약** |
| `structure.md` | 저장소 경로·URL·테스트 배치 **정본** |
| `documents/` | 알고리즘·CANON·ADR **정본** |

---

## Phase 1 — Django delivery (현재)

```
config/urls.py
    ├── django_apps/shapez_core/     (API: shape preview, health)
    ├── django_apps/web/             (pages, static, thin views)
    │       ├── shapez_solver        (solver UI, recipe graph endpoints)
    │       └── asteroid_lab         (asteroid miner lab UI)
    ├── django_apps/shapez_solver/   (planner, graph, models)
    └── django_apps/asteroid_lab/    (decode, replay, optimization)
            └── shapez_core only
```

### 의존 방향

- `shapez_core` ← `shapez_solver`, `asteroid_lab` (각각 core만)
- `shapez_solver` ↔ `asteroid_lab` **금지**
- `web` → core, solver, asteroid_lab

### URL ownership (요약)

| Path prefix | Owner |
|---|---|
| `/admin/`, `/accounts/` | Django / allauth |
| `/api/` | `shapez_core` |
| `/`, `/solver/`, `/asteroid-miner-layout/`, … | `web` (i18n) |

상세: [`structure.md`](../../structure.md)

---

## Phase 2+ — Hexagonal target

```
src/shapez2_factory/
├── domain/          # 순수 비즈니스 규칙 (I/O 없음)
├── application/
│   ├── ports/       # Protocol / ABC
│   └── use_cases/   # 오케스트레이션
├── adapters/        # ORM, 외부 API, DTO 변환
├── interfaces/      # UI 조합
└── bootstrap/       # DI wiring
```

### 의존 방향

```
interfaces ──► application (use_cases, ports)
adapters   ──► application.ports
application──► domain
bootstrap  ──► adapters, interfaces, application
domain     ──► (없음)
```

현재 `src/shapez2_factory/`는 stub만 있으며, 추출은 Phase 2 이후다.

---

## Django → hexagonal 매핑

| Phase 1 (Django) | Phase 2+ (target) | 담당 |
|---|---|---|
| `shapez_core/domain/` | `domain/` | 도미닉 |
| `shapez_solver/services/` (orchestration) | `application/use_cases/` | 유리 |
| `shapez_solver/ports/`, protocols | `application/ports/` | 유리 |
| ORM, `services/`, external I/O | `adapters/` | 아다 |
| `django_apps/web/` | `interfaces/` | 지나 |
| `config/`, `INSTALLED_APPS` | `bootstrap/` | 시몬 |

## Port 설계 (Phase 2+)

1. `application/ports/` 아래 Protocol 또는 ABC.
2. use case는 port 타입에만 의존.
3. adapter는 port 구현 + DTO 변환.
4. 테스트는 port fake로 unit test.

## 참조

- [Domain Manual](../domain/README.md)
- [ADR](../adr/README.md)
- [architecture.mdc](../../.cursor/rules/architecture.mdc)
- [AGENTS.md](../../AGENTS.md)
