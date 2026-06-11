---
source_file: "django_apps/asteroid_lab/replay/timeline_composer.py"
type: "code"
community: "compose_replay_timeline()"
location: "L81"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/compose_replay_timeline
---

# compose_replay_timeline()

## Connections
- [[Assign global ``frame_index`` 0..n-1; truncate when over max_frames.      Wh]] - `rationale_for` [EXTRACTED]
- [[ReplayTimelineFrame]] - `references` [EXTRACTED]
- [[_retain_keyframes_and_tail()]] - `calls` [EXTRACTED]
- [[build_lab_replay_frames_for_project()]] - `calls` [INFERRED]
- [[timeline_composer.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/compose_replay_timeline