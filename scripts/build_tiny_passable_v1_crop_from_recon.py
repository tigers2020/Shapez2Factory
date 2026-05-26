"""Crop recon-l0 around first successful commit cluster for tiny-passable-v1."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

# ruff: noqa: E402

from django_apps.asteroid_lab import models as m  # noqa: E402
from django_apps.asteroid_lab.adapters.decode_adapter import encode_copy_string  # noqa: E402
from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot  # noqa: E402
from django_apps.asteroid_lab.reconstruction.complete_map import (  # noqa: E402
    build_reconstruction_complete_map,
)
from django_apps.asteroid_lab.reconstruction.pipeline import (
    run_topology_reconstruction,  # noqa: E402
)
from django_apps.asteroid_lab.reconstruction.topology_contract import (  # noqa: E402
    decode_shapez_copy_string,
    load_reconstruction_fixture_line_pairs,
)
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (  # noqa: E402
    build_reconstruction_capacity_envelope,
)

_ANCHOR_RE = re.compile(r"^(-?\d+),(-?\d+):")


def _anchors_from_run(run_id: int) -> list[tuple[int, int]]:
    run = m.SolverRun.objects.get(pk=run_id)
    sm = (run.config_json or {}).get("solver_summary") or {}
    order = list(sm.get("commit_order") or [])
    out: list[tuple[int, int]] = []
    for cid in order[:8]:
        mch = _ANCHOR_RE.match(cid)
        if mch:
            out.append((int(mch.group(1)), int(mch.group(2))))
    return out


def _bbox(
    anchors: list[tuple[int, int]],
    *,
    pad: int = 3,
) -> tuple[int, int, int, int]:
    xs = [a[0] for a in anchors]
    ys = [a[1] for a in anchors]
    return min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad


def build_crop_copy(*, run_id: int, max_fields: int = 24) -> str:
    required_copy, _ = load_reconstruction_fixture_line_pairs()[0]
    snap = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    complete = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)

    anchors = _anchors_from_run(run_id)
    if not anchors:
        msg = "no commit anchors"
        raise ValueError(msg)
    origin = anchors[0]
    cluster = [a for a in anchors if abs(a[0] - origin[0]) + abs(a[1] - origin[1]) <= 8]
    x0, x1, y0, y1 = _bbox(cluster, pad=2)

    field_in_box = sorted(
        (x, y) for x, y in complete.field_cells if x0 <= x <= x1 and y0 <= y <= y1
    )
    if len(field_in_box) > max_fields:
        # keep closest to first anchor
        ax, ay = anchors[0]
        field_in_box = sorted(
            field_in_box,
            key=lambda c: abs(c[0] - ax) + abs(c[1] - ay),
        )[:max_fields]

    entries: list[dict[str, object]] = [
        {"X": x, "Y": y, "T": "Layout_ShapeMinerExtension"} for x, y in field_in_box
    ]
    from django_apps.asteroid_lab.snapshots.transport_components import is_transport_tile

    for cell in snap.cells:
        if abs(cell.x - origin[0]) + abs(cell.y - origin[1]) > 8:
            continue
        if cell.cell_kind in ("asteroid_shape_field", "asteroid_fluid_field"):
            continue
        t = cell.tile_type or str((cell.raw_entry_json or {}).get("T") or "")
        if not t:
            continue
        if is_transport_tile(cell):
            entries.append({"X": cell.x, "Y": cell.y, "T": t})

    root = {"V": 21, "BP": {"$type": "Island", "Entries": entries}}
    copy = encode_copy_string(root)

    # verify
    snap2 = decode_shapez_copy_string(copy)
    cleanup2 = deconstruct_snapshot(snap2)
    recon2 = run_topology_reconstruction(cleanup2)
    complete2 = build_reconstruction_complete_map(cleanup=cleanup2, recon=recon2)
    env = build_reconstruction_capacity_envelope(complete_map=complete2)
    print(
        "bbox",
        x0,
        x1,
        y0,
        y1,
        "fields",
        complete2.shape_field_cell_count,
        "max",
        env["by_resource"]["shape"]["max_throughput_per_min"],
        "entries",
        len(entries),
    )
    return copy


def main() -> None:
    proj = m.AsteroidProject.objects.filter(slug="rttp-cert-candidate-recon-l0").first()
    if proj is None:
        msg = "recon-l0 project missing"
        raise SystemExit(msg)
    run = m.SolverRun.objects.filter(project_id=proj.pk).order_by("-id").first()
    if run is None:
        msg = "no solver run"
        raise SystemExit(msg)
    print(build_crop_copy(run_id=int(run.pk)))


if __name__ == "__main__":
    main()
