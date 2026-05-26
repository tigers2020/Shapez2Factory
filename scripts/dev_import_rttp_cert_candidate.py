"""One-off: import RTTP pass-capable certification candidate maps (dev DB only)."""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import os
import sys
from pathlib import Path


def _bootstrap_django() -> None:
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()


def tiny_island_copy() -> str:
    from django_apps.asteroid_lab.adapters.decode_adapter import encode_copy_string

    return encode_copy_string(
        {
            "V": 21,
            "BP": {
                "$type": "Island",
                "Entries": [
                    {"X": 1, "Y": 0, "T": "Layout_FluidMiner"},
                    {"X": 2, "Y": 0, "T": "Layout_FluidMinerExtension"},
                ],
            },
        }
    )


def tiny_passable_v1_copy() -> str:
    """recon-l0 crop around first commit cluster (route-known geometry)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "build_tiny_passable_v1_crop_from_recon",
        Path(__file__).resolve().parent / "build_tiny_passable_v1_crop_from_recon.py",
    )
    if spec.loader is None:
        msg = "crop builder load failed"
        raise RuntimeError(msg)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    from django_apps.asteroid_lab import models as m

    proj = m.AsteroidProject.objects.filter(slug="rttp-cert-candidate-recon-l0").first()
    if proj is None:
        msg = "import recon-l0 before tiny-passable-v1"
        raise RuntimeError(msg)
    run = m.SolverRun.objects.filter(project_id=proj.pk).order_by("-id").first()
    if run is None:
        msg = "run_solver on recon-l0 before tiny-passable-v1"
        raise RuntimeError(msg)
    return mod.build_crop_copy(run_id=int(run.pk), max_fields=12)


def tiny_passable_v2_copy() -> str:
    """v1 commit anchors; 4–5 field cells + nearby trunk (B-3F-v2)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "build_tiny_passable_v2_crop_from_recon",
        Path(__file__).resolve().parent / "build_tiny_passable_v2_crop_from_recon.py",
    )
    if spec.loader is None:
        msg = "v2 crop builder load failed"
        raise RuntimeError(msg)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_crop_v2_copy(run_id=mod._V1_REFERENCE_RUN_ID, max_fields=5)


def tiny_passable_l0_copy() -> str:
    """4-field shape ring + exterior belt trunk (Track B-3F ops fixture)."""
    from django_apps.asteroid_lab.adapters.decode_adapter import encode_copy_string

    return encode_copy_string(
        {
            "V": 21,
            "BP": {
                "$type": "Island",
                "Entries": [
                    {"X": 2, "Y": 0, "T": "Layout_ProMiner"},
                    {"X": 3, "Y": 0, "T": "SpaceBelt_Right"},
                    {"X": 4, "Y": 0, "T": "SpaceBelt_Right"},
                    {"X": 1, "Y": 1, "T": "UnknownTile_A"},
                    {"X": 2, "Y": 1, "T": "UnknownTile_B"},
                    {"X": 3, "Y": 1, "T": "UnknownTile_C"},
                    {"X": 1, "Y": 2, "T": "UnknownTile_D"},
                    {"X": 3, "Y": 2, "T": "UnknownTile_E"},
                    {"X": 1, "Y": 3, "T": "UnknownTile_F"},
                    {"X": 2, "Y": 3, "T": "UnknownTile_G"},
                    {"X": 3, "Y": 3, "T": "UnknownTile_H"},
                ],
            },
        }
    )


def minimal_fluid_miner_copy() -> str:
    from django_apps.asteroid_lab.adapters.decode_adapter import encode_copy_string

    return encode_copy_string(
        {
            "V": 21,
            "BP": {
                "$type": "Island",
                "Entries": [{"X": 0, "Y": 0, "T": "Layout_FluidMiner"}],
            },
        }
    )


def minimal_valid_copy() -> str:
    payload = json.dumps(
        {
            "V": 1,
            "BP": {
                "$type": "Island",
                "Entries": [
                    {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                    {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
                ],
            },
        },
        separators=(",", ":"),
    ).encode("utf-8")
    b64 = base64.b64encode(gzip.compress(payload)).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


def import_map(*, slug: str, name: str, copy: str, replace: bool) -> int:
    from django_apps.asteroid_lab import models as m
    from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input

    proj, created = m.AsteroidProject.objects.get_or_create(
        slug=slug,
        defaults={"name": name},
    )
    if not created and replace:
        m.AsteroidMapInput.objects.filter(project_id=proj.pk).delete()
    elif not created and proj.map_inputs.exists():
        print(f"skip existing slug={slug} project_id={proj.pk}")
        return int(proj.pk)
    create_copy_code_map_input(proj, copy)
    print(f"imported slug={slug} project_id={proj.pk} created={created}")
    return int(proj.pk)


def main() -> None:
    from django_apps.asteroid_lab.reconstruction.topology_contract import (
        load_reconstruction_fixture_line_pairs,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--variant",
        choices=(
            "minimal",
            "tiny-island",
            "minimal-fluid",
            "recon-l0",
            "recon-l1",
            "tiny-passable-l0",
            "tiny-passable-v1",
            "tiny-passable-v2",
            "all",
        ),
        default="all",
    )
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    if args.variant in ("minimal", "all"):
        import_map(
            slug="rttp-cert-candidate-minimal",
            name="RTTP cert candidate (minimal valid copy)",
            copy=minimal_valid_copy(),
            replace=args.replace,
        )
    if args.variant in ("tiny-island", "all"):
        import_map(
            slug="rttp-cert-candidate-tiny-island",
            name="RTTP cert candidate (tiny island fluid)",
            copy=tiny_island_copy(),
            replace=args.replace,
        )
    if args.variant in ("minimal-fluid", "all"):
        import_map(
            slug="rttp-cert-candidate-minimal-fluid",
            name="RTTP cert candidate (single fluid miner)",
            copy=minimal_fluid_miner_copy(),
            replace=args.replace,
        )
    if args.variant in ("recon-l0", "all"):
        required_copy, _ = load_reconstruction_fixture_line_pairs()[0]
        import_map(
            slug="rttp-cert-candidate-recon-l0",
            name="RTTP cert candidate (recon fixture L0)",
            copy=required_copy,
            replace=args.replace,
        )
    if args.variant in ("recon-l1", "all"):
        required_copy, _ = load_reconstruction_fixture_line_pairs()[1]
        import_map(
            slug="rttp-cert-candidate-recon-l1",
            name="RTTP cert candidate (recon fixture L1 / canon hole)",
            copy=required_copy,
            replace=args.replace,
        )
    if args.variant in ("tiny-passable-l0", "all"):
        import_map(
            slug="rttp-cert-candidate-tiny-passable-l0",
            name="RTTP cert tiny-passable L0 (4-field shape ring)",
            copy=tiny_passable_l0_copy(),
            replace=args.replace,
        )
    if args.variant in ("tiny-passable-v1", "all"):
        import_map(
            slug="rttp-cert-candidate-tiny-passable-v1",
            name="RTTP cert tiny-passable v1 (recon-l0 crop 12 fields)",
            copy=tiny_passable_v1_copy(),
            replace=args.replace,
        )
    if args.variant in ("tiny-passable-v2", "all"):
        import_map(
            slug="rttp-cert-candidate-tiny-passable-v2",
            name="RTTP cert tiny-passable v2 (commit-anchor crop)",
            copy=tiny_passable_v2_copy(),
            replace=args.replace,
        )


if __name__ == "__main__":
    _bootstrap_django()
    main()
