# Architecture

이 문서는 `.cursor/rules/architecture.mdc`의 사람 친화 버전이다. 레이어 책임과 의존 방향을 규범적으로 기술한다.

## 레이어 구조

```
src/{{package_name}}/
├── domain/          # 순수 비즈니스 규칙, 값 객체, 정책 (I/O 없음)
├── application/
│   ├── ports/       # port 추상화 (Protocol / ABC)
│   └── use_cases/   # use case 오케스트레이션
├── adapters/        # port 구현체, 외부 시스템 연동, DTO 변환
├── interfaces/      # UI 화면, 사용자 상태, 위젯 조합
└── bootstrap/       # 의존성 조립 (DI wiring)
```

## 의존 방향

```
interfaces ──► application (use_cases, ports)
adapters   ──► application (ports)
application──► domain
bootstrap  ──► adapters, interfaces, application
domain     ──► (없음 — 외부 의존 금지)
```

## 레이어별 책임

### domain

- 엔티티, 값 객체, 도메인 이벤트, 정책
- I/O, UI, DB, 외부 API 호출 절대 금지
- 담당: 도미닉

### application

- use case = 입력 수신 → domain 호출 → 출력 반환
- port(Protocol/ABC)로 외부 의존을 추상화
- 구체 adapter 구현 직접 import 금지
- 담당: 유리

### adapters

- port 계약 구현
- 외부 응답을 application DTO로 변환
- 비즈니스 정책 포함 금지
- 담당: 아다

### interfaces

- UI 화면, 사용자 상태 관리
- use case 또는 application DTO에만 의존
- adapter 구현 직접 알지 않음
- 담당: 지나

### bootstrap

- 구체 adapter와 UI/use case를 조립
- 프레임워크 초기화, 설정 로딩
- 담당: 시몬

## Port 설계 지침

1. `application/ports/` 아래에 Protocol 또는 ABC로 정의한다.
2. use case는 port 타입에만 의존한다 (구체 클래스 X).
3. adapter는 port 계약을 만족하는 구체 구현을 제공한다.
4. 테스트에서는 port를 fake(stub/mock) 구현으로 교체한다.

## 참조

- [Domain Manual](../domain/README.md)
- [ADR](../adr/README.md)
- [architecture.mdc](../../.cursor/rules/architecture.mdc)
