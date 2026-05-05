from dataclasses import dataclass
from enum import StrEnum


class OperationType(StrEnum):
    CUTTER = "cutter"
    HALF_DESTROYER = "half_destroyer"
    SPLITTER = "splitter"
    SWAPPER = "swapper"

    ROTATE_CW = "rotate_cw"
    ROTATE_CCW = "rotate_ccw"
    ROTATE_180 = "rotate_180"

    STACKER = "stacker"
    PAINTER = "painter"
    COLOR_MIXER = "color_mixer"
    PIN_PUSHER = "pin_pusher"
    CRYSTAL_GENERATOR = "crystal_generator"


@dataclass(frozen=True, slots=True)
class OperationDefinition:
    type: OperationType
    label: str
    icon: str
    input_count: int
    output_count: int
    description: str
