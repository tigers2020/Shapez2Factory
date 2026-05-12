# Pass12 preserve-quality 텔레메트리: 검증·집계·A/B·정책 게이트 (2026-05-11)

## 1. 검증 (렉스)

| 항목 | 결과 |
|------|------|
| `python -m pytest tests/unit/shapez_asteroid/ -q` | 467 passed, 2 skipped |
| `ruff check` / `black --check` (변경 파일 한정) | `recovery_orchestrator.py` 통과 |
| `mypy` (변경 파일 한정) | `recovery_orchestrator.py` 통과 |
| 전체 `ruff check .` | 저장소 내 기존 E501 등으로 실패 가능 (이번 작업 범위 밖) |
| 전체 `black --check .` | `config/settings.py` 등 기존 미포맷 가능 (이번 작업 범위 밖) |

**코드 수정 (본 게이트)**: `recovery_orchestrator`에서 `max_cycles`가 0이 되어 Pass3→P4 루프가 한 번도 돌지 않는 경우를 막기 위해 `max_cycles = max(1, int(max_cycles))`를 적용했다. 단위 테스트가 `recovery_orchestrator.MAX_VALIDATION_RECOVERY_ATTEMPTS`만 0으로 패치하고 `is_validation_recovery_loop_enabled()`는 여전히 True인 조합에서 발생하던 회귀다.

## 2. 트레이스 소스 (픽)

운영 `var/asteroid_mining_layout_debug/*.ndjson`은 환경·gitignore에 따라 워크스페이스에 없을 수 있어, **production 계약과 동일한 형태**의 재현용 팩을 커밋했다.

- 디렉터리: [`tests/fixtures/pass12_telemetry_trace_pack/`](../../tests/fixtures/pass12_telemetry_trace_pack/)
- `trace_01` … `trace_05`: 각 파일 1줄 `kind=trace`, `message=solver_summary` NDJSON (합계 5 run)
- A/B 입력 BP: [`striped_greenfield_bp.json`](../../tests/fixtures/pass12_telemetry_trace_pack/striped_greenfield_bp.json) (스크립트 내 greenfield striped 스모크와 동형)

실제 운영 NDJSON이 있으면 동일 명령으로 교체하면 된다.

```bash
python scripts/aggregate_pass12_recoverability_from_ndjson.py path/to/debug_dir --split-by-ndjson-run-id
python scripts/pass12_preserve_recovery_ab.py --ndjson path/to/decoded_with_BP.json
```

## 3. Production aggregate 요약 (5 synthetic runs)

명령:

`python scripts/aggregate_pass12_recoverability_from_ndjson.py tests/fixtures/pass12_telemetry_trace_pack --split-by-ndjson-run-id`

| 지표 | 값 |
|------|-----|
| `total_runs` / `solver_summary_rows_used` | 5 |
| 클래스 합계 | `TRIVIAL` 16, `LOCAL_ROTATION` 9, `NEAR_TRANSPORT` 4, `UNRECOVERABLE` 5 |
| `avg_preserve_quality_score` | 0.682 |
| `p50` / `p90` (PQS) | 0.71 / 0.904 |
| `source_kind_breakdown` (rows) | `existing_shape_layout` 2, `existing_fluid_layout` 2, `unknown` 1 |

**source_kind 관찰**: `existing_fluid_layout` bucket에만 `UNRECOVERABLE` 5와 `STUB_GEOMETRY_BLOCKED` reason이 집중된다. `existing_shape_layout`은 `TRIVIAL` 비중이 크고 PQS 평균이 더 높다(합성 시나리오 기준).

## 4. A/B digest (striped greenfield BP)

명령:

`python scripts/pass12_preserve_recovery_ab.py --ndjson tests/fixtures/pass12_telemetry_trace_pack/striped_greenfield_bp.json`

출력: [`var/pass12_recovery_ab_experiment.json`](../../var/pass12_recovery_ab_experiment.json) (로컬 생성)

| 항목 | 값 |
|------|-----|
| `trace_run_id` | `null` (CLI 직접 실행, solver trace NDJSON 미결합) |
| `recovery_candidate_fraction` | `null` (stub drop 0 → 분모 없음) |
| `recoverability_outcome_by_class` | `{}` (OFF 측 drop 없음) |
| `recovery_default_on_candidate` | `false` |
| `recovery_safe_gate` | geometry/connectivity/step4/missing_stub 모두 통과, `preserve_quality_improved`는 `false` |
| OFF vs ON | stub drop·recovery success·PQS·step4 실패 모두 동일 (델타 0) |

이 입력은 preserve drop이 없어 **recovery ON 가치를 숫자로 논할 재료가 거의 없다**. drop이 있는 실제 BP로 같은 스크립트를 다시 돌려야 `recovery_candidate_fraction`·클래스별 nested outcome이 채워진다.

## 5. 정책 판정 (리뷰 기준 3줄)

1. **UNRECOVERABLE 비율**: 합성 팩에서 클래스 이벤트 대비 `UNRECOVERABLE`은 5/34 ≈ **14.7%**. 비율 자체만으로는 “매우 높다”고 단정하긴 어렵지만, **fluid bucket에 UNRECOVERABLE이 전부 몰린 패턴**이면 recovery default ON의 이득이 제한적일 수 있다.
2. **TRIVIAL / LOCAL_ROTATION + safe gate**: greenfield A/B는 safe gate는 통과하나 **개선 없음** → “default ON 후보”로 보기엔 근거 부족(이 케이스는 drop 자체 없음).
3. **source_kind 편차**: aggregate에서 shape vs fluid vs unknown의 class·reason·PQS 분포가 갈린다 → **source_kind별 policy**(또는 최소한 fluid에서만 stub recovery 실험) 검토 가치가 있다.

**권장 다음 액션 (코드 변경 없이)**:

- `SHAPEZ_COPY_DEBUG_DIR` 또는 채굴 솔버 NDJSON에서 **stub drop이 실제로 발생한** 3~5건을 골라 동일 aggregate + `pass12_preserve_recovery_ab.py --solver-trace … --bp-json …`로 A/B를 채운다.
- 그 결과로만 `SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY` 기본값 변경을 논의한다 (별도 플랜·승인).

## 6. 이후 진행 상황

- 합성 팩으로 aggregate·A/B 파이프라인·문서화 경로는 닫혔다.
- **완료**: 단위 회귀 수정, fixture 팩, 집계·A/B 실행, 본 정책 노트.
- **남음**: 실제 production trace로 동일 절차 1회 이상 반복 시 본 노트의 수치·결론을 갱신하면 된다.
