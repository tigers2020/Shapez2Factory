---
type: community
cohesion: 0.16
members: 21
---

# analyze_pattern_lab_shape()

**Cohesion:** 0.16 - loosely connected
**Members:** 21 nodes

## Members
- [[Pattern Lab 화면에 표시할 분석 결과.]] - rationale - django_apps/shapez_solver/services/pattern_lab_service.py
- [[PatternCatalogRepository_1]] - code - django_apps/shapez_solver/services/pattern_lab_service.py
- [[PatternLabAnalysis]] - code - django_apps/shapez_solver/services/pattern_lab_service.py
- [[RotationVariant]] - code - django_apps/shapez_solver/services/pattern_lab_service.py
- [[SymbolMapEntry]] - code - django_apps/shapez_solver/services/pattern_lab_service.py
- [[_build_rotation_variants()]] - code - django_apps/shapez_solver/services/pattern_lab_service.py
- [[_build_symbol_map()]] - code - django_apps/shapez_solver/services/pattern_lab_service.py
- [[_error_result()]] - code - django_apps/shapez_solver/services/pattern_lab_service.py
- [[_paint_shape()]] - code - django_apps/shapez_solver/services/pattern_lab_service.py
- [[_shape_tokens()]] - code - django_apps/shapez_solver/services/pattern_lab_service.py
- [[_structural_family_mismatch_for_layer_code()]] - code - django_apps/shapez_solver/services/pattern_lab_service.py
- [[analyze_pattern_lab_shape()]] - code - django_apps/shapez_solver/services/pattern_lab_service.py
- [[canonical  무채색 구조 코드  사분면 회전 variant로     ``family_signature``와의 불일치를 설명한다. 일]] - rationale - django_apps/shapez_solver/services/pattern_lab_service.py
- [[explain_pattern_family_mismatch()]] - code - django_apps/shapez_solver/services/pattern_lab_service.py
- [[pattern_lab_service.py]] - code - django_apps/shapez_solver/services/pattern_lab_service.py
- [[shape code를 pattern catalog 관점에서 분석한다.]] - rationale - django_apps/shapez_solver/services/pattern_lab_service.py
- [[shape_from_pattern()]] - code - django_apps/shapez_core/services/shape_codec.py
- [[symbolic signature 문자와 실제 shape token의 대응.]] - rationale - django_apps/shapez_solver/services/pattern_lab_service.py
- [[단일 레이어(8자)에 대해 family와 불일치 시 이유 문자열, 아니면 None.]] - rationale - django_apps/shapez_solver/services/pattern_lab_service.py
- [[레이어의 비어 있지 않은 사분면 색만 바꾼다 (무채색 골격 코드용).]] - rationale - django_apps/shapez_solver/services/pattern_lab_service.py
- [[사분면 회전 variant와 해당 signature.]] - rationale - django_apps/shapez_solver/services/pattern_lab_service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/analyze_pattern_lab_shape
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_pattern_signature()]]
- 3 edges to [[_COMMUNITY_ShapeCodeParseError]]
- 2 edges to [[_COMMUNITY_Shape]]
- 2 edges to [[_COMMUNITY_build_shape_render_scene()]]
- 2 edges to [[_COMMUNITY_shape_codec.py]]
- 1 edge to [[_COMMUNITY_parse_shape()]]
- 1 edge to [[_COMMUNITY_public_pages.py]]

## Top bridge nodes
- [[shape_from_pattern()]] - degree 9, connects to 4 communities
- [[analyze_pattern_lab_shape()]] - degree 11, connects to 3 communities
- [[_structural_family_mismatch_for_layer_code()]] - degree 8, connects to 2 communities
- [[explain_pattern_family_mismatch()]] - degree 6, connects to 2 communities
- [[_build_rotation_variants()]] - degree 6, connects to 1 community