
from typing import Set, TYPE_CHECKING
from bpy.types import Operator
from .base import COMPAT_ENGINES, COMPAT_OBJECTS
if TYPE_CHECKING:
    from bpy.types import Context


class CONEBASEDSHAPEKEYDRIVER_OT_add(Operator):

    bl_idname = 'cone_based_shape_key_driver.add'
    bl_label = "Add Cone-Based Shape Key Driver"
    bl_description = "Add a cone-based driver to the shape key"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context:'Context') -> bool:
        if context.engine in COMPAT_ENGINES:
            object = context.object
            if object is not None and object.type in COMPAT_OBJECTS:
                shape = object.active_shape_key
                if shape is not None:
                    key = shape.id_data
                    return (key.use_relative
                            and shape != key.reference_key
                            and (not key.is_property_set("cone_based_drivers")
                                 or shape.name not in key.cone_based_drivers))
        return False

    def execute(self, context: 'Context') -> Set[str]:
        shape = context.object.active_shape_key
        shape.id_data.cone_based_drivers.add().__init__(shape)
        return {'FINISHED'}
