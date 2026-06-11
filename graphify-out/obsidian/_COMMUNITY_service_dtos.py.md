---
type: community
cohesion: 0.20
members: 10
---

# service_dtos.py

**Cohesion:** 0.20 - loosely connected
**Members:** 10 nodes

## Members
- [[Aggregated decoded blueprint for UI overlay and replay decode frames.]] - rationale - src/shapez2_factory/domain/asteroid_lab/service_dtos.py
- [[Blueprint JSON ready to persist on ``AsteroidMapInput.decoded_json``.]] - rationale - src/shapez2_factory/domain/asteroid_lab/service_dtos.py
- [[Current persisted playback transport state (UI only).]] - rationale - src/shapez2_factory/domain/asteroid_lab/service_dtos.py
- [[DecodedBlueprintSnapshotDTO_1]] - code - src/shapez2_factory/domain/asteroid_lab/service_dtos.py
- [[NormalizedBlueprintDTO_1]] - code - src/shapez2_factory/domain/asteroid_lab/service_dtos.py
- [[PlaybackSessionDTO_1]] - code - src/shapez2_factory/domain/asteroid_lab/service_dtos.py
- [[Result row after persisting a snapshot as ``ReplayFrame`` (UI playback artifact)]] - rationale - src/shapez2_factory/domain/asteroid_lab/service_dtos.py
- [[Service boundary DTOs (no Django imports).  Replay rows, playback sessions, an]] - rationale - src/shapez2_factory/domain/asteroid_lab/service_dtos.py
- [[SnapshotFrameDTO_1]] - code - src/shapez2_factory/domain/asteroid_lab/service_dtos.py
- [[service_dtos.py]] - code - src/shapez2_factory/domain/asteroid_lab/service_dtos.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/service_dtospy
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_get_topology_modal_payload()]]
- 1 edge to [[_COMMUNITY_CreateProjectFromCopyCodeResultDTO]]
- 1 edge to [[_COMMUNITY_SolverRunDTO]]
- 1 edge to [[_COMMUNITY_ReplayFrameAppendDTO]]
- 1 edge to [[_COMMUNITY_ReplayFrameRowDTO]]
- 1 edge to [[_COMMUNITY_ReplayTrackPayloadDTO]]
- 1 edge to [[_COMMUNITY_ReplayTrackRefDTO]]
- 1 edge to [[_COMMUNITY_PlaybackPatchDTO]]
- 1 edge to [[_COMMUNITY_TopologyModalResultDTO]]
- 1 edge to [[_COMMUNITY_RawDecodedBlueprintDTO]]
- 1 edge to [[_COMMUNITY_ExistingTransportComponentDTO]]
- 1 edge to [[_COMMUNITY_ExistingEquipmentDTO]]
- 1 edge to [[_COMMUNITY_EquipmentAttachmentDTO]]
- 1 edge to [[_COMMUNITY_ExistingLayoutInspectionDTO]]
- 1 edge to [[_COMMUNITY_SnapshotEventDTO]]
- 1 edge to [[_COMMUNITY_ReplayRecordingPolicyDTO]]
- 1 edge to [[_COMMUNITY_InitialReplayPipelineResultDTO]]

## Top bridge nodes
- [[service_dtos.py]] - degree 24, connects to 17 communities