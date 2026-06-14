"""Default layout_t for exterior connector sprites (base tile; rotation separate)."""


def default_exterior_connector_layout_t(*, resource_kind: str) -> str:
    if resource_kind == "fluid":
        return "SpacePipe_Forward"
    return "SpaceBelt_Forward"


__all__ = ["default_exterior_connector_layout_t"]
