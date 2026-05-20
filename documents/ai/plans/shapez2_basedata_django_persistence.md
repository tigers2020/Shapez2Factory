# shapez2 basedata IVVD — Django 정본 영속화 (플랜)

**상태**: ACTIVE (구현 진행)  
**범위**: [`documents/shapez_2_data/basedata-v1137`](../../shapez_2_data/basedata-v1137)만 (세이브·블루프린트 제외).

## 목적

`shapez_core`를 **canonical immutable verified dataset** 레이어로 두고, 게임 basedata를 **결정적·검증 가능한** 형태로 SQLite/Postgres에 적재한다. `reverse_engineering` 등 tooling 앱은 **이 레이어를 import**하며, solver/replay는 **core만** 참조한다.

## 앱 경계

- **정본 DB·모델**: `django_apps.shapez_core`만.
- **추출·런타임 스캔·Explorer UI**: 별도 앱(예: `reverse_engineering`). solver/replay가 해당 앱을 import하지 않는다.

## 데이터 철학

| 단계 | 의미 |
|------|------|
| Imported | 원문 바이트 읽기, `raw_text`/`payload`, `sha256`, `byte_size` |
| Schema | `jsonschema` (해당 문서에 스키마가 매핑될 때만) |
| Cross-ref | `identifiers.json` ↔ `buildings.json` 등 ID 집합 일치 |
| Semantic | `domain/` 순수 규칙(추가 시); 현재는 최소 스텁 |
| Sealed | `shapez-ivvd-seal-v1` payload로 `release_integrity_hash` 확정 |

**IMPORT 성공 ≠ 검증 성공**: 구조 검증 실패 시에도 **raw/payload는 저장**하고, `ShapezIntegrityIssue`·`schema_valid` 등으로 표시.

## 원문(raw) 정책

- **기본**: full `raw_text`(또는 동등) 보존 — 역공학·증거 추적.
- **선택**: `compressed_raw_blob` + `raw_compression_codec` — 압축 해제 바이트의 `sha256`은 미압축과 동일해야 함.
- **예외 모드**: `hash_only_external`은 운영상 필요 시만 문서화(초기 구현에서는 생략 가능).

## Append-only·Sealed

- Sealed 이후 **document/identifier 행 rewrite 금지**(운영 원칙).
- 재검증: 새 `ShapezValidationRun`, 새 `ShapezIntegrityIssue`.
- **논리 대체**: `ShapezIntegrityIssue.is_superseded`, `superseded_by_run`으로 동일 phase의 이전 이슈를 폐기 표시(행 삭제 없음).

### Supersession 배치 규칙 (구현 기본)

동일 `release`·동일 `validation_phase`에 대해 새 `ShapezValidationRun`이 **성공 종료**되면, 그 phase의 **이전 run**에서 생성된 이슈 중 `is_superseded=False`인 것에 대해 `is_superseded=True`, `superseded_by_run=새 run`을 설정한다.

## Seal — `shapez-ivvd-seal-v1`

- 상수: `SEAL_ALGORITHM = "shapez-ivvd-seal-v1"`.
- Payload(개념): `algorithm_version`, `game_version`, `document_count`, `documents`(각 `source_relative_path`, `sha256`, `byte_size` — **`source_relative_path` 오름차순 정렬**, 경로 중복 없음).
- 직렬화: UTF-8, JSON `sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=False`.
- `release_integrity_hash` = 위 캐논 문자열의 SHA-256(hex).
- `ShapezBasedataRelease.seal_input_canonical_json`에 캐논 문자열 저장(재계산·디버깅).

## 좌표 도메인

- [`django_apps/shapez_core/domain/coordinates/`](../../django_apps/shapez_core/domain/coordinates/): `raw`/`server` 축, `x==0` 부재 규칙, 인접 정규화 등 — replay·reconstruction·topology의 **단일 출처**로 확장 예정. 초기에는 모듈 스텁·문서 문자열만 둔다.

## 파생 계열(lineage)

- `ShapezCanonicalArtifact`: `source_document`, `derivation_step`, `parent_artifact`로 raw → graph → topology … 추적 예정. 초기 스키마만.

## 관리 명령

- `python manage.py import_shapez_basedata --root <path> [--replace] [--strict-seal]`
- `--replace`: 동일 `game_version` 릴리스가 있으면 삭제 후 재적재.
- `--strict-seal`: seal 전에 error긴 이슈가 있으면 비0 종료(옵션).

## 설정

- `SHAPEZ_BASEDATA_ROOT`: 없으면 `BASE_DIR / "documents/shapez_2_data/basedata-v1137"`.

## 외부 개념 참고

- [Zuplo — JSON Schema validation](https://zuplo.com/blog/verify-json-schema/)
- [W3C VC JSON Schema](https://www.w3.org/TR/vc-json-schema/)

## 승인

본 문서는 구현 정렬용 ACTIVE 플랜이다. CANON 승격 시 `documents/index/document_inventory.md` 갱신한다.
