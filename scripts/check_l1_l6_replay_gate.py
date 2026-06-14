#!/usr/bin/env python3
"""Loop gate: L1–L6 Lab replay for documents/testmap/original_map.txt."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def main() -> int:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()

    from django_apps.asteroid_lab import models as m
    from django_apps.asteroid_lab.services import project_service
    from django_apps.asteroid_lab.services.artifact_replay_viewer_compose import (
        lab_replay_frames_are_renderable,
    )
    from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
        build_lab_replay_frames_for_project,
    )
    from django_apps.asteroid_lab.services.replay_pipeline_service import (
        build_initial_replay_for_map_input,
    )
    from shapez2_factory.adapters.asteroid_lab.runtime_wires.envelope import (
        MANIFEST_PATH_KEY,
        RUNTIME_WIRES_ARTIFACT_REL_PATH,
    )

    code = (_REPO / "documents" / "testmap" / "original_map.txt").read_text(encoding="utf-8").strip()
    slug = project_service.resolve_or_create_project_slug_for_copy_code(
        code,
        source_label="loop-l1l6-replay",
    )
    proj = m.AsteroidProject.objects.get(slug=slug)
    project_id = int(proj.pk)
    inp = (
        m.AsteroidMapInput.objects.filter(project_id=project_id).order_by("-id").first()
    )
    if inp is None:
        print("OVERALL_OK=false reason=no_map_input")
        return 1

    l1 = build_initial_replay_for_map_input(int(inp.pk), force=True)
    run = (
        m.SolverRun.objects.filter(project_id=project_id, lifecycle_status="succeeded")
        .exclude(artifact_root="")
        .order_by("-id")
        .first()
    )
    if run is None:
        print("OVERALL_OK=false reason=no_succeeded_solver_run")
        return 1

    root = Path(str(run.artifact_root))
    wires_path = root / RUNTIME_WIRES_ARTIFACT_REL_PATH
    manifest_paths = {}
    manifest_file = root / "manifest.json"
    if manifest_file.is_file():
        import json

        manifest_paths = json.loads(manifest_file.read_text(encoding="utf-8")).get("paths") or {}

    frames, metrics = build_lab_replay_frames_for_project(project_id, solver_run_id=int(run.pk))
    expected_layers = {
        "layer_01_reconstruction",
        "layer_02_exterior_transport",
        "layer_03_rim_greedy_placement",
        "layer_04_inner_pattern_fill",
        "layer_05_transport_routing",
        "layer_06_commit_validate",
    }
    found_layers: set[str] = set()
    for fr in frames:
        insp = fr.get("inspector") if isinstance(fr.get("inspector"), dict) else {}
        slug_hint = str(insp.get("layer_slug") or fr.get("title") or "")
        for layer in expected_layers:
            if layer in slug_hint or layer.replace("_", " ") in str(fr.get("title") or ""):
                found_layers.add(layer)
        phase = str(fr.get("phase") or "")
        et = str(fr.get("event_type") or "")
        if phase in {"decode", "reconstruction"}:
            found_layers.add("layer_01_reconstruction")
        if "exterior_transport" in et:
            found_layers.add("layer_02_exterior_transport")
        if "layer03" in et:
            found_layers.add("layer_03_rim_greedy_placement")
        if "pattern" in et:
            found_layers.add("layer_04_inner_pattern_fill")
        if "transport_routing" in et:
            found_layers.add("layer_05_transport_routing")
        if "validation" in et:
            found_layers.add("layer_06_commit_validate")

    missing_layers = sorted(expected_layers - found_layers)
    diagnostic = metrics.get("diagnostic_reason")
    ok = (
        l1.status == "ok"
        and wires_path.is_file()
        and MANIFEST_PATH_KEY in manifest_paths
        and lab_replay_frames_are_renderable(frames)
        and diagnostic in (None, "")
        and not missing_layers
        and len(frames) >= 7
    )

    print(f"project={slug} l1_status={l1.status} frames={len(frames)} diagnostic={diagnostic!r}")
    print(f"wires_file={wires_path.is_file()} missing_layers={missing_layers}")
    print(f"OVERALL_OK={'true' if ok else 'false'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
