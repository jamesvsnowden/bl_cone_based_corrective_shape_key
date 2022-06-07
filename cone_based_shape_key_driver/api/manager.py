
from typing import Optional, Tuple, TYPE_CHECKING
from uuid import uuid4
from bpy.types import Object, PropertyGroup
from bpy.props import (BoolProperty,
                       EnumProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       PointerProperty,
                       StringProperty)
from mathutils import Euler, Quaternion
from ..lib.driver_utils import driver_find, driver_ensure, driver_variables_empty
from ..lib.curve_mapping import to_bezier, keyframe_points_assign
from ..lib.utils import direction_of
from .activation import ConeBasedShapeKeyDriverActivation
if TYPE_CHECKING:
    from bpy.types import Context, ShapeKey
    from mathutils import Vector


def manager_bone_target(settings: 'ConeBasedShapeKeyDriverManager') -> str:
    fcurve = driver_find(settings.id_data, settings.data_path)
    if fcurve is not None:
        variables = fcurve.driver.variables
        if len(variables) > 1:
            return variables[1].targets[0].bone_target
    return ""


def manager_identifier(settings: 'ConeBasedShapeKeyDriverManager') -> str:
    return settings.get("identifier", ""),


def manager_object_validate(_: 'ConeBasedShapeKeyDriverManager', object: Object) -> bool:
    return object.type == 'ARMATURE'


def manager_center_angle(settings: 'ConeBasedShapeKeyDriverManager') -> float:
    return settings.center_quaternion.to_axis_angle()[1]


def manager_center_angle_set(settings: 'ConeBasedShapeKeyDriverManager', value: float) -> None:
    settings.center_quaternion = Quaternion(manager_center_axis(settings), value)


def manager_center_axis(settings: 'ConeBasedShapeKeyDriverManager') -> 'Vector':
    return settings.center_quaternion.to_axis_angle()[0]


def manager_center_axis_set(settings: 'ConeBasedShapeKeyDriverManager',
                            value: Tuple[float, float, float]) -> None:
    settings.center_quaternion = Quaternion(value, manager_center_angle(settings))


def manager_center_euler(manager: 'ConeBasedShapeKeyDriverManager') -> 'Euler':
    return manager.center_quaternion.to_euler()


def manager_center_euler_set(manager: 'ConeBasedShapeKeyDriverManager',
                             value: Tuple[float, float, float]) -> None:
    manager.center_quaternion = Euler(value).to_quaternion()


class ConeBasedShapeKeyDriverManager(PropertyGroup):
    """Manages and stores settings for a cone based corrective shape key"""

    def update(self, context: Optional[Context]=None) -> None:

        if isinstance(context, str):
            bone_target = context
        else:
            bone_target = self.get_bone_target()

        activation: ConeBasedShapeKeyDriverActivation = self.activation

        points = activation.points
        rangex = (1.0-activation.radius, 1.0)
        rangey = (0.0, activation.value)

        fcurve = driver_ensure(self.id_data, self.data_path)
        points = to_bezier(points, x_range=rangex, y_range=rangey, extrapolate=False)

        keyframe_points_assign(fcurve.keyframe_points, points)

        driver = fcurve.driver
        variables = driver_variables_empty(driver)

        variable = variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = self.identifier

        target = variable.targets[0]
        target.id_type = 'KEY'
        target.id = self.id_data
        target.data_path = "reference_key.value"

        for axis in 'WXYZ':

            variable = variables.new()
            variable.type = 'TRANSFORMS'
            variable.name = axis.lower()

            target = variable.targets[0]
            target.id = self.object
            target.bone_target = bone_target
            target.transform_type = f'ROT_{axis}'
            target.transform_space = 'LOCAL_SPACE'
            target.rotation_mode = 'QUATERNION'

        x, y, z = direction_of(self.center_quaternion)
        driver.type = 'SCRIPTED'
        # The function runs through the following steps:
        # - Convert the target bone's (local space) rotation quaternion to a direction vector
        # - Calculate the dot product between the pose's direction vector and the target bone's rotation vector
        # - Range the result and apply a inverse sine function to negate the effect of the dot product calculation so that the fcurve operates in the 0-1 range
        driver.expression = f'(asin(2.0*(x*y-w*z)*{x}+(1.0-2.0*(x*x+z*z))*{y}+2.0*(y*z+w*x)*{z})--(pi/2.0))/pi'

    bone_target: StringProperty(
        name="Bone",
        description="The bone to read rotations from",
        get=manager_bone_target,
        set=update,
        options=set()
        )

    @property
    def data_path(self) -> str:
        return f'key_blocks["{self.name}"].value'

    activation: PointerProperty(
        name="Activation Curve",
        description="The activation curve for the driver",
        type=ConeBasedShapeKeyDriverActivation,
        options=set()
        )

    identifier: StringProperty(
        name="Shape",
        description="Unique identifier used to hold a reference to the driven shape key.",
        get=manager_identifier,
        options={'HIDDEN'}
        )

    mute: BoolProperty(
        name="Mute",
        description=("Whether or not the driven shape key's driver is enabled. Disabling "
                     "the driver allows (temporary) editing of the shape key's value in the UI"),
        default=False,
        options=set(),
        update=update
        )

    object: PointerProperty(
        name="Object",
        description="The armature object",
        type=Object,
        poll=manager_object_validate,
        update=update,
        options=set()
        )

    center_angle: FloatProperty(
        name="Rotation",
        description="Rotation value for the driver",
        subtype='ANGLE',
        get=manager_center_angle,
        set=manager_center_angle_set,
        precision=3,
        options=set()
        )

    center_axis: FloatVectorProperty(
        name="Rotation",
        description="Rotation value for the driver",
        size=3,
        subtype='XYZ',
        get=manager_center_axis,
        set=manager_center_axis_set,
        precision=3,
        options=set()
        )

    center_quaternion: FloatVectorProperty(
        name="Rotation",
        description="Rotation value for the driver",
        size=4,
        default=(1.0, 0.0, 0.0, 0.0),
        precision=3,
        subtype='QUATERNION',
        update=update,
        options=set()
        )

    center_euler: FloatVectorProperty(
        name="Rotation",
        description="Rotation value for the driver",
        size=3,
        subtype='EULER',
        precision=3,
        get=manager_center_euler,
        set=manager_center_euler_set,
        options=set()
        )

    rotation_mode: EnumProperty(
        name="Mode",
        description="UI rotation mode. Does not affect the driver results.",
        items=[
            ('EULER'     , "Euler"     , "Euler angles"       ),
            ('QUATERNION', "Quaternion", "Quaternion rotation"),
            ('AXIS_ANGLE', "Axis/Angle", "Axis/Angle rotation"),
            ],
        default='QUATERNION',
        options=set()
        )

    def __init__(self, shape: 'ShapeKey') -> None:
        self["name"] = shape.name
        self["identifier"] = f'conedriver_{uuid4()}'
        self.activation.__init__(shape)
        self.update()
