# Post-reclaim Pass3 route-length ratio

메인 Pass3의 P3-E3b 원자 커밋은 `MAX_ROUTE_LENGTH_RATIO`(1.35, `ceil(baseline * ratio)`)로 경로 길이를 제한한다.

P4 이후 **post-reclaim Pass3 1회 재실행**에 한해, 메인 Pass3에서 확보한 `pass3_internal_transport_saved`에 비례해 상한을 완화한다.

- 공식: `min(POST_RECLAIM_P3E3_ROUTE_RATIO_BASE + saved * POST_RECLAIM_P3E3_ROUTE_RATIO_K, POST_RECLAIM_P3E3_ROUTE_RATIO_CAP)`
- 상수는 `django_apps/shapez_asteroid/services/asteroid_mining_layout/foundation/constants.py`에 정의한다.
- NDJSON·요약에는 `p3e3_route_length_ratio_cap`, `p3e3_route_allowed_max_length`, `p3e3_route_length_slack_cells`로 게이트와의 차이를 바로 읽을 수 있다.
- P4 직후 Pass3 절감 대비 reclaim이 내부 transport를 얼마나 소비했는지는 `pass3_reclaim_projected_net_internal_saved`(= `pass3_internal_transport_saved` − `p4_reclaim_loop_internal_transport_cumulative_added`)로 요약한다.
