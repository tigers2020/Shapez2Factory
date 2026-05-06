from types import MappingProxyType

from django_apps.shapez_solver.domain.operations import OperationDefinition, OperationType

OPERATION_CATALOG = MappingProxyType(
    {
        OperationType.CUTTER: OperationDefinition(
            type=OperationType.CUTTER,
            label="Cutter",
            icon="cutter.png",
            input_count=1,
            output_count=2,
            description="Cuts the shape into two halves.",
        ),
        OperationType.HALF_DESTROYER: OperationDefinition(
            type=OperationType.HALF_DESTROYER,
            label="Half Destroyer",
            icon="half-destroyer.png",
            input_count=1,
            output_count=1,
            description="Keeps one half of the shape and destroys the other half.",
        ),
        OperationType.SPLITTER: OperationDefinition(
            type=OperationType.SPLITTER,
            label="Splitter",
            icon="splitter.png",
            input_count=1,
            output_count=2,
            description="Splits the processed shape flow into separate outputs.",
        ),
        OperationType.SWAPPER: OperationDefinition(
            type=OperationType.SWAPPER,
            label="Swapper",
            icon="swapper.png",
            input_count=2,
            output_count=2,
            description="Swaps halves between two input shapes.",
        ),
        OperationType.ROTATE_CW: OperationDefinition(
            type=OperationType.ROTATE_CW,
            label="Rotate CW",
            icon="rotator-cw.png",
            input_count=1,
            output_count=1,
            description="Rotates the full shape 90 degrees clockwise.",
        ),
        OperationType.ROTATE_CCW: OperationDefinition(
            type=OperationType.ROTATE_CCW,
            label="Rotate CCW",
            icon="rotator-ccw.png",
            input_count=1,
            output_count=1,
            description="Rotates the full shape 90 degrees counterclockwise.",
        ),
        OperationType.ROTATE_180: OperationDefinition(
            type=OperationType.ROTATE_180,
            label="Rotate 180",
            icon="rotator-180.png",
            input_count=1,
            output_count=1,
            description="Rotates the full shape 180 degrees.",
        ),
        OperationType.STACKER: OperationDefinition(
            type=OperationType.STACKER,
            label="Stacker",
            icon="stacker.png",
            input_count=2,
            output_count=1,
            description=(
                "Stacks one shape on top of another shape. "
                "Recipe graph quantity on the output is the sum of the two input quantities."
            ),
        ),
        OperationType.MERGE: OperationDefinition(
            type=OperationType.MERGE,
            label="Merge",
            icon="merger.png",
            input_count=2,
            output_count=1,
            description=(
                "When both inputs are the same canonical shape, outputs that shape once "
                "with quantity equal to the sum of input quantities."
            ),
        ),
        OperationType.PAINTER: OperationDefinition(
            type=OperationType.PAINTER,
            label="Painter",
            icon="painter.png",
            input_count=2,
            output_count=1,
            description="Paints the shape using pure color fluid from the fluid input.",
        ),
        OperationType.COLOR_MIXER: OperationDefinition(
            type=OperationType.COLOR_MIXER,
            label="Color Mixer",
            icon="color-mixer.png",
            input_count=2,
            output_count=1,
            description="Mixes two pure color fluids into one fluid output.",
        ),
        OperationType.PIN_PUSHER: OperationDefinition(
            type=OperationType.PIN_PUSHER,
            label="Pin Pusher",
            icon="pin-pusher.png",
            input_count=1,
            output_count=1,
            description="Adds pins below a shape to lift the shape upward.",
        ),
        OperationType.CRYSTAL_GENERATOR: OperationDefinition(
            type=OperationType.CRYSTAL_GENERATOR,
            label="Crystal Generator",
            icon="crystal-generator.png",
            input_count=2,
            output_count=1,
            description=(
                "Fills gaps and pins with crystals using crystal_color on the node, "
                "or fluid (in-1) + target shape (in) like the painter."
            ),
        ),
    }
)
