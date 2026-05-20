# 유전자 샘플(GeneticSample) — 구현 메모

**상태**: ACTIVE (구현 진행)  
**목적**: Shapez2 복사 문자열(`SHAPEZ2-4-…`)을 저장 시 디코드해 `decoded_json`에 넣고, Django Admin에서 server 좌표 기반 미니 그리드 + `web/assets/sprites/` 스프라이트로 미리보기.

## 결정

- 앱: `asteroid_lab`. 모델 `GeneticSample`.
- 디코드: `decode_copy_string` → `normalize_decoded_blueprint` → `attach_server_coords_to_decoded_json` (맵 입력과 동일 파이프라인).
- 검증 실패: `Model.clean()`에서 `ValidationError`로 저장 차단.
- 스프라이트 파일명 규칙: `asteroid_miner_layout_lab.js`의 `LAB_SPRITE_KNOWN` / `labSpriteFilenameForCell`과 **Python 모듈에서 동기 복제** (주석으로 JS 위치 명시).
- Admin 그리드: bbox의 `server_*`로 열·행 수 결정; Y는 bbox **left-bottom** 규칙에 맞춰 위가 큰 `server_y`가 위쪽 행이 되도록 매핑.
- 선택 필드: `name`, `project`(nullable FK `AsteroidProject`).

## 참조 코드

- `django_apps/asteroid_lab/adapters/decode_adapter.py`
- `django_apps/asteroid_lab/snapshots/decoded_blueprint_snapshot.py`
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
