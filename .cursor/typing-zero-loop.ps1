# Dynamic typing-zero chain: inventory-driven, no fixed sleep, no per-slice CI.
# Canon: documents/ai/manuals/typing_boundary_layers.md
# Re-arm immediately after each slice (local gates only). Full test + Bugbot when Any=0.
Set-Location $PSScriptRoot\..
python scripts/typing_zero_next_wake.py
