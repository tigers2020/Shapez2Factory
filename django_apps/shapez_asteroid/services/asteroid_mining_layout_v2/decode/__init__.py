"""
STEP 0 decode adapters: copy string → decoded structures.

No v1 imports. Side-effect free other than explicit decode calls.
"""

from .copy_decode_adapter import ShapezCopyDecodeError, decode_copy_payload
from .existing_layout_analysis import (
    analyze_decoded_layout,
    analyze_to_context,
    compute_transport_components,
    trivial_unknown_analysis,
)

__all__ = [
    "ShapezCopyDecodeError",
    "analyze_decoded_layout",
    "analyze_to_context",
    "compute_transport_components",
    "decode_copy_payload",
    "trivial_unknown_analysis",
]
