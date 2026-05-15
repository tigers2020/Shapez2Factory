# 문서 정리 계획

> 생성: 2026-05-15. 이번 자동화는 삭제/이동 없이 low-risk README와 감사 보고서만 생성/갱신했다.

## 유지할 파일

- `documents/README.md`
- `documents/Algorithm/README.md`
- `documents/Algorithm/mining_solver_cursor_sessions/README.md`
- `documents/Algorithm/mining_solver_cursor_sessions/01_project_overview.md` through `14_step10_replay_ui.md`
- `documents/index/document_lifecycle.md`
- `documents/index/document_inventory.md`
- `documents/adr/*.md`
- `documents/ai/START_HERE.md`, `documents/ai/manuals/*.md`
- `documents/reports/documentation_audit/*.md`

## 이동 후보

| source | target | risk | reason |
|---|---|---|---|
| `documents/Algorithm/mining_solver_cursor_sessions/14_step4_routing_dto_refactor_inventory.md` | `documents/reports/documentation_audit/` 또는 `documents/Algorithm/mining_solver_cursor_sessions/supplemental/` | medium | canonical numbering collision. 사람 검토 필요. |
| `documents/Algorithm/mining_solver_cursor_sessions/15_step4_telemetry_field_semantics.md` | `documents/Algorithm/mining_solver_cursor_sessions/supplemental/` | medium | telemetry/output semantics 보조문서로 분리 권장. |
| `documents/plans/plan_pass12_*.md` | `documents/archive/2026-05-mining-layout-v1-era/plans/` 또는 `documents/plans/` 유지 | medium | active 여부 불명. current plan과 대조 필요. |
| root `v2_behavior_artifact_*.json` | `var/shapez_copy_debug/` 또는 삭제 | low | generated artifact. 사람 승인 후 정리. |

## archive 유지 후보

- `documents/archive/2026-05-mining-layout-v1-era/**`: 현재처럼 historical-only로 유지.
- `documents/archive/completed-implementation/**`: 완료 구현 history로 유지.
- `documents/refactory/README.md`: redirect만 유지하고 본문은 archive link로 제한.

## 사람 검토가 필요한 파일

- `documents/Algorithm/mining_solver_cursor_sessions/14_step4_routing_dto_refactor_inventory.md`
- `documents/Algorithm/mining_solver_cursor_sessions/15_step4_telemetry_field_semantics.md`
- `documents/ai/checklist.md`의 v1/v2 혼재 sections
- `documents/plans/plan_pass12_*.md`
- `documents/plans/plan_pass2_island_fallback_gate_2026-05-13.md`
- `documents/research/runtime_semantic_verification.md`
- `documents/meta/*.md`

## 깨진 링크 수정 후보

- archive 문서 안의 `../../django_apps/.../asteroid_mining_layout/` 링크는 현재 tree에 없는 v1 경로를 가리킬 수 있다. archive 내부에서는 historical broken link로 허용하거나 README에 명시한다.
- `documents/Algorithm/mining_solver_cursor_sessions/README.md`의 `../Shapez2 Asteroid Mining Solver logic.md` 링크는 현재 파일이 archive로 이동되어 있으면 archive 경로로만 유지해야 한다.
- `mdc:` 링크는 Cursor 전용이다. 일반 Markdown link checker에서는 실패할 수 있으므로 문서 검증에서 별도 예외 처리한다.

## 업데이트할 index 파일

- `documents/README.md`: canonical/plan/report/history/generated-output read order 유지.
- `documents/Algorithm/README.md`: STEP order와 supplemental 문서 분리.
- `documents/reports/README.md`: documentation audit 링크 추가 권장.
- `documents/index/document_inventory.md`: 이번 `document_inventory.md` 결과를 반영할지 별도 검토.

## 추천 semantic commit grouping

1. `docs(audit): add repository documentation audit reports`
   - `documents/reports/documentation_audit/*`
2. `docs(index): clarify documents authority hierarchy`
   - `documents/README.md`
   - `documents/Algorithm/README.md`
   - `documents/reports/documentation_audit/README.md`
3. `docs(archive): label v1 mining layout references historical-only`
   - 사람 승인 후 archive/readme only.
4. `chore(artifacts): remove or relocate generated behavior artifacts`
   - 사람 승인 후 root `v2_behavior_artifact_*.json` 처리.

## 적용 범위

이번 run에서 적용한 safe changes:

- 감사 보고서 디렉터리 생성.
- repository map, document inventory, authority matrix, code-doc crosscheck, obsolete candidates, cleanup plan 생성.
- top-level documents README와 Algorithm README를 정본 라우팅 중심으로 갱신/생성.

이번 run에서 하지 않은 것:

- production code 수정.
- tests 수정.
- solver algorithm behavior 수정.
- 문서 삭제 또는 물리적 이동.
