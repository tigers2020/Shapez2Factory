"""Stable ``event_type`` strings for replay snapshot events (A4 contract).

These values are persisted inside ``ReplayFrame.frame_payload``; treat them as a public UI/API
contract once shipped.
"""

from __future__ import annotations

# --- decode ---
EVENT_TYPE_DECODE_RAW_LOADED = "decode.raw_loaded"
EVENT_TYPE_DECODE_NORMALIZED = "decode.normalized"

# --- snapshot transaction replay (full_map per frame; UI-only) ---
EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_TRANSPORT = "replay.snapshot.cleanup_transport"
EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_EXTRACTOR = "replay.snapshot.cleanup_extractor"
EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_EXTENSION = "replay.snapshot.cleanup_extension"
EVENT_TYPE_REPLAY_SNAPSHOT_RECONSTRUCTION = "replay.snapshot.reconstruction"

# --- reconstruction ---
EVENT_TYPE_RECONSTRUCTION_BEGIN = "reconstruction.begin"
EVENT_TYPE_RECONSTRUCTION_CLEAR_OLD_LAYOUT = "reconstruction.clear_old_layout"
EVENT_TYPE_RECONSTRUCTION_SHELL_DETECTED = "reconstruction.shell_detected"
EVENT_TYPE_RECONSTRUCTION_EXTERNAL_FLOOD_FILL = "reconstruction.external_flood_fill"
EVENT_TYPE_RECONSTRUCTION_INTERNAL_VOID_DETECTED = "reconstruction.internal_void_detected"
EVENT_TYPE_RECONSTRUCTION_INTERIOR_PATCH_MARKED = "reconstruction.interior_patch_marked"
EVENT_TYPE_RECONSTRUCTION_MINEABLE_FINALIZED = "reconstruction.mineable_finalized"

# --- candidate ---
EVENT_TYPE_CANDIDATE_GENERATED = "candidate.generated"
EVENT_TYPE_CANDIDATE_INSERTED = "candidate.inserted"
EVENT_TYPE_CANDIDATE_REJECTED = "candidate.rejected"
EVENT_TYPE_CANDIDATE_REMOVED = "candidate.removed"
EVENT_TYPE_CANDIDATE_COMMITTED = "candidate.committed"

# --- routing ---
EVENT_TYPE_ROUTING_PROBE_STARTED = "routing.probe_started"
EVENT_TYPE_ROUTING_PATH_PREVIEWED = "routing.path_previewed"
EVENT_TYPE_ROUTING_FAILED = "routing.failed"
EVENT_TYPE_ROUTING_COMMITTED = "routing.committed"

# --- ga ---
EVENT_TYPE_GA_GENERATION_STARTED = "ga.generation_started"
EVENT_TYPE_GA_INDIVIDUAL_EVALUATED = "ga.individual_evaluated"
EVENT_TYPE_GA_MUTATION_APPLIED = "ga.mutation_applied"
EVENT_TYPE_GA_CROSSOVER_APPLIED = "ga.crossover_applied"
EVENT_TYPE_GA_SELECTION_APPLIED = "ga.selection_applied"
EVENT_TYPE_GA_BEST_UPDATED = "ga.best_updated"

# --- existing layout inspection (A6; UI/replay only) ---
EVENT_TYPE_EXISTING_LAYOUT_BEGIN = "existing_layout.begin"
EVENT_TYPE_EXISTING_LAYOUT_TRANSPORT_COMPONENTS_INDEXED = (
    "existing_layout.transport_components_indexed"
)
EVENT_TYPE_EXISTING_LAYOUT_EQUIPMENT_INDEXED = "existing_layout.equipment_indexed"
EVENT_TYPE_EXISTING_LAYOUT_ATTACHMENT_ANALYZED = "existing_layout.attachment_analyzed"
EVENT_TYPE_EXISTING_LAYOUT_HINTS_GENERATED = "existing_layout.hints_generated"

SNAPSHOT_EVENT_TYPES: frozenset[str] = frozenset(
    {
        EVENT_TYPE_DECODE_RAW_LOADED,
        EVENT_TYPE_DECODE_NORMALIZED,
        EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_TRANSPORT,
        EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_EXTRACTOR,
        EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_EXTENSION,
        EVENT_TYPE_REPLAY_SNAPSHOT_RECONSTRUCTION,
        EVENT_TYPE_RECONSTRUCTION_BEGIN,
        EVENT_TYPE_RECONSTRUCTION_CLEAR_OLD_LAYOUT,
        EVENT_TYPE_RECONSTRUCTION_SHELL_DETECTED,
        EVENT_TYPE_RECONSTRUCTION_EXTERNAL_FLOOD_FILL,
        EVENT_TYPE_RECONSTRUCTION_INTERNAL_VOID_DETECTED,
        EVENT_TYPE_RECONSTRUCTION_INTERIOR_PATCH_MARKED,
        EVENT_TYPE_RECONSTRUCTION_MINEABLE_FINALIZED,
        EVENT_TYPE_CANDIDATE_GENERATED,
        EVENT_TYPE_CANDIDATE_INSERTED,
        EVENT_TYPE_CANDIDATE_REJECTED,
        EVENT_TYPE_CANDIDATE_REMOVED,
        EVENT_TYPE_CANDIDATE_COMMITTED,
        EVENT_TYPE_ROUTING_PROBE_STARTED,
        EVENT_TYPE_ROUTING_PATH_PREVIEWED,
        EVENT_TYPE_ROUTING_FAILED,
        EVENT_TYPE_ROUTING_COMMITTED,
        EVENT_TYPE_GA_GENERATION_STARTED,
        EVENT_TYPE_GA_INDIVIDUAL_EVALUATED,
        EVENT_TYPE_GA_MUTATION_APPLIED,
        EVENT_TYPE_GA_CROSSOVER_APPLIED,
        EVENT_TYPE_GA_SELECTION_APPLIED,
        EVENT_TYPE_GA_BEST_UPDATED,
        EVENT_TYPE_EXISTING_LAYOUT_BEGIN,
        EVENT_TYPE_EXISTING_LAYOUT_TRANSPORT_COMPONENTS_INDEXED,
        EVENT_TYPE_EXISTING_LAYOUT_EQUIPMENT_INDEXED,
        EVENT_TYPE_EXISTING_LAYOUT_ATTACHMENT_ANALYZED,
        EVENT_TYPE_EXISTING_LAYOUT_HINTS_GENERATED,
    }
)


def is_registered_event_type(event_type: str) -> bool:
    return event_type in SNAPSHOT_EVENT_TYPES


def assert_registered_event_type(event_type: str) -> None:
    if not is_registered_event_type(event_type):
        msg = f"Unknown snapshot event_type: {event_type!r}"
        raise ValueError(msg)
