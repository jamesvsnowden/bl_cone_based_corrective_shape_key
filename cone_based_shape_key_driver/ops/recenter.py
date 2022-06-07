
from typing import Set, TYPE_CHECKING
from bpy.types import Operator
from .base import COMPAT_ENGINES, COMPAT_OBJECTS
from ..lib.transform_utils import transform_matrix
if TYPE_CHECKING:
    from bpy.types import Context


class CONEBASEDSHAPEKEYDRIVER_OT_recenter(Operator):

    bl_idname = 'cone_based_shape_key_driver.recenter'
    bl_label = "Update Center"
    bl_description = "Update the rotation center from the target's current rotation value"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        if context.engine in COMPAT_ENGINES:
            object = context.object
            if object is not None and object.type in COMPAT_OBJECTS:
                shape = object.active_shape_key
                if shape is not None:
                    key = shape.id_data
                    if (key.use_relative
                        and shape != key.reference_key
                        and key.is_property_set("cone_based_drivers")):
                        settings = key.cone_based_drivers.get(shape.name)
                        if settings:
                            object = settings.object
                            return (object is not None
                                    and object.type == 'ARMATURE'
                                    and settings.bone_target in object.pose.bones)
        return False

    def execute(self, context: 'Context') -> Set[str]:
        shape = context.object.active_shape_key
        manager = shape.id_data.cone_based_drivers[shape.name]
        object = manager.object
        target = manager.bone_target
        matrix = transform_matrix(object.pose.bones[target], 'LOCAL_SPACE')
        manager.center_quaternion = matrix.to_quaternion()
        return {'FINISHED'}
