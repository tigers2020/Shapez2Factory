# ACTIVE — v2 DTO 물리 분해·호환 re-export (게이트)

**상태**: Slice 1~7 및 **8(`DecodedBlueprintDocument`)** 구현 완료. `domain/dto.py`는 **호환 배럴**(전 심볼 re-export)만 남음.

**주의**: `replay/trace_event.py`의 가변 `TraceEvent`(NDJSON 행)은 **별 타입**이다.

---

## 완료된 슬라이스 (요약)

| Slice | 모듈 | 비고 |
|-------|------|------|
| 1 | `domain/reconstruction.py` | |
| 2 | `domain/existing_layout.py` | |
| 3 | `domain/placement.py` | |
| 4 | `domain/routing.py` | |
| 5 | `domain/validation.py` | |
| 6 | `runtime/trace_events.py` | `TraceEvent` |
| 6b | `domain/orchestration.py` | |
| 7 | `serialization/public_artifacts.py`, `dto_adapters.py` | behavior artifact JSON 계약 |
| 8 | `domain/decoded_blueprint.py` | `DecodedBlueprintDocument`; `dto`·`domain/__init__` re-export / 직접 import 병행 |

**호환**: `from ...domain.dto import DecodedBlueprintDocument` 유지(`dto`가 `decoded_blueprint`와 동일 객체 re-export).

**경계**: `test_domain_import_boundaries.py`에 `decoded_blueprint.py` AST 금지 + `dto`↔`decoded_blueprint` 동일성.

---

## 다음(선택)

- `dto.py` 배럴을 더 얇게(문서만 re-export·신규 코드는 세부 모듈 직접 import 권장) 하는 팀 규칙 정리.
- 솔버 전체 E2E·replay는 별 플랜.

**하지 말 것**: 공개 JSON 키 rename, 알고리즘 무단 변경.

---

## 검증 (로컬)

```text
python -m pytest tests/unit/shapez_asteroid_v2/
python -m ruff check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2
python -m black --check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2
```
