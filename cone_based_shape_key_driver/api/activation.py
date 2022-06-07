
from typing import TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import FloatProperty
from ..lib.curve_mapping import BCLMAP_CurveManager
if TYPE_CHECKING:
    from bpy.types import Context, ShapeKey


def activation_radius_update_handler(activation: 'ConeBasedShapeKeyDriverActivation',
                                     _: 'Context') -> None:
    path: str = activation.path_from_id()
    activation.id_data.path_resolve(path.rpartition(".")[0]).update()


def activation_target_update_handler(activation: 'ConeBasedShapeKeyDriverActivation',
                                     _: 'Context') -> None:
    path: str = activation.path_from_id()
    activation.id_data.path_resolve(path.rpartition(".")[0]).update()


class ConeBasedShapeKeyDriverActivation(BCLMAP_CurveManager, PropertyGroup):

    radius: FloatProperty(
        name="Radius",
        description=("The cone driver's radius. Controls how close to the center "
                     "the target's rotation is before the shape key is activated."),
        min=0.0,
        max=1.0,
        default=0.2,
        precision=3,
        options=set(),
        update=activation_radius_update_handler,
        )

    target: FloatProperty(
        name="Goal",
        description="The value of the shape key when fully activated by the driver",
        default=1.0,
        options=set(),
        update=activation_target_update_handler
        )

    def update(self) -> None:
        super().update()
        self.id_data.path_resolve(self.path_from_id().rpartition(".")[0]).update()

    def __init__(self, shape: 'ShapeKey') -> None:
        self["value"] = shape.value
        super().__init__(interpolation='QUAD', easing='EASE_IN_OUT')
