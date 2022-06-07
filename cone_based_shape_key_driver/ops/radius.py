
from typing import Set, TYPE_CHECKING
from math import asin, pi
from bpy.types import Operator
from bpy.props import EnumProperty
from base import COMPAT_ENGINES, COMPAT_OBJECTS
from ..lib.utils import direction_of
if TYPE_CHECKING:
    from bpy.types import Context


class CONEBASEDSHAPEKEYDRIVER_OT_radius_calculate(Operator):

    bl_idname = 'cone_based_shape_key_driver.radius_calculate'
    bl_label = "Calculate Radius"
    bl_description = "Calculate the radius based on the distance to the nearest neighboring target pose"
    bl_options = {'INTERNAL', 'UNDO'}

    method: EnumProperty(
        name="Calculate Radius",
        items=[
            ('CENT', "Nearest Neighbor", ""),
            ('EDGE', "Nearest Neighbor (No Intersection)", ""),
            ],
            default='CENT',
            options=set()
        )

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
                                    and bool(settings.bone_target))
        return False

    def execute(self, context: 'Context') -> Set[str]:
        shape = context.object.active_shape_key
        key = shape.id_data
        data = key.cone_based_drivers
        item = data[shape.name]
        object = item.object
        bone = item.bone_target
        neighbors = [x for x in data if x != item and x.object == object and x.bone_target == bone]
        if neighbors:
            value = direction_of(item.rotation_quaternion)
            radii = []
            outer = self.method == 'EDGE'
            for other in neighbors:
                radius = (asin(value.dot(direction_of(other.rotation_quaternion))) - -(pi/2.0))/pi
                radii.append(max(0.0, radius - other.radius if outer else radius))
            radius = min(radii)
            if radius > 0.001:
                item.radius = radius
        return {'FINISHED'}
