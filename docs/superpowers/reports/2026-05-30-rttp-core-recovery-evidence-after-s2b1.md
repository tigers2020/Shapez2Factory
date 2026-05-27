# RTTP Core Recovery — A0 Evidence Baseline

**Schema:** `rttp.core_recovery_evidence.v1`  
**Captured:** `2026-05-27T00:28:29.244836+00:00`  
**Gate A primary pass count:** 0

## Solver semantics

- Task A4: placement_goal_count from ReconstructionCompleteMap asteroid_field_cell_count × placement_target_percent.
- Task A5: output_stub outside traversable envelope reserved when FOT is outside mineable (FL-06); placement_goal_shortfall not goal cap.
- committed_extractor_count below placement_goal_count is expected shortfall, not placement goal failure.
- Task A6: validation fail-closed on missing_output_transport / missing_exterior_route; shortfall does not set validation_passed false.

## Results

| Slug | Run ID | Ext | Route | Ext-route | T1b | Val | Gate A | 1st stage | Primary symptom |
|------|--------|-----|-------|-----------|-----|-----|--------|-----------|-----------------|
| `rttp-core-recovery-test-map` | 230 | 58 | 153 | 0 | True | True | False | `S3` | `route_cells_zero_but_validation_passed` |
| `rttp-cert-candidate-recon-l0` | 231 | 58 | 153 | 0 | True | True | False | `S3` | `route_cells_zero_but_validation_passed` |

### Placement goal (Task A4, per slug)

- **rttp-core-recovery-test-map**: asteroid_fields=583 percent=80 goal=467 committed=20 route_cap=356 anchor_cap=67
- **rttp-cert-candidate-recon-l0**: asteroid_fields=583 percent=80 goal=467 committed=20 route_cap=356 anchor_cap=67

### Diagnostic flags (per slug)

- **rttp-core-recovery-test-map**: blocking=['S3', 'S4', 'S6'] flags=['exterior_route_missing', 'placement_goal_shortfall', 'validation_false_positive']
- **rttp-cert-candidate-recon-l0**: blocking=['S3', 'S4', 'S6'] flags=['exterior_route_missing', 'placement_goal_shortfall', 'validation_false_positive']
