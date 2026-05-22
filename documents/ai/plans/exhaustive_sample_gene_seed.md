# Exhaustive sample gene DB 시드 (승인 요약)

## 목적

규칙으로 정의된 **채굴기 1 + R 방향 transport 1칸 + N/W/S만 extension(최대 3, 트리)** 조합을 전수 생성하고, `encode_copy_string`으로 복사 문자열을 만든 뒤 `GeneticSample`에 **gene_key 기준**으로 idempotent 저장한다. 기존 수동 샘플 16개 등은 **입력이 아니라** 레이아웃·타일 참고용이다.

## 파이프라인

```text
rules → canonical topology → layout JSON → encode_copy_string → GeneticSample.update_or_create(gene_key=…)
```

게임 공식 섬 export(`translate_lab_entries_to_official_xy`) 앵커:

```text
export_x = raw_x_to_dense_index(raw_x) - raw_x_to_dense_index(extractor_x)
export_y = raw_y - extractor_y - 1
```

(`raw_x - (extractor_x + 1)` 사용 금지 — west branch 에서 dense 열 갭.) 시드 후 `decoded_json` 의 `server_x` 는 연속 bbox 를 기대한다.

## 불변식

- **`gene_key`**: canonical topology 문자열(JSON). **upsert·중복 제거·stale 삭제의 정본**.
- **`name`**: 표시용. topology 동일 시 `gene_key` 동일, 이름만 바꿔도 동일 row upsert.

## 추상 격자 → raw `X,Y` (`grid_to_raw_xy`)

- 추상: extractor `(0,0)`, 출력 transport `(1,0)` (= R 한 칸).
- 부착: extension만 `N=(0,-1), W=(-1,0), S=(0,1)` (R 금지).
- raw 변환 `abstract_grid_to_raw_xy` (구현: `django_apps/asteroid_lab/services/sample_gene_exhaustive_generator.py`):
  - `gx >= 0` → `X = gx + 1`
  - `gx < 0` → `X = gx`
  - `Y = gy`  
  → raw 열 `X==0` 은 **금지**; 위 식으로 양수 추상 열은 항상 `X>=1`, 음수 추상 열은 `X<0`.  
  `build_layout_root` 는 `BP.Entries` 빌드 직후 `X==0` 이면 `ValueError` 로 실패한다.
- 확장기 `R`(쿼터): 부모 셀과 `equipment_bundles.ports_compatible` 이 되도록 선택(입구가 부모 방향).

## Canonical `gene_key`

`transport_kind` + `extension_count` + 정렬된 엣지 리스트  
각 엣지: `(parent_abstract_coord, child_abstract_coord, attach_dir)`.

## DB 필드

- `GeneticSample.gene_key` (nullable, indexed, partial unique: 값이 있을 때만 유일)
- `GeneticSample.metadata_json` — `generator`, `transport_kind`, `extension_topology_key`, `rules` 등 (게임 JSON과 분리)

## 커맨드

```bash
python manage.py seed_exhaustive_sample_genes --dry-run
python manage.py seed_exhaustive_sample_genes
```

옵션: `--transport-kind`, `--max-extensions`, `--limit`, `--delete-stale-generated`, `--generator-version`.  
`--delete-stale-generated`는 `metadata_json.generator`가 일치하고 이번 실행 결과 `gene_key`에 없는 행만 삭제; **`--limit`이 있으면 스킵**.

## Django Admin

`GeneticSample` changelist 상단 **「전수 샘플 gene 시드」** 폼 → `seed_exhaustive_sample_genes` (`dry-run`, `delete_stale_generated` 체크박스).  
구현: `django_apps/asteroid_lab/admin.py` · `django_apps/web/templates/admin/asteroid_lab/geneticsample/change_list.html` (`TEMPLATES['DIRS']`).

## 검증

- `python -m pytest tests/unit/asteroid_lab -k "sample_gene or exhaustive"`
- `ruff` / `mypy` / `black` (변경 범위)
