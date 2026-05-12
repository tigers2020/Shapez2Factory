# Pass12 `recoverability_class` 계약 (2026-05-11)

## 목적

`PreserveDropReason`(왜 drop됐는지) 위에 **salvage 가능성 티어** `recoverability_class`를 얹어 운영·A/B에서
`UNRECOVERABLE`과 “휴리스틱/라우팅 부족”을 구분한다.

## 범위

- `pass12_merged_layout_seed`: drop 상세 dict에 `recoverability_class` 필드, 집계
  `pass12_recoverability_class_counts`.
- 초기 매핑은 **정적 테이블**(trace 기반 조정 가능). ML·동적 학습 없음.
- `SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY=True`일 때만 **merged-seed miner 순서**를
  nearest-hop 근접도로 정렬(라우터 penalty 비변경).

## 가정

- `nearest_same_kind_transport_hops`는 기존 BFS trace와 동일 계약.
- `MAX_PASS12_RECOVERY_BFS_HOPS`는 recovery 예산 상한과 정렬 기준에 공통 사용.

## 검증

- `tests/unit/shapez_asteroid/test_pass12_preserve_drop_and_recovery.py` (매핑·히스토그램).

## 승인

로드맵 구현 단계에서 본 문서로 스키마 확장 게이트를 충족한다.
