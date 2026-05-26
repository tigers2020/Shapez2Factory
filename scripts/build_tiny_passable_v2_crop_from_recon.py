"""Track B-3F-v2: v1 bbox crop with lower field cap (preserve commit geometry)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

_V1_REFERENCE_RUN_ID = 136
_DEFAULT_MAX_FIELDS = 5


def _load_v1_builder():
    spec = importlib.util.spec_from_file_location(
        "build_tiny_passable_v1_crop_from_recon",
        Path(__file__).resolve().parent / "build_tiny_passable_v1_crop_from_recon.py",
    )
    if spec.loader is None:
        msg = "v1 crop builder load failed"
        raise RuntimeError(msg)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_crop_v2_copy(
    *,
    run_id: int = _V1_REFERENCE_RUN_ID,
    max_fields: int = _DEFAULT_MAX_FIELDS,
) -> str:
    """Same bbox/cluster crop as v1; cap shape_field_cell_count for T2 denominator."""
    return _load_v1_builder().build_crop_copy(run_id=run_id, max_fields=max_fields)


def main() -> None:
    print(build_crop_v2_copy())


if __name__ == "__main__":
    main()
