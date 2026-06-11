---
type: community
cohesion: 0.20
members: 14
---

# shapez_copy_decode.py

**Cohesion:** 0.20 - loosely connected
**Members:** 14 nodes

## Members
- [[Decode Shapez 2 in-game copy strings (blueprint  island payload).  Pipeline]] - rationale - django_apps/shapez_core/services/shapez_copy_decode.py
- [[Decode a Shapez 2 copy code into a JSON object (``dict``).      Whitespace any]] - rationale - django_apps/shapez_core/services/shapez_copy_decode.py
- [[Decode like func`decode_shapez2_copy` but record pipeline steps for UI playbac]] - rationale - django_apps/shapez_core/services/shapez_copy_decode.py
- [[DecodeTraceResult]] - code - django_apps/shapez_core/services/shapez_copy_decode.py
- [[Drop trailing characters outside standard Base64 (e.g. shelleditor ``$``).]] - rationale - django_apps/shapez_core/services/shapez_copy_decode.py
- [[Invalid copy string, payload, compression, or JSON.]] - rationale - django_apps/shapez_core/services/shapez_copy_decode.py
- [[Pad standard Base64 so length is a multiple of four.]] - rationale - django_apps/shapez_core/services/shapez_copy_decode.py
- [[Result of func`decode_shapez2_copy_trace` (success or failure with partial ste]] - rationale - django_apps/shapez_core/services/shapez_copy_decode.py
- [[ShapezCopyDecodeError]] - code - django_apps/shapez_core/services/shapez_copy_decode.py
- [[_pad_base64()]] - code - django_apps/shapez_core/services/shapez_copy_decode.py
- [[_trim_trailing_non_base64()]] - code - django_apps/shapez_core/services/shapez_copy_decode.py
- [[decode_shapez2_copy()]] - code - django_apps/shapez_core/services/shapez_copy_decode.py
- [[decode_shapez2_copy_trace()]] - code - django_apps/shapez_core/services/shapez_copy_decode.py
- [[shapez_copy_decode.py]] - code - django_apps/shapez_core/services/shapez_copy_decode.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/shapez_copy_decodepy
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_Any]]
- 1 edge to [[_COMMUNITY_ValueError]]

## Top bridge nodes
- [[decode_shapez2_copy()]] - degree 5, connects to 1 community
- [[ShapezCopyDecodeError]] - degree 4, connects to 1 community