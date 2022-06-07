
from typing import Set, TYPE_CHECKING
from bpy.types import Operator
from .base import COMPAT_ENGINES, COMPAT_OBJECTS
from ..lib.driver_utils import driver_remove
if TYPE_CHECKING:
    from bpy.types import Context


class CONEBASEDSHAPEKEYDRIVER_OT_remove(Operator):

    bl_idname = 'cone_based_shape_key_driver.remove'
    bl_label = "Remove Cone-Based Shape Key Driver"
    bl_description = "Remove the shape key's cone-based driver"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        if context.engine in COMPAT_ENGINES:
            object = context.object
            if object is not None and object.type in COMPAT_OBJECTS:
                shape = object.active_shape_key
                if shape is not None:
                    key = shape.id_data
                    return (key.use_relative
                            and shape != key.reference_key
                            and key.is_property_set("cone_based_drivers")
                            and shape.name in key.cone_based_drivers)
        return False

    def execute(self, context: 'Context') -> Set[str]:
        shape = context.object.active_shape_key
        key = shape.id_data
        driver_remove(key, f'key_blocks["{shape.name}"].value')
        key.cone_based_drivers.remove(key.cone_based_drivers.find(shape.name))
        return {'FINISHED'}
